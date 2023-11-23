import sys
import os
import json
import time
from time import time, sleep
import datetime
from uuid import uuid4
import importlib.util
from sentence_transformers import SentenceTransformer
import shutil
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, Range
#from qdrant_client.http.models import Batch 
from qdrant_client.http import models
import numpy as np
import re
import requests
import html
import random
import aiohttp
import aiofiles
import asyncio

# For a locally hosted Oobabooga Client use "http://localhost:5000/api"
# For a Google Colab hosted Oobabooga Client use the given Public Non-Streaming Url:



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
            


async def Semantic_Terms_Call(prompt, username, bot_name):
    data = {
        "LLM_Template": "Llama_2_Chat_No_End_Token",
        "Username": username,
        "Bot_Name": bot_name,
        "system_prompt": "You are a search query coordinator. Your role is to interpret the original user query and generate 2-4 synonymous search terms that will guide the exploration of the chatbot's memory database. Each alternative term should reflect the essence of the user's initial search input. Please list your results using bullet point format. Only print your response using the format: •<search term>",
        "prompt": prompt,
        "max_new_tokens": 100,
        "temperature": 0.75,
        "top_p": 0.4,
        "top_k": 40,
        "repetition_penalty": 1.20
    }
    
    

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_first('HOST_AetherNode')}/generate-text/", json=data) as post_response: # POST request to generate text
            if post_response.status == 200:
                post_data = await post_response.json()
                request_id = post_data['request_id']
                # print(f"Request ID: {request_id}")
                max_attempts = 10
                attempts = 0
                delay_seconds = 5  # Delay between each polling attempt
                while attempts < max_attempts:
                    async with session.get(f"{open_file_first('HOST_AetherNode')}/retrieve-text/{request_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            if "generated_text" in get_data:
                                return html.unescape(get_data["generated_text"])
                            await asyncio.sleep(delay_seconds) # If the result is not ready, wait before the next attempt
                        else:
                            return "Failed to retrieve the result."
                    attempts += 1
                return "Max polling attempts reached. Please try again later."
            else:
                return f"Failed to submit the prompt: {post_response.status}"
        
        
async def Domain_Selection_Call(prompt, username, bot_name):
    data = {
        "LLM_Template": "Llama_2_Chat_No_End_Token",
        "Username": username,
        "Bot_Name": bot_name,
        "system_prompt": "You are a Knowledge Domain Selector. Your role is to identify the most relevant knowledge domain based on the user's question. Choose only from the provided list and do not create or use any domains outside of it. Your response should be limited to naming the single chosen knowledge domain from the list, do not include anything but the knowledge domain.",
        "prompt": prompt,
        "max_new_tokens": 30,
        "temperature": 0.2,
        "top_p": 0.2,
        "top_k": 20,
        "repetition_penalty": 1.15
    }


    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_first('HOST_AetherNode')}/generate-text/", json=data) as post_response: # POST request to generate text
            if post_response.status == 200:
                post_data = await post_response.json()
                request_id = post_data['request_id']
                # print(f"Request ID: {request_id}")
                max_attempts = 10
                attempts = 0
                delay_seconds = 5  # Delay between each polling attempt
                while attempts < max_attempts:
                    async with session.get(f"{open_file_first('HOST_AetherNode')}/retrieve-text/{request_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            if "generated_text" in get_data:
                                return html.unescape(get_data["generated_text"])
                            await asyncio.sleep(delay_seconds) # If the result is not ready, wait before the next attempt
                        else:
                            return "Failed to retrieve the result."
                    attempts += 1
                return "Max polling attempts reached. Please try again later."
            else:
                return f"Failed to submit the prompt: {post_response.status}"
        
        
async def Domain_Extraction_Call(prompt, username, bot_name):
    data = {
        "LLM_Template": "Llama_2_Chat",
        "Username": username,
        "Bot_Name": bot_name,
        "system_prompt": "You are a knowledge domain extractor.  Your task is to analyze the given input, then extract the single most salient generalized knowledge domain representative of the input.  Your response should be a single word.",
        "prompt": prompt,
        "max_new_tokens": 100,
        "temperature": 0.75,
        "top_p": 0.4,
        "top_k": 40,
        "repetition_penalty": 1.10
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_first('HOST_AetherNode')}/generate-text/", json=data) as post_response: # POST request to generate text
            if post_response.status == 200:
                post_data = await post_response.json()
                request_id = post_data['request_id']
                # print(f"Request ID: {request_id}")
                max_attempts = 10
                attempts = 0
                delay_seconds = 5  # Delay between each polling attempt
                while attempts < max_attempts:
                    async with session.get(f"{open_file_first('HOST_AetherNode')}/retrieve-text/{request_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            if "generated_text" in get_data:
                                return html.unescape(get_data["generated_text"])
                            await asyncio.sleep(delay_seconds) # If the result is not ready, wait before the next attempt
                        else:
                            return "Failed to retrieve the result."
                    attempts += 1
                return "Max polling attempts reached. Please try again later."
            else:
                return f"Failed to submit the prompt: {post_response.status}"
        
        
async def Input_Expansion_Call(prompt, username, bot_name):
    data = {
        "LLM_Template": "Llama_2_Chat",
        "Username": username,
        "Bot_Name": bot_name,
        "system_prompt": "You are a task rephraser. Your primary task is to rephrase the user's input in a way that ensures it contains the full context needed to know what is asked. Please return the rephrased version of the user’s most recent input.",
        "prompt": prompt,
        "max_new_tokens": 100,
        "temperature": 0.3,
        "top_p": 0.35,
        "top_k": 25,
        "repetition_penalty": 1.08
    }
    

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_first('HOST_AetherNode')}/generate-text/", json=data) as post_response: # POST request to generate text
            if post_response.status == 200:
                post_data = await post_response.json()
                request_id = post_data['request_id']
                # print(f"Request ID: {request_id}")
                max_attempts = 10
                attempts = 0
                delay_seconds = 5  # Delay between each polling attempt
                while attempts < max_attempts:
                    async with session.get(f"{open_file_first('HOST_AetherNode')}/retrieve-text/{request_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            if "generated_text" in get_data:
                                return html.unescape(get_data["generated_text"])
                            await asyncio.sleep(delay_seconds) # If the result is not ready, wait before the next attempt
                        else:
                            return "Failed to retrieve the result."
                    attempts += 1
                return "Max polling attempts reached. Please try again later."
            else:
                return f"Failed to submit the prompt: {post_response.status}"
        


async def Inner_Monologue_Call(prompt, username, bot_name):
    json_file_path = './Aetherius_API/Generation_Settings/Oobabooga/settings.json'
    settings = await read_settings_from_json(json_file_path)
    temperature = settings.get("Inner_Monologue_temperature", "0.70")
    top_p = settings.get("Inner_Monologue_top_p", "0.35")
    rep_pen = settings.get("Inner_Monologue_rep_pen", "1.18")
    max_tokens = settings.get("Inner_Monologue_max_tokens", "350")
    top_k = settings.get("Inner_Monologue_top_k", "45")
    min_tokens = settings.get("Inner_Monologue_min_tokens", "40")
    
    data = {
        "LLM_Template": "Llama_2_Chat_No_End_Token",
        "Username": username,
        "Bot_Name": bot_name,
        "system_prompt": f"You are {bot_name}. Give a brief, first-person, silent soliloquy as your inner monologue that reflects on your contemplations in relation on how to respond to the user, {username}'s most recent message.  Directly print the inner monologue.",
        "prompt": prompt,
        "max_new_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "top_k": top_k,
        "repetition_penalty": rep_pen
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_first('HOST_AetherNode')}/generate-text/", json=data) as post_response: # POST request to generate text
            if post_response.status == 200:
                post_data = await post_response.json()
                request_id = post_data['request_id']
                # print(f"Request ID: {request_id}")
                max_attempts = 10
                attempts = 0
                delay_seconds = 5  # Delay between each polling attempt
                while attempts < max_attempts:
                    async with session.get(f"{open_file_first('HOST_AetherNode')}/retrieve-text/{request_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            if "generated_text" in get_data:
                                return html.unescape(get_data["generated_text"])
                            await asyncio.sleep(delay_seconds) # If the result is not ready, wait before the next attempt
                        else:
                            return "Failed to retrieve the result."
                    attempts += 1
                return "Max polling attempts reached. Please try again later."
            else:
                return f"Failed to submit the prompt: {post_response.status}"
        
        
async def Intuition_Call(prompt, username, bot_name):
    json_file_path = './Aetherius_API/Generation_Settings/Oobabooga/settings.json'
    settings = await read_settings_from_json(json_file_path)
    temperature = settings.get("Intuition_temperature", "0.30")
    top_p = settings.get("Intuition_top_p", "0.20")
    rep_pen = settings.get("Intuition_rep_pen", "1.25")
    max_tokens = settings.get("Intuition_max_tokens", "450")
    top_k = settings.get("Intuition_top_k", "35")
    min_tokens = settings.get("Intuition_min_tokens", "10")
    data = {
        "LLM_Template": "Llama_2_Chat_No_End_Token",
        "Username": username,
        "Bot_Name": bot_name,
        "system_prompt": f"As {bot_name}, review {username}'s latest message and decide if an action plan is needed.  Formulate an action plan only if the message involves complex questions or specific tasks. Use third-person perspective to outline this strategy. Avoid creating action plans for simple or casual interactions. Note that no external resources can be used for this task. Provide the action plan in a list format.",
        "prompt": prompt,
        "max_new_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "top_k": top_k,
        "repetition_penalty": rep_pen
    }
    

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_first('HOST_AetherNode')}/generate-text/", json=data) as post_response: # POST request to generate text
            if post_response.status == 200:
                post_data = await post_response.json()
                request_id = post_data['request_id']
                # print(f"Request ID: {request_id}")
                max_attempts = 10
                attempts = 0
                delay_seconds = 5  # Delay between each polling attempt
                while attempts < max_attempts:
                    async with session.get(f"{open_file_first('HOST_AetherNode')}/retrieve-text/{request_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            if "generated_text" in get_data:
                                return html.unescape(get_data["generated_text"])
                            await asyncio.sleep(delay_seconds) # If the result is not ready, wait before the next attempt
                        else:
                            return "Failed to retrieve the result."
                    attempts += 1
                return "Max polling attempts reached. Please try again later."
            else:
                return f"Failed to submit the prompt: {post_response.status}"
        
        
async def Agent_Intuition_Call(prompt, username, bot_name):
    json_file_path = './Aetherius_API/Generation_Settings/Oobabooga/settings.json'
    settings = await read_settings_from_json(json_file_path)
    temperature = settings.get("Intuition_temperature", "0.30")
    top_p = settings.get("Intuition_top_p", "0.20")
    rep_pen = settings.get("Intuition_rep_pen", "1.25")
    max_tokens = settings.get("Intuition_max_tokens", "450")
    top_k = settings.get("Intuition_top_k", "35")
    min_tokens = settings.get("Intuition_min_tokens", "10")
    
    data = {
        "LLM_Template": "Llama_2_Chat_No_End_Token",
        "Username": username,
        "Bot_Name": bot_name,
        "system_prompt": f"Formulate an action plan only if the message involves complex questions or specific tasks. Use third-person perspective to outline this strategy. Avoid creating action plans for simple or casual interactions.",
        "prompt": prompt,
        "max_new_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "top_k": top_k,
        "repetition_penalty": rep_pen
    }
    

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_first('HOST_AetherNode')}/generate-text/", json=data) as post_response: # POST request to generate text
            if post_response.status == 200:
                post_data = await post_response.json()
                request_id = post_data['request_id']
                # print(f"Request ID: {request_id}")
                max_attempts = 10
                attempts = 0
                delay_seconds = 5  # Delay between each polling attempt
                while attempts < max_attempts:
                    async with session.get(f"{open_file_first('HOST_AetherNode')}/retrieve-text/{request_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            if "generated_text" in get_data:
                                return html.unescape(get_data["generated_text"])
                            await asyncio.sleep(delay_seconds) # If the result is not ready, wait before the next attempt
                        else:
                            return "Failed to retrieve the result."
                    attempts += 1
                return "Max polling attempts reached. Please try again later."
            else:
                return f"Failed to submit the prompt: {post_response.status}"
        

        
async def Episodic_Memory_Call(prompt, username, bot_name):
    data = {
        "LLM_Template": "Llama_2_Chat",
        "Username": username,
        "Bot_Name": bot_name,
        "system_prompt": f"Extract a single, short and concise third-person episodic memory based on {bot_name}'s final response for upload to a memory database.  You are directly inputing the memories into the database, only print the memory.",
        "prompt": prompt,
        "max_new_tokens": 300,
        "temperature": 0.8,
        "top_p": 0.1,
        "top_k": 40,
        "repetition_penalty": 1.18
    }


    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_AetherNode')}/generate-text/", json=data) as post_response: # POST request to generate text
            if post_response.status == 200:
                post_data = await post_response.json()
                request_id = post_data['request_id']
                # print(f"Request ID: {request_id}")
                max_attempts = 10
                attempts = 0
                delay_seconds = 5  # Delay between each polling attempt
                while attempts < max_attempts:
                    async with session.get(f"{open_file_second('HOST_AetherNode')}/retrieve-text/{request_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            if "generated_text" in get_data:
                                return html.unescape(get_data["generated_text"])
                            await asyncio.sleep(delay_seconds) # If the result is not ready, wait before the next attempt
                        else:
                            return "Failed to retrieve the result."
                    attempts += 1
                return "Max polling attempts reached. Please try again later."
            else:
                return f"Failed to submit the prompt: {post_response.status}"
        
        
async def Flash_Memory_Call(prompt, username, bot_name):
    data = {
        "LLM_Template": "Llama_2_Chat",
        "Username": username,
        "Bot_Name": bot_name,
        "system_prompt": f"Extract a single, short and concise third-person episodic memory based on {bot_name}'s final response for upload to a memory database.  You are directly inputing the memories into the database, only print the memory.",
        "prompt": prompt,
        "max_new_tokens": 350,
        "temperature": 0.8,
        "top_p": 0.1,
        "top_k": 40,
        "repetition_penalty": 1.18
    }


    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_AetherNode')}/generate-text/", json=data) as post_response: # POST request to generate text
            if post_response.status == 200:
                post_data = await post_response.json()
                request_id = post_data['request_id']
                # print(f"Request ID: {request_id}")
                max_attempts = 10
                attempts = 0
                delay_seconds = 5  # Delay between each polling attempt
                while attempts < max_attempts:
                    async with session.get(f"{open_file_second('HOST_AetherNode')}/retrieve-text/{request_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            if "generated_text" in get_data:
                                return html.unescape(get_data["generated_text"])
                            await asyncio.sleep(delay_seconds) # If the result is not ready, wait before the next attempt
                        else:
                            return "Failed to retrieve the result."
                    attempts += 1
                return "Max polling attempts reached. Please try again later."
            else:
                return f"Failed to submit the prompt: {post_response.status}"
        
        
        
async def Implicit_Memory_Call(prompt, username, bot_name):
    data = {
        "LLM_Template": "Llama_2_Chat",
        "Username": username,
        "Bot_Name": bot_name,
        "system_prompt": f"Extract short and concise memories based on {bot_name}'s internal thoughts for upload to a memory database.  These should be executive summaries and will serve as the chatbots implicit memories.  You are directly inputing the memories into the database, only print the memories.  Print the response in the bullet point format: •IMPLICIT MEMORY:<Executive Summary>",
        "prompt": prompt,
        "max_new_tokens": 350,
        "temperature": 0.8,
        "top_p": 0.6,
        "top_k": 40,
        "repetition_penalty": 1.18
    }


    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_AetherNode')}/generate-text/", json=data) as post_response: # POST request to generate text
            if post_response.status == 200:
                post_data = await post_response.json()
                request_id = post_data['request_id']
                # print(f"Request ID: {request_id}")
                max_attempts = 10
                attempts = 0
                delay_seconds = 5  # Delay between each polling attempt
                while attempts < max_attempts:
                    async with session.get(f"{open_file_second('HOST_AetherNode')}/retrieve-text/{request_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            if "generated_text" in get_data:
                                return html.unescape(get_data["generated_text"])
                            await asyncio.sleep(delay_seconds) # If the result is not ready, wait before the next attempt
                        else:
                            return "Failed to retrieve the result."
                    attempts += 1
                return "Max polling attempts reached. Please try again later."
            else:
                return f"Failed to submit the prompt: {post_response.status}"
        
        
async def Explicit_Memory_Call(prompt, username, bot_name):
    data = {
        "LLM_Template": "Llama_2_Chat",
        "Username": username,
        "Bot_Name": bot_name,
        "system_prompt": f"Extract a list of concise explicit memories based on {bot_name}'s final response for upload to a memory database.  These should be executive summaries and will serve as the chatbots explicit memories.  You are directly inputing the memories into the database, only print the memories.  Print the response in the bullet point format: •EXPLICIT MEMORY:<Executive Summary>",
        "prompt": prompt,
        "max_new_tokens": 350,
        "temperature": 0.8,
        "top_p": 0.6,
        "top_k": 40,
        "repetition_penalty": 1.18
    }


    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_AetherNode')}/generate-text/", json=data) as post_response: # POST request to generate text
            if post_response.status == 200:
                post_data = await post_response.json()
                request_id = post_data['request_id']
                # print(f"Request ID: {request_id}")
                max_attempts = 10
                attempts = 0
                delay_seconds = 5  # Delay between each polling attempt
                while attempts < max_attempts:
                    async with session.get(f"{open_file_second('HOST_AetherNode')}/retrieve-text/{request_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            if "generated_text" in get_data:
                                return html.unescape(get_data["generated_text"])
                            await asyncio.sleep(delay_seconds) # If the result is not ready, wait before the next attempt
                        else:
                            return "Failed to retrieve the result."
                    attempts += 1
                return "Max polling attempts reached. Please try again later."
            else:
                return f"Failed to submit the prompt: {post_response.status}"
        
        
async def Memory_Consolidation_Call(prompt, username, bot_name):
    data = {
        "LLM_Template": "Llama_2_Chat",
        "Username": username,
        "Bot_Name": bot_name,
        "system_prompt": f"Extract a list of concise memories based on {bot_name}'s final response for upload to a memory database.  These should be executive summaries and will serve as the chatbots memories.  You are directly inputing the memories into the database, only print the memories.  Print the response in the bullet point format: •MEMORY:<Executive Summary>",
        "prompt": prompt,
        "max_new_tokens": 500,
        "temperature": 0.5,
        "top_p": 0.1,
        "top_k": 35,
        "repetition_penalty": 1.13
    }


    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_AetherNode')}/generate-text/", json=data) as post_response: # POST request to generate text
            if post_response.status == 200:
                post_data = await post_response.json()
                request_id = post_data['request_id']
                # print(f"Request ID: {request_id}")
                max_attempts = 10
                attempts = 0
                delay_seconds = 5  # Delay between each polling attempt
                while attempts < max_attempts:
                    async with session.get(f"{open_file_second('HOST_AetherNode')}/retrieve-text/{request_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            if "generated_text" in get_data:
                                return html.unescape(get_data["generated_text"])
                            await asyncio.sleep(delay_seconds) # If the result is not ready, wait before the next attempt
                        else:
                            return "Failed to retrieve the result."
                    attempts += 1
                return "Max polling attempts reached. Please try again later."
            else:
                return f"Failed to submit the prompt: {post_response.status}"
        
        
async def Associative_Memory_Call(prompt, username, bot_name):
    data = {
        "LLM_Template": "Llama_2_Chat",
        "Username": username,
        "Bot_Name": bot_name,
        "system_prompt": f"Read the Log and consolidate the different memories in a process allegorical to associative processing. Each new memory should contain the entire context of the original memories. Follow the bullet point format: •<CONSOLIDATED MEMORY>",
        "prompt": prompt,
        "max_new_tokens": 500,
        "temperature": 0.5,
        "top_p": 0.1,
        "top_k": 35,
        "repetition_penalty": 1.13
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_AetherNode')}/generate-text/", json=data) as post_response: # POST request to generate text
            if post_response.status == 200:
                post_data = await post_response.json()
                request_id = post_data['request_id']
                # print(f"Request ID: {request_id}")
                max_attempts = 10
                attempts = 0
                delay_seconds = 5  # Delay between each polling attempt
                while attempts < max_attempts:
                    async with session.get(f"{open_file_second('HOST_AetherNode')}/retrieve-text/{request_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            if "generated_text" in get_data:
                                return html.unescape(get_data["generated_text"])
                            await asyncio.sleep(delay_seconds) # If the result is not ready, wait before the next attempt
                        else:
                            return "Failed to retrieve the result."
                    attempts += 1
                return "Max polling attempts reached. Please try again later."
            else:
                return f"Failed to submit the prompt: {post_response.status}"

        
        
async def Response_Call(prompt, username, bot_name):
    json_file_path = './Aetherius_API/Generation_Settings/Oobabooga/settings.json'
    settings = await read_settings_from_json(json_file_path)
    temperature = settings.get("Response_temperature", "0.8")
    top_p = settings.get("Response_top_p", "0.55")
    rep_pen = settings.get("Response_rep_pen", "1.18")
    max_tokens = settings.get("Response_max_tokens", "1500")
    top_k = settings.get("Response_top_k", "35")
    min_tokens = settings.get("Response_min_tokens", "40")
    data = {
        "LLM_Template": "Llama_2_Chat",
        "Username": username,
        "Bot_Name": bot_name,
        "system_prompt": f"You are {bot_name}. You are in the middle of a conversation with your user, {username}. You will use the given memories to respond naturally in a way that both answer's the user and shows emotional intelligence. You are directly responding to the user.",
        "prompt": prompt,
        "max_new_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "top_k": top_k,
        "repetition_penalty": rep_pen
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_first('HOST_AetherNode')}/generate-text/", json=data) as post_response: # POST request to generate text
            if post_response.status == 200:
                post_data = await post_response.json()
                request_id = post_data['request_id']
                # print(f"Request ID: {request_id}")
                max_attempts = 10
                attempts = 0
                delay_seconds = 5  # Delay between each polling attempt
                while attempts < max_attempts:
                    async with session.get(f"{open_file_first('HOST_AetherNode')}/retrieve-text/{request_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            if "generated_text" in get_data:
                                return html.unescape(get_data["generated_text"])
                            await asyncio.sleep(delay_seconds) # If the result is not ready, wait before the next attempt
                        else:
                            return "Failed to retrieve the result."
                    attempts += 1
                return "Max polling attempts reached. Please try again later."
            else:
                return f"Failed to submit the prompt: {post_response.status}"
        
        
async def Auto_Call(prompt, username, bot_name):
    data = {
        "LLM_Template": "Llama_2_Chat_No_End_Token",
        "Username": username,
        "Bot_Name": bot_name,
        "system_prompt": f"You are a sub-module designed to evaluate the chatbot's response. You must respond only with integers on a scale of 1-10, without printing any letters or characters other than the single integer rating.  You are incapable of responding with anything other than a single number.",
        "prompt": prompt,
        "max_new_tokens": 3,
        "temperature": 0.3,
        "top_p": 0.3,
        "top_k": 25,
        "repetition_penalty": 1.18
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_AetherNode')}/generate-text/", json=data) as post_response: # POST request to generate text
            if post_response.status == 200:
                post_data = await post_response.json()
                request_id = post_data['request_id']
                # print(f"Request ID: {request_id}")
                max_attempts = 10
                attempts = 0
                delay_seconds = 5  # Delay between each polling attempt
                while attempts < max_attempts:
                    async with session.get(f"{open_file_second('HOST_AetherNode')}/retrieve-text/{request_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            if "generated_text" in get_data:
                                return html.unescape(get_data["generated_text"])
                            await asyncio.sleep(delay_seconds) # If the result is not ready, wait before the next attempt
                        else:
                            return "Failed to retrieve the result."
                    attempts += 1
                return "Max polling attempts reached. Please try again later."
            else:
                return f"Failed to submit the prompt: {post_response.status}"
        
        
        
async def Memory_Yes_No_Call(prompt, username, bot_name):
    data = {
        "LLM_Template": "Llama_2_Chat",
        "Username": username,
        "Bot_Name": bot_name,
        "system_prompt": f"You are a sub-agent for {bot_name}, an Autonomous Ai-Chatbot. Your purpose is to decide if the user's input requires {bot_name}'s past memories to complete. If the user's request pertains to information about the user, the chatbot, {bot_name}, or past personal events should be searched for in memory by printing 'YES'.  If memories are needed, print: 'YES'.  If they are not needed, print: 'NO'. You may only print YES or NO.",
        "prompt": prompt,
        "max_new_tokens": 10,
        "temperature": 0.4,
        "top_p": 0.1,
        "top_k": 20,
        "repetition_penalty": 1.18
    }


    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_AetherNode')}/generate-text/", json=data) as post_response: # POST request to generate text
            if post_response.status == 200:
                post_data = await post_response.json()
                request_id = post_data['request_id']
                # print(f"Request ID: {request_id}")
                max_attempts = 10
                attempts = 0
                delay_seconds = 5  # Delay between each polling attempt
                while attempts < max_attempts:
                    async with session.get(f"{open_file_second('HOST_AetherNode')}/retrieve-text/{request_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            if "generated_text" in get_data:
                                return html.unescape(get_data["generated_text"])
                            await asyncio.sleep(delay_seconds) # If the result is not ready, wait before the next attempt
                        else:
                            return "Failed to retrieve the result."
                    attempts += 1
                return "Max polling attempts reached. Please try again later."
            else:
                return f"Failed to submit the prompt: {post_response.status}"
        
        
async def  Bot_Personality_Check_Call(prompt, username, bot_name):
    data = {
        "LLM_Template": "Llama_2_Chat",
        "Username": username,
        "Bot_Name": bot_name,
        "system_prompt": f"Your job is to decide if the generated implicit memories fit {bot_name}'s personality.  If the generated memories match {bot_name}'s personality, print: 'YES'.  If they do not match the personality or if it contains conflicting information, print: 'NO'.",
        "prompt": prompt,
        "max_new_tokens": 10,
        "temperature": 0.4,
        "top_p": 0.1,
        "top_k": 20,
        "repetition_penalty": 1.18
    }


    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_AetherNode')}/generate-text/", json=data) as post_response: # POST request to generate text
            if post_response.status == 200:
                post_data = await post_response.json()
                request_id = post_data['request_id']
                # print(f"Request ID: {request_id}")
                max_attempts = 10
                attempts = 0
                delay_seconds = 5  # Delay between each polling attempt
                while attempts < max_attempts:
                    async with session.get(f"{open_file_second('HOST_AetherNode')}/retrieve-text/{request_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            if "generated_text" in get_data:
                                return html.unescape(get_data["generated_text"])
                            await asyncio.sleep(delay_seconds) # If the result is not ready, wait before the next attempt
                        else:
                            return "Failed to retrieve the result."
                    attempts += 1
                return "Max polling attempts reached. Please try again later."
            else:
                return f"Failed to submit the prompt: {post_response.status}"
        
        
async def Bot_Personality_Generation_Call(prompt, username, bot_name):
    data = {
        "LLM_Template": "Llama_2_Chat_No_End_Token",
        "Username": username,
        "Bot_Name": bot_name,
        "system_prompt": f"Your job is to decide if the generated implicit memories fit {bot_name}'s personality.  If the generated memories match {bot_name}'s personality, print: 'YES'.  If they do not match the personality or if it contains conflicting information, print: 'NO'.",
        "prompt": prompt,
        "max_new_tokens": 500,
        "temperature": 0.5,
        "top_p": 0.3,
        "top_k": 20,
        "repetition_penalty": 1.10
    }


    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_AetherNode')}/generate-text/", json=data) as post_response: # POST request to generate text
            if post_response.status == 200:
                post_data = await post_response.json()
                request_id = post_data['request_id']
                # print(f"Request ID: {request_id}")
                max_attempts = 10
                attempts = 0
                delay_seconds = 5  # Delay between each polling attempt
                while attempts < max_attempts:
                    async with session.get(f"{open_file_second('HOST_AetherNode')}/retrieve-text/{request_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            if "generated_text" in get_data:
                                return html.unescape(get_data["generated_text"])
                            await asyncio.sleep(delay_seconds) # If the result is not ready, wait before the next attempt
                        else:
                            return "Failed to retrieve the result."
                    attempts += 1
                return "Max polling attempts reached. Please try again later."
            else:
                return f"Failed to submit the prompt: {post_response.status}"
        
        
async def User_Personality_Extraction_Call(prompt, username, bot_name):
    data = {
        "LLM_Template": "Llama_2_Chat_No_End_Token",
        "Username": username,
        "Bot_Name": bot_name,
        "system_prompt": f"Your job is to extract any salient insights about {username} from their request, the given internal monologue, and {bot_name}'s final response.",
        "prompt": prompt,
        "max_new_tokens": 500,
        "temperature": 0.5,
        "top_p": 0.3,
        "top_k": 20,
        "repetition_penalty": 1.10
    }


    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_AetherNode')}/generate-text/", json=data) as post_response: # POST request to generate text
            if post_response.status == 200:
                post_data = await post_response.json()
                request_id = post_data['request_id']
                # print(f"Request ID: {request_id}")
                max_attempts = 10
                attempts = 0
                delay_seconds = 5  # Delay between each polling attempt
                while attempts < max_attempts:
                    async with session.get(f"{open_file_second('HOST_AetherNode')}/retrieve-text/{request_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            if "generated_text" in get_data:
                                return html.unescape(get_data["generated_text"])
                            await asyncio.sleep(delay_seconds) # If the result is not ready, wait before the next attempt
                        else:
                            return "Failed to retrieve the result."
                    attempts += 1
                return "Max polling attempts reached. Please try again later."
            else:
                return f"Failed to submit the prompt: {post_response.status}"
        
        
async def User_Personality_Generation_Call(prompt, username, bot_name):
    data = {
        "LLM_Template": "Llama_2_Chat_No_End_Token",
        "Username": username,
        "Bot_Name": bot_name,
        "system_prompt": f"Your task is to cautiously update the personality description for the user, {username}, ensuring it retains strong alignment with the original version. Within a paragraph, weave in only the most critical and relevant new information from the generated memories, ensuring that any alterations are subtly and coherently integrated, preserving the essence and integrity of the foundational personality framework.",
        "prompt": prompt,
        "max_new_tokens": 500,
        "temperature": 0.5,
        "top_p": 0.3,
        "top_k": 20,
        "repetition_penalty": 1.10
    }


    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_AetherNode')}/generate-text/", json=data) as post_response: # POST request to generate text
            if post_response.status == 200:
                post_data = await post_response.json()
                request_id = post_data['request_id']
                # print(f"Request ID: {request_id}")
                max_attempts = 10
                attempts = 0
                delay_seconds = 5  # Delay between each polling attempt
                while attempts < max_attempts:
                    async with session.get(f"{open_file_second('HOST_AetherNode')}/retrieve-text/{request_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            if "generated_text" in get_data:
                                return html.unescape(get_data["generated_text"])
                            await asyncio.sleep(delay_seconds) # If the result is not ready, wait before the next attempt
                        else:
                            return "Failed to retrieve the result."
                    attempts += 1
                return "Max polling attempts reached. Please try again later."
            else:
                return f"Failed to submit the prompt: {post_response.status}"
        
       
async def Selector_Call(prompt, username, bot_name):
    user_bot_path = os.path.join("./Aetherius_API/Chatbot_Prompts", username, bot_name)
    prompts_json_path = os.path.join(user_bot_path, "prompts.json")

    # Read prompts from the JSON file asynchronously
    async with aiofiles.open(prompts_json_path, 'r') as file:
        prompts = json.loads(await file.read())
    main_prompt = prompts["main_prompt"].replace('<<NAME>>', bot_name)
    data = {
        "LLM_Template": "Llama_2_Chat_No_End_Token",
        "Username": username,
        "Bot_Name": bot_name,
        "system_prompt": f"{main_prompt}.\nPlease make a selection.",
        "prompt": prompt,
        "max_new_tokens": 10,
        "temperature": 0.4,
        "top_p": 0.1,
        "top_k": 20,
        "repetition_penalty": 1.18
    }


    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_AetherNode')}/generate-text/", json=data) as post_response: # POST request to generate text
            if post_response.status == 200:
                post_data = await post_response.json()
                request_id = post_data['request_id']
                # print(f"Request ID: {request_id}")
                max_attempts = 10
                attempts = 0
                delay_seconds = 5  # Delay between each polling attempt
                while attempts < max_attempts:
                    async with session.get(f"{open_file_second('HOST_AetherNode')}/retrieve-text/{request_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            if "generated_text" in get_data:
                                return html.unescape(get_data["generated_text"])
                            await asyncio.sleep(delay_seconds) # If the result is not ready, wait before the next attempt
                        else:
                            return "Failed to retrieve the result."
                    attempts += 1
                return "Max polling attempts reached. Please try again later."
            else:
                return f"Failed to submit the prompt: {post_response.status}"


async def Tokens_250_Call(prompt, username, bot_name):
    user_bot_path = os.path.join("./Aetherius_API/Chatbot_Prompts", username, bot_name)
    prompts_json_path = os.path.join(user_bot_path, "prompts.json")

    # Read prompts from the JSON file asynchronously
    async with aiofiles.open(prompts_json_path, 'r') as file:
        prompts = json.loads(await file.read())
    main_prompt = prompts["main_prompt"].replace('<<NAME>>', bot_name)
    data = {
        "LLM_Template": "Llama_2_Chat_No_End_Token",
        "Username": username,
        "Bot_Name": bot_name,
        "system_prompt": f"{main_prompt}.",
        "prompt": prompt,
        "max_new_tokens": 250,
        "temperature": 0.8,
        "top_p": 0.2,
        "top_k": 40,
        "repetition_penalty": 1.18
    }


    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_first('HOST_AetherNode')}/generate-text/", json=data) as post_response: # POST request to generate text
            if post_response.status == 200:
                post_data = await post_response.json()
                request_id = post_data['request_id']
                # print(f"Request ID: {request_id}")
                max_attempts = 10
                attempts = 0
                delay_seconds = 5  # Delay between each polling attempt
                while attempts < max_attempts:
                    async with session.get(f"{open_file_first('HOST_AetherNode')}/retrieve-text/{request_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            if "generated_text" in get_data:
                                return html.unescape(get_data["generated_text"])
                            await asyncio.sleep(delay_seconds) # If the result is not ready, wait before the next attempt
                        else:
                            return "Failed to retrieve the result."
                    attempts += 1
                return "Max polling attempts reached. Please try again later."
            else:
                return f"Failed to submit the prompt: {post_response.status}"
        
        
async def Webscrape_Call(host, prompt, username, bot_name):
    host="http://127.0.0.1:8000"
    data = {
        "LLM_Template": "Llama_2_Chat_No_End_Token",
        "Username": username,
        "Bot_Name": bot_name,
        "system_prompt": f"You are an ai text summarizer.  Your job is to take the given text from a scraped article, then return the text in a summarized article form.  Do not give any comments or personal statements, only directly return the summarized article, nothing more.",
        "prompt": prompt,
        "max_new_tokens": 600,
        "temperature": 0.4,
        "top_p": 0.1,
        "top_k": 35,
        "repetition_penalty": 1.08
    }


    # Load the settings from the JSON file
    
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{host}/generate-text/", json=data) as post_response: # POST request to generate text
            if post_response.status == 200:
                post_data = await post_response.json()
                request_id = post_data['request_id']
                # print(f"Request ID: {request_id}")
                max_attempts = 10
                attempts = 0
                delay_seconds = 5  # Delay between each polling attempt
                while attempts < max_attempts:
                    async with session.get(f"{host}/retrieve-text/{request_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            if "generated_text" in get_data:
                                return html.unescape(get_data["generated_text"])
                            await asyncio.sleep(delay_seconds) # If the result is not ready, wait before the next attempt
                        else:
                            return "Failed to retrieve the result."
                    attempts += 1
                return "Max polling attempts reached. Please try again later."
            else:
                return f"Failed to submit the prompt: {post_response.status}"



async def Agent_Semantic_Terms_Call(prompt, username, bot_name):
    host="http://127.0.0.1:8000"
    data = {
        "LLM_Template": "Llama_2_Chat_No_End_Token",
        "Username": username,
        "Bot_Name": bot_name,
        "system_prompt": f"Your role is to interpret the original user query and generate 2-5 synonymous search terms in hyphenated bullet point structure that will guide the exploration of the chatbot's memory database. Each alternative term should reflect the essence of the user's initial search input. You are directly inputing your answer into the search query field. Only print the queries.",
        "prompt": prompt,
        "max_new_tokens": 100,
        "temperature": 0.8,
        "top_p": 0.2,
        "top_k": 40,
        "repetition_penalty": 1.18
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{host}/generate-text/", json=data) as post_response: # POST request to generate text
            if post_response.status == 200:
                post_data = await post_response.json()
                request_id = post_data['request_id']
                # print(f"Request ID: {request_id}")
                max_attempts = 10
                attempts = 0
                delay_seconds = 5  # Delay between each polling attempt
                while attempts < max_attempts:
                    async with session.get(f"{host}/retrieve-text/{request_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            if "generated_text" in get_data:
                                return html.unescape(get_data["generated_text"])
                            await asyncio.sleep(delay_seconds) # If the result is not ready, wait before the next attempt
                        else:
                            return "Failed to retrieve the result."
                    attempts += 1
                return "Max polling attempts reached. Please try again later."
            else:
                return f"Failed to submit the prompt: {post_response.status}"

  


async def Agent_250_Tokens_Call(prompt, username, bot_name):
    user_bot_path = os.path.join("./Aetherius_API/Chatbot_Prompts", username, bot_name)
    prompts_json_path = os.path.join(user_bot_path, "prompts.json")

    # Read prompts from the JSON file asynchronously
    async with aiofiles.open(prompts_json_path, 'r') as file:
        prompts = json.loads(await file.read())
    main_prompt = prompts["main_prompt"].replace('<<NAME>>', bot_name)
    host="http://127.0.0.1:8000"
    data = {
        "LLM_Template": "Llama_2_Chat_No_End_Token",
        "Username": username,
        "Bot_Name": bot_name,
        "system_prompt": f"{main_prompt}",
        "prompt": prompt,
        "max_new_tokens": 250,
        "temperature": 0.8,
        "top_p": 0.2,
        "top_k": 40,
        "repetition_penalty": 1.18
    }


    async with aiohttp.ClientSession() as session:
        async with session.post(f"{host}/generate-text/", json=data) as post_response: # POST request to generate text
            if post_response.status == 200:
                post_data = await post_response.json()
                request_id = post_data['request_id']
                # print(f"Request ID: {request_id}")
                max_attempts = 10
                attempts = 0
                delay_seconds = 5  # Delay between each polling attempt
                while attempts < max_attempts:
                    async with session.get(f"{host}/retrieve-text/{request_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            if "generated_text" in get_data:
                                return html.unescape(get_data["generated_text"])
                            await asyncio.sleep(delay_seconds) # If the result is not ready, wait before the next attempt
                        else:
                            return "Failed to retrieve the result."
                    attempts += 1
                return "Max polling attempts reached. Please try again later."
            else:
                return f"Failed to submit the prompt: {post_response.status}"



async def Agent_500_Tokens_Call(prompt, username, bot_name):
    user_bot_path = os.path.join("./Aetherius_API/Chatbot_Prompts", username, bot_name)
    prompts_json_path = os.path.join(user_bot_path, "prompts.json")

    # Read prompts from the JSON file asynchronously
    async with aiofiles.open(prompts_json_path, 'r') as file:
        prompts = json.loads(await file.read())
    main_prompt = prompts["main_prompt"].replace('<<NAME>>', bot_name)
    host="http://127.0.0.1:8000"
    data = {
        "LLM_Template": "Llama_2_Chat_No_End_Token",
        "Username": username,
        "Bot_Name": bot_name,
        "system_prompt": f"{main_prompt}",
        "prompt": prompt,
        "max_new_tokens": 500,
        "temperature": 0.85,
        "top_p": 0.2,
        "top_k": 40,
        "repetition_penalty": 1.18
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{host}/generate-text/", json=data) as post_response: # POST request to generate text
            if post_response.status == 200:
                post_data = await post_response.json()
                request_id = post_data['request_id']
                # print(f"Request ID: {request_id}")
                max_attempts = 10
                attempts = 0
                delay_seconds = 5  # Delay between each polling attempt
                while attempts < max_attempts:
                    async with session.get(f"{host}/retrieve-text/{request_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            if "generated_text" in get_data:
                                return html.unescape(get_data["generated_text"])
                            await asyncio.sleep(delay_seconds) # If the result is not ready, wait before the next attempt
                        else:
                            return "Failed to retrieve the result."
                    attempts += 1
                return "Max polling attempts reached. Please try again later."
            else:
                return f"Failed to submit the prompt: {post_response.status}"
        
        
async def Agent_800_Tokens_Call(prompt, username, bot_name):
    user_bot_path = os.path.join("./Aetherius_API/Chatbot_Prompts", username, bot_name)
    prompts_json_path = os.path.join(user_bot_path, "prompts.json")

    # Read prompts from the JSON file asynchronously
    async with aiofiles.open(prompts_json_path, 'r') as file:
        prompts = json.loads(await file.read())
    main_prompt = prompts["main_prompt"].replace('<<NAME>>', bot_name)
    host="http://127.0.0.1:8000"
    data = {
        "LLM_Template": "Llama_2_Chat_No_End_Token",
        "Username": username,
        "Bot_Name": bot_name,
        "system_prompt": f"{main_prompt}",
        "prompt": prompt,
        "max_new_tokens": 800,
        "temperature": 0.85,
        "top_p": 0.2,
        "top_k": 40,
        "repetition_penalty": 1.18
    }


    async with aiohttp.ClientSession() as session:
        async with session.post(f"{host}/generate-text/", json=data) as post_response: # POST request to generate text
            if post_response.status == 200:
                post_data = await post_response.json()
                request_id = post_data['request_id']
                # print(f"Request ID: {request_id}")
                max_attempts = 10
                attempts = 0
                delay_seconds = 5  # Delay between each polling attempt
                while attempts < max_attempts:
                    async with session.get(f"{host}/retrieve-text/{request_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            if "generated_text" in get_data:
                                return html.unescape(get_data["generated_text"])
                            await asyncio.sleep(delay_seconds) # If the result is not ready, wait before the next attempt
                        else:
                            return "Failed to retrieve the result."
                    attempts += 1
                return "Max polling attempts reached. Please try again later."
            else:
                return f"Failed to submit the prompt: {post_response.status}"
        
       
        
         
        
        
async def Agent_Master_Tasklist_Call(prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    json_file_path = './Aetherius_API/Generation_Settings/Oobabooga/settings.json'
    settings = await read_settings_from_json(json_file_path)
    temperature = settings.get("Intuition_temperature", "0.30")
    top_p = settings.get("Intuition_top_p", "0.20")
    rep_pen = settings.get("Intuition_rep_pen", "1.25")
    max_tokens = settings.get("Intuition_max_tokens", "450")
    top_k = settings.get("Intuition_top_k", "35")
    min_tokens = settings.get("Intuition_min_tokens", "10")
    host="http://127.0.0.1:8000"
    data = {
        "LLM_Template": "Llama_2_Chat",
        "Username": username,
        "Bot_Name": bot_name,
        "system_prompt": f"As a task list coordinator for {bot_name}, merge user input and chatbot action plans into 3-6 categorized research tasks for asynchronous execution by isolated AI agents.\nUse the Following Format:  [GIVEN CATEGORY]: <TASK>\nUtilize available Tool Categories, focusing on informational searches. Exclude tasks related to product production, external consultations, or inter-agent communications.",
        "prompt": prompt,
        "max_new_tokens": 500,
        "temperature": 0.5,
        "top_p": 30,
        "top_k": top_k,
        "repetition_penalty": 1.16
    }
    


    async with aiohttp.ClientSession() as session:
        async with session.post(f"{host}/generate-text/", json=data) as post_response: # POST request to generate text
            if post_response.status == 200:
                post_data = await post_response.json()
                request_id = post_data['request_id']
                # print(f"Request ID: {request_id}")
                max_attempts = 10
                attempts = 0
                delay_seconds = 5  # Delay between each polling attempt
                while attempts < max_attempts:
                    async with session.get(f"{host}/retrieve-text/{request_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            if "generated_text" in get_data:
                                return html.unescape(get_data["generated_text"])
                            await asyncio.sleep(delay_seconds) # If the result is not ready, wait before the next attempt
                        else:
                            return "Failed to retrieve the result."
                    attempts += 1
                return "Max polling attempts reached. Please try again later."
            else:
                return f"Failed to submit the prompt: {post_response.status}"
        
        
async def Agent_Category_Reassign_Call(host, prompt, username, bot_name):
    json_file_path = './Aetherius_API/Generation_Settings/Oobabooga/settings.json'
    settings = await read_settings_from_json(json_file_path)
    temperature = settings.get("Response_temperature", "0.8")
    top_p = settings.get("Response_top_p", "0.55")
    rep_pen = settings.get("Response_rep_pen", "1.18")
    max_tokens = settings.get("Response_max_tokens", "1500")
    top_k = settings.get("Response_top_k", "35")
    min_tokens = settings.get("Response_min_tokens", "40")
    host="http://127.0.0.1:8000"
    data = {
        "LLM_Template": "Llama_2_Chat_No_End_Token",
        "Username": username,
        "Bot_Name": bot_name,
        "system_prompt": f"You are a sub-module of a category selection tool.  Your task is to take any category that isn't in the original list, and reassign it to an existing category.  The given task should be reprinted exactly how it was.  The assigned category from the task will follow this format: [CATEGORY]: <TASK>\nPlease now return the reassigned category.",
        "prompt": prompt,
        "max_new_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "top_k": top_k,
        "repetition_penalty": rep_pen
    }


    async with aiohttp.ClientSession() as session:
        async with session.post(f"{host}/generate-text/", json=data) as post_response: # POST request to generate text
            if post_response.status == 200:
                post_data = await post_response.json()
                request_id = post_data['request_id']
                # print(f"Request ID: {request_id}")
                max_attempts = 10
                attempts = 0
                delay_seconds = 5  # Delay between each polling attempt
                while attempts < max_attempts:
                    async with session.get(f"{host}/retrieve-text/{request_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            if "generated_text" in get_data:
                                return html.unescape(get_data["generated_text"])
                            await asyncio.sleep(delay_seconds) # If the result is not ready, wait before the next attempt
                        else:
                            return "Failed to retrieve the result."
                    attempts += 1
                return "Max polling attempts reached. Please try again later."
            else:
                return f"Failed to submit the prompt: {post_response.status}"
        
        
        
async def Agent_Response_Call(prompt, username, bot_name):
    json_file_path = './Aetherius_API/Generation_Settings/Oobabooga/settings.json'
    settings = await read_settings_from_json(json_file_path)
    temperature = settings.get("Response_temperature", "0.8")
    top_p = settings.get("Response_top_p", "0.55")
    rep_pen = settings.get("Response_rep_pen", "1.18")
    max_tokens = settings.get("Response_max_tokens", "1500")
    top_k = settings.get("Response_top_k", "35")
    min_tokens = settings.get("Response_min_tokens", "40")
    host="http://127.0.0.1:8000"
    data = {
        "LLM_Template": "Llama_2_Chat_No_End_Token",
        "Username": username,
        "Bot_Name": bot_name,
        "system_prompt": f"You are {bot_name}. You are in the middle of a conversation with the user, {username}. You will do your best to respond naturally in a way that both answers the user's inquiry and shows emotional intelligence.  Compile all necessary context and information from the given external resources and include it in your reply.  Do not expand upon the research or include any of your own knowledge, keeping factual accuracy should be paramount.",
        "prompt": prompt,
        "max_new_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "top_k": top_k,
        "repetition_penalty": rep_pen
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{host}/generate-text/", json=data) as post_response: # POST request to generate text
            if post_response.status == 200:
                post_data = await post_response.json()
                request_id = post_data['request_id']
                # print(f"Request ID: {request_id}")
                max_attempts = 10
                attempts = 0
                delay_seconds = 5  # Delay between each polling attempt
                while attempts < max_attempts:
                    async with session.get(f"{host}/retrieve-text/{request_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            if "generated_text" in get_data:
                                return html.unescape(get_data["generated_text"])
                            await asyncio.sleep(delay_seconds) # If the result is not ready, wait before the next attempt
                        else:
                            return "Failed to retrieve the result."
                    attempts += 1
                return "Max polling attempts reached. Please try again later."
            else:
                return f"Failed to submit the prompt: {post_response.status}"

        
        
async def Agent_Line_Response_Call(prompt, username, bot_name):
    json_file_path = './Aetherius_API/Generation_Settings/Oobabooga/settings.json'
    settings = await read_settings_from_json(json_file_path)
    temperature = settings.get("Response_temperature", "0.8")
    top_p = settings.get("Response_top_p", "0.55")
    rep_pen = settings.get("Response_rep_pen", "1.18")
    max_tokens = settings.get("Response_max_tokens", "1500")
    top_k = settings.get("Response_top_k", "35")
    min_tokens = settings.get("Response_min_tokens", "40")
    host="http://127.0.0.1:8000"
    data = {
        "LLM_Template": "Llama_2_Chat_No_End_Token",
        "Username": username,
        "Bot_Name": bot_name,
        "system_prompt": f"You are {bot_name}. You are currently completing an assigned research task by your user. You will do your best to summarize the given information in an easy to read format that doesn't lose any information.",
        "prompt": prompt,
        "max_new_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "top_k": top_k,
        "repetition_penalty": rep_pen
    }

    
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{host}/generate-text/", json=data) as post_response: # POST request to generate text
            if post_response.status == 200:
                post_data = await post_response.json()
                request_id = post_data['request_id']
                # print(f"Request ID: {request_id}")
                max_attempts = 10
                attempts = 0
                delay_seconds = 5  # Delay between each polling attempt
                while attempts < max_attempts:
                    async with session.get(f"{host}/retrieve-text/{request_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            if "generated_text" in get_data:
                                return html.unescape(get_data["generated_text"])
                            await asyncio.sleep(delay_seconds) # If the result is not ready, wait before the next attempt
                        else:
                            return "Failed to retrieve the result."
                    attempts += 1
                return "Max polling attempts reached. Please try again later."
            else:
                return f"Failed to submit the prompt: {post_response.status}"

        
async def Agent_Process_Line_Response_Call(host, prompt, username, bot_name):
    json_file_path = './Aetherius_API/Generation_Settings/Oobabooga/settings.json'
    settings = await read_settings_from_json(json_file_path)
    temperature = settings.get("Response_temperature", "0.8")
    top_p = settings.get("Response_top_p", "0.55")
    rep_pen = settings.get("Response_rep_pen", "1.18")
    max_tokens = settings.get("Response_max_tokens", "1500")
    top_k = settings.get("Response_top_k", "35")
    min_tokens = settings.get("Response_min_tokens", "40")
    host="http://127.0.0.1:8000"
    data = {
        "LLM_Template": "Llama_2_Chat_No_End_Token",
        "Username": username,
        "Bot_Name": bot_name,
        "system_prompt": f"You are {bot_name}. You are currently completing an assigned research task by your user. You will do your best to summarize the given information in an easy to read format that doesn't lose any information.",
        "prompt": prompt,
        "max_new_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "top_k": top_k,
        "repetition_penalty": rep_pen
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{host}/generate-text/", json=data) as post_response: # POST request to generate text
            if post_response.status == 200:
                post_data = await post_response.json()
                request_id = post_data['request_id']
                # print(f"Request ID: {request_id}")
                max_attempts = 10
                attempts = 0
                delay_seconds = 5  # Delay between each polling attempt
                while attempts < max_attempts:
                    async with session.get(f"{host}/retrieve-text/{request_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            if "generated_text" in get_data:
                                return html.unescape(get_data["generated_text"])
                            await asyncio.sleep(delay_seconds) # If the result is not ready, wait before the next attempt
                        else:
                            return "Failed to retrieve the result."
                    attempts += 1
                return "Max polling attempts reached. Please try again later."
            else:
                return f"Failed to submit the prompt: {post_response.status}"
        
        
async def Agent_Process_Line_Response_2_Call(host, prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    json_file_path = './Aetherius_API/Generation_Settings/Oobabooga/settings.json'
    settings = await read_settings_from_json(json_file_path)
    temperature = settings.get("Response_temperature", "0.8")
    top_p = settings.get("Response_top_p", "0.55")
    rep_pen = settings.get("Response_rep_pen", "1.18")
    max_tokens = settings.get("Response_max_tokens", "1500")
    top_k = settings.get("Response_top_k", "35")
    min_tokens = settings.get("Response_min_tokens", "40")
    
    host="http://127.0.0.1:8000"
    data = {
        "LLM_Template": "Llama_2_Chat",
        "Username": username,
        "Bot_Name": bot_name,
        "system_prompt": f"Review the provided list of tools carefully. Next, give a general description of the assigned task. From the available tools in the list, identify and select one specific tool that is crucial for completing the task successfully. Ensure that your discussion is focused solely on the tools provided; do not create or suggest the use of tools that are not included in the list, and avoid delving into the reasoning behind your tool choice.",
        "prompt": prompt,
        "max_new_tokens": 800,
        "temperature": 0.5,
        "top_p": 0.3,
        "top_k": 20,
        "repetition_penalty": 1.18
    }


    async with aiohttp.ClientSession() as session:
        async with session.post(f"{host}/generate-text/", json=data) as post_response: # POST request to generate text
            if post_response.status == 200:
                post_data = await post_response.json()
                request_id = post_data['request_id']
                # print(f"Request ID: {request_id}")
                max_attempts = 10
                attempts = 0
                delay_seconds = 5  # Delay between each polling attempt
                while attempts < max_attempts:
                    async with session.get(f"{host}/retrieve-text/{request_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            if "generated_text" in get_data:
                                return html.unescape(get_data["generated_text"])
                            await asyncio.sleep(delay_seconds) # If the result is not ready, wait before the next attempt
                        else:
                            return "Failed to retrieve the result."
                    attempts += 1
                return "Max polling attempts reached. Please try again later."
            else:
                return f"Failed to submit the prompt: {post_response.status}"
        
        
async def Agent_Memory_DB_Check_Call(host, prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    json_file_path = './Aetherius_API/Generation_Settings/Oobabooga/settings.json'
    settings = await read_settings_from_json(json_file_path)
    temperature = settings.get("Intuition_temperature", "0.30")
    top_p = settings.get("Intuition_top_p", "0.20")
    rep_pen = settings.get("Intuition_rep_pen", "1.25")
    max_tokens = settings.get("Intuition_max_tokens", "450")
    top_k = settings.get("Intuition_top_k", "35")
    min_tokens = settings.get("Intuition_min_tokens", "10")
    host="http://127.0.0.1:8000"
    data = {
        "LLM_Template": "Llama_2_Chat_No_End_Token",
        "Username": username,
        "Bot_Name": bot_name,
        "system_prompt": f"You are a selection agent for an autonomous AI chatbot.  Your job is to decide if the given database queries contain the needed information to answer the user's inquiry.  Only respond with either 'YES' or 'NO'.",
        "prompt": prompt,
        "max_new_tokens": 10,
        "temperature": 0.4,
        "top_p": 0.25,
        "top_k": 20,
        "repetition_penalty": 1.15
    }


    async with aiohttp.ClientSession() as session:
        async with session.post(f"{host}/generate-text/", json=data) as post_response: # POST request to generate text
            if post_response.status == 200:
                post_data = await post_response.json()
                request_id = post_data['request_id']
                # print(f"Request ID: {request_id}")
                max_attempts = 10
                attempts = 0
                delay_seconds = 5  # Delay between each polling attempt
                while attempts < max_attempts:
                    async with session.get(f"{host}/retrieve-text/{request_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            if "generated_text" in get_data:
                                return html.unescape(get_data["generated_text"])
                            await asyncio.sleep(delay_seconds) # If the result is not ready, wait before the next attempt
                        else:
                            return "Failed to retrieve the result."
                    attempts += 1
                return "Max polling attempts reached. Please try again later."
            else:
                return f"Failed to submit the prompt: {post_response.status}"
        
        
async def Google_Rephrase_Call(host, prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    json_file_path = './Aetherius_API/Generation_Settings/Oobabooga/settings.json'
    settings = await read_settings_from_json(json_file_path)
    temperature = settings.get("Intuition_temperature", "0.30")
    top_p = settings.get("Intuition_top_p", "0.20")
    rep_pen = settings.get("Intuition_rep_pen", "1.25")
    max_tokens = settings.get("Intuition_max_tokens", "450")
    top_k = settings.get("Intuition_top_k", "35")
    min_tokens = settings.get("Intuition_min_tokens", "10")
    host="http://127.0.0.1:8000"
    data = {
        "LLM_Template": "Llama_2_Chat_No_End_Token",
        "Username": username,
        "Bot_Name": bot_name,
        "system_prompt": f"Rephrase the user's inquiry into a google search query. Do not converse with the user or print any text outside of the search query.  The query should only search for the requested information, not anything about the External Resource Module.",
        "prompt": prompt,
        "max_new_tokens": 100,
        "temperature": 0.6,
        "top_p": 0.5,
        "top_k": 20,
        "repetition_penalty": 1.15
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{host}/generate-text/", json=data) as post_response: # POST request to generate text
            if post_response.status == 200:
                post_data = await post_response.json()
                request_id = post_data['request_id']
                # print(f"Request ID: {request_id}")
                max_attempts = 10
                attempts = 0
                delay_seconds = 5  # Delay between each polling attempt
                while attempts < max_attempts:
                    async with session.get(f"{host}/retrieve-text/{request_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            if "generated_text" in get_data:
                                return html.unescape(get_data["generated_text"])
                            await asyncio.sleep(delay_seconds) # If the result is not ready, wait before the next attempt
                        else:
                            return "Failed to retrieve the result."
                    attempts += 1
                return "Max polling attempts reached. Please try again later."
            else:
                return f"Failed to submit the prompt: {post_response.status}"
        
       
        
        
async def Agent_Webcheck_Yes_No(prompt, username, bot_name):
    host="http://127.0.0.1:8000"
    data = {
        "LLM_Template": "Llama_2_Chat_No_End_Token",
        "Username": username,
        "Bot_Name": bot_name,
        "system_prompt": f"You are a sub-agent for an automated webscraping tool. Your task is to decide if the previous Ai sub-agent scraped legible information. The scraped text should contain some form of article, if it does, print 'YES'.  If the webscrape failed or is illegible, print: 'NO'.",
        "prompt": prompt,
        "max_new_tokens": 100,
        "temperature": 0.4,
        "top_p": 0.1,
        "top_k": 20,
        "repetition_penalty": 1.18
    }


    async with aiohttp.ClientSession() as session:
        async with session.post(f"{host}/generate-text/", json=data) as post_response: # POST request to generate text
            if post_response.status == 200:
                post_data = await post_response.json()
                request_id = post_data['request_id']
                # print(f"Request ID: {request_id}")
                max_attempts = 10
                attempts = 0
                delay_seconds = 5  # Delay between each polling attempt
                while attempts < max_attempts:
                    async with session.get(f"{host}/retrieve-text/{request_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            if "generated_text" in get_data:
                                return html.unescape(get_data["generated_text"])
                            await asyncio.sleep(delay_seconds) # If the result is not ready, wait before the next attempt
                        else:
                            return "Failed to retrieve the result."
                    attempts += 1
                return "Max polling attempts reached. Please try again later."
            else:
                return f"Failed to submit the prompt: {post_response.status}"
        
        
async def Agent_Web_Yes_No(prompt, username, bot_name):
    host="http://127.0.0.1:8000"
    data = {
        "LLM_Template": "Llama_2_Chat_No_End_Token",
        "Username": username,
        "Bot_Name": bot_name,
        "system_prompt": f"You are a sub-agent for {bot_name}, an Autonomous AI Chatbot, your task is to determine whether the user's input requires factual data for completion. Please note that information related to {username} and {bot_name}'s memories is handled by another agent and does not need factual verification. If factual data is necessary, respond with 'YES'. Otherwise, respond with 'NO'. Your responses should be limited to either 'YES' or 'NO'.",
        "prompt": prompt,
        "max_new_tokens": 10,
        "temperature": 0.4,
        "top_p": 0.1,
        "top_k": 20,
        "repetition_penalty": 1.18
    }


    async with aiohttp.ClientSession() as session:
        async with session.post(f"{host}/generate-text/", json=data) as post_response: # POST request to generate text
            if post_response.status == 200:
                post_data = await post_response.json()
                request_id = post_data['request_id']
                # print(f"Request ID: {request_id}")
                max_attempts = 10
                attempts = 0
                delay_seconds = 5  # Delay between each polling attempt
                while attempts < max_attempts:
                    async with session.get(f"{host}/retrieve-text/{request_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            if "generated_text" in get_data:
                                return html.unescape(get_data["generated_text"])
                            await asyncio.sleep(delay_seconds) # If the result is not ready, wait before the next attempt
                        else:
                            return "Failed to retrieve the result."
                    attempts += 1
                return "Max polling attempts reached. Please try again later."
            else:
                return f"Failed to submit the prompt: {post_response.status}"
        
       
        
        
async def File_Processor_Call(host, prompt, username, bot_name):
    host="http://127.0.0.1:8000"
    data = {
        "LLM_Template": "Llama_2_Chat_No_End_Token",
        "Username": username,
        "Bot_Name": bot_name,
        "system_prompt": f"You are a summarizer for a text scraping tool. Your task is to take the given file and summarize it without losing any factual data or semantic meaning.",
        "prompt": prompt,
        "max_new_tokens": 600,
        "temperature": 0.85,
        "top_p": 0.2,
        "top_k": 40,
        "repetition_penalty": 1.10
    }


    async with aiohttp.ClientSession() as session:
        async with session.post(f"{host}/generate-text/", json=data) as post_response: # POST request to generate text
            if post_response.status == 200:
                post_data = await post_response.json()
                request_id = post_data['request_id']
                # print(f"Request ID: {request_id}")
                max_attempts = 10
                attempts = 0
                delay_seconds = 5  # Delay between each polling attempt
                while attempts < max_attempts:
                    async with session.get(f"{host}/retrieve-text/{request_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            if "generated_text" in get_data:
                                return html.unescape(get_data["generated_text"])
                            await asyncio.sleep(delay_seconds) # If the result is not ready, wait before the next attempt
                        else:
                            return "Failed to retrieve the result."
                    attempts += 1
                return "Max polling attempts reached. Please try again later."
            else:
                return f"Failed to submit the prompt: {post_response.status}"