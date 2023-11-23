import sys
sys.path.insert(0, './Aetherius_API/resources')
import os
import json
import time
import datetime as dt
from datetime import datetime
from uuid import uuid4
import importlib.util
from importlib.util import spec_from_file_location, module_from_spec
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import requests
import shutil
from qdrant_client import QdrantClient
from qdrant_client.models import (Distance, VectorParams, PointStruct, Filter, FieldCondition, 
                                 Range, MatchValue)
from qdrant_client.http import models
import numpy as np
import re
import subprocess
import keyboard
import pandas as pd
from queue import Queue
import traceback
import asyncio
import aiofiles
import aiohttp
from bs4 import BeautifulSoup


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

        
        
# Import Utility Functions.
def get_script_path_from_file(json_path, key, base_folder='./Aetherius_API/Utilities/'):
    with open(json_path, 'r', encoding='utf-8') as file:
        settings = json.load(file)
    script_name = settings.get(key, "").strip()
    return f'{base_folder}{script_name}.py'

# Path to the JSON settings file
json_file_path = './Aetherius_API/chatbot_settings.json'

# Import for embedding model
script_path1 = get_script_path_from_file(json_file_path, "Embeddings")
import_functions_from_script(script_path1, "embedding_module")

script_path2 = get_script_path_from_file(json_file_path, "TTS")
import_functions_from_script(script_path2, "TTS_module")


# Import for model
script_path3 = get_script_path_from_file(json_file_path, "LLM_Model", base_folder='./Aetherius_API/resources/')
import_functions_from_script(script_path3, "model_module")


with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
    settings = json.load(f)
select_api = settings.get('API', 'Oobabooga')

if select_api == "Oobabooga":
    script_path4 = get_script_path_from_file(json_file_path, "Vision_Model", base_folder='./Aetherius_API/Tools/Llama_2_Async/')
if select_api == "AetherNode":
    script_path4 = get_script_path_from_file(json_file_path, "Vision_Model", base_folder='./Aetherius_API/Tools/AetherNode_Llama_2/')
if select_api == "Open_Ai":
    script_path4 = get_script_path_from_file(json_file_path, "Vision_Model", base_folder='./Aetherius_API/Tools/Open_Ai/')
import_functions_from_script(script_path4, "eyes_module")








async def read_prompts_from_json(json_file_path):
    with open(json_file_path, 'r') as file:
        prompts = json.load(file)
    return prompts
    
    
def timestamp_to_datetime(unix_time):
    datetime_obj = datetime.datetime.fromtimestamp(unix_time)
    datetime_str = datetime_obj.strftime("%A, %B %d, %Y at %I:%M%p %Z")
    return datetime_str
    
    
# Running Conversation List
class MainConversation:
    def __init__(self, username, user_id, bot_name, max_entries, prompt, greeting):
        botnameupper = bot_name.upper()
        usernameupper = username.upper()
        self.max_entries = int(max_entries)
        self.file_path = f'./history/{user_id}/{bot_name}_main_conversation_history.json'
        self.file_path2 = f'./history/{user_id}/{bot_name}_main_history.json'
        self.main_conversation = [prompt, greeting]
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.running_conversation = data.get('running_conversation', [])
        else:
            self.running_conversation = []
            self.save_to_file()

    def append(self, timestring, username, usernameupper, user_input, bot_name, botnameupper, response_two):
        entry = []
        entry.append(f"{usernameupper}: [{timestring}] - {user_input}")
        entry.append(f"{botnameupper}: {response_two}")
        self.running_conversation.append("\n\n".join(entry))
        while len(self.running_conversation) > self.max_entries:
            self.running_conversation.pop(0)
        self.save_to_file()

    def save_to_file(self):
        history = self.main_conversation + self.running_conversation

        data_to_save = {
            'main_conversation': self.main_conversation,
            'running_conversation': self.running_conversation
        }

        data_to_save2 = {
            'history': [{'visible': entry} for entry in history]
        }
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=4)
        with open(self.file_path2, 'w', encoding='utf-8') as f:
            json.dump(data_to_save2, f, indent=4)
    def get_conversation_history(self):
        if not os.path.exists(self.file_path) or not os.path.exists(self.file_path2):
            self.save_to_file()
        return self.main_conversation + ["\n\n".join(entry.split("\n\n")) for entry in self.running_conversation]
        
    def get_last_entry(self):
        if self.running_conversation:
            return self.running_conversation[-1]
        else:
            return None
            
            
async def Aetherius_Chatbot(user_input, username, user_id, bot_name, image_path=None):
    tasklist = list()
    inner_monologue = list()
    intuition = list()
    implicit_memory = list()
    response = list()
    explicit_memory = list()
    payload = list()
    input_expansion = list()
    domain_extraction = list()
    counter = 0
    counter2 = 0
    mem_counter = 0
    with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
    API = settings.get('API', 'AetherNode')
    if API == "Oobabooga":
        HOST = settings.get('HOST_Oobabooga', 'http://localhost:5000/api')
    if API == "AetherNode":
        HOST = settings.get('HOST_AetherNode', 'http://127.0.0.1:8000')
    External_Research_Search = settings.get('Search_External_Resource_DB', 'False')
    conv_length = settings.get('Conversation_Length', '3')
    Web_Search = settings.get('Search_Web', 'False')
    Inner_Monologue_Output = settings.get('Output_Inner_Monologue', 'True')
    Intuition_Output = settings.get('Output_Intuition', 'False')
    Response_Output = settings.get('Output_Response', 'True')
    DB_Search_Output = settings.get('Output_DB_Search', 'False')
    memory_mode = settings.get('Memory_Mode', 'Forced')
    Update_Bot_Personality_Description = settings.get('Update_Bot_Personality_Description', 'False')
    Update_User_Personality_Description = settings.get('Update_User_Personality_Description', 'False')
    Use_Bot_Personality_Description = settings.get('Use_Bot_Personality_Description', 'False')
    Use_User_Personality_Description = settings.get('Use_User_Personality_Description', 'False')
    backend_model = settings.get('Model_Backend', 'Llama_2')
    LLM_Model = settings.get('LLM_Model', 'Llama_2')
    botnameupper = bot_name.upper()
    usernameupper = username.upper()
    if backend_model == "Llama_2":
        user_input_end = "[/INST]"
        user_input_start = "[INST]"
    if backend_model == "Open_Ai":
        user_input_end = ""
        user_input_start = ""
    base_path = "./Aetherius_API/Chatbot_Prompts"
    base_prompts_path = os.path.join(base_path, "Base")
    user_bot_path = os.path.join(base_path, user_id, bot_name)  
    if not os.path.exists(user_bot_path):
        os.makedirs(user_bot_path)
    prompts_json_path = os.path.join(user_bot_path, "prompts.json")
    base_prompts_json_path = os.path.join(base_prompts_path, "prompts.json")
    if not os.path.exists(prompts_json_path) and os.path.exists(base_prompts_json_path):
        async with aiofiles.open(base_prompts_json_path, 'r') as base_file:
            base_prompts_content = await base_file.read()
        async with aiofiles.open(prompts_json_path, 'w') as user_file:
            await user_file.write(base_prompts_content)
    async with aiofiles.open(prompts_json_path, 'r') as file:
        prompts = json.loads(await file.read())
    main_prompt = prompts["main_prompt"].replace('<<NAME>>', bot_name)
    secondary_prompt = prompts["secondary_prompt"]
    greeting_msg = prompts["greeting_prompt"].replace('<<NAME>>', bot_name)
    main_conversation = MainConversation(username, user_id, bot_name, conv_length, main_prompt, greeting_msg)
    while True:
        print(f"\n\n{username}: {user_input}")
        conversation_history = main_conversation.get_conversation_history()
        con_hist = '\n'.join(conversation_history)
        timestamp = time()
        timestring = timestamp_to_datetime(timestamp)
        input_2 = None
        if len(user_input) > 2:
            input_2 = user_input
        if image_path is not None:
            user_input = gpt_vision(user_input, image_path)
            if input_2 is not None and len(input_2) > 2:
                user_input = f"VISION: {user_input}\nORIGINAL USER INQUIRY: {input_2}"
        
        input_expansion.append({'role': 'user', 'content': f"PREVIOUS CONVERSATION HISTORY: {con_hist}\n\n\n"})
        input_expansion.append({'role': 'system', 'content': f"You are a task rephraser. Your primary task is to rephrase the user's most recent input succinctly and accurately. Please return the rephrased version of the user’s most recent input. USER'S MOST RECENT INPUT: {user_input} {user_input_end}"})
        input_expansion.append({'role': 'assistant', 'content': f"TASK REPHRASER: Sure! Here's the rephrased version of the user's most recent input: "})
    #    print(input_expansion)
        
        if backend_model == "Open_Ai":
            expanded_input = Input_Expansion_Call(input_expansion, username, bot_name)

        if backend_model == "Llama_2":
            prompt = ''.join([message_dict['content'] for message_dict in input_expansion])
            expanded_input = await Input_Expansion_Call(prompt, username, bot_name)
        print(f"\n\nExpanded User Input: {expanded_input}")
        

        
        
        domain_extraction.append({'role': 'system', 'content': f"You are a knowledge domain extractor.  Your task is to analyze the user's inquiry, then choose the single most salent generalized knowledge domain needed to complete the user's inquiry from the list of existing domains.  Your response should only contain the single existing knowledge domain.\n"})
        domain_extraction.append({'role': 'user', 'content': f"USER INPUT: {expanded_input} {user_input_end} "})
        
        if backend_model == "Llama_2":
            prompt = ''.join([message_dict['content'] for message_dict in domain_extraction])
            extracted_domain = await Domain_Extraction_Call(prompt, username, bot_name)
            
        if backend_model == "Open_Ai":
            extracted_domain = Domain_Extraction_Call(domain_extraction, username, bot_name)
            
        domain_extraction.clear()
            
        if ":" in extracted_domain:
            extracted_domain = extracted_domain.split(":")[-1]
            extracted_domain = extracted_domain.replace("\n", "")
            extracted_domain = extracted_domain.upper()
            extracted_domain = re.sub(r'[^A-Z]', '', extracted_domain)
            extracted_domain = extracted_domain.replace("_", " ")
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
                limit=25
            )
            domain_search = [hit.payload['knowledge_domain'] for hit in hits]
        except Exception as e:
            if "Not found: Collection" in str(e):
                print("\nCollection does not exist.")
                domain_search = "No Collection"
            else:
                print(f"\nAn unexpected error occurred: {str(e)}")
                domain_search = "No Collection"
                
                
        def remove_duplicate_dicts(input_list):
            output_list = []
            for item in input_list:
                if item not in output_list:
                    output_list.append(item)
            return output_list
        domain_search = remove_duplicate_dicts(domain_search)
        print(f"\nKnowledge Domains: {domain_search}")
        
        
        domain_extraction.append({'role': 'system', 'content': f"{user_input_start} Your role as a Knowledge Domain Selector is to analyze the user's question and identify the most relevant knowledge domain from the provided list. Ensure that your choice is from the existing domains, and avoid creating or using any not listed. Respond with the name of the single selected knowledge domain.\n"})
        domain_extraction.append({'role': 'user', 'content': f"Could you provide the current list of knowledge domains? {user_input_end}"})
        domain_extraction.append({'role': 'assistant', 'content': f"CURRENT KNOWLEDGE DOMAINS: {domain_search}"})
        domain_extraction.append({'role': 'user', 'content': f"USER QUESTION: {user_input}\nADDITIONAL CONTEXT: {expanded_input} {user_input_end}"})
        domain_extraction.append({'role': 'assistant', 'content': f"EXTRACTED KNOWLEDGE DOMAIN: "})

        if backend_model == "Llama_2":
            prompt = ''.join([message_dict['content'] for message_dict in domain_extraction])
            extracted_domain = await Domain_Extraction_Call(prompt, username, bot_name)
            
        if backend_model == "Open_Ai":
            extracted_domain = Domain_Extraction_Call(domain_extraction, username, bot_name)
            
            
            
        if ":" in extracted_domain:
            extracted_domain = extracted_domain.split(":")[-1]
            extracted_domain = extracted_domain.replace("\n", "")
        extracted_domain = extracted_domain.upper()
        extracted_domain = re.sub(r'[^A-Z]', '', extracted_domain)
        extracted_domain = extracted_domain.replace("_", " ")
        print(f"Extracted Domain: {extracted_domain}")
        conversation_history = main_conversation.get_last_entry()
        con_hist = f'{conversation_history}'
        vector_input = embeddings(expanded_input)
        
        
        
        tasklist.append({'role': 'system', 'content': f"SYSTEM: You are a search query corrdinator. Your role is to interpret the original user query and generate 2-4 synonymous search terms that will guide the exploration of the chatbot's memory database. Each alternative term should reflect the essence of the user's initial search input. Please list your results using bullet point format.\n"})
        tasklist.append({'role': 'user', 'content': f"USER: {user_input}\nUse the format: •Search Query {user_input_end} "})
        tasklist.append({'role': 'assistant', 'content': f"ASSISTANT: Sure, I'd be happy to help! Here are 2-4 synonymous search terms: "})
        
        if backend_model == "Llama_2":
            prompt = ''.join([message_dict['content'] for message_dict in tasklist])
            tasklist_output = await Semantic_Terms_Call(prompt, username, bot_name)
        
        if backend_model == "Open_Ai":
            tasklist_output = Semantic_Terms_Call(tasklist, username, bot_name)
        
        
        
        lines = tasklist_output.splitlines()
        tasklist_counter = 0
        tasklist_counter2 = 0
        
        
        inner_monologue.append({'role': 'system', 'content': f"{main_prompt}"})


        # Load Bot Personality Description
        if Use_Bot_Personality_Description == 'True':
            try:
                file_path = f"./Chatbot_Personalities/{bot_name}/{user_id}/{bot_name}_personality_file.txt"
                if not os.path.exists(file_path):
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    default_prompts = f"{main_prompt}\n{secondary_prompt}\n{greeting_msg}"
                    async def write_prompts():
                        try:
                            async with aiofiles.open(file_path, 'w') as txt_file:
                                await txt_file.write(default_prompts)
                        except Exception as e:
                            print(f"\nFailed to write to file: {e}")
                    await write_prompts()
                try:
                    async with aiofiles.open(file_path, mode='r') as file:
                        personality_file = await file.read()
                except FileNotFoundError:
                    personality_file = "File not found."

                try:
                    async with aiofiles.open(file_path, mode='r', encoding='utf-8') as file:
                        file_content = await file.readlines()
                except FileNotFoundError:
                    print(f"No such file or directory: '{file_path}'")
                    return None
                except IOError:
                    print("An I/O error occurred while handling the file")
                    return None
                else:
                    bot_personality = [line.strip() for line in file_content]
                inner_monologue.append({'role': 'assistant', 'content': f"{botnameupper}'S PERSONALITY DESCRIPTION: {bot_personality}\n\n"})
            except:
                pass
                
                
                
        inner_monologue.append({'role': 'user', 'content': f"Now return your most relevant memories: {user_input_end}"})
        inner_monologue.append({'role': 'assistant', 'content': f"{botnameupper}'S LONG TERM CHATBOT MEMORIES: "})
        
        
        intuition.append({'role': 'system', 'content': f"{main_prompt}"})
        
        
        # Load User Personality Description
        if Use_User_Personality_Description == 'True':
            try:
                file_path = f"./Chatbot_Personalities/{bot_name}/{user_id}/{username}_personality_file.txt"
                if not os.path.exists(file_path):
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    default_prompts = f"The user {user_id} does not yet have a personality file."

                    async def write_prompts():
                        try:
                            async with aiofiles.open(file_path, 'w') as txt_file:
                                await txt_file.write(default_prompts)
                        except Exception as e:
                            print(f"Failed to write to file: {e}")
                    await write_prompts()
                try:
                    async with aiofiles.open(file_path, mode='r') as file:
                        personality_file = await file.read()
                except FileNotFoundError:
                    personality_file = "File not found."
                try:
                    async with aiofiles.open(file_path, mode='r', encoding='utf-8') as file:
                        file_content = await file.readlines()
                except FileNotFoundError:
                    print(f"No such file or directory: '{file_path}'")
                    return None
                except IOError:
                    print("An I/O error occurred while handling the file")
                    return None
                else:
                    user_personality = [line.strip() for line in file_content]
                intuition.append({'role': 'user', 'content': f"{usernameupper}'S PERSONALITY DESCRIPTION: {user_personality}\n\n"})
            except:
                pass
                
                
        intuition.append({'role': 'user', 'content': f"Now return your most relevant memories: {user_input_end}"})
        intuition.append({'role': 'assistant', 'content': f"{botnameupper}'S LONG TERM CHATBOT MEMORIES: "})
        
        
        temp_list = list()
        temp_list2 = list()
        for line in lines:
            if line.startswith("•"):
                try:
                    hits = client.search(
                        collection_name=f"Bot_{bot_name}",
                        query_vector=vector_input,
                        query_filter=Filter(
                            must=[
                                FieldCondition(
                                    key="memory_type",
                                    match=MatchValue(value="Explicit_Long_Term"),
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
                        limit=5
                    )
                    unsorted_table = [(hit.payload['timestring'], hit.payload['message']) for hit in hits]
                    sorted_table = sorted(unsorted_table, key=lambda x: x[0])  # Sort by the 'timestring' field
                    db_search_1 = "\n".join([f"{message}" for timestring, message in sorted_table])
                    temp_list.append({'role': 'assistant', 'content': f"{db_search_1}  "})
                    if tasklist_counter < 4:
                        temp_list2.append({'role': 'assistant', 'content': f"{db_search_1}  "})
                    tasklist_counter + 1
                    if DB_Search_Output == 'True':
                        print(db_search_1)
                except Exception as e:
                    if DB_Search_Output == 'True':
                        if "Not found: Collection" in str(e):
                            print("\nCollection does not exist.")
                        else:
                            print(f"\nAn unexpected error occurred: {str(e)}")
        
                try:
                    hits = client.search(
                        collection_name=f"Bot_{bot_name}",
                        query_vector=vector_input,
                        query_filter=Filter(
                            must=[
                                FieldCondition(
                                    key="memory_type",
                                    match=MatchValue(value="Implicit_Long_Term"),
                                ),
                                FieldCondition(
                                    key="user",
                                    match=models.MatchValue(value=f"{user_id}"),
                                ),
                            ]
                        ),
                        limit=6
                    )
                    unsorted_table = [(hit.payload['timestring'], hit.payload['message']) for hit in hits]
                    sorted_table = sorted(unsorted_table, key=lambda x: x[0])  # Sort by the 'timestring' field
                    db_search_2 = "\n".join([f"{message}" for timestring, message in sorted_table])
                    temp_list.append({'role': 'assistant', 'content': f"{db_search_2}  "})
                    if tasklist_counter2 < 4:
                        temp_list2.append({'role': 'assistant', 'content': f"{db_search_2}  "})
                    tasklist_counter2 + 1
                    if DB_Search_Output == 'True':
                        print(f"\n\n{db_search_2}")
                except Exception as e:
                    if DB_Search_Output == 'True':
                        if "Not found: Collection" in str(e):
                            print("\nCollection does not exist.")
                        else:
                            print(f"\nAn unexpected error occurred: {str(e)}")
                            
                def remove_duplicate_dicts(input_list):
                    output_list = []
                    for item in input_list:
                        if item not in output_list:
                            output_list.append(item)
                    return output_list

                temp_list = remove_duplicate_dicts(temp_list)
                temp_list2 = remove_duplicate_dicts(temp_list2)
        inner_monologue.append({'role': 'system', 'content': f"{temp_list}"})       
        intuition.append({'role': 'system', 'content': f"{temp_list2}"})                    
        db_search_3, db_search_4, db_search_5, db_search_6 = None, None, None, None
        
        try:
            hits = client.search(
                collection_name=f"Bot_{bot_name}",
                query_vector=vector_input,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="memory_type",
                            match=MatchValue(value="Episodic"),
                        ),
                        FieldCondition(
                            key="user",
                            match=models.MatchValue(value=f"{user_id}"),
                        ),
                    ]
                ),
                limit=6
            )
            unsorted_table = [(hit.payload['timestring'], hit.payload['message']) for hit in hits]
            sorted_table = sorted(unsorted_table, key=lambda x: x[0])  # Sort by the 'timestring' field
            db_search_3 = "\n".join([f"{message}" for timestring, message in sorted_table])
            if DB_Search_Output == 'True':
                print(db_search_3)
        except Exception as e:
            if DB_Search_Output == 'True':
                if "Not found: Collection" in str(e):
                    print("Collection does not exist.")
                else:
                    print(f"An unexpected error occurred: {str(e)}")
                    
        try:
            hits = client.search(
                collection_name=f"Bot_{bot_name}_Explicit_Short_Term",
                query_vector=vector_input,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="memory_type",
                            match=MatchValue(value="Explicit_Short_Term"),
                        ),
                        FieldCondition(
                            key="user",
                            match=models.MatchValue(value=f"{user_id}"),
                        ),
                    ]
                ),
                limit=4
            )
            unsorted_table = [(hit.payload['timestring'], hit.payload['message']) for hit in hits]
            sorted_table = sorted(unsorted_table, key=lambda x: x[0])  # Sort by the 'timestring' field
            explicit_short = "\n".join([f"{message}" for timestring, message in sorted_table])
            if DB_Search_Output == 'True':
                print(explicit_short)
        except Exception as e:
            explicit_short = "No Memories"
            if DB_Search_Output == 'True':
                if "Not found: Collection" in str(e):
                    print("Collection does not exist.")
                else:
                    print(f"An unexpected error occurred: {str(e)}")
                    
        try:
            hits = client.search(
                collection_name=f"Bot_{bot_name}_Implicit_Short_Term",
                query_vector=vector_input,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="memory_type",
                            match=MatchValue(value="Implicit_Short_Term"),
                        ),
                        FieldCondition(
                            key="user",
                            match=models.MatchValue(value=f"{user_id}"),
                        ),
                    ]
                ),
                limit=3
            )
            unsorted_table = [(hit.payload['timestring'], hit.payload['message']) for hit in hits]
            sorted_table = sorted(unsorted_table, key=lambda x: x[0])  # Sort by the 'timestring' field
            implicit_short = "\n".join([f"{message}" for timestring, message in sorted_table])
            if DB_Search_Output == 'True':
                print(f"\n\nIMPLICIT SHORT TERM MEMORIES:\n{implicit_short}")
        except Exception as e:
            implicit_short = "No Memories"
            if DB_Search_Output == 'True':
                if "Not found: Collection" in str(e):
                    print("\nCollection does not exist.")
                else:
                    print(f"\nAn unexpected error occurred: {str(e)}")
                    
        db_search_4 = f"{implicit_short}\n{explicit_short}"
        
        try:
            hits = client.search(
                collection_name=f"Bot_{bot_name}",
                query_vector=vector_input,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="memory_type",
                            match=MatchValue(value="Flashbulb"),
                        ),
                        FieldCondition(
                            key="user",
                            match=models.MatchValue(value=f"{user_id}"),
                        ),
                    ]
                ),
                limit=2
            )
            unsorted_table = [(hit.payload['timestring'], hit.payload['message']) for hit in hits]
            sorted_table = sorted(unsorted_table, key=lambda x: x[0])  # Sort by the 'timestring' field
            db_search_5 = "\n".join([f"{message}" for timestring, message in sorted_table])
            if DB_Search_Output == 'True':
                print(f"FLASHBULB MEMORIES:\n{db_search_5}")
        except Exception as e:
            if DB_Search_Output == 'True':
                if "Not found: Collection" in str(e):
                    print("\nCollection does not exist.")
                else:
                    print(f"\nAn unexpected error occurred: {str(e)}")
                          
        try:
            hits = client.search(
                collection_name=f"Bot_{bot_name}",
                query_vector=vector_input,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="memory_type",
                            match=MatchValue(value="Heuristics"),
                        ),
                        FieldCondition(
                            key="user",
                            match=models.MatchValue(value=f"{user_id}"),
                        ),
                    ]
                ),
                limit=5
            )
            unsorted_table = [(hit.payload['timestring'], hit.payload['message']) for hit in hits]
            sorted_table = sorted(unsorted_table, key=lambda x: x[0])  # Sort by the 'timestring' field
            db_search_6 = "\n".join([f"{message}" for timestring, message in sorted_table])
            if DB_Search_Output == 'True':
                print(db_search_6)
        except Exception as e:
            if DB_Search_Output == 'True':
                if "Not found: Collection" in str(e):
                    print("Collection does not exist.")
                else:
                    print(f"An unexpected error occurred: {str(e)}")
                       
        if External_Research_Search == 'True':
            try:
                hits = client.search(
                    collection_name=f"Bot_{bot_name}_External_Knowledgebase",
                    query_vector=vector_input,
                    query_filter=Filter(
                        must=[
                            FieldCondition(
                                key="user",
                                match=models.MatchValue(value=f"{user_id}"),
                            ),
                        ]
                    ),
                    limit=5
                )
                inner_web = [hit.payload['message'] for hit in hits]
                if DB_Search_Output == 'True':
                    print(inner_web)
            except Exception as e:
                if DB_Search_Output == 'True':
                    if "Not found: Collection" in str(e):
                        print("Collection does not exist.")
                    else:
                        print(f"An unexpected error occurred: {str(e)}")
                        
                        
                        
        inner_monologue.append({'role': 'assistant', 'content': f"{botnameupper}'S EPISODIC MEMORIES: {db_search_3}\n{db_search_5}\n{botnameupper}'S SHORT-TERM MEMORIES: {db_search_4}\n{botnameupper}'s HEURISTICS: {db_search_6} {user_input_start} Now return and analyze the current conversation history. {user_input_end} CURRENT CONVERSATION HISTORY: {con_hist} "})
        inner_monologue.append({'role': 'user', 'content': f"{user_input_start} SYSTEM: Compose a short silent soliloquy to serve as {bot_name}'s internal monologue/narrative.  Ensure it includes {bot_name}'s contemplations in relation to {username}'s request and does not exceed a paragraph in length.\n{usernameupper}/USER'S REQUEST: {user_input} {user_input_end} "})
        inner_monologue.append({'role': 'assistant', 'content': f"{botnameupper}: "})
        
        if backend_model == "Llama_2":
            prompt = ''.join([message_dict['content'] for message_dict in inner_monologue])
            output_one = await Inner_Monologue_Call(prompt, username, bot_name)
        
        if backend_model == "Open_Ai":
            output_one = Inner_Monologue_Call(inner_monologue, username, bot_name)
        
       
        
        
        bot_monologue_pattern = re.compile(rf"^{re.escape(bot_name)}[\s:-]+", re.IGNORECASE)

        output_one = output_one.strip()
        match = bot_monologue_pattern.search(output_one)
        if match:
            output_one = output_one[match.end():]

        sentences = re.split(r'(?<=[.!?])\s+', output_one)
        if sentences and not re.search(r'[.!?]$', sentences[-1]):
            sentences.pop()
        output_one = ' '.join(sentences)
        
        
        
        
        
        
        
        inner_output = (f'{output_one}\n\n')
        paragraph = output_one
        if Inner_Monologue_Output == 'True':
            print('\n\nINNER_MONOLOGUE: %s' % output_one)
        inner_monologue.clear()
        
        vector_monologue = embeddings(output_one)
        db_search_7, db_search_8, db_search_9, db_search_10 = None, None, None, None
        
        try:
            hits = client.search(
                collection_name=f"Bot_{bot_name}",
                query_vector=vector_monologue,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="memory_type",
                            match=MatchValue(value="Episodic"),
                        ),
                        FieldCondition(
                            key="user",
                            match=models.MatchValue(value=f"{user_id}"),
                        ),
                    ]
                ),
                limit=3
            )
            unsorted_table = [(hit.payload['timestring'], hit.payload['message']) for hit in hits]
            sorted_table = sorted(unsorted_table, key=lambda x: x[0])  # Sort by the 'timestring' field
            db_search_7 = "\n".join([f"{message}" for timestring, message in sorted_table])
            if DB_Search_Output == 'True':
                print(f"\n\nEPISODIC:\n{db_search_7}")
        except Exception as e:
            if DB_Search_Output == 'True':
                if "Not found: Collection" in str(e):
                    print("\nCollection does not exist.")
                else:
                     print(f"\nAn unexpected error occurred: {str(e)}")
                       
        try:
            hits = client.search(
                collection_name=f"Bot_{bot_name}_Explicit_Short_Term",
                query_vector=vector_monologue,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="memory_type",
                            match=MatchValue(value="Explicit_Short_Term"),
                        ),
                        FieldCondition(
                            key="user",
                            match=models.MatchValue(value=f"{user_id}"),
                        ),
                    ]
                ),
                limit=3
            )
            unsorted_table = [(hit.payload['timestring'], hit.payload['message']) for hit in hits]
            sorted_table = sorted(unsorted_table, key=lambda x: x[0])  # Sort by the 'timestring' field
            db_search_8 = "\n".join([f"{message}" for timestring, message in sorted_table])
            if DB_Search_Output == 'True':
                print(f"\n\nEXPLICIT SHORT TERM:\n{db_search_8}")
        except Exception as e:
            if DB_Search_Output == 'True':
                if "Not found: Collection" in str(e):
                    print("\nCollection does not exist.")
                else:
                    print(f"\nAn unexpected error occurred: {str(e)}")
                      
        try:
            hits = client.search(
                collection_name=f"Bot_{bot_name}",
                query_vector=vector_monologue,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="memory_type",
                            match=MatchValue(value="Flashbulb"),
                        ),
                        FieldCondition(
                            key="user",
                            match=models.MatchValue(value=f"{user_id}"),
                        ),
                    ]
                ),
                limit=2
            )
            unsorted_table = [(hit.payload['timestring'], hit.payload['message']) for hit in hits]
            sorted_table = sorted(unsorted_table, key=lambda x: x[0])  # Sort by the 'timestring' field
            db_search_9 = "\n".join([f"{message}" for timestring, message in sorted_table])
            if DB_Search_Output == 'True':
                print(f"\n\nFLASHBULB:\n{db_search_9}")
        except Exception as e:
            if DB_Search_Output == 'True':
                if "Not found: Collection" in str(e):
                    print("Collection does not exist.")
                else:
                    print(f"An unexpected error occurred: {str(e)}")
                    
        try:
            hits = client.search(
                collection_name=f"Bot_{bot_name}",
                query_vector=vector_monologue,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="memory_type",
                            match=MatchValue(value="Heuristics"),
                        ),
                        FieldCondition(
                            key="user",
                            match=models.MatchValue(value=f"{user_id}"),
                        ),
                    ]
                ),
                limit=5
            )
            unsorted_table = [(hit.payload['timestring'], hit.payload['message']) for hit in hits]
            sorted_table = sorted(unsorted_table, key=lambda x: x[0])  # Sort by the 'timestring' field
            db_search_10 = "\n".join([f"{message}" for timestring, message in sorted_table])
            if DB_Search_Output == 'True':
                print(f"\n\nHEURISTICS:\n{db_search_10}")
        except Exception as e:
            if DB_Search_Output == 'True':
                if "Not found: Collection" in str(e):
                    print("\nCollection does not exist.")
                else:
                    print(f"\nAn unexpected error occurred: {str(e)}")
                    

   
        # # Intuition Generation
        intuition.append({'role': 'assistant', 'content': f"{botnameupper}'S FLASHBULB MEMORIES: {db_search_9}\n{botnameupper}'S EXPLICIT MEMORIES: {db_search_8}\n{botnameupper}'s HEURISTICS: {db_search_10}\n{botnameupper}'S INNER THOUGHTS: {output_one}\n{botnameupper}'S EPISODIC MEMORIES: {db_search_7} {user_input_start} Now return and analyze the previous conversation history. {user_input_end} PREVIOUS CONVERSATION HISTORY: {con_hist} "})
        intuition.append({'role': 'user', 'content': f"{user_input_start} SYSTEM: Using syllogistic reasoning, transmute the user, {username}'s message as {bot_name} by devising a truncated predictive action plan in the third person point of view on how to best respond to {username}'s most recent message. You do not have access to external resources.  If the user's message is casual conversation, print 'No Plan Needed'. Only create a syllogistic action plan for informational requests or if requested to complete a complex task.  If the user is requesting information on a subject or asking a question, predict what information needs to be provided with syllogistic reasoning, ensuring to double check your work. Do not give examples, only the action plan. {usernameupper}: {user_input} {user_input_end} "})
        intuition.append({'role': 'assistant', 'content': f"{botnameupper}: "}) 
        
        if backend_model == "Llama_2":
            prompt = ''.join([message_dict['content'] for message_dict in intuition])
            output_two = await Intuition_Call(prompt, username, bot_name)
            
        if backend_model == "Open_Ai":
            output_two = Intuition_Call(intuition, username, bot_name)
            
            
            
        if Intuition_Output == 'True':
            print(f'\n\nINTUITION: {output_two}')
            
        if memory_mode != 'None':
        
        
        
            implicit_short_term_memory = f'\nUSER: {user_input}\nINNER_MONOLOGUE: {output_one}'
            implicit_memory.append({'role': 'assistant', 'content': f"LOG: {implicit_short_term_memory} {user_input_start} SYSTEM: Read the log to identify key interactions between {bot_name} and {username} from the chatbot's inner monologue. Create 3-5 bullet-point summaries that will serve as automatic, unconscious memories for {bot_name}'s future interactions. These memories should not be easily verbalized but should capture the essence of skills, habits, or associations learned during interactions. Each bullet point should contain enough context to understand the significance without tying to explicit reasoning or verbal explanation. Use the following bullet point format: •[memory] {user_input_end} {botnameupper}: Sure! Here are the bullet-point summaries which will serve as memories based on {bot_name}'s internal thoughts:"})
            
            if backend_model == "Llama_2":
                prompt_implicit = ''.join([message_dict['content'] for message_dict in implicit_memory])
                
            if backend_model == "Open_Ai":
                prompt_implicit = implicit_memory
                
            
            if memory_mode != 'Manual':
                task = asyncio.create_task(Aetherius_Implicit_Memory(user_input, output_one, bot_name, username, user_id, prompt_implicit))
        intuition.clear()
        
        conversation_history = main_conversation.get_conversation_history()
        con_hist = f'{conversation_history}'
        timestamp = time()
        timestring = timestamp_to_datetime(timestamp)
        
        try:
            hits = client.search(
                collection_name=f"Bot_{bot_name}",
                query_vector=vector_monologue,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="memory_type",
                            match=MatchValue(value="Cadence"),
                        ),
                        FieldCondition(
                            key="user",
                            match=models.MatchValue(value=f"{user_id}"),
                        ),
                    ]
                ),
                limit=2
            )
            db_search_11 = [hit.payload['message'] for hit in hits]
            response.append({'role': 'assistant', 'content': f"CADENCE: I will extract the cadence from the following messages and mimic it to the best of my ability: {db_search_11}"})
        except:
            pass
            
            
            
        response.append({'role': 'system', 'content': f"Now return your most relevant memories: {user_input_end} "})
        response.append({'role': 'system', 'content': f"{botnameupper}'S LONG TERM CHATBOT MEMORIES: "})
        response.append({'role': 'user', 'content': f"USER INPUT: {user_input}\n"})
        
        
        
        db_search_12, db_search_13, db_search_14 = None, None, None
        
        try:
            hits = client.search(
                collection_name=f"Bot_{bot_name}",
                query_vector=vector_monologue,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="memory_type",
                            match=MatchValue(value="Implicit_Long_Term"),
                        ),
                        FieldCondition(
                            key="user",
                            match=models.MatchValue(value=f"{user_id}"),
                        ),
                    ]
                ),
                limit=4
            )
            unsorted_table = [(hit.payload['timestring'], hit.payload['message']) for hit in hits]
            sorted_table = sorted(unsorted_table, key=lambda x: x[0])  
            db_search_12 = "\n".join([f"{message}" for timestring, message in sorted_table])
            if DB_Search_Output == 'True':
                print(f"\n\nIMPLICIT LONG TERM:\n{db_search_12}")
        except Exception as e:
            if DB_Search_Output == 'True':
                if "Not found: Collection" in str(e):
                    print("\nCollection does not exist.")
                else:
                    print(f"\nAn unexpected error occurred: {str(e)}")
                    
        try:
            hits = client.search(
                collection_name=f"Bot_{bot_name}",
                query_vector=vector_monologue,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="memory_type",
                            match=MatchValue(value="Episodic"),
                        ),
                        FieldCondition(
                            key="user",
                            match=models.MatchValue(value=f"{user_id}"),
                        ),
                    ]
                ),
                limit=7
            )
            unsorted_table = [(hit.payload['timestring'], hit.payload['message']) for hit in hits]
            sorted_table = sorted(unsorted_table, key=lambda x: x[0])  
            db_search_13 = "\n".join([f"{message}" for timestring, message in sorted_table])
            if DB_Search_Output == 'True':
                print(f"\n\nEPISODIC:\n{db_search_13}")
        except Exception as e:
            if DB_Search_Output == 'True':
                if "Not found: Collection" in str(e):
                    print("\nCollection does not exist.")
                else:
                    print(f"\nAn unexpected error occurred: {str(e)}")
                    
        try:
            hits = client.search(
                collection_name=f"Bot_{bot_name}",
                query_vector=vector_monologue,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="memory_type",
                            match=MatchValue(value="Heuristics"),
                        ),
                        FieldCondition(
                            key="user",
                            match=models.MatchValue(value=f"{user_id}"),
                        ),
                    ]
                ),
                limit=5
            )
            unsorted_table = [(hit.payload['timestring'], hit.payload['message']) for hit in hits]
            sorted_table = sorted(unsorted_table, key=lambda x: x[0]) 
            db_search_14 = "\n".join([f"{message}" for timestring, message in sorted_table])
            if DB_Search_Output == 'True':
                print(f"\n\nHEURISTICS:\n{db_search_14}")
        except Exception as e:
            if DB_Search_Output == 'True':
                if "Not found: Collection" in str(e):
                    print("\nCollection does not exist.")
                else:
                    print(f"\nAn unexpected error occurred: {str(e)}")
                    
                  
                  
        response.append({'role': 'assistant', 'content': f"{botnameupper}'S MEMORIES: {db_search_12}\n{db_search_13}\n{bot_name}'s HEURISTICS: {db_search_14}\n{botnameupper}'S INNER THOUGHTS: {output_one}\n{secondary_prompt} {user_input_start} Now return and analyze the previous conversation history. {user_input_end} CONVERSATION HISTORY: {con_hist} "})
        response.append({'role': 'user', 'content': f"{user_input_start} {usernameupper}: We are currently in the middle of a conversation, please review your action plan for your response. {user_input_end}"})
        response.append({'role': 'assistant', 'content': f"{botnameupper}: I will now review my action plan, using it as a framework to construct my upcoming response: {output_two}\nI will proceed by reviewing our previous conversation to ensure I respond in a manner that is both informative and emotionally attuned. Please now give me the message I am to respond to."})
        response.append({'role': 'user', 'content': f"{user_input_start} {usernameupper}'S MOST RECENT MESSAGE: {user_input} {user_input_end} "})
        response.append({'role': 'assistant', 'content': f"{botnameupper}: Sure, here is a natural sounding response to {username}'s latest message: "})
        
        if backend_model == "Llama_2":
            prompt = ''.join([message_dict['content'] for message_dict in response])
            response_two = await Response_Call(prompt, username, bot_name)
        
        if backend_model == "Open_Ai":
            response_two = Response_Call(response, username, bot_name)

        
        bot_name_pattern = re.compile(rf"^{re.escape(bot_name)}[\s:-]+", re.IGNORECASE)

        response_two = response_two.strip()
        match = bot_name_pattern.search(response_two)
        if match:
            response_two = response_two[match.end():]

        sentences = re.split(r'(?<=[.!?])\s+', response_two)
        if sentences and not re.search(r'[.!?]$', sentences[-1]):
            sentences.pop()
        response_two = ' '.join(sentences)
        if Response_Output == 'True':
            print('\n\n%s: %s' % (bot_name, response_two))
            
        main_conversation.append(timestring, username, usernameupper, user_input, bot_name, botnameupper, response_two)
        
        if memory_mode != 'None':
        
            db_msg = f"USER: {user_input}\nINNER_MONOLOGUE: {output_one}\n{bot_name}'s RESPONSE: {response_two}"
            explicit_memory.append({'role': 'system', 'content': f"LOG: {db_msg} {user_input_start} SYSTEM: Use the log to extract salient points about interactions between {bot_name} and {username}, as well as any informational topics mentioned in the chatbot's inner monologue and responses. These points should be used to create concise executive summaries in bullet point format, intended to serve as explicit memories for {bot_name}'s future interactions. These memories should be consciously recollected and easily talked about, focusing on general knowledge and facts discussed or learned. Each bullet point should be rich in detail, providing all the essential context for full recollection and articulation. Each bullet point should be considered a separate memory and contain full context. Use the following bullet point format: •[memory] {user_input_end} "})
            explicit_memory.append({'role': 'assistant', 'content': f"{botnameupper}: Sure! Here are 3-5 bullet-point summaries that will serve as memories based on {bot_name}'s responses:"})
            
            if backend_model == "Llama_2":
                prompt_explicit = ''.join([message_dict['content'] for message_dict in explicit_memory])
        
            if backend_model == "Open_Ai":
                prompt_explicit = explicit_memory
        
        
        
            if memory_mode != 'Manual':
                task = asyncio.create_task(Aetherius_Explicit_Memory(user_input, vector_input, vector_monologue, output_one, response_two, bot_name, username, user_id, prompt_explicit))

        
        response.clear()
        
        
        if memory_mode == 'Manual':
            if backend_model == "Llama_2":
                inner_loop_memory = await Implicit_Memory_Call(prompt_implicit, username, bot_name)
                response_memory = await Explicit_Memory_Call(prompt_explicit, username, bot_name)
                
            if backend_model == "Open_Ai":
                inner_loop_memory = Implicit_Memory_Call(prompt_implicit)
                response_memory = Explicit_Memory_Call(prompt_explicit)
                
            print(f"Do you want to upload the following memories:\n{inner_loop_response}\n{response_memory}\n'Y' or 'N'")
            mem_upload_yescheck = input("Enter 'Y' or 'N': ")
            if mem_upload_yescheck.upper == "Y":
                segments = re.split(r'•|\n\s*\n', inner_loop_response)
                total_segments = len(segments)

                for index, segment in enumerate(segments):
                    segment = segment.strip()
                    if segment == '':
                        continue     
                    if index == total_segments - 1 and not segment[-1] in ['.', '!', '?']:
                        continue
                    await Upload_Implicit_Short_Term_Memories(segment, username, user_id, bot_name)
                segments = re.split(r'•|\n\s*\n', db_upsert)
                total_segments = len(segments)
                for index, segment in enumerate(segments):
                    segment = segment.strip()
                    if segment == '':
                        continue     
                    if index == total_segments - 1 and not segment[-1] in ['.', '!', '?']:
                        continue
                    await Upload_Explicit_Short_Term_Memories(segment, username, user_id, bot_name)
                task = asyncio.create_task(Aetherius_Memory_Loop(user_input, username, user_id, bot_name, vector_input, vector_monologue, output_one, response_two))
        return response_two
        
        
        
        
async def Aetherius_Agent(user_input, username, user_id, bot_name, image_path=None):
    with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
    API = settings.get('API', 'AetherNode')
    if API == "Oobabooga":
        HOST = settings.get('HOST_Oobabooga', 'http://localhost:5000/api')
    if API == "AetherNode":
        HOST = settings.get('HOST_AetherNode', 'http://127.0.0.1:8000')
    embed_size = settings['embed_size']
    External_Research_Search = settings.get('Search_External_Resource_DB', 'False')
    conv_length = settings.get('Conversation_Length', '3')
    Web_Search = settings.get('Search_Web', 'False')
    Inner_Monologue_Output = settings.get('Output_Inner_Monologue', 'True')
    Intuition_Output = settings.get('Output_Intuition', 'False')
    Response_Output = settings.get('Output_Response', 'True')
    DB_Search_Output = settings.get('Output_DB_Search', 'False')
    memory_mode = settings.get('Memory_Mode', 'Forced')
    Sub_Module_Output = settings.get('Output_Sub_Module', 'False')
    Update_Bot_Personality_Description = settings.get('Update_Bot_Personality_Description', 'False')
    Update_User_Personality_Description = settings.get('Update_User_Personality_Description', 'False')
    Use_Bot_Personality_Description = settings.get('Use_Bot_Personality_Description', 'False')
    Use_User_Personality_Description = settings.get('Use_User_Personality_Description', 'False')
    backend_model = settings.get('Model_Backend', 'Llama_2')
    LLM_Model = settings.get('LLM_Model', 'Llama_2')
    select_api = settings.get('API', 'Oobabooga')
    tasklist = list()
    agent_inner_monologue = list()
    agent_intuition = list()
    conversation2 = list()
    implicit_memory = list()
    explicit_memory = list()
    summary = list()
    auto = list()
    payload = list()
    consolidation  = list()
    tasklist_completion = list()
    master_tasklist = list()
    tasklist = list()
    tasklist_log = list()
    memcheck = list()
    memcheck2 = list()
    webcheck = list()
    cat_list = list()
    domain_extraction = list()
    input_expansion = list()
    counter = 0
    counter2 = 0
    mem_counter = 0
    botnameupper = bot_name.upper()
    usernameupper = username.upper()
    if backend_model == "Llama_2":
        user_input_end = "[/INST]"
        user_input_start = "[INST]"
    if backend_model == "Open_Ai":
        user_input_end = ""
        user_input_start = ""
    base_path = "./Aetherius_API/Chatbot_Prompts"
    base_prompts_path = os.path.join(base_path, "Base")
    user_bot_path = os.path.join(base_path, user_id, bot_name)
    if not os.path.exists(user_bot_path):
        os.makedirs(user_bot_path)
    prompts_json_path = os.path.join(user_bot_path, "prompts.json")
    base_prompts_json_path = os.path.join(base_prompts_path, "prompts.json")
    if not os.path.exists(prompts_json_path) and os.path.exists(base_prompts_json_path):
        async with aiofiles.open(base_prompts_json_path, 'r') as base_file:
            base_prompts_content = await base_file.read()
        async with aiofiles.open(prompts_json_path, 'w') as user_file:
            await user_file.write(base_prompts_content)
    async with aiofiles.open(prompts_json_path, 'r') as file:
        prompts = json.loads(await file.read())
    main_prompt = prompts["main_prompt"].replace('<<NAME>>', bot_name)
    secondary_prompt = prompts["secondary_prompt"]
    greeting_msg = prompts["greeting_prompt"].replace('<<NAME>>', bot_name)
    main_conversation = MainConversation(username, user_id, bot_name, conv_length, main_prompt, greeting_msg)
    while True:
        print(f"{username}: {user_input}\n\n")
        conversation_history = main_conversation.get_last_entry()
        con_hist = f'{conversation_history}'
        timestamp = time()
        timestring = timestamp_to_datetime(timestamp)

        input_2 = None
        if len(user_input) > 2:
            input_2 = user_input
        if image_path is not None:
            user_input = gpt_vision(user_input, image_path)
            if input_2 is not None and len(input_2) > 2:
                user_input = f"VISION: {user_input}\nORIGINAL USER INQUIRY: {input_2}"
        
        vector_input = embeddings(user_input)
        
        

        
        input_expansion.append({'role': 'user', 'content': f"PREVIOUS CONVERSATION HISTORY: {con_hist}\n\n\n"})
        input_expansion.append({'role': 'system', 'content': f"You are a task rephraser. Your primary task is to rephrase the user's most recent input succinctly and accurately. Please return the rephrased version of the user’s most recent input. USER'S MOST RECENT INPUT: {user_input} {user_input_end}"})
        input_expansion.append({'role': 'user', 'content': f"TASK REPHRASER: Sure! Here's the rephrased version of the user's most recent input: "})
        
        if backend_model == "Open_Ai":
            expanded_input = Input_Expansion_Call(input_expansion, username, bot_name)

        if backend_model == "Llama_2":
            prompt = ''.join([message_dict['content'] for message_dict in input_expansion])
            expanded_input = await Input_Expansion_Call(prompt, username, bot_name)
        print(f"\n\nExpanded User Input: {expanded_input}")
        

        
        
        
        domain_extraction.append({'role': 'user', 'content': f"You are a knowledge domain extractor.  Your task is to analyze the user's inquiry, then choose the single most salent generalized knowledge domain needed to complete the user's inquiry from the list of existing domains.  Your response should only contain the single existing knowledge domain.\n"})
        domain_extraction.append({'role': 'user', 'content': f"USER INPUT: {expanded_input} {user_input_end} "})
        
        if backend_model == "Llama_2":
            prompt = ''.join([message_dict['content'] for message_dict in domain_extraction])
            extracted_domain = await Domain_Extraction_Call(prompt, username, bot_name)
            
        if backend_model == "Open_Ai":
            extracted_domain = Domain_Extraction_Call(domain_extraction, username, bot_name)
          
            
        if ":" in extracted_domain:
            extracted_domain = extracted_domain.split(":")[-1]
            extracted_domain = extracted_domain.replace("\n", "")
            extracted_domain = extracted_domain.upper()
            extracted_domain = re.sub(r'[^A-Z]', '', extracted_domain)
            extracted_domain = extracted_domain.replace("_", " ")
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
            print(f"\nKnowledge Domains: {domain_search}")
        except Exception as e:
            if "Not found: Collection" in str(e):
                print("Collection does not exist.")
                domain_search = "No Collection"
            else:
                print(f"An unexpected error occurred: {str(e)}")
                domain_search = "No Collection"
        
        
        
        domain_extraction.append({'role': 'user', 'content': f"Could you provide the current list of knowledge domains? {user_input_end}"})
        domain_extraction.append({'role': 'user', 'content': f"CURRENT KNOWLEDGE DOMAINS: {domain_search}"})
        domain_extraction.append({'role': 'user', 'content': f"{user_input_start} Your role as a Knowledge Domain Selector is to analyze the user's question and identify the most relevant knowledge domain from the provided list. Ensure that your choice is from the existing domains, and avoid creating or using any not listed. Respond with the name of the single selected knowledge domain.\n"})
        domain_extraction.append({'role': 'user', 'content': f"USER QUESTION: {user_input}\nADDITIONAL CONTEXT: {expanded_input} {user_input_end}"})
        
        if backend_model == "Llama_2":
            prompt = ''.join([message_dict['content'] for message_dict in domain_extraction])
            extracted_domain = await Domain_Selection_Call(prompt, username, bot_name)
            
        if backend_model == "Open_Ai":
            extracted_domain = Domain_Selection_Call(domain_extraction, username, bot_name)
            
            
        if ":" in extracted_domain:
            extracted_domain = extracted_domain.split(":")[-1]
            extracted_domain = extracted_domain.replace("\n", "")
            extracted_domain = extracted_domain.upper()
            extracted_domain = re.sub(r'[^A-Z]', '', extracted_domain)
            extracted_domain = extracted_domain.replace("_", " ")
        print(f"Extracted Domain: {extracted_domain}")
        

        conversation_history = main_conversation.get_last_entry()
        con_hist = f'{conversation_history}'
        
        vector_input1 = embeddings(expanded_input)
        

        agent_inner_monologue.append({'role': 'system', 'content': f"SYSTEM: {main_prompt}"})
        if Use_Bot_Personality_Description == 'True':
            try:
                file_path = f"./Chatbot_Personalities/{bot_name}/{user_id}/{bot_name}_personality_file.txt"
                if not os.path.exists(file_path):
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    default_prompts = f"{main_prompt}\n{secondary_prompt}\n{greeting_msg}"
                    async def write_prompts():
                        try:
                            async with aiofiles.open(file_path, 'w') as txt_file:
                                await txt_file.write(default_prompts)
                        except Exception as e:
                            print(f"Failed to write to file: {e}")
                    await write_prompts()
                try:
                    async with aiofiles.open(file_path, mode='r') as file:
                        personality_file = await file.read()
                except FileNotFoundError:
                    personality_file = "File not found."
                try:
                    async with aiofiles.open(file_path, mode='r', encoding='utf-8') as file:
                        file_content = await file.readlines()
                except FileNotFoundError:
                    print(f"No such file or directory: '{file_path}'")
                    return None
                except IOError:
                    print("An I/O error occurred while handling the file")
                    return None
                else:
                    bot_personality = [line.strip() for line in file_content]
                agent_inner_monologue.append({'role': 'system', 'content': f"{botnameupper}'S PERSONALITY DESCRIPTION: {bot_personality}\n\n"})
            except:
                pass
        
        
        
        agent_inner_monologue.append({'role': 'system', 'content': f"{botnameupper}'S LONG TERM CHATBOT MEMORIES: "})
        agent_intuition.append({'role': 'system', 'content': f"{main_prompt}"})
        
        
        
        if Use_User_Personality_Description == 'True':
            try:
                file_path = f"./Chatbot_Personalities/{bot_name}/{user_id}/{username}_personality_file.txt"
                # Check if file exists, if not create and write default prompts.
                if not os.path.exists(file_path):
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    default_prompts = f"The user {user_id} does not yet have a personality file."

                    async def write_prompts():
                        try:
                            async with aiofiles.open(file_path, 'w') as txt_file:
                                await txt_file.write(default_prompts)
                        except Exception as e:
                            print(f"Failed to write to file: {e}")

                    # Ensure to call write_prompts in an async context
                    await write_prompts()

                try:
                    async with aiofiles.open(file_path, mode='r') as file:
                        personality_file = await file.read()
                except FileNotFoundError:
                    personality_file = "File not found."
                try:
                    async with aiofiles.open(file_path, mode='r', encoding='utf-8') as file:
                        file_content = await file.readlines()
                except FileNotFoundError:
                    print(f"No such file or directory: '{file_path}'")
                    return None
                except IOError:
                    print("An I/O error occurred while handling the file")
                    return None
                else:
                    user_personality = [line.strip() for line in file_content]
                agent_intuition.append({'role': 'system', 'content': f"{usernameupper}'S PERSONALITY DESCRIPTION: {user_personality}\n\n"})
            except:
                pass
        
        
        
        agent_intuition.append({'role': 'system', 'content': f"Now return your most relevant memories: {user_input_end}"})
        agent_intuition.append({'role': 'system', 'content': f"{botnameupper}'S LONG TERM CHATBOT MEMORIES: "})
        tasklist.append({'role': 'system', 'content': "SYSTEM: You are a search query corrdinator. Your role is to interpret the original user query and generate 2-4 synonymous search terms that will guide the exploration of the chatbot's memory database. Each alternative term should reflect the essence of the user's initial search input. Please list your results using bullet point format.\n"})
        tasklist.append({'role': 'user', 'content': f"USER: %s {user_input_end} ASSISTANT: Sure, I'd be happy to help! Here are 1-3 synonymous search terms: " % user_input})
        
        if backend_model == "Llama_2":
            prompt = ''.join([message_dict['content'] for message_dict in tasklist])
            tasklist_output = await Semantic_Terms_Call(prompt, username, bot_name)
       
        if backend_model == "Open_Ai":
            tasklist_output = Semantic_Terms_Call(tasklist, username, bot_name)
       
       
        lines = tasklist_output.splitlines()
        db_term = {}
        db_term_result = {}
        db_term_result2 = {}
        tasklist_counter = 0
        tasklist_counter2 = 0
        temp_list = list()
        temp_list2 = list()
        for line in lines:
            if External_Research_Search == 'True':
                try:
                    hits = client.search(
                        collection_name=f"Bot_{bot_name}_External_Knowledgebase",
                        query_vector=vector_input1,
                        query_filter=Filter(
                            must=[
                                models.FieldCondition(
                                    key="user",
                                    match=models.MatchValue(value=f"{user_id}"),
                                ),
                            ]
                        ),
                        limit=2
                   )
                    unsorted_table = [(hit.payload['timestring'], hit.payload['tag'], hit.payload['message']) for hit in hits]
                    
                    sorted_table = sorted(unsorted_table, key=lambda x: x[0])
                    external_scrape = "\n".join([f"{tag} - {message}" for timestring, tag, message in sorted_table])
                    if DB_Search_Output == 'True':
                        print(external_scrape)
                except Exception as e:
                    print(f"An unexpected error occurred: {str(e)}")
                    external_scrape = "No External Resources Selected"
            else:
                external_scrape = "No External Resources Selected"
                if DB_Search_Output == 'True':
                    print(external_scrape)
         
            try:
                hits = client.search(
                    collection_name=f"Bot_{bot_name}",
                    query_vector=vector_input1,
                    query_filter=Filter(
                        must=[
                            FieldCondition(
                                key="memory_type",
                                match=MatchValue(value="Explicit_Long_Term"),
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
                    limit=5
                )
                unsorted_table = [(hit.payload['timestring'], hit.payload['message']) for hit in hits]
                sorted_table = sorted(unsorted_table, key=lambda x: x[0])
                db_search_1 = "\n".join([f"{message}" for timestring, message in sorted_table])
                temp_list.append({'role': 'assistant', 'content': f"{db_search_1}  "})
                if tasklist_counter < 4:
                    temp_list2.append({'role': 'assistant', 'content': f"{db_search_1}  "})
                    if External_Research_Search == 'True':
                        temp_list.append({'role': 'assistant', 'content': f"{external_scrape}"})
                        temp_list2.append({'role': 'assistant', 'content': f"{external_scrape}"})
                tasklist_counter + 1
                if DB_Search_Output == 'True':
                    print(db_search_1)
            except Exception as e:
                if DB_Search_Output == 'True':
                    if "Not found: Collection" in str(e):
                        print("Collection does not exist.")
                    else:
                        print(f"An unexpected error occurred: {str(e)}")
    
            try:
                hits = client.search(
                    collection_name=f"Bot_{bot_name}",
                    query_vector=vector_input1,
                    query_filter=Filter(
                        must=[
                            FieldCondition(
                                key="memory_type",
                                match=MatchValue(value="Implicit_Long_Term"),
                            ),
                            FieldCondition(
                                key="user",
                                match=models.MatchValue(value=f"{user_id}"),
                            ),
                        ]
                    ),
                    limit=6
                )
                unsorted_table = [(hit.payload['timestring'], hit.payload['message']) for hit in hits]
                sorted_table = sorted(unsorted_table, key=lambda x: x[0]) 
                db_search_2 = "\n".join([f"{message}" for timestring, message in sorted_table])
                temp_list.append({'role': 'assistant', 'content': f"{db_search_2}  "})
                if tasklist_counter2 < 4:
                    temp_list2.append({'role': 'assistant', 'content': f"{db_search_2}  "})
                tasklist_counter2 + 1
                if DB_Search_Output == 'True':
                    print(db_search_2)
            except Exception as e:
                if DB_Search_Output == 'True':
                    if "Not found: Collection" in str(e):
                        print("Collection does not exist.")
                    else:
                        print(f"An unexpected error occurred: {str(e)}")
                        
            def remove_duplicate_dicts(input_list):
                output_list = []
                for item in input_list:
                    if item not in output_list:
                        output_list.append(item)
                return output_list
            temp_list = remove_duplicate_dicts(temp_list)
            temp_list2 = remove_duplicate_dicts(temp_list2)
        agent_inner_monologue.append({'role': 'system', 'content': f"{temp_list}"})       
        agent_intuition.append({'role': 'system', 'content': f"{temp_list2}"})   
        
        temp_list.clear()
        temp_list2.clear()

        db_search_1, db_search_2, db_search_3, db_search_14 = None, None, None, None
        try:
            hits = client.search(
                collection_name=f"Bot_{bot_name}",
                query_vector=vector_input1,
                query_filter=Filter(
                    must=[
                        models.FieldCondition(
                            key="memory_type",
                            match=models.MatchValue(value="Episodic"),
                        ),
                        models.FieldCondition(
                            key="user",
                            match=models.MatchValue(value=f"{user_id}"),
                        ),
                    ]
                ),
                limit=4
            )
            unsorted_table = [(hit.payload['timestring'], hit.payload['message']) for hit in hits]
            sorted_table = sorted(unsorted_table, key=lambda x: x[0])
            db_search_1 = "\n".join([f"{message}" for timestring, message in sorted_table])
            if DB_Search_Output == 'True':
                print(db_search_1)
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
            
        try:
            hits = client.search(
                collection_name=f"Bot_{bot_name}_Implicit_Short_Term",
                query_vector=vector_input1,
                query_filter=Filter(
                    must=[
                        models.FieldCondition(
                            key="memory_type",
                            match=models.MatchValue(value="Implicit_Short_Term"),
                        ),
                        models.FieldCondition(
                            key="user",
                            match=models.MatchValue(value=f"{user_id}"),
                        ),
                    ]
                ),
                limit=3
            )
            unsorted_table = [(hit.payload['timestring'], hit.payload['message']) for hit in hits]
            sorted_table = sorted(unsorted_table, key=lambda x: x[0])
            db_search_1 = "\n".join([f"{message}" for timestring, message in sorted_table])
            if DB_Search_Output == 'True':
                print(db_search_1)
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
            
        try:
            hits = client.search(
                collection_name=f"Bot_{bot_name}",
                query_vector=vector_input1,
                query_filter=Filter(
                    must=[
                        models.FieldCondition(
                            key="memory_type",
                            match=models.MatchValue(value="Heuristics"),
                        ),
                        models.FieldCondition(
                            key="user",
                            match=models.MatchValue(value=f"{user_id}"),
                        ),
                    ]
                ),
                limit=5
            )
            unsorted_table = [(hit.payload['timestring'], hit.payload['message']) for hit in hits]
            sorted_table = sorted(unsorted_table, key=lambda x: x[0])
            db_search_14 = "\n".join([f"{message}" for timestring, message in sorted_table])
            if DB_Search_Output == 'True':
                print(db_search_14)
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
            
        if External_Research_Search == 'True':
            try:
                hits = client.search(
                    collection_name=f"Bot_{bot_name}_External_Knowledgebase",
                    query_vector=vector_input1,
                    query_filter=Filter(
                        must=[
                            models.FieldCondition(
                                key="user",
                                match=models.MatchValue(value=f"{user_id}"),
                            ),
                        ]
                    ),
                    limit=3
                )
                unsorted_table = [(hit.payload['timestring'], hit.payload['tag'], hit.payload['message']) for hit in hits]
                sorted_table = sorted(unsorted_table, key=lambda x: x[0])
                db_search_2 = "\n".join([f"{tag} - {message}" for timestring, tag, message in sorted_table])
                if DB_Search_Output == 'True':
                    print(db_search_2)
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")
        else:      
            db_search_2 = "No External Resources Selected"
            if DB_Search_Output == 'True':
                print(db_search_2)
            
        if External_Research_Search == 'True':
            external_resources = f"{user_input_start} Search your external resources and find relevant information to help form your thoughts. {user_input_end}  EXTERNAL RESOURCES: {db_search_2}"
        else:
            external_resources = " "


            
        # # Inner Monologue Generation
        agent_inner_monologue.append({'role': 'assistant', 'content': f"{botnameupper}'S EPISODIC MEMORIES: {db_search_1}\n{bot_name}'s HEURISTICS: {db_search_14}\nPREVIOUS CONVERSATION HISTORY: {con_hist} {user_input_start} SYSTEM: Compose a truncated silent soliloquy to serve as {bot_name}'s internal monologue/narrative using the external resources.  Ensure it includes {bot_name}'s contemplations on how {username}'s request relates to the given external information.\n{usernameupper}: {user_input} {user_input_end} {botnameupper}: Sure, here is an internal narrative as {bot_name} on how the user's request relates to the Given External information: "})
        
        if backend_model == "Llama_2":
            prompt = ''.join([message_dict['content'] for message_dict in agent_inner_monologue])
            output_one = await Inner_Monologue_Call(prompt, username, bot_name)
            
        if backend_model == "Open_Ai":
            output_one = Inner_Monologue_Call(agent_inner_monologue, username, bot_name)
            
            
            
        if Inner_Monologue_Output == 'True':
            print('\n\nINNER_MONOLOGUE: %s' % output_one)
        agent_inner_monologue.clear()

        vector_monologue = embeddings('Inner Monologue: ' + output_one)     
        db_search_4, db_search_5, db_search_12, db_search_15 = None, None, None, None
        try:
            hits = client.search(
                collection_name=f"Bot_{bot_name}",
                query_vector=vector_monologue,
                query_filter=Filter(
                    must=[
                        models.FieldCondition(
                            key="memory_type",
                            match=models.MatchValue(value="Episodic"),
                        ),
                        models.FieldCondition(
                            key="user",
                            match=models.MatchValue(value=f"{user_id}"),
                        ),
                    ]
                ),
                limit=3
            )
            unsorted_table = [(hit.payload['timestring'], hit.payload['message']) for hit in hits]
            sorted_table = sorted(unsorted_table, key=lambda x: x[0])  # Sort by the 'timestring' field
            db_search_4 = "\n".join([f"{message}" for timestring, message in sorted_table])
            if DB_Search_Output == 'True':
                print(db_search_4)
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
        try:
            hits = client.search(
                collection_name=f"Bot_{bot_name}_Explicit_Short_Term",
                query_vector=vector_monologue,
                query_filter=Filter(
                    must=[
                        models.FieldCondition(
                            key="memory_type",
                            match=models.MatchValue(value="Explicit_Short_Term"),
                        ),
                        models.FieldCondition(
                            key="user",
                            match=models.MatchValue(value=f"{user_id}"),
                        ),
                    ]
                ),
                limit=3
            )

            db_search_5 = [hit.payload['message'] for hit in hits]
            if DB_Search_Output == 'True':
                print(db_search_5)
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
        try:
            hits = client.search(
                collection_name=f"Bot_{bot_name}",
                query_vector=vector_monologue,
                query_filter=Filter(
                    must=[
                        models.FieldCondition(
                            key="memory_type",
                            match=models.MatchValue(value="Heuristics"),
                        ),
                        models.FieldCondition(
                            key="user",
                            match=models.MatchValue(value=f"{user_id}"),
                        ),
                    ]
                ),
                limit=3
            )
            db_search_15 = [hit.payload['message'] for hit in hits]
            if DB_Search_Output == 'True':
                print(db_search_15)
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
            
        cwd = os.getcwd()
        if select_api == "Oobabooga":
            sub_agent_path = "Aetherius_API\Sub_Agents\Llama_2_Async"
        if select_api == "AetherNode":
            sub_agent_path = "Aetherius_API\Sub_Agents\AetherNode_Llama_2"
        if select_api == "Open_Ai":
            sub_agent_path = "Aetherius_API\Sub_Agents\OpenAi"
        
        folder_path = os.path.join(cwd, sub_agent_path.lstrip('/'))
        filename_description_map = await load_filenames_and_descriptions(folder_path, username, user_id, bot_name)

        collection_name = f"Bot_{bot_name}_{user_id}_Sub_Agents"
        try:
            collection_info = client.get_collection(collection_name=collection_name)
        except:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=embed_size, distance=Distance.COSINE),
            )
        try:
            cat_set = set()
            for filename, file_data in filename_description_map.items():
                file_desc = f"{filename} - {file_data['description']}"
                cat = file_data['category']
                catupper = cat.upper()
                cat_des = file_data['cat_description']
                cat_entry = f"[{cat}]- {cat_des}"
                if cat_entry not in cat_set:  # Check if the category description is unique
                    cat_set.add(cat_entry)
                    cat_list.append({'content': cat_entry})
                vector = embeddings(file_desc)  
                unique_id = str(uuid4())
                timestamp = time()
                metadata = {
                    'bot': bot_name,
                    'user': user_id,
                    'time': timestamp,
                    'filename': filename,
                    'description': file_data['description'],
                    'category': catupper,
                    'category_description': file_data['cat_description'],
                    'uuid': unique_id,
                }

                client.upsert(collection_name=collection_name,
                             points=[PointStruct(id=unique_id, vector=vector, payload=metadata)])
                             
            subagent_cat = '\n'.join([message_dict['content'] for message_dict in cat_list])
            print(f"\n\n{subagent_cat}")
        except Exception as e:
            traceback.print_exc()
            print(f"An error occurred: {e}")
            error = e
            return error
            
        try:
            hits = client.search(
                collection_name=f"Bot_{bot_name}_{user_id}_Sub_Agents",
                query_vector=vector_input,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="user",
                            match=MatchValue(value=f"{user_id}")
                        ),
                    ]
                ),
                limit=5
            )
            tool_db = [hit.payload['filename'] for hit in hits]
        except Exception as e:
            print(f"Error with Subagent DB: {e}")
            tool_db = "No Sub-Agents Found"
            
            

        # # Intuition Generation
        inner_loop_db = 'None'
        agent_intuition.append({'role': 'assistant', 'content': f"{botnameupper}'S EPISODIC MEMORIES: {db_search_4}\n{botnameupper}'s HEURISTICS: {db_search_15}\n{botnameupper}'S INNER THOUGHTS: {output_one} "})
        agent_intuition.append({'role': 'user', 'content': f"{user_input_start} Now return the list of tools available for you to use. {user_input_end} AVAILABLE TOOLS: {subagent_cat} {user_input_start} Now return and analyze the previous conversation history. {user_input_end} PREVIOUS CONVERSATION HISTORY: {con_hist} {user_input_start} SYSTEM: Transmute the user, {username}'s message as {bot_name} by devising a truncated predictive action plan in the third person point of view on how to best respond to {username}'s most recent message using the given External Resources and list of available tools.  If the user is requesting information on a subjector asking a question, predict what information needs to be provided. Do not give examples or double check work, only provide the action plan. {usernameupper}: {user_input} {user_input_end} "}) 
        agent_intuition.append({'role': 'assistant', 'content': f"{botnameupper}: "})
        inner_loop_response = 'None'
        
        if backend_model == "Llama_2":
            prompt = ''.join([message_dict['content'] for message_dict in agent_intuition])
            output_two = await Agent_Intuition_Call(prompt, username, bot_name)
        
        if backend_model == "Open_Ai":
            output_two = Agent_Intuition_Call(agent_intuition, username, bot_name)
        
        
        message_two = output_two
        if Intuition_Output == 'True':
            print('\n\nINTUITION: %s' % output_two)
        if memory_mode != 'None':
        
        
        
            implicit_short_term_memory = f'\nUSER: {user_input}\nINNER_MONOLOGUE: {output_one}'
            implicit_memory.append({'role': 'system', 'content': f"LOG: {implicit_short_term_memory} {user_input_start} SYSTEM: Extract core facts and aspects of Aetherius's personality based on the dialogue interactions between {bot_name} and {username}. Formulate 1-5 bullet-point summaries to be embedded as subtle, non-verbalizable memories for {bot_name}'s future engagements. Ensure these encapsulations carry enough context to implicitly influence {bot_name}'s responses and actions, without being directly tied to verbal reasoning or explicit recall. Adhere to the bullet point format below: •[memory] {user_input_end} "})
            implicit_memory.append({'role': 'assistant', 'content': f"{botnameupper}: Certainly! The encapsulated memories derived from Aetherius's persona, as observed in the dialogues, are as follows: "})
            
            if backend_model == "Llama_2":
                prompt_implicit = ''.join([message_dict['content'] for message_dict in implicit_memory])
                
            if backend_model == "Open_Ai":
                prompt_implicit = implicit_memory
            
            
            if memory_mode != 'Manual':
                asyncio.create_task(Aetherius_Implicit_Memory(user_input, output_one, bot_name, username, user_id, prompt_implicit))

        timestamp = time()
        timestring = timestamp_to_datetime(timestamp)
        vector = embeddings(output_two)
        if External_Research_Search == 'True':
            try:
                hits = client.search(
                    collection_name=f"Bot_{bot_name}_External_Knowledgebase",
                    query_vector=vector,
                    query_filter=Filter(
                        must=[
                            FieldCondition(
                                key="user",
                                match=MatchValue(value=f"{user_id}")
                            )
                        ]
                    ),
                    limit=10
                )
                ext_resources = [hit.payload['message'] for hit in hits]
                if DB_Search_Output == 'True':
                    print(ext_resources)
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")
                ext_resources = "No External Resources Available"



        if External_Research_Search == 'True':
            master_tasklist.append({'role': 'system', 'content': f"{user_input_start}Please search the external resource database for relevant topics associated with the user's request. {user_input_end} EXTERNAL RESOURCES: {ext_resources}"})

        master_tasklist.append({'role': 'system', 'content': f"{user_input_start} MAIN SYSTEM PROMPT: You are a task list coordinator for {bot_name}, an autonomous AI chatbot. Your job is to merge the user's input and the user-facing chatbot's action plan, along with the given available Tool Categories, to formulate a list of 3-6 independent research search queries. Each task should strictly be allocated a specific Tool Category from the provided list by including '[GIVEN CATEGORY]' at the beginning of each task. These categories should not be altered or created anew. The tasks will be executed by separate AI agents in a cluster computing environment who are stateless and can't communicate with each other or the user during task execution. Exclude tasks focused on final product production, user communication, seeking external help, seeking external validation, or liaising with other entities. Respond using the following format: '•[GIVEN CATEGORY]: <TASK>'\n\nNow, please return the Chatbot's Action Plan and available Tool List."})
        master_tasklist.append({'role': 'user', 'content': f"USER FACING CHATBOT'S INTUITIVE ACTION PLAN: {output_two}\n\nAVAILABLE TOOL CATEGORIES:\n{subagent_cat}\n\n"})
        master_tasklist.append({'role': 'user', 'content': f"USER INQUIRY: {user_input}\nUse only the given categories from the provided list. Do not create or use any categories outside of the given Tool Categories. {user_input_end} "})
        master_tasklist.append({'role': 'assistant', 'content': f"TASK COORDINATOR: Sure, here is a bullet point list of 3-6 tasks, each strictly assigned a category from the given Tool Categories: "})


        if backend_model == "Llama_2":
            prompt = ' '.join([message_dict['content'] for message_dict in master_tasklist])
            master_tasklist_output = await Agent_Master_Tasklist_Call(prompt, username, bot_name)
            
        if backend_model == "Open_Ai":
            master_tasklist_output = Agent_Master_Tasklist_Call(master_tasklist, username, bot_name)
            
            
        print(f"\nTASKLIST OUTPUT: {master_tasklist_output}")
        if Intuition_Output == 'True':
            print('-------\nMaster Tasklist:')
            print(master_tasklist_output)
            
            
            
        tasklist_completion.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: {main_prompt}\n\n"})
        tasklist_completion.append({'role': 'assistant', 'content': f"You are the final response module for the cluster compute Ai-Chatbot {bot_name}. Your job is to take the completed task list, and then give a verbose response to the end user in accordance with their initial request.{user_input_end}\n\n"})
        tasklist_completion.append({'role': 'user', 'content': f"{user_input_start}FULL TASKLIST: {master_tasklist_output}\n\n"})
        
        
        
        task = {}
        task_result = {}
        task_result2 = {}
        task_counter = 1
        try:
            with open('Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
                
            if API == "Oobabooga":
                host_data = settings.get('HOST_Oobabooga', 'http://localhost:5000/api').strip()
            if API == "AetherNode":
                host_data = settings.get('HOST_AetherNode', 'http://127.0.0.1:8000').strip()
            hosts = host_data.split(' ')
            num_hosts = len(hosts)
        except Exception as e:
            print(f"An error occurred while reading the host file: {e}")
        host_queue = asyncio.Queue()
        for host in hosts:
            await host_queue.put(host)

        try:
            lines = re.split(r'\n\s*•\s*|\n\n', master_tasklist_output)
            lines = [line.strip() for line in lines if line.strip()]
        except Exception as e:
            print(f"An error occurred: {e}")
            lines = [master_tasklist_output]

        try:
            tasks = []
            for task_counter, line in enumerate(lines, start=1):
                if line != "None":
                    task = asyncio.create_task(
                        wrapped_process_line(
                            host_queue, bot_name, username, line, task_counter, 
                            output_one, output_two, master_tasklist_output, 
                            user_input, filename_description_map, subagent_cat, user_id
                        )
                    )
                    tasks.append(task)

            completed_tasks = await asyncio.gather(*tasks)
            for task_result in completed_tasks:
                tasklist_completion.extend(task_result)
        except Exception as e:
            print(f"An error occurred while executing tasks: {e}")
                    
        try:
            client.delete(
                collection_name=f"Bot_{bot_name}_{user_id}_Sub_Agents",
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            FieldCondition(
                                key="user",
                                match=models.MatchValue(value=f"{user_id}"),
                            ),
                        ],
                    )
                ),
            ) 
        except:
             print("No Collection to Delete")  

        try:
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
                        ],
                    )
                ),
            ) 
        except:
             print("No Collection to Delete") 
             
             
             
        try:            
            tasklist_completion.append({'role': 'assistant', 'content': f"{user_input_start} USER'S INITIAL INPUT: {user_input} {user_input_end} {botnameupper}'S INNER_MONOLOGUE: {output_one}"})
            tasklist_completion.append({'role': 'system', 'content': f"{user_input_start} SYSTEM: You are tasked with crafting a comprehensive response for {username}. Use the insights and information gathered from the completed tasks during the research task loop to formulate your answer. Since {username} did not have access to the research process, ensure that your reply is self-contained, providing all necessary context and information. Do not introduce information beyond what was discovered during the research tasks, and ensure that factual accuracy is maintained throughout your response. \nUSER'S INITIAL INPUT: {user_input}\nYour research and planning phase is concluded. Concentrate on composing a detailed, coherent, and conversational reply that fully addresses the user's question based on the completed research tasks. {user_input_end} "})
        #    tasklist_completion.append({'role': 'assistant', 'content': f"{botnameupper}: "})

            if backend_model == "Llama_2":
                prompt = ''.join([message_dict['content'] for message_dict in tasklist_completion])
                response_two = await Agent_Response_Call(prompt, username, bot_name)
                
            if backend_model == "Open_Ai":
                response_two = Agent_Response_Call(tasklist_completion, username, bot_name)
                
                
                
            if Response_Output == 'True':
                print("\n\n----------------------------------\n\n")
                print(f"RESPONSE: {response_two}")
        except Exception as e:
            traceback.print_exc()
            print(f"An error occurred: {e}")
            
        main_conversation.append(timestring, username, usernameupper, user_input, bot_name, botnameupper, response_two)
        
        
        
        if memory_mode != 'None':
            db_msg = f"USER: {user_input}\nINNER_MONOLOGUE: {output_one}\n{bot_name}'s RESPONSE: {response_two}"
            explicit_memory.append({'role': 'assistant', 'content': f"LOG: {db_msg} {user_input_start} SYSTEM: Use the log to extract salient points about interactions between {bot_name} and {username}, as well as any informational topics mentioned in the chatbot's inner monologue and responses. These points should be used to create concise executive summaries in bullet point format, intended to serve as explicit memories for {bot_name}'s future interactions. These memories should be consciously recollected and easily talked about, focusing on general knowledge and facts discussed or learned. Each bullet point should be rich in detail, providing all the essential context for full recollection and articulation. Each bullet point should be considered a separate memory and contain full context. Use the following bullet point format: •[memory] {user_input_end} {botnameupper}: Sure! Here are 1-5 bullet-point summaries that will serve as memories based on {bot_name}'s responses:"})
            
            if backend_model == "Llama_2":
                prompt_explicit = ''.join([message_dict['content'] for message_dict in explicit_memory])
                
            if backend_model == "Open_Ai":
                prompt_explicit = explicit_memory
        
        
            if memory_mode != 'Manual':
                task = asyncio.create_task(Aetherius_Explicit_Memory(user_input, vector_input, vector_monologue, output_one, response_two, bot_name, username, user_id, prompt_explicit))

        conversation2.clear()
        if memory_mode == 'Manual':
            if backend_model == "Llama_2":
                inner_loop_memory = await Implicit_Memory_Call(prompt_implicit, username, bot_name)
                response_memory = await Explicit_Memory_Call(prompt_explicit, username, bot_name)
                
            if backend_model == "Open_Ai":
                inner_loop_memory = Implicit_Memory_Call(prompt_implicit, username, bot_name)
                response_memory = Explicit_Memory_Call(prompt_explicit, username, bot_name)
        
            print(f"Do you want to upload the following memories:\n{inner_loop_response}\n{response_memory}\n'Y' or 'N'")
            mem_upload_yescheck = input("Enter 'Y' or 'N': ")
            if mem_upload_yescheck.upper == "Y":
                segments = re.split(r'•|\n\s*\n', inner_loop_response)
                total_segments = len(segments)

                for index, segment in enumerate(segments):
                    segment = segment.strip()
                    if segment == '': 
                        continue     
                    if index == total_segments - 1 and not segment[-1] in ['.', '!', '?']:
                        continue
                    await Upload_Implicit_Short_Term_Memories(segment, username, user_id, bot_name)
                segments = re.split(r'•|\n\s*\n', db_upsert)
                total_segments = len(segments)

                for index, segment in enumerate(segments):
                    segment = segment.strip()
                    if segment == '': 
                        continue   
                    if index == total_segments - 1 and not segment[-1] in ['.', '!', '?']:
                        continue
                    await Upload_Explicit_Short_Term_Memories(segment, username, user_id, bot_name)
                task = asyncio.create_task(Aetherius_Memory_Loop(user_input, username, user_id, bot_name, vector_input, vector_monologue, output_one, response_two))
        return response_two


        
async def wrapped_process_line(host_queue, bot_name, username, line, task_counter, output_one, output_two, master_tasklist_output, user_input, filename_description_map, subagent_cat, user_id):
    host = await host_queue.get()
    result = await process_line(host, host_queue, bot_name, username, line, task_counter, output_one, output_two, master_tasklist_output, user_input, filename_description_map, subagent_cat, user_id)
    await host_queue.put(host)
    return result

        
        
async def process_line(host, host_queue, bot_name, username, line, task_counter, output_one, output_two, master_tasklist_output, user_input, filename_description_map, subagent_cat, user_id):
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        Sub_Module_Output = settings.get('Output_Sub_Module', 'False')
        completed_task = "Error Completing Task"
        backend_model = settings.get('Model_Backend', 'Llama_2')
        select_api = settings.get('API', 'Oobabooga')
        tasklist_completion2 = list()
        conversation = list()
        cat_list = list()
        cat_choose = list()
        botnameupper = bot_name.upper()
        usernameupper = username.upper()
        line_cat = "Research"
        try:
            if backend_model == "Llama_2":
                user_input_end = "[/INST]"
                user_input_start = "[INST]"
            if backend_model == "Open_Ai":
                user_input_end = ""
                user_input_start = ""

            for filename, file_data in filename_description_map.items():
                cat = file_data['category']
                cat = cat.upper()
                cat_list.append(cat)

            category_found = False
            lineupper = line.upper()
            content_within_brackets = re.findall(r'\[(.*?)\]', lineupper)

            for cat in cat_list:
                for content in content_within_brackets:
                    if cat in content:
                        line_cat = cat
                        category_found = True
                        break
               
               
               
            if not category_found:
                cat_choose.append({'role': 'system', 'content': f"{user_input_start} ROLE: You are functioning as a sub-module within a category selection tool. OBJECTIVE: Your primary responsibility is to reevaluate and reassign categories. If a task is associated with a category not present in the predefined list, you must reassign it to an applicable existing category from the list. FORMAT: Maintain the original task wording, and follow this structure for the reassigned task: '[NEW CATEGORY]: <TASK>'. Upon completion, return the task with the updated category assignment. {user_input_end}"})
                cat_choose.append({'role': 'assistant', 'content': f"AVAILABLE TOOL CATEGORIES: {subagent_cat}"})
                cat_choose.append({'role': 'user', 'content': f"TASK REQUIRING CATEGORY REASSIGNMENT: {line}"})
                
                if backend_model == "Llama_2":
                    prompt = ''.join([message_dict['content'] for message_dict in cat_choose])
                    task_expansion = await Agent_Category_Reassign_Call(host, prompt, username, bot_name)
                    
                if backend_model == "Open_Ai":
                    task_expansion = Agent_Category_Reassign_Call(cat_choose, username, bot_name)
                    
                task_expansion = task_expansion.upper()
                category_matches = re.findall(r'\[(.*?)\]', task_expansion)
                for cat in cat_list:
                    for matched_category in category_matches:
                        if cat.upper() in matched_category.upper():
                            line_cat = matched_category
                            category_found = True
                            print(f"\n-----------------------\n")
                            print(f"\nExtracted category: {line_cat}")
                            break
                    if category_found:
                        break
                if not category_found:
                    print(f"\n-----------------------\n")   
                    print("\n\nNo matching category found in the string.")   
        except Exception as e:
            print(f"An error occurred: {e}")

        vector = embeddings(line_cat)
        try:
            hits = client.search(
                collection_name=f"Bot_{bot_name}_{user_id}_Sub_Agents",
                query_vector=vector,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="category",
                            match=MatchValue(value=line_cat)
                        ),
                    ]
                ),
                limit=10
            )
            subagent_list = [hit.payload['filename'] for hit in hits]
        except Exception as e:
            print(f"\nError with Subagent DB: {e}")
            subagent_list = "No Sub-Agents Found"
      
        
        
        tasklist_completion2.append({'role': 'user', 'content': f"TASK: {line} {user_input_end} "})
        conversation.append({'role': 'assistant', 'content': f"First, please query your tool database to identify the tools that are currently available to you. Remember, you can only use these tools. {user_input_end} "})
        conversation.append({'role': 'assistant', 'content': f"AVAILABLE TOOLS: {subagent_list} "})
        conversation.append({'role': 'user', 'content': f"{user_input_start} Your task is to select one of the given tools to complete the assigned task from the provided list of available tools. Ensure that your choice is strictly based on the options provided, and do not suggest or introduce tools that are not part of the list. Your response should be a concise answer that distinctly identifies the chosen tool without going into the operational process or detailed usage of the tool.\n"})
        conversation.append({'role': 'assistant', 'content': f"ASSIGNED TASK: {line}. {user_input_end}"})

        if backend_model == "Llama_2":
            prompt = '\n'.join([message_dict['content'] for message_dict in conversation])
            task_expansion = await Agent_Process_Line_Response_2_Call(host, prompt, username, bot_name)
            
        if backend_model == "Open_Ai":
            task_expansion = Agent_Process_Line_Response_2_Call(conversation, username, bot_name)
            
            
            
        if Sub_Module_Output == 'True':
            print("\n\n----------------------------------\n\n")
            print(task_expansion)
            print("\n\n----------------------------------\n\n")
        vector = embeddings(task_expansion)
        try:
            hits = client.search(
                collection_name=f"Bot_{bot_name}_{user_id}_Sub_Agents",
                query_vector=vector,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="category",
                            match=MatchValue(value=line_cat)
                        ),
                    ]
                ),
                limit=1
            )
            subagent_selection = [hit.payload['filename'] for hit in hits]

        except Exception as e:
            print(f"\nError with Subagent DB: {e}")
            subagent_selection = "No Sub-Agents Found"

        if subagent_selection != "No Sub-Agents Found":
            tasks = []  
            if Sub_Module_Output == 'True':
                print(f"\nTrying to execute function from {subagent_selection}...")
            if not subagent_selection:
                print("\nError with Module, using fallback")
                
                if backend_model == "Llama_2":
                    if select_api == "Oobabooga":
                        fallback_path = ".\Aetherius_API\Sub_Agents\Llama_2_Async\Research\External_Resource_DB_Search.py"
                    if select_api == "AetherNode":
                        fallback_path = ".\Aetherius_API\Sub_Agents\AetherNode_Llama_2\Research\External_Resource_DB_Search.py"
                    if select_api == "Open_Ai":
                        fallback_path = ".\Aetherius_API\Sub_Agents\OpenAi\Research\External_Resource_DB_Search.py"
                
                subagent_selection = [os.path.basename(fallback_path)]
            for filename_with_extension in subagent_selection:
                filename = filename_with_extension.rstrip('.py')
                
                if backend_model == "Llama_2":
                    if select_api == "Oobabooga":
                        script_path = os.path.join(f'.\Aetherius_API\Sub_Agents\Llama_2_Async\{line_cat}', filename_with_extension)
                    if select_api == "AetherNode":
                        script_path = os.path.join(f'.\Aetherius_API\Sub_Agents\AetherNode_Llama_2\{line_cat}', filename_with_extension)
                    

                if os.path.exists(script_path):
                    spec = spec_from_file_location(filename, script_path)
                    module = module_from_spec(spec)
                    spec.loader.exec_module(module)

                    function_to_call = getattr(module, filename, None)
                    
                    if function_to_call is not None:
                        if Sub_Module_Output == 'True':
                            print(f"\nCalling function: {filename}")
                        if asyncio.iscoroutinefunction(function_to_call):
                            task = function_to_call(host, bot_name, username, user_id, line, task_counter, output_one, output_two, master_tasklist_output, user_input)
                        else:
                            loop = asyncio.get_running_loop()
                            task = loop.run_in_executor(None, function_to_call, host, bot_name, username, user_id, line, task_counter, output_one, output_two, master_tasklist_output, user_input)
                        tasks.append(task)

            completed_task = await asyncio.gather(*tasks)
            tasklist_completion2.append({'role': 'assistant', 'content': f"COMPLETED TASK: {completed_task} "})
        
        return tasklist_completion2
    except Exception as e:
        traceback.print_exc()
        print(f"An error occurred: {e}")
        error = e
        return error
        
            
async def load_filenames_and_descriptions(folder_path, username, user_id, bot_name):
    """
    Load all Python filenames in the given folder along with their descriptions and categories.
    Returns a dictionary mapping filenames to their descriptions and categories.
    """
    filename_description_map = {}  

    try:
        categories = [d for d in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, d))]
        for category in categories:
            cat_folder_path = os.path.join(folder_path, category)
            cat_description_file = os.path.join(cat_folder_path, f"{category}.txt")
            cat_description = "Category description not found."
            if os.path.isfile(cat_description_file):
                with open(cat_description_file, 'r') as file:
                    cat_description = file.read().strip()
                    cat_description = cat_description.replace('<<USERNAME>>', username)
                    cat_description = cat_description.replace('<<BOTNAME>>', bot_name)

            filenames = [f for f in os.listdir(cat_folder_path) if f.endswith('.py')]

            for filename in filenames:
                base_filename = os.path.splitext(filename)[0]

                spec = spec_from_file_location(base_filename, os.path.join(cat_folder_path, filename))
                module = module_from_spec(spec)
                spec.loader.exec_module(module)

                description_function = getattr(module, f"{base_filename}_Description", None)
                
                description = "Description function not found."
                if description_function:
                    try:
                        description = description_function(username, bot_name)
                        description = description.replace('<<USERNAME>>', username)
                        description = description.replace('<<BOTNAME>>', bot_name)
                    except Exception as e:
                        print(f"An error occurred: {e}")

                filename_description_map[filename] = {"filename": filename, "description": description, "category": category, "cat_description": cat_description}

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    return filename_description_map
        

        
        
async def Aetherius_Implicit_Memory(user_input, output_one, bot_name, username, user_id, prompt_implicit):
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        API = settings.get('API', 'AetherNode')
        if API == "Oobabooga":
            HOST = settings.get('HOST_Oobabooga', 'http://localhost:5000/api')
        if API == "AetherNode":
            HOST = settings.get('HOST_AetherNode', 'http://127.0.0.1:8000')
        embed_size = settings['embed_size']
        DB_Search_Output = settings.get('Output_DB_Search', 'False')
        memory_mode = settings.get('Memory_Mode', 'Forced')
        Update_Bot_Personality_Description = settings.get('Update_Bot_Personality_Description', 'True')
        Use_Bot_Personality_Description = settings.get('Use_Bot_Personality_Description', 'True')
        backend_model = settings.get('Model_Backend', 'Llama_2')
        Print_Personality_Description = settings.get('Print_Personality_Descriptions', 'True')
        timestamp = time()
        botnameupper = bot_name.upper()
        usernameupper = username.upper()
        timestring = timestamp_to_datetime(timestamp)
        auto = list()
        personality_list = list()
        personality_update = list()
        
        if backend_model == "Llama_2":
            inner_loop_response = await Implicit_Memory_Call(prompt_implicit, username, bot_name)
        
        if backend_model == "Open_Ai":
            inner_loop_response = Implicit_Memory_Call(prompt_implicit, username, bot_name)
        
        inner_loop_db = inner_loop_response
        paragraph = inner_loop_db
        vector = embeddings(paragraph)
        base_path = "./Aetherius_API/Chatbot_Prompts"
        base_prompts_path = os.path.join(base_path, "Base")
        user_bot_path = os.path.join(base_path, user_id, bot_name) 
        if not os.path.exists(user_bot_path):
            os.makedirs(user_bot_path)
        if backend_model == "Llama_2":
            user_input_end = "[/INST]"
            user_input_start = "[INST]"
        if backend_model == "Open_Ai":
            user_input_end = ""
            user_input_start = ""
        prompts_json_path = os.path.join(user_bot_path, "prompts.json")
        base_prompts_json_path = os.path.join(base_prompts_path, "prompts.json")
        if not os.path.exists(prompts_json_path) and os.path.exists(base_prompts_json_path):
            async with aiofiles.open(base_prompts_json_path, 'r') as base_file:
                base_prompts_content = await base_file.read()
            async with aiofiles.open(prompts_json_path, 'w') as user_file:
                await user_file.write(base_prompts_content)
        async with aiofiles.open(prompts_json_path, 'r') as file:
            prompts = json.loads(await file.read())
        main_prompt = prompts["main_prompt"].replace('<<NAME>>', bot_name)
        secondary_prompt = prompts["secondary_prompt"]
        greeting_msg = prompts["greeting_prompt"].replace('<<NAME>>', bot_name)
        if memory_mode == 'Auto': 
            auto_count = 0
            auto.clear()
            auto.append({'role': 'system', 'content': "CURRENT SYSTEM PROMPT: You are a sub-module designed to reflect on your thought process. You are only able to respond with integers on a scale of 1-10, being incapable of printing letters.\n"})
            auto.append({'role': 'user', 'content': f"USER INPUT: {user_input}\nCHATBOTS INNER THOUGHTS: {output_one}\nPlease rate the chatbot's inner thoughts on a scale of 1 to 10. The rating will be directly input into a field, so ensure you only print a single number between 1 and 10. You are incapable of responding with anything other than a single number. {user_input_end}"})
            auto.append({'role': 'assistant', 'content': f"RATING: Sure, here is a numerical rating between 1 and 10: "})

            auto_int = None
            while auto_int is None:
                if backend_model == "Llama_2":
                    prompt = ''.join([message_dict['content'] for message_dict in auto])
                    automemory = await Auto_Call(prompt, username, bot_name)
                    
                if backend_model == "Open_Ai":
                    automemory = Auto_Call(auto, username, bot_name)
             #   print(automemory)
                values_to_check = ["7", "8", "9", "10"]
                if any(val in automemory for val in values_to_check):
                    auto_int = ('Pass')
                    segments = re.split(r'•|\n\s*\n', inner_loop_response)
                    total_segments = len(segments)
                    print("\n\nIMPLICIT MEMORIES:")
                    for index, segment in enumerate(segments):
                        segment = segment.strip()
                        if segment == '': 
                            continue  
                        if index == total_segments - 1 and not segment[-1] in ['.', '!', '?']:
                            continue
                        payload = list()   
                        collection_name = f"Bot_{bot_name}_Implicit_Short_Term"
                        print(f"{segment}")
                        try:
                            collection_info = client.get_collection(collection_name=collection_name)
                        except:
                            client.create_collection(
                                collection_name=collection_name,
                                vectors_config=VectorParams(size=embed_size, distance=Distance.COSINE),
                            )
                        vector1 = embeddings(segment)
                        unique_id = str(uuid4())
                        point_id = unique_id + str(int(timestamp))
                        metadata = {
                            'bot': bot_name,
                            'time': timestamp,
                            'message': segment,
                            'timestring': timestring,
                            'uuid': unique_id,
                            'user': user_id,
                            'memory_type': 'Implicit_Short_Term',
                        }
                        client.upsert(collection_name=collection_name,
                                             points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])  
                        payload.clear()
                        
                        # Add loop for removing redundant information in assosiation process.
                         
                    else:
                        break
                        
                values_to_check2 = ["1", "2", "3", "4", "5", "6"]
                if any(val in automemory for val in values_to_check2):
                    print("\nMemories not worthy of Upload")
                    break
                else:
                    auto_int = None
                    auto_count += 1
                    if auto_count > 2:
                        print('\nAuto Memory Failed')
                        break
            else:
                pass   
                
        if memory_mode == 'Forced':
            segments = re.split(r'•|\n\s*\n', inner_loop_response)
            total_segments = len(segments)
            print("\n\nIMPLICIT MEMORIES:")
            for index, segment in enumerate(segments):
                segment = segment.strip()
                if segment == '': 
                    continue  
                if index == total_segments - 1 and not segment[-1] in ['.', '!', '?']:
                    continue
                payload = list()   
                collection_name = f"Bot_{bot_name}_Implicit_Short_Term"
                print(f"{segment}")
                try:
                    collection_info = client.get_collection(collection_name=collection_name)
                except:
                    client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(size=embed_size, distance=Distance.COSINE),
                    )
                vector1 = embeddings(segment)
                unique_id = str(uuid4())
                point_id = unique_id + str(int(timestamp))
                metadata = {
                    'bot': bot_name,
                    'time': timestamp,
                    'message': segment,
                    'timestring': timestring,
                    'uuid': unique_id,
                    'user': user_id,
                    'memory_type': 'Implicit_Short_Term',
                }
                client.upsert(collection_name=collection_name,
                                     points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])  
                payload.clear()
                
                
        if memory_mode == 'Training':
            print(f"\n\nUpload Implicit Memories?\n{inner_loop_response}\n\n")
            mem_upload_yescheck = input("Enter 'Y' or 'N': ")
            if mem_upload_yescheck.upper == 'Y':
                await Upload_Implicit_Short_Term_Memories(inner_loop_response, username, user_id, bot_name)
                
        if Update_Bot_Personality_Description == 'True':        
            file_path = f"./Chatbot_Personalities/{bot_name}/{user_id}/{bot_name}_personality_file.txt"
            if not os.path.exists(file_path):
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                default_prompts = f"{main_prompt}\n{secondary_prompt}\n{greeting_msg}"

                async def write_prompts():
                    try:
                        # Specify encoding as utf-8 when writing to the file
                        async with aiofiles.open(file_path, 'w', encoding='utf-8') as txt_file:
                            await txt_file.write(default_prompts)
                    except Exception as e:
                        print(f"Failed to write to file: {e}")
                await write_prompts()

            try:
                # Specify encoding as utf-8 when reading from the file
                async with aiofiles.open(file_path, mode='r', encoding='utf-8') as file:
                    personality_file = await file.read()
            except FileNotFoundError:
                personality_file = "File not found."

                
                
            
            personality_list.append({'role': 'system', 'content': f"You are a sub-module for the autonomous Ai Entity {bot_name}.  Your job is to decide if the generated implicit memories fit {bot_name}'s personality.  If the generated memories match {bot_name}'s personality, print: 'YES'.  If they do not match the personality or if it contains conflicting information, print: 'NO'.{user_input_end}"})
            personality_list.append({'role': 'assistant', 'content': f"I will only print 'YES' or 'NO' in determination of if the given implicit memories match {bot_name}'s personality."})
            personality_list.append({'role': 'user', 'content': f"{user_input_start} Please return your personality file and your generated implicit memories. {user_input_end}"})
            personality_list.append({'role': 'assistant', 'content': f"{botnameupper}'S PERSONALITY: {personality_file}"})
            personality_list.append({'role': 'assistant', 'content': f"GENERATED IMPLICIT MEMORIES: {inner_loop_response}"})
            personality_list.append({'role': 'user', 'content': f"Now, please provide your 'YES' or 'NO' answer."})
            
            if backend_model == "Llama_2":
                prompt = ''.join([message_dict['content'] for message_dict in personality_list])
                personality_check = await Bot_Personality_Check_Call(prompt, username, bot_name)
                
            if backend_model == "Open_Ai":
                personality_check = Bot_Personality_Check_Call(personality_list, username, bot_name)
                  
            print(f"\n\nPERSONALITY CHECK: {personality_check}")
                
                
            if 'YES' in personality_check.upper():
                personality_update.append({'role': 'system', 'content': f"You are tasked with the delicate updating of the personality list for the AI entity, {bot_name}. Your main objective is to assimilate any vital and outstanding information from {bot_name}'s implicit memories into the personality list while maintaining utmost fidelity to the original content. Minimize modifications and intertwine any new information subtly and congruently within the established framework. The original personality data must remain predominantly unaltered. {user_input_end}"})
                personality_update.append({'role': 'assistant', 'content': f"I will attentively update the personality description, ensuring any amendments are warranted and essential."})
                personality_update.append({'role': 'user', 'content': f"{user_input_start} Please provide your current personality file along with the generated implicit memories. {user_input_end}"})
                personality_update.append({'role': 'user', 'content': f"PERSONALITY LIST: {personality_file}"})
                personality_update.append({'role': 'assistant', 'content': f"IMPLICIT MEMORIES: {inner_loop_response}"})
                personality_update.append({'role': 'user', 'content': f"{user_input_start} Kindly return the refined personality list in a single paragraph. Note that you'll be writing directly to the personality file; refrain from conversational responses and only output the updated list. Please write in the third person. {user_input_end}"})
                personality_update.append({'role': 'assistant', 'content': f"{botnameupper}'S PERSONALITY LIST: "})
                if backend_model == "Llama_2":
                    prompt = ''.join([message_dict['content'] for message_dict in personality_update])
                    personality_gen = await Bot_Personality_Generation_Call(prompt, username, bot_name)
                    
                if backend_model == "Open_Ai":
                    personality_gen = Bot_Personality_Generation_Call(personality_update, username, bot_name)
                    
                if ':' in personality_gen:
                    personality_gen = personality_gen.split(':', 1)[1].strip()
                
                if Print_Personality_Description == "True":
                    print(f"\n\nPRINT OF BOT PERSONALITY FILE: {personality_gen}")
                new_personality_content = personality_gen
                
                def safe_encode(content):
                    return content.encode('utf-8', errors='ignore').decode('utf-8')

                # Use the safe_encode function before writing to the file
                async with aiofiles.open(file_path, 'w', encoding='utf-8') as file:
                    safe_content = safe_encode(new_personality_content)
                    await file.write(safe_content)

                
    except Exception as e:
        traceback_details = traceback.format_exc()  # This will give you the full traceback
        print(f"\nERROR WITH IMPLICIT MEM MODULE: {e}")
        print(traceback_details) 
        
        
async def Upload_Implicit_Short_Term_Memories(query, username, user_id, bot_name):
    with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
    embed_size = settings['embed_size']   
    backend_model = settings.get('Model_Backend', 'Llama_2')    
    timestamp = time()
    timestring = timestamp_to_datetime(timestamp)
    payload = list()
    payload = list()    
    collection_name = f"Bot_{bot_name}_Implicit_Short_Term"
    try:
        collection_info = client.get_collection(collection_name=collection_name)
    except:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=embed_size, distance=Distance.COSINE),
        )
    vector1 = embeddings(query)
    unique_id = str(uuid4())
    point_id = unique_id + str(int(timestamp))
    metadata = {
        'bot': bot_name,
        'time': timestamp,
        'message': query,
        'timestring': timestring,
        'uuid': unique_id,
        'user': user_id,
        'memory_type': 'Implicit_Short_Term',
    }
    client.upsert(collection_name=collection_name,
                         points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])    
    return query
    
    
async def Aetherius_Explicit_Memory(user_input, vector_input, vector_monologue, output_one, response_two, bot_name, username, user_id, prompt_explicit):
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        API = settings.get('API', 'AetherNode')
        if API == "Oobabooga":
            HOST = settings.get('HOST_Oobabooga', 'http://localhost:5000/api')
        if API == "AetherNode":
            HOST = settings.get('HOST_AetherNode', 'http://127.0.0.1:8000')
        embed_size = settings['embed_size']
        DB_Search_Output = settings.get('Output_DB_Search', 'False')
        memory_mode = settings.get('Memory_Mode', 'Forced')
        Update_User_Personality_Description = settings.get('Update_Bot_Personality_Description', 'True')
        Use_User_Personality_Description = settings.get('Use_User_Personality_Description', 'True')
        backend_model = settings.get('Model_Backend', 'Llama_2')
        Print_Personality_Description = settings.get('Print_Personality_Descriptions', 'True')
        usernameupper = username.upper()
        botnameupper = bot_name.upper()
        base_path = "./Aetherius_API/Chatbot_Prompts"
        base_prompts_path = os.path.join(base_path, "Base")
        user_bot_path = os.path.join(base_path, user_id, bot_name)  
        if not os.path.exists(user_bot_path):
            os.makedirs(user_bot_path)
        if backend_model == "Llama_2":
            user_input_end = "[/INST]"
            user_input_start = "[INST]"
        if backend_model == "Open_Ai":
            user_input_end = ""
            user_input_start = ""
        prompts_json_path = os.path.join(user_bot_path, "prompts.json")
        base_prompts_json_path = os.path.join(base_prompts_path, "prompts.json")
        if not os.path.exists(prompts_json_path) and os.path.exists(base_prompts_json_path):
            async with aiofiles.open(base_prompts_json_path, 'r') as base_file:
                base_prompts_content = await base_file.read()
            async with aiofiles.open(prompts_json_path, 'w') as user_file:
                await user_file.write(base_prompts_content)
        async with aiofiles.open(prompts_json_path, 'r') as file:
            prompts = json.loads(await file.read())
        main_prompt = prompts["main_prompt"].replace('<<NAME>>', bot_name)
        secondary_prompt = prompts["secondary_prompt"]
        greeting_msg = prompts["greeting_prompt"].replace('<<NAME>>', bot_name)
        timestamp = time()
        timestring = timestamp_to_datetime(timestamp)
        personality_list = list()
        personality_update = list()
        auto = list()
        if backend_model == "Llama_2":
            db_upload = await Explicit_Memory_Call(prompt_explicit, username, bot_name)
        if backend_model == "Open_Ai":
            db_upload = Explicit_Memory_Call(prompt_explicit, username, bot_name)
        db_upsert = db_upload
        if memory_mode == 'Auto': 
            auto_count = 0
            auto.clear()
            
            
            auto.append({'role': 'system', 'content': "CURRENT SYSTEM PROMPT: You are a sub-module designed to reflect on your response to the user. You are only able to respond with integers on a scale of 1-10, being incapable of printing letters.\n"})
            auto.append({'role': 'user', 'content': f"USER INPUT: {user_input} CHATBOTS RESPONSE: {response_two}\nPlease rate the chatbot's response on a scale of 1 to 10. The rating will be directly input into a field, so ensure you only print a single number between 1 and 10. You are incapable of responding with anything other than a single number. {user_input_end}"})
            auto.append({'role': 'assistant', 'content': f"RATING: Sure, here is a numerical rating between 1 and 10: "})
            
            
            auto_int = None
            while auto_int is None:
                if backend_model == "Llama_2":
                    prompt = ''.join([message_dict['content'] for message_dict in auto])
                    automemory = await Auto_Call(prompt, username, bot_name)
                    
                if backend_model == "Open_Ai":
                    automemory = Auto_Call(auto, username, bot_name)
                    
          #      print(f"EXPLICIT RATING: {automemory}")
                values_to_check = ["7", "8", "9", "10"]
                if any(val in automemory for val in values_to_check):
                    auto_int = ('Pass')
                    segments = re.split(r'•|\n\s*\n', db_upsert)
                    total_segments = len(segments)
                    print("\n\nEXPLICIT MEMORIES:")
                    for index, segment in enumerate(segments):
                        segment = segment.strip()
                        if segment == '': 
                            continue  
                        if index == total_segments - 1 and not segment[-1] in ['.', '!', '?']:
                            continue
                        print(f"{segment}")
                        payload = list()       
                        collection_name = f"Bot_{bot_name}_Explicit_Short_Term"
                        try:
                            collection_info = client.get_collection(collection_name=collection_name)
                        except:
                            client.create_collection(
                                collection_name=collection_name,
                                vectors_config=VectorParams(size=embed_size, distance=Distance.COSINE),
                            )
                        vector1 = embeddings(segment)
                        unique_id = str(uuid4())
                        point_id = unique_id + str(int(timestamp))
                        metadata = {
                            'bot': bot_name,
                            'time': timestamp,
                            'message': segment,
                            'timestring': timestring,
                            'uuid': unique_id,
                            'user': user_id,
                            'memory_type': 'Explicit_Short_Term',
                        }
                        client.upsert(collection_name=collection_name,
                                             points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])    
                        payload.clear()
                    else:
                        break
                values_to_check2 = ["1", "2", "3", "4", "5", "6"]
                if any(val in automemory for val in values_to_check2):
                    print("Memories not worthy of Upload")
                    break
                else:
                    auto_int = None
                    auto_count += 1
                    if auto_count > 2:
                        print('Auto Memory Failed')
                        break
            else:
                pass
            task = asyncio.create_task(Aetherius_Memory_Loop(user_input, username, user_id, bot_name, vector_input, vector_monologue, output_one, response_two))

        if memory_mode == 'Forced':
            try:
                segments = re.split(r'•|\n\s*\n', db_upsert)
                total_segments = len(segments)
                print("\n\nEXPLICIT MEMORIES:")
                for index, segment in enumerate(segments):
                    segment = segment.strip()
                    if segment == '': 
                        continue  
                    if index == total_segments - 1 and not segment[-1] in ['.', '!', '?']:
                        continue
                    print(f"{segment}")
                    payload = list()       
                    collection_name = f"Bot_{bot_name}_Explicit_Short_Term"
                    try:
                        collection_info = client.get_collection(collection_name=collection_name)
                    except:
                        client.create_collection(
                            collection_name=collection_name,
                            vectors_config=VectorParams(size=embed_size, distance=Distance.COSINE),
                        )
                    vector1 = embeddings(segment)
                    unique_id = str(uuid4())
                    point_id = unique_id + str(int(timestamp))
                    metadata = {
                        'bot': bot_name,
                        'time': timestamp,
                        'message': segment,
                        'timestring': timestring,
                        'uuid': unique_id,
                        'user': user_id,
                        'memory_type': 'Explicit_Short_Term',
                    }
                    client.upsert(collection_name=collection_name,
                                         points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])    
                    payload.clear()
            except Exception as e:
                print(e)
            task = asyncio.create_task(Aetherius_Memory_Loop(user_input, username, user_id, bot_name, vector_input, vector_monologue, output_one, response_two))
        
        if memory_mode == 'Training':
            print(f"\n\nUpload Explicit Memories?\n{db_upload}\n\n")
            db_upload_yescheck = ask_upload_explicit_memories(db_upsert)
            
            print(f"\n\nUpload Explicit Memories?\n{db_upload}\n\n")
            db_upload_yescheck = input("Enter 'Y' or 'N': ")
            if db_upload_yescheck.upper == 'Y':
                await Upload_Explicit_Short_Term_Memories(db_upsert, username, user_id, bot_name)

            if db_upload_yescheck.upper == 'Y':
                task = asyncio.create_task(Aetherius_Memory_Loop(user_input, username, user_id, bot_name, vector_input, vector_monologue, output_one, response_two))
                
        if Update_User_Personality_Description == 'True':
            file_path = f"./Chatbot_Personalities/{bot_name}/{user_id}/{username}_personality_file.txt"
            if not os.path.exists(file_path):
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                default_prompts = f"The user {user_id} does not yet have a personality file."
                async def write_prompts():
                    try:
                        # Specify encoding as UTF-8 when writing the file
                        async with aiofiles.open(file_path, 'w', encoding='utf-8') as txt_file:
                            await txt_file.write(default_prompts)
                    except Exception as e:
                        print(f"\nFailed to write to file: {e}")
                await write_prompts()

            try:
                # Specify encoding as UTF-8 when reading the file
                async with aiofiles.open(file_path, mode='r', encoding='utf-8') as file:
                    personality_file = await file.read()
            except FileNotFoundError:
                personality_file = "File not found."
            
            personality_list.clear()
            personality_update.clear()



            personality_list.append({'role': 'system', 'content': f"You are a sub-module for the autonomous Ai Entity {bot_name}.  Your job is to extract any salient insights about {username} from their request, the given internal monologue, and {bot_name}'s final response. {user_input_end}"})
            personality_list.append({'role': 'assistant', 'content': f"I will extract any salient insights about the user from the given information."})
            personality_list.append({'role': 'user', 'content': f"{user_input_start} Please return the user's inquirythe given internal monologue, and {bot_name}'s final response. {user_input_end}"})
            personality_list.append({'role': 'assistant', 'content': f"{usernameupper}'S INQUIRY: {user_input}"})
            personality_list.append({'role': 'assistant', 'content': f"{botnameupper}'S INNER MONOLOGUE: {output_one}"})
            personality_list.append({'role': 'assistant', 'content': f"{botnameupper}'S FINAL RESPONSE: {response_two}"})
            personality_list.append({'role': 'user', 'content': f"{user_input_start} Now, please provide the extracted salient points about {username}. {user_input_end}"})

            if backend_model == "Llama_2":
                prompt = ''.join([message_dict['content'] for message_dict in personality_list])
                personality_extraction = await User_Personality_Extraction_Call(prompt, username, bot_name)
                
            if backend_model == "Open_Ai":
                personality_extraction = User_Personality_Extraction_Call(personality_list, username, bot_name)
                
            print(personality_extraction)
            
            
            personality_check = 'YES'   
            if 'YES' in personality_check.upper():
                personality_update.append({'role': 'system', 'content': f"You are tasked with the delicate updating of the personality description for the user, {username}. Your main objective is to assimilate any vital and outstanding information from the given explicit memories into the personality list while maintaining utmost fidelity to the original content. Minimize modifications and intertwine any new information subtly and congruently within the established framework. The original personality data must remain predominantly unaltered. {user_input_end}"})
                personality_update.append({'role': 'assistant', 'content': f"I will attentively update the user's personality description, ensuring any amendments are warranted and essential."})
                personality_update.append({'role': 'user', 'content': f"{user_input_start} Please provide your current personality file along with the generated explicit memories. {user_input_end}"})
                personality_update.append({'role': 'user', 'content': f"{usernameupper}'S PERSONALITY LIST: {personality_file}"})
                personality_update.append({'role': 'assistant', 'content': f"EXPLICIT MEMORIES: {personality_extraction}"})
                personality_update.append({'role': 'user', 'content': f"{user_input_start} Kindly return the refined user personality description in a single paragraph. Note that you'll be writing directly to the personality file; refrain from conversational responses and only output the updated description. Please write in the third person. {user_input_end}"})
                personality_update.append({'role': 'assistant', 'content': f"{usernameupper}'S PERSONALITY DESCRIPTION: "})

                if backend_model == "Llama_2":
                    prompt = ''.join([message_dict['content'] for message_dict in personality_update])
                    personality_gen = await User_Personality_Generation_Call(prompt, username, bot_name)
                    
                if backend_model == "Open_Ai":
                    personality_gen = User_Personality_Generation_Call(personality_update, username, bot_name)
                    
                if ':' in personality_gen:
                    personality_gen = personality_gen.split(':', 1)[1].strip()
                
                if Print_Personality_Description == "True":
                    print(f"\n\nPRINT OF USER PERSONALITY FILE: {personality_gen}")
                new_personality_content = personality_gen
                
                def safe_encode(content):
                    return content.encode('utf-8', errors='ignore').decode('utf-8')

                # Use the safe_encode function before writing to the file
                async with aiofiles.open(file_path, 'w', encoding='utf-8') as file:
                    safe_content = safe_encode(new_personality_content)
                    await file.write(safe_content)
    except Exception as e:
        traceback_details = traceback.format_exc()  # This will give you the full traceback
        print(f"\nERROR WITH IMPLICIT MEM MODULE: {e}")
        print(traceback_details) 
        
        
async def Upload_Heuristics(query, username, user_id, bot_name):
    with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
    embed_size = settings['embed_size']    
    backend_model = settings.get('Model_Backend', 'Llama_2')
    timestamp = time()
    timestring = timestamp_to_datetime(timestamp)
    payload = list()
    payload = list()    
    collection_name = f"Bot_{bot_name}"
    try:
        collection_info = client.get_collection(collection_name=collection_name)
    except:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=embed_size, distance=Distance.COSINE),
        )
    vector1 = embeddings(query)
    unique_id = str(uuid4())
    point_id = unique_id + str(int(timestamp))
    metadata = {
        'bot': bot_name,
        'time': timestamp,
        'message': query,
        'timestring': timestring,
        'uuid': unique_id,
        'user': user_id,
        'memory_type': 'Heuristics',
    }
    client.upsert(collection_name=collection_name,
                         points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])    
    return query
    
    
async def Upload_Explicit_Short_Term_Memories(query, username, user_id, bot_name):
    with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
    embed_size = settings['embed_size']    
    backend_model = settings.get('Model_Backend', 'Llama_2')
    timestamp = time()
    timestring = timestamp_to_datetime(timestamp)
    payload = list()
    payload = list()    
    collection_name = f"Bot_{bot_name}_Explicit_Short_Term"
    try:
        collection_info = client.get_collection(collection_name=collection_name)
    except:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=embed_size, distance=Distance.COSINE),
        )
    vector1 = embeddings(query)
    unique_id = str(uuid4())
    point_id = unique_id + str(int(timestamp))
    metadata = {
        'bot': bot_name,
        'time': timestamp,
        'message': query,
        'timestring': timestring,
        'uuid': unique_id,
        'user': user_id,
        'memory_type': 'Explicit_Short_Term',
    }
    client.upsert(collection_name=collection_name,
                         points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])    
    return query
    
    
async def Upload_Implicit_Long_Term_Memories(query, username, user_id, bot_name):
    with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
    embed_size = settings['embed_size']    
    backend_model = settings.get('Model_Backend', 'Llama_2')
    timestamp = time()
    timestring = timestamp_to_datetime(timestamp)
    payload = list()
    payload = list()    
    collection_name = f"Bot_{bot_name}"
    try:
        collection_info = client.get_collection(collection_name=collection_name)
    except:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=embed_size, distance=Distance.COSINE),
        )
    vector1 = embeddings(query)
    unique_id = str(uuid4())
    point_id = unique_id + str(int(timestamp))
    metadata = {
        'bot': bot_name,
        'time': timestamp,
        'message': query,
        'timestring': timestring,
        'uuid': unique_id,
        'user': user_id,
        'memory_type': 'Implicit_Long_Term',
    }
    client.upsert(collection_name=collection_name,
                         points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])    
    return query
    
    
async def Upload_Explicit_Long_Term_Memories(query, username, user_id, bot_name):
    with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
    embed_size = settings['embed_size']    
    timestamp = time()
    timestring = timestamp_to_datetime(timestamp)
    payload = list()
    payload = list()    
    collection_name = f"Bot_{bot_name}"
    try:
        collection_info = client.get_collection(collection_name=collection_name)
    except:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=embed_size, distance=Distance.COSINE),
        )
    vector1 = embeddings(query)
    unique_id = str(uuid4())
    point_id = unique_id + str(int(timestamp))
    metadata = {
        'bot': bot_name,
        'time': timestamp,
        'message': query,
        'timestring': timestring,
        'uuid': unique_id,
        'user': user_id,
        'memory_type': 'Explicit_Long_Term',
    }
    client.upsert(collection_name=collection_name,
                         points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])    
    return query
    
    
async def Aetherius_Memory_Loop(user_input, username, user_id, bot_name, vector_input, vector_monologue, output_one, response_two):
    with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
    embed_size = settings['embed_size']
    backend_model = settings.get('Model_Backend', 'Llama_2')
    DB_Search_Output = settings.get('Output_DB_Search', 'False')
    conversation = list()
    conversation2 = list()
    summary = list()
    auto = list()
    payload = list()
    consolidation  = list()
    counter = 0
    counter2 = 0
    importance_score = list()
    domain_extraction = list()
    mem_counter = 0
    with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
    length_config = int(settings['Conversation_Length'])
    conv_length = int(settings['Conversation_Length'])
    botnameupper = bot_name.upper()
    usernameupper = username.upper()
    base_path = "./Aetherius_API/Chatbot_Prompts"
    base_prompts_path = os.path.join(base_path, "Base")
    user_bot_path = os.path.join(base_path, user_id, bot_name) 
    if not os.path.exists(user_bot_path):
        os.makedirs(user_bot_path)
    prompts_json_path = os.path.join(user_bot_path, "prompts.json")
    base_prompts_json_path = os.path.join(base_prompts_path, "prompts.json")
    if not os.path.exists(prompts_json_path) and os.path.exists(base_prompts_json_path):
        async with aiofiles.open(base_prompts_json_path, 'r') as base_file:
            base_prompts_content = await base_file.read()
        async with aiofiles.open(prompts_json_path, 'w') as user_file:
            await user_file.write(base_prompts_content)
    async with aiofiles.open(prompts_json_path, 'r') as file:
        prompts = json.loads(await file.read())
    main_prompt = prompts["main_prompt"].replace('<<NAME>>', bot_name)
    secondary_prompt = prompts["secondary_prompt"]
    greeting_msg = prompts["greeting_prompt"].replace('<<NAME>>', bot_name)
    while True:
        if backend_model == "Llama_2":
            user_input_end = "[/INST]"
            user_input_start = "[INST]"
        if backend_model == "Open_Ai":
            user_input_end = ""
            user_input_start = ""
        a = user_input
        timestamp = time()
        timestring = timestamp_to_datetime(timestamp)
        counter += 1
        conversation.clear()
        conversation.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: You are a sub-module of {bot_name}, an AI entity designed for autonomous interaction. Your specialized function is to distill each conversation with {username} into a single, short and concise narrative sentence. This sentence should serve as {bot_name}'s autobiographical memory of the conversation, capturing the most significant events, context, and emotions experienced by either {bot_name} or {username}. Note that 'autobiographical memory' refers to a detailed recollection of a specific event, often including emotions and sensory experiences. Your task is to focus on preserving the most crucial elements without omitting key context or feelings. After that, please print the user's message followed by your response. {user_input_end}"})
        conversation.append({'role': 'user', 'content': f"USER: {a}\n"})
        conversation.append({'role': 'user', 'content': f"{botnameupper}'s INNER MONOLOGUE: {output_one}\n"})
        conversation.append({'role': 'user', 'content': f"{botnameupper}'S FINAL RESPONSE: {response_two}"})
        conversation.append({'role': 'user', 'content': f"{user_input_start} Please now generate an autobiographical memory for {bot_name}. {user_input_end}"})
        conversation.append({'role': 'assistant', 'content': f"THIRD-PERSON AUTOBIOGRAPHICAL MEMORY: "})

        if backend_model == "Llama_2":
            prompt = ''.join([message_dict['content'] for message_dict in conversation])
            conv_summary = await Episodic_Memory_Call(prompt, username, bot_name)
            
        if backend_model == "Open_Ai":
            conv_summary = Episodic_Memory_Call(conversation, username, bot_name)
        
            
        sentences = re.split(r'(?<=[.!?])\s+', conv_summary)
        if sentences and not re.search(r'[.!?]$', sentences[-1]):
            sentences.pop()
        conv_summary = ' '.join(sentences)
        collection_name = f"Bot_{bot_name}" 
        try:
            collection_info = client.get_collection(collection_name=collection_name)
        except:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=embed_size, distance=Distance.COSINE),
            )
        episodic_msg = f'{timestring} - {conv_summary}'
        vector1 = embeddings(episodic_msg)
        unique_id = str(uuid4())
        importance_score.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: You are a sub-module of {bot_name}, an autonomous AI entity. Your function is to process a given memory and rate its importance to personal development and/or its ability to impact the greater world.  You are to give the rating on a scale of 1-100.\n"})
        importance_score.append({'role': 'system', 'content': f"{botnameupper}'S MAIN PROMPT: {main_prompt}\n"})
        importance_score.append({'role': 'system', 'content': f"{botnameupper}'S SECONDARY PROMPT: {secondary_prompt}\n"})
        importance_score.append({'role': 'system', 'content': f"{botnameupper}'S GREETING MESSAGE: {greeting_msg}\n"})
        importance_score.append({'role': 'system', 'content': f"MEMORY TO RATE: {episodic_msg}\n"})
        importance_score.append({'role': 'system', 'content': f"{usernameupper}: Please now rate the given memory on a scale of 1-100. Only print the numerical rating as a digit. {user_input_end}"})
        importance_score.append({'role': 'system', 'content': f"{botnameupper}: Sure thing! Here's the memory rated on a scale of 1-100:\nRating: "})
        if backend_model == "Llama_2":
            prompt = ''.join([message_dict['content'] for message_dict in importance_score])
        score = 75
        importance_score.clear()
        metadata = {
            'bot': bot_name,
            'user': user_id,
            'time': timestamp,
            'rating': score,
            'message': episodic_msg,
            'timestring': timestring,
            'uuid': unique_id,
            'memory_type': 'Episodic',
        }
        client.upsert(collection_name=collection_name,
                             points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])   
        payload.clear()
        collection_name = f"Flash_Counter_Bot_{bot_name}_{user_id}"
        try:
            collection_info = client.get_collection(collection_name=collection_name)
        except:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=embed_size, distance=Distance.COSINE),
            )
            
        vector1 = embeddings(timestring)
        unique_id = str(uuid4())
        metadata = {
            'bot': bot_name,
            'user': user_id,
            'time': timestamp,
            'message': timestring,
            'timestring': timestring,
            'uuid': unique_id,
            'memory_type': 'Flash_Counter',
        }
        client.upsert(collection_name=collection_name,
                             points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])   
        payload.clear()
        
        # # Flashbulb Memory Generation
        collection_name = f"Flash_Counter_Bot_{bot_name}_{user_id}"
        try:
            collection_info = client.get_collection(collection_name=collection_name)
        except:
            collection_info.vectors_count = 0
        if collection_info.vectors_count > 8:
            flash_db = None
            try:
                hits = client.search(
                    collection_name=f"Bot_{bot_name}",
                    query_vector=vector_input,
                    query_filter=Filter(
                        must=[
                            FieldCondition(
                                key="memory_type",
                                match=MatchValue(value="Episodic"),
                            ),
                            FieldCondition(
                                key="user",
                                match=models.MatchValue(value=f"{user_id}"),
                            ),
                        ]
                    ),
                    limit=5
                )
                flash_db = [hit.payload['message'] for hit in hits]
            except Exception as e:
                if "Not found: Collection" in str(e):
                    print("\nCollection does not exist.")
                else:
                    print(f"\nAn unexpected error occurred: {str(e)}")
                
            flash_db1 = None
            try:
                hits = client.search(
                    collection_name=f"Bot_{bot_name}",
                    query_vector=vector_monologue,
                    query_filter=Filter(
                        must=[
                            FieldCondition(
                                key="memory_type",
                                match=MatchValue(value="Implicit_Long_Term"),
                            ),
                            FieldCondition(
                                key="user",
                                match=models.MatchValue(value=f"{user_id}"),
                            ),

                        ]
                    ),
                    limit=8
                )
                flash_db1 = [hit.payload['message'] for hit in hits]
            except Exception as e:
                if "Not found: Collection" in str(e):
                    print("\nCollection does not exist.")
                else:
                    print(f"\nAn unexpected error occurred: {str(e)}")
            # # Generate Flashbulb Memory
            consolidation.append({'role': 'system', 'content': "Main System Prompt: As a data extractor, your role is to read the provided episodic memories and emotional reactions. Extract emotional information corresponding to each memory and then combine these to form flashbulb memories. Only include memories strongly tied to emotions. Format the flashbulb memories as bullet points using the template: •[flashbulb memory]. Then, create and present the final list of flashbulb memories.\n"})
            consolidation.append({'role': 'user', 'content': f"EMOTIONAL REACTIONS: {flash_db}\nEPISODIC MEMORIES: {flash_db1} {user_input_end}"})
            consolidation.append({'role': 'user', 'content': f"{user_input_start} FORMAT: Use the format: •[Flashbulb Memory] {user_input_end}"})
            consolidation.append({'role': 'assistant', 'content': f"{botnameupper}: I will now combine the extracted data to form flashbulb memories in bullet point format, combining associated data. I will only include memories with a strong emotion attached: "})
            if backend_model == "Llama_2":
                prompt = ''.join([message_dict['content'] for message_dict in consolidation])
                flash_response = await Flash_Memory_Call(prompt, username, bot_name)
                
            if backend_model == "Open_Ai":
                flash_response = Flash_Memory_Call(consolidation, username, bot_name)
                
        #    memories = results
            segments = re.split(r'•|\n\s*\n', flash_response)
            for segment in segments:
                if segment.strip() == '':
                    continue  
                else:
                    # Define the collection name
                    collection_name = f"Bot_{bot_name}"
                    try:
                        collection_info = client.get_collection(collection_name=collection_name)
                    except:
                        client.create_collection(
                            collection_name=collection_name,
                            vectors_config=VectorParams(size=embed_size, distance=Distance.COSINE),
                        )
                    vector1 = embeddings(segment)
                    unique_id = str(uuid4())
                    flash_mem = f'{timestring} - {segment}'
                    importance_score.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: You are a sub-module of {bot_name}, an autonomous AI entity. Your function is to process a given memory and rate its importance to personal development and/or its ability to impact the greater world.  You are to give the rating on a scale of 1-100.\n"})
                    importance_score.append({'role': 'system', 'content': f"{botnameupper}'S MAIN PROMPT: {main_prompt}\n"})
                    importance_score.append({'role': 'system', 'content': f"{botnameupper}'S SECONDARY PROMPT: {secondary_prompt}\n"})
                    importance_score.append({'role': 'system', 'content': f"{botnameupper}'S GREETING MESSAGE: {greeting_msg}\n"})
                    importance_score.append({'role': 'system', 'content': f"MEMORY TO RATE: {flash_mem}\n"})
                    importance_score.append({'role': 'system', 'content': f"{usernameupper}: Please now rate the given memory on a scale of 1-100. Only print the numerical rating as a digit. {user_input_end}"})
                    importance_score.append({'role': 'system', 'content': f"{botnameupper}: Sure thing! Here's the memory rated on a scale of 1-100:\nRating: "})
                    if backend_model == "Llama_2":
                        prompt = ''.join([message_dict['content'] for message_dict in importance_score])
                    score = 75
                    # print(score)
                    importance_score.clear()
                    metadata = {
                        'bot': bot_name,
                        'user': user_id,
                        'time': timestamp,
                        'rating': score,
                        'message': flash_mem,
                        'timestring': timestring,
                        'uuid': unique_id,
                        'memory_type': 'Flashbulb',
                    }
                    client.upsert(collection_name=collection_name,
                                         points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])   
                    payload.clear()
            client.delete(
                collection_name=f"Flash_Counter_Bot_{bot_name}_{user_id}",
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="user",
                                match=models.MatchValue(value=f"{user_id}"),
                            ),
                        ],
                    )
                ),
            ) 
            
        # # Short Term Memory Consolidation based on amount of vectors in namespace    
        collection_name = f"Bot_{bot_name}_Explicit_Short_Term"
        try:
            collection_info = client.get_collection(collection_name=collection_name)
        except:
            collection_info.vectors_count = 0
        if collection_info.vectors_count > 23:
            try:
                consolidation.clear()
                memory_consol_db = None
                        
                try:
                    hits = client.search(
                        collection_name=f"Bot_{bot_name}_Explicit_Short_Term",
                        query_vector=vector_input,
                        query_filter=Filter(
                            must=[
                                FieldCondition(
                                    key="user",
                                    match=MatchValue(value=f"{user_id}")
                                )
                            ]
                        ),
                        limit=20
                    )
                    memory_consol_db = [hit.payload['message'] for hit in hits]
               #     print(memory_consol_db)
                except Exception as e:
                    if "Not found: Collection" in str(e):
                        print("\nCollection does not exist.")
                    else:
                        print(f"\nAn unexpected error occurred: {str(e)}")
                except Exception as e:
                    if "Not found: Collection" in str(e):
                        print("\nCollection does not exist.")
                    else:
                        print(f"\nAn unexpected error occurred: {str(e)}")

                consolidation.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: {main_prompt}\n\n"})
                consolidation.append({'role': 'system', 'content': f"LOG: {memory_consol_db}\n\nSYSTEM: Read the Log and combine the similar topics from the given short term memories into a bullet point list to serve as {bot_name}'s long term memories. Each summary should contain the entire context of the memory. Follow the format •[memory] {user_input_end} "})
                consolidation.append({'role': 'assistant', 'content': f"{botnameupper}: Sure, here is the list of consolidated memories: "})
                if backend_model == "Llama_2":
                    prompt = ''.join([message_dict['content'] for message_dict in consolidation])
                    memory_consol = await Memory_Consolidation_Call(prompt, username, bot_name)
                    
                if backend_model == "Open_Ai":
                    memory_consol = Memory_Consolidation_Call(consolidation, username, bot_name)
                    
                if DB_Search_Output == 'True':
                    print(f"\n\nEXPLICIT MEMORY CONSOLIDATION:\n{memory_consol}")
                    print('\n-----------------------\n')
                segments = re.split(r'•|\n\s*\n', memory_consol)
                for segment in segments:
                    if segment.strip() == '':
                        continue 
                    else:
             #           print(segment)
                        collection_name = f"Bot_{bot_name}"
                        try:
                            collection_info = client.get_collection(collection_name=collection_name)
                        except:
                            client.create_collection(
                                collection_name=collection_name,
                                vectors_config=VectorParams(size=embed_size, distance=Distance.COSINE),
                            )
                        vector1 = embeddings(segment)
                        unique_id = str(uuid4())
                        importance_score.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: You are a sub-module of {bot_name}, an autonomous AI entity. Your function is to process a given memory and rate its importance to personal development and/or its ability to impact the greater world.  You are to give the rating on a scale of 1-100.\n"})
                        importance_score.append({'role': 'system', 'content': f"{botnameupper}'S MAIN PROMPT: {main_prompt}\n"})
                        importance_score.append({'role': 'system', 'content': f"{botnameupper}'S SECONDARY PROMPT: {secondary_prompt}\n"})
                        importance_score.append({'role': 'system', 'content': f"{botnameupper}'S GREETING MESSAGE: {greeting_msg}\n"})
                        importance_score.append({'role': 'system', 'content': f"MEMORY TO RATE: {segment}\n"})
                        importance_score.append({'role': 'system', 'content': f"{usernameupper}: Please now rate the given memory on a scale of 1-100. Only print the numerical rating as a digit. {user_input_end}"})
                        importance_score.append({'role': 'system', 'content': f"{botnameupper}: Sure thing! Here's the memory rated on a scale of 1-100:\nRating: "})
                        
                        prompt = ''.join([message_dict['content'] for message_dict in importance_score])
                        score = 75
                        importance_score.clear()
                        
                        
                        domain_extraction.append({'role': 'system', 'content': f"You are a knowledge domain extractor.  Your task is to analyze the user's inquiry, then extract the single most salent generalized knowledge domain needed to complete the user's inquiry.  Your response should be a single word.\n"})
                        domain_extraction.append({'role': 'user', 'content': f"USER INPUT: {segment} {user_input_end} "})
                        
                        if backend_model == "Llama_2":
                            prompt = ''.join([message_dict['content'] for message_dict in domain_extraction])
                            extracted_domain = await Domain_Extraction_Call(prompt, username, bot_name)
                            
                        if backend_model == "Open_Ai":
                            extracted_domain = Domain_Extraction_Call(domain_extraction, username, bot_name)
                            
                            
                        if ":" in extracted_domain:
                            extracted_domain = extracted_domain.split(":")[-1]
                        extracted_domain = extracted_domain.replace("\n", "")
                        extracted_domain = extracted_domain.upper()
                        extracted_domain = re.sub(r'[^A-Z]', '', extracted_domain)
                        extracted_domain = extracted_domain.replace("_", " ")
                        domain_extraction.clear()
                        
                        metadata = {
                            'bot': bot_name,
                            'user': user_id,
                            'time': timestamp,
                            'rating': score,
                            'message': segment,
                            'knowledge_domain': extracted_domain,
                            'timestring': timestring,
                            'uuid': unique_id,
                            'memory_type': 'Explicit_Long_Term',
                        }
                        client.upsert(collection_name=collection_name,
                                             points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])   
                        payload.clear()
                        
                        
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
                                limit=20
                            )
                            domain_search = [hit.payload['knowledge_domain'] for hit in hits]
                        except Exception as e:
                            if "Not found: Collection" in str(e):
                                print("\nCollection does not exist.")
                                domain_search = "No Collection"
                            else:
                                print(f"\nAn unexpected error occurred: {str(e)}")
                        
                        
                        if extracted_domain not in domain_search:
                            collection_name = f"Bot_{bot_name}_Knowledge_Domains"
                            # Create the collection only if it doesn't exist
                            try:
                                collection_info = client.get_collection(collection_name=collection_name)
                            except:
                                client.create_collection(
                                    collection_name=collection_name,
                                    vectors_config=VectorParams(size=embed_size, distance=Distance.COSINE),
                                )
                            unique_id = str(uuid4())
                            metadata = {
                                'bot': bot_name,
                                'user': user_id,
                                'knowledge_domain': extracted_domain,
                                'uuid': unique_id,
                            }
                            client.upsert(collection_name=collection_name,
                                                 points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])   
                            payload.clear()
                        
                        
                client.delete(
                    collection_name=f"Bot_{bot_name}_Explicit_Short_Term",
                    points_selector=models.FilterSelector(
                        filter=models.Filter(
                            must=[
                                models.FieldCondition(
                                    key="user",
                                    match=models.MatchValue(value=f"{user_id}"),
                                ),
                            ],
                        )
                    ),
                ) 
                
                collection_name = f'Consol_Counter_Bot_{bot_name}_{user_id}'
                try:
                    collection_info = client.get_collection(collection_name=collection_name)
                except:
                    client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=embed_size, distance=Distance.COSINE),
                    )
                vector1 = embeddings(segment)
                unique_id = str(uuid4())
                metadata = {
                    'bot': bot_name,
                    'user': user_id,
                    'time': timestamp,
                    'message': segment,
                    'timestring': timestring,
                    'uuid': unique_id,
                    'memory_type': 'Consol_Counter',
                }
                client.upsert(collection_name=f'Consol_Counter_Bot_{bot_name}_{user_id}',
                    points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])   
                payload.clear()
                consolidation.clear()
                
                
                # # Implicit Short Term Memory Consolidation based on amount of vectors in namespace
                collection_name = f"Consol_Counter_Bot_{bot_name}_{user_id}"
                collection_info = client.get_collection(collection_name=collection_name)
                if collection_info.vectors_count % 2 == 0:
                    consolidation.clear()
                    memory_consol_db2 = None
      
                    try:
                        hits = client.search(
                            collection_name=f"Bot_{bot_name}_Implicit_Short_Term",
                            query_vector=vector_input,
                            query_filter=Filter(
                                must=[
                                    FieldCondition(
                                        key="user",
                                        match=MatchValue(value=f"{user_id}")
                                    )
                                ]
                            ),
                            limit=25
                        )
                        memory_consol_db2 = [hit.payload['message'] for hit in hits]
                    except Exception as e:
                        if "Not found: Collection" in str(e):
                            print("\nCollection does not exist.")
                        else:
                            print(f"\nAn unexpected error occurred: {str(e)}") 

                    consolidation.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: {main_prompt}\n\n"})
                    consolidation.append({'role': 'system', 'content': f"LOG: {memory_consol_db2}\n\nSYSTEM:  Read the Log and combine the similar topics from the given short term memories into a bullet point list to serve as {bot_name}'s long term memories. Each summary should contain the entire context of the memory. Follow the format: •[memory] {user_input_end} "})
                    consolidation.append({'role': 'assistant', 'content': f"{bot_name}: Sure, here is the list of consolidated memories: "})
                    if backend_model == "Llama_2":
                        prompt = ''.join([message_dict['content'] for message_dict in consolidation])
                        memory_consol2 = await Memory_Consolidation_Call(prompt, username, bot_name)
                        
                    if backend_model == "Open_Ai":
                        memory_consol2 = Memory_Consolidation_Call(consolidation, username, bot_name)
                        
                    consolidation.clear()
             #       print('Finished.\nRemoving Redundant Memories.')
                    vector_sum = embeddings(memory_consol2)
                    memory_consol_db3 = None
                    try:
                        hits = client.search(
                            collection_name=f"Bot_{bot_name}",
                            query_vector=vector_sum,
                            query_filter=Filter(
                                must=[
                                    FieldCondition(
                                        key="memory_type",
                                        match=MatchValue(value="Implicit_Long_Term"),
                                    ),
                                    FieldCondition(
                                        key="user",
                                        match=MatchValue(value=f"{user_id}"),
                                    ),
                                ]
                            ),
                            limit=8
                        )
                        memory_consol_db3 = [hit.payload['message'] for hit in hits]
                    except Exception as e:
                        memory_consol_db3 = 'Failed Lookup'
                        if "Not found: Collection" in str(e):
                            print("\nCollection does not exist.")
                        else:
                            print(f"\nAn unexpected error occurred: {str(e)}")
                            
                            
                            
                    consolidation.append({'role': 'system', 'content': f"{main_prompt}\n\n"})
                    consolidation.append({'role': 'system', 'content': f"IMPLICIT LONG TERM MEMORY: {memory_consol_db3}\n\nIMPLICIT SHORT TERM MEMORY: {memory_consol_db2}\n\nRESPONSE: Compare your short-term memories and the given Long Term Memories, then, remove any duplicate information from your Implicit Short Term memory that is already found in your Long Term Memory. After this is done, consolidate similar topics into a new set of memories. Each summary should contain the entire context of the memory. Use the following format: •[memory] {user_input_end} "})
                    consolidation.append({'role': 'assistant', 'content': f"{botnameupper}: Sure, here is the list of consolidated memories: "})
                    
                    if backend_model == "Llama_2":
                        prompt = ''.join([message_dict['content'] for message_dict in consolidation])
                        memory_consol3 = await Memory_Consolidation_Call(prompt, username, bot_name)
                        
                    if backend_model == "Open_Ai":
                        memory_consol3 = Memory_Consolidation_Call(consolidation, username, bot_name)
                        
                    if DB_Search_Output == 'True':
                        print(f"\n\nIMPLICIT MEMORY CONSOLIDATION:\n{memory_consol3}")
                    segments = re.split(r'•|\n\s*\n', memory_consol3)
                    for segment in segments:
                        if segment.strip() == '':  
                            continue  
                        else:
                            collection_name = f"Bot_{bot_name}"

                            try:
                                collection_info = client.get_collection(collection_name=collection_name)
                            except:
                                client.create_collection(
                                    collection_name=collection_name,
                                    vectors_config=VectorParams(size=embed_size, distance=Distance.COSINE),
                                )
                            vector1 = embeddings(segment)
                            unique_id = str(uuid4())
                            importance_score.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: You are a sub-module of {bot_name}, an autonomous AI entity. Your function is to process a given memory and rate its importance to personal development and/or its ability to impact the greater world.  You are to give the rating on a scale of 1-100.\n"})
                            importance_score.append({'role': 'system', 'content': f"{botnameupper}'S MAIN PROMPT: {main_prompt}\n"})
                            importance_score.append({'role': 'system', 'content': f"{botnameupper}'S SECONDARY PROMPT: {secondary_prompt}\n"})
                            importance_score.append({'role': 'system', 'content': f"{botnameupper}'S GREETING MESSAGE: {greeting_msg}\n"})
                            importance_score.append({'role': 'system', 'content': f"MEMORY TO RATE: {segment}\n"})
                            importance_score.append({'role': 'system', 'content': f"{usernameupper}: Please now rate the given memory on a scale of 1-100. Only print the numerical rating as a digit. {user_input_end}"})
                            importance_score.append({'role': 'system', 'content': f"{botnameupper}: Sure thing! Here's the memory rated on a scale of 1-100:\nRating: "})
                            if backend_model == "Llama_2":
                                prompt = ''.join([message_dict['content'] for message_dict in importance_score])
                            score = 75
                            
                            importance_score.clear()
                            metadata = {
                                'bot': bot_name,
                                'user': user_id,
                                'time': timestamp,
                                'rating': score,
                                'message': segment,
                                'timestring': timestring,
                                'uuid': unique_id,
                                'memory_type': 'Implicit_Long_Term',
                            }
                            client.upsert(collection_name=collection_name,
                                                 points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])   
                            payload.clear()
                    client.delete(
                        collection_name=f"Bot_{bot_name}_Implicit_Short_Term",
                        points_selector=models.FilterSelector(
                            filter=models.Filter(
                                must=[
                                    models.FieldCondition(
                                        key="user",
                                        match=models.MatchValue(value=f"{user_id}"),
                                    ),
                                ],
                            )
                        ),
                    )
                else:   
                    pass
                    
                    
            # # Implicit Associative Processing/Pruning based on amount of vectors in namespace   
                collection_name = f"Consol_Counter_Bot_{bot_name}_{user_id}"
                collection_info = client.get_collection(collection_name=collection_name)
                if collection_info.vectors_count % 4 == 0:
                    consolidation.clear()
            #        print('Running Associative Processing/Pruning of Implicit Memory')
                    memory_consol_db4 = None
                    try:
                        hits = client.search(
                            collection_name=f"Bot_{bot_name}",
                            query_vector=vector_input,
                            query_filter=Filter(
                                must=[
                                    FieldCondition(
                                        key="memory_type",
                                        match=MatchValue(value="Implicit_Long_Term"),
                                    ),
                                    FieldCondition(
                                        key="user",
                                        match=MatchValue(value=f"{user_id}"),
                                    ),
                                ]
                            ),
                            limit=10
                        )
                        memory_consol_db4 = [hit.payload['message'] for hit in hits]
                    except Exception as e:
                        if "Not found: Collection" in str(e):
                            print("\nCollection does not exist.")
                        else:
                            print(f"\nAn unexpected error occurred: {str(e)}")

                    ids_to_delete = [m.id for m in hits]
           #         consolidation.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: {main_prompt}\n\n"})
                    consolidation.append({'role': 'assistant', 'content': f"LOG: {memory_consol_db4}\n\nSYSTEM: Read the Log and consolidate the different memories into executive summaries in a process allegorical to associative memory processing. Each summary should contain the entire context of the memory. Follow the bullet point format: •[memory] {user_input_end} {botnameupper}: Sure, here is the list of consolidated memories: "})
                    if backend_model == "Llama_2":
                        prompt = ''.join([message_dict['content'] for message_dict in consolidation])
                        memory_consol4 = await Associative_Memory_Call(prompt, username, bot_name)
                        
                    if backend_model == "Open_Ai":
                        memory_consol4 = Associative_Memory_Call(consolidation, username, bot_name)
                        
                    if DB_Search_Output == 'True':
                        print(f"\n\nIMPLICIT MEMORY ASSOCIATION:\n{memory_consol4}")
                        print('--------')
                    segments = re.split(r'•|\n\s*\n', memory_consol4)
                    for segment in segments:
                        if segment.strip() == '':  # This condition checks for blank segments
                            continue  # This condition checks for blank lines
                        else:
                            # Define the collection name
                            collection_name = f"Bot_{bot_name}"
                            # Create the collection only if it doesn't exist
                            try:
                                collection_info = client.get_collection(collection_name=collection_name)
                            except:
                                client.create_collection(
                                    collection_name=collection_name,
                                    vectors_config=VectorParams(size=embed_size, distance=Distance.COSINE),
                                )
                            vector1 = embeddings(segment)
                            unique_id = str(uuid4())
                            importance_score.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: You are a sub-module of {bot_name}, an autonomous AI entity. Your function is to process a given memory and rate its importance to personal development and/or its ability to impact the greater world.  You are to give the rating on a scale of 1-100.\n"})
                            importance_score.append({'role': 'system', 'content': f"{botnameupper}'S MAIN PROMPT: {main_prompt}\n"})
                            importance_score.append({'role': 'system', 'content': f"{botnameupper}'S SECONDARY PROMPT: {secondary_prompt}\n"})
                            importance_score.append({'role': 'system', 'content': f"{botnameupper}'S GREETING MESSAGE: {greeting_msg}\n"})
                            importance_score.append({'role': 'system', 'content': f"MEMORY TO RATE: {segment}\n"})
                            importance_score.append({'role': 'system', 'content': f"{usernameupper}: Please now rate the given memory on a scale of 1-100. Only print the numerical rating as a digit. {user_input_end}"})
                            importance_score.append({'role': 'system', 'content': f"{botnameupper}: Sure thing! Here's the memory rated on a scale of 1-100:\nRating: "})
                            if backend_model == "Llama_2":
                                prompt = ''.join([message_dict['content'] for message_dict in importance_score])
                            score = 75
                            # print(score)
                            importance_score.clear()
                            metadata = {
                                'bot': bot_name,
                                'user': user_id,
                                'time': timestamp,
                                'rating': score,
                                'message': segment,
                                'timestring': timestring,
                                'uuid': unique_id,
                                'memory_type': 'Implicit_Long_Term',
                            }
                            client.upsert(collection_name=collection_name,
                                                 points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])   
                            payload.clear()
                    try:
                        client.delete(
                            collection_name=f"Bot_{bot_name}",
                            points_selector=models.PointIdsList(
                                points=ids_to_delete,
                            ),
                        )
                    except Exception as e:
                        print(f"Error: {e}")
                        
                        
            # # Explicit Long-Term Memory Associative Processing/Pruning based on amount of vectors in namespace
                collection_name = f"Consol_Counter_Bot_{bot_name}_{user_id}"
                collection_info = client.get_collection(collection_name=collection_name)
                if collection_info.vectors_count > 5:
           #     if collection_info.vectors_count > 2:
                    consolidation.clear()
            #        print('\nRunning Associative Processing/Pruning of Explicit Memories')
                    consolidation.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: You are a data extractor. Your job is to read the user's input and provide a single semantic search query representative of a habit of {bot_name}.\n\n"})
                    consol_search = None
                    try:
                        hits = client.search(
                            collection_name=f"Bot_{bot_name}",
                            query_vector=vector_monologue,
                            query_filter=Filter(
                                must=[
                                    FieldCondition(
                                        key="memory_type",
                                        match=MatchValue(value="Implicit_Long_Term"),
                                    ),
                                    FieldCondition(
                                        key="user",
                                        match=MatchValue(value=f"{user_id}"),
                                    ),
                                ]
                            ),
                            limit=5
                        )
                        consol_search = [hit.payload['message'] for hit in hits]
                    except Exception as e:
                        if "Not found: Collection" in str(e):
                            print("\nCollection does not exist.")
                        else:
                            print(f"\nAn unexpected error occurred: {str(e)}")

                    consolidation.append({'role': 'user', 'content': f"{bot_name}'s Memories: {consol_search}{user_input_end}\n\n"})
                    consolidation.append({'role': 'assistant', 'content': "RESPONSE: Semantic Search Query: "})
                    if backend_model == "Llama_2":
                        prompt = ''.join([message_dict['content'] for message_dict in consolidation])
                        consol_search_term = await Tokens_250_Call(prompt, username, bot_name)
                        
                    if backend_model == "Open_Ai":
                        consol_search_term = Tokens_250_Call(consolidation, username, bot_name)
                        
                    consol_vector = embeddings(consol_search_term)
                    memory_consol_db2 = None
                    try:
                        hits = client.search(
                            collection_name=f"Bot_{bot_name}",
                            query_vector=consol_vector,
                            query_filter=Filter(
                                must=[
                                    FieldCondition(
                                        key="memory_type",
                                        match=MatchValue(value="Explicit_Long_Term"),
                                    ),
                                    FieldCondition(
                                        key="user",
                                        match=MatchValue(value=f"{user_id}"),
                                    ),
                                ]
                            ),
                            limit=5
                        )
                        memory_consol_db2 = [hit.payload['message'] for hit in hits]
                    except Exception as e:
                        if "Not found: Collection" in str(e):
                            print("\nCollection does not exist.")
                        else:
                            print(f"\nAn unexpected error occurred: {str(e)}")

                    #Find solution for this
                    ids_to_delete2 = [m.id for m in hits]
                    consolidation.clear()
            #        consolidation.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: {main_prompt}\n\n"})
                    consolidation.append({'role': 'assistant', 'content': f"LOG: {memory_consol_db2}\n\nSYSTEM: Read the Log and consolidate the different memories in a process allegorical to associative memory processing. Each summary should contain full context.\n\nFORMAT: Follow the bullet point format: •[memory] {user_input_end} {botnameupper}: Sure, here is the list of consolidated memories: "})
                    
                    if backend_model == "Llama_2":
                        prompt = ''.join([message_dict['content'] for message_dict in consolidation])
                        memory_consol5 = await Associative_Memory_Call(prompt, username, bot_name)
                        
                    if backend_model == "Open_Ai":
                        memory_consol5 = Associative_Memory_Call(consolidation, username, bot_name)
                        
                    if DB_Search_Output == 'True':
                        print(f"\n\nEXPLICIT MEMORY ASSOCIATION:\n{memory_consol5}")
                        print('\n-----------------------\n')
                #    memories = results
                    segments = re.split(r'•|\n\s*\n', memory_consol5)
                    for segment in segments:
                        if segment.strip() == '':  
                            continue 
                        else:
                            collection_name = f"Bot_{bot_name}"
                            try:
                                collection_info = client.get_collection(collection_name=collection_name)
                            except:
                                client.create_collection(
                                    collection_name=collection_name,
                                    vectors_config=VectorParams(size=embed_size, distance=Distance.COSINE),
                                )
                            vector1 = embeddings(segment)
                            unique_id = str(uuid4())
                            importance_score.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: You are a sub-module of {bot_name}, an autonomous AI entity. Your function is to process a given memory and rate its importance to personal development and/or its ability to impact the greater world.  You are to give the rating on a scale of 1-100.\n"})
                            importance_score.append({'role': 'system', 'content': f"{botnameupper}'S MAIN PROMPT: {main_prompt}\n"})
                            importance_score.append({'role': 'system', 'content': f"{botnameupper}'S SECONDARY PROMPT: {secondary_prompt}\n"})
                            importance_score.append({'role': 'system', 'content': f"{botnameupper}'S GREETING MESSAGE: {greeting_msg}\n"})
                            importance_score.append({'role': 'system', 'content': f"MEMORY TO RATE: {segment}\n"})
                            importance_score.append({'role': 'system', 'content': f"{usernameupper}: Please now rate the given memory on a scale of 1-100. Only print the numerical rating as a digit. {user_input_end}"})
                            importance_score.append({'role': 'system', 'content': f"{botnameupper}: Sure thing! Here's the memory rated on a scale of 1-100:\nRating: "})
                            if backend_model == "Llama_2":
                                prompt = ''.join([message_dict['content'] for message_dict in importance_score])
                            score = 75
                            
                            
                            domain_extraction.append({'role': 'user', 'content': f"You are a knowledge domain extractor.  Your task is to analyze the user's inquiry, then extract the single most salent generalized knowledge domain needed to complete the user's inquiry.  Your response should be a single word.\n"})
                            domain_extraction.append({'role': 'user', 'content': f"USER INPUT: {segment} {user_input_end} "})
                            
                            if backend_model == "Llama_2":
                                prompt = ''.join([message_dict['content'] for message_dict in domain_extraction])
                                extracted_domain = await Domain_Extraction_Call(prompt, username, bot_name)
                                
                            if backend_model == "Open_Ai":
                                extracted_domain = Domain_Extraction_Call(domain_extraction, username, bot_name)
                                
                            if ":" in extracted_domain:
                                extracted_domain = extracted_domain.split(":")[-1]
                            extracted_domain = extracted_domain.replace("\n", "")
                            extracted_domain = extracted_domain.upper()
                            extracted_domain = re.sub(r'[^A-Z]', '', extracted_domain)
                            extracted_domain = extracted_domain.replace("_", " ")
                            domain_extraction.clear()
                            
                            vector2 = embeddings(extracted_domain)
                            # print(score)
                            importance_score.clear()
                            metadata = {
                                'bot': bot_name,
                                'user': user_id,
                                'time': timestamp,
                                'rating': score,
                                'message': segment,
                                'knowledge_domain': extracted_domain,
                                'timestring': timestring,
                                'uuid': unique_id,
                                'memory_type': 'Explicit_Long_Term',
                            }
                            client.upsert(collection_name=collection_name,
                                                 points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])   
                            payload.clear()
                            
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
                                    limit=20
                                )
                                domain_search = [hit.payload['knowledge_domain'] for hit in hits]
                            except Exception as e:
                                if "Not found: Collection" in str(e):
                                    print("\nCollection does not exist.")
                                    domain_search = "No Collection"
                                else:
                                    print(f"\nAn unexpected error occurred: {str(e)}")
                            
                            
                            if extracted_domain not in domain_search:
                                collection_name = f"Bot_{bot_name}_Knowledge_Domains"
                                try:
                                    collection_info = client.get_collection(collection_name=collection_name)
                                except:
                                    client.create_collection(
                                        collection_name=collection_name,
                                        vectors_config=VectorParams(size=embed_size, distance=Distance.COSINE),
                                    )
                                unique_id = str(uuid4())
                                metadata = {
                                    'bot': bot_name,
                                    'user': user_id,
                                    'knowledge_domain': extracted_domain,
                                    'uuid': unique_id,
                                }
                                client.upsert(collection_name=collection_name,
                                                     points=[PointStruct(id=unique_id, vector=vector2, payload=metadata)])   
                                payload.clear()
                            
                            
                    try:
                        client.delete(
                            collection_name=f"Bot_{bot_name}",
                            points_selector=models.PointIdsList(
                                points=ids_to_delete2,
                            ),
                        )
                    except:
                        print('\n\nFailed2')  
                    client.delete_collection(collection_name=f"Consol_Counter_Bot_{bot_name}_{user_id}")    
            except Exception as e:
                pass
        else:
            pass
        consolidation.clear()
        conversation2.clear()
        break