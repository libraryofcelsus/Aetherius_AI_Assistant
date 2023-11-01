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
            


async def oobabooga_terms(prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 100,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nYou are a search query coordinator. Your role is to interpret the original user query and generate 2-4 synonymous search terms that will guide the exploration of the chatbot's memory database. Each alternative term should reflect the essence of the user's initial search input. Please list your results using bullet point format. Only print your response using the format: •<search term>\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.75,
        'top_p': 0.4,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.20,
        'top_k': 40,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_first('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
async def oobabooga_domain_selection(prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 30,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nYou are a Knowledge Domain Selector. Your role is to identify the most relevant knowledge domain based on the user's question. Choose only from the provided list and do not create or use any domains outside of it. Your response should be limited to naming the single chosen knowledge domain from the list, do not include anything but the knowledge domain.\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.2,
        'top_p': 0.20,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.00,
        'encoder_repetition_penalty': 1.26,
        'top_k': 20,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_first('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
async def oobabooga_domain_extraction(prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 100,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nYou are a knowledge domain extractor.  Your task is to analyze the given input, then extract the single most salient generalized knowledge domain representative of the input.  Your response should be a single word.\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.75,
        'top_p': 0.4,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.10,
        'top_k': 40,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_first('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
async def oobabooga_input_expansion(prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 100,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nYou are a task rephraser. Your primary task is to rephrase the user's input in a way that ensures it contains the full context needed to know what is asked. Please return the rephrased version of the user’s most recent input.\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.3,
        'top_p': 0.35,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.08,
        'top_k': 25,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_first('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']

        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        


async def oobabooga_inner_monologue(prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    json_file_path = './Aetherius_API/Generation_Settings/Oobabooga/settings.json'
    settings = await read_settings_from_json(json_file_path)
    temperature = settings.get("Inner_Monologue_temperature", "0.70")
    top_p = settings.get("Inner_Monologue_top_p", "0.35")
    rep_pen = settings.get("Inner_Monologue_rep_pen", "1.18")
    max_tokens = settings.get("Inner_Monologue_max_tokens", "350")
    top_k = settings.get("Inner_Monologue_top_k", "45")
    min_tokens = settings.get("Inner_Monologue_min_tokens", "40")
    request = {
        'user_input': prompt,
        'max_new_tokens': max_tokens,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nYou are {bot_name}. Give a brief, first-person, silent soliloquy as your inner monologue that reflects on your contemplations in relation on how to respond to the user, {username}'s most recent message.  Directly print the inner monologue.\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': temperature,
        'top_p': top_p,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': rep_pen,
        'top_k': top_k,
        'min_length': min_tokens,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_first('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']

    #    print(json.dumps(result, indent=4))
        
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
async def oobabooga_intuition(prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    json_file_path = './Aetherius_API/Generation_Settings/Oobabooga/settings.json'
    settings = await read_settings_from_json(json_file_path)
    temperature = settings.get("Intuition_temperature", "0.30")
    top_p = settings.get("Intuition_top_p", "0.20")
    rep_pen = settings.get("Intuition_rep_pen", "1.25")
    max_tokens = settings.get("Intuition_max_tokens", "450")
    top_k = settings.get("Intuition_top_k", "35")
    min_tokens = settings.get("Intuition_min_tokens", "10")
    request = {
        'user_input': prompt,
        'max_new_tokens': max_tokens,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nAs {bot_name}, review {username}'s latest message and decide if an action plan is needed.  Formulate an action plan only if the message involves complex questions or specific tasks. Use third-person perspective to outline this strategy. Avoid creating action plans for simple or casual interactions. Note that no external resources can be used for this task. Provide the action plan in a list format.\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': temperature,
        'top_p': top_p,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': rep_pen,
        'top_k': top_k,
        'min_length': min_tokens,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_first('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        

        
async def oobabooga_episodic_memory(prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 300,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nExtract a single, short and concise third-person episodic memory based on {bot_name}'s final response for upload to a memory database.  You are directly inputing the memories into the database, only print the memory.\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.8,
        'top_p': 0.1,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.18,
        'top_k': 40,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
async def oobabooga_flash_memory(prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 350,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nI will now combine the extracted data to form flashbulb memories in bullet point format, combining associated data. I will only include memories with a strong emotion attached, excluding redundant or irrelevant information.  You are directly inputing the memories into the database, only print the memories.\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.8,
        'top_p': 0.1,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.18,
        'top_k': 40,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
        
async def oobabooga_implicit_memory(prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 350,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nExtract short and concise memories based on {bot_name}'s internal thoughts for upload to a memory database.  These should be executive summaries and will serve as the chatbots implicit memories.  You are directly inputing the memories into the database, only print the memories.  Print the response in the bullet point format: •IMPLICIT MEMORY:<Executive Summary>\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.8,
        'top_p': 0.6,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.18,
        'top_k': 40,
        'min_length': 30,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
async def oobabooga_explicit_memory(prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 350,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nExtract a list of concise explicit memories based on {bot_name}'s final response for upload to a memory database.  These should be executive summaries and will serve as the chatbots explicit memories.  You are directly inputing the memories into the database, only print the memories.  Print the response in the bullet point format: •EXPLICIT MEMORY:<Executive Summary>\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.8,
        'top_p': 0.6,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.18,
        'top_k': 40,
        'min_length': 50,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
async def oobabooga_consolidation_memory(prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 500,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"Read the Log and combine the different associated topics into executive summaries. Each summary should contain the entire context of the memory. Follow the format •Executive Summary",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.5,
        'top_p': 0.1,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.13,
        'top_k': 35,
        'min_length': 100,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
     #   print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
async def oobabooga_associative_memory(prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 500,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"Read the Log and consolidate the different memories in a process allegorical to associative processing. Each new memory should contain the entire context of the original memories. Follow the bullet point format: •<CONSOLIDATED MEMORY>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.5,
        'top_p': 0.1,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.13,
        'top_k': 35,
        'min_length': 100,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
     #   print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string

        
        
async def oobabooga_response(prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    json_file_path = './Aetherius_API/Generation_Settings/Oobabooga/settings.json'
    settings = await read_settings_from_json(json_file_path)
    temperature = settings.get("Response_temperature", "0.8")
    top_p = settings.get("Response_top_p", "0.55")
    rep_pen = settings.get("Response_rep_pen", "1.18")
    max_tokens = settings.get("Response_max_tokens", "1500")
    top_k = settings.get("Response_top_k", "35")
    min_tokens = settings.get("Response_min_tokens", "40")
    request = {
        'user_input': prompt,
        'max_new_tokens': max_tokens,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nYou are {bot_name}. You are in the middle of a conversation with your user, {username}. You will use the given memories to respond naturally in a way that both answer's the user and shows emotional intelligence. You are directly responding to the user.\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': temperature,
        'top_p': top_p,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': rep_pen,
        'top_k': top_k,
        'min_length': min_tokens,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_first('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
async def oobabooga_auto(prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 3,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nYou are a sub-module designed to reflect on the given text.  You are only able to respond with integers on a scale of 1-10, being incapable of printing letters.\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.4,
        'top_p': 0.3,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.25,
        'top_k': 30,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
        
async def oobabooga_memyesno(prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 10,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nYou are a sub-agent for {bot_name}, an Autonomous Ai-Chatbot. Your purpose is to decide if the user's input requires {bot_name}'s past memories to complete. If the user's request pertains to information about the user, the chatbot, {bot_name}, or past personal events should be searched for in memory by printing 'YES'.  If memories are needed, print: 'YES'.  If they are not needed, print: 'NO'. You may only print YES or NO.\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.4,
        'top_p': 0.1,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.18,
        'top_k': 20,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
async def oobabooga_personality_check(prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 10,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nYour job is to decide if the generated implicit memories fit {bot_name}'s personality.  If the generated memories match {bot_name}'s personality, print: 'YES'.  If they do not match the personality or if it contains conflicting information, print: 'NO'.\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.4,
        'top_p': 0.1,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.18,
        'top_k': 20,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
async def oobabooga_personality_gen(prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 500,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nYour task is to cautiously update the personality description for {bot_name}, ensuring it retains strong alignment with the original version. Within a paragraph, weave in only the most critical and relevant new information from {bot_name}'s implicit memories, ensuring that any alterations are subtly and coherently integrated, preserving the essence and integrity of the foundational personality framework.\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.5,
        'top_p': 0.3,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.10,
        'top_k': 20,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
async def oobabooga_user_personality_extraction(prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 500,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nYour job is to extract any salient insights about {username} from their request, the given internal monologue, and {bot_name}'s final response.\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.5,
        'top_p': 0.3,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.10,
        'top_k': 20,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
async def oobabooga_user_personality_gen(prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 500,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nYour task is to cautiously update the personality description for the user, {username}, ensuring it retains strong alignment with the original version. Within a paragraph, weave in only the most critical and relevant new information from the generated memories, ensuring that any alterations are subtly and coherently integrated, preserving the essence and integrity of the foundational personality framework.\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.5,
        'top_p': 0.3,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.10,
        'top_k': 20,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
       
async def oobabooga_selector(prompt, username, bot_name):
    user_bot_path = os.path.join("./Aetherius_API/Chatbot_Prompts", username, bot_name)
    prompts_json_path = os.path.join(user_bot_path, "prompts.json")

    # Read prompts from the JSON file asynchronously
    async with aiofiles.open(prompts_json_path, 'r') as file:
        prompts = json.loads(await file.read())
    main_prompt = prompts["main_prompt"].replace('<<NAME>>', bot_name)
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 10,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"{main_prompt}",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.4,
        'top_p': 0.1,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.18,
        'top_k': 20,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string


async def oobabooga_250(prompt, username, bot_name):
    user_bot_path = os.path.join("./Aetherius_API/Chatbot_Prompts", username, bot_name)
    prompts_json_path = os.path.join(user_bot_path, "prompts.json")

    # Read prompts from the JSON file asynchronously
    async with aiofiles.open(prompts_json_path, 'r') as file:
        prompts = json.loads(await file.read())
    main_prompt = prompts["main_prompt"].replace('<<NAME>>', bot_name)
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 250,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"{main_prompt}",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.8,
        'top_p': 0.2,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.18,
        'top_k': 40,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_first('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
async def scrape_oobabooga_scrape(host, prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 600,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nYou are an ai text summarizer.  Your job is to take the given text from a scraped article, then return the text in a summarized article form.  Do not give any comments or personal statements, only directly return the summarized article, nothing more.\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.4,
        'top_p': 0.1,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.08,
        'top_k': 35,
        'min_length': 100,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    # Load the settings from the JSON file
    
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{host}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
                # print(json.dumps(result, indent=4))
                
                decoded_string = html.unescape(result['visible'][-1][1])
                return decoded_string



async def agent_oobabooga_terms(prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 100,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nYour role is to interpret the original user query and generate 2-5 synonymous search terms in hyphenated bullet point structure that will guide the exploration of the chatbot's memory database. Each alternative term should reflect the essence of the user's initial search input. You are directly inputing your answer into the search query field. Only print the queries.\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.8,
        'top_p': 0.2,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.18,
        'top_k': 40,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    response = requests.post(f"{open_file_first('HOST_Oobabooga')}/v1/chat", json=request)

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_first('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string


async def agent_oobabooga_inner_monologue(prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    json_file_path = './Aetherius_API/Generation_Settings/Oobabooga/settings.json'
    settings = await read_settings_from_json(json_file_path)
    temperature = settings.get("Inner_Monologue_temperature", "0.70")
    top_p = settings.get("Inner_Monologue_top_p", "0.35")
    rep_pen = settings.get("Inner_Monologue_rep_pen", "1.18")
    max_tokens = settings.get("Inner_Monologue_max_tokens", "350")
    top_k = settings.get("Inner_Monologue_top_k", "45")
    min_tokens = settings.get("Inner_Monologue_min_tokens", "40")
    request = {
        'user_input': prompt,
        'max_new_tokens': max_tokens,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nYou are {bot_name}. Give a brief, first-person, silent soliloquy as your inner monologue that reflects on how  the user's most recent message relates to the given external resources.  Directly print the inner monologue.\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': temperature,
        'top_p': top_p,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': rep_pen,
        'top_k': top_k,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_first('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
async def agent_oobabooga_intuition(prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    json_file_path = './Aetherius_API/Generation_Settings/Oobabooga/settings.json'
    settings = await read_settings_from_json(json_file_path)
    temperature = settings.get("Intuition_temperature", "0.30")
    top_p = settings.get("Intuition_top_p", "0.20")
    rep_pen = settings.get("Intuition_rep_pen", "1.25")
    max_tokens = settings.get("Intuition_max_tokens", "450")
    top_k = settings.get("Intuition_top_k", "35")
    min_tokens = settings.get("Intuition_min_tokens", "10")
    request = {
        'user_input': prompt,
        'max_new_tokens': max_tokens,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nFormulate an action plan only if the message involves complex questions or specific tasks. Use third-person perspective to outline this strategy. Avoid creating action plans for simple or casual interactions.\n<</SYS>>",  # Optional  
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': temperature,
        'top_p': top_p,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': rep_pen,
        'top_k': top_k,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_first('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        

        
async def agent_oobabooga_episodicmem(prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 300,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nExtract a single, short and concise third-person episodic memory based on {bot_name}'s final response for upload to a memory database.  You are directly inputing the memories into the database, only print the memory.\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.8,
        'top_p': 0.1,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.18,
        'top_k': 40,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
async def agent_oobabooga_flashmem(prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 350,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nI will now combine the extracted data to form flashbulb memories in bullet point format, combining associated data. I will only include memories with a strong emotion attached, excluding redundant or irrelevant information.  You are directly inputing the memories into the database, only print the memories.\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.8,
        'top_p': 0.1,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.18,
        'top_k': 40,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
        
async def agent_oobabooga_implicitmem(prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 350,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nExtract short and concise memories based on {bot_name}'s internal thoughts for upload to a memory database.  These should be executive summaries and will serve as the chatbots implicit memories.  You are directly inputing the memories into the database, only print the memories.  Use the bullet point format: •IMPLICIT MEMORY\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.8,
        'top_p': 0.1,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.18,
        'top_k': 40,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
async def agent_oobabooga_explicitmem(prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 350,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nExtract short and concise memories based on {bot_name}'s final response for upload to a memory database.  These should be executive summaries and will serve as the chatbots explicit memories.  You are directly inputing the memories into the database, only print the memories.  Use the bullet point format: •EXPLICIT MEMORY\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.8,
        'top_p': 0.1,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.18,
        'top_k': 40,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
async def agent_oobabooga_consolidationmem(prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 500,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"Read the Log and combine the different associated topics into executive summaries. Each summary should contain the entire context of the memory. Follow the format •Executive Summary",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.85,
        'top_p': 0.1,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.18,
        'top_k': 40,
        'min_length': 100,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
async def agent_oobabooga_associativemem(prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 500,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"Read the Log and consolidate the different memories into executive summaries in a process allegorical to associative processing. Each summary should contain the entire context of the memory. Follow the bullet point format: •<EMOTIONAL TAG>: <CONSOLIDATED MEMORY>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.7,
        'top_p': 0.1,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.18,
        'top_k': 40,
        'min_length': 100,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string


async def agent_oobabooga_250(prompt, username, bot_name):
    user_bot_path = os.path.join("./Aetherius_API/Chatbot_Prompts", username, bot_name)
    prompts_json_path = os.path.join(user_bot_path, "prompts.json")

    # Read prompts from the JSON file asynchronously
    async with aiofiles.open(prompts_json_path, 'r') as file:
        prompts = json.loads(await file.read())
    main_prompt = prompts["main_prompt"].replace('<<NAME>>', bot_name)
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 250,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"{main_prompt}",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.8,
        'top_p': 0.2,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.18,
        'top_k': 40,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_first('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string



async def agent_oobabooga_500(prompt, username, bot_name):
    user_bot_path = os.path.join("./Aetherius_API/Chatbot_Prompts", username, bot_name)
    prompts_json_path = os.path.join(user_bot_path, "prompts.json")

    # Read prompts from the JSON file asynchronously
    async with aiofiles.open(prompts_json_path, 'r') as file:
        prompts = json.loads(await file.read())
    main_prompt = prompts["main_prompt"].replace('<<NAME>>', bot_name)
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 500,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"{main_prompt}",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.85,
        'top_p': 0.2,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.18,
        'top_k': 40,
        'min_length': 100,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
async def agent_oobabooga_800(prompt, username, bot_name):
    user_bot_path = os.path.join("./Aetherius_API/Chatbot_Prompts", username, bot_name)
    prompts_json_path = os.path.join(user_bot_path, "prompts.json")

    # Read prompts from the JSON file asynchronously
    async with aiofiles.open(prompts_json_path, 'r') as file:
        prompts = json.loads(await file.read())
    main_prompt = prompts["main_prompt"].replace('<<NAME>>', bot_name)
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 600,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"{main_prompt}",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.85,
        'top_p': 0.2,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.18,
        'top_k': 40,
        'min_length': 100,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
async def agent_oobabooga_scrape(prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 600,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nYou are a summarizer for a webscrape tool. Your task is to take the given webscrape and summarize it without losing any factual data or semantic meaning.\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.7,
        'top_p': 0.3,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.08,
        'top_k': 40,
        'min_length': 100,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_all('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
         
        
        
async def agent_oobabooga_master_tasklist(prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    json_file_path = './Aetherius_API/Generation_Settings/Oobabooga/settings.json'
    settings = await read_settings_from_json(json_file_path)
    temperature = settings.get("Intuition_temperature", "0.30")
    top_p = settings.get("Intuition_top_p", "0.20")
    rep_pen = settings.get("Intuition_rep_pen", "1.25")
    max_tokens = settings.get("Intuition_max_tokens", "450")
    top_k = settings.get("Intuition_top_k", "35")
    min_tokens = settings.get("Intuition_min_tokens", "10")
    request = {
        'user_input': prompt,
        'max_new_tokens': 500,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nAs a task list coordinator for {bot_name}, merge user input and chatbot action plans into 3-6 categorized research tasks for asynchronous execution by isolated AI agents.\nFormat:  [GIVEN CATEGORY]: <TASK>\nUtilize available Tool Categories, focusing on informational searches. Exclude tasks related to product production, external consultations, or inter-agent communications.\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.5,
        'top_p': 30,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.20,
        'top_k': top_k,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_first('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
async def agent_oobabooga_category_reassign(host, prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    json_file_path = './Aetherius_API/Generation_Settings/Oobabooga/settings.json'
    settings = await read_settings_from_json(json_file_path)
    temperature = settings.get("Response_temperature", "0.8")
    top_p = settings.get("Response_top_p", "0.55")
    rep_pen = settings.get("Response_rep_pen", "1.18")
    max_tokens = settings.get("Response_max_tokens", "1500")
    top_k = settings.get("Response_top_k", "35")
    min_tokens = settings.get("Response_min_tokens", "40")
    request = {
        'user_input': prompt,
        'max_new_tokens': 50,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nYou are a sub-module of a category selection tool.  Your task is to take any category that isn't in the original list, and reassign it to an existing category.  The given task should be reprinted exactly how it was.  The assigned category from the task will follow this format: [CATEGORY]: <TASK>\nPlease now return the reassigned category.\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.3,
        'top_p': 0.3,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.10,
        'top_k': 20,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{host}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
                # print(json.dumps(result, indent=4))
                
                decoded_string = html.unescape(result['visible'][-1][1])
                return decoded_string
        
        
        
async def agent_oobabooga_response(prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    json_file_path = './Aetherius_API/Generation_Settings/Oobabooga/settings.json'
    settings = await read_settings_from_json(json_file_path)
    temperature = settings.get("Response_temperature", "0.8")
    top_p = settings.get("Response_top_p", "0.55")
    rep_pen = settings.get("Response_rep_pen", "1.18")
    max_tokens = settings.get("Response_max_tokens", "1500")
    top_k = settings.get("Response_top_k", "35")
    min_tokens = settings.get("Response_min_tokens", "40")
    request = {
        'user_input': prompt,
        'max_new_tokens': max_tokens,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nYou are {bot_name}. You are in the middle of a conversation with the user, {username}. You will do your best to respond naturally in a way that both answers the user's inquiry and shows emotional intelligence.  Compile all necessary context and information from the given external resources and include it in your reply.  Do not expand upon the research or include any of your own knowledge, keeping factual accuracy should be paramount.\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': temperature,
        'top_p': top_p,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': rep_pen,
        'top_k': top_k,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_first('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
async def agent_oobabooga_line_response(prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    json_file_path = './Aetherius_API/Generation_Settings/Oobabooga/settings.json'
    settings = await read_settings_from_json(json_file_path)
    temperature = settings.get("Response_temperature", "0.8")
    top_p = settings.get("Response_top_p", "0.55")
    rep_pen = settings.get("Response_rep_pen", "1.18")
    max_tokens = settings.get("Response_max_tokens", "1500")
    top_k = settings.get("Response_top_k", "35")
    min_tokens = settings.get("Response_min_tokens", "40")
    request = {
        'user_input': prompt,
        'max_new_tokens': max_tokens,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nYou are {bot_name}. You are currently completing an assigned research task by your user. You will do your best to summarize the given information in an easy to read format that doesn't lose any information.\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': temperature,
        'top_p': top_p,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': rep_pen,
        'top_k': top_k,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    next_host = get_next_host('HOST_Oobabooga')
    
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{next_host}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
                # print(json.dumps(result, indent=4))
                
                decoded_string = html.unescape(result['visible'][-1][1])
                return decoded_string

        
async def agent_oobabooga_process_line_response(host, prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    json_file_path = './Aetherius_API/Generation_Settings/Oobabooga/settings.json'
    settings = await read_settings_from_json(json_file_path)
    temperature = settings.get("Response_temperature", "0.8")
    top_p = settings.get("Response_top_p", "0.55")
    rep_pen = settings.get("Response_rep_pen", "1.18")
    max_tokens = settings.get("Response_max_tokens", "1500")
    top_k = settings.get("Response_top_k", "35")
    min_tokens = settings.get("Response_min_tokens", "40")
    request = {
        'user_input': prompt,
        'max_new_tokens': max_tokens,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nYou are {bot_name}. You are currently completing an assigned research task by your user. You will do your best to summarize the given information in an easy to read format that doesn't lose any information.\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': temperature,
        'top_p': top_p,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': rep_pen,
        'top_k': top_k,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{host}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
                # print(json.dumps(result, indent=4))
                
                decoded_string = html.unescape(result['visible'][-1][1])
                return decoded_string
        
        
async def agent_oobabooga_process_line_response2(host, prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    json_file_path = './Aetherius_API/Generation_Settings/Oobabooga/settings.json'
    settings = await read_settings_from_json(json_file_path)
    temperature = settings.get("Response_temperature", "0.8")
    top_p = settings.get("Response_top_p", "0.55")
    rep_pen = settings.get("Response_rep_pen", "1.18")
    max_tokens = settings.get("Response_max_tokens", "1500")
    top_k = settings.get("Response_top_k", "35")
    min_tokens = settings.get("Response_min_tokens", "40")
    request = {
        'user_input': prompt,
        'max_new_tokens': 200,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nReview the provided list of tools carefully. Next, give a general description of the assigned task. From the available tools in the list, identify and select one specific tool that is crucial for completing the task successfully. Ensure that your discussion is focused solely on the tools provided; do not create or suggest the use of tools that are not included in the list, and avoid delving into the reasoning behind your tool choice.\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.5,
        'top_p': 0.3,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.18,
        'top_k': 20,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{host}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
                # print(json.dumps(result, indent=4))
                
                decoded_string = html.unescape(result['visible'][-1][1])
                return decoded_string
        
        
async def agent_oobabooga_memory_db_check(host, prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    json_file_path = './Aetherius_API/Generation_Settings/Oobabooga/settings.json'
    settings = await read_settings_from_json(json_file_path)
    temperature = settings.get("Intuition_temperature", "0.30")
    top_p = settings.get("Intuition_top_p", "0.20")
    rep_pen = settings.get("Intuition_rep_pen", "1.25")
    max_tokens = settings.get("Intuition_max_tokens", "450")
    top_k = settings.get("Intuition_top_k", "35")
    min_tokens = settings.get("Intuition_min_tokens", "10")
    request = {
        'user_input': prompt,
        'max_new_tokens': max_tokens,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nYou are a selection agent for an autonomous AI chatbot.  Your job is to decide if the given database queries contain the needed information to answer the user's inquiry.  Only respond with either 'YES' or 'NO'.\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.4,
        'top_p': .25,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.15,
        'top_k': 20,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{host}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
                # print(json.dumps(result, indent=4))
                
                decoded_string = html.unescape(result['visible'][-1][1])
                return decoded_string
        
        
async def agent_oobabooga_google_rephrase(host, prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    json_file_path = './Aetherius_API/Generation_Settings/Oobabooga/settings.json'
    settings = await read_settings_from_json(json_file_path)
    temperature = settings.get("Intuition_temperature", "0.30")
    top_p = settings.get("Intuition_top_p", "0.20")
    rep_pen = settings.get("Intuition_rep_pen", "1.25")
    max_tokens = settings.get("Intuition_max_tokens", "450")
    top_k = settings.get("Intuition_top_k", "35")
    min_tokens = settings.get("Intuition_min_tokens", "10")
    request = {
        'user_input': prompt,
        'max_new_tokens': 100,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nRephrase the user's inquiry into a google search query. Do not converse with the user or print any text outside of the search query.  The query should only search for the requested information, not anything about the External Resource Module.\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.6,
        'top_p': .5,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.15,
        'top_k': 20,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{host}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
                # print(json.dumps(result, indent=4))
                
                decoded_string = html.unescape(result['visible'][-1][1])
                return decoded_string
        
        
async def agent_oobabooga_auto(prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 2,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nYou are a chatbot memory gate.  Your task is to ensure the chatbot's congruency with the user's inquiry.  Rate the chatbot's outputs on a scale of 1 to 10. You are directly inputing into an answer field, only print the number.\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.1,
        'top_p': 0.25,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.25,
        'top_k': 15,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
        
async def agent_oobabooga_memyesno(prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 10,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nYou are a sub-agent for {bot_name}, an Autonomous Ai-Chatbot. Your purpose is to decide if the user's input requires {bot_name}'s past memories to complete. If the user's request pertains to information about the user, the chatbot, {bot_name}, or past personal events should be searched for in memory by printing 'YES'.  If memories are needed, print: 'YES'.  If they are not needed, print: 'NO'. You may only print YES or NO.\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.4,
        'top_p': 0.1,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.18,
        'top_k': 20,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
async def agent_oobabooga_webcheckyesno(prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 10,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nYou are a sub-agent for an automated webscraping tool. Your task is to decide if the previous Ai sub-agent scraped legible information. The scraped text should contain some form of article, if it does, print 'YES'.  If the webscrape failed or is illegible, print: 'NO'.\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.4,
        'top_p': 0.1,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.18,
        'top_k': 20,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
async def agent_oobabooga_webyesno(prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 10,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nYou are a sub-agent for {bot_name}, an Autonomous AI Chatbot, your task is to determine whether the user's input requires factual data for completion. Please note that information related to {username} and {bot_name}'s memories is handled by another agent and does not need factual verification. If factual data is necessary, respond with 'YES'. Otherwise, respond with 'NO'. Your responses should be limited to either 'YES' or 'NO'.\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.4,
        'top_p': 0.1,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.18,
        'top_k': 20,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
       
async def agent_oobabooga_selector(prompt, username, bot_name):
    user_bot_path = os.path.join("./Aetherius_API/Chatbot_Prompts", username, bot_name)
    prompts_json_path = os.path.join(user_bot_path, "prompts.json")

    # Read prompts from the JSON file asynchronously
    async with aiofiles.open(prompts_json_path, 'r') as file:
        prompts = json.loads(await file.read())
    main_prompt = prompts["main_prompt"].replace('<<NAME>>', bot_name)
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 10,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\n{main_prompt}\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.4,
        'top_p': 0.1,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.18,
        'top_k': 20,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
async def File_Processor_oobabooga_scrape(host, prompt, username, bot_name):
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 600,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nYou are a summarizer for a text scraping tool. Your task is to take the given file and summarize it without losing any factual data or semantic meaning.\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.85,
        'top_p': 0.2,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.10,
        'top_k': 40,
        'min_length': 100,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ['[/']
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{host}/v1/chat", json=request) as response:
            if response.status == 200:
                json_response = await response.json()
                result = json_response['results'][0]['history']
                # print(json.dumps(result, indent=4))
                
                decoded_string = html.unescape(result['visible'][-1][1])
                return decoded_string