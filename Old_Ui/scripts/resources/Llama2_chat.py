import sys
sys.path.insert(0, './scripts')
sys.path.insert(0, './config')
sys.path.insert(0, './config/Chatbot_Prompts')
sys.path.insert(0, './scripts/resources')
import os
import json
import time
from time import time, sleep
import datetime
from uuid import uuid4
import importlib.util
from basic_functions import *
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

# For a locally hosted Oobabooga Client use "http://localhost:5000/api"
# For a Google Colab hosted Oobabooga Client use the given Public Non-Streaming Url:



def open_file(filepath):
    json_file_path = './config/chatbot_settings.json'  # Replace with the actual path to your JSON file
    with open(json_file_path, 'r', encoding='utf-8') as f:
        settings_dict = json.load(f)
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read().strip()

def open_file_first(key):
    json_file_path = './config/chatbot_settings.json'  # Replace with the actual path to your JSON file
    with open(json_file_path, 'r', encoding='utf-8') as f:
        settings_dict = json.load(f)

    content = settings_dict.get(key, '')
    first_host = content.split(' ')[0]
    return first_host

def open_file_second(key):
    json_file_path = './config/chatbot_settings.json'  # Replace with the actual path to your JSON file
    with open(json_file_path, 'r', encoding='utf-8') as f:
        settings_dict = json.load(f)

    content = settings_dict.get(key, '')
    hosts = content.split(' ')
    if len(hosts) >= 2:
        return hosts[1]
    else:
        return hosts[0]

POSITION_FILE = './config/current_position.txt'

def store_position(position):
    json_file_path = './config/chatbot_settings.json'  # Replace with the actual path to your JSON file
    with open(json_file_path, 'r', encoding='utf-8') as f:
        settings_dict = json.load(f)

    with open(POSITION_FILE, 'w') as file:
        file.write(str(position))

def read_position():
    json_file_path = './config/chatbot_settings.json'  # Replace with the actual path to your JSON file
    with open(json_file_path, 'r', encoding='utf-8') as f:
        settings_dict = json.load(f)

    if not os.path.exists('./config'):
        os.makedirs('./config')
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
    json_file_path = './config/chatbot_settings.json'  # Replace with the actual path to your JSON file
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
    json_file_path = './config/chatbot_settings.json'  # Replace with the actual path to your JSON file
    with open(json_file_path, 'r', encoding='utf-8') as f:
        settings_dict = json.load(f)

    content = settings_dict.get(key, '')
    hosts = content.split(' ')
    while True:
        for host in hosts:
            yield host
            
            

            
            
            
            


def oobabooga_terms(prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
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

    response = requests.post(f"{open_file_first('HOST_Oobabooga')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string


def oobabooga_inner_monologue(prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
    history = {'internal': [], 'visible': []}
    temperature = open_file(f'./config/Generation_Settings/Inner_Monologue/temperature.txt')
    top_p = open_file(f'./config/Generation_Settings/Inner_Monologue/top_p.txt')
    rep_pen = open_file(f'./config/Generation_Settings/Inner_Monologue/rep_pen.txt')
    max_tokens = open_file(f'./config/Generation_Settings/Inner_Monologue/max_tokens.txt')
    top_k = open_file(f'./config/Generation_Settings/Inner_Monologue/top_k.txt')
    min_tokens = open_file(f'./config/Generation_Settings/Inner_Monologue/min_tokens.txt')
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

    response = requests.post(f"{open_file_first('HOST_Oobabooga')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def oobabooga_intuition(prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
    history = {'internal': [], 'visible': []}
    temperature = open_file(f'./config/Generation_Settings/Intuition/temperature.txt')
    top_p = open_file(f'./config/Generation_Settings/Intuition/top_p.txt')
    rep_pen = open_file(f'./config/Generation_Settings/Intuition/rep_pen.txt')
    max_tokens = open_file(f'./config/Generation_Settings/Intuition/max_tokens.txt')
    top_k = open_file(f'./config/Generation_Settings/Intuition/top_k.txt')
    min_tokens = open_file(f'./config/Generation_Settings/Intuition/min_tokens.txt')
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

    response = requests.post(f"{open_file_first('HOST_Oobabooga')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        

        
def oobabooga_episodicmem(prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
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

    response = requests.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def oobabooga_flashmem(prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
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

    response = requests.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
        
def oobabooga_implicitmem(prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
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

    response = requests.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def oobabooga_explicitmem(prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
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

    response = requests.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def oobabooga_consolidationmem(prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
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

    response = requests.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
     #   print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def oobabooga_associativemem(prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
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

    response = requests.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
     #   print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string


def oobabooga_250(prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
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

    response = requests.post(f"{open_file_first('HOST_Oobabooga')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string



def oobabooga_500(prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
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

    response = requests.post(f"{open_file_first('HOST_Oobabooga')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
     #   print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def oobabooga_800(prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 800,
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

    response = requests.post(f"{open_file_first('HOST_Oobabooga')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
        
def oobabooga_response(prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
    history = {'internal': [], 'visible': []}
    temperature = open_file(f'./config/Generation_Settings/Response/temperature.txt')
    top_p = open_file(f'./config/Generation_Settings/Response/top_p.txt')
    rep_pen = open_file(f'./config/Generation_Settings/Response/rep_pen.txt')
    max_tokens = open_file(f'./config/Generation_Settings/Response/max_tokens.txt')
    top_k = open_file(f'./config/Generation_Settings/Response/top_k.txt')
    min_tokens = open_file(f'./config/Generation_Settings/Response/min_tokens.txt')
    request = {
        'user_input': prompt,
        'max_new_tokens': max_tokens,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nYou are {bot_name}. You are in the middle of a conversation with your user, {username}. You will do your best to respond naturally in a way that both answer's the user and shows emotional intelligence.\n<</SYS>>",  # Optional
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

    response = requests.post(f"{open_file_first('HOST_Oobabooga')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def oobabooga_auto(prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
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

    response = requests.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
        
def oobabooga_memyesno(prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
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

    response = requests.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
       
def oobabooga_selector(prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
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

    response = requests.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string

        
        
def scrape_oobabooga_scrape(host, prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)   
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
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
    
    response = requests.post(f"{host}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
     #   print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string



def agent_oobabooga_terms(prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
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

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string


def agent_oobabooga_inner_monologue(prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
    history = {'internal': [], 'visible': []}
    temperature = open_file(f'./config/Generation_Settings/Inner_Monologue/temperature.txt')
    top_p = open_file(f'./config/Generation_Settings/Inner_Monologue/top_p.txt')
    rep_pen = open_file(f'./config/Generation_Settings/Inner_Monologue/rep_pen.txt')
    max_tokens = open_file(f'./config/Generation_Settings/Inner_Monologue/max_tokens.txt')
    top_k = open_file(f'./config/Generation_Settings/Inner_Monologue/top_k.txt')
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

    response = requests.post(f"{open_file_first('HOST_Oobabooga')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def agent_oobabooga_intuition(prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
    history = {'internal': [], 'visible': []}
    temperature = open_file(f'./config/Generation_Settings/Intuition/temperature.txt')
    top_p = open_file(f'./config/Generation_Settings/Intuition/top_p.txt')
    rep_pen = open_file(f'./config/Generation_Settings/Intuition/rep_pen.txt')
    max_tokens = open_file(f'./config/Generation_Settings/Intuition/max_tokens.txt')
    top_k = open_file(f'./config/Generation_Settings/Intuition/top_k.txt')
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

    response = requests.post(f"{open_file_first('HOST_Oobabooga')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        

        
def agent_oobabooga_episodicmem(prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
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

    response = requests.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def agent_oobabooga_flashmem(prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
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

    response = requests.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
        
def agent_oobabooga_implicitmem(prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
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

    response = requests.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def agent_oobabooga_explicitmem(prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
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

    response = requests.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def agent_oobabooga_consolidationmem(prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
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

    response = requests.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def agent_oobabooga_associativemem(prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
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

    response = requests.post(f"{open_file_second('HOST_Oobabooga')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string


def agent_oobabooga_250(prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
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

    response = requests.post(f"{open_file_first('HOST_Oobabooga')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string



def agent_oobabooga_500(prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
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

    response = requests.post(f"{open_file_first('HOST_Oobabooga')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def agent_oobabooga_800(prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
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

    response = requests.post(f"{open_file_first('HOST_Oobabooga')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def agent_oobabooga_scrape(prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
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

    response = requests.post(f"{open_file_all('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
         
        
        
def agent_oobabooga_master_tasklist(prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
    history = {'internal': [], 'visible': []}
    temperature = open_file(f'./config/Generation_Settings/Response/temperature.txt')
    top_p = open_file(f'./config/Generation_Settings/Response/top_p.txt')
    rep_pen = open_file(f'./config/Generation_Settings/Response/rep_pen.txt')
    max_tokens = open_file(f'./config/Generation_Settings/Response/max_tokens.txt')
    top_k = open_file(f'./config/Generation_Settings/Response/top_k.txt')
    request = {
        'user_input': prompt,
        'max_new_tokens': 500,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nYou are a stateless task list coordinator for {bot_name}, an autonomous Ai chatbot. Your job is to combine the user's input and the user facing chatbots action plan (with a focus on the user's inquiry), then transform it into a bullet point list of independent research queries for {bot_name}'s response that can be executed by separate AI agents in a cluster computing environment.  These research queries should only be asynchronous informational search requests. Exclude tasks involving final product production, user communication, seeking outside help, seeking external validation, or checking work with other entities.\n<</SYS>>",  # Optional
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

    response = requests.post(f"{open_file_first('HOST_Oobabooga')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def agent_oobabooga_response(prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
    history = {'internal': [], 'visible': []}
    temperature = open_file(f'./config/Generation_Settings/Response/temperature.txt')
    top_p = open_file(f'./config/Generation_Settings/Response/top_p.txt')
    rep_pen = open_file(f'./config/Generation_Settings/Response/rep_pen.txt')
    max_tokens = open_file(f'./config/Generation_Settings/Response/max_tokens.txt')
    top_k = open_file(f'./config/Generation_Settings/Response/top_k.txt')
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

    response = requests.post(f"{open_file_first('HOST_Oobabooga')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def agent_oobabooga_line_response(prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
    history = {'internal': [], 'visible': []}
    temperature = open_file(f'./config/Generation_Settings/Response/temperature.txt')
    top_p = open_file(f'./config/Generation_Settings/Response/top_p.txt')
    rep_pen = open_file(f'./config/Generation_Settings/Response/rep_pen.txt')
    max_tokens = open_file(f'./config/Generation_Settings/Response/max_tokens.txt')
    top_k = open_file(f'./config/Generation_Settings/Response/top_k.txt')
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
    response = requests.post(f"{next_host}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def agent_oobabooga_process_line_response(host, prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
    history = {'internal': [], 'visible': []}
    temperature = open_file(f'./config/Generation_Settings/Response/temperature.txt')
    top_p = open_file(f'./config/Generation_Settings/Response/top_p.txt')
    rep_pen = open_file(f'./config/Generation_Settings/Response/rep_pen.txt')
    max_tokens = open_file(f'./config/Generation_Settings/Response/max_tokens.txt')
    top_k = open_file(f'./config/Generation_Settings/Response/top_k.txt')
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

    response = requests.post(f"{host}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def agent_oobabooga_process_line_response2(host, prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
    history = {'internal': [], 'visible': []}
    temperature = open_file(f'./config/Generation_Settings/Response/temperature.txt')
    top_p = open_file(f'./config/Generation_Settings/Response/top_p.txt')
    rep_pen = open_file(f'./config/Generation_Settings/Response/rep_pen.txt')
    max_tokens = open_file(f'./config/Generation_Settings/Response/max_tokens.txt')
    top_k = open_file(f'./config/Generation_Settings/Response/top_k.txt')
    request = {
        'user_input': prompt,
        'max_new_tokens': 200,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nYour job is to generalize the given task, outlining what kind of tool is needed in order to complete it.  You may only use a single tool.\n<</SYS>>",  # Optional
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

    response = requests.post(f"{host}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def agent_oobabooga_memory_db_check(host, prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
    history = {'internal': [], 'visible': []}
    temperature = open_file(f'./config/Generation_Settings/Response/temperature.txt')
    top_p = open_file(f'./config/Generation_Settings/Response/top_p.txt')
    rep_pen = open_file(f'./config/Generation_Settings/Response/rep_pen.txt')
    max_tokens = open_file(f'./config/Generation_Settings/Response/max_tokens.txt')
    top_k = open_file(f'./config/Generation_Settings/Response/top_k.txt')
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

    response = requests.post(f"{host}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def agent_oobabooga_google_rephrase(host, prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
    history = {'internal': [], 'visible': []}
    temperature = open_file(f'./config/Generation_Settings/Response/temperature.txt')
    top_p = open_file(f'./config/Generation_Settings/Response/top_p.txt')
    rep_pen = open_file(f'./config/Generation_Settings/Response/rep_pen.txt')
    max_tokens = open_file(f'./config/Generation_Settings/Response/max_tokens.txt')
    top_k = open_file(f'./config/Generation_Settings/Response/top_k.txt')
    request = {
        'user_input': prompt,
        'max_new_tokens': max_tokens,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nRephrase the user's inquiry into a google search query. Do not converse with the user or print any text outside of the search query.\n<</SYS>>",  # Optional
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

    response = requests.post(f"{host}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def agent_oobabooga_auto(prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
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

    response = requests.post(f"{open_file_first('HOST_Oobabooga')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
        
def agent_oobabooga_memyesno(prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
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

    response = requests.post(f"{open_file_first('HOST_Oobabooga')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def agent_oobabooga_webcheckyesno(prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
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

    response = requests.post(f"{open_file_first('HOST_Oobabooga')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def agent_oobabooga_webyesno(prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
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

    response = requests.post(f"{open_file_first('HOST_Oobabooga')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
       
def agent_oobabooga_selector(prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
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

    response = requests.post(f"{open_file_first('HOST_Oobabooga')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def File_Processor_oobabooga_scrape(host, prompt):
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
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

    response = requests.post(f"{host}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
     #   print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string