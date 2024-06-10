import os
import sys
sys.path.insert(0, './Aetherius_API/resources')
from KoboldCpp import *
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


        
        
async def search_explicit_db(line_vec, extracted_domain, user_id, bot_name):
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
                            match=models.MatchValue(value="Explicit_Long_Term"),
                        ),
                        FieldCondition(
                            key="knowledge_domain",
                            match=MatchValue(value=extracted_domain),
                        ),
                        FieldCondition(
                            key="user",
                            match=models.MatchValue(value=f"{user_id}"),
                        ),
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
                collection_name=f"Bot_{bot_name}_Explicit_Short_Term",
                query_vector=line_vec,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="memory_type",
                            match=models.MatchValue(value="Explicit_Short_Term"),
                        ),
                        FieldCondition(
                            key="user",
                            match=models.MatchValue(value=f"{user_id}"),
                        ),
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
        

def load_format_settings(backend_model):
    file_path = f'./Aetherius_API/Model_Formats/{backend_model}.json'
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            formats = json.load(file)
    else:
        formats = {
            "heuristic_input_start": "",
            "heuristic_input_end": "",
            "system_input_start": "",
            "system_input_end": "",
            "user_input_start": "", 
            "user_input_end": "", 
            "assistant_input_start": "", 
            "assistant_input_end": ""
        }
    return formats       

def set_format_variables(backend_model):
    format_settings = load_format_settings(backend_model)
    heuristic_input_start = format_settings.get("heuristic_input_start", "")
    heuristic_input_end = format_settings.get("heuristic_input_end", "")
    system_input_start = format_settings.get("system_input_start", "")
    system_input_end = format_settings.get("system_input_end", "")
    user_input_start = format_settings.get("user_input_start", "")
    user_input_end = format_settings.get("user_input_end", "")
    assistant_input_start = format_settings.get("assistant_input_start", "")
    assistant_input_end = format_settings.get("assistant_input_end", "")
    return heuristic_input_start, heuristic_input_end, system_input_start, system_input_end, user_input_start, user_input_end, assistant_input_start, assistant_input_end



# Create a Description for the Module
def Explicit_Memory_Search_Description(username, bot_name):
    description = f"Explicit_Memory_Search.py: A module centered on {bot_name}'s simulated Explicit Memories. Explicit memories are conscious recollections of facts and events. In this module, {bot_name} will generate responses that convey clear and deliberate recall of information and occurrences, aiming to facilitate interactions that feel informed and mindful. Note that this is for simulation purposes and not for validating factual accuracy."
    return description
    
    
# Add your custom code Here
async def Explicit_Memory_Search(host, bot_name, username, user_id, line, task_counter, output_one, output_two, master_tasklist_output, user_input):
    try:
        async with aiofiles.open('./Aetherius_API/chatbot_settings.json', mode='r', encoding='utf-8') as f:
            settings = json.loads(await f.read())
        embed_size = settings['embed_size']
        Sub_Module_Output = settings.get('Output_Sub_Module', 'False')
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat')
        heuristic_input_start, heuristic_input_end, system_input_start, system_input_end, user_input_start, user_input_end, assistant_input_start, assistant_input_end = set_format_variables(backend_model)
        # List used for returning response to main chatbot
        tasklist_completion2 = list()
        conversation = list()
        memcheck  = list()
        memcheck2 = list()
        sub_agent_completion = list()
        domain_extraction = list()
        
        sub_agent_completion.append({'role': 'user', 'content': f"TASK: {line} [/INST] "})
        botnameupper = bot_name.upper()
        usernameupper = username.upper()
        task_completion = "Task Failed"
        line_vec = embeddings(line)
        
       
        
        
        domain_extraction.append({'role': 'system', 'content': f"You are a knowledge domain extractor.  Your task is to analyze the user's inquiry, then choose the single most salent generalized knowledge domain needed to complete the user's inquiry from the list of existing domains.  Your response should only contain the single existing knowledge domain."})
        domain_extraction.append({'role': 'user', 'content': f"USER INPUT: {line}"})
        
    #    prompt = ''.join([message_dict['content'] for message_dict in domain_extraction])
        extracted_domain = await Domain_Selection_Call(domain_extraction, username, bot_name)
        if ":" in extracted_domain:
            extracted_domain = extracted_domain.split(":")[-1]
            extracted_domain = extracted_domain.replace("\n", "")
            extracted_domain = extracted_domain.upper()
        domain_extraction.clear()
        
        
        vector1 = embeddings(extracted_domain)
        try:
            hits = client.search(
                collection_name=f"Bot_{bot_name}_Knowledge_Domains",
                query_vector=vector1,
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
            domain_search = [hit.payload['knowledge_domain'] for hit in hits]
            print(f"Knowledge Domains: {domain_search}")
        except Exception as e:
            if "Not found: Collection" in str(e):
                print("Collection does not exist.")
                domain_search = "No Collection"
            else:
                print(f"An unexpected error occurred: {str(e)}")
        
        domain_extraction.append({'role': 'system', 'content': f"You are a knowledge domain selector.  Your task is to analyze the user's inquiry, then choose the single most salent generalized knowledge domain from the given list needed to complete the user's inquiry.  Your response should only contain the single existing knowledge domain."})
        domain_extraction.append({'role': 'user', 'content': f"Please return the existing knowledge domains."})
        domain_extraction.append({'role': 'assistant', 'content': f"EXISTING KNOWLEGE DOMAINS: {domain_search}"})

        domain_extraction.append({'role': 'user', 'content': f"USER INPUT: {line} "})
        
    #    prompt = ''.join([message_dict['content'] for message_dict in domain_extraction])
        extracted_domain = await Domain_Selection_Call(domain_extraction, username, bot_name)
        if ":" in extracted_domain:
            extracted_domain = extracted_domain.split(":")[-1]
            extracted_domain = extracted_domain.replace("\n", "")
            extracted_domain = extracted_domain.upper()
        print(f"Extracted Domain: {extracted_domain}")

        
        try:
            result = await search_explicit_db(line_vec, extracted_domain, user_id, bot_name)
            conversation.append({'role': 'assistant', 'content': f"MEMORIES: {result}\n\n"})

        except Exception as e:
            print(e)
        conversation.append({'role': 'user', 'content': f"SYSTEM: Summarize the pertinent information from the given memories related to the given task. Present the summarized data in a single, easy-to-understand paragraph. Do not generalize, expand upon, or use any latent knowledge in your summary, only return a truncated version of previously given information."})
        conversation.append({'role': 'assistant', 'content': f"BOT {task_counter}: Sure, here's an overview of the scraped text: "})
   #     prompt = ''.join([message_dict['content'] for message_dict in conversation])
        task_completion = await Agent_Process_Line_Response_Call(host, conversation, username, bot_name)
        # chatgpt35_completion(conversation),
        conversation.clear()
        sub_agent_completion.append({'role': 'assistant', 'content': f"COMPLETED TASK: {task_completion} {user_input_start} "})
        if Sub_Module_Output == 'True':
            print(line)
            print('-------')
            print(task_completion)
        return sub_agent_completion


    except Exception as e:
        print(f'Failed with error: {e}')
        error = 'ERROR WITH PROCESS LINE FUNCTION'
        return error