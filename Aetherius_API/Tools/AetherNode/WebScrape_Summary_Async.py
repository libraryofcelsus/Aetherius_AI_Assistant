import os
import sys
sys.path.insert(0, './Aetherius_API/resources')
from AetherNode import *
import asyncio
import aiofiles
import aiohttp
from bs4 import BeautifulSoup
import json
import time
import datetime as dt
from datetime import datetime
from uuid import uuid4
import traceback
import importlib.util
from importlib.util import spec_from_file_location, module_from_spec
import requests
from qdrant_client import QdrantClient
from qdrant_client.models import (Distance, VectorParams, PointStruct, Filter, FieldCondition, 
                                 Range, MatchValue)
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer


model = SentenceTransformer('all-mpnet-base-v2')


def embeddings(query):
    vector = model.encode([query])[0].tolist()
    return vector

def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
       return file.read().strip()


def check_local_server_running():
    try:
        response = requests.get("http://localhost:6333/dashboard/")
        return response.status_code == 200
    except requests.ConnectionError:
        return False

# Check if local server is running
if check_local_server_running():
    client = QdrantClient(url="http://localhost:6333")
else:
    try:
        url = open_file('./Aetherius_API/api_keys/qdrant_url.txt')
        api_key = open_file('./Aetherius_API/api_keys/qdrant_api_key.txt')
        client = QdrantClient(url=url, api_key=api_key)
        client.recreate_collection(
            collection_name="Ping",
            vectors_config=VectorParams(size=1, distance=Distance.COSINE),
        )
    except:
        if not os.path.exists("./Qdrant_DB"):
            os.makedirs("./Qdrant_DB")
        client = QdrantClient(path="./Qdrant_DB")
        
        


def timestamp_to_datetime(unix_time):
    datetime_obj = datetime.fromtimestamp(unix_time)
    datetime_str = datetime_obj.strftime("%A, %B %d, %Y at %I:%M%p %Z")
    return datetime_str


async def fetch_html(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()

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
        
        
async def async_chunk_text_from_url(url, username, bot_name, chunk_size=380, overlap=40):
    try:
        print("Scraping given URL, please wait...")
        
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
            with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
            host_data = settings.get('HOST_AetherNode', '').strip()
            embed_size = settings.get('embed_size', '').strip()
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
            # Call wrapped_chunk_from_url and ensure it returns a consistent result format
            result = await wrapped_chunk_from_url(
                host_queue, chunk, collection_name, bot_name, username, client, url
            )
            # Ensure result is a dictionary as expected
            if isinstance(result, dict) and 'url' in result and 'processed_text' in result:
                weblist.append(result['url'] + ' ' + result['processed_text'])
        #        print(result['url'] + '\n' + result.get('semantic_db_term', '') + '\n' + result['processed_text'])
            else:
                print("Error processing chunk: Invalid result format")
            return result
        
        # Use asyncio.gather to run all the coroutines concurrently
        await asyncio.gather(*(process_chunk(chunk) for chunk in chunks))
        
        table = weblist
        return
    except Exception as e:
        print(e)
        traceback.print_exc()
        table = "Error"
        return


async def wrapped_chunk_from_url(host_queue, chunk, collection_name, bot_name, username, client, url):
    try:
        host = await host_queue.get()
        result = await summarized_chunk_from_url(host, chunk, collection_name, bot_name, username, client, url)
        await host_queue.put(host)
        return result if result else {"url": url, "processed_text": "Failed to process chunk"}
    except Exception as e:
        print(e)
        return {"url": url, "processed_text": "Exception occurred"}


async def summarized_chunk_from_url(host, chunk, collection_name, bot_name, username, client, url):
    try:
        weblist = list()
        websum = list()
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        API = settings.get('API', 'AetherNode')
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat')
        LLM_Model = settings.get('LLM_Model', 'AetherNode')
        webyescheck = 'yes'
        if backend_model == "Llama_2_Chat":
            user_input_end = "[/INST]"
            user_input_start = "[INST]"
        if backend_model == "OpenAi":
            user_input_end = ""
            user_input_start = ""
        if backend_model == "Alpaca":
            user_input_start = "\n\n### Instruction:"
            user_input_end = "\n\n### Response:"
        if backend_model == "Vicuna":
            user_input_start = "USER: "
            user_input_end = "ASSISTANT:"
        if backend_model == "ChatML":
            user_input_start = "<|im_end|>\n<|im_start|>user\n"
            user_input_end = "<|im_end|>\n<|im_start|>assistant"
        
        websum.append({'role': 'system', 'content': f"{user_input_start} MAIN SYSTEM PROMPT: You are an ai text summarizer.  Your job is to take the given text from a scraped article, then return the text in a summarized article form.  Do not generalize, rephrase, or add information in your summary, keep the same semantic meaning.  If no article is given, print no article.\n\n\n"})
        websum.append({'role': 'user', 'content': f"SCRAPED ARTICLE: {chunk}\n\nINSTRUCTIONS: Summarize the article without losing any factual data or semantic meaning.  Ensure to maintain full context and information. Only print the truncated article, do not include any additional text or comments. {user_input_end} SUMMARIZER BOT: Sure! Here is the summarized article based on the scraped text: "})
        prompt = ''.join([message_dict['content'] for message_dict in websum])
            
        text = await Webscrape_Call(host, prompt, username, bot_name)
        if text.startswith("Sure! Here is the summarized article based on the scraped text:"):
                # Remove the specified text from the variable
            text = text[len("Sure! Here is the summarized article based on the scraped text:"):]
        if len(text) < 20:
            text = "No Webscrape available"
        #    text = chatgpt35_completion(websum)
        #    paragraphs = text.split('\n\n')  # Split into paragraphs
        #    for paragraph in paragraphs:  # Process each paragraph individually, add a check to see if paragraph contained actual information.
        webcheck = list()
        webcheck.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: You are a sub-agent for an automated webscraping tool. Your task is to decide if the previous Ai sub-agent scraped legible information. The scraped text should contain some form of text, if it does, print 'YES'.  If the webscrape failed or is illegible, print: 'NO'."})
        webcheck.append({'role': 'user', 'content': f"{user_input_start} ORIGINAL TEXT FROM SCRAPE: {chunk} {user_input_end}"})
        webcheck.append({'role': 'user', 'content': f"PROCESSED WEBSCRAPE: {text}\n\n"})
        webcheck.append({'role': 'user', 'content': f"{user_input_start} SYSTEM: You are responding for a Yes or No input field. You are only capible of printing Yes or No. Use the format: [AI AGENT: <'Yes'/'No'>] {user_input_end} "})

        prompt = ''.join([message_dict['content'] for message_dict in webcheck])
        #    webyescheck = agent_oobabooga_webcheckyesno(prompt)
        webyescheck = 'yes'
        if 'no webscrape' in text.lower():
            text = chunk
            print('---------')
            print('Summarization Failed')
            pass
        if 'no article' in text.lower():
            text = chunk
            print('---------')
            print('Summarization Failed')
            pass
        if 'you are a text' in text.lower():
            text = chunk
            print('---------')
            print('Summarization Failed')
            pass
        if 'no summary' in text.lower():
            text = chunk
            print('---------')
            print('Summarization Failed')
            pass  
        if 'i am an ai' in text.lower():
            text = chunk
            print('---------')
            print('Summarization Failed')
            pass                
        else:
            if 'cannot provide a summary of' in text.lower():
                text = chunk
            if 'yes' in webyescheck.lower():
                semanticterm = list()
                semanticterm.append({'role': 'system', 'content': f"{user_input_start} MAIN SYSTEM PROMPT: You are a bot responsible for taging articles with a title for database queries.  Your job is to read the given text, then create a title in question form representative of what the article is about, focusing on its main subject.  The title should be semantically identical to the overview of the article and not include extraneous info.  The article is from the URL: {url}. Use the format: [<TITLE IN QUESTION FORM>].\n\n"})
                semanticterm.append({'role': 'user', 'content': f"ARTICLE: {text}\n\n"})
                semanticterm.append({'role': 'user', 'content': f"SYSTEM: Create a short, single question that encapsulates the semantic meaning of the Article.  Use the format: [<QUESTION TITLE>].  Please only print the title, it will be directly input in front of the article. {user_input_end} ASSISTANT: Sure! Here's the summary of the webscrape: "})
                prompt = ''.join([message_dict['content'] for message_dict in semanticterm])
                semantic_db_term = await Webscrape_Call(host, prompt, username, bot_name)
                if 'cannot provide a summary of' in semantic_db_term.lower():
                    semantic_db_term = 'Tag Censored by Model'
                print('---------')
                weblist.append(url + ' ' + text)
                print(url + '\n' + semantic_db_term + '\n' + text)
                payload = list()
                timestamp = time.time()
                timestring = timestamp_to_datetime(timestamp)
                    # Create the collection only if it doesn't exist
                embed_text = f"{semantic_db_term} - {text}"
                vector1 = embeddings(semantic_db_term + ' ' + text)
                #    embedding = model.encode(query)
                unique_id = str(uuid4())
                point_id = unique_id + str(int(timestamp))
                metadata = {
                    'bot': bot_name,
                    'user': username,
                    'time': timestamp,
                    'source': url,
                    'tag': semantic_db_term,
                    'message': text,
                    'timestring': timestring,
                    'uuid': unique_id,
                    'memory_type': 'Web_Scrape',
                }
                client.upsert(collection_name=collection_name,
                                     points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)]) 
                payload.clear()           
            else:
                print('---------')
                print(f"\n\n\nFAILED ARTICLE: {text}")
                print(f'\nERROR MESSAGE FROM BOT: {webyescheck}\n\n\n')  
        table = weblist
        return {"url": url, "processed_text": text}  # text is the summarized text
    except Exception as e:
        print(e)
        return {"url": url, "processed_text": "Error in summarization"}