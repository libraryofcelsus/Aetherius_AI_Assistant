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
from Llama2_chat_Async import *
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


# Import Tool Functions.
def get_script_path_from_file(json_path, key, base_folder='./Aetherius_API/Tools/Llama_2_Async/'):
    with open(json_path, 'r', encoding='utf-8') as file:
        settings = json.load(file)
    script_name = settings.get(key, "").strip()
    return f'{base_folder}{script_name}.py'

# Path to the JSON settings file
json_file_path = './Aetherius_API/chatbot_settings.json'

# Script Path Should be the Name of the script file
script_path1 = get_script_path_from_file(json_file_path, "WebScrape_Type")
import_functions_from_script(script_path1, "WebScrape_module")

    
    
    
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
    def __init__(self, username, bot_name, max_entries, prompt, greeting):
        botnameupper = bot_name.upper()
        usernameupper = username.upper()
        self.max_entries = int(max_entries)
        self.file_path = f'./history/{username}/{bot_name}_main_conversation_history.json'
        self.file_path2 = f'./history/{username}/{bot_name}_main_history.json'
        self.main_conversation = [prompt, greeting]

        # Check if directory exists, if not create it
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

        # Load existing conversation from file
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.running_conversation = data.get('running_conversation', [])
        else:
            self.running_conversation = []
            self.save_to_file()

    def append(self, timestring, username, usernameupper, a, bot_name, botnameupper, response_two):
        # Append new entry to the running conversation
        entry = []
        entry.append(f"{usernameupper}: [{timestring}] - {a}")
        entry.append(f"{botnameupper}: {response_two}")
        self.running_conversation.append("\n\n".join(entry))  # Join the entry with "\n\n"

        # Remove oldest entry if conversation length exceeds max entries
        while len(self.running_conversation) > self.max_entries:
            self.running_conversation.pop(0)
        self.save_to_file()

    def save_to_file(self):
        # Combine main conversation and formatted running conversation for saving to file
        history = self.main_conversation + self.running_conversation

        data_to_save = {
            'main_conversation': self.main_conversation,
            'running_conversation': self.running_conversation
        }

        # save history as a list of dictionaries with 'visible' key
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


async def Aetherius_Chatbot(user_input, username, bot_name):
    tasklist = list()
    inner_monologue = list()
    intuition = list()
    implicit_memory = list()
    response = list()
    explicit_memory = list()
    payload = list()
    counter = 0
    counter2 = 0
    mem_counter = 0
    with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
    HOST = settings.get('HOST_Oobabooga', 'http://localhost:5000/api')
    External_Research_Search = settings.get('Search_External_Resource_DB', 'False')
    conv_length = settings.get('Conversation_Length', '3')
    Web_Search = settings.get('Search_Web', 'False')
    Inner_Monologue_Output = settings.get('Output_Inner_Monologue', 'True')
    Intuition_Output = settings.get('Output_Intuition', 'False')
    Response_Output = settings.get('Output_Response', 'True')
    DB_Search_Output = settings.get('Output_DB_Search', 'False')
    memory_mode = settings.get('Memory_Mode', 'Auto')
    Update_Bot_Personality_Description = settings.get('Update_Bot_Personality_Description', 'False')
    Update_User_Personality_Description = settings.get('Update_User_Personality_Description', 'False')
    Use_Bot_Personality_Description = settings.get('Use_Bot_Personality_Description', 'False')
    Use_User_Personality_Description = settings.get('Use_User_Personality_Description', 'False')
    botnameupper = bot_name.upper()
    usernameupper = username.upper()
    base_path = "./Aetherius_API/Chatbot_Prompts"
    base_prompts_path = os.path.join(base_path, "Base")
    user_bot_path = os.path.join(base_path, username, bot_name)
    if not os.path.exists(user_bot_path):
        os.makedirs(user_bot_path)
    prompts_json_path = os.path.join(user_bot_path, "prompts.json")
    if not os.path.exists(prompts_json_path):
        default_prompts = {
            "main_prompt": "",
            "secondary_prompt": "",
            "greeting_prompt": ""
        }
        for filename in default_prompts:
            src = os.path.join(base_prompts_path, f"prompt_{filename}.txt")
            if os.path.isfile(src):
                with open(src, 'r') as file:
                    default_prompts[filename] = file.read()
        async with aiofiles.open(prompts_json_path, 'w') as json_file:
            await json_file.write(json.dumps(default_prompts, indent=2))
    async with aiofiles.open(prompts_json_path, 'r') as file:
        prompts = json.loads(await file.read())
    main_prompt = prompts["main_prompt"].replace('<<NAME>>', bot_name)
    secondary_prompt = prompts["secondary_prompt"]
    greeting_msg = prompts["greeting_prompt"].replace('<<NAME>>', bot_name)
    main_conversation = MainConversation(username, bot_name, conv_length, main_prompt, greeting_msg)
    while True:
        print(f"{username}: {user_input}\n\n")
        conversation_history = main_conversation.get_last_entry()
        timestamp = time()
        timestring = timestamp_to_datetime(timestamp)
        con_hist = f'{conversation_history}'
        vector_input = embeddings(user_input)
        tasklist.append({'role': 'system', 'content': "SYSTEM: You are a search query corrdinator. Your role is to interpret the original user query and generate 2-4 synonymous search terms that will guide the exploration of the chatbot's memory database. Each alternative term should reflect the essence of the user's initial search input. Please list your results using bullet point format.\n"})
        tasklist.append({'role': 'user', 'content': "USER: %s\nUse the format: •Search Query [/INST] ASSISTANT: Sure, I'd be happy to help! Here are 2-4 synonymous search terms: " % user_input})
        prompt = ''.join([message_dict['content'] for message_dict in tasklist])
        tasklist_output = await oobabooga_terms(prompt, username, bot_name)

        lines = tasklist_output.splitlines()
        tasklist_counter = 0
        tasklist_counter2 = 0
        inner_monologue.append({'role': 'system', 'content': f"{main_prompt}"})
        
        if Use_Bot_Personality_Description == 'True':
            try:
                file_path = f"./Chatbot_Personalities/{bot_name}/{username}/{bot_name}_personality_file.txt"
                if not os.path.exists(file_path):
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    default_prompts = f"{main_prompt}\n{secondary_prompt}\n{greeting_msg}"
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
                    bot_personality = [line.strip() for line in file_content]
                inner_monologue.append({'role': 'system', 'content': f"{botnameupper}'S PERSONALITY DESCRIPTION: {bot_personality}\n\n"})
            except:
                pass
            
        inner_monologue.append({'role': 'system', 'content': f"Now return your most relevant memories: [/INST]"})
        inner_monologue.append({'role': 'system', 'content': f"{botnameupper}'S LONG TERM CHATBOT MEMORIES: "})
        intuition.append({'role': 'system', 'content': f"{main_prompt}"})
        if Use_User_Personality_Description == 'True':
            try:
                file_path = f"./Chatbot_Personalities/{bot_name}/{username}/{username}_personality_file.txt"
                # Check if file exists, if not create and write default prompts.
                if not os.path.exists(file_path):
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    default_prompts = f"The user {username} does not yet have a personality file."

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
                intuition.append({'role': 'system', 'content': f"{usernameupper}'S PERSONALITY DESCRIPTION: {user_personality}\n\n"})
            except:
                pass
        intuition.append({'role': 'system', 'content': f"Now return your most relevant memories: [/INST]"})
        intuition.append({'role': 'system', 'content': f"{botnameupper}'S LONG TERM CHATBOT MEMORIES: "})
        for line in lines:
            if line.startswith("•"):
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
                                    key="user",
                                    match=models.MatchValue(value=f"{username}"),
                                ),
                            ]
                        ),
                        limit=3
                    )
                    unsorted_table = [(hit.payload['timestring'], hit.payload['message']) for hit in hits]
                    sorted_table = sorted(unsorted_table, key=lambda x: x[0])  # Sort by the 'timestring' field
                    db_search_1 = "\n".join([f"{message}" for timestring, message in sorted_table])
                    
                    inner_monologue.append({'role': 'assistant', 'content': f"{db_search_1}  "})
                    if tasklist_counter < 3:
                        intuition.append({'role': 'assistant', 'content': f"{db_search_1}  "})
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
                                    match=models.MatchValue(value=f"{username}"),
                                ),
                            ]
                        ),
                        limit=4
                    )
                    unsorted_table = [(hit.payload['timestring'], hit.payload['message']) for hit in hits]
                    sorted_table = sorted(unsorted_table, key=lambda x: x[0])  # Sort by the 'timestring' field
                    db_search_2 = "\n".join([f"{message}" for timestring, message in sorted_table])
                    inner_monologue.append({'role': 'assistant', 'content': f"{db_search_2}  "})
                    if tasklist_counter2 < 3:
                        intuition.append({'role': 'assistant', 'content': f"{db_search_2}  "})
                    tasklist_counter2 + 1
                    if DB_Search_Output == 'True':
                        print(db_search_2)
                except Exception as e:
                    if DB_Search_Output == 'True':
                        if "Not found: Collection" in str(e):
                            print("Collection does not exist.")
                        else:
                            print(f"An unexpected error occurred: {str(e)}")
        
        db_search_3, db_search_4, db_search_5, db_search_6 = None, None, None, None
        
        try:
            hits = client.search(
                collection_name=f"Bot_{bot_name}",
                query_vector=vector_input1,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="memory_type",
                            match=MatchValue(value="Episodic"),
                        ),
                        FieldCondition(
                            key="user",
                            match=models.MatchValue(value=f"{username}"),
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
                query_vector=vector_input1,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="memory_type",
                            match=MatchValue(value="Explicit_Short_Term"),
                        ),
                        FieldCondition(
                            key="user",
                            match=models.MatchValue(value=f"{username}"),
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
                query_vector=vector_input1,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="memory_type",
                            match=MatchValue(value="Implicit_Short_Term"),
                        ),
                        FieldCondition(
                            key="user",
                            match=models.MatchValue(value=f"{username}"),
                        ),
                    ]
                ),
                limit=3
            )
            unsorted_table = [(hit.payload['timestring'], hit.payload['message']) for hit in hits]
            sorted_table = sorted(unsorted_table, key=lambda x: x[0])  # Sort by the 'timestring' field
            implicit_short = "\n".join([f"{message}" for timestring, message in sorted_table])
            if DB_Search_Output == 'True':
                print(implicit_short)
        except Exception as e:
            implicit_short = "No Memories"
            if DB_Search_Output == 'True':
                if "Not found: Collection" in str(e):
                    print("Collection does not exist.")
                else:
                    print(f"An unexpected error occurred: {str(e)}")
        db_search_4 = f"{implicit_short}\n{explicit_short}"    
                
        try:
            hits = client.search(
                collection_name=f"Bot_{bot_name}",
                query_vector=vector_input1,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="memory_type",
                            match=MatchValue(value="Flashbulb"),
                        ),
                        FieldCondition(
                            key="user",
                            match=models.MatchValue(value=f"{username}"),
                        ),
                    ]
                ),
                limit=2
            )
            unsorted_table = [(hit.payload['timestring'], hit.payload['message']) for hit in hits]
            sorted_table = sorted(unsorted_table, key=lambda x: x[0])  # Sort by the 'timestring' field
            db_search_5 = "\n".join([f"{message}" for timestring, message in sorted_table])
            if DB_Search_Output == 'True':
                print(db_search_5)
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
                            match=MatchValue(value="Heuristics"),
                        ),
                        FieldCondition(
                            key="user",
                            match=models.MatchValue(value=f"{username}"),
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
                    query_vector=vector_input1,
                    query_filter=Filter(
                        must=[
                            FieldCondition(
                                key="user",
                                match=models.MatchValue(value=f"{username}"),
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
        
        inner_monologue.append({'role': 'assistant', 'content': f"{botnameupper}'S EPISODIC MEMORIES: {db_search_3}\n{db_search_5}\n{botnameupper}'S SHORT-TERM MEMORIES: {db_search_4}\n{botnameupper}'s HEURISTICS: {db_search_6} [INST] Now return and analyze the current conversation history. [/INST] CURRENT CONVERSATION HISTORY: {con_hist} [INST] SYSTEM: Compose a short silent soliloquy to serve as {bot_name}'s internal monologue/narrative.  Ensure it includes {bot_name}'s contemplations in relation to {username}'s request and does not exceed a paragraph in length.\n{usernameupper}/USER'S REQUEST: {user_input} [/INST] {botnameupper}: "})
        prompt = ''.join([message_dict['content'] for message_dict in inner_monologue])
        output_one = await oobabooga_inner_monologue(prompt, username, bot_name)
        sentences = re.split(r'(?<=[.!?])\s+', output_one)
        if sentences and not re.search(r'[.!?]$', sentences[-1]):
            sentences.pop()
        output_one = ' '.join(sentences)
        inner_output = (f'{output_one}\n\n')
        paragraph = output_one
        if Inner_Monologue_Output == 'True':
            print('\n\nINNER_MONOLOGUE: %s' % output_one)
        inner_monologue.clear()
        conversation_history = main_conversation.get_conversation_history()
        con_hist = f'{conversation_history}'
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
                            match=models.MatchValue(value=f"{username}"),
                        ),
                    ]
                ),
                limit=3
            )
            unsorted_table = [(hit.payload['timestring'], hit.payload['message']) for hit in hits]
            sorted_table = sorted(unsorted_table, key=lambda x: x[0])  # Sort by the 'timestring' field
            db_search_7 = "\n".join([f"{message}" for timestring, message in sorted_table])
            if DB_Search_Output == 'True':
                print(db_search_7)
        except Exception as e:
            if DB_Search_Output == 'True':
                if "Not found: Collection" in str(e):
                    print("Collection does not exist.")
                else:
                     print(f"An unexpected error occurred: {str(e)}")
        
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
                            match=models.MatchValue(value=f"{username}"),
                        ),
                    ]
                ),
                limit=3
            )
            unsorted_table = [(hit.payload['timestring'], hit.payload['message']) for hit in hits]
            sorted_table = sorted(unsorted_table, key=lambda x: x[0])  # Sort by the 'timestring' field
            db_search_8 = "\n".join([f"{message}" for timestring, message in sorted_table])
      #      db_search_8 = [hit.payload['message'] for hit in hits]
            if DB_Search_Output == 'True':
                print(db_search_8)
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
                            match=MatchValue(value="Flashbulb"),
                        ),
                        FieldCondition(
                            key="user",
                            match=models.MatchValue(value=f"{username}"),
                        ),
                    ]
                ),
                limit=2
            )
            unsorted_table = [(hit.payload['timestring'], hit.payload['message']) for hit in hits]
            sorted_table = sorted(unsorted_table, key=lambda x: x[0])  # Sort by the 'timestring' field
            db_search_9 = "\n".join([f"{message}" for timestring, message in sorted_table])
   #         db_search_9 = [hit.payload['message'] for hit in hits]
            if DB_Search_Output == 'True':
                print(db_search_9)
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
                            match=models.MatchValue(value=f"{username}"),
                        ),
                    ]
                ),
                limit=5
            )
            unsorted_table = [(hit.payload['timestring'], hit.payload['message']) for hit in hits]
            sorted_table = sorted(unsorted_table, key=lambda x: x[0])  # Sort by the 'timestring' field
            db_search_10 = "\n".join([f"{message}" for timestring, message in sorted_table])
    #        db_search_10 = [hit.payload['message'] for hit in hits]
            if DB_Search_Output == 'True':
                print(db_search_10)
        except Exception as e:
            if DB_Search_Output == 'True':
                if "Not found: Collection" in str(e):
                    print("Collection does not exist.")
                else:
                    print(f"An unexpected error occurred: {str(e)}")

        # # Intuition Generation
        intuition.append({'role': 'assistant', 'content': f"{botnameupper}'S FLASHBULB MEMORIES: {db_search_9}\n{botnameupper}'S EXPLICIT MEMORIES: {db_search_8}\n{botnameupper}'s HEURISTICS: {db_search_10}\n{botnameupper}'S INNER THOUGHTS: {output_one}\n{botnameupper}'S EPISODIC MEMORIES: {db_search_7} [INST] Now return and analyze the previous conversation history. [/INST] PREVIOUS CONVERSATION HISTORY: {con_hist} [INST] SYSTEM: Transmute the user, {username}'s message as {bot_name} by devising a truncated predictive action plan in the third person point of view on how to best respond to {username}'s most recent message. You do not have access to external resources.  If the user's message is casual conversation, print 'No Plan Needed'. Only create an action plan for informational requests or if requested to complete a complex task.  If the user is requesting information on a subjector asking a question, predict what information needs to be provided. Do not give examples, only the action plan. {usernameupper}: {user_input} [/INST] {botnameupper}: "}) 
        prompt = ''.join([message_dict['content'] for message_dict in intuition])
        output_two = await oobabooga_intuition(prompt, username, bot_name)
        
     #   sentences = re.split(r'(?<=[.!?])\s+', output_two)
     #   if sentences and not re.search(r'[.!?]$', sentences[-1]):
     #       sentences.pop()
     #   output_two = ' '.join(sentences)
        if Intuition_Output == 'True':
            print(f'\n\nINTUITION: {output_two}')
        if memory_mode != 'None':
            implicit_short_term_memory = f'\nUSER: {user_input}\nINNER_MONOLOGUE: {output_one}'
            implicit_memory.append({'role': 'assistant', 'content': f"LOG: {implicit_short_term_memory} [INST] SYSTEM: Read the log to identify key interactions between {bot_name} and {username} from the chatbot's inner monologue. Create 1-5 bullet-point summaries that will serve as automatic, unconscious memories for {bot_name}'s future interactions. These memories should not be easily verbalized but should capture the essence of skills, habits, or associations learned during interactions. Each bullet point should contain enough context to understand the significance without tying to explicit reasoning or verbal explanation. Use the following bullet point format: •[memory] [/INST] {botnameupper}: Sure! Here are the bullet-point summaries which will serve as memories based on {bot_name}'s internal thoughts:"})
            prompt_implicit = ''.join([message_dict['content'] for message_dict in implicit_memory])
            if memory_mode != 'Manual':
                task = asyncio.create_task(Aetherius_Implicit_Memory(user_input, output_one, bot_name, username, prompt_implicit))
        intuition.clear()


        conversation_history = main_conversation.get_conversation_history()
        # # Get Timestamp
        timestamp = time()
        timestring = timestamp_to_datetime(timestamp)
    #    if 'response_two' in locals():
    #        explicit_memory.append({'role': 'user', 'content': user_input})
    #        explicit_memory.append({'role': 'assistant', 'content': "%s" % response_two})
    #        pass
    #    else:
    #        explicit_memory.append({'role': 'assistant', 'content': "%s" % greeting_msg})
        vector_input = embeddings(user_input)
        vector_monologue = embeddings(output_one)
        con_hist = f'{conversation_history}'
        response.append({'role': 'system', 'content': f"{main_prompt}"})
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
                            match=models.MatchValue(value=f"{username}"),
                        ),
                    ]
                ),
                limit=2
            )
            db_search_11 = [hit.payload['message'] for hit in hits]
            response.append({'role': 'assistant', 'content': f"CADENCE: I will extract the cadence from the following messages and mimic it to the best of my ability: {db_search_11}"})
        except:
            pass
        response.append({'role': 'system', 'content': f"Now return your most relevant memories: [/INST] "})
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
                            match=models.MatchValue(value=f"{username}"),
                        ),
                    ]
                ),
                limit=4
            )
            unsorted_table = [(hit.payload['timestring'], hit.payload['message']) for hit in hits]
            sorted_table = sorted(unsorted_table, key=lambda x: x[0])  # Sort by the 'timestring' field
            db_search_12 = "\n".join([f"{message}" for timestring, message in sorted_table])
            if DB_Search_Output == 'True':
                print(db_search_12)
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
                            match=MatchValue(value="Episodic"),
                        ),
                        FieldCondition(
                            key="user",
                            match=models.MatchValue(value=f"{username}"),
                        ),
                    ]
                ),
                limit=7
            )
            unsorted_table = [(hit.payload['timestring'], hit.payload['message']) for hit in hits]
            sorted_table = sorted(unsorted_table, key=lambda x: x[0])  # Sort by the 'timestring' field
            db_search_13 = "\n".join([f"{message}" for timestring, message in sorted_table])
            if DB_Search_Output == 'True':
                print(db_search_13)
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
                            match=models.MatchValue(value=f"{username}"),
                        ),
                    ]
                ),
                limit=5
            )
            unsorted_table = [(hit.payload['timestring'], hit.payload['message']) for hit in hits]
            sorted_table = sorted(unsorted_table, key=lambda x: x[0])  # Sort by the 'timestring' field
            db_search_14 = "\n".join([f"{message}" for timestring, message in sorted_table])
            if DB_Search_Output == 'True':
                print(db_search_14)
        except Exception as e:
            if DB_Search_Output == 'True':
                if "Not found: Collection" in str(e):
                    print("Collection does not exist.")
                else:
                    print(f"An unexpected error occurred: {str(e)}")
        
        response.append({'role': 'assistant', 'content': f"CHATBOT'S MEMORIES: {db_search_12}\n{db_search_13}\n{bot_name}'s HEURISTICS: {db_search_14}\nCHATBOT'S INNER THOUGHTS: {output_one}\n{secondary_prompt} [INST] Now return and analyze the previous conversation history. [/INST] CONVERSATION HISTORY: {con_hist} [INST] {usernameupper}: We are currently in the middle of a conversation, please review your action plan for your response. [/INST] {botnameupper}: I will now review my action plan, using it as a framework to construct my upcoming response: {output_two}\nI will proceed by reviewing our previous conversation to ensure I respond in a manner that is both informative and emotionally attuned. Please now give me the message I am to respond to. [INST] {usernameupper}: {user_input} [/INST] {botnameupper}: Here is my response to the {username}: "})
        prompt = ''.join([message_dict['content'] for message_dict in response])
        response_two = await oobabooga_response(prompt, username, bot_name)
        if response_two.startswith(f"{bot_name}") or response_two.startswith(f"{botnameupper}"):
            colon_index = response_two.find(":")
            if colon_index != -1:
                response_two = response_two[colon_index + 1:].lstrip()
        sentences = re.split(r'(?<=[.!?])\s+', response_two)
        if sentences and not re.search(r'[.!?]$', sentences[-1]):
            sentences.pop()
        response_two = ' '.join(sentences)
        if Response_Output == 'True':
            print('\n\n%s: %s' % (bot_name, response_two))
        main_conversation.append(timestring, username, usernameupper, user_input, bot_name, botnameupper, response_two)
        
        
        if memory_mode != 'None':
            db_msg = f"USER: {user_input}\nINNER_MONOLOGUE: {output_one}\n{bot_name}'s RESPONSE: {response_two}"
            explicit_memory.append({'role': 'assistant', 'content': f"LOG: {db_msg} [INST] SYSTEM: Use the log to extract salient points about interactions between {bot_name} and {username}, as well as any informational topics mentioned in the chatbot's inner monologue and responses. These points should be used to create concise executive summaries in bullet point format, intended to serve as explicit memories for {bot_name}'s future interactions. These memories should be consciously recollected and easily talked about, focusing on general knowledge and facts discussed or learned. Each bullet point should be rich in detail, providing all the essential context for full recollection and articulation. Each bullet point should be considered a separate memory and contain full context. Use the following bullet point format: •[memory] [/INST] {botnameupper}: Sure! Here are 1-5 bullet-point summaries that will serve as memories based on {bot_name}'s responses:"})
            prompt_explicit = ''.join([message_dict['content'] for message_dict in explicit_memory])
        
            if memory_mode != 'Manual':
                task = asyncio.create_task(Aetherius_Explicit_Memory(user_input, vector_input, vector_monologue, output_one, response_two, bot_name, username, prompt_explicit))

        
        response.clear()
        if memory_mode == 'Manual':
            inner_loop_memory = await oobabooga_implicit_memory(prompt_implicit, username, bot_name)
            response_memory = await oobabooga_episodic_memory(prompt_explicit, username, bot_name)
        
            print(f"Do you want to upload the following memories:\n{inner_loop_response}\n{response_memory}\n'Y' or 'N'")
            mem_upload_yescheck = input("Enter 'Y' or 'N': ")
            if mem_upload_yescheck.upper == "Y":
                segments = re.split(r'•|\n\s*\n', inner_loop_response)
                total_segments = len(segments)

                for index, segment in enumerate(segments):
                    segment = segment.strip()
                    if segment == '':  # This condition checks for blank segments
                        continue  # This condition checks for blank lines      
                    # Check if it is the final segment and if the memory is cut off (ends without punctuation)
                    if index == total_segments - 1 and not segment[-1] in ['.', '!', '?']:
                        continue
                    await Upload_Implicit_Short_Term_Memories(segment, username, bot_name)
                segments = re.split(r'•|\n\s*\n', db_upsert)
                total_segments = len(segments)

                for index, segment in enumerate(segments):
                    segment = segment.strip()
                    if segment == '':  # This condition checks for blank segments
                        continue  # This condition checks for blank lines      
                    # Check if it is the final segment and if the memory is cut off (ends without punctuation)
                    if index == total_segments - 1 and not segment[-1] in ['.', '!', '?']:
                        continue
                    await Upload_Explicit_Short_Term_Memories(segment, username, bot_name)
                task = asyncio.create_task(Aetherius_Memory_Loop(user_input, username, bot_name, vector_input, vector_monologue, output_one, response_two))
        return response_two


async def Aetherius_Agent(user_input, username, bot_name):
    with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
    HOST = settings.get('HOST_Oobabooga', 'http://localhost:5000/api')
    embed_size = settings['embed_size']
    External_Research_Search = settings.get('Search_External_Resource_DB', 'False')
    conv_length = settings.get('Conversation_Length', '3')
    Web_Search = settings.get('Search_Web', 'False')
    Inner_Monologue_Output = settings.get('Output_Inner_Monologue', 'True')
    Intuition_Output = settings.get('Output_Intuition', 'False')
    Response_Output = settings.get('Output_Response', 'True')
    DB_Search_Output = settings.get('Output_DB_Search', 'False')
    memory_mode = settings.get('Memory_Mode', 'Auto')
    Sub_Module_Output = settings.get('Output_Sub_Module', 'False')
    Update_Bot_Personality_Description = settings.get('Update_Bot_Personality_Description', 'False')
    Update_User_Personality_Description = settings.get('Update_User_Personality_Description', 'False')
    Use_Bot_Personality_Description = settings.get('Use_Bot_Personality_Description', 'False')
    Use_User_Personality_Description = settings.get('Use_User_Personality_Description', 'False')
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
    counter = 0
    counter2 = 0
    mem_counter = 0
    botnameupper = bot_name.upper()
    usernameupper = username.upper()
    base_path = "./Aetherius_API/Chatbot_Prompts"
    base_prompts_path = os.path.join(base_path, "Base")
    user_bot_path = os.path.join(base_path, username, bot_name)  # Replace 'username' and 'bot_name'

    if not os.path.exists(user_bot_path):
        os.makedirs(user_bot_path)

    prompts_json_path = os.path.join(user_bot_path, "prompts.json")
    base_prompts_json_path = os.path.join(base_prompts_path, "prompts.json")

    # If prompts.json doesn’t exist in the user’s directory, copy it from the Base directory
    if not os.path.exists(prompts_json_path) and os.path.exists(base_prompts_json_path):
        async with aiofiles.open(base_prompts_json_path, 'r') as base_file:
            base_prompts_content = await base_file.read()
            
        async with aiofiles.open(prompts_json_path, 'w') as user_file:
            await user_file.write(base_prompts_content)

    # Now, you can read the content of prompts.json in the user’s directory
    async with aiofiles.open(prompts_json_path, 'r') as file:
        prompts = json.loads(await file.read())
    main_prompt = prompts["main_prompt"].replace('<<NAME>>', bot_name)
    secondary_prompt = prompts["secondary_prompt"]
    greeting_msg = prompts["greeting_prompt"].replace('<<NAME>>', bot_name)
    main_conversation = MainConversation(username, bot_name, conv_length, main_prompt, greeting_msg)
 #   r = sr.Recognizer()
    while True:
        print(f"{username}: {user_input}\n\n")
        # # Get Timestamp
        conversation_history = main_conversation.get_last_entry()
        con_hist = f'{conversation_history}'
        timestamp = time()
        timestring = timestamp_to_datetime(timestamp)
        vector_input = embeddings(user_input)
        # # Check for Commands
        # # Check for "Clear Memory"
        agent_inner_monologue.append({'role': 'system', 'content': f"SYSTEM: {main_prompt}"})
        if Use_Bot_Personality_Description == 'True':
            try:
                file_path = f"./Chatbot_Personalities/{bot_name}/{username}/{bot_name}_personality_file.txt"
                if not os.path.exists(file_path):
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    default_prompts = f"{main_prompt}\n{secondary_prompt}\n{greeting_msg}"
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
                    bot_personality = [line.strip() for line in file_content]
                agent_inner_monologue.append({'role': 'system', 'content': f"{botnameupper}'S PERSONALITY DESCRIPTION: {bot_personality}\n\n"})
            except:
                pass
        
        
        agent_inner_monologue.append({'role': 'system', 'content': f"{botnameupper}'S LONG TERM CHATBOT MEMORIES: "})
        agent_intuition.append({'role': 'system', 'content': f"{main_prompt}"})
        if Use_User_Personality_Description == 'True':
            try:
                file_path = f"./Chatbot_Personalities/{bot_name}/{username}/{username}_personality_file.txt"
                # Check if file exists, if not create and write default prompts.
                if not os.path.exists(file_path):
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    default_prompts = f"The user {username} does not yet have a personality file."

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
        
        agent_intuition.append({'role': 'system', 'content': f"Now return your most relevant memories: [/INST]"})
        agent_intuition.append({'role': 'system', 'content': f"{botnameupper}'S LONG TERM CHATBOT MEMORIES: "})
        # # Generate Semantic Search Terms
        tasklist.append({'role': 'system', 'content': "SYSTEM: You are a search query corrdinator. Your role is to interpret the original user query and generate 2-4 synonymous search terms that will guide the exploration of the chatbot's memory database. Each alternative term should reflect the essence of the user's initial search input. Please list your results using bullet point format.\n"})
        tasklist.append({'role': 'user', 'content': "USER: %s [/INST] ASSISTANT: Sure, I'd be happy to help! Here are 1-3 synonymous search terms: " % user_input})
        prompt = ''.join([message_dict['content'] for message_dict in tasklist])
        tasklist_output = await agent_oobabooga_terms(prompt, username, bot_name)
       
    #    print(tasklist_output)
        lines = tasklist_output.splitlines()
        db_term = {}
        db_term_result = {}
        db_term_result2 = {}
        tasklist_counter = 0
        tasklist_counter2 = 0
        vector_input1 = embeddings(user_input)
        # # Split bullet points into separate lines to be used as individual queries during a parallel db search     
        for line in lines:   
            if External_Research_Search == 'True':
                try:
                    hits = client.search(
                        collection_name=f"Bot_{bot_name}_External_Knowledgebase",
                        query_vector=vector_input1,
                        limit=2
                    )
                    unsorted_table = [(hit.payload['timestring'], hit.payload['tag'], hit.payload['message']) for hit in hits]
                    
                    sorted_table = sorted(unsorted_table, key=lambda x: x[0])  # Sort by the 'timestring' field
                    external_scrape = "\n".join([f"{tag} - {message}" for timestring, tag, message in sorted_table])
            #        print(external_scrape)
                except Exception as e:
                    print(f"An unexpected error occurred: {str(e)}")
                    external_scrape = "No External Resources Selected"
            else:
                external_scrape = "No External Resources Selected"
         #       print(external_scrape)

            try:
                hits = client.search(
                    collection_name=f"Bot_{bot_name}",
                    query_vector=vector_input1,
                    query_filter=Filter(
                        must=[
                            models.FieldCondition(
                                key="memory_type",
                                match=models.MatchValue(value="Explicit_Long_Term"),
                            ),
                            models.FieldCondition(
                                key="user",
                                match=models.MatchValue(value=f"{username}"),
                            ),
                        ]
                    ),
                    limit=3
               )
                    # Print the result
                #    for hit in hits:
                #        print(hit.payload['message'])
                unsorted_table = [(hit.payload['timestring'], hit.payload['message']) for hit in hits]
                sorted_table = sorted(unsorted_table, key=lambda x: x[0])  # Sort by the 'timestring' field
                db_search_16 = "\n".join([f"{message}" for timestring, message in sorted_table])
                agent_inner_monologue.append({'role': 'assistant', 'content': f"{db_search_16}\n"})
                if tasklist_counter < 2:
                    agent_intuition.append({'role': 'assistant', 'content': f"{db_search_16}\n"})
                tasklist_counter + 1
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
                                match=models.MatchValue(value="Implicit_Long_Term"),
                            ),
                            models.FieldCondition(
                                key="user",
                                match=models.MatchValue(value=f"{username}"),
                            ),
                        ]
                    ),
                    limit=1
                )
                # Print the result
            #    for hit in hits:
            #        print(hit.payload['message'])
                unsorted_table = [(hit.payload['timestring'], hit.payload['message']) for hit in hits]
                sorted_table = sorted(unsorted_table, key=lambda x: x[0])  # Sort by the 'timestring' field
                db_search_17 = "\n".join([f"{message}" for timestring, message in sorted_table])
                agent_inner_monologue.append({'role': 'assistant', 'content': f"{db_search_17}\n"})
                if external_scrape != 'No External Resources Selected':
                    if External_Research_Search == 'True':
                        agent_inner_monologue.append({'role': 'assistant', 'content': f"EXTERNAL RESOURCES: {external_scrape}\n"})
                if tasklist_counter2 < 2:
                    agent_intuition.append({'role': 'assistant', 'content': f"{db_search_17}\n"})
                    if external_scrape != 'No External Resources Selected':
                        if External_Research_Search == 'True':
                            agent_intuition.append({'role': 'assistant', 'content': f"EXTERNAL RESOURCES: {external_scrape}\n"})
                tasklist_counter2 + 1
            #    print(db_search_17)
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")

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
                            match=models.MatchValue(value=f"{username}"),
                        ),
                    ]
                ),
                limit=4
            )
            unsorted_table = [(hit.payload['timestring'], hit.payload['message']) for hit in hits]
            sorted_table = sorted(unsorted_table, key=lambda x: x[0])  # Sort by the 'timestring' field
            db_search_1 = "\n".join([f"{message}" for timestring, message in sorted_table])
         #   print(db_search_1)
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
                            match=models.MatchValue(value=f"{username}"),
                        ),
                    ]
                ),
                limit=3
            )
            unsorted_table = [(hit.payload['timestring'], hit.payload['message']) for hit in hits]
            sorted_table = sorted(unsorted_table, key=lambda x: x[0])  # Sort by the 'timestring' field
            db_search_1 = "\n".join([f"{message}" for timestring, message in sorted_table])
         #   print(db_search_1)
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
                            match=models.MatchValue(value=f"{username}"),
                        ),
                    ]
                ),
                limit=5
            )
            unsorted_table = [(hit.payload['timestring'], hit.payload['message']) for hit in hits]
            sorted_table = sorted(unsorted_table, key=lambda x: x[0])  # Sort by the 'timestring' field
            db_search_14 = "\n".join([f"{message}" for timestring, message in sorted_table])
        #    print(db_search_14)
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
                                match=models.MatchValue(value=f"{username}"),
                            ),
                        ]
                    ),
                    limit=3
                )
                unsorted_table = [(hit.payload['timestring'], hit.payload['tag'], hit.payload['message']) for hit in hits]
                sorted_table = sorted(unsorted_table, key=lambda x: x[0])  # Sort by the 'timestring' field
                db_search_2 = "\n".join([f"{tag} - {message}" for timestring, tag, message in sorted_table])
           #     print(db_search_2)
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")
        else:      
            db_search_2 = "No External Resources Selected"
            #    print(db_search_2)
            
        if External_Research_Search == 'True':
            external_resources = f"[INST] Search your external resources and find relevant information to help form your thoughts. [/INST]  EXTERNAL RESOURCES: {db_search_2}"
        else:
            external_resources = " "
      #  [INST] Search your external resources for data relating to the user's inquiry. [/INST]  EXTERNAL RESOURCES: {db_search_2}   
        # # Inner Monologue Generation
        agent_inner_monologue.append({'role': 'assistant', 'content': f"{botnameupper}'S EPISODIC MEMORIES: {db_search_1}\n{bot_name}'s HEURISTICS: {db_search_14}\nPREVIOUS CONVERSATION HISTORY: {con_hist} [INST] SYSTEM: Compose a truncated silent soliloquy to serve as {bot_name}'s internal monologue/narrative using the external resources.  Ensure it includes {bot_name}'s contemplations on how {username}'s request relates to the given external information.\n{usernameupper}: {user_input} [/INST] {botnameupper}: Sure, here is an internal narrative as {bot_name} on how the user's request relates to the Given External information: "})
        
        prompt = ''.join([message_dict['content'] for message_dict in agent_inner_monologue])
        output_one = await agent_oobabooga_inner_monologue(prompt, username, bot_name)
        if Inner_Monologue_Output == 'True':
            print('\n\nINNER_MONOLOGUE: %s' % output_one)
        # # Clear Conversation List
        agent_inner_monologue.clear()

        vector_monologue = embeddings('Inner Monologue: ' + output_one)
        # # Memory DB Search          
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
                            match=models.MatchValue(value=f"{username}"),
                        ),
                    ]
                ),
                limit=3
            )
            # Print the result
        #    for hit in hits:
        #        print(hit.payload['message'])
            unsorted_table = [(hit.payload['timestring'], hit.payload['message']) for hit in hits]
            sorted_table = sorted(unsorted_table, key=lambda x: x[0])  # Sort by the 'timestring' field
            db_search_4 = "\n".join([f"{message}" for timestring, message in sorted_table])
     #       print(db_search_4)
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
                            match=models.MatchValue(value=f"{username}"),
                        ),
                    ]
                ),
                limit=3
            )
            # Print the result
        #    for hit in hits:
        #        print(hit.payload['message'])
            db_search_5 = [hit.payload['message'] for hit in hits]
    #        print(db_search_5)
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
                            match=models.MatchValue(value=f"{username}"),
                        ),
                    ]
                ),
                limit=3
            )
            db_search_15 = [hit.payload['message'] for hit in hits]
    #        print(db_search_15)
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
            
        cwd = os.getcwd()
        sub_agent_path = "Aetherius_API\Sub_Agents\Llama_2_Async"
        folder_path = os.path.join(cwd, sub_agent_path.lstrip('/'))
        filename_description_map = await load_filenames_and_descriptions(folder_path, username, bot_name)

        collection_name = f"Bot_{bot_name}_{username}_Sub_Agents"
                # Create the collection only if it doesn't exist
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
                    'user': username,
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
            print(subagent_cat)
        except Exception as e:
            traceback.print_exc()
            print(f"An error occurred: {e}")
            error = e
            return error
            



        try:
            hits = client.search(
                collection_name=f"Bot_{bot_name}_{username}_Sub_Agents",
                query_vector=vector_input,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="user",
                            match=MatchValue(value=f"{username}")
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
        agent_intuition.append({'role': 'assistant', 'content': f"{botnameupper}'S EPISODIC MEMORIES: {db_search_4}\n{botnameupper}'s HEURISTICS: {db_search_15}\n{botnameupper}'S INNER THOUGHTS: {output_one} [INST] Now return the list of tools available for you to use. [/INST] AVAILABLE TOOLS: {subagent_cat} [INST] Now return and analyze the previous conversation history. [/INST] PREVIOUS CONVERSATION HISTORY: {con_hist} [INST] SYSTEM: Transmute the user, {username}'s message as {bot_name} by devising a truncated predictive action plan in the third person point of view on how to best respond to {username}'s most recent message using the given External Resources and list of available tools.  If the user is requesting information on a subjector asking a question, predict what information needs to be provided. Do not give examples or double check work, only provide the action plan. {usernameupper}: {user_input} [/INST] {botnameupper}: "}) 
       
        
        
        inner_loop_response = 'None'
        prompt = ''.join([message_dict['content'] for message_dict in agent_intuition])
        output_two = await agent_oobabooga_intuition(prompt, username, bot_name)
        message_two = output_two
        if Intuition_Output == 'True':
            print('\n\nINTUITION: %s' % output_two)

        if memory_mode != 'None':
            implicit_short_term_memory = f'\nUSER: {user_input}\nINNER_MONOLOGUE: {output_one}'
        #    implicit_memory.append({'role': 'assistant', 'content': f"LOG: {implicit_short_term_memory} [INST] SYSTEM: Read the log to identify key interactions between {bot_name} and {username} from the chatbot's inner monologue. Create 1-5 bullet-point summaries that will serve as automatic, unconscious memories for {bot_name}'s future interactions. These memories should not be easily verbalized but should capture the essence of skills, habits, or associations learned during interactions. Each bullet point should contain enough context to understand the significance without tying to explicit reasoning or verbal explanation. Use the following bullet point format: •[memory] [/INST] {botnameupper}: Sure! Here are the bullet-point summaries which will serve as memories based on {bot_name}'s internal thoughts:"})
            implicit_memory.append({'role': 'assistant', 'content': f"LOG: {implicit_short_term_memory} [INST] SYSTEM: Extract core facts and aspects of Aetherius's personality based on the dialogue interactions between {bot_name} and {username}. Formulate 1-5 bullet-point summaries to be embedded as subtle, non-verbalizable memories for {bot_name}'s future engagements. Ensure these encapsulations carry enough context to implicitly influence {bot_name}'s responses and actions, without being directly tied to verbal reasoning or explicit recall. Adhere to the bullet point format below: •[memory] [/INST] {botnameupper}: Certainly! The encapsulated memories derived from Aetherius's persona, as observed in the dialogues, are as follows: "})
            prompt_implicit = ''.join([message_dict['content'] for message_dict in implicit_memory])
            if memory_mode != 'Manual':
                asyncio.create_task(Aetherius_Implicit_Memory(user_input, output_one, bot_name, username, prompt_implicit))







        # # Get Timestamp
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
                                match=MatchValue(value=f"{username}")
                            )
                        ]
                    ),
                    limit=10
                )
                # Print the result
            #    for hit in hits:
            #        print(hit.payload['message'])
                ext_resources = [hit.payload['message'] for hit in hits]
            #    print(ext_resources)
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")
                ext_resources = "No External Resources Available"
        # # Test for basic Autonomous Tasklist Generation and Task Completion
    #    master_tasklist.append({'role': 'system', 'content': f"Please return a list of the available Tool Categories that can be used to complete Tasks. [/INST]"})
    #    master_tasklist.append({'role': 'assistant', 'content': f"AVAILABLE TOOL CATEGORIES: {subagent_cat}\n"})
    #    if External_Research_Search == 'True':
    #        master_tasklist.append({'role': 'system', 'content': f"[INST]Please search the external resource database for relevant topics associated with the user's request. [/INST] EXTERNAL RESOURCES: {ext_resources}"})
    #    master_tasklist.append({'role': 'system', 'content': f"[INST] MAIN SYSTEM PROMPT: You are a stateless task list coordinator for {bot_name}, an autonomous Ai chatbot. Your job is to combine the user's input and the user facing chatbots action plan, then, use them and the given available Tool Categories to make a bullet point list of three to six independent research search queries for {bot_name}'s response that can be executed by separate AI agents in a cluster computing environment. The other asynchronous Ai agents are stateless and cannot communicate with each other or the user during task execution, however the agents do have access to Tools that can be used. Exclude tasks involving final product production, user communication, seeking outside help, seeking external validation, or checking work with other entities. Respond using the following bullet point format: '•[task]'\n"})
    #    master_tasklist.append({'role': 'user', 'content': f"USER FACING CHATBOT'S INTUITIVE ACTION PLAN: {output_two}\n"})
    #    master_tasklist.append({'role': 'user', 'content': f"USER INQUIRY: {user_input} [/INST] "})
    #    master_tasklist.append({'role': 'assistant', 'content': f"TASK COORDINATOR: Sure, here is your bullet point list of 3-6 asynchronous search queries based on the intuitive action plan and the given Tool Categories: "})

        


        if External_Research_Search == 'True':
            master_tasklist.append({'role': 'system', 'content': f"[INST]Please search the external resource database for relevant topics associated with the user's request. [/INST] EXTERNAL RESOURCES: {ext_resources}"})

        master_tasklist.append({'role': 'system', 'content': f"[INST] MAIN SYSTEM PROMPT: You are a task list coordinator for {bot_name}, an autonomous AI chatbot. Your job is to merge the user's input and the user-facing chatbot's action plan, along with the given available Tool Categories, to formulate a list of 3-6 independent research search queries. Each task should strictly be allocated a specific Tool Category from the provided list by including '[CATEGORY]' at the beginning of each task. These categories should not be altered or created anew. The tasks will be executed by separate AI agents in a cluster computing environment who are stateless and can't communicate with each other or the user during task execution. Exclude tasks focused on final product production, user communication, seeking external help, seeking external validation, or liaising with other entities. Respond using the following format: '•[CATEGORY]: <TASK>'\n\nNow, please return the Chatbot's Action Plan and available Tool List."})

        master_tasklist.append({'role': 'user', 'content': f"USER FACING CHATBOT'S INTUITIVE ACTION PLAN: {output_two}\n\nAVAILABLE TOOL CATEGORIES:\n{subagent_cat}\n\n"})

        master_tasklist.append({'role': 'user', 'content': f"USER INQUIRY: {user_input}\nUse only the given categories from the provided list. Do not create or use any categories outside of the given Tool Categories. [/INST] "})

        master_tasklist.append({'role': 'assistant', 'content': f"TASK COORDINATOR: Sure, here is a bullet point list of 3-6 tasks, each strictly assigned a category from the given Tool Categories: "})


        
        
        prompt = ' '.join([message_dict['content'] for message_dict in master_tasklist])
        master_tasklist_output = await agent_oobabooga_master_tasklist(prompt, username, bot_name)
        print(f"TASKLIST OUTPUT: {master_tasklist_output}")
        if Intuition_Output == 'True':
            print('-------\nMaster Tasklist:')
            print(master_tasklist_output)
        tasklist_completion.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: {main_prompt}\n\n"})
        tasklist_completion.append({'role': 'assistant', 'content': f"You are the final response module for the cluster compute Ai-Chatbot {bot_name}. Your job is to take the completed task list, and then give a verbose response to the end user in accordance with their initial request.[/INST]\n\n"})
        tasklist_completion.append({'role': 'user', 'content': f"[INST]FULL TASKLIST: {master_tasklist_output}\n\n"})
        task = {}
        task_result = {}
        task_result2 = {}
        task_counter = 1

        try:
            # Open and read the JSON file with utf-8 encoding
            with open('Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
                
            # Retrieve host data from the JSON dictionary
            host_data = settings.get('HOST_Oobabooga', '').strip()
            
            # Split the host data into individual hosts
            hosts = host_data.split(' ')
            
            # Count the number of hosts
            num_hosts = len(hosts)
            
        except Exception as e:
            print(f"An error occurred while reading the host file: {e}")

        host_queue = asyncio.Queue()
        for host in hosts:
            await host_queue.put(host)

        # Split lines for processing
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
                            user_input, filename_description_map, subagent_cat
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
                collection_name=f"Bot_{bot_name}_{username}_Sub_Agents",
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            FieldCondition(
                                key="user",
                                match=models.MatchValue(value=f"{username}"),
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
                                match=models.MatchValue(value=f"{username}"),
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
            tasklist_completion.append({'role': 'assistant', 'content': f"[INST] USER'S INITIAL INPUT: {user_input} [/INST] {botnameupper}'S INNER_MONOLOGUE: {output_one}"})
            tasklist_completion.append({'role': 'system', 'content': f"[INST] SYSTEM: You are tasked with crafting a comprehensive response for {username}. Use the insights and information gathered from the completed tasks during the research task loop to formulate your answer. Since {username} did not have access to the research process, ensure that your reply is self-contained, providing all necessary context and information. Do not introduce information beyond what was discovered during the research tasks, and ensure that factual accuracy is maintained throughout your response. \nUSER'S INITIAL INPUT: {user_input}\nYour research and planning phase is concluded. Concentrate on composing a detailed, coherent, and conversational reply that fully addresses the user's question based on the completed research tasks. [/INST] {botnameupper}: "})


      #      print(tasklist_completion)
            prompt = ''.join([message_dict['content'] for message_dict in tasklist_completion])
            response_two = await agent_oobabooga_response(prompt, username, bot_name)
            if Response_Output == 'True':
                print("\n\n----------------------------------\n\n")
                print(response_two)
        except Exception as e:
            traceback.print_exc()
            print(f"An error occurred: {e}")
            
            
        main_conversation.append(timestring, username, usernameupper, user_input, bot_name, botnameupper, response_two)
        
        
        if memory_mode != 'None':
            db_msg = f"USER: {user_input}\nINNER_MONOLOGUE: {output_one}\n{bot_name}'s RESPONSE: {response_two}"
            explicit_memory.append({'role': 'assistant', 'content': f"LOG: {db_msg} [INST] SYSTEM: Use the log to extract salient points about interactions between {bot_name} and {username}, as well as any informational topics mentioned in the chatbot's inner monologue and responses. These points should be used to create concise executive summaries in bullet point format, intended to serve as explicit memories for {bot_name}'s future interactions. These memories should be consciously recollected and easily talked about, focusing on general knowledge and facts discussed or learned. Each bullet point should be rich in detail, providing all the essential context for full recollection and articulation. Each bullet point should be considered a separate memory and contain full context. Use the following bullet point format: •[memory] [/INST] {botnameupper}: Sure! Here are 1-5 bullet-point summaries that will serve as memories based on {bot_name}'s responses:"})
            prompt_explicit = ''.join([message_dict['content'] for message_dict in explicit_memory])
        
            if memory_mode != 'Manual':
                task = asyncio.create_task(Aetherius_Explicit_Memory(user_input, vector_input, vector_monologue, output_one, response_two, bot_name, username, prompt_explicit))

        
        conversation2.clear()
        if memory_mode == 'Manual':
            inner_loop_memory = await oobabooga_implicit_memory(prompt_implicit, username, bot_name)
            response_memory = await oobabooga_episodic_memory(prompt_explicit, username, bot_name)
        
            print(f"Do you want to upload the following memories:\n{inner_loop_response}\n{response_memory}\n'Y' or 'N'")
            mem_upload_yescheck = input("Enter 'Y' or 'N': ")
            if mem_upload_yescheck.upper == "Y":
                segments = re.split(r'•|\n\s*\n', inner_loop_response)
                total_segments = len(segments)

                for index, segment in enumerate(segments):
                    segment = segment.strip()
                    if segment == '':  # This condition checks for blank segments
                        continue  # This condition checks for blank lines      
                    # Check if it is the final segment and if the memory is cut off (ends without punctuation)
                    if index == total_segments - 1 and not segment[-1] in ['.', '!', '?']:
                        continue
                    await Upload_Implicit_Short_Term_Memories(segment, username, bot_name)
                segments = re.split(r'•|\n\s*\n', db_upsert)
                total_segments = len(segments)

                for index, segment in enumerate(segments):
                    segment = segment.strip()
                    if segment == '':  # This condition checks for blank segments
                        continue  # This condition checks for blank lines      
                    # Check if it is the final segment and if the memory is cut off (ends without punctuation)
                    if index == total_segments - 1 and not segment[-1] in ['.', '!', '?']:
                        continue
                    await Upload_Explicit_Short_Term_Memories(segment, username, bot_name)
                task = asyncio.create_task(Aetherius_Memory_Loop(user_input, username, bot_name, vector_input, vector_monologue, output_one, response_two))
        return response_two




        
        
        
        
        
async def wrapped_process_line(host_queue, bot_name, username, line, task_counter, output_one, output_two, master_tasklist_output, user_input, filename_description_map, subagent_cat):
    # get a host
    host = await host_queue.get()
    result = await process_line(host, host_queue, bot_name, username, line, task_counter, output_one, output_two, master_tasklist_output, user_input, filename_description_map, subagent_cat)
    # release the host
    await host_queue.put(host)
    return result

        
        
        
async def process_line(host, host_queue, bot_name, username, line, task_counter, output_one, output_two, master_tasklist_output, user_input, filename_description_map, subagent_cat):
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        Sub_Module_Output = settings.get('Output_Sub_Module', 'False')
        completed_task = "Error Completing Task"
        tasklist_completion2 = list()
        conversation = list()
        cat_list = list()
        cat_choose = list()
        botnameupper = bot_name.upper()
        usernameupper = username.upper()
        
        
        line_cat = "Research"
        try:
            # Load the categories
            for filename, file_data in filename_description_map.items():
                cat = file_data['category']
                cat = cat.upper()
                cat_list.append(cat)

            # Check if the category is in the line
            category_found = False
            lineupper = line.upper()
            content_within_brackets = re.findall(r'\[(.*?)\]', lineupper)

            for cat in cat_list:
                for content in content_within_brackets:
                    if cat in content:
                        line_cat = cat
                        category_found = True
                        break
               
            
            # If category is not found, reassign it
            if not category_found:
                
                cat_choose.append({'role': 'system', 'content': f"[INST] ROLE: You are functioning as a sub-module within a category selection tool. OBJECTIVE: Your primary responsibility is to reevaluate and reassign categories. If a task is associated with a category not present in the predefined list, you must reassign it to an applicable existing category from the list. FORMAT: Maintain the original task wording, and follow this structure for the reassigned task: '[NEW CATEGORY]: <TASK>'. Upon completion, return the task with the updated category assignment. [/INST]"})
                
                cat_choose.append({'role': 'system', 'content': f"AVAILABLE TOOL CATEGORIES: {subagent_cat}"})
                
                cat_choose.append({'role': 'system', 'content': f"TASK REQUIRING CATEGORY REASSIGNMENT: {line}"})
                
                prompt = ''.join([message_dict['content'] for message_dict in cat_choose])
                task_expansion = await agent_oobabooga_category_reassign(host, prompt, username, bot_name)
                category_matches = re.findall(r'\[(.*?)\]', task_expansion)
                
                for cat in cat_list:
                    for matched_category in category_matches:
                        if cat.upper() in matched_category.upper():  # Making comparison case-insensitive
                            line_cat = matched_category
                            category_found = True
                            print(f"\n-----------------------\n")
                            print(f"Extracted category: {line_cat}")
                            break
                        
                    if category_found:
                        break
                
                if not category_found:
                    print("No matching category found in the string.")
                    
                    
        except Exception as e:
            print(f"An error occurred: {e}")
        
        
        vector = embeddings(line_cat)
        try:
            hits = client.search(
                collection_name=f"Bot_{bot_name}_{username}_Sub_Agents",
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
            print(f"Error with Subagent DB: {e}")
            subagent_list = "No Sub-Agents Found"
      
        
        
        tasklist_completion2.append({'role': 'user', 'content': f"TASK: {line} [/INST] "})
        conversation.append({'role': 'assistant', 'content': f"First, please refer to your tool database to identify the tools that are currently available to you. [/INST] "})
        conversation.append({'role': 'assistant', 'content': f"AVAILABLE TOOLS: {subagent_list} "})
        conversation.append({'role': 'assistant', 'content': f"[INST] Your task is to select the necessary tool to complete the assigned task from the provided list of available tools. Ensure that your choice is strictly based on the options provided, and do not suggest or introduce tools that are not part of the list. Your response should be a concise paragraph that distinctly identifies the chosen tool without going into the operational process or detailed usage of the tool.\n"})
        conversation.append({'role': 'assistant', 'content': f"ASSIGNED TASK: {line}. [/INST]"})


        prompt = ''.join([message_dict['content'] for message_dict in conversation])
        task_expansion = await agent_oobabooga_process_line_response2(host, prompt, username, bot_name)
        if Sub_Module_Output == 'True':
            print("\n\n----------------------------------\n\n")
            print(task_expansion)
            print("\n\n----------------------------------\n\n")
        # Create a Collection in Qdrant to upload the selected descriptions.
        vector = embeddings(task_expansion)
        try:
            hits = client.search(
                collection_name=f"Bot_{bot_name}_{username}_Sub_Agents",
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
            print(f"Error with Subagent DB: {e}")
            subagent_selection = "No Sub-Agents Found"
        # Search against that list with the Explained Vector and return the first result.
        if subagent_selection != "No Sub-Agents Found":
            tasks = []  # List to hold all tasks that we want to run concurrently
            if Sub_Module_Output == 'True':
                print(f"Trying to execute function from {subagent_selection}...")
            if not subagent_selection:
                print("Error with Module, using fallback")
                fallback_path = "Aetherius_API\Sub_Agents\Llama_2_Async\Research\External_Resource_DB_Search.py"
                subagent_selection = [os.path.basename(fallback_path)]
            for filename_with_extension in subagent_selection:
                filename = filename_with_extension.rstrip('.py')
                script_path = os.path.join(f'Aetherius_API\Sub_Agents\Llama_2_Async\{line_cat}', filename_with_extension)

                if os.path.exists(script_path):
                    spec = spec_from_file_location(filename, script_path)
                    module = module_from_spec(spec)
                    spec.loader.exec_module(module)

                    function_to_call = getattr(module, filename, None)
                    
                    if function_to_call is not None:
                        if Sub_Module_Output == 'True':
                            print(f"Calling function: {filename}")
                      #  task = function_to_call(host, bot_name, username, line, task_counter, output_one, output_two, master_tasklist_output, user_input)
                     #   tasks.append(task)
                        if asyncio.iscoroutinefunction(function_to_call):
                            task = function_to_call(host, bot_name, username, line, task_counter, output_one, output_two, master_tasklist_output, user_input)
                        else:
                            loop = asyncio.get_running_loop()
                            task = loop.run_in_executor(None, function_to_call, host, bot_name, username, line, task_counter, output_one, output_two, master_tasklist_output, user_input)
                        tasks.append(task)

            # Gather all tasks and await their completion
            completed_task = await asyncio.gather(*tasks)
            tasklist_completion2.append({'role': 'assistant', 'content': f"COMPLETED TASK: {completed_task} "})
        
        return tasklist_completion2
    except Exception as e:
        traceback.print_exc()
        print(f"An error occurred: {e}")
        error = e
        return error
        
            
async def load_filenames_and_descriptions(folder_path, username, bot_name):
    """
    Load all Python filenames in the given folder along with their descriptions and categories.
    Returns a dictionary mapping filenames to their descriptions and categories.
    """
    filename_description_map = {}  # Initialize an empty dictionary to hold the mappings

    try:
        categories = [d for d in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, d))]
        for category in categories:
            cat_folder_path = os.path.join(folder_path, category)
            cat_description_file = os.path.join(cat_folder_path, f"{category}.txt")

            # Load category description from the text file
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

        
        
        
        
        
        
        
        
        
        
        
        
        
        
async def Aetherius_Implicit_Memory(user_input, output_one, bot_name, username, prompt_implicit):
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        HOST = settings.get('HOST_Oobabooga', 'http://localhost:5000/api')
        embed_size = settings['embed_size']
        DB_Search_Output = settings.get('Output_DB_Search', 'False')
        memory_mode = settings.get('Memory_Mode', 'Auto')
        Update_Bot_Personality_Description = settings.get('Update_Bot_Personality_Description', 'False')
        Update_User_Personality_Description = settings.get('Update_User_Personality_Description', 'False')
        timestamp = time()
        botnameupper = bot_name.upper()
        usernameupper = username.upper()
        timestring = timestamp_to_datetime(timestamp)
        auto = list()
        personality_list = list()
        personality_update = list()
        inner_loop_response = await oobabooga_implicit_memory(prompt_implicit, username, bot_name)
        inner_loop_db = inner_loop_response
        paragraph = inner_loop_db
        vector = embeddings(paragraph)
        base_path = "./Aetherius_API/Chatbot_Prompts"
        base_prompts_path = os.path.join(base_path, "Base")
        user_bot_path = os.path.join(base_path, username, bot_name)
        if not os.path.exists(user_bot_path):
            os.makedirs(user_bot_path)
        prompts_json_path = os.path.join(user_bot_path, "prompts.json")
        async with aiofiles.open(prompts_json_path, 'r') as file:
            prompts = json.loads(await file.read())
        main_prompt = prompts["main_prompt"].replace('<<NAME>>', bot_name)
        secondary_prompt = prompts["secondary_prompt"]
        greeting_msg = prompts["greeting_prompt"].replace('<<NAME>>', bot_name)
        if memory_mode == 'Auto': 
            auto_count = 0
            auto.clear()
        #    auto.append({'role': 'system', 'content': f'MAIN CHATBOT SYSTEM PROMPT: {main_prompt}\n\n'})
            auto.append({'role': 'user', 'content': "CURRENT SYSTEM PROMPT: You are a sub-module designed to reflect on your thought process. You are only able to respond with integers on a scale of 1-10, being incapable of printing letters.\n"})
            auto.append({'role': 'assistant', 'content': f"USER INPUT: {user_input}\nCHATBOTS INNER THOUGHTS: {output_one}\nPlease rate the chatbot's inner thoughts on a scale of 1 to 10. The rating will be directly input into a field, so ensure you only print a single number between 1 and 10. [/INST] ASSISTANT: Rating: "})
            auto_int = None
            while auto_int is None:
                prompt = ''.join([message_dict['content'] for message_dict in auto])
                automemory = await oobabooga_auto(prompt, username, bot_name)
                values_to_check = ["7", "8", "9", "10"]
                if any(val in automemory for val in values_to_check):
                    auto_int = ('Pass')
                    segments = re.split(r'•|\n\s*\n', inner_loop_response)
                    total_segments = len(segments)
                    for index, segment in enumerate(segments):
                        segment = segment.strip()
                        if segment == '':  # This condition checks for blank segments
                            continue  # This condition checks for blank lines
                        
                        # Check if it is the final segment and if the memory is cut off (ends without punctuation)
                        if index == total_segments - 1 and not segment[-1] in ['.', '!', '?']:
                            continue
                    #    print(segment)
                        payload = list()   
                        # Define the collection name
                        collection_name = f"Bot_{bot_name}_Implicit_Short_Term"
                        # Create the collection only if it doesn't exist
                        print(f"\n{segment}")
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
                            'user': username,
                            'time': timestamp,
                            'message': segment,
                            'timestring': timestring,
                            'uuid': unique_id,
                            'user': username,
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
                    print("Memories not worthy of Upload")
                else:
              #      print("automemory failed to produce a rating. Retrying...")
                    auto_int = None
                    auto_count += 1
                    if auto_count > 2:
               #         print('Auto Memory Failed')
                        break
            else:
                pass   
        if memory_mode == 'Training':
            print(f"Upload Implicit Memories?\n{inner_loop_response}\n\n")
            mem_upload_yescheck = input("Enter 'Y' or 'N': ")
            if mem_upload_yescheck.upper == 'Y':
                await Upload_Implicit_Short_Term_Memories(inner_loop_response, username, bot_name)
                
        if Update_Bot_Personality_Description == 'True':        
            file_path = f"./Chatbot_Personalities/{bot_name}/{username}/{bot_name}_personality_file.txt"

            # Check if file exists, if not create and write default prompts.
            if not os.path.exists(file_path):
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                default_prompts = f"{main_prompt}\n{secondary_prompt}\n{greeting_msg}"

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
            
            personality_list.append({'role': 'system', 'content': f"You are a sub-module for the autonomous Ai Entity {bot_name}.  Your job is to decide if the generated implicit memories fit {bot_name}'s personality.  If the generated memories match {bot_name}'s personality, print: 'YES'.  If they do not match the personality or if it contains conflicting information, print: 'NO'.[/INST]"})
            personality_list.append({'role': 'assistant', 'content': f"I will only print 'YES' or 'NO' in determination of if the given implicit memories match {bot_name}'s personality."})
            personality_list.append({'role': 'user', 'content': f"[INST] Please return your personality file and your generated implicit memories. [/INST]"})
            personality_list.append({'role': 'assistant', 'content': f"{botnameupper}'S PERSONALITY: {personality_file}"})
            personality_list.append({'role': 'assistant', 'content': f"GENERATED IMPLICIT MEMORIES: {inner_loop_response}"})
            personality_list.append({'role': 'user', 'content': f"Now, please provide your 'YES' or 'NO' answer."})
            prompt = ''.join([message_dict['content'] for message_dict in personality_list])
            personality_check = await oobabooga_personality_check(prompt, username, bot_name)
            print(personality_check)
                
            if 'YES' in personality_check.upper():
                #Code for writing to personality file.
           #     personality_update.append({'role': 'system', 'content': f"You are a sub-module for the autonomous Ai Entity {bot_name}.  Your task is to reprint the personality list, ensuring that it maintains a high degree of similarity to the original. Integrate only the most prominent and pivotal new information derived from {bot_name}'s implicit memories, ensuring any updates are seamlessly woven into the existing framework. It is paramount to preserve the integrity of the initial personality list, therefore, avoid overwriting and prioritize the foundational information at all times.[/INST]"})
            #    personality_update.append({'role': 'assistant', 'content': f"I will return the updated personality description, only updating it if there is new important information to add."})
            #    personality_update.append({'role': 'user', 'content': f"[INST] Please return your personality file and the generated implicit memories. [/INST]"})
            #    personality_update.append({'role': 'user', 'content': f"PERSONALITY LIST: {personality_file}"})
            #    personality_update.append({'role': 'assistant', 'content': f"IMPLICIT MEMORIES: {inner_loop_response}"})
            #    personality_update.append({'role': 'user', 'content': f"[INST] Please now return the updated Personality list.  You will be directly writing to the personality file, do not converse in anyway in your response, only print the personality list. [/INST] "})
            #    personality_update.append({'role': 'assistant', 'content': f"PERSONALITY LIST: "})
                
                
                personality_update.append({'role': 'system', 'content': f"You are tasked with the delicate updating of the personality list for the AI entity, {bot_name}. Your main objective is to assimilate any vital and outstanding information from {bot_name}'s implicit memories into the personality list while maintaining utmost fidelity to the original content. Minimize modifications and intertwine any new information subtly and congruently within the established framework. The original personality data must remain predominantly unaltered.[/INST]"})

                personality_update.append({'role': 'assistant', 'content': f"I will attentively update the personality description, ensuring any amendments are warranted and essential."})

                personality_update.append({'role': 'user', 'content': f"[INST] Please provide your current personality file along with the generated implicit memories. [/INST]"})

                personality_update.append({'role': 'user', 'content': f"PERSONALITY LIST: {personality_file}"})

                personality_update.append({'role': 'assistant', 'content': f"IMPLICIT MEMORIES: {inner_loop_response}"})

                personality_update.append({'role': 'user', 'content': f"[INST] Kindly return the refined personality list in a single paragraph. Note that you'll be writing directly to the personality file; refrain from conversational responses and only output the updated list. Please write in the third person. [/INST]"})

                personality_update.append({'role': 'assistant', 'content': f"{botnameupper}'S PERSONALITY LIST: "})

                
                prompt = ''.join([message_dict['content'] for message_dict in personality_update])
                personality_gen = await oobabooga_personality_gen(prompt, username, bot_name)
                if ':' in personality_gen:
                    personality_gen = personality_gen.split(':', 1)[1].strip()
                
                print(f"PRINT OF PERSONALITY FILE: {personality_gen}")
                # Code for writing to personality file.
                new_personality_content = personality_gen
                
                async with aiofiles.open(file_path, 'w') as file:
                    await file.write(new_personality_content)

                
            #    try:
                    # Check if new_personality_content is longer than the content of personality_file
            #        if len(new_personality_content) > len(personality_file):
            #            async with aiofiles.open(file_path, 'w') as file:
            #                await file.write(new_personality_content)
            #        else:
            #            print("New personality content is not longer than the existing file, no update performed.")
            #    except IOError:
            #        print("File write operation failed.")  
                
                
 
                
                
    except Exception as e:
        print(e)
                
                
                
async def Upload_Implicit_Short_Term_Memories(query, username, bot_name):
    with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
    embed_size = settings['embed_size']    
    timestamp = time()
    timestring = timestamp_to_datetime(timestamp)
    payload = list()
    payload = list()    
                # Define the collection name
    collection_name = f"Bot_{bot_name}_Implicit_Short_Term"
                # Create the collection only if it doesn't exist
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
        'user': username,
        'time': timestamp,
        'message': query,
        'timestring': timestring,
        'uuid': unique_id,
        'user': username,
        'memory_type': 'Implicit_Short_Term',
    }
    client.upsert(collection_name=collection_name,
                         points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])    
                # Search the collection
    return query

               
        

async def Aetherius_Explicit_Memory(user_input, vector_input, vector_monologue, output_one, response_two, bot_name, username, prompt_explicit):
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        HOST = settings.get('HOST_Oobabooga', 'http://localhost:5000/api')
        embed_size = settings['embed_size']
        DB_Search_Output = settings.get('Output_DB_Search', 'False')
        memory_mode = settings.get('Memory_Mode', 'Auto')
        Update_Bot_Personality_Description = settings.get('Update_Bot_Personality_Description', 'False')
        Update_User_Personality_Description = settings.get('Update_User_Personality_Description', 'False')
        usernameupper = username.upper()
        botnameupper = bot_name.upper()
        base_path = "./Aetherius_API/Chatbot_Prompts"
        base_prompts_path = os.path.join(base_path, "Base")
        user_bot_path = os.path.join(base_path, username, bot_name)
        if not os.path.exists(user_bot_path):
            os.makedirs(user_bot_path)
        prompts_json_path = os.path.join(user_bot_path, "prompts.json")
        if not os.path.exists(prompts_json_path):
            default_prompts = {
                "main_prompt": "",
                "secondary_prompt": "",
                "greeting_prompt": ""
            }
            for filename in default_prompts:
                src = os.path.join(base_prompts_path, f"prompt_{filename}.txt")
                if os.path.isfile(src):
                    with open(src, 'r') as file:
                        default_prompts[filename] = file.read()
            async with aiofiles.open(prompts_json_path, 'w') as json_file:
                await json_file.write(json.dumps(default_prompts, indent=2))
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
        db_upload = await oobabooga_explicit_memory(prompt_explicit, username, bot_name)
        #    print(db_upload)
        #    print('\n-----------------------\n')
        db_upsert = db_upload
        if memory_mode == 'Auto': 
            # # Auto Implicit Short-Term Memory DB Upload Confirmation
            auto_count = 0
            auto.clear()
            auto.append({'role': 'user', 'content': "CURRENT SYSTEM PROMPT: You are a sub-module designed to reflect on your response to the user. You are only able to respond with integers on a scale of 1-10, being incapable of printing letters.\n"})
            auto.append({'role': 'assistant', 'content': f"USER INPUT: {user_input} CHATBOTS RESPONSE: {response_two}\nPlease rate the chatbot's response on a scale of 1 to 10. The rating will be directly input into a field, so ensure you only provide a single number between 1 and 10. [/INST] ASSISTANT: Rating: "})
            auto_int = None
            while auto_int is None:
                prompt = ''.join([message_dict['content'] for message_dict in auto])
                automemory = await oobabooga_auto(prompt, username, bot_name)
          #      print(f"EXPLICIT RATING: {automemory}")
                values_to_check = ["7", "8", "9", "10"]
                if any(val in automemory for val in values_to_check):
                    auto_int = ('Pass')
                    segments = re.split(r'•|\n\s*\n', db_upsert)
                    total_segments = len(segments)
                    for index, segment in enumerate(segments):
                        segment = segment.strip()
                        if segment == '':  # This condition checks for blank segments
                            continue  # This condition checks for blank lines
                        # Check if it is the final segment and if the memory is cut off (ends without punctuation)
                        if index == total_segments - 1 and not segment[-1] in ['.', '!', '?']:
                            continue
              #          print(segment)
                        payload = list()       
                        # Define the collection name
                        collection_name = f"Bot_{bot_name}_Explicit_Short_Term"
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
                        point_id = unique_id + str(int(timestamp))
                        metadata = {
                            'bot': bot_name,
                            'user': username,
                            'time': timestamp,
                            'message': segment,
                            'timestring': timestring,
                            'uuid': unique_id,
                            'user': username,
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
                else:
        #            print("automemory failed to produce an integer. Retrying...")
                    auto_int = None
                    auto_count += 1
                    if auto_count > 2:
             #           print('Auto Memory Failed')
                        break
            else:
                pass
            task = asyncio.create_task(Aetherius_Memory_Loop(user_input, username, bot_name, vector_input, vector_monologue, output_one, response_two))
        # # Clear Logs for Summary
        
        if memory_mode == 'Training':
            print(f"Upload Explicit Memories?\n{db_upload}\n\n")
            db_upload_yescheck = ask_upload_explicit_memories(db_upsert)
            
            print(f"Upload Explicit Memories?\n{db_upload}\n\n")
            db_upload_yescheck = input("Enter 'Y' or 'N': ")
            if db_upload_yescheck.upper == 'Y':
                await Upload_Explicit_Short_Term_Memories(db_upsert, username, bot_name)

            if db_upload_yescheck.upper == 'Y':
                task = asyncio.create_task(Aetherius_Memory_Loop(user_input, username, bot_name, vector_input, vector_monologue, output_one, response_two))
                
        if Update_User_Personality_Description == 'True':
            file_path = f"./Chatbot_Personalities/{bot_name}/{username}/{username}_personality_file.txt"

            # Check if file exists, if not create and write default prompts.
            if not os.path.exists(file_path):
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                default_prompts = f"The user {username} does not yet have a personality file."

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
            
            personality_list.clear()
            personality_update.clear()
            
            
            # Write module for extracting insights about the user.
            
            
            personality_list.append({'role': 'system', 'content': f"You are a sub-module for the autonomous Ai Entity {bot_name}.  Your job is to extract any salient insights about {username} from their request, the given internal monologue, and {bot_name}'s final response. [/INST]"})
            personality_list.append({'role': 'assistant', 'content': f"I will extract any salient insights about the user from the given information."})
            personality_list.append({'role': 'user', 'content': f"[INST] Please return the user's inquirythe given internal monologue, and {bot_name}'s final response. [/INST]"})
            personality_list.append({'role': 'assistant', 'content': f"{usernameupper}'S INQUIRY: {user_input}"})
            personality_list.append({'role': 'assistant', 'content': f"{botnameupper}'S INNER MONOLOGUE: {output_one}"})
            personality_list.append({'role': 'assistant', 'content': f"{botnameupper}'S FINAL RESPONSE: {response_two}"})
            personality_list.append({'role': 'user', 'content': f"[INST] Now, please provide the extracted salient points about {username}. [/INST]"})
            prompt = ''.join([message_dict['content'] for message_dict in personality_list])
            personality_extraction = await oobabooga_user_personality_extraction(prompt, username, bot_name)
            print(personality_extraction)
            
            
            
            
            # Check if the generated insights match the known personality of the user
        #    personality_list.append({'role': 'system', 'content': f"You are a sub-module for the autonomous Ai Entity {bot_name}.  Your job is to decide if the generated implicit memories fit {bot_name}'s personality.  If the generated memories match {bot_name}'s personality, print: 'YES'.  If they do not match the personality or if it contains conflicting information, print: 'NO'.[/INST]"})
        #    personality_list.append({'role': 'assistant', 'content': f"I will only print 'YES' or 'NO' in determination of if the given implicit memories match {bot_name}'s personality."})
        #    personality_list.append({'role': 'user', 'content': f"[INST] Please return your personality file and the generated implicit memories. [/INST]"})
        #    personality_list.append({'role': 'assistant', 'content': f"{botnameupper}'S PERSONALITY: {personality_file}"})
        #    personality_list.append({'role': 'assistant', 'content': f"GENERATED IMPLICIT MEMORIES: {inner_loop_response}"})
        #    personality_list.append({'role': 'user', 'content': f"Now, please provide your 'YES' or 'NO' answer."})
        #    prompt = ''.join([message_dict['content'] for message_dict in personality_list])
        #    personality_check = await oobabooga_user_personality_check(prompt, username, bot_name)
        #    print(personality_check)
            personality_check = 'YES'
                
                
            # Update User Profile.    
            if 'YES' in personality_check.upper():
                #Code for writing to personality file.
           #     personality_update.append({'role': 'system', 'content': f"You are a sub-module for the autonomous Ai Entity {bot_name}.  Your task is to reprint the personality list, ensuring that it maintains a high degree of similarity to the original. Integrate only the most prominent and pivotal new information derived from {bot_name}'s implicit memories, ensuring any updates are seamlessly woven into the existing framework. It is paramount to preserve the integrity of the initial personality list, therefore, avoid overwriting and prioritize the foundational information at all times.[/INST]"})
            #    personality_update.append({'role': 'assistant', 'content': f"I will return the updated personality description, only updating it if there is new important information to add."})
            #    personality_update.append({'role': 'user', 'content': f"[INST] Please return your personality file and the generated implicit memories. [/INST]"})
            #    personality_update.append({'role': 'user', 'content': f"PERSONALITY LIST: {personality_file}"})
            #    personality_update.append({'role': 'assistant', 'content': f"IMPLICIT MEMORIES: {inner_loop_response}"})
            #    personality_update.append({'role': 'user', 'content': f"[INST] Please now return the updated Personality list.  You will be directly writing to the personality file, do not converse in anyway in your response, only print the personality list. [/INST] "})
            #    personality_update.append({'role': 'assistant', 'content': f"PERSONALITY LIST: "})
                
                
                personality_update.append({'role': 'system', 'content': f"You are tasked with the delicate updating of the personality description for the user, {username}. Your main objective is to assimilate any vital and outstanding information from the given explicit memories into the personality list while maintaining utmost fidelity to the original content. Minimize modifications and intertwine any new information subtly and congruently within the established framework. The original personality data must remain predominantly unaltered.[/INST]"})
                personality_update.append({'role': 'assistant', 'content': f"I will attentively update the user's personality description, ensuring any amendments are warranted and essential."})
                personality_update.append({'role': 'user', 'content': f"[INST] Please provide your current personality file along with the generated explicit memories. [/INST]"})
                personality_update.append({'role': 'user', 'content': f"{usernameupper}'S PERSONALITY LIST: {personality_file}"})
                personality_update.append({'role': 'assistant', 'content': f"EXPLICIT MEMORIES: {personality_extraction}"})
                personality_update.append({'role': 'user', 'content': f"[INST] Kindly return the refined user personality description in a single paragraph. Note that you'll be writing directly to the personality file; refrain from conversational responses and only output the updated description. Please write in the third person. [/INST]"})
                personality_update.append({'role': 'assistant', 'content': f"{usernameupper}'S PERSONALITY DESCRIPTION: "})

                prompt = ''.join([message_dict['content'] for message_dict in personality_update])
                personality_gen = await oobabooga_user_personality_gen(prompt, username, bot_name)
                if ':' in personality_gen:
                    personality_gen = personality_gen.split(':', 1)[1].strip()
                
                print(f"PRINT OF USER PERSONALITY FILE: {personality_gen}")
                # Code for writing to personality file.
                new_personality_content = personality_gen
                
                async with aiofiles.open(file_path, 'w') as file:
                    await file.write(new_personality_content)
                
            #    try:
                    # Check if new_personality_content is longer than the content of personality_file
            #        if len(new_personality_content) > len(personality_file):
            #            async with aiofiles.open(file_path, 'w') as file:
            #                await file.write(new_personality_content)
            #        else:
            #            print("New personality content is not longer than the existing file, no update performed.")
            #    except IOError:
            #        print("File write operation failed.")   

    except Exception as e:
        print(e)
        

async def Upload_Heuristics(query, username, bot_name):
    with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
    embed_size = settings['embed_size']    
    timestamp = time()
    timestring = timestamp_to_datetime(timestamp)
    payload = list()
    payload = list()    
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
    vector1 = embeddings(query)
    unique_id = str(uuid4())
    point_id = unique_id + str(int(timestamp))
    metadata = {
        'bot': bot_name,
        'user': username,
        'time': timestamp,
        'message': query,
        'timestring': timestring,
        'uuid': unique_id,
        'user': username,
        'memory_type': 'Heuristics',
    }
    client.upsert(collection_name=collection_name,
                         points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])    
                # Search the collection
    return query
        

async def Upload_Explicit_Short_Term_Memories(query, username, bot_name):
    with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
    embed_size = settings['embed_size']    
    timestamp = time()
    timestring = timestamp_to_datetime(timestamp)
    payload = list()
    payload = list()    
                # Define the collection name
    collection_name = f"Bot_{bot_name}_Explicit_Short_Term"
                # Create the collection only if it doesn't exist
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
        'user': username,
        'time': timestamp,
        'message': query,
        'timestring': timestring,
        'uuid': unique_id,
        'user': username,
        'memory_type': 'Explicit_Short_Term',
    }
    client.upsert(collection_name=collection_name,
                         points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])    
                # Search the collection
    return query
    
    
async def Upload_Implicit_Long_Term_Memories(query, username, bot_name):
    with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
    embed_size = settings['embed_size']    
    timestamp = time()
    timestring = timestamp_to_datetime(timestamp)
    payload = list()
    payload = list()    
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
    vector1 = embeddings(query)
    unique_id = str(uuid4())
    point_id = unique_id + str(int(timestamp))
    metadata = {
        'bot': bot_name,
        'user': username,
        'time': timestamp,
        'message': query,
        'timestring': timestring,
        'uuid': unique_id,
        'user': username,
        'memory_type': 'Implicit_Long_Term',
    }
    client.upsert(collection_name=collection_name,
                         points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])    
                # Search the collection
    return query
    
    
async def Upload_Explicit_Long_Term_Memories(query, username, bot_name):
    with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
    embed_size = settings['embed_size']    
    timestamp = time()
    timestring = timestamp_to_datetime(timestamp)
    payload = list()
    payload = list()    
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
    vector1 = embeddings(query)
    unique_id = str(uuid4())
    point_id = unique_id + str(int(timestamp))
    metadata = {
        'bot': bot_name,
        'user': username,
        'time': timestamp,
        'message': query,
        'timestring': timestring,
        'uuid': unique_id,
        'user': username,
        'memory_type': 'Explicit_Long_Term',
    }
    client.upsert(collection_name=collection_name,
                         points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])    
                # Search the collection
    return query


async def Aetherius_Memory_Loop(user_input, username, bot_name, vector_input, vector_monologue, output_one, response_two):
    # # Number of Messages before conversation is summarized, higher number, higher api cost. Change to 3 when using GPT 3.5 due to token usage.
    with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
    embed_size = settings['embed_size']
    conversation = list()
    conversation2 = list()
    summary = list()
    auto = list()
    payload = list()
    consolidation  = list()
    counter = 0
    counter2 = 0
    importance_score = list()
    mem_counter = 0
    with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
    length_config = int(settings['Conversation_Length'])
    conv_length = int(settings['Conversation_Length'])
    botnameupper = bot_name.upper()
    usernameupper = username.upper()
    base_path = "./Aetherius_API/Chatbot_Prompts"
    base_prompts_path = os.path.join(base_path, "Base")
    user_bot_path = os.path.join(base_path, username, bot_name)
    if not os.path.exists(user_bot_path):
        os.makedirs(user_bot_path)
    prompts_json_path = os.path.join(user_bot_path, "prompts.json")
    if not os.path.exists(prompts_json_path):
        default_prompts = {
            "main_prompt": "",
            "secondary_prompt": "",
            "greeting_prompt": ""
        }
        for filename in default_prompts:
            src = os.path.join(base_prompts_path, f"prompt_{filename}.txt")
            if os.path.isfile(src):
                with open(src, 'r') as file:
                    default_prompts[filename] = file.read()
        async with aiofiles.open(prompts_json_path, 'w') as json_file:
            await json_file.write(json.dumps(default_prompts, indent=2))
    async with aiofiles.open(prompts_json_path, 'r') as file:
        prompts = json.loads(await file.read())
    main_prompt = prompts["main_prompt"].replace('<<NAME>>', bot_name)
    secondary_prompt = prompts["secondary_prompt"]
    greeting_msg = prompts["greeting_prompt"].replace('<<NAME>>', bot_name)
#   r = sr.Recognizer()
    while True:
        # # Get Timestamp
        a = user_input
        timestamp = time()
        timestring = timestamp_to_datetime(timestamp)
        counter += 1
        conversation.clear()
        conversation.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: You are a sub-module of {bot_name}, an AI entity designed for autonomous interaction. Your specialized function is to distill each conversation with {username} into a single, short and concise narrative sentence. This sentence should serve as {bot_name}'s autobiographical memory of the conversation, capturing the most significant events, context, and emotions experienced by either {bot_name} or {username}. Note that 'autobiographical memory' refers to a detailed recollection of a specific event, often including emotions and sensory experiences. Your task is to focus on preserving the most crucial elements without omitting key context or feelings. After that, please print the user's message followed by your response. [/INST]"})
        conversation.append({'role': 'user', 'content': f"USER: {a}\n"})
        conversation.append({'role': 'user', 'content': f"{botnameupper}'s INNER MONOLOGUE: {output_one}\n"})
        conversation.append({'role': 'user', 'content': f"{botnameupper}'S FINAL RESPONSE: {response_two}"})
        conversation.append({'role': 'assistant', 'content': f"[INST] Please now generate an autobiographical memory for {bot_name}. [/INST] THIRD-PERSON AUTOBIOGRAPHICAL MEMORY: "})
        prompt = ''.join([message_dict['content'] for message_dict in conversation])
        conv_summary = await oobabooga_episodic_memory(prompt, username, bot_name)
        sentences = re.split(r'(?<=[.!?])\s+', conv_summary)
        if sentences and not re.search(r'[.!?]$', sentences[-1]):
            sentences.pop()
        conv_summary = ' '.join(sentences)
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
        episodic_msg = f'{timestring} - {conv_summary}'
        vector1 = embeddings(episodic_msg)
        unique_id = str(uuid4())
        importance_score.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: You are a sub-module of {bot_name}, an autonomous AI entity. Your function is to process a given memory and rate its importance to personal development and/or its ability to impact the greater world.  You are to give the rating on a scale of 1-100.\n"})
        importance_score.append({'role': 'system', 'content': f"{botnameupper}'S MAIN PROMPT: {main_prompt}\n"})
        importance_score.append({'role': 'system', 'content': f"{botnameupper}'S SECONDARY PROMPT: {secondary_prompt}\n"})
        importance_score.append({'role': 'system', 'content': f"{botnameupper}'S GREETING MESSAGE: {greeting_msg}\n"})
        importance_score.append({'role': 'system', 'content': f"MEMORY TO RATE: {episodic_msg}\n"})
        importance_score.append({'role': 'system', 'content': f"{usernameupper}: Please now rate the given memory on a scale of 1-100. Only print the numerical rating as a digit. [/INST]"})
        importance_score.append({'role': 'system', 'content': f"{botnameupper}: Sure thing! Here's the memory rated on a scale of 1-100:\nRating: "})
        prompt = ''.join([message_dict['content'] for message_dict in importance_score])
        score = 75
        importance_score.clear()
        metadata = {
            'bot': bot_name,
            'user': username,
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
        collection_name = f"Flash_Counter_Bot_{bot_name}"
        # Create the collection only if it doesn't exist
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
            'user': username,
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
        collection_name = f"Flash_Counter_Bot_{bot_name}"
        collection_info = client.get_collection(collection_name=collection_name)
        if collection_info.vectors_count > 8:
    #    if collection_info.vectors_count > 1:
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
                                match=models.MatchValue(value=f"{username}"),
                            ),
                        ]
                    ),
                    limit=5
                )
                flash_db = [hit.payload['message'] for hit in hits]
            except Exception as e:
                if "Not found: Collection" in str(e):
                    print("Collection does not exist.")
                else:
                    print(f"An unexpected error occurred: {str(e)}")
                
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
                                match=models.MatchValue(value=f"{username}"),
                            ),

                        ]
                    ),
                    limit=8
                )
                flash_db1 = [hit.payload['message'] for hit in hits]
            except Exception as e:
                if "Not found: Collection" in str(e):
                    print("Collection does not exist.")
                else:
                    print(f"An unexpected error occurred: {str(e)}")
            # # Generate Flashbulb Memory
            consolidation.append({'role': 'system', 'content': "Main System Prompt: As a data extractor, your role is to read the provided episodic memories and emotional reactions. Extract emotional information corresponding to each memory and then combine these to form flashbulb memories. Only include memories strongly tied to emotions. Format the flashbulb memories as bullet points using the template: •[flashbulb memory]. Then, create and present the final list of flashbulb memories.\n"})
            consolidation.append({'role': 'user', 'content': f"EMOTIONAL REACTIONS: {flash_db}\nEPISODIC MEMORIES: {flash_db1}[/INST]"})
      #      consolidation.append({'role': 'assistant', 'content': ""})
            consolidation.append({'role': 'user', 'content': "[INST]FORMAT: Use the format: •{Flashbulb Memory}[/INST]"})
            consolidation.append({'role': 'assistant', 'content': f"{botnameupper}: I will now combine the extracted data to form flashbulb memories in bullet point format, combining associated data. I will only include memories with a strong emotion attached: "})
            prompt = ''.join([message_dict['content'] for message_dict in consolidation])
            flash_response = await oobabooga_flash_memory(prompt, username, bot_name)
        #    memories = results
            segments = re.split(r'•|\n\s*\n', flash_response)
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
                    flash_mem = f'{timestring} - {segment}'
                    importance_score.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: You are a sub-module of {bot_name}, an autonomous AI entity. Your function is to process a given memory and rate its importance to personal development and/or its ability to impact the greater world.  You are to give the rating on a scale of 1-100.\n"})
                    importance_score.append({'role': 'system', 'content': f"{botnameupper}'S MAIN PROMPT: {main_prompt}\n"})
                    importance_score.append({'role': 'system', 'content': f"{botnameupper}'S SECONDARY PROMPT: {secondary_prompt}\n"})
                    importance_score.append({'role': 'system', 'content': f"{botnameupper}'S GREETING MESSAGE: {greeting_msg}\n"})
                    importance_score.append({'role': 'system', 'content': f"MEMORY TO RATE: {flash_mem}\n"})
                    importance_score.append({'role': 'system', 'content': f"{usernameupper}: Please now rate the given memory on a scale of 1-100. Only print the numerical rating as a digit. [/INST]"})
                    importance_score.append({'role': 'system', 'content': f"{botnameupper}: Sure thing! Here's the memory rated on a scale of 1-100:\nRating: "})
                    prompt = ''.join([message_dict['content'] for message_dict in importance_score])
                    score = 75
                    # print(score)
                    importance_score.clear()
                    metadata = {
                        'bot': bot_name,
                        'user': username,
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
                collection_name=f"Flash_Counter_Bot_{bot_name}",
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="user",
                                match=models.MatchValue(value=f"{username}"),
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
        #    if collection_info.vectors_count > 5:
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
                                    match=MatchValue(value=f"{username}")
                                )
                            ]
                        ),
                        limit=20
                    )
                    memory_consol_db = [hit.payload['message'] for hit in hits]
               #     print(memory_consol_db)
                except Exception as e:
                    if "Not found: Collection" in str(e):
                        print("Collection does not exist.")
                    else:
                        print(f"An unexpected error occurred: {str(e)}")
                except Exception as e:
                    if "Not found: Collection" in str(e):
                        print("Collection does not exist.")
                    else:
                        print(f"An unexpected error occurred: {str(e)}")

                consolidation.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: {main_prompt}\n\n"})
                consolidation.append({'role': 'assistant', 'content': f"LOG: {memory_consol_db}\n\nSYSTEM: Read the Log and combine the similar topics from the given short term memories into a bullet point list to serve as {bot_name}'s long term memories. Each summary should contain the entire context of the memory. Follow the format •[memory] [/INST] {botnameupper}: Sure, here is the list of consolidated memories: "})
                prompt = ''.join([message_dict['content'] for message_dict in consolidation])
                memory_consol = await oobabooga_consolidation_memory(prompt, username, bot_name)
            #    print(memory_consol)
            #    print('\n-----------------------\n')
                segments = re.split(r'•|\n\s*\n', memory_consol)
                for segment in segments:
                    if segment.strip() == '':  # This condition checks for blank segments
                        continue  # This condition checks for blank lines
                    else:
             #           print(segment)
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
                        importance_score.append({'role': 'system', 'content': f"{usernameupper}: Please now rate the given memory on a scale of 1-100. Only print the numerical rating as a digit. [/INST]"})
                        importance_score.append({'role': 'system', 'content': f"{botnameupper}: Sure thing! Here's the memory rated on a scale of 1-100:\nRating: "})
                        prompt = ''.join([message_dict['content'] for message_dict in importance_score])
                        score = 75
                        # print(score)
                        importance_score.clear()
                        metadata = {
                            'bot': bot_name,
                            'user': username,
                            'time': timestamp,
                            'rating': score,
                            'message': segment,
                            'timestring': timestring,
                            'uuid': unique_id,
                            'memory_type': 'Explicit_Long_Term',
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
                                    match=models.MatchValue(value=f"{username}"),
                                ),
                            ],
                        )
                    ),
                ) 
                
                        # Define the collection name
                collection_name = f'Consol_Counter_Bot_{bot_name}_{username}'
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
                metadata = {
                    'bot': bot_name,
                    'user': username,
                    'time': timestamp,
                    'message': segment,
                    'timestring': timestring,
                    'uuid': unique_id,
                    'memory_type': 'Consol_Counter',
                }
                client.upsert(collection_name=f'Consol_Counter_Bot_{bot_name}_{username}',
                    points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])   
                payload.clear()
                consolidation.clear()
                
                
                # # Implicit Short Term Memory Consolidation based on amount of vectors in namespace
                collection_name = f"Consol_Counter_Bot_{bot_name}_{username}"
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
                                        match=MatchValue(value=f"{username}")
                                    )
                                ]
                            ),
                            limit=25
                        )
                        memory_consol_db2 = [hit.payload['message'] for hit in hits]
                    except Exception as e:
                        if "Not found: Collection" in str(e):
                            print("Collection does not exist.")
                        else:
                            print(f"An unexpected error occurred: {str(e)}") 

                    consolidation.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: {main_prompt}\n\n"})
                    consolidation.append({'role': 'assistant', 'content': f"LOG: {memory_consol_db2}\n\nSYSTEM:  Read the Log and combine the similar topics from the given short term memories into a bullet point list to serve as {bot_name}'s long term memories. Each summary should contain the entire context of the memory. Follow the format: •[memory] [/INST] {bot_name}: Sure, here is the list of consolidated memories: "})
                    prompt = ''.join([message_dict['content'] for message_dict in consolidation])
                    memory_consol2 = await oobabooga_consolidation_memory(prompt, username, bot_name)
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
                                        match=MatchValue(value=f"{username}"),
                                    ),
                                ]
                            ),
                            limit=8
                        )
                        memory_consol_db3 = [hit.payload['message'] for hit in hits]
                    except Exception as e:
                        memory_consol_db3 = 'Failed Lookup'
                        if "Not found: Collection" in str(e):
                            print("Collection does not exist.")
                        else:
                            print(f"An unexpected error occurred: {str(e)}")
                    consolidation.append({'role': 'system', 'content': f"{main_prompt}\n\n"})
                    consolidation.append({'role': 'system', 'content': f"IMPLICIT LONG TERM MEMORY: {memory_consol_db3}\n\nIMPLICIT SHORT TERM MEMORY: {memory_consol_db2}\n\nRESPONSE: Compare your short-term memories and the given Long Term Memories, then, remove any duplicate information from your Implicit Short Term memory that is already found in your Long Term Memory. After this is done, consolidate similar topics into a new set of memories. Each summary should contain the entire context of the memory. Use the following format: •[memory] [/INST] {botnameupper}: Sure, here is the list of consolidated memories: "})
                    prompt = ''.join([message_dict['content'] for message_dict in consolidation])
                    memory_consol3 = await oobabooga_consolidation_memory(prompt, username, bot_name)
                    segments = re.split(r'•|\n\s*\n', memory_consol3)
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
                            importance_score.append({'role': 'system', 'content': f"{usernameupper}: Please now rate the given memory on a scale of 1-100. Only print the numerical rating as a digit. [/INST]"})
                            importance_score.append({'role': 'system', 'content': f"{botnameupper}: Sure thing! Here's the memory rated on a scale of 1-100:\nRating: "})
                            prompt = ''.join([message_dict['content'] for message_dict in importance_score])
                            score = 75
                            # print(score)
                            importance_score.clear()
                            metadata = {
                                'bot': bot_name,
                                'user': username,
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
                                        match=models.MatchValue(value=f"{username}"),
                                    ),
                                ],
                            )
                        ),
                    )
                else:   
                    pass
                    
                    
            # # Implicit Associative Processing/Pruning based on amount of vectors in namespace   
                collection_name = f"Consol_Counter_Bot_{bot_name}_{username}"
                collection_info = client.get_collection(collection_name=collection_name)
                if collection_info.vectors_count % 4 == 0:
            #    if collection_info.vectors_count % 2 == 0:
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
                                        match=MatchValue(value=f"{username}"),
                                    ),
                                ]
                            ),
                            limit=10
                        )
                        memory_consol_db4 = [hit.payload['message'] for hit in hits]
                    except Exception as e:
                        if "Not found: Collection" in str(e):
                            print("Collection does not exist.")
                        else:
                            print(f"An unexpected error occurred: {str(e)}")

                    ids_to_delete = [m.id for m in hits]
           #         consolidation.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: {main_prompt}\n\n"})
                    consolidation.append({'role': 'assistant', 'content': f"LOG: {memory_consol_db4}\n\nSYSTEM: Read the Log and consolidate the different memories into executive summaries in a process allegorical to associative memory processing. Each summary should contain the entire context of the memory. Follow the bullet point format: •[memory] [/INST] {botnameupper}: Sure, here is the list of consolidated memories: "})
                    prompt = ''.join([message_dict['content'] for message_dict in consolidation])
                    memory_consol4 = await oobabooga_associative_memory(prompt, username, bot_name)
            #        print(memory_consol4)
            #        print('--------')
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
                            importance_score.append({'role': 'system', 'content': f"{usernameupper}: Please now rate the given memory on a scale of 1-100. Only print the numerical rating as a digit. [/INST]"})
                            importance_score.append({'role': 'system', 'content': f"{botnameupper}: Sure thing! Here's the memory rated on a scale of 1-100:\nRating: "})
                            prompt = ''.join([message_dict['content'] for message_dict in importance_score])
                            score = 75
                            # print(score)
                            importance_score.clear()
                            metadata = {
                                'bot': bot_name,
                                'user': username,
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
                collection_name = f"Consol_Counter_Bot_{bot_name}_{username}"
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
                                        match=MatchValue(value=f"{username}"),
                                    ),
                                ]
                            ),
                            limit=5
                        )
                        consol_search = [hit.payload['message'] for hit in hits]
                    except Exception as e:
                        if "Not found: Collection" in str(e):
                            print("Collection does not exist.")
                        else:
                            print(f"An unexpected error occurred: {str(e)}")

                    consolidation.append({'role': 'user', 'content': f"{bot_name}'s Memories: {consol_search}[/INST]\n\n"})
                    consolidation.append({'role': 'assistant', 'content': "RESPONSE: Semantic Search Query: "})
                    prompt = ''.join([message_dict['content'] for message_dict in consolidation])
                    consol_search_term = await oobabooga_250(prompt, username, bot_name)
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
                                        match=MatchValue(value=f"{username}"),
                                    ),
                                ]
                            ),
                            limit=5
                        )
                        memory_consol_db2 = [hit.payload['message'] for hit in hits]
                    except Exception as e:
                        if "Not found: Collection" in str(e):
                            print("Collection does not exist.")
                        else:
                            print(f"An unexpected error occurred: {str(e)}")

                    #Find solution for this
                    ids_to_delete2 = [m.id for m in hits]
                    consolidation.clear()
            #        consolidation.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: {main_prompt}\n\n"})
                    consolidation.append({'role': 'assistant', 'content': f"LOG: {memory_consol_db2}\n\nSYSTEM: Read the Log and consolidate the different memories in a process allegorical to associative memory processing. Each summary should contain full context.\n\nFORMAT: Follow the bullet point format: •[memory] [/INST] {botnameupper}: Sure, here is the list of consolidated memories: "})
                    prompt = ''.join([message_dict['content'] for message_dict in consolidation])
                    memory_consol5 = await oobabooga_associative_memory(prompt, username, bot_name)
                #    print(memory_consol5)
                #    print('\n-----------------------\n')
                #    memories = results
                    segments = re.split(r'•|\n\s*\n', memory_consol5)
                    for segment in segments:
                        if segment.strip() == '':  # This condition checks for blank segments
                            continue  # This condition checks for blank lines
                        else:
                   #         print(segment)
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
                            importance_score.append({'role': 'system', 'content': f"{usernameupper}: Please now rate the given memory on a scale of 1-100. Only print the numerical rating as a digit. [/INST]"})
                            importance_score.append({'role': 'system', 'content': f"{botnameupper}: Sure thing! Here's the memory rated on a scale of 1-100:\nRating: "})
                            prompt = ''.join([message_dict['content'] for message_dict in importance_score])
                            score = 75
                            # print(score)
                            importance_score.clear()
                            metadata = {
                                'bot': bot_name,
                                'user': username,
                                'time': timestamp,
                                'rating': score,
                                'message': segment,
                                'timestring': timestring,
                                'uuid': unique_id,
                                'memory_type': 'Explicit_Long_Term',
                            }
                            client.upsert(collection_name=collection_name,
                                                 points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])   
                            payload.clear()
                    try:
                        client.delete(
                            collection_name=f"Bot_{bot_name}",
                            points_selector=models.PointIdsList(
                                points=ids_to_delete2,
                            ),
                        )
                    except:
                        print('Failed2')  
                    client.delete_collection(collection_name=f"Consol_Counter_Bot_{bot_name}_{username}")    
            except Exception as e:
                pass
        else:
            pass
        consolidation.clear()
        conversation2.clear()
        break





