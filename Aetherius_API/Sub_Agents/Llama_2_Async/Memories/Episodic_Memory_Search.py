import os
import sys
sys.path.insert(0, './Aetherius_API/resources')
from Llama2_chat_Async import *
import time
from datetime import datetime
from uuid import uuid4
import json
import importlib.util
import requests
import tkinter as tk
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, Range, MatchValue
from qdrant_client.http import models
import asyncio
import aiofiles


def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
       return file.read().strip()


# Check if Qdrant Server is Running
def check_local_server_running():
    try:
        response = requests.get("http://localhost:6333/dashboard/")
        return response.status_code == 200
    except requests.ConnectionError:
        return False

# Connect to Qdrant Server
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


# Import Aetherius's Settings
with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
    settings = json.load(f)
# Set embed size from settings to variable
embed_size = settings['embed_size']





model = SentenceTransformer('all-mpnet-base-v2')


def embeddings(query):
    vector = model.encode([query])[0].tolist()
    return vector

def fail():
  #  print('')
    fail = "Not Needed"
    return fail  
    
    
def timestamp_to_datetime(unix_time):
    datetime_obj = datetime.datetime.fromtimestamp(unix_time)
    datetime_str = datetime_obj.strftime("%A, %B %d, %Y at %I:%M%p %Z")
    return datetime_str


async def search_episodic_db(line_vec, username, bot_name):
    try:
        memories = None
        try:
            hits = client.search(
                collection_name=f"Bot_{bot_name}",
                query_vector=line_vec,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="memory_type",
                            match=MatchValue(value="Episodic")
                        )
                    ]
                ),
                limit=5
            )
                # Print the result
            memories = [hit.payload['message'] for hit in hits]
        except Exception as e:
            if "Not found: Collection" in str(e):
                print("Collection has no memories.")
            else:
                print(f"An unexpected error occurred: {str(e)}")
        return memories
    except Exception as e:
        print(e)
        memories = "Error"
        return memories
        
        
async def search_implicit_db(line_vec, username, bot_name):
    try:
        memories1 = None
        memories2  = None
        try:
            hits = client.search(
                collection_name=f"Bot_{bot_name}",
                query_vector=line_vec,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="memory_type",
                            match=MatchValue(value="Implicit_Long_Term")
                        )
                    ]
                ),
                limit=3
            )
                # Print the result
            memories1 = [hit.payload['message'] for hit in hits]
        except Exception as e:
            if "Not found: Collection" in str(e):
                print("Collection has no memories.")
            else:
                if "Not found: Collection" in str(e):
                    print("Collection has no memories.")
                else:
                    print(f"An unexpected error occurred: {str(e)}")
    
        try:
            hits = client.search(
                collection_name=f"Bot_{bot_name}_Implicit_Short_Term",
                query_vector=line_vec,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="memory_type",
                            match=MatchValue(value="Implicit_Short_Term")
                        )
                    ]
                ),
                limit=5
            )
                # Print the result
            memories2 = [hit.payload['message'] for hit in hits]
        except Exception as e:
            if "Not found: Collection" in str(e):
                print("Collection has no memories.")
            else:
                print(f"An unexpected error occurred: {str(e)}")
            
        memories = f'{memories1}\n{memories2}'    
        return memories
    except Exception as e:
        print(e)
        memories = "Error"
        return memories
        
        
async def search_flashbulb_db(line_vec, username, bot_name):
    try:
        memories = None
        try:
            hits = client.search(
                collection_name=f"Bot_{bot_name}",
                query_vector=line_vec,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="memory_type",
                            match=MatchValue(value="Flashbulb")
                        )
                    ]
                ),
                limit=2
            )
                # Print the result
            memories = [hit.payload['message'] for hit in hits]
        except Exception as e:
            if "Not found: Collection" in str(e):
                print("Collection has no memories.")
            else:
                print(f"An unexpected error occurred: {str(e)}")
        return memories
    except Exception as e:
        print(e)
        memories = "Error"
        return memories 
        
        
async def search_explicit_db(line_vec, username, bot_name):
    try:
        memories1 = None
        memories2 = None
        try:
            hits = client.search(
                collection_name=f"Bot_{bot_name}",
                query_vector=line_vec,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="memory_type",
                            match=MatchValue(value="Explicit_Long_Term")
                        )
                    ]
                ),
                limit=3
            )
                # Print the result
            memories1 = [hit.payload['message'] for hit in hits]
        except Exception as e:
            if "Not found: Collection" in str(e):
                print("Collection has no memories.")
            else:
                print(f"An unexpected error occurred: {str(e)}")
    
        try:
            hits = client.search(
                collection_name=f"Bot_{bot_name}_{username}_Explicit_Short_Term",
                query_vector=line_vec,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="memory_type",
                            match=MatchValue(value="Explicit_Short_Term")
                        )
                    ]
                ),
                limit=5
            )
                # Print the result
            memories2 = [hit.payload['message'] for hit in hits]
        except Exception as e:
            if "Not found: Collection" in str(e):
                print("Collection has no memories.")
            else:
                print(f"An unexpected error occurred: {str(e)}")
        memories = f'{memories1}\n{memories2}'    
        return memories
    except Exception as e:
        print(e)
        memories = "Error"
        return memories
        




# Create a Description for the Module
def Episodic_Memory_Search_Description(username, bot_name):
    description = f"Episodic_Memory_Search.py: A module dedicated to {bot_name}'s simulated Episodic Memories. Episodic memories represent personal experiences tied to specific times and places. For {bot_name}, this means generating responses based on hypothetical past events, not actual history. This isn't for factual validation but to enhance contextually relevant interactions."
    return description
    
    
# Add your custom code Here
async def Episodic_Memory_Search(host, bot_name, username, line, task_counter, output_one, output_two, master_tasklist_output, user_input):
    try:
        async with aiofiles.open('./Aetherius_API/chatbot_settings.json', mode='r', encoding='utf-8') as f:
            settings = json.loads(await f.read())
        embed_size = settings['embed_size']
        Sub_Module_Output = settings.get('Output_Sub_Module', 'False')
        # List used for returning response to main chatbot
        tasklist_completion2 = list()
        conversation = list()
        memcheck  = list()
        memcheck2 = list()
        sub_agent_completion = list()
        sub_agent_completion.append({'role': 'user', 'content': f"TASK: {line} [/INST] "})
        botnameupper = bot_name.upper()
        usernameupper = username.upper()
        task_completion = "Task Failed"
        line_vec = embeddings(line)
        try:
            result = await search_episodic_db(line_vec, username, bot_name)
            conversation.append({'role': 'assistant', 'content': f"MEMORIES: {result}\n\n"})

        except Exception as e:
            print(e)
        conversation.append({'role': 'user', 'content': f"[INST] SYSTEM: Summarize the pertinent information from the given memories related to the given task. Present the summarized data in a single, easy-to-understand paragraph. Do not generalize, expand upon, or use any latent knowledge in your summary, only return a truncated version of previously given information. [/INST] Bot {task_counter}: Sure, here is a short summary combining the relevant information needed to complete the given task: "})
        conversation.append({'role': 'assistant', 'content': f"BOT {task_counter}: Sure, here's an overview of the scraped text: "})
        prompt = ''.join([message_dict['content'] for message_dict in conversation])
        task_completion = await agent_oobabooga_process_line_response(host, prompt, username, bot_name)
        # chatgpt35_completion(conversation),
        conversation.clear()
        sub_agent_completion.append({'role': 'assistant', 'content': f"COMPLETED TASK: {task_completion} [INST] "})
        if Sub_Module_Output == 'True':
            print(line)
            print('-------')
            print(task_completion)
        return sub_agent_completion


    except Exception as e:
        print(f'Failed with error: {e}')
        error = 'ERROR WITH PROCESS LINE FUNCTION'
        return error