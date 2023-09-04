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

# For a locally hosted Oobabooga Client use "http://localhost:5000/api"
# For a Google Colab hosted Oobabooga Client use the given Public Non-Streaming Url:


def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read().strip()


def oobabooga_terms(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string


def oobabooga_inner_monologue(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def oobabooga_intuition(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'context_instruct': f"[INST] <<SYS>>\nAs {bot_name}, review {username}'s latest message and formulate a specific action plan only if the message involves complex questions or specific tasks. Use third-person perspective to outline this strategy. Avoid creating action plans for simple or casual interactions. Note that no external resources can be used for this task.\n<</SYS>>",  # Optional
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        

        
def oobabooga_episodicmem(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def oobabooga_flashmem(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
        
def oobabooga_implicitmem(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def oobabooga_explicitmem(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def oobabooga_consolidationmem(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
     #   print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def oobabooga_associativemem(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
     #   print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string


def oobabooga_250(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string



def oobabooga_500(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
     #   print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def oobabooga_800(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
        
def oobabooga_response(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def oobabooga_auto(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 3,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nYou are a sub-module of {bot_name}. Your purpose is to rate the given memory on a scale of 1-10. Only print a single number between one and ten.\n<</SYS>>",  # Optional
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
        
def oobabooga_memyesno(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
       
def oobabooga_selector(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string


def scrape_oobabooga_terms(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string


def scrape_oobabooga_inner_monologue(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def scrape_oobabooga_intuition(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'context_instruct': f"[INST] <<SYS>>\nTransmute the user, {username}'s message as {bot_name} by devising a truncated predictive action plan in the third person point of view on how to best respond to {username}'s most recent message. You do not have access to external resources.  Do not create a plan for generic conversation, only on what information is needed to be given.\n<</SYS>>",  # Optional
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        

        
def scrape_oobabooga_episodicmem(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def scrape_oobabooga_flashmem(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
        
def scrape_oobabooga_implicitmem(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def scrape_oobabooga_explicitmem(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def scrape_oobabooga_consolidationmem(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
     #   print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def scrape_oobabooga_associativemem(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
     #   print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string


def scrape_oobabooga_250(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string



def scrape_oobabooga_500(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
     #   print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def scrape_oobabooga_800(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def scrape_oobabooga_scrape(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
     #   print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
        
def scrape_oobabooga_response(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def scrape_oobabooga_auto(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
        
def scrape_oobabooga_memyesno(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
       
def scrape_oobabooga_selector(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string


def agent_oobabooga_terms(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string


def agent_oobabooga_inner_monologue(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def agent_oobabooga_intuition(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'context_instruct': f"[INST] <<SYS>>\nTransmute the user, {username}'s message as {bot_name} by devising a truncated predictive action plan in the third person point of view on how to best respond to {username}'s most recent message.  Do not create a plan for generic conversation, only on what information is needed to be given.\n<</SYS>>",  # Optional
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        

        
def agent_oobabooga_episodicmem(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def agent_oobabooga_flashmem(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
        
def agent_oobabooga_implicitmem(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def agent_oobabooga_explicitmem(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def agent_oobabooga_consolidationmem(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def agent_oobabooga_associativemem(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string


def agent_oobabooga_250(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string



def agent_oobabooga_500(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def agent_oobabooga_800(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def agent_oobabooga_scrape(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
        
def agent_oobabooga_response(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'context_instruct': f"[INST] <<SYS>>\nYou are {bot_name}. You are in the middle of a conversation with the user, {username}. You will do your best to respond naturally in a way that both answers the user's inquiry and shows emotional intelligence.\n<</SYS>>",  # Optional
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def agent_oobabooga_line_response(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def agent_oobabooga_auto(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
        
def agent_oobabooga_memyesno(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def agent_oobabooga_webcheckyesno(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def agent_oobabooga_webyesno(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
       
def agent_oobabooga_selector(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def File_Processor_oobabooga_terms(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string


def File_Processor_oobabooga_inner_monologue(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 350,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nCompose a brief silent soliloquy as {bot_name}'s inner monologue that reflects on {bot_name}'s contemplations in relation on how to respond to the user's most recent message.  Keep the length to one paragraph or shorter.\n<</SYS>>",  # Optional
        'your_name': f'{username}',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_generation_attempts': 1,
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.95,
        'top_p': 0.6,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.25,
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def File_Processor_oobabooga_intuition(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 450,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nCreate a short predictive action plan in third person point of view as {bot_name} based on the user, {username}'s input. This response plan will be directly passed onto the main chatbot system to help plan the response to the user.  The character window is limited to 400 characters, leave out extraneous text to save space.  Please provide the truncated action plan in a tasklist format.  Focus on informational requests, do not get caught in loops of asking for more information.\n<</SYS>>",  # Optional
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
        'top_p': 0.15,
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        

        
def File_Processor_oobabooga_episodicmem(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 250,
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def File_Processor_oobabooga_flashmem(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 250,
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
        
def File_Processor_oobabooga_implicitmem(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 250,
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def File_Processor_oobabooga_explicitmem(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 250,
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def File_Processor_oobabooga_consolidationmem(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
     #   print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def File_Processor_oobabooga_associativemem(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
     #   print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string


def File_Processor_oobabooga_250(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string



def File_Processor_oobabooga_500(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
     #   print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def File_Processor_oobabooga_800(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def File_Processor_oobabooga_scrape(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
     #   print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
        
def File_Processor_oobabooga_response(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
    history = {'internal': [], 'visible': []}
    request = {
        'user_input': prompt,
        'max_new_tokens': 1500,
        'history': history,
        'mode': 'instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'instruction_template': 'Llama-v2',  # Will get autodetected if unset
        'context_instruct': f"[INST] <<SYS>>\nYou are {bot_name}.  Read the given completed tasklist, your inner monologue, action plan, and your memories.  Then, in first-person, generate a single comprehensive response to the user, {username}'s message using the information from the tasklist.\n<</SYS>>",  # Optional
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
        'top_p': 0.9,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.27,
        'repetition_penalty_range': 0,
        'top_k': 40,
        'min_length': 20,
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
def File_Processor_oobabooga_auto(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
        
        
def File_Processor_oobabooga_memyesno(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string
        
       
def File_Processor_oobabooga_selector(prompt):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
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
        'stopping_strings': []
    }

    response = requests.post(f"{open_file('api_keys/HOST_Oobabooga.txt')}/v1/chat", json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        decoded_string = html.unescape(result['visible'][-1][1])
        return decoded_string