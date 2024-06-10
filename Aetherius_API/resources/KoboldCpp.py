import sys
import os
import json
import time
import datetime as dt
from datetime import datetime
from uuid import uuid4
import requests
import shutil
from qdrant_client import QdrantClient
from qdrant_client.models import (Distance, VectorParams, PointStruct, Filter, FieldCondition, 
                                 Range, MatchValue)
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
import numpy as np
import re
import keyboard
import traceback
import asyncio
import aiofiles
import aiohttp

def open_file(filepath):
    json_file_path = './Aetherius_API/chatbot_settings.json'  # Replace with the actual path to your JSON file
    with open(json_file_path, 'r', encoding='utf-8') as f:
        settings_dict = json.load(f)
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read().strip()

def open_file_first(key):
    json_file_path = './Aetherius_API/chatbot_settings.json'  # Replace with the actual path to your JSON file
    with open(json_file_path, 'r', encoding='utf-8') as f:
        settings_dict = json.load(f)

    content = settings_dict.get(key, '')
    hosts = content.split(' ')
    return hosts[0]

def open_file_second(key):
    json_file_path = './Aetherius_API/chatbot_settings.json'  # Replace with the actual path to your JSON file
    with open(json_file_path, 'r', encoding='utf-8') as f:
        settings_dict = json.load(f)

    content = settings_dict.get(key, '')
    hosts = content.split(' ')
    if len(hosts) >= 2:
        return hosts[1]
    else:
        return hosts[0]

POSITION_FILE = './current_position.txt'

def store_position(position):
    json_file_path = './Aetherius_API/chatbot_settings.json'  # Replace with the actual path to your JSON file
    with open(json_file_path, 'r', encoding='utf-8') as f:
        settings_dict = json.load(f)

    with open(POSITION_FILE, 'w') as file:
        file.write(str(position))

def read_position():
    json_file_path = './Aetherius_API/chatbot_settings.json'  # Replace with the actual path to your JSON file
    with open(json_file_path, 'r', encoding='utf-8') as f:
        settings_dict = json.load(f)

    if not os.path.exists(POSITION_FILE) or os.path.getsize(POSITION_FILE) == 0:
        with open(POSITION_FILE, 'w') as file:
            file.write('0')
        return 0
    with open(POSITION_FILE, 'r') as file:
        position_str = file.read().strip()
        if not position_str:
            with open(POSITION_FILE, 'w') as file:
                file.write('0')
            return 0
        return int(position_str)

def get_next_host(key):
    json_file_path = './Aetherius_API/chatbot_settings.json'  # Replace with the actual path to your JSON file
    with open(json_file_path, 'r', encoding='utf-8') as f:
        settings_dict = json.load(f)

    content = settings_dict.get(key, '').strip()
    hosts = content.split(' ')
    hosts = [host for host in hosts if host]  # Remove empty strings

    if not hosts:  # Check if the hosts list is empty
        return "No hosts available"

    position = read_position()

    if position >= len(hosts) or position < 0:  # Reset position if it's out of range
        position = 0

    next_host = hosts[position]
    store_position(position + 1)
    
    return next_host

def open_file_all(key):
    json_file_path = './Aetherius_API/chatbot_settings.json'  # Replace with the actual path to your JSON file
    with open(json_file_path, 'r', encoding='utf-8') as f:
        settings_dict = json.load(f)

    content = settings_dict.get(key, '')
    hosts = content.split(' ')
    while True:
        for host in hosts:
            yield host
            
            
async def read_settings_from_json(json_file_path):
    with open(json_file_path, 'r') as file:
        settings = json.load(file)
    return settings


async def Input_Expansion_Call(prompt, username, bot_name): # Converted
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat') 
        
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "mode": "instruct",
            "instruction_template": backend_model,
            "messages": prompt,
            "max_tokens": 100,
            "temperature": 0.3,
            "top_p": 0.35,
            "top_k": 25,
            "repetition_penalty": 1.08,
            "stop_sequence": ["###"],
            "trim_stop": True
        }
    

        timeout = aiohttp.ClientTimeout(total=180)  # Increase the timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(f"{open_file_first('HOST_KoboldCpp')}/v1/chat/completions", headers=headers, json=data, ssl=False) as response:
                    if response.status == 200:
                        try:
                            response_json = await response.json()
                            assistant_message = response_json['choices'][0]['message']['content']
                            return assistant_message
                        except aiohttp.ClientPayloadError as e:
                            print(f"ClientPayloadError: {e}")
                            print("Response text:", await response.text())
                            return None
                        except ValueError:
                            print("Response content is not valid JSON:", await response.text())
                            return None
                    else:
                        print("Failed to get a valid response:", response.status)
                        return None
            except aiohttp.ClientError as e:
                print(f"ClientError: {e}")
                return None

    except Exception as e:
        traceback.print_exc()
        return None



async def Semantic_Terms_Call(prompt, username, bot_name): # Converted
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat') 
        
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "mode": "instruct",
            "instruction_template": backend_model,
            "messages": prompt,
            "max_tokens": 100,
            "temperature": 0.75,
            "top_p": 0.4,
            "top_k": 40,
            "repetition_penalty": 1.20,
            "stop_sequence": ["###"],
            "trim_stop": True
        }

        timeout = aiohttp.ClientTimeout(total=180)  # Increase the timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(f"{open_file_first('HOST_KoboldCpp')}/v1/chat/completions", headers=headers, json=data, ssl=False) as response:
                    if response.status == 200:
                        try:
                            response_json = await response.json()
                            assistant_message = response_json['choices'][0]['message']['content']
                            return assistant_message
                        except aiohttp.ClientPayloadError as e:
                            print(f"ClientPayloadError: {e}")
                            print("Response text:", await response.text())
                            return None
                        except ValueError:
                            print("Response content is not valid JSON:", await response.text())
                            return None
                    else:
                        print("Failed to get a valid response:", response.status)
                        return None
            except aiohttp.ClientError as e:
                print(f"ClientError: {e}")
                return None

    except Exception as e:
        traceback.print_exc()
        return None
        
        
        
        
async def Domain_Selection_Call(prompt, username, bot_name):
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat') 
        
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "mode": "instruct",
            "instruction_template": backend_model,
            "messages": prompt,
            "max_tokens": 100,
            "temperature": 0.2,
            "top_p": 0.2,
            "top_k": 20,
            "repetition_penalty": 1.20,
            "stop_sequence": ["###"],
            "trim_stop": True
        }

        timeout = aiohttp.ClientTimeout(total=180)  # Increase the timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(f"{open_file_first('HOST_KoboldCpp')}/v1/chat/completions", headers=headers, json=data, ssl=False) as response:
                    if response.status == 200:
                        try:
                            response_json = await response.json()
                            assistant_message = response_json['choices'][0]['message']['content']
                            return assistant_message
                        except aiohttp.ClientPayloadError as e:
                            print(f"ClientPayloadError: {e}")
                            print("Response text:", await response.text())
                            return None
                        except ValueError:
                            print("Response content is not valid JSON:", await response.text())
                            return None
                    else:
                        print("Failed to get a valid response:", response.status)
                        return None
            except aiohttp.ClientError as e:
                print(f"ClientError: {e}")
                return None

    except Exception as e:
        traceback.print_exc()
        return None  
        
        
        
        
async def Domain_Extraction_Call(prompt, username, bot_name):
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat') 
        
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "mode": "instruct",
            "instruction_template": backend_model,
            "messages": prompt,
            "max_tokens": 70,
            "temperature": 0.75,
            "top_p": 0.4,
            "top_k": 40,
            "repetition_penalty": 1.10,
            "stop_sequence": ["###"],
            "trim_stop": True
        }

        timeout = aiohttp.ClientTimeout(total=180)  # Increase the timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(f"{open_file_first('HOST_KoboldCpp')}/v1/chat/completions", headers=headers, json=data, ssl=False) as response:
                    if response.status == 200:
                        try:
                            response_json = await response.json()
                            assistant_message = response_json['choices'][0]['message']['content']
                            return assistant_message
                        except aiohttp.ClientPayloadError as e:
                            print(f"ClientPayloadError: {e}")
                            print("Response text:", await response.text())
                            return None
                        except ValueError:
                            print("Response content is not valid JSON:", await response.text())
                            return None
                    else:
                        print("Failed to get a valid response:", response.status)
                        return None
            except aiohttp.ClientError as e:
                print(f"ClientError: {e}")
                return None

    except Exception as e:
        traceback.print_exc()
        return None 



async def Inner_Monologue_Call(prompt, username, bot_name):
    json_file_path = './Aetherius_API/Generation_Settings/Oobabooga/settings.json'
    settings = await read_settings_from_json(json_file_path)
    temperature = float(settings.get("Inner_Monologue_temperature", "0.70"))
    top_p = float(settings.get("Inner_Monologue_top_p", "0.35"))
    rep_pen = float(settings.get("Inner_Monologue_rep_pen", "1.18"))
    max_tokens = int(settings.get("Inner_Monologue_max_tokens", "350"))
    top_k = int(settings.get("Inner_Monologue_top_k", "45"))
    min_tokens = int(settings.get("Inner_Monologue_min_tokens", "40"))
    
    json_file_path = './Aetherius_API/chatbot_settings.json'
    settings = await read_settings_from_json(json_file_path)
    backend_model = settings.get('Model_Backend', 'Llama_2_Chat')
    
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat') 
        
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "mode": "instruct",
            "instruction_template": backend_model,
            "messages": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "repetition_penalty": rep_pen,
            "stop_sequence": ["###"],
            "trim_stop": True
        }

        timeout = aiohttp.ClientTimeout(total=180)  # Increase the timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(f"{open_file_first('HOST_KoboldCpp')}/v1/chat/completions", headers=headers, json=data, ssl=False) as response:
                    if response.status == 200:
                        try:
                            response_json = await response.json()
                            assistant_message = response_json['choices'][0]['message']['content']
                            return assistant_message
                        except aiohttp.ClientPayloadError as e:
                            print(f"ClientPayloadError: {e}")
                            print("Response text:", await response.text())
                            return None
                        except ValueError:
                            print("Response content is not valid JSON:", await response.text())
                            return None
                    else:
                        print("Failed to get a valid response:", response.status)
                        return None
            except aiohttp.ClientError as e:
                print(f"ClientError: {e}")
                return None

    except Exception as e:
        traceback.print_exc()
        return None

    

        
        
async def Intuition_Call(prompt, username, bot_name):
    json_file_path = './Aetherius_API/Generation_Settings/Oobabooga/settings.json'
    settings = await read_settings_from_json(json_file_path)
    temperature = float(settings.get("Intuition_temperature", 0.30))
    top_p = float(settings.get("Intuition_top_p", 0.20))
    rep_pen = float(settings.get("Intuition_rep_pen", 1.25))
    max_tokens = int(settings.get("Intuition_max_tokens", 450))
    top_k = int(settings.get("Intuition_top_k", 35))
    min_tokens = int(settings.get("Intuition_min_tokens", 10))
    
    json_file_path = './Aetherius_API/chatbot_settings.json'
    settings = await read_settings_from_json(json_file_path)
    backend_model = settings.get('Model_Backend', 'Llama_2_Chat')
    
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat') 
        
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "mode": "instruct",
            "instruction_template": backend_model,
            "messages": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "repetition_penalty": rep_pen,
            "stop_sequence": ["###"],
            "trim_stop": True
        }
        timeout = aiohttp.ClientTimeout(total=180)  # Increase the timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(f"{open_file_first('HOST_KoboldCpp')}/v1/chat/completions", headers=headers, json=data, ssl=False) as response:
                    if response.status == 200:
                        try:
                            response_json = await response.json()
                            assistant_message = response_json['choices'][0]['message']['content']
                            return assistant_message
                        except aiohttp.ClientPayloadError as e:
                            print(f"ClientPayloadError: {e}")
                            print("Response text:", await response.text())
                            return None
                        except ValueError:
                            print("Response content is not valid JSON:", await response.text())
                            return None
                    else:
                        print("Failed to get a valid response:", response.status)
                        return None
            except aiohttp.ClientError as e:
                print(f"ClientError: {e}")
                return None

    except Exception as e:
        traceback.print_exc()
        return None

        
        
        
        
        
        
        
        
        
        
async def Episodic_Memory_Call(prompt, username, bot_name):
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat') 
        
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "mode": "instruct",
            "instruction_template": backend_model,
            "messages": prompt,
            "max_tokens": 300,
            "temperature": 0.8,
            "top_p": 0.1,
            "top_k": 40,
            "repetition_penalty": 1.18,
            "stop_sequence": ["###"],
            "trim_stop": True
        }

        timeout = aiohttp.ClientTimeout(total=180)  # Increase the timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(f"{open_file_first('HOST_KoboldCpp')}/v1/chat/completions", headers=headers, json=data, ssl=False) as response:
                    if response.status == 200:
                        try:
                            response_json = await response.json()
                            assistant_message = response_json['choices'][0]['message']['content']
                            return assistant_message
                        except aiohttp.ClientPayloadError as e:
                            print(f"ClientPayloadError: {e}")
                            print("Response text:", await response.text())
                            return None
                        except ValueError:
                            print("Response content is not valid JSON:", await response.text())
                            return None
                    else:
                        print("Failed to get a valid response:", response.status)
                        return None
            except aiohttp.ClientError as e:
                print(f"ClientError: {e}")
                return None

    except Exception as e:
        traceback.print_exc()
        return None
    
    
  
    
    
    
        
async def Flash_Memory_Call(prompt, username, bot_name):
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat') 
        
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "mode": "instruct",
            "instruction_template": backend_model,
            "messages": prompt,
            "max_tokens": 350,
            "temperature": 0.8,
            "top_p": 0.1,
            "top_k": 40,
            "repetition_penalty": 1.18,
            "stop_sequence": ["###", "### "],
            "trim_stop": True
        }

        timeout = aiohttp.ClientTimeout(total=180)  # Increase the timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(f"{open_file_first('HOST_KoboldCpp')}/v1/chat/completions", headers=headers, json=data, ssl=False) as response:
                    if response.status == 200:
                        try:
                            response_json = await response.json()
                            assistant_message = response_json['choices'][0]['message']['content']
                            return assistant_message
                        except aiohttp.ClientPayloadError as e:
                            print(f"ClientPayloadError: {e}")
                            print("Response text:", await response.text())
                            return None
                        except ValueError:
                            print("Response content is not valid JSON:", await response.text())
                            return None
                    else:
                        print("Failed to get a valid response:", response.status)
                        return None
            except aiohttp.ClientError as e:
                print(f"ClientError: {e}")
                return None

    except Exception as e:
        traceback.print_exc()
        return None
        
        
async def Implicit_Memory_Call(prompt, username, bot_name):
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat') 
        
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "mode": "instruct",
            "instruction_template": backend_model,
            "messages": prompt,
            "max_tokens": 350,
            "temperature": 0.8,
            "top_p": 0.6,
            "top_k": 40,
            "repetition_penalty": 1.18,
            "stop_sequence": ["###"]
        }
        timeout = aiohttp.ClientTimeout(total=180)  # Increase the timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(f"{open_file_first('HOST_KoboldCpp')}/v1/chat/completions", headers=headers, json=data, ssl=False) as response:
                    if response.status == 200:
                        try:
                            response_json = await response.json()
                            assistant_message = response_json['choices'][0]['message']['content']
                            return assistant_message
                        except aiohttp.ClientPayloadError as e:
                            print(f"ClientPayloadError: {e}")
                            print("Response text:", await response.text())
                            return None
                        except ValueError:
                            print("Response content is not valid JSON:", await response.text())
                            return None
                    else:
                        print("Failed to get a valid response:", response.status)
                        return None
            except aiohttp.ClientError as e:
                print(f"ClientError: {e}")
                return None

    except Exception as e:
        traceback.print_exc()
        return None
        
        
        
async def Explicit_Memory_Call(prompt, username, bot_name):
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat') 
        
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "mode": "instruct",
            "instruction_template": backend_model,
            "messages": prompt,
            "max_tokens": 350,
            "temperature": 0.8,
            "top_p": 0.6,
            "top_k": 40,
            "repetition_penalty": 1.18,
            "stop_sequence": ["###"]
        }

        timeout = aiohttp.ClientTimeout(total=180)  # Increase the timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(f"{open_file_first('HOST_KoboldCpp')}/v1/chat/completions", headers=headers, json=data, ssl=False) as response:
                    if response.status == 200:
                        try:
                            response_json = await response.json()
                            assistant_message = response_json['choices'][0]['message']['content']
                            return assistant_message
                        except aiohttp.ClientPayloadError as e:
                            print(f"ClientPayloadError: {e}")
                            print("Response text:", await response.text())
                            return None
                        except ValueError:
                            print("Response content is not valid JSON:", await response.text())
                            return None
                    else:
                        print("Failed to get a valid response:", response.status)
                        return None
            except aiohttp.ClientError as e:
                print(f"ClientError: {e}")
                return None

    except Exception as e:
        traceback.print_exc()
        return None
        
        
        
async def Memory_Consolidation_Call(prompt, username, bot_name):   
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat') 
        
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "mode": "instruct",
            "instruction_template": backend_model,
            "messages": prompt,
            "max_tokens": 500,
            "temperature": 0.5,
            "top_p": 0.1,
            "top_k": 35,
            "repetition_penalty": 1.13,
            "stop_sequence": ["###"]
        }
        timeout = aiohttp.ClientTimeout(total=180)  # Increase the timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(f"{open_file_first('HOST_KoboldCpp')}/v1/chat/completions", headers=headers, json=data, ssl=False) as response:
                    if response.status == 200:
                        try:
                            response_json = await response.json()
                            assistant_message = response_json['choices'][0]['message']['content']
                            return assistant_message
                        except aiohttp.ClientPayloadError as e:
                            print(f"ClientPayloadError: {e}")
                            print("Response text:", await response.text())
                            return None
                        except ValueError:
                            print("Response content is not valid JSON:", await response.text())
                            return None
                    else:
                        print("Failed to get a valid response:", response.status)
                        return None
            except aiohttp.ClientError as e:
                print(f"ClientError: {e}")
                return None

    except Exception as e:
        traceback.print_exc()
        return None
        
        
        
        
async def Associative_Memory_Call(prompt, username, bot_name): 
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat') 
        
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "mode": "instruct",
            "instruction_template": backend_model,
            "messages": prompt,
            "max_tokens": 500,
            "temperature": 0.5,
            "top_p": 0.1,
            "top_k": 35,
            "repetition_penalty": 1.13,
            "stop_sequence": ["###"]
        }
        timeout = aiohttp.ClientTimeout(total=180)  # Increase the timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(f"{open_file_first('HOST_KoboldCpp')}/v1/chat/completions", headers=headers, json=data, ssl=False) as response:
                    if response.status == 200:
                        try:
                            response_json = await response.json()
                            assistant_message = response_json['choices'][0]['message']['content']
                            return assistant_message
                        except aiohttp.ClientPayloadError as e:
                            print(f"ClientPayloadError: {e}")
                            print("Response text:", await response.text())
                            return None
                        except ValueError:
                            print("Response content is not valid JSON:", await response.text())
                            return None
                    else:
                        print("Failed to get a valid response:", response.status)
                        return None
            except aiohttp.ClientError as e:
                print(f"ClientError: {e}")
                return None

    except Exception as e:
        traceback.print_exc()
        return None
        
        
        
        
async def Response_Call(prompt, username, bot_name):
    json_file_path = './Aetherius_API/Generation_Settings/Oobabooga/settings.json'
    settings = await read_settings_from_json(json_file_path)
    temperature = float(settings.get("Response_temperature", 0.8))
    top_p = float(settings.get("Response_top_p", 0.55))
    rep_pen = float(settings.get("Response_rep_pen", 1.18))
    max_tokens = int(settings.get("Response_max_tokens", 1500))
    top_k = int(settings.get("Response_top_k", 35))
    min_tokens = int(settings.get("Response_min_tokens", 40))
    json_file_path = './Aetherius_API/chatbot_settings.json'
    settings = await read_settings_from_json(json_file_path)
    backend_model = settings.get('Model_Backend', 'Llama_2_Chat')
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat') 
        
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "mode": "instruct",
            "instruction_template": backend_model,
            "messages": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "repetition_penalty": rep_pen,
            "stop_sequence": ["###"]
        }
        timeout = aiohttp.ClientTimeout(total=180)  # Increase the timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(f"{open_file_first('HOST_KoboldCpp')}/v1/chat/completions", headers=headers, json=data, ssl=False) as response:
                    if response.status == 200:
                        try:
                            response_json = await response.json()
                            assistant_message = response_json['choices'][0]['message']['content']
                            return assistant_message
                        except aiohttp.ClientPayloadError as e:
                            print(f"ClientPayloadError: {e}")
                            print("Response text:", await response.text())
                            return None
                        except ValueError:
                            print("Response content is not valid JSON:", await response.text())
                            return None
                    else:
                        print("Failed to get a valid response:", response.status)
                        return None
            except aiohttp.ClientError as e:
                print(f"ClientError: {e}")
                return None

    except Exception as e:
        traceback.print_exc()
        return None

        
        
        
        
async def Auto_Call(prompt, username, bot_name):    
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat') 
        
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "mode": "instruct",
            "instruction_template": backend_model,
            "messages": prompt,
            "max_tokens": 3,
            "temperature": 0.3,
            "top_p": 0.3,
            "top_k": 25,
            "repetition_penalty": 1.18,
            "stop_sequence": ["###"]
        }

        timeout = aiohttp.ClientTimeout(total=180)  # Increase the timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(f"{open_file_first('HOST_KoboldCpp')}/v1/chat/completions", headers=headers, json=data, ssl=False) as response:
                    if response.status == 200:
                        try:
                            response_json = await response.json()
                            assistant_message = response_json['choices'][0]['message']['content']
                            return assistant_message
                        except aiohttp.ClientPayloadError as e:
                            print(f"ClientPayloadError: {e}")
                            print("Response text:", await response.text())
                            return None
                        except ValueError:
                            print("Response content is not valid JSON:", await response.text())
                            return None
                    else:
                        print("Failed to get a valid response:", response.status)
                        return None
            except aiohttp.ClientError as e:
                print(f"ClientError: {e}")
                return None

    except Exception as e:
        traceback.print_exc()
        return None
        
        
async def Memory_Yes_No_Call(prompt, username, bot_name):
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat') 
        
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "mode": "instruct",
            "instruction_template": backend_model,
            "messages": prompt,
            "max_tokens": 10,
            "temperature": 0.4,
            "top_p": 0.1,
            "top_k": 20,
            "repetition_penalty": 1.18,
            "stop_sequence": ["###"]
        }

        timeout = aiohttp.ClientTimeout(total=180)  # Increase the timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(f"{open_file_first('HOST_KoboldCpp')}/v1/chat/completions", headers=headers, json=data, ssl=False) as response:
                    if response.status == 200:
                        try:
                            response_json = await response.json()
                            assistant_message = response_json['choices'][0]['message']['content']
                            return assistant_message
                        except aiohttp.ClientPayloadError as e:
                            print(f"ClientPayloadError: {e}")
                            print("Response text:", await response.text())
                            return None
                        except ValueError:
                            print("Response content is not valid JSON:", await response.text())
                            return None
                    else:
                        print("Failed to get a valid response:", response.status)
                        return None
            except aiohttp.ClientError as e:
                print(f"ClientError: {e}")
                return None

    except Exception as e:
        traceback.print_exc()
        return None
       

async def  Bot_Personality_Check_Call(prompt, username, bot_name):    
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat') 
        
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "mode": "instruct",
            "instruction_template": backend_model,
            "messages": prompt,
            "max_tokens": 10,
            "temperature": 0.4,
            "top_p": 0.1,
            "top_k": 20,
            "repetition_penalty": 1.18,
            "stop_sequence": ["###"]
        }

        timeout = aiohttp.ClientTimeout(total=180)  # Increase the timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(f"{open_file_first('HOST_KoboldCpp')}/v1/chat/completions", headers=headers, json=data, ssl=False) as response:
                    if response.status == 200:
                        try:
                            response_json = await response.json()
                            assistant_message = response_json['choices'][0]['message']['content']
                            return assistant_message
                        except aiohttp.ClientPayloadError as e:
                            print(f"ClientPayloadError: {e}")
                            print("Response text:", await response.text())
                            return None
                        except ValueError:
                            print("Response content is not valid JSON:", await response.text())
                            return None
                    else:
                        print("Failed to get a valid response:", response.status)
                        return None
            except aiohttp.ClientError as e:
                print(f"ClientError: {e}")
                return None

    except Exception as e:
        traceback.print_exc()
        return None
        
        
async def Bot_Personality_Generation_Call(prompt, username, bot_name):
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat') 
        
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "mode": "instruct",
            "instruction_template": backend_model,
            "messages": prompt,
            "max_tokens": 500,
            "temperature": 0.5,
            "top_p": 0.3,
            "top_k": 20,
            "repetition_penalty": 1.10,
            "stop_sequence": ["###"]
        }

        timeout = aiohttp.ClientTimeout(total=180)  # Increase the timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(f"{open_file_first('HOST_KoboldCpp')}/v1/chat/completions", headers=headers, json=data, ssl=False) as response:
                    if response.status == 200:
                        try:
                            response_json = await response.json()
                            assistant_message = response_json['choices'][0]['message']['content']
                            return assistant_message
                        except aiohttp.ClientPayloadError as e:
                            print(f"ClientPayloadError: {e}")
                            print("Response text:", await response.text())
                            return None
                        except ValueError:
                            print("Response content is not valid JSON:", await response.text())
                            return None
                    else:
                        print("Failed to get a valid response:", response.status)
                        return None
            except aiohttp.ClientError as e:
                print(f"ClientError: {e}")
                return None

    except Exception as e:
        traceback.print_exc()
        return None


async def User_Personality_Extraction_Call(prompt, username, bot_name):
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat') 
        
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "mode": "instruct",
            "instruction_template": backend_model,
            "messages": prompt,
            "max_tokens": 500,
            "temperature": 0.5,
            "top_p": 0.3,
            "top_k": 20,
            "repetition_penalty": 1.10,
            "stop_sequence": ["###"]
        }
        timeout = aiohttp.ClientTimeout(total=180)  # Increase the timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(f"{open_file_first('HOST_KoboldCpp')}/v1/chat/completions", headers=headers, json=data, ssl=False) as response:
                    if response.status == 200:
                        try:
                            response_json = await response.json()
                            assistant_message = response_json['choices'][0]['message']['content']
                            return assistant_message
                        except aiohttp.ClientPayloadError as e:
                            print(f"ClientPayloadError: {e}")
                            print("Response text:", await response.text())
                            return None
                        except ValueError:
                            print("Response content is not valid JSON:", await response.text())
                            return None
                    else:
                        print("Failed to get a valid response:", response.status)
                        return None
            except aiohttp.ClientError as e:
                print(f"ClientError: {e}")
                return None

    except Exception as e:
        traceback.print_exc()
        return None


async def User_Personality_Generation_Call(prompt, username, bot_name):
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat') 
        
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "mode": "instruct",
            "instruction_template": backend_model,
            "messages": prompt,
            "max_tokens": 500,
            "temperature": 0.5,
            "top_p": 0.3,
            "top_k": 20,
            "repetition_penalty": 1.10,
            "stop_sequence": ["###"]
        }
        timeout = aiohttp.ClientTimeout(total=180)  # Increase the timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(f"{open_file_first('HOST_KoboldCpp')}/v1/chat/completions", headers=headers, json=data, ssl=False) as response:
                    if response.status == 200:
                        try:
                            response_json = await response.json()
                            assistant_message = response_json['choices'][0]['message']['content']
                            return assistant_message
                        except aiohttp.ClientPayloadError as e:
                            print(f"ClientPayloadError: {e}")
                            print("Response text:", await response.text())
                            return None
                        except ValueError:
                            print("Response content is not valid JSON:", await response.text())
                            return None
                    else:
                        print("Failed to get a valid response:", response.status)
                        return None
            except aiohttp.ClientError as e:
                print(f"ClientError: {e}")
                return None

    except Exception as e:
        traceback.print_exc()
        return None

async def Selector_Call(prompt, username, bot_name):

    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat') 
        
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "mode": "instruct",
            "instruction_template": backend_model,
            "messages": prompt,
            "max_tokens": 10,
            "temperature": 0.4,
            "top_p": 0.1,
            "top_k": 20,
            "repetition_penalty": 1.18,
            "stop_sequence": ["###"]
        }
        timeout = aiohttp.ClientTimeout(total=180)  # Increase the timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(f"{open_file_first('HOST_KoboldCpp')}/v1/chat/completions", headers=headers, json=data, ssl=False) as response:
                    if response.status == 200:
                        try:
                            response_json = await response.json()
                            assistant_message = response_json['choices'][0]['message']['content']
                            return assistant_message
                        except aiohttp.ClientPayloadError as e:
                            print(f"ClientPayloadError: {e}")
                            print("Response text:", await response.text())
                            return None
                        except ValueError:
                            print("Response content is not valid JSON:", await response.text())
                            return None
                    else:
                        print("Failed to get a valid response:", response.status)
                        return None
            except aiohttp.ClientError as e:
                print(f"ClientError: {e}")
                return None

    except Exception as e:
        traceback.print_exc()
        return None
    
async def Tokens_250_Call(prompt, username, bot_name):
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat') 
        
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "mode": "instruct",
            "instruction_template": backend_model,
            "messages": prompt,
            "max_tokens": 250,
            "temperature": 0.8,
            "top_p": 0.2,
            "top_k": 40,
            "repetition_penalty": 1.18,
            "stop_sequence": ["###"]
        }
        timeout = aiohttp.ClientTimeout(total=180)  # Increase the timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(f"{open_file_first('HOST_KoboldCpp')}/v1/chat/completions", headers=headers, json=data, ssl=False) as response:
                    if response.status == 200:
                        try:
                            response_json = await response.json()
                            assistant_message = response_json['choices'][0]['message']['content']
                            return assistant_message
                        except aiohttp.ClientPayloadError as e:
                            print(f"ClientPayloadError: {e}")
                            print("Response text:", await response.text())
                            return None
                        except ValueError:
                            print("Response content is not valid JSON:", await response.text())
                            return None
                    else:
                        print("Failed to get a valid response:", response.status)
                        return None
            except aiohttp.ClientError as e:
                print(f"ClientError: {e}")
                return None

    except Exception as e:
        traceback.print_exc()
        return None
        
        
       
    
    
        
async def Agent_Semantic_Terms_Call(prompt, username, bot_name):
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat') 
        
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "mode": "instruct",
            "instruction_template": backend_model,
            "messages": prompt,
            "max_tokens": 100,
            "temperature": 0.8,
            "top_p": 0.2,
            "top_k": 40,
            "repetition_penalty": 1.18,
            "stop_sequence": ["###"]
        }
        timeout = aiohttp.ClientTimeout(total=180)  # Increase the timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(f"{open_file_first('HOST_KoboldCpp')}/v1/chat/completions", headers=headers, json=data, ssl=False) as response:
                    if response.status == 200:
                        try:
                            response_json = await response.json()
                            assistant_message = response_json['choices'][0]['message']['content']
                            return assistant_message
                        except aiohttp.ClientPayloadError as e:
                            print(f"ClientPayloadError: {e}")
                            print("Response text:", await response.text())
                            return None
                        except ValueError:
                            print("Response content is not valid JSON:", await response.text())
                            return None
                    else:
                        print("Failed to get a valid response:", response.status)
                        return None
            except aiohttp.ClientError as e:
                print(f"ClientError: {e}")
                return None

    except Exception as e:
        traceback.print_exc()
        return None

        
async def Agent_250_Tokens_Call(prompt, username, bot_name):
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat') 
        
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "mode": "instruct",
            "instruction_template": backend_model,
            "messages": prompt,
            "max_tokens": 250,
            "temperature": 0.8,
            "top_p": 0.2,
            "top_k": 40,
            "repetition_penalty": 1.18,
            "stop_sequence": ["###"]
        }
        timeout = aiohttp.ClientTimeout(total=180)  # Increase the timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(f"{open_file_first('HOST_KoboldCpp')}/v1/chat/completions", headers=headers, json=data, ssl=False) as response:
                    if response.status == 200:
                        try:
                            response_json = await response.json()
                            assistant_message = response_json['choices'][0]['message']['content']
                            return assistant_message
                        except aiohttp.ClientPayloadError as e:
                            print(f"ClientPayloadError: {e}")
                            print("Response text:", await response.text())
                            return None
                        except ValueError:
                            print("Response content is not valid JSON:", await response.text())
                            return None
                    else:
                        print("Failed to get a valid response:", response.status)
                        return None
            except aiohttp.ClientError as e:
                print(f"ClientError: {e}")
                return None

    except Exception as e:
        traceback.print_exc()
        return None


async def Agent_500_Tokens_Call(prompt, username, bot_name):
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat') 
        
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "mode": "instruct",
            "instruction_template": backend_model,
            "messages": prompt,
            "max_tokens": 500,
            "temperature": 0.85,
            "top_p": 0.2,
            "top_k": 40,
            "repetition_penalty": 1.18,
            "stop_sequence": ["###"]
        }
        timeout = aiohttp.ClientTimeout(total=180)  # Increase the timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(f"{open_file_first('HOST_KoboldCpp')}/v1/chat/completions", headers=headers, json=data, ssl=False) as response:
                    if response.status == 200:
                        try:
                            response_json = await response.json()
                            assistant_message = response_json['choices'][0]['message']['content']
                            return assistant_message
                        except aiohttp.ClientPayloadError as e:
                            print(f"ClientPayloadError: {e}")
                            print("Response text:", await response.text())
                            return None
                        except ValueError:
                            print("Response content is not valid JSON:", await response.text())
                            return None
                    else:
                        print("Failed to get a valid response:", response.status)
                        return None
            except aiohttp.ClientError as e:
                print(f"ClientError: {e}")
                return None

    except Exception as e:
        traceback.print_exc()
        return None
    
        
async def Agent_800_Tokens_Call(prompt, username, bot_name):
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat') 
        
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "mode": "instruct",
            "instruction_template": backend_model,
            "messages": prompt,
            "max_tokens": 800,
            "temperature": 0.85,
            "top_p": 0.2,
            "top_k": 40,
            "repetition_penalty": 1.18,
            "stop_sequence": ["###"]
        }
        timeout = aiohttp.ClientTimeout(total=180)  # Increase the timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(f"{open_file_first('HOST_KoboldCpp')}/v1/chat/completions", headers=headers, json=data, ssl=False) as response:
                    if response.status == 200:
                        try:
                            response_json = await response.json()
                            assistant_message = response_json['choices'][0]['message']['content']
                            return assistant_message
                        except aiohttp.ClientPayloadError as e:
                            print(f"ClientPayloadError: {e}")
                            print("Response text:", await response.text())
                            return None
                        except ValueError:
                            print("Response content is not valid JSON:", await response.text())
                            return None
                    else:
                        print("Failed to get a valid response:", response.status)
                        return None
            except aiohttp.ClientError as e:
                print(f"ClientError: {e}")
                return None

    except Exception as e:
        traceback.print_exc()
        return None
    
    
async def Agent_Intuition_Call(prompt, username, bot_name):
    json_file_path = './Aetherius_API/Generation_Settings/Oobabooga/settings.json'
    settings = await read_settings_from_json(json_file_path)
    temperature = float(settings.get("Intuition_temperature", 0.30))
    top_p = float(settings.get("Intuition_top_p", 0.20))
    rep_pen = float(settings.get("Intuition_rep_pen", 1.25))
    max_tokens = int(settings.get("Intuition_max_tokens", 450))
    top_k = int(settings.get("Intuition_top_k", 35))
    min_tokens = int(settings.get("Intuition_min_tokens", 10))
    
    json_file_path = './Aetherius_API/chatbot_settings.json'
    settings = await read_settings_from_json(json_file_path)
    backend_model = settings.get('Model_Backend', 'Llama_2_Chat')
    
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat') 
        
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "mode": "instruct",
            "instruction_template": backend_model,
            "messages": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "repetition_penalty": rep_pen,
            "stop_sequence": ["###"]
        }

        timeout = aiohttp.ClientTimeout(total=180)  # Increase the timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(f"{open_file_first('HOST_KoboldCpp')}/v1/chat/completions", headers=headers, json=data, ssl=False) as response:
                    if response.status == 200:
                        try:
                            response_json = await response.json()
                            assistant_message = response_json['choices'][0]['message']['content']
                            return assistant_message
                        except aiohttp.ClientPayloadError as e:
                            print(f"ClientPayloadError: {e}")
                            print("Response text:", await response.text())
                            return None
                        except ValueError:
                            print("Response content is not valid JSON:", await response.text())
                            return None
                    else:
                        print("Failed to get a valid response:", response.status)
                        return None
            except aiohttp.ClientError as e:
                print(f"ClientError: {e}")
                return None

    except Exception as e:
        traceback.print_exc()
        return None
        
        
        
async def Agent_Response_Call(prompt, username, bot_name):
    json_file_path = './Aetherius_API/Generation_Settings/Oobabooga/settings.json'
    settings = await read_settings_from_json(json_file_path)
    temperature = float(settings.get("Response_temperature", 0.8))
    top_p = float(settings.get("Response_top_p", 0.55))
    rep_pen = float(settings.get("Response_rep_pen", 1.18))
    max_tokens = int(settings.get("Response_max_tokens", 1500))
    top_k = int(settings.get("Response_top_k", 35))
    min_tokens = int(settings.get("Response_min_tokens", 40))
    json_file_path = './Aetherius_API/chatbot_settings.json'
    settings = await read_settings_from_json(json_file_path)
    backend_model = settings.get('Model_Backend', 'Llama_2_Chat')
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat') 
        
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "mode": "instruct",
            "instruction_template": backend_model,
            "messages": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "repetition_penalty": rep_pen,
            "stop_sequence": ["###"]
        }
        timeout = aiohttp.ClientTimeout(total=180)  # Increase the timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(f"{open_file_first('HOST_KoboldCpp')}/v1/chat/completions", headers=headers, json=data, ssl=False) as response:
                    if response.status == 200:
                        try:
                            response_json = await response.json()
                            assistant_message = response_json['choices'][0]['message']['content']
                            return assistant_message
                        except aiohttp.ClientPayloadError as e:
                            print(f"ClientPayloadError: {e}")
                            print("Response text:", await response.text())
                            return None
                        except ValueError:
                            print("Response content is not valid JSON:", await response.text())
                            return None
                    else:
                        print("Failed to get a valid response:", response.status)
                        return None
            except aiohttp.ClientError as e:
                print(f"ClientError: {e}")
                return None

    except Exception as e:
        traceback.print_exc()
        return None
    
    
async def Agent_Master_Tasklist_Call(prompt, username, bot_name):
    json_file_path = './Aetherius_API/Generation_Settings/Oobabooga/settings.json'
    settings = await read_settings_from_json(json_file_path)
    temperature = float(settings.get("Intuition_temperature", 0.30))
    top_p = float(settings.get("Intuition_top_p", 0.20))
    rep_pen = float(settings.get("Intuition_rep_pen", 1.25))
    max_tokens = int(settings.get("Intuition_max_tokens", 450))
    top_k = int(settings.get("Intuition_top_k", 35))
    min_tokens = int(settings.get("Intuition_min_tokens", 10))
    
    json_file_path = './Aetherius_API/chatbot_settings.json'
    settings = await read_settings_from_json(json_file_path)
    backend_model = settings.get('Model_Backend', 'Llama_2_Chat')
    
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat') 
        
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "mode": "instruct",
            "instruction_template": backend_model,
            "messages": prompt,
            "max_tokens": 500,
            "temperature": 0.5,
            "top_p": 30,
            "top_k": top_k,
            "repetition_penalty": 1.16,
            "stop_sequence": ["###"]
        }
        timeout = aiohttp.ClientTimeout(total=180)  # Increase the timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(f"{open_file_first('HOST_KoboldCpp')}/v1/chat/completions", headers=headers, json=data, ssl=False) as response:
                    if response.status == 200:
                        try:
                            response_json = await response.json()
                            assistant_message = response_json['choices'][0]['message']['content']
                            return assistant_message
                        except aiohttp.ClientPayloadError as e:
                            print(f"ClientPayloadError: {e}")
                            print("Response text:", await response.text())
                            return None
                        except ValueError:
                            print("Response content is not valid JSON:", await response.text())
                            return None
                    else:
                        print("Failed to get a valid response:", response.status)
                        return None
            except aiohttp.ClientError as e:
                print(f"ClientError: {e}")
                return None

    except Exception as e:
        traceback.print_exc()
        return None
        
        
async def Agent_Webcheck_Yes_No(prompt, username, bot_name):
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat') 
        
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "mode": "instruct",
            "instruction_template": backend_model,
            "messages": prompt,
            "max_tokens": 100,
            "temperature": 0.4,
            "top_p": 0.1,
            "top_k": 20,
            "repetition_penalty": 1.18,
            "stop_sequence": ["###"]
        }
        timeout = aiohttp.ClientTimeout(total=180)  # Increase the timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(f"{open_file_first('HOST_KoboldCpp')}/v1/chat/completions", headers=headers, json=data, ssl=False) as response:
                    if response.status == 200:
                        try:
                            response_json = await response.json()
                            assistant_message = response_json['choices'][0]['message']['content']
                            return assistant_message
                        except aiohttp.ClientPayloadError as e:
                            print(f"ClientPayloadError: {e}")
                            print("Response text:", await response.text())
                            return None
                        except ValueError:
                            print("Response content is not valid JSON:", await response.text())
                            return None
                    else:
                        print("Failed to get a valid response:", response.status)
                        return None
            except aiohttp.ClientError as e:
                print(f"ClientError: {e}")
                return None

    except Exception as e:
        traceback.print_exc()
        return None
    
async def Agent_Web_Yes_No(prompt, username, bot_name):
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat') 
        
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "mode": "instruct",
            "instruction_template": backend_model,
            "messages": prompt,
            "max_tokens": 10,
            "temperature": 0.4,
            "top_p": 0.1,
            "top_k": 20,
            "repetition_penalty": 1.18,
            "stop_sequence": ["###"]
        }
        timeout = aiohttp.ClientTimeout(total=180)  # Increase the timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(f"{open_file_first('HOST_KoboldCpp')}/v1/chat/completions", headers=headers, json=data, ssl=False) as response:
                    if response.status == 200:
                        try:
                            response_json = await response.json()
                            assistant_message = response_json['choices'][0]['message']['content']
                            return assistant_message
                        except aiohttp.ClientPayloadError as e:
                            print(f"ClientPayloadError: {e}")
                            print("Response text:", await response.text())
                            return None
                        except ValueError:
                            print("Response content is not valid JSON:", await response.text())
                            return None
                    else:
                        print("Failed to get a valid response:", response.status)
                        return None
            except aiohttp.ClientError as e:
                print(f"ClientError: {e}")
                return None

    except Exception as e:
        traceback.print_exc()
        return None
        
    
async def Agent_Line_Response_Call(prompt, username, bot_name):
    json_file_path = './Aetherius_API/Generation_Settings/Oobabooga/settings.json'
    settings = await read_settings_from_json(json_file_path)
    temperature = float(settings.get("Response_temperature", 0.8))
    top_p = float(settings.get("Response_top_p", 0.55))
    rep_pen = float(settings.get("Response_rep_pen", 1.18))
    max_tokens = int(settings.get("Response_max_tokens", 1500))
    top_k = int(settings.get("Response_top_k", 35))
    min_tokens = int(settings.get("Response_min_tokens", 40))
    json_file_path = './Aetherius_API/chatbot_settings.json'
    settings = await read_settings_from_json(json_file_path)
    backend_model = settings.get('Model_Backend', 'Llama_2_Chat')
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat') 
        
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "mode": "instruct",
            "instruction_template": backend_model,
            "messages": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "repetition_penalty": rep_pen,
            "stop_sequence": ["###"]
        }
        timeout = aiohttp.ClientTimeout(total=180)  # Increase the timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(f"{open_file_first('HOST_KoboldCpp')}/v1/chat/completions", headers=headers, json=data, ssl=False) as response:
                    if response.status == 200:
                        try:
                            response_json = await response.json()
                            assistant_message = response_json['choices'][0]['message']['content']
                            return assistant_message
                        except aiohttp.ClientPayloadError as e:
                            print(f"ClientPayloadError: {e}")
                            print("Response text:", await response.text())
                            return None
                        except ValueError:
                            print("Response content is not valid JSON:", await response.text())
                            return None
                    else:
                        print("Failed to get a valid response:", response.status)
                        return None
            except aiohttp.ClientError as e:
                print(f"ClientError: {e}")
                return None

    except Exception as e:
        traceback.print_exc()
        return None

    
async def Agent_Category_Reassign_Call(host, prompt, username, bot_name):
    json_file_path = './Aetherius_API/Generation_Settings/Oobabooga/settings.json'
    settings = await read_settings_from_json(json_file_path)
    temperature = float(settings.get("Response_temperature", 0.8))
    top_p = float(settings.get("Response_top_p", 0.55))
    rep_pen = float(settings.get("Response_rep_pen", 1.18))
    max_tokens = int(settings.get("Response_max_tokens", 1500))
    top_k = int(settings.get("Response_top_k", 35))
    min_tokens = int(settings.get("Response_min_tokens", 40))
    json_file_path = './Aetherius_API/chatbot_settings.json'
    settings = await read_settings_from_json(json_file_path)
    backend_model = settings.get('Model_Backend', 'Llama_2_Chat')
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat') 
        
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "mode": "instruct",
            "instruction_template": backend_model,
            "messages": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "repetition_penalty": rep_pen,
            "stop_sequence": ["###"]
        }
 
        timeout = aiohttp.ClientTimeout(total=180)  # Increase the timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(f"{host}/v1/chat/completions", headers=headers, json=data, ssl=False) as response:
                if response.status == 200:
                    try:
                        response_json = await response.json()
                        assistant_message = response_json['choices'][0]['message']['content']
                        return assistant_message
                    except aiohttp.ClientPayloadError as e:
                        print(f"ClientPayloadError: {e}")
                        return None
                    except ValueError:
                        print("Response content is not valid JSON:", await response.text())
                        return None
                else:
                    print(f"Failed to get a valid response: {response.status}")
                    return None

    except Exception as e:
        traceback.print_exc()
        return None
    
    
   


async def Agent_Process_Line_Response_Call(host, prompt, username, bot_name):
    json_file_path = './Aetherius_API/Generation_Settings/Oobabooga/settings.json'
    settings = await read_settings_from_json(json_file_path)
    temperature = float(settings.get("Response_temperature", 0.8))
    top_p = float(settings.get("Response_top_p", 0.55))
    rep_pen = float(settings.get("Response_rep_pen", 1.18))
    max_tokens = int(settings.get("Response_max_tokens", 1500))
    top_k = int(settings.get("Response_top_k", 35))
    min_tokens = int(settings.get("Response_min_tokens", 40))
    json_file_path = './Aetherius_API/chatbot_settings.json'
    settings = await read_settings_from_json(json_file_path)
    backend_model = settings.get('Model_Backend', 'Llama_2_Chat')
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat') 
        
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "mode": "instruct",
            "instruction_template": backend_model,
            "messages": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "repetition_penalty": rep_pen,
            "stop_sequence": ["###"]
        }
 
        timeout = aiohttp.ClientTimeout(total=180)  # Increase the timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(f"{host}/v1/chat/completions", headers=headers, json=data, ssl=False) as response:
                if response.status == 200:
                    try:
                        response_json = await response.json()
                        assistant_message = response_json['choices'][0]['message']['content']
                        return assistant_message
                    except aiohttp.ClientPayloadError as e:
                        print(f"ClientPayloadError: {e}")
                        return None
                    except ValueError:
                        print("Response content is not valid JSON:", await response.text())
                        return None
                else:
                    print(f"Failed to get a valid response: {response.status}")
                    return None

    except Exception as e:
        traceback.print_exc()
        return None
        
        
    
async def Agent_Process_Line_Response_2_Call(host, prompt, username, bot_name):
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat') 
        
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "mode": "instruct",
            "instruction_template": backend_model,
            "messages": prompt,
            "max_tokens": 800,
            "temperature": 0.5,
            "top_p": 0.3,
            "top_k": 20,
            "repetition_penalty": 1.18,
            "stop_sequence": ["###"]
        }
 
        timeout = aiohttp.ClientTimeout(total=180)  # Increase the timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(f"{host}/v1/chat/completions", headers=headers, json=data, ssl=False) as response:
                if response.status == 200:
                    try:
                        response_json = await response.json()
                        assistant_message = response_json['choices'][0]['message']['content']
                        return assistant_message
                    except aiohttp.ClientPayloadError as e:
                        print(f"ClientPayloadError: {e}")
                        return None
                    except ValueError:
                        print("Response content is not valid JSON:", await response.text())
                        return None
                else:
                    print(f"Failed to get a valid response: {response.status}")
                    return None

    except Exception as e:
        traceback.print_exc()
        return None
    
    
async def Agent_Memory_DB_Check_Call(host, prompt, username, bot_name):
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat') 
        
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "mode": "instruct",
            "instruction_template": backend_model,
            "messages": prompt,
            "max_tokens": 10,
            "temperature": 0.4,
            "top_p": 0.25,
            "top_k": 20,
            "repetition_penalty": 1.15,
            "stop_sequence": ["###"]
        }
 
        timeout = aiohttp.ClientTimeout(total=180)  # Increase the timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(f"{host}/v1/chat/completions", headers=headers, json=data, ssl=False) as response:
                if response.status == 200:
                    try:
                        response_json = await response.json()
                        assistant_message = response_json['choices'][0]['message']['content']
                        return assistant_message
                    except aiohttp.ClientPayloadError as e:
                        print(f"ClientPayloadError: {e}")
                        return None
                    except ValueError:
                        print("Response content is not valid JSON:", await response.text())
                        return None
                else:
                    print(f"Failed to get a valid response: {response.status}")
                    return None

    except Exception as e:
        traceback.print_exc()
        return None
        
        
    
async def Webscrape_Call(host, prompt, username, bot_name):
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat') 
        
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "mode": "instruct",
            "instruction_template": backend_model,
            "messages": prompt,
            "max_tokens": 600,
            "temperature": 0.4,
            "top_p": 0.1,
            "top_k": 35,
            "repetition_penalty": 1.08,
            "stop_sequence": ["###"]
        }
 
        timeout = aiohttp.ClientTimeout(total=180)  # Increase the timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(f"{host}/v1/chat/completions", headers=headers, json=data, ssl=False) as response:
                if response.status == 200:
                    try:
                        response_json = await response.json()
                        assistant_message = response_json['choices'][0]['message']['content']
                        return assistant_message
                    except aiohttp.ClientPayloadError as e:
                        print(f"ClientPayloadError: {e}")
                        return None
                    except ValueError:
                        print("Response content is not valid JSON:", await response.text())
                        return None
                else:
                    print(f"Failed to get a valid response: {response.status}")
                    return None

    except Exception as e:
        traceback.print_exc()
        return None
    
async def Google_Rephrase_Call(host, prompt, username, bot_name):
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat') 
        
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "mode": "instruct",
            "instruction_template": backend_model,
            "messages": prompt,
            "max_tokens": 100,
            "temperature": 0.6,
            "top_p": 0.5,
            "top_k": 20,
            "repetition_penalty": 1.15,
            "stop_sequence": ["###"]
        }
 
        timeout = aiohttp.ClientTimeout(total=180)  # Increase the timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(f"{host}/v1/chat/completions", headers=headers, json=data, ssl=False) as response:
                if response.status == 200:
                    try:
                        response_json = await response.json()
                        assistant_message = response_json['choices'][0]['message']['content']
                        return assistant_message
                    except aiohttp.ClientPayloadError as e:
                        print(f"ClientPayloadError: {e}")
                        return None
                    except ValueError:
                        print("Response content is not valid JSON:", await response.text())
                        return None
                else:
                    print(f"Failed to get a valid response: {response.status}")
                    return None

    except Exception as e:
        traceback.print_exc()
        return None

    
async def File_Processor_Call(host, prompt, username, bot_name):
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat') 
        
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "mode": "instruct",
            "instruction_template": backend_model,
            "messages": prompt,
            "max_tokens": 600,
            "temperature": 0.85,
            "top_p": 0.2,
            "top_k": 40,
            "repetition_penalty": 1.10,
            "stop_sequence": ["###"],
            "trim_stop": True
        }
 
        timeout = aiohttp.ClientTimeout(total=180)  # Increase the timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(f"{host}/v1/chat/completions", headers=headers, json=data, ssl=False) as response:
                if response.status == 200:
                    try:
                        response_json = await response.json()
                        assistant_message = response_json['choices'][0]['message']['content']
                        return assistant_message
                    except aiohttp.ClientPayloadError as e:
                        print(f"ClientPayloadError: {e}")
                        return None
                    except ValueError:
                        print("Response content is not valid JSON:", await response.text())
                        return None
                else:
                    print(f"Failed to get a valid response: {response.status}")
                    return None

    except Exception as e:
        traceback.print_exc()
        return None

        
        
        
   
        