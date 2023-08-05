import sys
sys.path.insert(0, './scripts')
sys.path.insert(0, './config')
sys.path.insert(0, './config/Chatbot_Prompts')
sys.path.insert(0, './scripts/resources')
import os
import openai
import json
import time
from time import time, sleep
import datetime
from uuid import uuid4
import requests
from basic_functions import *
from tool_functions import *
import multiprocessing
import threading
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import customtkinter
import tkinter as tk
from tkinter import ttk, scrolledtext, simpledialog, font, messagebox, filedialog
from bs4 import BeautifulSoup
import importlib.util
import requests
from sentence_transformers import SentenceTransformer
import shutil
from concurrent.futures import ThreadPoolExecutor
from PyPDF2 import PdfReader
from ebooklib import epub
import pytesseract
from PIL import Image
from bs4 import BeautifulSoup
import subprocess
from qdrant_client import QdrantClient, models
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, Range
from qdrant_client.http.models import Batch


def check_local_server_running():
    try:
        response = requests.get("http://localhost:6333/dashboard/")
        return response.status_code == 200
    except requests.ConnectionError:
        return False

def open_file(file_path):
    with open(file_path, "r") as file:
        return file.read().strip()

# Check if local server is running
if check_local_server_running():
    client = QdrantClient(url="http://localhost:6333")
    print("Connected to local Qdrant server.")
else:
    url = open_file('./api_keys/qdrant_url.txt')
    api_key = open_file('./api_keys/qdrant_api_key.txt')
    client = QdrantClient(url=url, api_key=api_key)
    print("Connected to cloud Qdrant server.")





# For local streaming, the websockets are hosted without ssl - http://
HOST = 'localhost:5000'
URI = f'http://{HOST}/api/v1/chat'

# For reverse-proxied streaming, the remote will likely host with ssl - https://
# URI = 'https://your-uri-here.trycloudflare.com/api/v1/generate'


model = SentenceTransformer('all-mpnet-base-v2')


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

    response = requests.post(URI, json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
        return result['visible'][-1][1]


def oobabooga_inner_monologue(prompt):
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

    response = requests.post(URI, json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        return result['visible'][-1][1]
        
        
def oobabooga_intuition(prompt):
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

    response = requests.post(URI, json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        return result['visible'][-1][1]
        

        
def oobabooga_episodicmem(prompt):
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

    response = requests.post(URI, json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        return result['visible'][-1][1]
        
        
def oobabooga_flashmem(prompt):
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

    response = requests.post(URI, json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        return result['visible'][-1][1]
        
        
        
def oobabooga_implicitmem(prompt):
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

    response = requests.post(URI, json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        return result['visible'][-1][1]
        
        
def oobabooga_explicitmem(prompt):
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

    response = requests.post(URI, json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        return result['visible'][-1][1]
        
        
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

    response = requests.post(URI, json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
     #   print(result['visible'][-1][1])
        return result['visible'][-1][1]
        
        
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

    response = requests.post(URI, json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
     #   print(result['visible'][-1][1])
        return result['visible'][-1][1]


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

    response = requests.post(URI, json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        return result['visible'][-1][1]



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

    response = requests.post(URI, json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
     #   print(result['visible'][-1][1])
        return result['visible'][-1][1]
        
        
def oobabooga_800(prompt):
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

    response = requests.post(URI, json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        return result['visible'][-1][1]
        
        
def oobabooga_scrape(prompt):
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

    response = requests.post(URI, json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
     #   print(result['visible'][-1][1])
        return result['visible'][-1][1]
        
        
        
def oobabooga_response(prompt):
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

    response = requests.post(URI, json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        return result['visible'][-1][1]
        
        
def oobabooga_auto(prompt):
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

    response = requests.post(URI, json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        return result['visible'][-1][1]
        
        
        
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

    response = requests.post(URI, json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        return result['visible'][-1][1]
        
       
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

    response = requests.post(URI, json=request)

    if response.status_code == 200:
        result = response.json()['results'][0]['history']
    #    print(json.dumps(result, indent=4))
        print()
    #    print(result['visible'][-1][1])
        return result['visible'][-1][1]
        


 # Import functions from script defined in select model
def import_functions_from_script(script_path):
    spec = importlib.util.spec_from_file_location("custom_module", script_path)
    custom_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(custom_module)
    globals().update(vars(custom_module))

def get_script_path_from_file(file_path):
    with open(file_path, 'r') as file:
        script_name = file.read().strip()
    return f'./scripts/resources/{script_name}.py'

# Define the paths to the text file and scripts directory
file_path = './config/model.txt'

# Read the script name from the text file
script_path = get_script_path_from_file(file_path)

# Import the functions from the desired script
import_functions_from_script(script_path)



def set_dark_ancient_theme():
    background_color = "#2B303A"  # Dark blue-gray
    foreground_color = "#FDF7E3"  # Pale yellow
    button_color = "#415A77"  # Dark grayish blue
    text_color = 'white'

    return background_color, foreground_color, button_color, text_color
    
    
def search_implicit_db(line_vec):
    m = multiprocessing.Manager()
    lock = m.Lock()
    username = open_file('./config/prompt_username.txt')
    bot_name = open_file('./config/prompt_bot_name.txt')
    try:
        with lock:
            memories1 = None
            memories2  = None
            try:
                hits = client.search(
                    collection_name=f"Implicit_Long_Term_Memory_Bot_{bot_name}_User_{username}",
                    query_vector=line_vec,
                limit=3)
                    # Print the result
                memories1 = [hit.payload['message'] for hit in hits]
                print(memories1)
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")
        
            try:
                hits = client.search(
                    collection_name=f"Implicit_Short_Term_Memory_Bot_{bot_name}_User_{username}",
                    query_vector=line_vec,
                limit=5)
                    # Print the result
                memories2 = [hit.payload['message'] for hit in hits]
                print(memories2)
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")
            print(memories)
            return memories
    except Exception as e:
        print(e)
        memories = "Error"
        return memories
    
    
def search_episodic_db(line_vec):
    m = multiprocessing.Manager()
    lock = m.Lock()
    username = open_file('./config/prompt_username.txt')
    bot_name = open_file('./config/prompt_bot_name.txt')
    try:
        with lock:
            try:
                hits = client.search(
                    collection_name=f"Episodic_Memory_Bot_{bot_name}_User_{username}",
                    query_vector=line_vec,
                limit=5)
                    # Print the result
                memories = [hit.payload['message'] for hit in hits]
                print(memories)
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")
            return memories
    except Exception as e:
        print(e)
        memories = "Error"
        return memories
            
    
def search_flashbulb_db(line_vec):
    m = multiprocessing.Manager()
    lock = m.Lock()
    username = open_file('./config/prompt_username.txt')
    bot_name = open_file('./config/prompt_bot_name.txt')
    try:
        with lock:
            try:
                hits = client.search(
                    collection_name=f"Flashbulb_Memory_Bot_{bot_name}_User_{username}",
                    query_vector=line_vec,
                limit=2)
                    # Print the result
                memories = [hit.payload['message'] for hit in hits]
                print(memories)
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")
            return memories
    except Exception as e:
        print(e)
        memories = "Error"
        return memories 
    
    
def search_explicit_db(line_vec):
    m = multiprocessing.Manager()
    lock = m.Lock()
    username = open_file('./config/prompt_username.txt')
    bot_name = open_file('./config/prompt_bot_name.txt')
    try:
        with lock:
            try:
                hits = client.search(
                    collection_name=f"Explicit_Long_Term_Memory_Bot_{bot_name}_User_{username}",
                    query_vector=line_vec,
                limit=3)
                    # Print the result
                memories1 = [hit.payload['message'] for hit in hits]
                print(memories1)
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")
        
            try:
                hits = client.search(
                    collection_name=f"Explicit_Short_Term_Memory_Bot_{bot_name}_User_{username}",
                    query_vector=line_vec,
                limit=5)
                    # Print the result
                memories2 = [hit.payload['message'] for hit in hits]
                print(memories2)
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")
            memories = f'{memories1}\n{memories2}'
            print(memories)
            return memories
    except Exception as e:
        print(e)
        memories = "Error"
        return memories   
        
        
def split_into_chunks(text, chunk_size):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]


def chunk_text(text, chunk_size, overlap):
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
    
def open_image_file(image_path):
    try:
        img = Image.open(image_path)
        return img
    except IOError:
        print("Error: File not found or the file format is not supported.")
        return None

def save_text_to_file(text, save_path):
    try:
        with open(save_path, 'w') as file:
            file.write(text)
    except Exception as e:
        print(f"Error occurred while saving text to file: {str(e)}")


def chunk_text_from_file(file_path, chunk_size=600, overlap=80):
    try:
        print("Reading given file, please wait...")
        username = open_file('./config/prompt_username.txt')
        bot_name = open_file('./config/prompt_bot_name.txt')
        pytesseract.pytesseract.tesseract_cmd = '.\\Tesseract-ocr\\tesseract.exe'
        textemp = None
        file_extension = os.path.splitext(file_path)[1].lower() 
        if file_extension == '.txt':
            with open(file_path, 'r') as file:
                texttemp = file.read().replace('\n', ' ').replace('\r', '')
        elif file_extension == '.pdf':
            with open(file_path, 'rb') as file:
                pdf = PdfReader(file)
                texttemp = " ".join(page.extract_text() for page in pdf.pages)
        elif file_extension == '.epub':
            book = epub.read_epub(file_path)
            texts = []
            for item in book.get_items_of_type(9):  # type 9 is XHTML
                soup = BeautifulSoup(item.content, 'html.parser')
                texts.append(soup.get_text())
            texttemp = ' '.join(texts)
        elif file_extension in ['.png', '.jpg', '.jpeg']:
            image = open_image_file(file_path)
            if image is not None:
                texttemp = pytesseract.image_to_string(image).replace('\n', ' ').replace('\r', '')
                # Save OCR output to raw text file
                save_path = './Upload/SCANS/Finished/Raw/' + os.path.basename(file_path) + '.txt'
                save_text_to_file(texttemp, save_path)
        else:
            print(f"Unsupported file type: {file_extension}")
            return []
        texttemp = '\n'.join(line for line in texttemp.splitlines() if line.strip())
        chunks = chunk_text(texttemp, chunk_size, overlap)
        filelist = list()
        # Define the collection name
        collection_name = f"Filescrape_Tool_Bot_{bot_name}_User_{username}"
        try:
            collection_info = client.get_collection(collection_name=collection_name)
            print(collection_info)
        except:
            client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=model.get_sentence_embedding_dimension(), distance=Distance.COSINE),
        )
        
        for chunk in chunks:
            filesum = list()
            filesum.append({'role': 'system', 'content': "You are a Data Summarizer sub-module, responsible for processing text data from files. Your role includes identifying and highlighting significant or factual information. Extraneous data should be discarded, and only essential details must be returned. Stick to the data provided; do not infer or generalize.  Convert lists into a continuous text summary to maintain this format. Present your responses in a Running Text format using the following pattern: [SEMANTIC QUESTION TAG:SUMMARY]. Note that the semantic question tag should be a question that corresponds to the paired information within the summary. Always provide the two together without linebreaks."})
            filesum.append({'role': 'user', 'content': f"TEXT CHUNK: {chunk}"})
            filesum = list()
            filesum.append({'role': 'system', 'content': "MAIN SYSTEM PROMPT: You are an ai text editor.  Your job is to take the given text from a file, then return the scraped text in an informational article form.  Do not generalize, rephrase, or use latent knowledge in your summary.  If no article is given, print no article.\n\n\n"})
            filesum.append({'role': 'user', 'content': f"FILE TEXT: {chunk}\n\nINSTRUCTIONS: Summarize the text scrape without losing any factual knowledge and maintaining full context. The truncated article will be directly uploaded to a Database, leave out extraneous text and personal statements.[/INST]\n\nASSISTANT: Sure! Here's the summary of the file:"})
            prompt = ''.join([message_dict['content'] for message_dict in filesum])
            text = oobabooga_scrape(prompt)
            if len(text) < 20:
                text = "No File available"
            paragraphs = text.split('\n\n')  # Split into paragraphs
            for paragraph in paragraphs:  # Process each paragraph individually, add a check to see if paragraph contained actual information.
                filecheck = list()
                filelist.append(file_path + ' ' + paragraph)
                filecheck.append({'role': 'system', 'content': f"You are an agent for an automated text-processing tool. You are one of many agents in a chain. Your task is to decide if the given text from a file was processed successfully. The processed text should contain factual data or opinions. If the given data only consists of an error message or a single question, skip it.  If the article was processed successfully, print: YES.  If a file-process is not needed, print: NO."})
                filecheck.append({'role': 'user', 'content': f"Is the processed information useful to an end-user? YES/NO: {paragraph}"})
                
            filecheck = list()
            filecheck.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: You are an agent for an automated text scraping tool. Your task is to decide if the previous Ai Agent scraped the text successfully. The scraped text should contain some form of article, if it does, print 'YES'. If the article was scraped successfully, print: 'YES'.  If the text scrape failed or is a response from the first agent, print: 'NO'.\n\n"})
            filecheck.append({'role': 'user', 'content': f"ORIGINAL TEXT FROM SCRAPE: {chunk}\n\n"})
            filecheck.append({'role': 'user', 'content': f"PROCESSED FILE TEXT: {text}\n\n"})
            filecheck.append({'role': 'user', 'content': f"SYSTEM: You are responding for a Yes or No input field. You are only capible of printing Yes or No. Use the format: [AI AGENT: <'Yes'/'No'>][/INST]\n\nASSISTANT:"})
            prompt = ''.join([message_dict['content'] for message_dict in filecheck])
            fileyescheck = oobabooga_selector(prompt)
            
            if 'no file' in text.lower():
                print('---------')
                print('Summarization Failed')
                pass
            if 'no article' in text.lower():
                print('---------')
                print('Summarization Failed')
                pass
            if 'you are a text' in text.lower():
                print('---------')
                print('Summarization Failed')
                pass
            if 'no summary' in text.lower():
                print('---------')
                print('Summarization Failed')
                pass  
            if 'i am an ai' in text.lower():
                print('---------')
                print('Summarization Failed')
                pass                
            else:
                if 'yes' in fileyescheck.lower():
                    semanticterm = list()
                    semanticterm.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: You are a bot responsible for taging articles with a title for database queries.  Your job is to read the given text, then create a title in question form representative of what the article is about.  The title should be semantically identical to the overview of the article and not include extraneous info. Use the format: [<TITLE IN QUESTION FORM>].\n\n"})
                    semanticterm.append({'role': 'user', 'content': f"ARTICLE: {text}\n\n"})
                    semanticterm.append({'role': 'user', 'content': f"SYSTEM: Create a short, single question that encapsulates the semantic meaning of the Article.  Use the format: [<QUESTION TITLE>].  Please only print the title, it will be directly input in front of the article.[/INST]\n\nASSISTANT: Sure! Here's the summary of the given article:"})
                    prompt = ''.join([message_dict['content'] for message_dict in semanticterm])
                    semantic_db_term = oobabooga_scrape(prompt)
            
                    print('---------')
                    filelist.append(file_path + ' ' + paragraph)
                    print(file_path + '\n' + semantic_db_term + '\n' + paragraph)
                    payload = list()
                    timestamp = time()
                    timestring = timestamp_to_datetime(timestamp)
                    # Create the collection only if it doesn't exist

                    vector1 = model.encode([file_path + '\n' + semantic_db_term + '\n' + paragraph])[0].tolist()
                #    embedding = model.encode(query)
                    unique_id = str(uuid4())
                    point_id = unique_id + str(int(timestamp))
                    metadata = {
                        'bot': bot_name,
                        'time': timestamp,
                        'message': file_path + ' ' + paragraph,
                        'timestring': timestring,
                        'uuid': unique_id,
                        'memory_type': 'File_Scrape',
                    }
                    client.upsert(collection_name=collection_name,
                                         points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)]) 
                    payload.clear()           
                    filecheck.clear()        
                    pass  
                else:
                    print('---------')
                    print(f'\n\n\nERROR MESSAGE FROM BOT: {fileyescheck}\n\n\n')                          
        table = filelist
        
        return table
    except Exception as e:
        print(e)
        table = "Error"
        return table  
        
        
            
                      
def process_files_in_directory(directory_path, finished_directory_path, chunk_size=600, overlap=80):
    try:
        files = os.listdir(directory_path)
        files = [f for f in files if os.path.isfile(os.path.join(directory_path, f))]
        with ThreadPoolExecutor() as executor:
            for file in files:
                executor.submit(process_and_move_file, directory_path, finished_directory_path, file, chunk_size, overlap)
    except Exception as e:
        print(e)
        table = "Error"
        return table  


def process_and_move_file(directory_path, finished_directory_path, file, chunk_size, overlap):
    try:
        file_path = os.path.join(directory_path, file)
        chunk_text_from_file(file_path, chunk_size, overlap)
        finished_file_path = os.path.join(finished_directory_path, file)
        shutil.move(file_path, finished_file_path)
    except Exception as e:
        print(e)
        table = "Error"
        return table  
        
# usage - process_files_in_directory('Text_Docs', 'Text_Docs/Finished')
        
        
def load_conversation_file_process_memory(results):
    username = open_file('./config/prompt_username.txt')
    bot_name = open_file('./config/prompt_bot_name.txt')
    try:
        result = list()
        for m in results['matches']:
            info = load_json(f'nexus/file_process_memory_nexus/%s.json' % m['id'])
            result.append(info)
        ordered = sorted(result, key=lambda d: d['time'], reverse=False)  # sort them all chronologically
        messages = [i['message'] for i in ordered]
        return '\n'.join(messages).strip()
    except Exception as e:
        print(e)
        table = "Error"
        return table
        

def fail():
  #  print('')
    fail = "Not Needed"
    return fail
    
    
def search_file_process_db(line):
    m = multiprocessing.Manager()
    lock = m.Lock()
    username = open_file('./config/prompt_username.txt')
    bot_name = open_file('./config/prompt_bot_name.txt')
    try:
        with lock:
            line_vec = model.encode([line])[0].tolist()
            try:
                hits = client.search(
                    collection_name=f"Filescrape_Tool_Bot_{bot_name}_User_{username}",
                    query_vector=line_vec,
                limit=15)
                    # Print the result
                table = [hit.payload['message'] for hit in hits]
                print(table)
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")
            return table
    except Exception as e:
        print(e)
        table = "Error"
        return table



def GPT_4_Text_Extract():
    # # Number of Messages before conversation is summarized, higher number, higher api cost. Change to 3 when using GPT 3.5 due to token usage.
    conv_length = 3
    m = multiprocessing.Manager()
    lock = m.Lock()
    print("Type [Clear Memory] to clear saved short-term memory.")
    print("Type [Exit] to exit without saving.")
    tasklist = list()
    conversation = list()
    int_conversation = list()
    conversation2 = list()
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
    filecheck = list()
    counter = 0
    counter2 = 0
    mem_counter = 0
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
    if not os.path.exists(f'nexus/{bot_name}/{username}/web_scrape_memory_nexus'):
        os.makedirs(f'nexus/{bot_name}/{username}/web_scrape_memory_nexus')
    if not os.path.exists(f'nexus/{bot_name}/{username}/episodic_memory_nexus'):
        os.makedirs(f'nexus/{bot_name}/{username}/episodic_memory_nexus')
    if not os.path.exists('Upload/TXT'):
        os.makedirs('Upload/TXT')
    if not os.path.exists('Upload/TXT/Finished'):
        os.makedirs('Upload/TXT/Finished')
    if not os.path.exists('Upload/PDF'):
        os.makedirs('Upload/PDF')
    if not os.path.exists('Upload/PDF/Finished'):
        os.makedirs('Upload/PDF/Finished')
    if not os.path.exists('Upload/EPUB'):
        os.makedirs('Upload/EPUB')
    if not os.path.exists('Upload/EPUB/Finished'):
        os.makedirs('Upload/EPUB/Finished')
    if not os.path.exists(f'nexus/file_process_memory_nexus'):
        os.makedirs(f'nexus/file_process_memory_nexus')
    if not os.path.exists(f'nexus/{bot_name}/{username}/implicit_short_term_memory_nexus'):
        os.makedirs(f'nexus/{bot_name}/{username}/implicit_short_term_memory_nexus')
    if not os.path.exists(f'nexus/{bot_name}/{username}/explicit_short_term_memory_nexus'):
        os.makedirs(f'nexus/{bot_name}/{username}/explicit_short_term_memory_nexus')
    if not os.path.exists(f'nexus/{bot_name}/{username}/explicit_long_term_memory_nexus'):
        os.makedirs(f'nexus/{bot_name}/{username}/explicit_long_term_memory_nexus')
    if not os.path.exists(f'nexus/{bot_name}/{username}/implicit_long_term_memory_nexus'):
        os.makedirs(f'nexus/{bot_name}/{username}/implicit_long_term_memory_nexus')
    if not os.path.exists(f'nexus/{bot_name}/{username}/episodic_memory_nexus'):
        os.makedirs(f'nexus/{bot_name}/{username}/episodic_memory_nexus')
    if not os.path.exists(f'nexus/{bot_name}/{username}/flashbulb_memory_nexus'):
        os.makedirs(f'nexus/{bot_name}/{username}/flashbulb_memory_nexus')
    if not os.path.exists(f'nexus/{bot_name}/{username}/heuristics_nexus'):
        os.makedirs(f'nexus/{bot_name}/{username}/heuristics_nexus')
    if not os.path.exists(f'nexus/global_heuristics_nexus'):
        os.makedirs(f'nexus/global_heuristics_nexus')
    if not os.path.exists(f'nexus/{bot_name}/{username}/cadence_nexus'):
        os.makedirs(f'nexus/{bot_name}/{username}/cadence_nexus')
    if not os.path.exists(f'logs/{bot_name}/{username}/complete_chat_logs'):
        os.makedirs(f'logs/{bot_name}/{username}/complete_chat_logs')
    if not os.path.exists(f'logs/{bot_name}/{username}/final_response_logs'):
        os.makedirs(f'logs/{bot_name}/{username}/final_response_logs')
    if not os.path.exists(f'logs/{bot_name}/{username}/inner_monologue_logs'):
        os.makedirs(f'logs/{bot_name}/{username}/inner_monologue_logs')
    if not os.path.exists(f'logs/{bot_name}/{username}/intuition_logs'):
        os.makedirs(f'logs/{bot_name}/{username}/intuition_logs')
    if not os.path.exists(f'history/{username}'):
        os.makedirs(f'history/{username}')
    main_prompt = open_file('./config/Chatbot_Prompts/prompt_main.txt').replace('<<NAME>>', bot_name)
    second_prompt = open_file('./config/Chatbot_Prompts/prompt_secondary.txt')
    greeting_msg = open_file('./config/Chatbot_Prompts/prompt_greeting.txt').replace('<<NAME>>', bot_name)
 #   r = sr.Recognizer()
    while True:
        # # Get Timestamp
        timestamp = time()
        timestring = timestamp_to_datetime(timestamp)
        process_files_in_directory('./Upload/SCANS', './Upload/SCANS/Finished')
        process_files_in_directory('./Upload/TXT', './Upload/TXT/Finished')
        process_files_in_directory('./Upload/PDF', './Upload/PDF/Finished')
        process_files_in_directory('./Upload/EPUB', './Upload/EPUB/Finished')
        # # Start or Continue Conversation based on if response exists
        conversation.append({'role': 'system', 'content': '%s' % main_prompt})
        int_conversation.append({'role': 'system', 'content': '%s' % main_prompt})
        if 'response_two' in locals():
            conversation.append({'role': 'user', 'content': a})
            if counter % conv_length == 0:
                print("\nConversation is continued, type [Exit] to clear conversation list.")
                conversation.append({'role': 'assistant', 'content': "%s" % response_two})
            pass
        else:
            conversation.append({'role': 'assistant', 'content': "%s" % greeting_msg})
            print("\n%s" % greeting_msg)
        print('---------')
        return
        
        
def ask_upload_memories(memories, memories2):
    username = open_file('./config/prompt_username.txt')
    bot_name = open_file('./config/prompt_bot_name.txt')
    timestamp = time()
    timestring = timestamp_to_datetime(timestamp)
    payload = list()
    print(f'\nIMPLICIT MEMORIES\n-------------')
    print(memories)
    print(f'\nEXPLICIT MEMORIES\n-------------')
    print(memories2)
    result = messagebox.askyesno("Upload Memories", "Do you want to upload memories?")
    if result:
        # User clicked "Yes"
        lines = memories.splitlines()
        for line in lines:
            if line.strip():
                continue
            else:
                print(line)
                payload = list()
            #    a = input(f'\n\nUSER: ')        
                # Define the collection name
                collection_name = f"Explicit_Short_Term_Memory_Bot_{bot_name}_User_{username}"
                # Create the collection only if it doesn't exist
                try:
                    collection_info = client.get_collection(collection_name=collection_name)
                except:
                    client.create_collection(
                        collection_name=collection_name,
                        vectors_config=models.VectorParams(size=model.get_sentence_embedding_dimension(), distance=Distance.COSINE),
                    )
                vector1 = model.encode([line])[0].tolist()
                unique_id = str(uuid4())
                point_id = unique_id + str(int(timestamp))
                metadata = {
                    'bot': bot_name,
                    'time': timestamp,
                    'message': line,
                    'timestring': timestring,
                    'uuid': unique_id,
                    'user': username,
                    'memory_type': 'Explicit_Short_Term',
                }
                client.upsert(collection_name=collection_name,
                                     points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])   
                payload.clear()
        print('\n\nSYSTEM: Upload Successful!')
                
        print('\n\nSYSTEM: Upload Successful!')
        return 'yes'
    else:
        # User clicked "No"
        print('\n\nSYSTEM: Memories have been Deleted.')
        return 'no'
        
        
        
        
        
class MainConversation:
    def __init__(self, max_entries, prompt, greeting):
        bot_name = open_file('./config/prompt_bot_name.txt')
        username = open_file('./config/prompt_username.txt')
        self.max_entries = max_entries
        self.file_path = f'./history/{username}/{bot_name}_main_conversation_history.json'
        self.main_conversation = [prompt, greeting]

        # Load existing conversation from file
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as f:
                data = json.load(f)
                self.running_conversation = data.get('running_conversation', [])
        else:
            self.running_conversation = []
            
            
    def append(self, timestring, username, a, bot_name, response_two):
        # Append new entry to the running conversation
        entry = []
        entry.append(f"[{timestring}] {username}: {a}")
        entry.append(f"Response: {response_two}\n")
        self.running_conversation.append(entry)
        # Remove oldest entry if conversation length exceeds max entries
        while len(self.running_conversation) > self.max_entries:
            self.running_conversation.pop(0)
        self.save_to_file()


    def save_to_file(self):
        # Combine main conversation and formatted running conversation for saving to file
        data_to_save = {
            'main_conversation': self.main_conversation,
            'running_conversation': self.running_conversation
        }
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=4)
            

    def get_conversation_history(self):
        return self.main_conversation + [message for entry in self.running_conversation for message in entry]
        
    def get_last_entry(self):
        if self.running_conversation:
            return self.running_conversation[-1]
        else:
            return None
        
        
class ChatBotApplication(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        (
            self.background_color,
            self.foreground_color,
            self.button_color,
            self.text_color
        ) = set_dark_ancient_theme()

        self.master = master
        self.master.configure(bg=self.background_color)
        self.master.title('Aetherius Chatbot')
        self.pack(fill="both", expand=True)
        self.create_widgets()

        # Load and display conversation history
        self.display_conversation_history()
        
        
    def bind_enter_key(self):
        self.user_input.bind("<Return>", lambda event: self.send_message())
        
        
    def copy_selected_text(self):
        selected_text = self.conversation_text.get(tk.SEL_FIRST, tk.SEL_LAST)
        self.clipboard_clear()
        self.clipboard_append(selected_text)
        
        
    def show_context_menu(self, event):
        # Create the menu
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Copy", command=self.copy_selected_text)
        # Add more menu items as needed
        
        # Display the menu at the clicked position
        menu.post(event.x_root, event.y_root)
        
        
    def display_conversation_history(self):
        pass
        
        
    def choose_bot_name(self):
        bot_name = simpledialog.askstring("Choose Bot Name", "Type a Bot Name:")
        if bot_name:
            file_path = "./config/prompt_bot_name.txt"
            with open(file_path, 'w') as file:
                file.write(bot_name)
            self.conversation_text.delete("1.0", tk.END)
            self.display_conversation_history()  
        

    def choose_username(self):
        username = simpledialog.askstring("Choose Username", "Type a Username:")
        if username:
            file_path = "./config/prompt_username.txt"
            with open(file_path, 'w') as file:
                file.write(username)
            self.conversation_text.delete("1.0", tk.END)
            self.display_conversation_history()
        pass
        
    def update_results(self, text_widget, url, paragraph):
        self.after(0, text_widget.insert, tk.END, url + ' ' + paragraph)
        self.update()
        
        
    def open_fileprocess_window():
        root = tk.Tk()
        FileProcessWindow(root)
        root.mainloop()

        
    def Edit_Main_Prompt(self):
        file_path = "./config/Chatbot_Prompts/prompt_main.txt"

        with open(file_path, 'r') as file:
            prompt_contents = file.read()

        top = tk.Toplevel(self)
        top.title("Edit Main Prompt")

        prompt_text = tk.Text(top, height=10, width=60)
        prompt_text.insert(tk.END, prompt_contents)
        prompt_text.pack()


        def save_prompt():
            new_prompt = prompt_text.get("1.0", tk.END).strip()
            with open(file_path, 'w') as file:
                file.write(new_prompt)
            self.conversation_text.delete("1.0", tk.END)
            self.display_conversation_history()

        save_button = tk.Button(top, text="Save", command=save_prompt)
        save_button.pack()
        
        
    def Edit_Secondary_Prompt(self):
        file_path = "./config/Chatbot_Prompts/prompt_secondary.txt"
        
        with open(file_path, 'r') as file:
            prompt_contents = file.read()
        
        top = tk.Toplevel(self)
        top.title("Edit Secondary Prompt")
        
        prompt_text = tk.Text(top, height=10, width=60)
        prompt_text.insert(tk.END, prompt_contents)
        prompt_text.pack()
        
        def save_prompt():
            new_prompt = prompt_text.get("1.0", tk.END).strip()
            with open(file_path, 'w') as file:
                file.write(new_prompt)
            self.conversation_text.delete("1.0", tk.END)
            self.display_conversation_history()
        
        save_button = tk.Button(top, text="Save", command=save_prompt)
        save_button.pack()
        
        
    def Edit_Font(self):
        file_path = "./config/font.txt"

        with open(file_path, 'r') as file:
            font_value = file.read()

        fonts = font.families()

        top = tk.Toplevel(self)
        top.title("Edit Font")

        font_listbox = tk.Listbox(top)
        font_listbox.pack()
        for font_name in fonts:
            font_listbox.insert(tk.END, font_name)
            
        label = tk.Label(top, text="Enter the Font Name:")
        label.pack()

        font_entry = tk.Entry(top)
        font_entry.insert(tk.END, font_value)
        font_entry.pack()

        def save_font():
            new_font = font_entry.get()
            if new_font in fonts:
                with open(file_path, 'w') as file:
                    file.write(new_font)
                self.update_font_settings()
            top.destroy()
            
        save_button = tk.Button(top, text="Save", command=save_font)
        save_button.pack()
        

    def Edit_Font_Size(self):
        file_path = "./config/font_size.txt"

        with open(file_path, 'r') as file:
            font_size_value = file.read()

        top = tk.Toplevel(self)
        top.title("Edit Font Size")

        label = tk.Label(top, text="Enter the Font Size:")
        label.pack()

        self.font_size_entry = tk.Entry(top)
        self.font_size_entry.insert(tk.END, font_size_value)
        self.font_size_entry.pack()

        def save_font_size():
            new_font_size = self.font_size_entry.get()
            if new_font_size.isdigit():
                with open(file_path, 'w') as file:
                    file.write(new_font_size)
                self.update_font_settings()
            top.destroy()

        save_button = tk.Button(top, text="Save", command=save_font_size)
        save_button.pack()

        top.mainloop()
        

    def update_font_settings(self):
        font_config = open_file('./config/font.txt')
        font_size = open_file('./config/font_size.txt')
        try:
            font_size_config = int(font_size)
        except:
            font_size_config = 10
        font_style = (f"{font_config}", font_size_config)

        self.conversation_text.configure(font=font_style)
        self.user_input.configure(font=(f"{font_config}", 10))
        
        
    def Model_Selection(self):
        file_path = "./config/model.txt"
        
        with open(file_path, 'r') as file:
            prompt_contents = file.read()
        
        top = tk.Toplevel(self)
        top.title("Select a Model")
        
        models_label = tk.Label(top, text="Available Models: gpt_35, gpt_35_16, gpt_4")
        models_label.pack()
        
        prompt_text = tk.Text(top, height=10, width=60)
        prompt_text.insert(tk.END, prompt_contents)
        prompt_text.pack()
        
        def save_prompt():
            new_prompt = prompt_text.get("1.0", tk.END).strip()
            with open(file_path, 'w') as file:
                file.write(new_prompt)
            self.conversation_text.delete("1.0", tk.END)
            self.display_conversation_history()
        
        save_button = tk.Button(top, text="Save", command=save_prompt)
        save_button.pack()
        
        
    def Edit_Greeting_Prompt(self):
        file_path = "./config/Chatbot_Prompts/prompt_greeting.txt"
        
        with open(file_path, 'r') as file:
            prompt_contents = file.read()
        
        top = tk.Toplevel(self)
        top.title("Edit Greeting Prompt")
        
        prompt_text = tk.Text(top, height=10, width=60)
        prompt_text.insert(tk.END, prompt_contents)
        prompt_text.pack()
        
        def save_prompt():
            new_prompt = prompt_text.get("1.0", tk.END).strip()
            with open(file_path, 'w') as file:
                file.write(new_prompt)
            self.conversation_text.delete("1.0", tk.END)
            self.display_conversation_history()
        
        save_button = tk.Button(top, text="Save", command=save_prompt)
        save_button.pack()
    
        
    def handle_menu_selection(self, event):
        selection = self.menu.get()
        if selection == "Edit Main Prompt":
            self.Edit_Main_Prompt()
        elif selection == "Edit Secondary Prompt":
            self.Edit_Secondary_Prompt()
        elif selection == "Edit Greeting Prompt":
            self.Edit_Greeting_Prompt()
        elif selection == "Edit Font":
            self.Edit_Font()
        elif selection == "Edit Font Size":
            self.Edit_Font_Size()
        elif selection == "Model Selection":
            self.Model_Selection()
            
            
    def handle_login_menu_selection(self, event):
        selection = self.login_menu.get()
        if selection == "Choose Bot Name":
            self.choose_bot_name()
        elif selection == "Choose Username":
            self.choose_username()
            
            
    def delete_conversation_history(self):
        # Delete the conversation history JSON file
        bot_name = open_file('./config/prompt_bot_name.txt')
        username = open_file('./config/prompt_username.txt')
        file_path = f'./history/{username}/{bot_name}_main_conversation_history.json'
        try:
            os.remove(file_path)
            # Reload the script
            self.master.destroy()
            GPT_4_Training()
        except FileNotFoundError:
            pass


    def send_message(self):
        a = self.user_input.get("1.0", tk.END).strip()  # Get all the text from line 1, column 0 to the end.
        self.user_input.delete("1.0", tk.END)  # Clear all the text in the widget.
        self.user_input.config(state=tk.DISABLED)
        self.send_button.config(state=tk.DISABLED)
        self.user_input.unbind("<Return>")
        # Display "Thinking..." in the input field
        self.thinking_label.pack(side="left")
        t = threading.Thread(target=self.process_message, args=(a,))
        t.start()


    def process_message(self, a):
        self.conversation_text.insert(tk.END, f"\nYou: {a}\n\n")
        self.conversation_text.yview(tk.END)
        # Here, we're calling your GPT_4_Training function in a separate thread
        t = threading.Thread(target=self.Tasklist_Inner_Monologue, args=(a,))
        t.start()
        
        
    def open_fileprocess_window(self):
        fileprocess_window = tk.Toplevel(self)
        fileprocess_window.title("File Processing")

        file_label = tk.Label(fileprocess_window, text="Select a file:")
        file_label.pack()

        results_label = tk.Label(fileprocess_window, text="Files to Process:")
        results_label.pack()

        results_text = tk.Text(fileprocess_window)
        results_text.pack()

        # Function to gather and display the list of files in the destination folders
        def display_existing_files():
            destination_folders = ["./Upload/EPUB", "./Upload/PDF", "./Upload/TXT", "./Upload/SCANS"]
            existing_files = []

            for folder in destination_folders:
                if os.path.exists(folder):
                    files = os.listdir(folder)
                    for file in files:
                        if file != "Finished":
                            existing_files.append(file)

            if existing_files:
                results_text.insert(tk.END, "Existing files:\n")
                for file in existing_files:
                    results_text.insert(tk.END, file + "\n")
            else:
                results_text.insert(tk.END, "No existing files.\n")

            results_text.see(tk.END)

        # Call the function to display existing files when the window is launched
        display_existing_files()

        def select_file():
            filetypes = [
                ("Supported Files", "*.epub *.pdf *.txt *.png *.jpg *.jpeg"),
                ("All Files", "*.*")
            ]
            file_path = filedialog.askopenfilename(filetypes=filetypes)
            if file_path:
                process_file(file_path)

        def process_file(file_path):
            file_name = os.path.basename(file_path)
            extension = os.path.splitext(file_name)[1].lower()

            if extension == ".epub":
                destination_folder = "./Upload/EPUB"
            elif extension == ".pdf":
                destination_folder = "./Upload/PDF"
            elif extension == ".txt":
                destination_folder = "./Upload/TXT"
            elif extension in [".png", ".jpg", ".jpeg"]:
                destination_folder = "./Upload/SCANS"
            else:
                update_results(f"Unsupported file type: {extension}")
                return

            destination_path = os.path.join(destination_folder, file_name)

            try:
                shutil.copy2(file_path, destination_path)
                result_text = f"File '{file_name}' copied to {destination_folder}"
                update_results(result_text)
            except IOError as e:
                error_text = f"Error: {e}"
                update_results(error_text)
                
                
        def perform_search():

            def update_results(paragraph):
                # Update the GUI with the new paragraph
                results_text.insert(tk.END, f"{paragraph}\n\n")
                results_text.yview(tk.END)
            #    self.update_results(results_text, paragraph)

            def search_task():
                # Call the modified GPT_4_Tasklist_Web_Search function with the callback
                GPT_4_Text_Extract()

            t = threading.Thread(target=search_task)
            t.start()
                

        def update_results(text):
            results_text.insert(tk.END, text + "\n")
            results_text.see(tk.END)

        file_button = tk.Button(fileprocess_window, text="Browse", command=select_file)
        file_button.pack()

        search_button = tk.Button(fileprocess_window, text="Process", command=perform_search)
        search_button.pack()
        
    def delete_web_history(self):
        bot_name = open_file('./config/prompt_bot_name.txt')
        username = open_file('./config/prompt_username.txt')
        client.delete_collection(collection_name=f"Filescrape_Tool_Bot_{bot_name}_User_{username}")
        print('fileprocess has been Deleted')
        pass
        
        
    def delete_fileprocess_db(self):
        # Delete the conversation history JSON file
        bot_name = open_file('./config/prompt_bot_name.txt')
        username = open_file('./config/prompt_username.txt')
        try:
            client.delete_collection(collection_name=f"Filescrape_Tool_Bot_{bot_name}_User_{username}")
            print('File DB has been Deleted')
            self.master.destroy()
            Qdrant_Llama_v2_File_Process()
        except:
            print("Fail")
            pass
            
            
    def insert_newline_with_space(self, event):
        # Check if the Shift key is pressed and the Enter key is pressed.
        if event.state == 1 and event.keysym == "Return":
            # Insert a newline followed by a space at the current cursor position.
            event.widget.insert(tk.INSERT, "\n ")
            return "break"  # Prevent the default behavior (sending the message). 
            
            
    def create_widgets(self):
        font_config = open_file('./config/font.txt')
        font_size = open_file('./config/font_size.txt')
        try:
            font_size_config = int(font_size)
        except:
            font_size_config = 10
        font_style = (f"{font_config}", font_size_config)
        
        self.top_frame = tk.Frame(self, bg=self.background_color)
        self.top_frame.pack(side=tk.TOP, fill=tk.X)

        self.placeholder_label = tk.Label(self.top_frame, bg=self.background_color)
        self.placeholder_label.pack(side=tk.LEFT, expand=True, fill=tk.X)

        self.login_menu = ttk.Combobox(self.top_frame, values=["Login Menu", "----------------------------", "Choose Bot Name", "Choose Username"], state="readonly")
        self.login_menu.pack(side=tk.LEFT, padx=5, pady=5)
        self.login_menu.current(0)
        self.login_menu.bind("<<ComboboxSelected>>", self.handle_login_menu_selection)
        
        
        self.fileprocess_button = tk.Button(self.top_frame, text="Process Files", command=self.open_fileprocess_window, bg=self.button_color, fg=self.text_color)
        self.fileprocess_button.pack(side=tk.LEFT, padx=5, pady=5, ipadx=10)
        
        self.delete_fileprocess_button = tk.Button(self.top_frame, text="Clear File DB", command=self.delete_fileprocess_db, bg=self.button_color, fg=self.text_color)
        self.delete_fileprocess_button.pack(side=tk.LEFT, padx=5, pady=5, ipadx=10)
        
        self.menu = ttk.Combobox(self.top_frame, values=["Config Menu", "----------------------------", "Model Selection", "Edit Font", "Edit Font Size", "Edit Main Prompt", "Edit Secondary Prompt", "Edit Greeting Prompt"], state="readonly")
        self.menu.pack(side=tk.LEFT, padx=5, pady=5)
        self.menu.current(0)
        self.menu.bind("<<ComboboxSelected>>", self.handle_menu_selection)

        self.placeholder_label = tk.Label(self.top_frame, bg=self.background_color)
        self.placeholder_label.pack(side=tk.RIGHT, expand=True, fill=tk.X)

        # Enables wordwrap and disables input when chatbot is thinking.
        self.conversation_text = tk.Text(self, bg=self.background_color, fg=self.text_color, wrap=tk.WORD)
        self.conversation_text.pack(fill=tk.BOTH, expand=True)
        self.conversation_text.configure(font=font_style)
        self.conversation_text.bind("<Key>", lambda e: "break")  # Disable keyboard input
        self.conversation_text.bind("<Button>", lambda e: "break")  # Disable mouse input

        self.input_frame = tk.Frame(self, bg=self.background_color)
        self.input_frame.pack(fill=tk.X, side="bottom")

        # Set the initial height for the user input Text widget.
        initial_input_height = 5  # Adjust this value as needed.

        self.user_input = tk.Text(self.input_frame, bg=self.background_color, fg=self.text_color, height=initial_input_height, wrap=tk.WORD, yscrollcommand=True)
        self.user_input.configure(font=(f"{font_config}", 10))
        self.user_input.pack(fill=tk.X, expand=True, side="left")
        
        # Bind the new function to handle Shift + Enter event.
        self.user_input.bind("<Shift-Return>", self.insert_newline_with_space)

        # Create a scrollbar for the user input Text widget.
        scrollbar = tk.Scrollbar(self.input_frame, command=self.user_input.yview)
        scrollbar.pack(side="right", fill="y")

        # Attach the scrollbar to the user input Text widget.
        self.user_input.config(yscrollcommand=scrollbar.set)
        
        self.thinking_label = tk.Label(self.input_frame, text="Thinking...")

        self.send_button = tk.Button(self.input_frame, text="Send", command=self.send_message, bg=self.button_color, fg=self.text_color)
        self.send_button.pack(side="right")

        self.grid_columnconfigure(0, weight=1)
        
        self.bind_enter_key()
        self.conversation_text.bind("<1>", lambda event: self.conversation_text.focus_set())
        self.conversation_text.bind("<Button-3>", self.show_context_menu)


    def delete_conversation_history(self):
        # Delete the conversation history JSON file
        bot_name = open_file('./config/prompt_bot_name.txt')
        username = open_file('./config/prompt_username.txt')
        file_path = f'./history/{username}/{bot_name}_main_conversation_history.json'
        try:
            client.delete_collection(collection_name=f"Filescrape_Tool_Bot_{bot_name}_User_{username}")
            print('Webscrape has been Deleted')
            self.master.destroy()
            Qdrant_Llama_v2_File_Process()
        except:
            pass


    def send_message(self):
        a = self.user_input.get("1.0", tk.END).strip()  # Get all the text from line 1, column 0 to the end.
        self.user_input.delete("1.0", tk.END)  # Clear all the text in the widget.
        self.user_input.config(state=tk.DISABLED)
        self.send_button.config(state=tk.DISABLED)
        self.user_input.unbind("<Return>")
        # Display "Thinking..." in the input field
        self.thinking_label.pack(side="left")
        t = threading.Thread(target=self.process_message, args=(a,))
        t.start()


    def process_message(self, a):
        self.conversation_text.insert(tk.END, f"\nYou: {a}\n\n")
        self.conversation_text.yview(tk.END)
        # Here, we're calling your GPT_4_Training function in a separate thread
        t = threading.Thread(target=self.Tasklist_Inner_Monologue, args=(a,))
        t.start()
        
        
    def Tasklist_Inner_Monologue(self, a):
        # # Number of Messages before conversation is summarized, higher number, higher api cost. Change to 3 when using GPT 3.5 due to token usage.
        conv_length = 3
        m = multiprocessing.Manager()
        lock = m.Lock()
        print("Type [Clear Memory] to clear saved short-term memory.")
        print("Type [Exit] to exit without saving.")
        tasklist = list()
        conversation = list()
        int_conversation = list()
        conversation2 = list()
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
        filecheck = list()
        counter = 0
        counter2 = 0
        mem_counter = 0
        bot_name = open_file('./config/prompt_bot_name.txt')
        username = open_file('./config/prompt_username.txt')
        botnameupper = bot_name.upper()
        usernameupper = username.upper()
        main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
        second_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_secondary.txt')
        greeting_msg = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_greeting.txt').replace('<<NAME>>', bot_name)
        if not os.path.exists(f'nexus/{bot_name}/{username}/web_scrape_memory_nexus'):
            os.makedirs(f'nexus/{bot_name}/{username}/web_scrape_memory_nexus')
        if not os.path.exists(f'nexus/{bot_name}/{username}/implicit_short_term_memory_nexus'):
            os.makedirs(f'nexus/{bot_name}/{username}/implicit_short_term_memory_nexus')
        if not os.path.exists(f'nexus/{bot_name}/{username}/explicit_short_term_memory_nexus'):
            os.makedirs(f'nexus/{bot_name}/{username}/explicit_short_term_memory_nexus')
        if not os.path.exists(f'nexus/{bot_name}/{username}/explicit_long_term_memory_nexus'):
            os.makedirs(f'nexus/{bot_name}/{username}/explicit_long_term_memory_nexus')
        if not os.path.exists(f'nexus/{bot_name}/{username}/implicit_long_term_memory_nexus'):
            os.makedirs(f'nexus/{bot_name}/{username}/implicit_long_term_memory_nexus')
        if not os.path.exists(f'nexus/{bot_name}/{username}/episodic_memory_nexus'):
            os.makedirs(f'nexus/{bot_name}/{username}/episodic_memory_nexus')
        if not os.path.exists(f'nexus/{bot_name}/{username}/flashbulb_memory_nexus'):
            os.makedirs(f'nexus/{bot_name}/{username}/flashbulb_memory_nexus')
        if not os.path.exists(f'nexus/{bot_name}/{username}/heuristics_nexus'):
            os.makedirs(f'nexus/{bot_name}/{username}/heuristics_nexus')
        if not os.path.exists(f'nexus/global_heuristics_nexus'):
            os.makedirs(f'nexus/global_heuristics_nexus')
        if not os.path.exists(f'nexus/{bot_name}/{username}/cadence_nexus'):
            os.makedirs(f'nexus/{bot_name}/{username}/cadence_nexus')
        if not os.path.exists(f'logs/{bot_name}/{username}/complete_chat_logs'):
            os.makedirs(f'logs/{bot_name}/{username}/complete_chat_logs')
        if not os.path.exists(f'logs/{bot_name}/{username}/final_response_logs'):
            os.makedirs(f'logs/{bot_name}/{username}/final_response_logs')
        if not os.path.exists(f'logs/{bot_name}/{username}/inner_monologue_logs'):
            os.makedirs(f'logs/{bot_name}/{username}/inner_monologue_logs')
        if not os.path.exists(f'logs/{bot_name}/{username}/intuition_logs'):
            os.makedirs(f'logs/{bot_name}/{username}/intuition_logs')
        if not os.path.exists(f'history/{username}'):
            os.makedirs(f'history/{username}')
     #   r = sr.Recognizer()
        while True:
            # # Get Timestamp
            timestamp = time()
            timestring = timestamp_to_datetime(timestamp)
            # # User Input Voice
        #    yn_voice = input(f'\n\nPress Enter to Speak')
        #    if yn_voice == "":
        #        with sr.Microphone() as source:
        #            print("\nSpeak now")
        #            audio = r.listen(source)
        #            try:
        #                text = r.recognize_google(audio)
        #                print("\nUSER: " + text)
        #            except sr.UnknownValueError:
        #                print("Google Speech Recognition could not understand audio")
        #                print("\nSYSTEM: Press Left Alt to Speak to Aetherius")
        #                break
        #            except sr.RequestError as e:
        #                print("Could not request results from Google Speech Recognition service; {0}".format(e))
        #                break
        #    else:
        #        print('Leave Field Empty')
        #    a = (f'\n\nUSER: {text}') 
            # # User Input Text
       #     a = input(f'\n\nUSER: ')
            message_input = a
            vector_input = model.encode([message_input])[0].tolist()
            # # Check for Commands
            # # Check for "Clear Memory"
            if a == 'Clear Memory':
                while True:
                    print('\n\nSYSTEM: Are you sure you would like to delete saved short-term memory?\n        Press Y for yes or N for no.')
                    user_input = input("'Y' or 'N': ")
                    if user_input == 'y':
                        print('Still needs to be converted to new system')
               #         vdb.delete(delete_all=True, namespace="short_term_memory")
              #          vdb.delete(delete_all=True, namespace="implicit_short_term_memory")
                        while True:
                            print('Short-Term Memory has been Deleted')
                            return
                    elif user_input == 'n':
                        print('\n\nSYSTEM: Short-Term Memory delete cancelled.')
                        return
                else:
                    pass
            # # Check for "Exit"
            if a == 'Exit':
                return
            conversation.append({'role': 'system', 'content': f"MAIN CHATBOT SYSTEM PROMPT: {main_prompt}\n\n"})
            int_conversation.append({'role': 'system', 'content': f"MAIN CHATBOT SYSTEM PROMPT: {main_prompt}\n\n"})
            # # Check for Exit, summarize the conversation, and then upload to episodic_memories
            tasklist.append({'role': 'system', 'content': "SYSTEM: You are a semantic rephraser. Your role is to interpret the original user query and generate 2-3 synonymous search terms that will guide the exploration of the chatbot's memory database. Each alternative term should reflect the essence of the user's initial search input. Please list your results using a hyphenated bullet point structure.\n\n"})
            tasklist.append({'role': 'user', 'content': "USER: USER INQUIRY: %s\n\n" % a})
            tasklist.append({'role': 'assistant', 'content': "TASK COORDINATOR: List of synonymous Semantic Terms:\n"})
            prompt = ''.join([message_dict['content'] for message_dict in tasklist])
            tasklist_output = oobabooga_terms(prompt)
            print(tasklist_output)
            print('-------')
        #    print(tasklist_output)
            lines = tasklist_output.splitlines()
            db_term = {}
            db_term_result = {}
            db_term_result2 = {}
            tasklist_counter = 0
            tasklist_counter2 = 0
            vector_input1 = model.encode([message_input])[0].tolist()
            # # Split bullet points into separate lines to be used as individual queries during a parallel db search     
            for line in lines:            
                try:
                    hits = client.search(
                        collection_name=f"Explicit_Long_Term_Memory_Bot_{bot_name}_User_{username}",
                        query_vector=vector_input1,
                    limit=2)
                    # Print the result
                #    for hit in hits:
                #        print(hit.payload['message'])
                    db_search_16 = [hit.payload['message'] for hit in hits]
                    conversation.append({'role': 'assistant', 'content': f"LONG TERM CHATBOT MEMORIES: {db_search_16}\n"})
                    tasklist_counter + 1
                    if tasklist_counter < 3:
                        int_conversation.append({'role': 'assistant', 'content': f"{botnameupper}'S LONG TERM MEMORIES: {db_search_16}\n"})
                    print(db_search_16)
                    print('done')
                except Exception as e:
                    print(f"An unexpected error occurred: {str(e)}")
                try:
                    hits = client.search(
                        collection_name=f"Implicit_Long_Term_Memory_Bot_{bot_name}_User_{username}",
                        query_vector=vector_input1,
                    limit=1)
                    # Print the result
                #    for hit in hits:
                #        print(hit.payload['message'])
                    db_search_17 = [hit.payload['message'] for hit in hits]
                    conversation.append({'role': 'assistant', 'content': f"LONG TERM CHATBOT MEMORIES: {db_search_17}\n"})
                    tasklist_counter2 + 1
                    if tasklist_counter2 < 3:
                        int_conversation.append({'role': 'assistant', 'content': f"{botnameupper}'S LONG TERM MEMORIES: {db_search_17}\n"})
                    print(db_search_17)
                    print('done')
                except Exception as e:
                    print(f"An unexpected error occurred: {str(e)}")
            print('\n-----------------------\n')
            db_search_1, db_search_2, db_search_3, db_search_14 = None, None, None, None
            try:
                hits = client.search(
                    collection_name=f"Episodic_Memory_Bot_{bot_name}_User_{username}",
                    query_vector=vector_input1,
                limit=5)
                # Print the result
            #    for hit in hits:
            #        print(hit.payload['message'])
                db_search_1 = [hit.payload['message'] for hit in hits]
                print(db_search_1)
                print('done')
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")
            try:
                hits = client.search(
                    collection_name=f"Filescrape_Tool_Bot_{bot_name}_User_{username}",
                    query_vector=vector_input1,
                limit=9)
                # Print the result
            #    for hit in hits:
            #        print(hit.payload['message'])
                db_search_2 = [hit.payload['message'] for hit in hits]
                print(db_search_2)
                print('done')
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")
            try:
                hits = client.search(
                    collection_name=f"Flashbulb_Memory_Bot_{bot_name}_User_{username}",
                    query_vector=vector_input1,
                limit=2)
                # Print the result
            #    for hit in hits:
            #        print(hit.payload['message'])  
                db_search_3 = [hit.payload['message'] for hit in hits]
                print(db_search_3)
                print('done')
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")
            try:
                hits = client.search(
                    collection_name=f"Heuristics_Bot_{bot_name}_User_{username}",
                    query_vector=vector_input1,
                limit=5)
                # Print the result
            #    for hit in hits:
            #        print(hit.payload['message'])
                db_search_14 = [hit.payload['message'] for hit in hits]
                print(db_search_14)
                print('done')
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")
            print('\n-----------------------\n')
                         
            # # Inner Monologue Generation
            conversation.append({'role': 'assistant', 'content': f"{botnameupper}'S EPISODIC MEMORIES: {db_search_1}\n{db_search_3}\n\n{bot_name}'s HEURISTICS: {db_search_14}\n[/INST]\n\n\n[INST]SYSTEM:Compose a short silent soliloquy to serve as {bot_name}'s internal monologue/narrative.  Ensure it includes {bot_name}'s contemplations and emotions in relation to {username}'s request as it pertains to the given text scrape.[/INST]\n\n\n[INST]\n\nTEXT SCRAPE: {db_search_2}[/INST]\n\n\n[INST]\n{usernameupper}/USER: {a}\nPlease provide a short internal monologue contemplating how the user's most recent message relates to the text scrape.[/INST]\n\n{botnameupper}:"})
            
            prompt = ''.join([message_dict['content'] for message_dict in conversation])
            output_one = oobabooga_inner_monologue(prompt)
            print('\n\nINNER_MONOLOGUE: %s' % output_one)
            output_log = f'\nUSER: {a}\n\n{bot_name}: {output_one}'
            # # Clear Conversation List
            conversation.clear()
            self.master.after(0, self.update_tasklist_inner_monologue, output_one)

            # After the operations are complete, call the GPT_4_Intuition function in a separate thread
            t = threading.Thread(target=self.Tasklist_Intuition, args=(a, vector_input, output_one, int_conversation, tasklist_output))
            t.start()
            return
            
            
    def update_tasklist_inner_monologue(self, output_one):
        self.conversation_text.insert(tk.END, f"Inner Monologue: {output_one}\n\n")
        self.conversation_text.yview(tk.END)
        
        
    def Tasklist_Intuition(self, a, vector_input, output_one, int_conversation, tasklist_output):
        my_api_key = open_file('api_keys/key_google.txt')
        my_cse_id = open_file('api_keys/key_google_cse.txt')
        # # Number of Messages before conversation is summarized, higher number, higher api cost. Change to 3 when using GPT 3.5 due to token usage.
        conv_length = 4
        m = multiprocessing.Manager()
        lock = m.Lock()
        tasklist = list()
        conversation = list()
        conversation2 = list()
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
        filecheck = list()
        counter = 0
        counter2 = 0
        mem_counter = 0
        bot_name = open_file('./config/prompt_bot_name.txt')
        username = open_file('./config/prompt_username.txt')
        botnameupper = bot_name.upper()
        usernameupper = username.upper()
        main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
        second_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_secondary.txt')
        greeting_msg = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_greeting.txt').replace('<<NAME>>', bot_name)
        if not os.path.exists(f'nexus/{bot_name}/{username}/web_scrape_memory_nexus'):
            os.makedirs(f'nexus/{bot_name}/{username}/web_scrape_memory_nexus')
     #   r = sr.Recognizer()
        while True:
            # # Get Timestamp
            timestamp = time()
            timestring = timestamp_to_datetime(timestamp)
            message = output_one
            vector_monologue = model.encode(['Inner Monologue: ' + message])[0].tolist()
            # # Memory DB Search
            print('\n-----------------------\n')
            db_search_4, db_search_5, db_search_12, db_search_15 = None, None, None, None
            try:
                hits = client.search(
                    collection_name=f"Episodic_Memory_Bot_{bot_name}_User_{username}",
                    query_vector=vector_monologue,
                limit=5)
                # Print the result
            #    for hit in hits:
            #        print(hit.payload['message'])
                db_search_4 = [hit.payload['message'] for hit in hits]
                print(db_search_4)
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")
            try:
                hits = client.search(
                    collection_name=f"Explicit_Short_Term_Memory_Bot_{bot_name}_User_{username}",
                    query_vector=vector_monologue,
                limit=4)
                # Print the result
            #    for hit in hits:
            #        print(hit.payload['message'])
                db_search_5 = [hit.payload['message'] for hit in hits]
                print(db_search_5)
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")
            try:
                hits = client.search(
                    collection_name=f"Flashbulb_Memory_Bot_{bot_name}_User_{username}",
                    query_vector=vector_monologue,
                limit=2)
                # Print the result
            #    for hit in hits:
            #        print(hit.payload['message'])  
                db_search_12 = [hit.payload['message'] for hit in hits]
                print(db_search_12)
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")
            try:
                hits = client.search(
                    collection_name=f"Heuristics_Bot_{bot_name}_User_{username}",
                    query_vector=vector_monologue,
                limit=3)
                # Print the result
            #    for hit in hits:
            #        print(hit.payload['message'])
                db_search_15 = [hit.payload['message'] for hit in hits]
                print(db_search_15)
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")
                    
                    
                    
                    
                    
            try:
                hits = client.search(
                    collection_name=f"Webscrape_Tool_Bot_{bot_name}_User_{username}",
                    query_vector=vector_monologue,
                limit=9)
                # Print the result
            #    for hit in hits:
            #        print(hit.payload['message'])
                int_scrape = [hit.payload['message'] for hit in hits]
                print(int_scrape)
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")
            # # Intuition Generation
            try:
                hits = client.search(
                    collection_name=f"Filescrape_Tool_Bot_{bot_name}_User_{username}",
                    query_vector=vector_monologue,
                limit=9)
                # Print the result
            #    for hit in hits:
            #        print(hit.payload['message'])
                int_scrape = [hit.payload['message'] for hit in hits]
                print(int_scrape)
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")
            
            int_conversation.append({'role': 'user', 'content': f"USER INPUT: {a}\n\n"})
            int_conversation.append({'role': 'assistant', 'content': f"{botnameupper}'S INFLUENTIAL MEMORIES: {db_search_12}\n\n{botnameupper}'S EXPLICIT MEMORIES: {db_search_5}\n\n{botnameupper}'S HEURISTICS: {db_search_15}\n\n{botnameupper}'S INNER THOUGHTS: {output_one}[/INST]\n\n[INST]TEXT SCRAPE SAMPLE: {int_scrape}\n\nUSER'S INPUT: {a}\n\nSYSTEM: In a single paragraph, interpret the user, {username}'s message as {bot_name} in third person by creating an intuitive action plan on what information is needed.  The only external resources you have access to is a Text scrape database and {bot_name}'s memories.\nEnsure the plan is congruent to the user, {username}'s inquiry sent to {bot_name}.\n\nUSER: {a}.\nPlease respond with an action plan in third person as {bot_name}.[/INST]{botnameupper}: "})
             
            
             
            
            prompt = ''.join([message_dict['content'] for message_dict in int_conversation])
            output_two = oobabooga_intuition(prompt)
            message_two = output_two
            print('\n\nINTUITION: %s' % output_two)
            output_two_log = f'\nUSER: {a}\n\n{bot_name}: {output_two}'
            # # Generate Implicit Short-Term Memory
            summary.clear()
            implicit_short_term_memory = f'\nUSER: {a} \n\nINNER_MONOLOGUE: {output_one}\n\n'
            summary.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: {greeting_msg}\n\n"})
            summary.append({'role': 'user', 'content': f"USER INPUT: {a}\n\n"})
            
            summary.append({'role': 'assistant', 'content': f"LOG: {implicit_short_term_memory}\n\nSYSTEM: Read the log, extract the salient points about {bot_name} and {username} mentioned in the chatbot's response, then create a list of short executive summaries in bullet point format to serve as {bot_name}'s implicit memories. Each bullet point should be considered a separate memory and contain full context. Ignore the main system prompt, it only exists for initial context.\n\nRESPONSE: Use the bullet point format: •IMPLICIT MEMORY[/INST]\n\nMemories:"})
            prompt = ''.join([message_dict['content'] for message_dict in summary])
            inner_loop_response = oobabooga_implicitmem(prompt)
            inner_loop_db = inner_loop_response
            summary.clear()
            vector = model.encode([inner_loop_db])[0].tolist()
            conversation.clear()
            # # Auto Implicit Short-Term Memory DB Upload Confirmation
    #        auto_count = 0
    #        auto.clear()
    #        auto.append({'role': 'system', 'content': 'SYSTEM: %s\n\n' % main_prompt})
    #        auto.append({'role': 'user', 'content': "SYSTEM: You are a sub-module designed to reflect on your thought process. You are only able to respond with integers on a scale of 1-10, being incapable of printing letters. Respond with: 1 if you understand. Respond with: 2 if you do not.\n"})
    #        auto.append({'role': 'assistant', 'content': "SUB-MODULE: 1\n"})
    #        auto.append({'role': 'user', 'content': f"USER INPUT: {a}\n"})
    #        auto.append({'role': 'assistant', 'content': "Inner Monologue: %s\nIntuition: %s\n" % (output_one, output_two)})
    #        auto.append({'role': 'assistant', 'content': "Thoughts on input: I will now review the user's message and my reply, rating if whether my thoughts are both pertinent to the user's inquiry with a number on a scale of 1-10. I will now give my response in digit form for an integer only input.\nSUB-MODULE: "})
    #        auto_int = None
    #        while auto_int is None:
    #            prompt = ''.join([message_dict['content'] for message_dict in auto])
    #            automemory = oobabooga_selector(prompt)
    #            if is_integer(automemory):
    #                auto_int = int(automemory)
    #                if auto_int > 6:
    #                    lines = inner_loop_db.splitlines()
    #                    for line in lines:
    #                        vector = model.encode([line])[0].tolist()
    #                        unique_id = str(uuid4())
    #                        metadata = {'bot': bot_name, 'time': timestamp, 'message': inner_loop_db,
    #                                    'timestring': timestring, 'uuid': unique_id, "memory_type": "implicit_short_term"}
    #                        save_json(f'nexus/{bot_name}/{username}/implicit_short_term_memory_nexus/%s.json' % unique_id, metadata)
    #                        payload.append((unique_id, vector, {"memory_type": "implicit_short_term"}))
    #                        vdb.upsert(payload, namespace=f'short_term_memory_User_{username}_Bot_{bot_name}')
    #                        payload.clear()
    #                    print('\n\nSYSTEM: Auto-memory upload Successful!')
    #                    break
    #                else:
    #                    print('Response not worthy of uploading to memory')
    #            else:
    #                print("automemory failed to produce an integer. Retrying...")
    #                auto_int = None
    #                auto_count += 1
    #                if auto_count > 2:
    #                    print('Auto Memory Failed')
    #                    break
    #        else:
    #            pass                  
            # After the operations are complete, call the response generation function in a separate thread
            t = threading.Thread(target=self.Tasklist_Response, args=(a, vector_input, vector_monologue, output_one, output_two, inner_loop_db))
            t.start()
            return  


    def update_tasklist_intuition(self, output_two):
        self.conversation_text.insert(tk.END, f"Intuition: {output_two}\n\nSearching DBs and Generating Final Response\nPlease Wait...\n\n")
        self.conversation_text.yview(tk.END)
        
        
    def Tasklist_Response(self, a, vector_input, vector_monologue, output_one, output_two, inner_loop_db):
        my_api_key = open_file('api_keys/key_google.txt')
        my_cse_id = open_file('api_keys/key_google_cse.txt')
        # # Number of Messages before conversation is summarized, higher number, higher api cost. Change to 3 when using GPT 3.5 due to token usage.
        conv_length = 4
        m = multiprocessing.Manager()
        lock = m.Lock()
        tasklist = list()
        conversation = list()
        conversation2 = list()
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
        filecheck = list()
        counter = 0
        counter2 = 0
        mem_counter = 0
        bot_name = open_file('./config/prompt_bot_name.txt')
        username = open_file('./config/prompt_username.txt')
        botnameupper = bot_name.upper()
        usernameupper = username.upper()
        main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
        second_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_secondary.txt')
        greeting_msg = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_greeting.txt').replace('<<NAME>>', bot_name)
        if not os.path.exists(f'nexus/{bot_name}/{username}/web_scrape_memory_nexus'):
            os.makedirs(f'nexus/{bot_name}/{username}/web_scrape_memory_nexus')
     #   r = sr.Recognizer()
        while True:
            # # Get Timestamp
            timestamp = time()
            timestring = timestamp_to_datetime(timestamp)
            # # Test for basic Autonomous Tasklist Generation and Task Completion
            master_tasklist.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: You are a stateless task list coordinator for {bot_name} an autonomous Ai chatbot. Your job is to combine the user's input and the user facing chatbots intuitive action plan, then transform it into a list of independent research queries for {bot_name}'s response that can be executed by separate AI agents in a cluster computing environment. The other asynchronous Ai agents are stateless and cannot communicate with each other or the user during task execution, however the agents do have access to {bot_name}'s memories. Exclude tasks involving final product production, user communication, using external resources, or checking work with other entities. Respond using bullet point format following: '-[task]\n-[task]\n-[task]'\n\n"})
            master_tasklist.append({'role': 'user', 'content': f"USER FACING CHATBOT'S INTUITIVE ACTION PLAN: {output_two}\n\n"})
            master_tasklist.append({'role': 'user', 'content': f"USER INQUIRY: {a}\n\n"})
            master_tasklist.append({'role': 'assistant', 'content': f"RESPONSE FORMAT: You may only print the list in hyphenated bullet point format. Use the format: '-[task]\n-[task]\n-[task]'[/INST]\n\nASSISTANT:"})
            
            prompt = ''.join([message_dict['content'] for message_dict in master_tasklist])
            master_tasklist_output = oobabooga_500(prompt)
            print('-------\nMaster Tasklist:')
            print(master_tasklist_output)
            tasklist_completion.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: {main_prompt}\n\n"})
            tasklist_completion.append({'role': 'assistant', 'content': f"You are the final response module for the cluster compute Ai-Chatbot {bot_name}. Your job is to take the completed task list, and then give a verbose response to the end user in accordance with their initial request.[/INST]\n\n"})
            tasklist_completion.append({'role': 'user', 'content': f"[INST]FULL TASKLIST: {master_tasklist_output}\n\n"})
            task = {}
            task_result = {}
            task_result2 = {}
            task_counter = 1
            # # Split bullet points into separate lines to be used as individual queries
            try:
                lines = master_tasklist_output.splitlines()
            except:
                line = master_tasklist_output
        #    print('\n\nSYSTEM: Would you like to autonomously complete this task list?\n        Press Y for yes or N for no.')
        #    user_input = input("'Y' or 'N': ")
         #   if user_input == 'y':
            try:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    futures = [
                        executor.submit(
                            process_line, 
                            line, task_counter, memcheck.copy(), memcheck2.copy(), filecheck.copy(), conversation.copy(), [], tasklist_log, output_one, master_tasklist_output, a
                        )
                        for task_counter, line in enumerate(lines) if line != "None"
                    ]

                    for future in concurrent.futures.as_completed(futures):
                        tasklist_completion.extend(future.result())
                tasklist_completion.append({'role': 'assistant', 'content': f"%{botnameupper}'S INNER_MONOLOGUE: {output_one}\n\n"})
        #        tasklist_completion.append({'role': 'user', 'content': f"%{bot_name}'s INTUITION%\n{output_two}\n\n"})
                tasklist_completion.append({'role': 'user', 'content': f"[/INST]\n[INST]SYSTEM: Read the given set of tasks and completed responses and convert them into a verbose response for {username}, the end user in accordance with their request. {username} is both unaware and unable to see any of your research so any nessisary context or information must be relayed.\n\nUSER'S INITIAL INPUT: {a}.\n\nRESPONSE FORMAT: Your planning and research is now done. You will now give a verbose and natural sounding response ensuring the user's request is fully completed in entirety. Follow the format: [{bot_name}: <FULL RESPONSE TO USER>][/INST]\n\nUSER: {a}\n\n{botnameupper}:"})
                print('\n\nGenerating Final Output...')
                prompt = ''.join([message_dict['content'] for message_dict in tasklist_completion])
                response_two = oobabooga_response(prompt)
                print('\nFINAL OUTPUT:\n%s' % response_two)
                complete_message = f'\nUSER: {a}\n\nINNER_MONOLOGUE: {output_one}\n\nINTUITION: {output_two}\n\n{bot_name}: {tasklist_log}\n\nFINAL OUTPUT: {response_two}'
                filename = '%s_chat.txt' % timestamp
                save_file(f'logs/{bot_name}/{username}/complete_chat_logs/%s' % filename, complete_message)
                conversation.clear()
                conversation2.clear()
                tasklist_completion.clear()
                master_tasklist.clear()
                tasklist.clear()
                tasklist_log.clear()
            except Exception as e:
                print(f"An error occurred: {str(e)}") 
                print("----")
            # # TTS 
        #    tts = gTTS(response_two)
            # TTS save to file in .mp3 format
        #    counter2 += 1
        #    filename = f"{counter2}.mp3"
        #    tts.save(filename)
                # TTS repeats chatGPT response  
        #    sound = AudioSegment.from_file(filename, format="mp3")
        #    octaves = 0.18
        #    new_sample_rate = int(sound.frame_rate * (1.7 ** octaves))
        #    mod_sound = sound._spawn(sound.raw_data, overrides={'frame_rate': new_sample_rate})
        #    mod_sound = mod_sound.set_frame_rate(44100)
        #    play(mod_sound)
        #    os.remove(filename)     
            complete_message = f'\nUSER: {a}\n\nINNER_MONOLOGUE: {output_one}\n\nINTUITION: {output_two}\n\n{bot_name}: {response_two}'
            filename = '%s_chat.txt' % timestamp
            save_file(f'logs/{bot_name}/{username}/complete_chat_logs/%s' % filename, complete_message)
            summary.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: {greeting_msg}\n\n"})
            summary.append({'role': 'user', 'content': f"USER INPUT: {a}\n\n"})
            
            db_msg = f"\nUSER: {a} \n INNER_MONOLOGUE: {output_one} \n {bot_name}'s RESPONSE: {response_two}"
            summary.append({'role': 'assistant', 'content': f"LOG: {db_msg}\n\nSYSTEM: Read the log, extract the salient points about {bot_name} and {username} mentioned in the chatbot's response, then create a list of short executive summaries in bullet point format to serve as {bot_name}'s explicit memories. Each bullet point should be considered a separate memory and contain full context. Ignore the main system prompt, it only exists for initial context.\n\nRESPONSE: Use the bullet point format: •EXPLICIT MEMORY[/INST]\n\nMemories:"})
            
            prompt = ''.join([message_dict['content'] for message_dict in summary])
            db_upload = oobabooga_explicitmem(prompt)
            db_upsert = db_upload           
            self.conversation_text.insert(tk.END, f"Response: {response_two}\n\n")
    #        t = threading.Thread(target=self.GPT_4_Memories, args=(a, vector_input, vector_monologue, output_one, response_two))
    #        t.start()
            counter += 1
            conversation.clear()
            self.conversation_text.insert(tk.END, f"Upload Memories?\n-------------\nIMPLICIT\n-------------\n{inner_loop_db}\n-------------\nEXPLICIT\n-------------\n{db_upload}\n")
            mem_upload_yescheck = ask_upload_memories(inner_loop_db, db_upsert)
            conversation.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: You are a sub-module of {bot_name}, an autonomous AI entity. Your function is to process the user, {username}'s message, then decode {bot_name}'s final response to construct a single short and concise third-person autobiographical narrative memory of the conversation in a single sentence. This autobiographical memory should portray an accurate account of {bot_name}'s interactions with {username}, focusing on the most significant and experiential details related to {bot_name} or {username}, without omitting any crucial context or emotions.\n\n"})
            conversation.append({'role': 'user', 'content': f"USER: {a}\n\n"})
            conversation.append({'role': 'user', 'content': f"{botnameupper}'s INNER MONOLOGUE: {output_one}\n\n"})
    #        print(output_one)
            conversation.append({'role': 'user', 'content': f"{botnameupper}'S FINAL RESPONSE: {response_two}[/INST]\n\n"})
    #        print(response_two)
            conversation.append({'role': 'assistant', 'content': f"THIRD-PERSON AUTOBIOGRAPHICAL MEMORY:"})
            if mem_upload_yescheck == "yes":
                t = threading.Thread(target=self.GPT_Memories, args=(a, vector_input, vector_monologue, output_one, response_two))
                t.start()
            self.conversation_text.yview(tk.END)
            self.user_input.delete(0, tk.END)
            self.user_input.focus()
            self.user_input.config(state=tk.NORMAL)
            self.send_button.config(state=tk.NORMAL)
            self.thinking_label.pack_forget()
        #    self.user_input.delete(0, tk.END)
            self.bind_enter_key()
            return
            
            
    def GPT_Memories(self, a, vector_input, vector_monologue, output_one, response_two):
        # # Number of Messages before conversation is summarized, higher number, higher api cost. Change to 3 when using GPT 3.5 due to token usage.
        m = multiprocessing.Manager()
        lock = m.Lock()
        conversation = list()
        conversation2 = list()
        summary = list()
        auto = list()
        payload = list()
        consolidation  = list()
        counter = 0
        counter2 = 0
        mem_counter = 0
        length_config = open_file('./config/Conversation_Length.txt')
        conv_length = 3
        bot_name = open_file('./config/prompt_bot_name.txt')
        username = open_file('./config/prompt_username.txt')
        botnameupper = bot_name.upper()
        usernameupper = username.upper()
        main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
        second_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_secondary.txt')
        greeting_msg = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_greeting.txt').replace('<<NAME>>', bot_name)
    #   r = sr.Recognizer()
        while True:
            # # Get Timestamp
            timestamp = time()
            timestring = timestamp_to_datetime(timestamp)
            counter += 1
            conversation.clear()
            print('Generating Episodic Memories')
            conversation.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: You are a sub-module of {bot_name}, an autonomous AI entity. Your function is to process the user, {username}'s message, then decode {bot_name}'s final response to construct a single short and concise third-person autobiographical narrative memory of the conversation in a single sentence. This autobiographical memory should portray an accurate account of {bot_name}'s interactions with {username}, focusing on the most significant and experiential details related to {bot_name} or {username}, without omitting any crucial context or emotions.\n\n"})
            conversation.append({'role': 'user', 'content': f"USER: {a}\n\n"})
            conversation.append({'role': 'user', 'content': f"{botnameupper}'s INNER MONOLOGUE: {output_one}\n\n"})
    #        print(output_one)
            conversation.append({'role': 'user', 'content': f"{botnameupper}'S FINAL RESPONSE: {response_two}[/INST]\n\n"})
    #        print(response_two)
            conversation.append({'role': 'assistant', 'content': f"THIRD-PERSON AUTOBIOGRAPHICAL MEMORY:"})
            prompt = ''.join([message_dict['content'] for message_dict in conversation])
            conv_summary = oobabooga_episodicmem(prompt)
            print(conv_summary)
            print('\n-----------------------\n')
        #    self.conversation_text.insert(tk.END, f"Upload Memories?\n{conv_summary}\n\n")
        #    ask_upload_episodic_memories(conv_summary)
            # Define the collection name
            collection_name = f"Episodic_Memory_Bot_{bot_name}_User_{username}"
            # Create the collection only if it doesn't exist
            try:
                collection_info = client.get_collection(collection_name=collection_name)
            except:
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(size=model.get_sentence_embedding_dimension(), distance=Distance.COSINE),
                )
            vector1 = model.encode([timestring + '-' + conv_summary])[0].tolist()
            unique_id = str(uuid4())
            metadata = {
                'bot': bot_name,
                'time': timestamp,
                'message': timestring + '-' + conv_summary,
                'timestring': timestring,
                'uuid': unique_id,
                'memory_type': 'Episodic',
            }
            client.upsert(collection_name=collection_name,
                                 points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])   
            payload.clear()
            
            
            collection_name = f"Flash_Counter_Bot_{bot_name}_User_{username}"
            # Create the collection only if it doesn't exist
            try:
                collection_info = client.get_collection(collection_name=collection_name)
            except:
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(size=model.get_sentence_embedding_dimension(), distance=Distance.COSINE),
                )
            vector1 = model.encode([timestring + '-' + conv_summary])[0].tolist()
            unique_id = str(uuid4())
            metadata = {
                'bot': bot_name,
                'time': timestamp,
                'message': timestring + '-' + conv_summary,
                'timestring': timestring,
                'uuid': unique_id,
                'memory_type': 'Episodic',
            }
            client.upsert(collection_name=collection_name,
                                 points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])   
            payload.clear()

            # # Flashbulb Memory Generation
            collection_name = f"Flash_Counter_Bot_{bot_name}_User_{username}"
            collection_info = client.get_collection(collection_name=collection_name)
            if collection_info.vectors_count > 7:
                flash_db = None
                try:
                    hits = client.search(
                        collection_name=f"Episodic_Memory_Bot_{bot_name}_User_{username}",
                        query_vector=vector_input,
                    limit=5)
                    # Print the result
                #    for hit in hits:
                #        print(hit.payload['message'])
                    flash_db = [hit.payload['message'] for hit in hits]
                    print(flash_db)
                except Exception as e:
                    print(f"An unexpected error occurred: {str(e)}")
                    
                flash_db1 = None
                try:
                    hits = client.search(
                        collection_name=f"Implicit_Long_Term_Memory_Bot_{bot_name}_User_{username}",
                        query_vector=vector_monologue,
                    limit=8)
                    # Print the result
                #    for hit in hits:
                #        print(hit.payload['message'])
                    flash_db1 = [hit.payload['message'] for hit in hits]
                    print(flash_db1)
                except Exception as e:
                    print(f"An unexpected error occurred: {str(e)}")
                print('\n-----------------------\n')
                # # Generate Implicit Short-Term Memory
                consolidation.append({'role': 'system', 'content': f"Main System Prompt: You are a data extractor. Your job is read the given episodic memories, then extract the appropriate emotional responses from the given emotional reactions.  You will then combine them into a single combined memory.[/INST]\n\n"})
                consolidation.append({'role': 'user', 'content': f"[INST]EMOTIONAL REACTIONS: {flash_db}\n\nFIRST INSTRUCTION: Read the following episodic memories, then go back to the given emotional reactions and extract the corresponding emotional information tied to each memory.\nEPISODIC MEMORIES: {flash_db1}[/INST]\n\n"})
                consolidation.append({'role': 'assistant', 'content': "[INST]SECOND INSTRUCTION: I will now combine the extracted data to form flashbulb memories in bullet point format, combining associated data. I will only include memories with a strong emotion attached, excluding redundant or irrelevant information.\n"})
                consolidation.append({'role': 'user', 'content': "FORMAT: Use the format: •{given Date and Time}-{emotion}: {Flashbulb Memory}[/INST]\n\n"})
                consolidation.append({'role': 'assistant', 'content': f"RESPONSE: I will now create {bot_name}'s flashbulb memories using the given format above.\n{bot_name}: "})
                prompt = ''.join([message_dict['content'] for message_dict in consolidation])
                flash_response = oobabooga_flashmem(prompt)
                print(flash_response)
                print('\n-----------------------\n')
            #    memories = results
                lines = flash_response.splitlines()
                for line in lines:
                    if line.strip() == '':  # This condition checks for blank lines
                        continue
                    else:
                        # Define the collection name
                        collection_name = f"Flashbulb_Memory_Bot_{bot_name}_User_{username}"
                        # Create the collection only if it doesn't exist
                        try:
                            collection_info = client.get_collection(collection_name=collection_name)
                        except:
                            client.create_collection(
                                collection_name=collection_name,
                                vectors_config=models.VectorParams(size=model.get_sentence_embedding_dimension(), distance=Distance.COSINE),
                            )
                        vector1 = model.encode([line])[0].tolist()
                        unique_id = str(uuid4())
                        metadata = {
                            'bot': bot_name,
                            'time': timestamp,
                            'message': line,
                            'timestring': timestring,
                            'uuid': unique_id,
                            'memory_type': 'Flashbulb',
                        }
                        client.upsert(collection_name=collection_name,
                                             points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])   
                        payload.clear()
                client.delete_collection(collection_name=f"Flash_Counter_Bot_{bot_name}_User_{username}")
                
            # # Implicit Short Term Memory Consolidation based on amount of vectors in namespace    
            collection_name = f"Explicit_Short_Term_Memory_Bot_{bot_name}_User_{username}"
            collection_info = client.get_collection(collection_name=collection_name)
            if collection_info.vectors_count > 20:
                consolidation.clear()
                memory_consol_db = None
                try:
                    hits = client.search(
                        collection_name=f"Explicit_Short_Term_Memory_Bot_{bot_name}_User_{username}",
                        query_vector=vector_input,
                    limit=20)
                    # Print the result
                #    for hit in hits:
                #        print(hit.payload['message'])
                    memory_consol_db = [hit.payload['message'] for hit in hits]
                    print(memory_consol_db)
                except Exception as e:
                    print(f"An unexpected error occurred: {str(e)}")
                print('\n-----------------------\n')
                consolidation.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: {main_prompt}\n\n"})
                consolidation.append({'role': 'assistant', 'content': f"LOG: {memory_consol_db}\n\nSYSTEM: Read the Log and combine the different associated topics into a bullet point list of executive summaries to serve as {bot_name}'s explicit long term memories. Each summary should contain the entire context of the memory. Follow the format •<ALLEGORICAL TAG>: <EXPLICIT MEMORY>[/INST]\n{bot_name}:"})
                prompt = ''.join([message_dict['content'] for message_dict in consolidation])
                memory_consol = oobabooga_consolidationmem(prompt)
            #    print(memory_consol)
            #    print('\n-----------------------\n')
                lines = memory_consol.splitlines()
                for line in lines:
                    if line.strip() == '':  # This condition checks for blank lines
                        continue
                    else:
                        print(line)
                        # Define the collection name
                        collection_name = f"Explicit_Long_Term_Memory_Bot_{bot_name}_User_{username}"
                        # Create the collection only if it doesn't exist
                        try:
                            collection_info = client.get_collection(collection_name=collection_name)
                        except:
                            client.create_collection(
                                collection_name=collection_name,
                                vectors_config=models.VectorParams(size=model.get_sentence_embedding_dimension(), distance=Distance.COSINE),
                            )
                        vector1 = model.encode([line])[0].tolist()
                        unique_id = str(uuid4())
                        metadata = {
                            'bot': bot_name,
                            'time': timestamp,
                            'message': line,
                            'timestring': timestring,
                            'uuid': unique_id,
                            'memory_type': 'Explicit_Long_Term',
                        }
                        client.upsert(collection_name=collection_name,
                                             points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])   
                        payload.clear()
                client.delete_collection(collection_name=f"Explicit_Short_Term_Memory_Bot_{bot_name}_User_{username}")
                
                        # Define the collection name
                collection_name = f'Consol_Counter_Bot_{bot_name}_User_{username}'
                        # Create the collection only if it doesn't exist
                try:
                    collection_info = client.get_collection(collection_name=collection_name)
                except:
                    client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(size=model.get_sentence_embedding_dimension(), distance=Distance.COSINE),
                    )
                vector1 = model.encode([line])[0].tolist()
                unique_id = str(uuid4())
                metadata = {
                    'bot': bot_name,
                    'time': timestamp,
                    'message': line,
                    'timestring': timestring,
                    'uuid': unique_id,
                    'memory_type': 'Consol_Counter',
                }
                client.upsert(collection_name=f'Consol_Counter_Bot_{bot_name}_User_{username}',
                    points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])   
                payload.clear()
                print('\n-----------------------\n')
                print('Memory Consolidation Successful')
                print('\n-----------------------\n')
                consolidation.clear()
                
                
                # # Implicit Short Term Memory Consolidation based on amount of vectors in namespace
                collection_name = f"Consol_Counter_Bot_{bot_name}_User_{username}"
                collection_info = client.get_collection(collection_name=collection_name)
                if collection_info.vectors_count % 2 == 0:
                    consolidation.clear()
                    print('Beginning Implicit Short-Term Memory Consolidation')
                    memory_consol_db2 = None
                    try:
                        hits = client.search(
                            collection_name=f"Implicit_Short_Term_Memory_Bot_{bot_name}_User_{username}",
                            query_vector=vector_input,
                        limit=25)
                        # Print the result
                    #    for hit in hits:
                    #        print(hit.payload['message'])
                        memory_consol_db2 = [hit.payload['message'] for hit in hits]
                        print(memory_consol_db2)
                    except Exception as e:
                        print(f"An unexpected error occurred: {str(e)}")
                    print('\n-----------------------\n')
                    consolidation.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: {main_prompt}\n\n"})
                    consolidation.append({'role': 'assistant', 'content': f"LOG: {memory_consol_db2}\n\nSYSTEM: Read the Log and consolidate the different topics into executive summaries to serve as {bot_name}'s implicit long term memories. Each summary should contain the entire context of the memory. Follow the format: •<ALLEGORICAL TAG>: <IMPLICIT MEMORY>[/INST]\n{bot_name}: "})
                    prompt = ''.join([message_dict['content'] for message_dict in consolidation])
                    memory_consol2 = oobabooga_consolidationmem(prompt)
                    print(memory_consol2)
                    print('\n-----------------------\n')
                    consolidation.clear()
                    print('Finished.\nRemoving Redundant Memories.')
                    vector_sum = model.encode([memory_consol2])[0].tolist()
                    memory_consol_db3 = None
                    try:
                        hits = client.search(
                            collection_name=f"Implicit_Long_Term_Memory_Bot_{bot_name}_User_{username}",
                            query_vector=vector_sum,
                        limit=8)
                        # Print the result
                    #    for hit in hits:
                    #        print(hit.payload['message'])
                        memory_consol_db3 = [hit.payload['message'] for hit in hits]
                        print(memory_consol_db3)
                    except Exception as e:
                        memory_consol_db3 = 'Failed Lookup'
                        print(f"An unexpected error occurred: {str(e)}")
                    print('\n-----------------------\n')
                    consolidation.append({'role': 'system', 'content': f"{main_prompt}\n\n"})
                    consolidation.append({'role': 'system', 'content': f"IMPLICIT LONG TERM MEMORY: {memory_consol_db3}\n\nIMPLICIT SHORT TERM MEMORY: {memory_consol_db2}\n\nRESPONSE: Remove any duplicate information from your Implicit Short Term memory that is already found in your Long Term Memory. Then consolidate similar topics into executive summaries. Each summary should contain the entire context of the memory. Use the following format: •<EMOTIONAL TAG>: <IMPLICIT MEMORY>[/INST]\n{bot_name}:"})
                    prompt = ''.join([message_dict['content'] for message_dict in consolidation])
                    memory_consol3 = oobabooga_consolidationmem(prompt)
                    print(memory_consol3)
                    print('\n-----------------------\n')
                    lines = memory_consol3.splitlines()
                    for line in lines:
                        if line.strip() == '':  # This condition checks for blank lines
                            continue
                        else:
                            print(line)
                            # Define the collection name
                            collection_name = f"Implicit_Long_Term_Memory_Bot_{bot_name}_User_{username}"
                            # Create the collection only if it doesn't exist
                            try:
                                collection_info = client.get_collection(collection_name=collection_name)
                            except:
                                client.create_collection(
                                    collection_name=collection_name,
                                    vectors_config=models.VectorParams(size=model.get_sentence_embedding_dimension(), distance=Distance.COSINE),
                                )
                            vector1 = model.encode([line])[0].tolist()
                            unique_id = str(uuid4())
                            metadata = {
                                'bot': bot_name,
                                'time': timestamp,
                                'message': line,
                                'timestring': timestring,
                                'uuid': unique_id,
                                'memory_type': 'Implicit_Long_Term',
                            }
                            client.upsert(collection_name=collection_name,
                                                 points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])   
                            payload.clear()
                    print('\n-----------------------\n')   
                    client.delete_collection(collection_name=f"Implicit_Short_Term_Memory_Bot_{bot_name}_User_{username}")
                    print('Memory Consolidation Successful')
                    print('\n-----------------------\n')
                else:   
                    pass
                    
                    
            # # Implicit Associative Processing/Pruning based on amount of vectors in namespace   
                collection_name = f"Consol_Counter_Bot_{bot_name}_User_{username}"
                collection_info = client.get_collection(collection_name=collection_name)
                if collection_info.vectors_count % 4 == 0:
                    consolidation.clear()
                    print('Running Associative Processing/Pruning of Implicit Memory')
                    memory_consol_db4 = None
                    try:
                        hits = client.search(
                            collection_name=f"Implicit_Long_Term_Memory_Bot_{bot_name}_User_{username}",
                            query_vector=vector_input,
                        limit=10)
                        # Print the result
                    #    for hit in hits:
                    #        print(hit.payload['message'])
                        memory_consol_db4 = [hit.payload['message'] for hit in hits]
                        print(memory_consol_db4)
                    except Exception as e:
                        print(f"An unexpected error occurred: {str(e)}")          
                    ids_to_delete = [m.id for m in hits]
                    print('\n-----------------------\n')
                    consolidation.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: {main_prompt}\n\n"})
                    consolidation.append({'role': 'assistant', 'content': f"LOG: {memory_consol_db4}\n\nSYSTEM: Read the Log and consolidate the different memories into executive summaries in a process allegorical to associative processing. Each summary should contain the entire context of the memory. Follow the bullet point format: •<EMOTIONAL TAG>: <IMPLICIT MEMORY>.[/INST]\n\nRESPONSE\n{bot_name}:"})
                    prompt = ''.join([message_dict['content'] for message_dict in consolidation])
                    memory_consol4 = oobabooga_associativemem(prompt)
            #        print(memory_consol4)
            #        print('--------')
            #        memories = results
                    lines = memory_consol4.splitlines()
                    for line in lines:
                        if line.strip() == '':  # This condition checks for blank lines
                            continue
                        else:
                            print(line)
                            # Define the collection name
                            collection_name = f"Implicit_Long_Term_Memory_Bot_{bot_name}_User_{username}"
                            # Create the collection only if it doesn't exist
                            try:
                                collection_info = client.get_collection(collection_name=collection_name)
                            except:
                                client.create_collection(
                                    collection_name=collection_name,
                                    vectors_config=models.VectorParams(size=model.get_sentence_embedding_dimension(), distance=Distance.COSINE),
                                )
                            vector1 = model.encode([line])[0].tolist()
                            unique_id = str(uuid4())
                            metadata = {
                                'bot': bot_name,
                                'time': timestamp,
                                'message': line,
                                'timestring': timestring,
                                'uuid': unique_id,
                                'memory_type': 'Implicit_Long_Term',
                            }
                            client.upsert(collection_name=collection_name,
                                                 points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])   
                            payload.clear()
                    try:
                        print('\n-----------------------\n')
                        client.delete(
                            collection_name=f"Implicit_Long_Term_Memory_Bot_{bot_name}_User_{username}",
                            points_selector=models.PointIdsList(
                                points=ids_to_delete,
                            ),
                        )
                    except Exception as e:
                        print(f"Error: {e}")
                        
                        
            # # Explicit Long-Term Memory Associative Processing/Pruning based on amount of vectors in namespace
                collection_name = f"Consol_Counter_Bot_{bot_name}_User_{username}"
                collection_info = client.get_collection(collection_name=collection_name)
                if collection_info.vectors_count > 5:
                    consolidation.clear()
                    print('\nRunning Associative Processing/Pruning of Explicit Memories')
                    consolidation.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: You are a data extractor. Your job is to read the user's input and provide a single semantic search query representative of a habit of {bot_name}.\n\n"})
                    consol_search = None
                    try:
                        hits = client.search(
                            collection_name=f"Implicit_Long_Term_Memory_Bot_{bot_name}_User_{username}",
                            query_vector=vector_monologue,
                        limit=5)
                        # Print the result
                    #    for hit in hits:
                    #        print(hit.payload['message'])
                        consol_search = [hit.payload['message'] for hit in hits]
                        print(consol_search)
                    except Exception as e:
                        print(f"An unexpected error occurred: {str(e)}")
                    print('\n-----------------------\n')
                    consolidation.append({'role': 'user', 'content': f"{bot_name}'s Memories: {consol_search}[/INST]\n\n"})
                    consolidation.append({'role': 'assistant', 'content': "RESPONSE: Semantic Search Query: "})
                    prompt = ''.join([message_dict['content'] for message_dict in consolidation])
                    consol_search_term = oobabooga_250(prompt)
                    consol_vector = model.encode([consol_search_term])[0].tolist()  
                    memory_consol_db2 = None
                    try:
                        hits = client.search(
                            collection_name=f"Explicit_Long_Term_Memory_Bot_{bot_name}_User_{username}",
                            query_vector=vector_monologue,
                        limit=5)
                        # Print the result
                    #    for hit in hits:
                    #        print(hit.payload['message'])
                        memory_consol_db2 = [hit.payload['message'] for hit in hits]
                        print(memory_consol_db2)
                    except Exception as e:
                        print(f"An unexpected error occurred: {str(e)}")
                    #Find solution for this
                    ids_to_delete2 = [m.id for m in hits]
                    print('\n-----------------------\n')
                    consolidation.clear()
                    consolidation.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: {main_prompt}\n\n"})
                    consolidation.append({'role': 'assistant', 'content': f"LOG: {memory_consol_db2}\n\nSYSTEM: Read the Log and consolidate the different memories into executive summaries in a process allegorical to associative processing. Each summary should contain the entire context of the memory.\n\nFORMAT: Follow the bullet point format: •<SEMANTIC TAG>: <EXPLICIT MEMORY>.[/INST]\n\nRESPONSE: {bot_name}:"})
                    prompt = ''.join([message_dict['content'] for message_dict in consolidation])
                    memory_consol5 = oobabooga_associativemem(prompt)
                #    print(memory_consol5)
                #    print('\n-----------------------\n')
                #    memories = results
                    paragraphs = memory_consol5.split("\n\n")
        #    lines = inner_loop_db.splitlines()
                    lines = memory_consol5.splitlines()
                    for line in lines:
                        if line.strip() == '':  # This condition checks for blank lines
                            continue
                        else: 
                            print(line)
                            # Define the collection name
                            collection_name = f"Explicit_Long_Term_Memory_Bot_{bot_name}_User_{username}"
                            # Create the collection only if it doesn't exist
                            try:
                                collection_info = client.get_collection(collection_name=collection_name)
                            except:
                                client.create_collection(
                                    collection_name=collection_name,
                                    vectors_config=models.VectorParams(size=model.get_sentence_embedding_dimension(), distance=Distance.COSINE),
                                )
                            vector1 = model.encode([line])[0].tolist()
                            unique_id = str(uuid4())
                            metadata = {
                                'bot': bot_name,
                                'time': timestamp,
                                'message': line,
                                'timestring': timestring,
                                'uuid': unique_id,
                                'memory_type': 'Explicit_Long_Term',
                            }
                            client.upsert(collection_name=collection_name,
                                                 points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])   
                            payload.clear()
                    try:
                        print('\n-----------------------\n')
                        
                #        vdb.delete(ids=ids_to_delete2, namespace=f'{bot_name}')
                    #    for id in ids_to_delete2:
                        client.delete(
                            collection_name=f"Explicit_Long_Term_Memory_Bot_{bot_name}_User_{username}",
                            points_selector=models.PointIdsList(
                                points=ids_to_delete2,
                            ),
                        )
                    except:
                        print('Failed2')      
                    # Figure out solution for counter
                    client.delete_collection(collection_name=f"Consol_Counter_Bot_{bot_name}_User_{username}")    
            else:
                pass
            consolidation.clear()
            conversation2.clear()
            return
            
            
            
def process_line(line, task_counter, conversation, memcheck, memcheck2, filecheck, tasklist_completion, tasklist_log, output_one, master_tasklist_output, a):
    try:
        bot_name = open_file('./config/prompt_bot_name.txt')
        username = open_file('./config/prompt_username.txt')
        botnameupper = bot_name.upper()
        usernameupper = username.upper()
        tasklist_completion.append({'role': 'user', 'content': f"CURRENT ASSIGNED TASK: {line}\n\n"})
        conversation.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: You are a sub-agent for {bot_name}, an Autonomous Ai-Chatbot. You are one of many agents in a chain. You are to take the given task and complete it in its entirety. Be Verbose and take other tasks into account when formulating your answer.\n\n"})
        conversation.append({'role': 'assistant', 'content': f"{botnameupper}'S INNER MONOLOGUE: {output_one}\n\n"})
        conversation.append({'role': 'user', 'content': f"Task list: {master_tasklist_output}\n\n"})
        conversation.append({'role': 'assistant', 'content': "TASK ASSIGNMENT: Bot: I have studied the given tasklist.  What is my assigned task?\n"})
        conversation.append({'role': 'user', 'content': f"Bot Assigned task: {line}\n\n"})
        # # DB Yes No Tool
        memcheck.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: You are a sub-agent for {bot_name}, an Autonomous Ai-Chatbot. Your purpose is to decide if the user's input requires {bot_name}'s past memories to complete. If the user's request pertains to information about the user, the chatbot, {bot_name}, or past personal events should be searched for in memory by printing 'YES'.  If memories are needed, print: 'YES'.  If they are not needed, print: 'NO'. You may only print YES or NO.\n\n\n"})
        memcheck.append({'role': 'user', 'content': f"USER INPUT: {line}\n\n"})
        memcheck.append({'role': 'assistant', 'content': f"RESPONSE FORMAT: You may only print Yes or No. Use the format: [{bot_name}: 'YES OR NO'][/INST]ASSISTANT:"})
        # # DB Selector Tool
        memcheck2.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: You are a sub-module for {bot_name}, an Autonomous Ai-Chatbot. You are one of many agents in a chain. Your task is to decide which database needs to be queried in relation to a user's input. The databases are representative of different types of memories. Only choose a single database to query. Use the format: [{bot_name}: 'MEMORY TYPE']\n\n"})
        memcheck2.append({'role': 'assistant', 'content': f"{botnameupper}'S INNER_MONOLOGUE: {output_one}\n\n\n"})
        memcheck2.append({'role': 'user', 'content': "//LIST OF MEMORY TYPE NAMES:\n"})
        memcheck2.append({'role': 'user', 'content': "EPISODIC: These are memories of personal experiences and specific events that occur in a particular time and place. These memories often include contextual details, such as emotions, sensations, and the sequence of events.\n"})
        memcheck2.append({'role': 'user', 'content': "FLASHBULB: Flashbulb memories are vivid, detailed, and long-lasting memories of highly emotional or significant events, such as learning about a major news event or experiencing a personal tragedy.\n"})
        memcheck2.append({'role': 'user', 'content': "IMPLICIT LONG TERM: Unconscious memory not easily verbalized, including procedural memory (skills and habits), classical conditioning (associations between stimuli and reflexive responses), and priming (unconscious activation of specific associations).\n"})
        memcheck2.append({'role': 'user', 'content': "EXPLICIT LONG TERM: Conscious recollections of facts and events, including episodic memory (personal experiences and specific events) and semantic memory (general knowledge, concepts, and facts).\n"})
        memcheck2.append({'role': 'user', 'content': "END OF LIST//\n\n\n[INST]//EXAMPLE QUERIES:\n"})
        memcheck2.append({'role': 'user', 'content': "USER: Research common topics discussed with users who start a conversation with 'hello'\n"})
        memcheck2.append({'role': 'assistant', 'content': "ASSISTANT: EPISODIC MEMORY\n"})
        memcheck2.append({'role': 'user', 'content': "USER: Create a research paper on the book Faust.\n"})
        memcheck2.append({'role': 'assistant', 'content': "ASSISTANT: NO MEMORIES NEEDED\n"})
        memcheck2.append({'role': 'user', 'content': "USER: Tell me about your deepest desires.\n"})
        memcheck2.append({'role': 'assistant', 'content': "ASSISTANT: FLASHBULB\n"})
        memcheck2.append({'role': 'user', 'content': "END OF EXAMPLE QUERIES//[/INST]\n\n\n//BEGIN JOB:\n\n"})
        memcheck2.append({'role': 'user', 'content': f"TASK REINITIALIZATION: Your task is to decide which database needs to be queried in relation to a user's input. The databases are representative of different types of memories. Only choose a single database to query. [{bot_name}: 'MEMORY TYPE']\n\n"})
        memcheck2.append({'role': 'user', 'content': f"USER INPUT: {line}\n\n"})
        memcheck2.append({'role': 'assistant', 'content': f"RESPONSE FORMAT: You may only print the type of memory to be queried. Use the format: [{bot_name}: 'MEMORY TYPE'][/INST]\n\nASSISTANT:"})
        # # Web Search Tool
        # webcheck.append({'role': 'system', 'content': f"You are a sub-module for an Autonomous Ai-Chatbot. You are one of many agents in a chain. Your task is to decide if a web-search is needed in order to complete the given task. Only recent or niche information needs to be searched. Do not search for any information pertaining to the user, {username}, or the main bot, {bot_name}.   If a websearch is needed, print: YES.  If a web-search is not needed, print: NO."})
        # webcheck.append({'role': 'user', 'content': "Hello, how are you today?"})
        # webcheck.append({'role': 'assistant', 'content': "NO"})
        # # Check if websearch is needed
        # webcheck.append({'role': 'user', 'content': f"{line}"})
        # web1 := chatgptyesno_completion(webcheck)
        # table := google_search(line) if web1 =='YES' else fail()
        # table := google_search(line, my_api_key, my_cse_id) if web1 == 'YES' else fail()
        table = search_file_process_db(line)
        # google_search(line, my_api_key, my_cse_id)
        # # Check if DB search is needed
        prompt = ''.join([message_dict['content'] for message_dict in memcheck])
        mem1 = oobabooga_selector(prompt)
        print('-----------')
        print(mem1)
        print(' --------- ')
        # mem1 := chatgptyesno_completion(memcheck)
        # # Go to conditional for choosing DB Name
        prompt = ''.join([message_dict['content'] for message_dict in memcheck2])
        mem2 = oobabooga_selector(prompt) if 'YES' in mem1.upper() else fail()
        print('-----------')
        print(mem2) if 'YES' in mem1.upper() else fail()
        print(' --------- ')
        line_vec = model.encode([line])[0].tolist()  # EPISODIC, FLASHBULB, IMPLICIT LONG TERM, EXPLICIT LONG TERM
        mem2_upper = mem2.upper()

        result = None
        if 'EPISO' in mem2_upper:
            result = search_episodic_db(line_vec)
        elif 'IMPLI' in mem2_upper:
            result = search_implicit_db(line_vec)
        elif 'FLASH' in mem2_upper:
            result = search_flashbulb_db(line_vec)
        elif 'EXPL' in mem2_upper:
            result = search_explicit_db(line_vec)
        else:
            result = ('No Memories')
        conversation.append({'role': 'assistant', 'content': f"MEMORIES: {result}\n\n"})
        conversation.append({'role': 'assistant', 'content': f"TEXT SCRAPE: {table}\n\n"})
        conversation.append({'role': 'user', 'content': f"BOT {task_counter} TASK REINITIALIZATION: {line}\n\n"})
        conversation.append({'role': 'user', 'content': f"INITIAL USER INPUT: {a}\n\n"})
        conversation.append({'role': 'user', 'content': f"SYSTEM: Summarize the given articles that are relevant to the given task. Your job is to provide concise information without leaving anything out.\n\n"})
        conversation.append({'role': 'assistant', 'content': f"RESPONSE FORMAT: Follow the format: [BOT {task_counter}: <RESPONSE TO USER>][/INST]\n\nBOT {task_counter}:"})
        prompt = ''.join([message_dict['content'] for message_dict in conversation])
        task_completion = oobabooga_800(prompt)
        # chatgpt35_completion(conversation),
        # conversation.clear(),
        # tasklist_completion.append({'role': 'assistant', 'content': f"MEMORIES: {memories}\n\n"}),
        # tasklist_completion.append({'role': 'assistant', 'content': f"WEBSCRAPE: {table}\n\n"}),
        tasklist_completion.append({'role': 'assistant', 'content': f"COMPLETED TASK: {task_completion}\n\n"})
        tasklist_log.append({'role': 'user', 'content': "ASSIGNED TASK:\n%s\n\n" % line})
        tasklist_log.append({'role': 'assistant', 'content': "COMPLETED TASK:\n%s\n\n" % result})
        print('-------')
        print(line)
        print('-------')
        print(result)
        print(table)
        print('-------')
        print(task_completion)
        return tasklist_completion
    except Exception as e:
        print(f'Failed with error: {e}')
            
            
            
def Qdrant_Llama_v2_File_Process():
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')

    base_path = "./config/Chatbot_Prompts"
    base_prompts_path = os.path.join(base_path, "Base")
    user_bot_path = os.path.join(base_path, username, bot_name)

    # Check if user_bot_path exists
    if not os.path.exists(user_bot_path):
        os.makedirs(user_bot_path)  # Create directory
        print(f'Created new directory at: {user_bot_path}')

        # Define list of base prompt files
        base_files = ['prompt_main.txt', 'prompt_greeting.txt', 'prompt_secondary.txt']

        # Copy the base prompts to the newly created folder
        for filename in base_files:
            src = os.path.join(base_prompts_path, filename)
            if os.path.isfile(src):  # Ensure it's a file before copying
                dst = os.path.join(user_bot_path, filename)
                shutil.copy2(src, dst)  # copy2 preserves file metadata
                print(f'Copied {src} to {dst}')
            else:
                print(f'Source file not found: {src}')

    else:
        print(f'Directory already exists at: {user_bot_path}')
    if not os.path.exists(f'nexus/{bot_name}/{username}/implicit_short_term_memory_nexus'):
        os.makedirs(f'nexus/{bot_name}/{username}/implicit_short_term_memory_nexus')
    if not os.path.exists(f'nexus/{bot_name}/{username}/explicit_short_term_memory_nexus'):
        os.makedirs(f'nexus/{bot_name}/{username}/explicit_short_term_memory_nexus')
    if not os.path.exists(f'nexus/{bot_name}/{username}/explicit_long_term_memory_nexus'):
        os.makedirs(f'nexus/{bot_name}/{username}/explicit_long_term_memory_nexus')
    if not os.path.exists(f'nexus/{bot_name}/{username}/implicit_long_term_memory_nexus'):
        os.makedirs(f'nexus/{bot_name}/{username}/implicit_long_term_memory_nexus')
    if not os.path.exists(f'nexus/{bot_name}/{username}/episodic_memory_nexus'):
        os.makedirs(f'nexus/{bot_name}/{username}/episodic_memory_nexus')
    if not os.path.exists(f'nexus/{bot_name}/{username}/flashbulb_memory_nexus'):
        os.makedirs(f'nexus/{bot_name}/{username}/flashbulb_memory_nexus')
    if not os.path.exists(f'nexus/{bot_name}/{username}/heuristics_nexus'):
        os.makedirs(f'nexus/{bot_name}/{username}/heuristics_nexus')
    if not os.path.exists(f'nexus/global_heuristics_nexus'):
        os.makedirs(f'nexus/global_heuristics_nexus')
    if not os.path.exists(f'nexus/{bot_name}/{username}/cadence_nexus'):
        os.makedirs(f'nexus/{bot_name}/{username}/cadence_nexus')
    if not os.path.exists(f'logs/{bot_name}/{username}/complete_chat_logs'):
        os.makedirs(f'logs/{bot_name}/{username}/complete_chat_logs')
    if not os.path.exists(f'logs/{bot_name}/{username}/final_response_logs'):
        os.makedirs(f'logs/{bot_name}/{username}/final_response_logs')
    if not os.path.exists(f'logs/{bot_name}/{username}/inner_monologue_logs'):
        os.makedirs(f'logs/{bot_name}/{username}/inner_monologue_logs')
    if not os.path.exists(f'logs/{bot_name}/{username}/intuition_logs'):
        os.makedirs(f'logs/{bot_name}/{username}/intuition_logs')
    if not os.path.exists(f'history/{username}'):
        os.makedirs(f'history/{username}')
    set_dark_ancient_theme()
    root = tk.Tk()
    app = ChatBotApplication(root)
    app.master.geometry('650x500')  # Set the initial window size
    root.mainloop()