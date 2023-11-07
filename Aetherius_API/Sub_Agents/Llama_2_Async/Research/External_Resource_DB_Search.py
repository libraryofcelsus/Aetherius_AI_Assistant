import os
import sys
sys.path.insert(0, './Aetherius_API/resources')
from Llama2_chat_Async import *
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, Range, MatchValue
from qdrant_client.http import models
from time import time
from datetime import datetime
from uuid import uuid4
import json
import importlib.util
import requests
import asyncio
import aiohttp
import aiofiles
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

# Set the desired search engine to use if information cannot be found in DB
# Available Options: "Google, Bing"
Search_Engine = "Google"



with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
    settings = json.load(f)
    
embed_size = settings['embed_size']

def check_local_server_running():
    try:
        response = requests.get("http://localhost:6333/dashboard/")
        return response.status_code == 200
    except requests.ConnectionError:
        return False

        
def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
       return file.read().strip()

# Check if local server is running
if check_local_server_running():
    client = QdrantClient(url="http://localhost:6333")
    # print("Connected to local Qdrant server.")
else:
    try:
        url = open_file('./Aetherius_API/api_keys/qdrant_url.txt')
        api_key = open_file('./Aetherius_API/api_keys/qdrant_api_key.txt')
        client = QdrantClient(url=url, api_key=api_key)
        client.recreate_collection(
            collection_name="Ping",
            vectors_config=VectorParams(size=1, distance=Distance.COSINE),
        )
        # print("Connected to cloud Qdrant server.")
    except:
        if not os.path.exists("./Qdrant_DB"):
            os.makedirs("./Qdrant_DB")
        client = QdrantClient(path="./Qdrant_DB")
        # print("Neither a local nor a cloud Qdrant server could be connected. Using disk storage.")




model = SentenceTransformer('all-mpnet-base-v2')


executor = ThreadPoolExecutor()

async def embeddings(query):
    loop = asyncio.get_event_loop()
    vector = await loop.run_in_executor(executor, lambda: model.encode([query])[0].tolist())
    return vector
    
    
def timestamp_to_datetime(unix_time):
    datetime_obj = datetime.fromtimestamp(unix_time)
    datetime_str = datetime_obj.strftime("%A, %B %d, %Y at %I:%M%p %Z")
    return datetime_str
    
    
async def google_search(query, my_api_key, my_cse_id, **kwargs):
    params = {
        "key": my_api_key,
        "cx": my_cse_id,
        "q": query,
        "num": 7,
        "snippet": "true"  # use a string here instead of a boolean
    }
    async with aiohttp.ClientSession() as session:
        async with session.get("https://www.googleapis.com/customsearch/v1", params=params) as response:
            if response.status == 200:
                data = await response.json()
                urls = [item['link'] for item in data.get("items", [])]
                snippets = [item['snippet'] for item in data.get("items", [])]
                return urls, snippets
            else:
                raise Exception(f"Request failed with status code {response.status}")


     
async def fetch_html(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()
            
async def fetch_all(urls, username, bot_name, task_counter):
    tasks = [chunk_text_from_url(url, username, bot_name, task_counter) for url in urls]
    return await asyncio.gather(*tasks)

async def read_json(filepath):
    async with aiofiles.open(filepath, mode='r', encoding='utf-8') as f:
        return json.loads(await f.read())
        
async def chunk_text(text, chunk_size, overlap):
    chunks = []
    start = 0
    end = chunk_size
    while end <= len(text):
        chunks.append(text[start:end])
        start += chunk_size - overlap
        end += chunk_size - overlap
    if end > len(text):
        chunks.append(text[start:])
    return chunks 
        
        
async def chunk_text_from_url(url, username, bot_name, task_counter, chunk_size=480, overlap=40):
    try:
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                html = await response.text()

        soup = BeautifulSoup(html, 'html.parser')
        texttemp = soup.get_text().strip()
        texttemp = texttemp.replace('\n', '').replace('\r', '')
        texttemp = '\n'.join(line for line in texttemp.splitlines() if line.strip())
        chunks = await chunk_text(texttemp, chunk_size, overlap)
        weblist = list()

        try:
            async with aiofiles.open('config/chatbot_settings.json', mode='r', encoding='utf-8') as f:
                contents = await f.read()
            settings = json.loads(contents)
            host_data = settings.get('HOST_Oobabooga', '').strip()
            hosts = host_data.split(' ')
            num_hosts = len(hosts)
        except Exception as e:
            print(f"An error occurred while reading the host file: {e}")
        # Assuming host_queue is now an async queue
        host_queue = asyncio.Queue()
        for host in hosts:
            await host_queue.put(host)
            
        # Define the collection name
        collection_name = f"Bot_{bot_name}_External_Knowledgebase"
        try:
            collection_info = client.get_collection(collection_name=collection_name)
            print(collection_info)
        except:
            client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=embed_size, distance=Distance.COSINE),
        )
        
        
        async def process_chunk(chunk):
            nonlocal weblist  # Make sure you can modify weblist
            try:
                result = await wrapped_chunk_from_url(
                    host_queue, chunk, collection_name, bot_name, username, client, url, task_counter
                )
                
                if not isinstance(result, dict):
                    weblist.append(f"Error: Expected a dictionary, but got {type(result)}")
                    return

                if 'url' not in result or 'processed_text' not in result:
                    weblist.append(f"Error: Expected keys 'url' and 'processed_text' in the result dictionary. Got: {result.keys()}")
                    return

                weblist.append(result['url'] + ' ' + result['processed_text'])
                
            except Exception as e:
                weblist.append(f"An error occurred in process_chunk: {e}")

        # Use asyncio.gather to run all the coroutines concurrently
        await asyncio.gather(*(process_chunk(chunk) for chunk in chunks))

        return weblist  # Return weblist here

    except Exception as e:
        return [f"An error occurred in your_parent_function: {e}"]


async def wrapped_chunk_from_url(host_queue, chunk, collection_name, bot_name, username, client, url, task_counter):
    try:
        # get a host
        host = await host_queue.get()
        
        # Assuming summarized_chunk_from_url is also async function
        result = await summarized_chunk_from_url(host, chunk, collection_name, bot_name, username, client, url, task_counter)
        # release the host
        await host_queue.put(host)
        return result
    except Exception as e:
        print(e)


async def summarized_chunk_from_url(host, chunk, collection_name, bot_name, username, client, url, task_counter):
    try:
        weblist = list()
        text = str(chunk)

        weblist.append(url + ' ' + text)
        payload = list()
        timestamp = time()
        timestring = timestamp_to_datetime(timestamp)

        vector1 = await embeddings(text)
        unique_id = str(uuid4())
        point_id = unique_id + str(int(timestamp))
        metadata = {
            'bot': bot_name,
            'user': username,
            'time': timestamp,
            'source': url,
            'task': task_counter,
            'message': text,
            'timestring': timestring,
            'uuid': unique_id,
            'memory_type': 'Web_Scrape_Temp',
        }

        client.upsert(collection_name=collection_name,
                      points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)]) 
      

        # Assuming weblist is a list with a single item formatted as "url text"
        if weblist:
            result_url, result_text = weblist[0].split(' ', 1)
            return {'url': result_url, 'processed_text': result_text}

    except Exception as e:
        print(e)
        return {'url': 'Error', 'processed_text': str(e)}


def External_Resource_DB_Search_Description(username, bot_name):
    description = f"External_Resource_DB_Search.py: A module for searching {bot_name}'s External Resource Database.  This Module is meant to be used for the verification and retrieval of external information. This module also includes a web-search Tool."
    return description

async def External_Resource_DB_Search(host, bot_name, username, user_id, line, task_counter, output_one, output_two, master_tasklist_output, user_input):
    try:
        async with aiofiles.open('./Aetherius_API/chatbot_settings.json', mode='r', encoding='utf-8') as f:
            settings = json.loads(await f.read())
        embed_size = settings['embed_size']
        Web_Search = settings.get('Search_Web', 'False')
        Search_Engine = settings.get('Search_Engine', 'Google')
        Sub_Module_Output = settings.get('Output_Sub_Module', 'False')
        tasklist_completion2 = list()
        memcheck = list()
        memcheck2 = list()
        webcheck = list()
        tasklist_log = list()
        conversation = list()
        websearch_check = list()
        websearch_rephrase = list()
        botnameupper = bot_name.upper()
        usernameupper = username.upper()
        tasklist_completion2.append({'role': 'user', 'content': f"TASK: {line} [/INST] "})
        conversation.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: You are a sub-agent for {bot_name}, an Autonomous Ai-Chatbot. You are one of many agents in a chain. You are to take the given task and complete it in its entirety, using the given external resources to ensure factual accuracy. Be Verbose and take other tasks into account when formulating your answer.\n"})
        conversation.append({'role': 'user', 'content': f"Task list: {master_tasklist_output}\nNow, choose a task to research.[/INST]"})
        conversation.append({'role': 'assistant', 'content': f"Bot {task_counter}: I have studied the given tasklist. The task I have chosen to complete is: {line}."})
        vector_input1 = await embeddings(line)
        table = "No External Resources in DB"
        # Define the collection name
        collection_name = f"Bot_{bot_name}_External_Knowledgebase"
        try:
            collection_info = client.get_collection(collection_name=collection_name)
            print(collection_info)
        except:
            client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=embed_size, distance=Distance.COSINE),
        )
        
        try:
            hits = client.search(
                collection_name=f"Bot_{bot_name}_External_Knowledgebase",
                query_vector=vector_input1,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="user",
                            match=MatchValue(value=f"{user_id}")
                        )
                    ]
                ),
                limit=15
            )
            unsorted_table = [(hit.payload['tag'], hit.payload['message']) for hit in hits]
            sorted_table = sorted(unsorted_table, key=lambda x: x[0])  # Sort by the 'tag' field
            table = "\n".join([f"{tag} - {message}" for tag, message in sorted_table])
                # print(table)
        except:
            table = "No External Resources Available"
            
        if Web_Search == 'True':    
            websearch_check.append({'role': 'assistant', 'content': f"You are a selection agent for an autonomous AI chatbot.  Your job is to decide if the given database queries contain the needed information to answer the user's inquiry. If the information isn't given or if it needs to be updated, print 'NO'.  Only respond with either 'YES' or 'NO'.\n\nGIVEN DATABASE QUERIES: {table}\n\nUSER INQUIRY: {user_input} [/INST] "})
            prompt = ''.join([message_dict['content'] for message_dict in websearch_check])
            web_check = await agent_oobabooga_memory_db_check(host, prompt, username, bot_name)
            print(web_check)
            if "NO" in web_check:
                websearch_rephrase.append({'role': 'assistant', 'content': f"Rephrase the user's inquiry into a google search query that will return the requested information.  Only print the search query, do not include anything about the External Resources Module.  The search query should be a natural sounding question.\nUSER INQUIRY: {line} [/INST] Google Search Query: "})
                prompt = ''.join([message_dict['content'] for message_dict in websearch_rephrase])
                rephrased_query = await agent_oobabooga_google_rephrase(host, prompt, username, bot_name)
                if '"' in rephrased_query:
                    rephrased_query = rephrased_query.replace('"', '')
                print(rephrased_query)
                if Search_Engine == "Google":
                    try:
                        my_api_key = open_file('./Aetherius_API/api_keys/key_google.txt')
                        my_cse_id = open_file('./Aetherius_API/api_keys/key_google_cse.txt')
                        urls, snippets = await google_search(rephrased_query, my_api_key, my_cse_id)

                        for url, snippet in zip(urls, snippets):
                            payload = list()
                            timestamp = time()
                            timestring = timestamp_to_datetime(timestamp) 
                            vector1 = await embeddings(snippet)  
                            unique_id = str(uuid4())
                            point_id = unique_id + str(int(timestamp))
                            metadata = {
                                'bot': bot_name, 
                                'user': user_id, 
                                'source': url,
                                'task': task_counter,  
                                'message': snippet,
                                'uuid': unique_id,
                                'memory_type': 'Web_Scrape_Url',
                            }

                    
                            client.upsert(collection_name = f"Bot_{bot_name}_External_Knowledgebase",
                                          points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])
                            payload.clear()
                        
                        vector1 = await embeddings(user_input)

                        try:
                            payload = list()
                            # Perform the search query
                            hits = client.search(
                                collection_name=f"Bot_{bot_name}_External_Knowledgebase",
                                query_vector=vector1,
                                query_filter=Filter(
                                    must=[
                                        FieldCondition(
                                            key="user",
                                            match=models.MatchValue(value=f"{user_id}")
                                        ),
                                        FieldCondition(
                                            key="memory_type",
                                            match=models.MatchValue(value=f"Web_Scrape_Url")
                                        ),
                                        FieldCondition(
                                            key="task",
                                            match=models.MatchValue(value=task_counter)
                                        ),
                                    ]
                                ),
                                limit=1
                            )
                            # Prepare the table from the search hits
                            unsorted_table = [(hit.payload['source'], hit.payload['message']) for hit in hits]
                            sorted_table = sorted(unsorted_table, key=lambda x: x[0])
                            joined_table = "\n".join([f"{source} - {message}" for source, message in sorted_table])
                            table = f"{joined_table}\n{snippets}"

                            # Extract the URLs from search to be passed into fetch_all
                            urls_from_search = [hit.payload['source'] for hit in hits]
                            urls = urls_from_search

                        except Exception as e:
                            print(f"An error occurred: {e}")
                            table = "No External Resources Available"

                        try:
                            # Perform the fetch for all URLs
                            texts = await fetch_all(urls, username, bot_name, task_counter)
                        except Exception as e:
                            print(f"An error occurred while fetching all texts: {e}")
                            texts = []
                        
                        
                        try:
                            hits = client.search(
                                collection_name=f"Bot_{bot_name}_External_Knowledgebase",
                                query_vector=vector_input1,
                                query_filter=Filter(
                                    must=[
                                        FieldCondition(
                                            key="user",
                                            match=models.MatchValue(value=f"{user_id}"),
                                        ),
                                        FieldCondition(
                                            key="memory_type",
                                            match=models.MatchValue(value=f"Web_Scrape_Temp"),
                                        ),
                                        FieldCondition(
                                            key="task",
                                            match=models.MatchValue(value=task_counter),
                                        ),
                                    ]
                                ),
                                limit=13
                            )
                            
                            
                            unsorted_table = [(hit.payload['source'], hit.payload['message']) for hit in hits]
                            sorted_table = sorted(unsorted_table, key=lambda x: x[0])  # Sort by the 'source' field
                            joined_table = " ".join([f"{source} - {message}" for source, message in sorted_table])
                            table = f"{snippets}\n{joined_table}"
                        except Exception as e:  # Log the exception for debugging
                            print(f"An error occurred: {e}")
                            table = "No External Resources Available"
                        


                    except Exception as e:
                        print(e)
                        table = "Google Search Failed.  Remind user they need to add the Google Api key to the api keys folder or disable the web-search in the External Resources Sub-Agent."
                        print(table)

                if Search_Engine == "Bing":
                    try:
                        subscription_key = open_file('./Aetherius_API/api_keys/key_bing.txt')
                        assert subscription_key
                        search_url = "https://api.bing.microsoft.com/v7.0/search"

                        headers = {"Ocp-Apim-Subscription-Key": subscription_key}
                        params = {"q": rephrased_query, "textDecorations": True, "textFormat": "HTML"}

                        response = requests.get(search_url, headers=headers, params=params)
                        response.raise_for_status()
                        search_results = response.json()
                        results = search_results
                        rows = "\n".join(["""<tr>
                                            <td><a href=\"{0}\">{1}</a></td>
                                            <td>{2}</td>
                                            </tr>""".format(v["url"], v["name"], v["snippet"])
                                        for v in results["webPages"]["value"]])
                        table = "<table>{0}</table>".format(rows)
                    except Exception as e:
                        print(e)
                        table = "Bing Search Failed.  Remind user they need to add the Bing Api key to the api keys folder or disable the web-search in the External Resources Sub-Agent."
                        print(table)

        print(table)
        conversation.append({'role': 'assistant', 'content': f"[INST] INITIAL USER REQUEST: {user_input}\n Now please provide relevant external resources to answer the query. [/INST]"})
        conversation.append({'role': 'user', 'content': f"Bot {task_counter}: EXTERNAL RESOURCES: {table}"})
        conversation.append({'role': 'user', 'content': f"[INST] SYSTEM: Summarize the pertinent information from the given external sources related to the given task. Present the summarized data in a single, easy-to-understand paragraph. Do not generalize, expand upon, or use any latent knowledge in your summary, only return a truncated version of previously given information. [/INST] Bot {task_counter}: Sure, here is a short summary combining the relevant information needed to complete the given task: "})
        conversation.append({'role': 'assistant', 'content': f"BOT {task_counter}: Sure, here's an overview of the scraped text: "})
        prompt = ''.join([message_dict['content'] for message_dict in conversation])
        task_completion = await agent_oobabooga_process_line_response(host, prompt, username, bot_name)
            # chatgpt35_completion(conversation),
            # conversation.clear(),
            # tasklist_completion.append({'role': 'assistant', 'content': f"MEMORIES: {memories}\n\n"}),
            # tasklist_completion.append({'role': 'assistant', 'content': f"WEBSCRAPE: {table}\n\n"}),
        tasklist_completion2.append({'role': 'assistant', 'content': f"COMPLETED TASK: {task_completion} [INST] "})
        tasklist_log.append({'role': 'user', 'content': "ASSIGNED TASK:\n%s\n\n" % line})
        if Sub_Module_Output == 'True':
            print('-------')
            print(line)
            print('-------')
            # print(result)
            # print(table)
            # print('-------')
            print(task_completion)
        client.delete(
            collection_name=f"Bot_{bot_name}_External_Knowledgebase",
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        FieldCondition(
                            key="user",
                            match=models.MatchValue(value=f"{user_id}"),
                        ),
                        FieldCondition(
                            key="memory_type",
                            match=models.MatchValue(value=f"Web_Scrape_Temp"),
                        ),
                        FieldCondition(
                            key="task",
                            match=models.MatchValue(value=task_counter),
                        ),
                    ],
                )
            ),
        ) 
        client.delete(
            collection_name=f"Bot_{bot_name}_External_Knowledgebase",
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        FieldCondition(
                            key="user",
                            match=models.MatchValue(value=f"{user_id}"),
                        ),
                        FieldCondition(
                            key="memory_type",
                            match=models.MatchValue(value=f"Web_Scrape_Url"),
                        ),
                        FieldCondition(
                            key="task",
                            match=models.MatchValue(value=task_counter),
                        ),
                    ],
                )
            ),
        ) 
        
        return tasklist_completion2
    except Exception as e:
        print(f'Failed with error: {e}')
        error = 'ERROR WITH PROCESS LINE FUNCTION'
        return error