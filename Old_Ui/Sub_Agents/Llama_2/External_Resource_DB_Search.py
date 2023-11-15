import os
import sys
sys.path.insert(0, './scripts/resources')
from Llama2_chat import *
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, Range, MatchValue
from qdrant_client.http import models
import time
import json
import importlib.util
import requests
import tkinter as tk
import requests
import concurrent.futures
from bs4 import BeautifulSoup


# Set to True if you want Aetherius to search the web if the information cannot be found in it's external resources database.
Search_Web = True

# Set the desired search engine to use if information cannot be found in DB
# Available Options: "Google, Bing"
Search_Engine = "Google"



with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
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
        url = open_file('./api_keys/qdrant_url.txt')
        api_key = open_file('./api_keys/qdrant_api_key.txt')
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


def import_functions_from_script(script_path, custom_name="custom_module"):
    """
    Import functions from a given script path.

    Parameters:
    - script_path: The path to the script to import.
    - custom_name: Optional custom module name for import.
    """
    spec = importlib.util.spec_from_file_location(custom_name, script_path)
    custom_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(custom_module)
    globals().update(vars(custom_module))


def get_script_path_from_file(json_path, key, base_folder='./scripts/resources/'):
    """
    Get the script path from a JSON file.

    Parameters:
    - json_path: The path to the JSON file containing the settings.
    - key: The key for the particular setting.
    - base_folder: The base folder where the script is located.
    """
    with open(json_path, 'r', encoding='utf-8') as file:
        settings = json.load(file)
    script_name = settings.get(key, "").strip()
    return f'{base_folder}{script_name}.py'

# Path to the JSON settings file
json_file_path = './config/chatbot_settings.json'

# Import for model
script_path1 = get_script_path_from_file(json_file_path, "model")
import_functions_from_script(script_path1, "model_module")

# Import for embedding model
script_path2 = get_script_path_from_file(json_file_path, "embedding_model")
import_functions_from_script(script_path2, "embedding_module")

# Import for TTS
script_path3 = get_script_path_from_file(json_file_path, "TTS", base_folder='./scripts/resources/TTS/')
import_functions_from_script(script_path3, "TTS_module")



def google_search(query, my_api_key, my_cse_id, **kwargs):
    params = {
        "key": my_api_key,
        "cx": my_cse_id,
        "q": query,
        "num": 7,
        "snippet": "true"  # use a string here instead of a boolean
    }
    
    response = requests.get("https://www.googleapis.com/customsearch/v1", params=params)
    
    if response.status_code == 200:
        data = response.json()
        urls = [item['link'] for item in data.get("items", [])]
        snippets = [item['snippet'] for item in data.get("items", [])]
        return urls, snippets
    else:
        raise Exception(f"Request failed with status code {response.status_code}")


# Define any missing functions like summarized_chunk_from_url and embeddings

def fetch_html(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def fetch_all(urls, username, bot_name, task_counter):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(lambda url: chunk_text_from_url(url, username, bot_name, task_counter), urls))
    return results

def read_json(filepath):
    with open(filepath, mode='r', encoding='utf-8') as f:
        return json.load(f)

def chunk_text(text, chunk_size, overlap):
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

def chunk_text_from_url(url, username, bot_name, task_counter, chunk_size=380, overlap=40):
    try:
        response = requests.get(url)
        response.raise_for_status()
        html = response.text

        soup = BeautifulSoup(html, 'html.parser')
        texttemp = soup.get_text().strip()
        texttemp = texttemp.replace('\n', '').replace('\r', '')
        texttemp = '\n'.join(line for line in texttemp.splitlines() if line.strip())
        chunks = chunk_text(texttemp, chunk_size, overlap)
        weblist = list()

        try:
            with open('config/chatbot_settings.json', mode='r', encoding='utf-8') as f:
                contents = f.read()
            settings = json.loads(contents)
            host_data = settings.get('HOST_Oobabooga', '').strip()
            hosts = host_data.split(' ')
            num_hosts = len(hosts)
        except Exception as e:
            print(f"An error occurred while reading the host file: {e}")

        host_queue = concurrent.futures.Queue()
        for host in hosts:
            host_queue.put(host)

        collection_name = f"Bot_{bot_name}_External_Knowledgebase"
        try:
            collection_info = client.get_collection(collection_name=collection_name)
            print(collection_info)
        except:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=embed_size, distance=Distance.COSINE),
            )

        def process_chunk(chunk):
            nonlocal weblist
            try:
                result = wrapped_chunk_from_url(
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

        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(process_chunk, chunks)

        return weblist

    except Exception as e:
        return [f"An error occurred in your_parent_function: {e}"]

def wrapped_chunk_from_url(host_queue, chunk, collection_name, bot_name, username, client, url, task_counter):
    try:
        host = host_queue.get()

        result = summarized_chunk_from_url(host, chunk, collection_name, bot_name, username, client, url, task_counter)
        host_queue.put(host)
        return result
    except Exception as e:
        print(e)

def summarized_chunk_from_url(host, chunk, collection_name, bot_name, username, client, url, task_counter):
    try:
        weblist = list()
        text = str(chunk)

        weblist.append(url + ' ' + text)
        payload = list()
        timestamp = time.time()
        timestring = timestamp_to_datetime(timestamp)

        vector1 = embeddings(text)
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

        if weblist:
            result_url, result_text = weblist[0].split(' ', 1)
            return {'url': result_url, 'processed_text': result_text}

    except Exception as e:
        print(e)
        return {'url': 'Error', 'processed_text': str(e)}

        
def search_and_chunk(query, my_api_key, my_cse_id, **kwargs):
    try:
        urls = google_search(query, my_api_key, my_cse_id, **kwargs)
        chunks = []
        for url in urls:
            chunks += chunk_text_from_url(url)
        return chunks
    except:
        print('Fail1')



def External_Resource_DB_Search_Description():
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    
    description = f"A module for searching {bot_name}'s External Resource Database.\nThis Module is meant to be used for verifying or searching for external information."
    return description

def External_Resource_DB_Search(self, host, bot_name, username, line, task_counter, output_one, output_two, master_tasklist_output, a):
    try:
        user_input = a
        my_api_key = open_file('api_keys/key_google.txt')
        my_cse_id = open_file('api_keys/key_google_cse.txt')
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
        vector_input1 = embeddings(line)
        table = "No External Resources in DB"
        try:
            hits = client.search(
                collection_name=f"Bot_{bot_name}_External_Knowledgebase",
                query_vector=vector_input1,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="user",
                            match=MatchValue(value=f"{username}")
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
            
        if Search_Web == True:    
            websearch_check.append({'role': 'assistant', 'content': f"You are a selection agent for an autonomous AI chatbot.  Your job is to decide if the given database queries contain the needed information to answer the user's inquiry. If the information isn't given or if it needs to be updated, print 'NO'.  Only respond with either 'YES' or 'NO'.\n\nGIVEN DATABASE QUERIES: {table}\n\nUSER INQUIRY: {user_input} [/INST] "})
            prompt = ''.join([message_dict['content'] for message_dict in websearch_check])
            web_check = agent_oobabooga_memory_db_check(host, prompt)
            print(web_check)
            if "NO" in web_check:
                websearch_rephrase.append({'role': 'assistant', 'content': f"Rephrase the user's inquiry into a google search query that will return the requested information.  Only print the search query, do not include anything about the External Resources Module.  The search query should be a natural sounding question.\nUSER INQUIRY: {line} [/INST] Google Search Query: "})
                prompt = ''.join([message_dict['content'] for message_dict in websearch_rephrase])
                rephrased_query = agent_oobabooga_google_rephrase(host, prompt)
                if '"' in rephrased_query:
                    rephrased_query = rephrased_query.replace('"', '')
                print(rephrased_query)
                if Search_Engine == "Google":
                    try:
                        my_api_key = open_file('api_keys/key_google.txt')
                        my_cse_id = open_file('api_keys/key_google_cse.txt')
                                
                        urls, snippets = google_search(rephrased_query, my_api_key, my_cse_id)

                        for url, snippet in zip(urls, snippets):
                            payload = list()
                            timestamp = time()
                            timestring = timestamp_to_datetime(timestamp)  # Assuming timestamp_to_datetime is defined
                            vector1 = embeddings(snippet)  # Assuming embeddings is an asynchronous function
                            unique_id = str(uuid4())
                            point_id = unique_id + str(int(timestamp))
                            metadata = {
                                'bot': bot_name,  # Assuming bot_name is defined
                                'user': username,  # Assuming username is defined
                                'source': url,
                                'task': task_counter,  # Assuming task_counter is defined
                                'message': snippet,
                                'uuid': unique_id,
                                'memory_type': 'Web_Scrape_Url',
                            }

                            # Assuming PointStruct and client are defined and set up properly
                            client.upsert(collection_name = f"Bot_{bot_name}_External_Knowledgebase",
                                          points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])
                            payload.clear()
                        
                        
                        
                        
                        
                        
                        vector1 = embeddings(user_input)

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
                                            match=models.MatchValue(value=f"{username}")
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
                            texts = fetch_all(urls, username, bot_name, task_counter)
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
                                            match=models.MatchValue(value=f"{username}"),
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
                        self.conversation_text.insert(tk.END, f"{table}\n")
                        self.conversation_text.insert(tk.END, f"------------------------------------------------------------------------------------------------------------------\n")
                        print(table)
                        

                if Search_Engine == "Bing":
                    try:
                        subscription_key = open_file('./api_keys/key_bing.txt')
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
                        self.conversation_text.insert(tk.END, f"{table}\n")
                        self.conversation_text.insert(tk.END, f"------------------------------------------------------------------------------------------------------------------\n")
                        print(table)

        conversation.append({'role': 'assistant', 'content': f"[INST] INITIAL USER REQUEST: {a}\n Now please provide relevant external resources to answer the query. [/INST]"})
        conversation.append({'role': 'user', 'content': f"Bot {task_counter}: EXTERNAL RESOURCES: {table}"})
        conversation.append({'role': 'user', 'content': f"[INST] SYSTEM: Summarize the pertinent information from the given external sources related to the given task. Present the summarized data in a single, easy-to-understand paragraph. Do not generalize, expand upon, or use any latent knowledge in your summary, only return a truncated version of previously given information. [/INST] Bot {task_counter}: Sure, here is a short summary combining the relevant information needed to complete the given task: "})
        conversation.append({'role': 'assistant', 'content': f"BOT {task_counter}: Sure, here's an overview of the scraped text: "})
        prompt = ''.join([message_dict['content'] for message_dict in conversation])
        task_completion = agent_oobabooga_process_line_response(host, prompt)
            # chatgpt35_completion(conversation),
            # conversation.clear(),
            # tasklist_completion.append({'role': 'assistant', 'content': f"MEMORIES: {memories}\n\n"}),
            # tasklist_completion.append({'role': 'assistant', 'content': f"WEBSCRAPE: {table}\n\n"}),
        tasklist_completion2.append({'role': 'assistant', 'content': f"COMPLETED TASK: {task_completion} [INST] "})
        tasklist_log.append({'role': 'user', 'content': "ASSIGNED TASK:\n%s\n\n" % line})
        print('-------')
        self.conversation_text.insert(tk.END, f"Task {task_counter}: {line}\n")
        self.conversation_text.insert(tk.END, f"Task Completion: {task_completion}\n")
        self.conversation_text.insert(tk.END, f"------------------------------------------------------------------------------------------------------------------\n")
        print(line)
        print('-------')
        # print(result)
        # print(table)
        # print('-------')
        print(task_completion)
        return tasklist_completion2
    except Exception as e:
        print(f'Failed with error: {e}')
        error = 'ERROR WITH PROCESS LINE FUNCTION'
        return error