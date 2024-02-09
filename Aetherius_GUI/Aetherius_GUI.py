import sys
sys.path.insert(0, './Aetherius_API')
sys.path.insert(0, './config')
sys.path.insert(0, './Aetherius_API/Chatbot_Prompts')
sys.path.insert(0, './Aetherius_API/resources')
import os
import json
import asyncio
import time
from time import time, sleep
import datetime
from uuid import uuid4
import importlib.util
from importlib.util import spec_from_file_location, module_from_spec
import multiprocessing
import threading
import concurrent.futures
import customtkinter
import tkinter as tk
from tkinter import ttk, scrolledtext, simpledialog, font, messagebox, filedialog
import requests
import shutil
from PyPDF2 import PdfReader
from ebooklib import epub
import pytesseract
from PIL import Image
from bs4 import BeautifulSoup
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, Range, MatchValue
from qdrant_client.http import models
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import re
import sounddevice as sd
import whisper
import pydub
import subprocess
import keyboard
from scipy.io.wavfile import write
from pydub.playback import play as pydub_play
from gtts import gTTS
import pandas as pd
from queue import Queue
import traceback
from Aetherius_API.Main import *

# LATER is the key for later editing needed



# Read the JSON file
with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
    settings = json.load(f)

# Extract the embed_size value
embed_size = settings['embed_size']


        
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
    script_path3 = get_script_path_from_file(json_file_path, "WebScrape_Type", base_folder='./Aetherius_API/Tools/AetherNode/')
    script_path4 = get_script_path_from_file(json_file_path, "Vision_Model", base_folder='./Aetherius_API/Tools/Llama_2_Async/')
if select_api == "AetherNode":
    script_path3 = get_script_path_from_file(json_file_path, "WebScrape_Type", base_folder='./Aetherius_API/Tools/AetherNode/')
    script_path4 = get_script_path_from_file(json_file_path, "Vision_Model", base_folder='./Aetherius_API/Tools/AetherNode_Llama_2/')
if select_api == "OpenAi":
    script_path3 = get_script_path_from_file(json_file_path, "WebScrape_Type", base_folder='./Aetherius_API/Tools/AetherNode/')
    script_path4 = get_script_path_from_file(json_file_path, "Vision_Model", base_folder='./Aetherius_API/Tools/OpenAi/')
import_functions_from_script(script_path4, "eyes_module")
import_functions_from_script(script_path3, "webscrape_module")







# Set the Theme for the Chatbot
def set_dark_ancient_theme():
    background_color = "#2B303A"  # Dark blue-gray
    foreground_color = "#FDF7E3"  # Pale yellow
    button_color = "#415A77"  # Dark grayish blue
    text_color = 'white'

    return background_color, foreground_color, button_color, text_color
    

# record_audio('audio', duration, sample_rate, channels, dtype)

def record_audio(filename, duration, sample_rate, channels, dtype):
    self.is_recording = True
    print("Press and hold the Right Alt key to record...")
    audio_data = []

    while True:
        if keyboard.is_pressed('right alt'):
            if len(audio_data) == 0:
                print("Recording...")

            # Record 100ms chunks while key is down
            audio_chunk = sd.rec(int(sample_rate * 0.1), samplerate=sample_rate, channels=channels, dtype=dtype)
            sd.wait()

            # Append chunk to audio data
            audio_data.extend(audio_chunk)

        elif len(audio_data) > 0:
            print("Stopped recording.")
            break

    audio_data = np.array(audio_data, dtype=dtype)

    # Save audio as a WAV file first
    write('audio.wav', sample_rate, np.array(audio_data))

    # Use FFmpeg to convert WAV to MP3
    subprocess.run(['ffmpeg', '-i', 'audio.wav', 'audio.mp3'])
    print(f"Saved as {filename}.mp3")
    
    
def play(audio_segment):
    pydub_play(audio_segment)
    self.is_recording = False
    
    
#def write_to_dataset(a, response_two, bot_name, username):
#    # Define the folder and file paths
#    result = messagebox.askyesno("Upload Memories", "Do you want to write to dataset?")
#    if result:
#        folder_path = f"./logs/Datasets/{bot_name}/{username}"
#        file_path = f"{folder_path}/dataset.json"

        # Check if the folder exists; if not, create it
#        if not os.path.exists(folder_path):
#            os.makedirs(folder_path)

        # Read existing data
#        try:
#            with open(file_path, 'r') as f:
#                data = json.load(f)
#        except FileNotFoundError:
#            data = []

        # Append new data
#        new_entry = {
#            "input": a,
#            "output": response_two
#        }
#        data.append(new_entry)

        # Write updated data back to file
#        with open(file_path, 'w') as f:
#            json.dump(data, f, indent=4)


def write_to_dataset(a, response_two, bot_name, username, main_prompt):
    # Ask for permission to write to dataset
    result = messagebox.askyesno("Upload Memories", "Do you want to write to dataset?")
    if result:
        folder_path = f"./logs/Datasets/{bot_name}/{user_id}"
        json_file_path = f"{folder_path}/dataset.json"
        csv_file_path = f"{folder_path}/dataset.csv"
        txt_file_path = f"{folder_path}/dataset.txt"

        # Check if the folder exists; if not, create it
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        # Update JSON
        try:
            with open(json_file_path, 'r') as f:
                json_data = json.load(f)
        except FileNotFoundError:
            json_data = []
        
        new_entry_json = {
            "instruction": main_prompt,
            "input": a,
            "output": response_two
        }
        json_data.append(new_entry_json)

        with open(json_file_path, 'w') as f:
            json.dump(json_data, f, indent=4)

        # Update CSV
        try:
            df = pd.read_csv(csv_file_path, encoding='utf-8')
        except FileNotFoundError:
            df = pd.DataFrame(columns=['text'])

        formatted_text = f"[INST] <<SYS>>\n{main_prompt}\n<</SYS>>\n\n{a} [/INST] {response_two}"
        new_entry_csv = {'text': [formatted_text]}
        
        new_df = pd.DataFrame(new_entry_csv)
        df = pd.concat([df, new_df], ignore_index=True)
        
        df.to_csv(csv_file_path, index=False, encoding='utf-8')

        # Update TXT
        new_entry_txt = f"%INSTRUCTION%\n{main_prompt}\n\n%INPUT%\n{a}\n\n%OUTPUT%\n{response_two}\n\n\n\n"
        try:
            with open(txt_file_path, 'a', encoding='utf-8') as f:  # 'a' means append mode
                f.write(new_entry_txt)
        except FileNotFoundError:
            with open(txt_file_path, 'w', encoding='utf-8') as f:  # 'w' means write mode
                f.write(new_entry_txt)

    
   
        
        

    
    
    
# Function for Uploading Cadence, called in the create widgets function.
def DB_Upload_Cadence(query):
    # key = input("Enter OpenAi API KEY:")
    with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
        
    bot_name = settings.get('Current_Ui_Bot_Name', '')
    username = settings.get('Current_Ui_Username', '')
    user_id = settings.get('Current_Ui_User_ID', '')
    while True:
        payload = list()
    #    a = input(f'\n\nUSER: ')        
        timestamp = time()
        timestring = timestamp_to_datetime(timestamp)
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
            'user': user_id,
            'time': timestamp,
            'message': query,
            'timestring': timestring,
            'memory_type': 'Cadence',
        }
        client.upsert(collection_name=collection_name,
                             points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])    
        print('\n\nSYSTEM: Upload Successful!')
        return query
 
        
# Function for Uploading Heuristics, called in the create widgets function.
def DB_Upload_Heuristics(query):
    with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
        
    bot_name = settings.get('Current_Ui_Bot_Name', '')
    username = settings.get('Current_Ui_Username', '')
    user_id = settings.get('Current_Ui_User_ID', '')
    while True:
        payload = list()
    #    a = input(f'\n\nUSER: ')        
        timestamp = time()
        timestring = timestamp_to_datetime(timestamp)
        # Define the collection name
        collection_name = f"Bot_{bot_name}"
        try:
            collection_info = client.get_collection(collection_name=collection_name)
        except:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=embed_size, distance=Distance.COSINE),
            )
    #    embedding = embeddings(query)
        embedding = embeddings(query)
        unique_id = str(uuid4())
        metadata = {
            'bot': bot_name,
            'user': user_id,
            'time': timestamp,
            'message': query,
            'timestring': timestring,
            'memory_type': 'Heuristics',
        }
        client.upsert(collection_name=collection_name,
                             points=[PointStruct(id=unique_id, payload=metadata, vector=embedding)])  
        print('\n\nSYSTEM: Upload Successful!')
        return query
        
        
def upload_implicit_long_term_memories(query):
    with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
        
    bot_name = settings.get('Current_Ui_Bot_Name', '')
    username = settings.get('Current_Ui_Username', '')
    user_id = settings.get('Current_Ui_User_ID', '')
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
        'user': user_id,
        'time': timestamp,
        'message': query,
        'timestring': timestring,
        'user': username,
        'memory_type': 'Implicit_Long_Term',
    }
    client.upsert(collection_name=collection_name,
                         points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])    
                # Search the collection
    print('\n\nSYSTEM: Upload Successful!')
    return query
        
        
def upload_explicit_long_term_memories(query):
    with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
        
    bot_name = settings.get('Current_Ui_Bot_Name', '')
    username = settings.get('Current_Ui_Username', '')
    user_id = settings.get('Current_Ui_User_ID', '')
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
        'user': user_id,
        'time': timestamp,
        'message': query,
        'timestring': timestring,
        'user': username,
        'memory_type': 'Explicit_Long_Term',
    }
    client.upsert(collection_name=collection_name,
                         points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])    
                # Search the collection
    print('\n\nSYSTEM: Upload Successful!')
    return query
    
    
def upload_implicit_short_term_memories(query):
    with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
        
    bot_name = settings.get('Current_Ui_Bot_Name', '')
    username = settings.get('Current_Ui_Username', '')
    user_id = settings.get('Current_Ui_User_ID', '')
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
        'user': user_id,
        'time': timestamp,
        'message': query,
        'timestring': timestring,
        'user': username,
        'memory_type': 'Implicit_Short_Term',
    }
    client.upsert(collection_name=collection_name,
                         points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])    
                # Search the collection
    return query
        
        
def upload_explicit_short_term_memories(query):
    with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
        
    bot_name = settings.get('Current_Ui_Bot_Name', '')
    username = settings.get('Current_Ui_Username', '')
    user_id = settings.get('Current_Ui_User_ID', '')
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
        'user': user_id,
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
    
    
def ask_upload_implicit_memories(memories):
    with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
        
    bot_name = settings.get('Current_Ui_Bot_Name', '')
    username = settings.get('Current_Ui_Username', '')
    user_id = settings.get('Current_Ui_User_ID', '')
    timestamp = time()
    timestring = timestamp_to_datetime(timestamp)
    payload = list()
    result = messagebox.askyesno("Upload Memories", "Do you want to upload the implicit memories?")
    if result:
        # User clicked "Yes"
        segments = re.split(r'•|\n\s*\n', memories)
        total_segments = len(segments)

        for index, segment in enumerate(segments):
            segment = segment.strip()
            if segment == '':  # This condition checks for blank segments
                continue  # This condition checks for blank lines      
            # Check if it is the final segment and if the memory is cut off (ends without punctuation)
            if index == total_segments - 1 and not segment[-1] in ['.', '!', '?']:
                print(segment)
                payload = list()
            #    a = input(f'\n\nUSER: ')        
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
                vector1 = embeddings(segment)
                unique_id = str(uuid4())
                point_id = unique_id + str(int(timestamp))
                metadata = {
                    'bot': bot_name,
                    'user': user_id,
                    'time': timestamp,
                    'message': segment,
                    'timestring': timestring,
                    'uuid': unique_id,
                    'user': username,
                    'memory_type': 'Implicit_Short_Term',
                }
                client.upsert(collection_name=collection_name,
                                     points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])    
                # Search the collection
        print('\n\nSYSTEM: Upload Successful!')
        return 'yes'
    else:
        # User clicked "No"
        print('\n\nSYSTEM: Memories have been Deleted.')
        
        
def ask_upload_explicit_memories(memories):
    with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
        
    bot_name = settings.get('Current_Ui_Bot_Name', '')
    username = settings.get('Current_Ui_Username', '')
    user_id = settings.get('Current_Ui_User_ID', '')
    timestamp = time()
    timestring = timestamp_to_datetime(timestamp)
    payload = list()
    result = messagebox.askyesno("Upload Memories", "Do you want to upload the explicit memories?")
    if result:
        # User clicked "Yes"
        segments = re.split(r'•|\n\s*\n', memories)
        total_segments = len(segments)

        for index, segment in enumerate(segments):
            segment = segment.strip()
            if segment == '':  # This condition checks for blank segments
                continue  # This condition checks for blank lines      
            # Check if it is the final segment and if the memory is cut off (ends without punctuation)
            if index == total_segments - 1 and not segment[-1] in ['.', '!', '?']:
                print(segment)
                payload = list()
            #    a = input(f'\n\nUSER: ')        
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
                    'user': user_id,
                    'time': timestamp,
                    'message': segment,
                    'timestring': timestring,
                    'uuid': unique_id,
                    'user': username,
                    'memory_type': 'Explicit_Short_Term',
                }
                client.upsert(collection_name=collection_name,
                                     points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])    
                # Search the collection
        print('\n\nSYSTEM: Upload Successful!')
        return 'yes'
    else:
        # User clicked "No"
        print('\n\nSYSTEM: Memories have been Deleted.')
        
        
def ask_upload_memories(memories, memories2):
    with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
        
    bot_name = settings.get('Current_Ui_Bot_Name', '')
    username = settings.get('Current_Ui_Username', '')
    user_id = settings.get('Current_Ui_User_ID', '')
    timestamp = time()
    timestring = timestamp_to_datetime(timestamp)
    payload = list()
    print(f'\nIMPLICIT MEMORIES\n-------------')
    print(memories)
    print(f'\nEXPLICIT MEMORIES\n-------------')
    print(memories2)
    result = messagebox.askyesno("Upload Memories", "Do you want to upload the memories?")
    if result: 
        return 'yes'
    else:
        # User clicked "No"
        print('\n\nSYSTEM: Memories have been Deleted.')
        return 'no'
        
        
def upload_implicit_short_term_memories(query):
    with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
        
    bot_name = settings.get('Current_Ui_Bot_Name', '')
    username = settings.get('Current_Ui_Username', '')
    user_id = settings.get('Current_Ui_User_ID', '')
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
        'user': user_id,
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
        
        
def upload_explicit_short_term_memories(query):
    with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
        
    bot_name = settings.get('Current_Ui_Bot_Name', '')
    username = settings.get('Current_Ui_Username', '')
    user_id = settings.get('Current_Ui_User_ID', '')
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
        'user': user_id,
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
        
        
def search_implicit_db(line_vec):
    m = multiprocessing.Manager()
    lock = m.Lock()
    with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
        
    bot_name = settings.get('Current_Ui_Bot_Name', '')
    username = settings.get('Current_Ui_Username', '')
    user_id = settings.get('Current_Ui_User_ID', '')
    try:
        with lock:
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
                print(memories1)
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
                print(memories2)
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
    
    
def search_episodic_db(line_vec):
    m = multiprocessing.Manager()
    lock = m.Lock()
    with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
        
    bot_name = settings.get('Current_Ui_Bot_Name', '')
    username = settings.get('Current_Ui_Username', '')
    user_id = settings.get('Current_Ui_User_ID', '')
    try:
        with lock:
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
                print(memories)
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
            
    
def search_flashbulb_db(line_vec):
    m = multiprocessing.Manager()
    lock = m.Lock()
    with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
        
    bot_name = settings.get('Current_Ui_Bot_Name', '')
    username = settings.get('Current_Ui_Username', '')
    user_id = settings.get('Current_Ui_User_ID', '')
    try:
        with lock:
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
                print(memories)
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
    
    
def search_explicit_db(line_vec):
    m = multiprocessing.Manager()
    lock = m.Lock()
    with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
        
    bot_name = settings.get('Current_Ui_Bot_Name', '')
    username = settings.get('Current_Ui_Username', '')
    user_id = settings.get('Current_Ui_User_ID', '')
    try:
        with lock:
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
                print(memories1)
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
                                match=MatchValue(value="Explicit_Short_Term")
                            )
                        ]
                    ),
                    limit=5
                )
                    # Print the result
                memories2 = [hit.payload['message'] for hit in hits]
                print(memories2)
            except Exception as e:
                if "Not found: Collection" in str(e):
                    print("Collection has no memories.")
                else:
                    print(f"An unexpected error occurred: {str(e)}")
            memories = f'{memories1}\n{memories2}'    
            print(memories)
            return memories
    except Exception as e:
        print(e)
        memories = "Error"
        return memories  
        
        
async def GPT_4_Text_Extract():
    # # Number of Messages before conversation is summarized, higher number, higher api cost. Change to 3 when using GPT 3.5 due to token usage.
    conv_length = 3
    m = multiprocessing.Manager()
    lock = m.Lock()
    tasklist = list()
    conversation = list()
    int_conversation = list()
    conversation2 = list()
    counter = 0
    counter2 = 0
    mem_counter = 0
    with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
        
    bot_name = settings.get('Current_Ui_Bot_Name', '')
    username = settings.get('Current_Ui_Username', '')
    user_id = settings.get('Current_Ui_User_ID', '')
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
    if not os.path.exists('Upload/VIDEOS'):
        os.makedirs('Upload/VIDEOS')
    if not os.path.exists('Upload/VIDEOS/Finished'):
        os.makedirs('Upload/VIDEOS/Finished')
    if not os.path.exists('Upload/EPUB/Finished'):
        os.makedirs('Upload/EPUB/Finished')
        
    while True:
        try:
        # # Get Timestamp
            timestamp = time.time()
            timestring = timestamp_to_datetime(timestamp)
            await process_files_in_directory('./Upload/SCANS', './Upload/SCANS/Finished')
            await process_files_in_directory('./Upload/TXT', './Upload/TXT/Finished')
            await process_files_in_directory('./Upload/PDF', './Upload/PDF/Finished')
            await process_files_in_directory('./Upload/EPUB', './Upload/EPUB/Finished')
            await process_files_in_directory('./Upload/VIDEOS', './Upload/VIDEOS/Finished')  
        
        except:
            traceback.print_exc()
        
async def process_files_in_directory(directory_path, finished_directory_path, chunk_size=600, overlap=80):
    try:
        files = os.listdir(directory_path)
        files = [f for f in files if os.path.isfile(os.path.join(directory_path, f))]
        tasks = [asyncio.create_task(process_and_move_file(directory_path, finished_directory_path, file, chunk_size, overlap)) for file in files]
        await asyncio.gather(*tasks)
    except Exception as e:
        print(e)
        traceback.print_exc()


        
async def process_and_move_file(directory_path, finished_directory_path, file, chunk_size, overlap):
    try:
        file_path = os.path.join(directory_path, file)
        await chunk_text_from_file(file_path, chunk_size, overlap)  # Correct usage
        finished_file_path = os.path.join(finished_directory_path, file)
        shutil.move(file_path, finished_file_path)
    except Exception as e:
        print(e)
        traceback.print_exc()
        return "Error"
        
        
async def chunk_text_from_file(file_path, chunk_size=400, overlap=40):
    with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
        
    bot_name = settings.get('Current_Ui_Bot_Name', '')
    username = settings.get('Current_Ui_Username', '')
    user_id = settings.get('Current_Ui_User_ID', '')
    try:
        print("Reading given file, please wait...")
        pytesseract.pytesseract.tesseract_cmd = '.\\Tesseract-ocr\\tesseract.exe'
        textemp = None
        file_extension = os.path.splitext(file_path)[1].lower()
        
        texttemp = None  # Initialize texttemp
        
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
                
        elif file_extension in ['.mp4', '.mkv', '.flv', '.avi']:
            audio_file = "audio_extracted.wav"  # Replace with a more unique name if needed
            subprocess.run(["ffmpeg", "-i", file_path, "-vn", "-acodec", "pcm_s16le", "-ac", "1", "-ar", "44100", "-f", "wav", audio_file])
            
            model_stt = whisper.load_model("tiny")
            transcribe_result = model_stt.transcribe(audio_file)
            if isinstance(transcribe_result, dict) and 'text' in transcribe_result:
                texttemp = transcribe_result['text']
            else:
                print("Unexpected transcribe result")
                texttemp = ""  # or set to some default value
            os.remove(audio_file)  # Make sure you want to delete this
            
        else:
            print(f"Unsupported file type: {file_extension}")
            return []

        # The rest of your existing code
        texttemp = '\n'.join(line for line in texttemp.splitlines() if line.strip())
        chunks = await chunk_text(texttemp, chunk_size, overlap)
        filelist = list()
        try:
                # Open and read the JSON file with utf-8 encoding
            with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
                # Retrieve host data from the JSON dictionary
            host_data = settings.get('HOST_AetherNode', '').strip()
                # Split the host data into individual hosts
            hosts = host_data.split(' ')
                # Count the number of hosts
            num_hosts = len(hosts)
                
        except Exception as e:
            print(f"An error occurred while reading the host file: {e}")
        host_queue = Queue()
        for host in hosts:
            host_queue.put(host)
        # Define the collection name
        collection_name = f"Bot_{bot_name}_External_Knowledgebase"
        try:
            collection_info = client.get_collection(collection_name=collection_name)
            print(collection_info)
        except:
            client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=embed_size, distance=Distance.COSINE),
        )
        
    #    for chunk in chunks:
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_hosts) as executor:
                futures = []
                for chunk in chunks:
                    future = executor.submit(
                        wrapped_chunk_from_file,
                        host_queue, chunk, collection_name, bot_name, username, embeddings, client, file_path
                    )
                    futures.append(future)

                # Gather results
                results = []
                for future in concurrent.futures.as_completed(futures):
                    results.append(future.result())

                # Do something with the results, like appending to `weblist`
                filelist = []
            #    for result in results:
            #        filelist.append(result['file_path'] + ' ' + result['processed_text'])
                #    print(result['file_path'] + '\n' + result['semantic_db_term'] + '\n' + result['processed_text'])

        except Exception as e:
            traceback.print_exc()
            print(f"An error occurred while executing threads: {e}")

    #    table = filelist
    #    return table
        return
    except Exception as e:
        print(e)
        traceback.print_exc()
        table = "Error"
        return table  
        
        
def wrapped_chunk_from_file(host_queue, chunk, collection_name, bot_name, username, embeddings, client, file_path):
    try:
            # get a host
        host = host_queue.get()
        result = summarized_chunk_from_file(host, chunk, collection_name, bot_name, username, embeddings, client, file_path)
            # release the host
        host_queue.put(host)
        return result
    except Exception as e:
        print(e)
        traceback.print_exc()
        
        
def summarized_chunk_from_file(host, chunk, collection_name, bot_name, username, embeddings, client, file_path):
    try:
    
        filesum = list()
        filelist = list()
        filesum.append({'role': 'system', 'content': "MAIN SYSTEM PROMPT: You are an ai text summarizer.  Your job is to take the given text from a scraped file, then return the text in a summarized article form.  Do not generalize, rephrase, or add information in your summary, keep the same semantic meaning.  If no article is given, print no article.\n\n\n"})
        filesum.append({'role': 'user', 'content': f"SCRAPED ARTICLE: {chunk}\n\nINSTRUCTIONS: Summarize the article without losing any factual knowledge and maintaining full context and information. Only print the truncated article, do not include any additional text or comments. [/INST] SUMMARIZER BOT: Sure! Here is the summarized article based on the scraped text: "})
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
            
        user_id = settings.get('Current_Ui_User_ID', '')

        prompt = ''.join([message_dict['content'] for message_dict in filesum])
        text = asyncio.run(File_Processor_Call(host, prompt, username, bot_name))
        if len(text) < 20:
            text = "No File available"
        #    paragraphs = text.split('\n\n')  # Split into paragraphs
        #    for paragraph in paragraphs:  # Process each paragraph individually, add a check to see if paragraph contained actual information.
        #        filecheck = list()
        #        filelist.append(file_path + ' ' + paragraph)
        #        filecheck.append({'role': 'system', 'content': f"You are an agent for an automated text-processing tool. You are one of many agents in a chain. Your task is to decide if the given text from a file was processed successfully. The processed text should contain factual data or opinions. If the given data only consists of an error message or a single question, skip it.  If the article was processed successfully, print: YES.  If a file-process is not needed, print: NO."})
        #        filecheck.append({'role': 'user', 'content': f"Is the processed information useful to an end-user? YES/NO: {paragraph}"})
                
        filecheck = list()
        filecheck.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: You are an agent for an automated text scraping tool. Your task is to decide if the previous Ai Agent scraped the text successfully. The scraped text should contain some form of article, if it does, print 'YES'. If the article was scraped successfully, print: 'YES'.  If the text scrape failed or is a response from the first agent, print: 'NO'.\n\n"})
        filecheck.append({'role': 'user', 'content': f"ORIGINAL TEXT FROM SCRAPE: {chunk}\n\n"})
        filecheck.append({'role': 'user', 'content': f"PROCESSED FILE TEXT: {text}\n\n"})
        filecheck.append({'role': 'user', 'content': f"SYSTEM: You are responding for a Yes or No input field. You are only capible of printing Yes or No. Use the format: [AI AGENT: <'Yes'/'No'>][/INST]\n\nASSISTANT: "})
        prompt = ''.join([message_dict['content'] for message_dict in filecheck])
        fileyescheck = 'yes'
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
            if 'cannot provide a summary of' in text.lower():
                text = chunk
            if 'yes' in fileyescheck.lower():
                semanticterm = list()
                semanticterm.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: You are a bot responsible for taging articles with a title for database queries.  Your job is to read the given text, then create a title in question form representative of what the article is about.  The title should be semantically identical to the overview of the article and not include extraneous info. Use the format: [<TITLE IN QUESTION FORM>].\n\n"})
                semanticterm.append({'role': 'user', 'content': f"ARTICLE: {text}\n\n"})
                semanticterm.append({'role': 'user', 'content': f"SYSTEM: Create a short, single question that encapsulates the semantic meaning of the Article.  Use the format: [<QUESTION TITLE>].  Please only print the title, it will be directly input in front of the article.[/INST]\n\nASSISTANT: Sure! Here's the summary of the given article: "})
                prompt = ''.join([message_dict['content'] for message_dict in semanticterm])
                semantic_db_term = asyncio.run(File_Processor_Call(host, prompt, username, bot_name))
                filename = os.path.basename(file_path)
                print('---------')
                if 'cannot provide a summary of' in semantic_db_term.lower():
                    semantic_db_term = 'Tag Censored by Model'
                    # Generate and append filename and paragraph to filelist
                filelist.append(filename + ' ' + text)
                print(filename + '\n' + semantic_db_term + '\n' + text)

                    # Create or update the text file in ./Upload
                text_file_path = './Upload/' + filename + '.txt'
                with open(text_file_path, 'a') as f:  # 'a' means append mode
                    f.write('<' + filename + '>\n')
                    f.write('<' + semantic_db_term + '>\n')
                    f.write('<' + text + '>\n\n')  # Double newline for separation

                payload = list()
                timestamp = time.time()
                timestring = timestamp_to_datetime(timestamp)
                vector1 = embeddings(filename + '\n' + semantic_db_term + '\n' + text)
                unique_id = str(uuid4())
                point_id = unique_id + str(int(timestamp))

                metadata = {
                    'bot': bot_name,
                    'user': user_id,
                    'time': timestamp,
                    'source': filename,
                    'tag': semantic_db_term,
                    'message': text,
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
        traceback.print_exc()
        table = "Error"
        return table   
        
        
        
# Running Conversation List
class MainConversation:
    def __init__(self, max_entries, prompt, greeting):
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
            
        bot_name = settings.get('Current_Ui_Bot_Name', '')
        username = settings.get('Current_Ui_Username', '')
        user_id = settings.get('Current_Ui_User_ID', '')
        botnameupper = bot_name.upper()
        usernameupper = username.upper()
        self.max_entries = max_entries
        self.file_path = f'./logs/history/{user_id}/{bot_name}_main_conversation_history.json'
        self.file_path2 = f'./logs/history/{user_id}/{bot_name}_main_history.json'
        self.main_conversation = [prompt, greeting]

        # Load existing conversation from file
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.running_conversation = data.get('running_conversation', [])
        else:
            self.running_conversation = []

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
            
            
class ChatBotApplication(customtkinter.CTkFrame):
    # Create Tkinter GUI
    def __init__(self, master=None):
        super().__init__(master)
        (
            self.background_color,
            self.foreground_color,
            self.button_color,
            self.text_color
        ) = set_dark_ancient_theme()

        self.master = master
        dark_bg_color = "#2B2B2B"
        self.master.configure(bg=dark_bg_color)
        self.master.title('Aetherius Chatbot')
        self.pack(fill="both", expand=True)
        self.create_widgets()
        # Load and display conversation history
        self.display_conversation_history()
        self.is_recording = False
        self.loop = asyncio.new_event_loop()
        self.loop_thread = threading.Thread(target=self.loop.run_forever)
        self.loop_thread.start()
        self.temperature_value = tk.StringVar()
        self.top_p_value = tk.StringVar()
        self.top_k_value = tk.StringVar()
        self.rep_pen_value = tk.StringVar()
        self.min_tokens_value = tk.StringVar()
        self.max_tokens_value = tk.StringVar()
        
        
    def show_context_menu(self, event):
        # Create the menu
        menu = tk.Menu(self, tearoff=0)
        # Right Click Menu
        menu.add_command(label="Copy", command=self.copy_selected_text)
        # Display the menu at the clicked position
        menu.post(event.x_root, event.y_root)
        
        
    def display_conversation_history(self):
        # Load the conversation history from the JSON file
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
            
        bot_name = settings.get('Current_Ui_Bot_Name', '')
        username = settings.get('Current_Ui_Username', '')
        user_id = settings.get('Current_Ui_User_ID', '')
        
        file_path = f'./history/{user_id}/{bot_name}_main_conversation_history.json'
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                conversation_data = json.load(f)
            # Retrieve the conversation history
            conversation_history = conversation_data['main_conversation'] + conversation_data['running_conversation']
            # Display the conversation history in the text widget
            for entry in conversation_history:
                if isinstance(entry, list):
                    message = '\n'.join(entry)
                else:
                    message = entry
                self.conversation_text.insert(tk.END, message + '\n\n')
        except FileNotFoundError:
            base_path = "./Aetherius_API/Chatbot_Prompts"
            base_prompts_path = os.path.join(base_path, "Base")
            user_bot_path = os.path.join(base_path, user_id, bot_name)  
            if not os.path.exists(user_bot_path):
                os.makedirs(user_bot_path)
            prompts_json_path = os.path.join(user_bot_path, "prompts.json")
            base_prompts_json_path = os.path.join(base_prompts_path, "prompts.json")

            if not os.path.exists(prompts_json_path) and os.path.exists(base_prompts_json_path):
                with open(base_prompts_json_path, 'r') as base_file:
                    base_prompts_content = base_file.read()
                with open(prompts_json_path, 'w') as user_file:
                    user_file.write(base_prompts_content)

            with open(prompts_json_path, 'r') as file:
                prompts = json.loads(file.read())
            main_prompt = prompts["main_prompt"].replace('<<NAME>>', bot_name)
            secondary_prompt = prompts["secondary_prompt"]
            greeting_msg = prompts["greeting_prompt"].replace('<<NAME>>', bot_name)
            self.conversation_text.insert(tk.END, greeting_msg + '\n\n')
        self.conversation_text.yview(tk.END)
        
        
    # #  Login Menu 
    # Edit Bot Name
    def choose_bot_name(self):
        # Read the JSON configuration file
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
            
        current_bot_name = settings.get('Current_Ui_Bot_Name', '')
        username = settings.get('Current_Ui_Username', '')
        user_id = settings.get('Current_Ui_User_ID', '')

        dark_bg_color = "#2B2B2B"
        light_text_color = "#ffffff"

        # Use current_bot_name as the initialvalue for the simpledialog
        bot_name = simpledialog.askstring("Choose Bot Name", "Type a Bot Name:", initialvalue=current_bot_name)
        if bot_name:
            # Update the bot name in the JSON settings file
            settings['Current_Ui_Bot_Name'] = bot_name
            with open('./Aetherius_API/chatbot_settings.json', 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            
            self.conversation_text.delete("1.0", tk.END)
            self.display_conversation_history()
            self.master.destroy()
            Aetherius_GUI()
        

    # Edit User Name
    def choose_username(self):
        # Load settings from JSON file
        # Read the JSON configuration file
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
            
        bot_name = settings.get('Current_Ui_Bot_Name', '')
        current_username = settings.get('Current_Ui_Username', '')
        user_id = settings.get('Current_Ui_User_ID', '')
        dark_bg_color = "#2B2B2B"
        light_text_color = "#ffffff"


        # Use current_username as the initialvalue for the simpledialog
        username = simpledialog.askstring("Choose Username", "Type a Username:", initialvalue=current_username)

        if username:
            # Update username in the JSON settings
            settings['Current_Ui_Username'] = username
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)


            self.conversation_text.delete("1.0", tk.END)
            self.display_conversation_history()
            self.master.destroy()
            Aetherius_GUI()
        pass
        
        
    # Edit User Name
    def choose_user_id(self):
        # Load settings from JSON file
        # Read the JSON configuration file
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
            
        bot_name = settings.get('Current_Ui_Bot_Name', '')
        current_username = settings.get('Current_Ui_Username', '')
        current_user_id = settings.get('Current_Ui_User_ID', '')
        dark_bg_color = "#2B2B2B"
        light_text_color = "#ffffff"


        # Use current_username as the initialvalue for the simpledialog
        user_id = simpledialog.askstring("Choose User ID", "Type a User ID:", initialvalue=current_user_id)

        if user_id:
            # Update username in the JSON settings
            settings['Current_Ui_User_ID'] = user_id
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)


            self.conversation_text.delete("1.0", tk.END)
            self.display_conversation_history()
            self.master.destroy()
            Aetherius_GUI()
        pass
        
        
    # Edits Main Chatbot System Prompt
    def Edit_Main_Prompt(self):
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        bot_name = settings.get('Current_Ui_Bot_Name', '')
        username = settings.get('Current_Ui_Username', '')
        user_id = settings.get('Current_Ui_User_ID', '')
        file_path = f"./Aetherius_API/Chatbot_Prompts/{user_id}/{bot_name}/prompts.json"
        dark_bg_color = "#2B2B2B"
        light_text_color = "#ffffff"

        with open(file_path, 'r', encoding='utf-8') as file:
            prompt_data = json.load(file)
            prompt_contents = prompt_data.get('main_prompt', '')

        top = tk.Toplevel(self)
        top.configure(bg=dark_bg_color)
        top.title("Edit Main Prompt")

        prompt_text = tk.Text(top, height=10, width=60, bg=dark_bg_color, fg=light_text_color)
        prompt_text.insert(tk.END, prompt_contents)
        prompt_text.pack()

        def save_prompt():
            new_prompt = prompt_text.get("1.0", tk.END).strip()
            prompt_data['main_prompt'] = new_prompt
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(prompt_data, file, indent=4)
            self.conversation_text.delete("1.0", tk.END)
            self.display_conversation_history()

        save_button = customtkinter.CTkButton(top, text="Save", command=save_prompt)
        save_button.pack()
        
        
    # Edit secondary prompt (Less priority than main prompt)    
    def Edit_Secondary_Prompt(self):
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        bot_name = settings.get('Current_Ui_Bot_Name', '')
        username = settings.get('Current_Ui_Username', '')
        user_id = settings.get('Current_Ui_User_ID', '')
        file_path = f"./Aetherius_API/Chatbot_Prompts/{user_id}/{bot_name}/prompts.json"
        dark_bg_color = "#2B2B2B"
        light_text_color = "#ffffff"
        
        with open(file_path, 'r', encoding='utf-8') as file:
            prompt_data = json.load(file)
            prompt_contents = prompt_data.get('secondary_prompt', '')
        
        top = tk.Toplevel(self)
        top.configure(bg=dark_bg_color)
        top.title("Edit Secondary Prompt")
        
        prompt_text = tk.Text(top, height=10, width=60, bg=dark_bg_color, fg=light_text_color)
        prompt_text.insert(tk.END, prompt_contents)
        prompt_text.pack()
        
        def save_prompt():
            new_prompt = prompt_text.get("1.0", tk.END).strip()
            prompt_data['secondary_prompt'] = new_prompt
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(prompt_data, file, indent=4)
            self.conversation_text.delete("1.0", tk.END)
            self.display_conversation_history()
        
        save_button = customtkinter.CTkButton(top, text="Save", command=save_prompt)
        save_button.pack()
        
        
    # Edits initial chatbot greeting, called in create widgets
    def Edit_Greeting_Prompt(self):
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        bot_name = settings.get('Current_Ui_Bot_Name', '')
        username = settings.get('Current_Ui_Username', '')
        user_id = settings.get('Current_Ui_User_ID', '')
        file_path = f"./Aetherius_API/Chatbot_Prompts/{user_id}/{bot_name}/prompts.json"
        dark_bg_color = "#2B2B2B"
        light_text_color = "#ffffff"

        with open(file_path, 'r', encoding='utf-8') as file:
            prompt_data = json.load(file)
            prompt_contents = prompt_data.get('greeting_prompt', '')
        
        top = tk.Toplevel(self)
        top.configure(bg=dark_bg_color)
        top.title("Edit Greeting Prompt")
        
        prompt_text = tk.Text(top, height=10, width=60, bg=dark_bg_color, fg=light_text_color)
        prompt_text.insert(tk.END, prompt_contents)
        prompt_text.pack()
        
        def save_prompt():
            new_prompt = prompt_text.get("1.0", tk.END).strip()
            prompt_data['greeting_prompt'] = new_prompt
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(prompt_data, file, indent=4)
            self.conversation_text.delete("1.0", tk.END)
            self.display_conversation_history()
        
        save_button = customtkinter.CTkButton(top, text="Save", command=save_prompt)
        save_button.pack()
        
        
    # Edits running conversation list
    def Edit_Conversation(self):
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        bot_name = settings.get('Current_Ui_Bot_Name', '')
        username = settings.get('Current_Ui_Username', '')
        user_id = settings.get('Current_Ui_User_ID', '')
        file_path = f"./history/{user_id}/{bot_name}_main_conversation_history.json"
        dark_bg_color = "#2B2B2B"
        light_text_color = "#ffffff"
        customtkinter.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"

        with open(file_path, 'r', encoding='utf-8') as file:
            conversation_data = json.load(file)

        running_conversation = conversation_data.get("running_conversation", [])

        top = tk.Toplevel(self)
        top.configure(bg=dark_bg_color)
        top.title("Edit Running Conversation")
        
        entry_texts = []  # List to store the entry text widgets

        def update_entry():
            nonlocal entry_index
            entry_text.delete("1.0", tk.END)
            entry_text.insert(tk.END, running_conversation[entry_index].strip())
            entry_number_label.configure(text=f"Entry {entry_index + 1}/{len(running_conversation)}", bg_color=dark_bg_color)

        entry_index = 0

        entry_text = tk.Text(top, height=10, width=60, bg=dark_bg_color, fg=light_text_color)
        entry_text.pack(fill=tk.BOTH, expand=True)
        entry_texts.append(entry_text)  # Store the reference to the entry text widget

        entry_number_label = customtkinter.CTkLabel(top, bg_color=dark_bg_color, text=f"Entry {entry_index + 1}/{len(running_conversation)}")
        entry_number_label.pack()
        
        button_frame = tk.Frame(top, bg=dark_bg_color)
        button_frame.pack()

        update_entry()

        def go_back():
            nonlocal entry_index
            if entry_index > 0:
                entry_index -= 1
                update_entry()

        def go_forward():
            nonlocal entry_index
            if entry_index < len(running_conversation) - 1:
                entry_index += 1
                update_entry()

# Navigation Frame
        navigation_frame = tk.Frame(top, bg=dark_bg_color)
        navigation_frame.pack(pady=10)  # Add some padding to separate the frames

        back_button = customtkinter.CTkButton(navigation_frame, text="Back", command=go_back, bg_color=dark_bg_color)
        back_button.pack(side=tk.LEFT, padx=5)

        forward_button = customtkinter.CTkButton(navigation_frame, text="Forward", command=go_forward, bg_color=dark_bg_color)
        forward_button.pack(side=tk.LEFT, padx=5)

        def save_conversation():
            for i, entry_text in enumerate(entry_texts):
                entry_lines = entry_text.get("1.0", tk.END).strip()
                running_conversation[entry_index + i] = entry_lines

            conversation_data["running_conversation"] = running_conversation

            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(conversation_data, file, indent=4, ensure_ascii=False)

            # Update your conversation display or perform any required actions here
            self.conversation_text.delete("1.0", tk.END)
            self.display_conversation_history()
            update_entry()  # Update the displayed entry in the cycling menu

            # Update the entry number label after saving the changes
            entry_number_label.configure(text=f"Entry {entry_index + 1}/{len(running_conversation)}")
        
        def delete_entry():
            nonlocal entry_index
            if len(running_conversation) == 1:
                # If this is the last entry, simply clear the entry_text
                entry_text.delete("1.0", tk.END)
                running_conversation.clear()
            else:
                # Delete the current entry from the running conversation list
                del running_conversation[entry_index]

                # Adjust the entry_index if it exceeds the valid range
                if entry_index >= len(running_conversation):
                    entry_index = len(running_conversation) - 1

                # Update the displayed entry
                update_entry()
                entry_number_label.configure(text=f"Entry {entry_index + 1}/{len(running_conversation)}")

            # Save the conversation after deleting an entry
            save_conversation()

        # Action Frame
        action_frame = tk.Frame(top, bg=dark_bg_color)
        action_frame.pack(pady=10)  # Add some padding to separate the frames

        delete_button = customtkinter.CTkButton(action_frame, text="Delete", command=delete_entry, bg_color=dark_bg_color)
        delete_button.pack(side=tk.LEFT, padx=5)
        
        save_button = customtkinter.CTkButton(action_frame, text="Save", command=save_conversation, bg_color=dark_bg_color)
        save_button.pack(side=tk.LEFT, padx=5)

        # Configure the top level window to scale with the content
        top.pack_propagate(False)
        top.geometry("600x400")  # Set the initial size of the window
        
        
    def update_results(self, text_widget, search_results):
        self.after(0, text_widget.delete, "1.0", tk.END)
        self.after(0, text_widget.insert, tk.END, search_results)
        
        
    def open_cadence_window(self):
        dark_bg_color = "#2B2B2B"
        light_text_color = "#ffffff"
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        bot_name = settings.get('Current_Ui_Bot_Name', '')
        username = settings.get('Current_Ui_Username', '')
        user_id = settings.get('Current_Ui_User_ID', '')
        cadence_window = tk.Toplevel(self)
        cadence_window.configure(bg=dark_bg_color)
        cadence_window.title("Cadence DB Upload")
        query_label = customtkinter.CTkLabel(cadence_window, text="Enter Cadence Example:", bg_color=dark_bg_color)
        query_label.grid(row=0, column=0, padx=5, pady=5)

        query_entry = tk.Entry(cadence_window, bg=dark_bg_color, fg=light_text_color)
        query_entry.grid(row=1, column=0, padx=5, pady=5)

        results_label = customtkinter.CTkLabel(cadence_window, text="Scrape results: ", bg_color=dark_bg_color)
        results_label.grid(row=2, column=0, padx=5, pady=5)

        results_text = tk.Text(cadence_window, bg=dark_bg_color, fg=light_text_color)
        results_text.grid(row=3, column=0, padx=5, pady=5)

        def perform_search():
            query = query_entry.get()

            def update_results():
                # Update the GUI with the new paragraph
                self.results_text.insert(tk.END, f"{query}\n\n")
                self.results_text.yview(tk.END)

            def search_task():
                # Call the modified GPT_3_5_Tasklist_Web_Search function with the callback
                search_results = DB_Upload_Cadence(query)
                self.update_results(results_text, search_results)

            t = threading.Thread(target=search_task)
            t.start()

        def delete_cadence():
            # Replace 'username' and 'bot_name' with appropriate variables if available.
            # You may need to adjust 'vdb' based on how your database is initialized.
            with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            bot_name = settings.get('Current_Ui_Bot_Name', '')
            username = settings.get('Current_Ui_Username', '')
            user_id = settings.get('Current_Ui_User_ID', '')
            confirm = messagebox.askyesno("Confirmation", "Are you sure you want to delete saved cadence?")
            if confirm:
                client.delete(
                    collection_name=f"Bot_{bot_name}",
                    points_selector=models.FilterSelector(
                        filter=models.Filter(
                            must=[
                                models.FieldCondition(
                                    key="memory_type",
                                    match=models.MatchValue(value="Cadence"),
                                ),
                                models.FieldCondition(
                                    key="user",
                                    match=models.MatchValue(value=f"{user_id}"),
                                ),
                            ],
                        )
                    ),
                )  
                # Clear the results_text widget after deleting heuristics (optional)
                results_text.delete("1.0", tk.END)  

        search_button = customtkinter.CTkButton(cadence_window, text="Upload", command=perform_search, bg_color=dark_bg_color)
        search_button.grid(row=4, column=0, padx=5, pady=5)

        # Use `side=tk.LEFT` for the delete button to position it at the top-left corner
        delete_button = customtkinter.CTkButton(cadence_window, text="Delete Cadence", command=delete_cadence, bg_color=dark_bg_color)
        delete_button.grid(row=5, column=0, padx=5, pady=5)
        
        
    def open_heuristics_window(self):
        dark_bg_color = "#2B2B2B"
        light_text_color = "#ffffff"
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        bot_name = settings.get('Current_Ui_Bot_Name', '')
        username = settings.get('Current_Ui_Username', '')
        user_id = settings.get('Current_Ui_User_ID', '')
        heuristics_window = tk.Toplevel(self)
        heuristics_window.configure(bg=dark_bg_color)
        heuristics_window.title("Heuristics DB Upload")

        query_label = customtkinter.CTkLabel(heuristics_window, text="Enter Heuristics:", bg_color=dark_bg_color)
        query_label.grid(row=0, column=0, padx=5, pady=5)

        query_entry = tk.Entry(heuristics_window, bg=dark_bg_color, fg=light_text_color)
        query_entry.grid(row=1, column=0, padx=5, pady=5)

        results_label = customtkinter.CTkLabel(heuristics_window, text="Entered Heuristics: ")
        results_label.grid(row=2, column=0, padx=5, pady=5)

        results_text = tk.Text(heuristics_window, bg=dark_bg_color, fg=light_text_color)
        results_text.grid(row=3, column=0, padx=5, pady=5)

        def perform_search():
            query = query_entry.get()

            def update_results(query):
                # Update the GUI with the new paragraph
                results_text.insert(tk.END, f"{query}\n\n")
                results_text.yview(tk.END)
                query_entry.delete(0, tk.END)

            def search_task():
                # Call the modified GPT_3_5_Tasklist_Web_Search function with the callback
                search_results = DB_Upload_Heuristics(query)

                # Use the `after` method to schedule the `update_results` function on the main Tkinter thread
                heuristics_window.after(0, update_results, search_results)
                   
            t = threading.Thread(target=search_task)
            t.start()
                
        def delete_heuristics():
            # Replace 'username' and 'bot_name' with appropriate variables if available.
            # You may need to adjust 'vdb' based on how your database is initialized.
            with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            bot_name = settings.get('Current_Ui_Bot_Name', '')
            username = settings.get('Current_Ui_Username', '')
            user_id = settings.get('Current_Ui_User_ID', '')
            confirm = messagebox.askyesno("Confirmation", "Are you sure you want to delete heuristics?")
            if confirm:
                client.delete(
                    collection_name=f"Bot_{bot_name}",
                    points_selector=models.FilterSelector(
                        filter=models.Filter(
                            must=[
                                models.FieldCondition(
                                    key="memory_type",
                                    match=models.MatchValue(value="Heuristics"),
                                ),
                                models.FieldCondition(
                                    key="user",
                                    match=models.MatchValue(value=f"{user_id}"),
                                ),
                            ],
                        )
                    ),
                )    
                # Clear the results_text widget after deleting heuristics (optional)
                results_text.delete("1.0", tk.END)  

        search_button = customtkinter.CTkButton(heuristics_window, text="Upload", command=perform_search, bg_color=dark_bg_color)
        search_button.grid(row=4, column=0, padx=5, pady=5)

        # Use `side=tk.LEFT` for the delete button to position it at the top-left corner
        delete_button = customtkinter.CTkButton(heuristics_window, text="Delete Heuristics", command=delete_heuristics, bg_color=dark_bg_color)
        delete_button.grid(row=5, column=0, padx=5, pady=5)
        
        
    def open_long_term_window(self):
        dark_bg_color = "#2B2B2B"
        light_text_color = "#ffffff"
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        bot_name = settings.get('Current_Ui_Bot_Name', '')
        username = settings.get('Current_Ui_Username', '')
        user_id = settings.get('Current_Ui_User_ID', '')
        long_term_window = tk.Toplevel(self)
        long_term_window.configure(bg=dark_bg_color)
        long_term_window.title("Long Term Memory DB Upload")


        query_label = customtkinter.CTkLabel(long_term_window, text="Enter Memory:", bg_color=dark_bg_color)
        query_label.grid(row=0, column=0, padx=5, pady=5)

        query_entry = tk.Entry(long_term_window, bg=dark_bg_color, fg=light_text_color)
        query_entry.grid(row=1, column=0, padx=5, pady=5)

        results_label = customtkinter.CTkLabel(long_term_window, text="Entered Memories: ")
        results_label.grid(row=2, column=0, padx=5, pady=5)

        results_text = tk.Text(long_term_window, bg=dark_bg_color, fg=light_text_color)
        results_text.grid(row=3, column=0, padx=5, pady=5)

        # LATER Replace with API upload functions.
        def perform_implicit_upload():
            query = query_entry.get()

            def update_results(query):
                # Update the GUI with the new paragraph
                results_text.insert(tk.END, f"{query}\n\n")
                results_text.yview(tk.END)
                query_entry.delete(0, tk.END)

            def search_task():
                # Call the modified GPT_3_5_Tasklist_Web_Search function with the callback
                search_results = upload_implicit_long_term_memories(query)

                # Use the `after` method to schedule the `update_results` function on the main Tkinter thread
                long_term_window.after(0, update_results, search_results)
                   
            t = threading.Thread(target=search_task)
            t.start()
            
            
        def perform_explicit_upload():
            query = query_entry.get()

            def update_results(query):
                # Update the GUI with the new paragraph
                results_text.insert(tk.END, f"{query}\n\n")
                results_text.yview(tk.END)
                query_entry.delete(0, tk.END)

            def search_task():
                # Call the modified GPT_3_5_Tasklist_Web_Search function with the callback
                search_results = upload_explicit_long_term_memories(query)

                # Use the `after` method to schedule the `update_results` function on the main Tkinter thread
                long_term_window.after(0, update_results, search_results)
                   
            t = threading.Thread(target=search_task)
            t.start()


        implicit_search_button = customtkinter.CTkButton(long_term_window, text="Implicit Upload", command=perform_implicit_upload, bg_color=dark_bg_color)
        implicit_search_button.grid(row=4, column=0, padx=5, pady=5, columnspan=1)  # Set columnspan to 1

        explicit_search_button = customtkinter.CTkButton(long_term_window, text="Explicit Upload", command=perform_explicit_upload, bg_color=dark_bg_color)
        explicit_search_button.grid(row=5, column=0, padx=5, pady=5, columnspan=1) 
        
        
    def open_deletion_window(self):
        dark_bg_color = "#2B2B2B"
        light_text_color = "#ffffff"
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        bot_name = settings.get('Current_Ui_Bot_Name', '')
        username = settings.get('Current_Ui_Username', '')
        user_id = settings.get('Current_Ui_User_ID', '')
        deletion_window = tk.Toplevel(self)
        deletion_window.configure(bg=dark_bg_color)
        deletion_window.title("DB Deletion Menu")
        
        
        def delete_cadence():
                # Replace 'username' and 'bot_name' with appropriate variables if available.
                # You may need to adjust 'vdb' based on how your database is initialized.
            with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            bot_name = settings.get('Current_Ui_Bot_Name', '')
            username = settings.get('Current_Ui_Username', '')
            user_id = settings.get('Current_Ui_User_ID', '')
            confirm = messagebox.askyesno("Confirmation", "Are you sure you want to delete saved cadence?")
            if confirm:
                client.delete(
                    collection_name=f"Bot_{bot_name}",
                    points_selector=models.FilterSelector(
                        filter=models.Filter(
                            must=[
                                models.FieldCondition(
                                    key="memory_type",
                                    match=models.MatchValue(value="Cadence"),
                                ),
                                models.FieldCondition(
                                    key="user",
                                    match=models.MatchValue(value=f"{user_id}"),
                                ),
                            ],
                        )
                    ),
                )   
        
    
        def delete_heuristics():
                # Replace 'username' and 'bot_name' with appropriate variables if available.
                # You may need to adjust 'vdb' based on how your database is initialized.
            with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            bot_name = settings.get('Current_Ui_Bot_Name', '')
            username = settings.get('Current_Ui_Username', '')
            user_id = settings.get('Current_Ui_User_ID', '')
            confirm = messagebox.askyesno("Confirmation", "Are you sure you want to delete heuristics?")
            if confirm:
                client.delete(
                    collection_name=f"Bot_{bot_name}",
                    points_selector=models.FilterSelector(
                        filter=models.Filter(
                            must=[
                                models.FieldCondition(
                                    key="memory_type",
                                    match=models.MatchValue(value="Heuristics"),
                                ),
                                models.FieldCondition(
                                    key="user",
                                    match=models.MatchValue(value=f"{user_id}"),
                                ),
                            ],
                        )
                    ),
                )   
                
                
        def delete_counters():
                # Replace 'username' and 'bot_name' with appropriate variables if available.
                # You may need to adjust 'vdb' based on how your database is initialized.
            with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            bot_name = settings.get('Current_Ui_Bot_Name', '')
            username = settings.get('Current_Ui_Username', '')
            user_id = settings.get('Current_Ui_User_ID', '')
            confirm = messagebox.askyesno("Confirmation", "Are you sure you want to delete memory consolidation counters?")
            if confirm:
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
                client.delete(
                    collection_name=f"Consol_Counter_Bot_{bot_name}_{user_id}",
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
                
        def delete_webscrape():
                # Replace 'username' and 'bot_name' with appropriate variables if available.
                # You may need to adjust 'vdb' based on how your database is initialized.
            with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            bot_name = settings.get('Current_Ui_Bot_Name', '')
            username = settings.get('Current_Ui_Username', '')
            user_id = settings.get('Current_Ui_User_ID', '')
            confirm = messagebox.askyesno("Confirmation", "Are you sure you want to delete the saved webscrape?")
            if confirm:
                client.delete(
                    collection_name=f"Bot_{bot_name}_External_Knowledgebase",
                    points_selector=models.FilterSelector(
                        filter=models.Filter(
                            must=[
                                models.FieldCondition(
                                    key="user",
                                    match=models.MatchValue(value=f"{user_id}"),
                                ),
                                models.FieldCondition(
                                    key="memory_type",
                                    match=models.MatchValue(value=f"Web_Scrape"),
                                ),
                            ],
                        )
                    ),
                ) 
                client.delete(
                    collection_name=f"Bot_{bot_name}_External_Knowledgebase",
                    points_selector=models.FilterSelector(
                        filter=models.Filter(
                            must=[
                                models.FieldCondition(
                                    key="user",
                                    match=models.MatchValue(value=f"{user_id}"),
                                ),
                                models.FieldCondition(
                                    key="memory_type",
                                    match=models.MatchValue(value=f"Web_Scrape_Temp"),
                                ),
                            ],
                        )
                    ),
                ) 
                
        def delete_filescrape():
                # Replace 'username' and 'bot_name' with appropriate variables if available.
                # You may need to adjust 'vdb' based on how your database is initialized.
            with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            bot_name = settings.get('Current_Ui_Bot_Name', '')
            username = settings.get('Current_Ui_Username', '')
            user_id = settings.get('Current_Ui_User_ID', '')
            confirm = messagebox.askyesno("Confirmation", "Are you sure you want to delete the saved scraped files?")
            if confirm:
                client.delete(
                    collection_name=f"Bot_{bot_name}_External_Knowledgebase",
                    points_selector=models.FilterSelector(
                        filter=models.Filter(
                            must=[
                                models.FieldCondition(
                                    key="user",
                                    match=models.MatchValue(value=f"{user_id}"),
                                ),
                                models.FieldCondition(
                                    key="memory_type",
                                    match=models.MatchValue(value=f"File_Scrape"),
                                ),
                            ],
                        )
                    ),
                ) 

                
                
        def delete_bot():
                # Replace 'username' and 'bot_name' with appropriate variables if available.
                # You may need to adjust 'vdb' based on how your database is initialized.
            with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            bot_name = settings.get('Current_Ui_Bot_Name', '')
            username = settings.get('Current_Ui_Username', '')
            user_id = settings.get('Current_Ui_User_ID', '')
            confirm = messagebox.askyesno("Confirmation", f"Are you sure you want to delete {bot_name} in their entirety?")
            if confirm:
                try:
                    client.delete(
                        collection_name=f"Bot_{bot_name}",
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
                except:
                    pass
                try:
                    client.delete(
                        collection_name=f"Bot_{bot_name}_External_Knowledgebase",
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
                except:
                    pass
                try:
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
                except:
                    pass
                try:
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
                except:
                    pass
                try:
                    client.delete(
                        collection_name=f"Flash_Counter_Bot_{bot_name}",
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
                except:
                    pass
                try:
                    client.delete(
                        collection_name=f"Consol_Counter_Bot_{bot_name}_{user_id}",
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
                except:
                    pass
                
                
        delete_cadence_button = customtkinter.CTkButton(deletion_window, text="Delete Cadence", command=delete_cadence)
        delete_cadence_button.pack()
                
        delete_heuristics_button = customtkinter.CTkButton(deletion_window, text="Delete Heuristics", command=delete_heuristics)
        delete_heuristics_button.pack()
        
        delete_webscrape_button = customtkinter.CTkButton(deletion_window, text="Delete Webscrape DB", command=delete_webscrape)
        delete_webscrape_button.pack()
        
        delete_filescrape_button = customtkinter.CTkButton(deletion_window, text="Delete File DB", command=delete_filescrape)
        delete_filescrape_button.pack()
        
        delete_counters_button = customtkinter.CTkButton(deletion_window, text="Delete Memory Consolidation Counters", command=delete_counters)
        delete_counters_button.pack()
        
        delete_bot_button = customtkinter.CTkButton(deletion_window, text="Delete Entire Chatbot", command=delete_bot)
        delete_bot_button.pack()
        
        
    def delete_conversation_history(self):
        # Delete the conversation history JSON file
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        bot_name = settings.get('Current_Ui_Bot_Name', '')
        username = settings.get('Current_Ui_Username', '')
        user_id = settings.get('Current_Ui_User_ID', '')
        file_path = f'./history/{user_id}/{bot_name}_main_conversation_history.json'
        try:
            os.remove(file_path)
            # Reload the script
            self.master.destroy()
            Aetherius_GUI()
        except FileNotFoundError:
            pass


    def send_message(self):
        a = self.user_input.get("1.0", tk.END).strip()  # Get all the text from line 1, column 0 to the end.
        self.user_input.delete("1.0", tk.END)  # Clear all the text in the widget.
    #    self.user_input.configure(state=tk.DISABLED)
        self.send_button.configure(state=tk.DISABLED)
        self.voice_button.configure(state=tk.DISABLED)
        self.user_input.unbind("<Return>")
        # Display "Thinking..." in the input field
    #    self.thinking_label.grid(row=2, column=2, pady=3)
        self.user_input.insert(tk.END, f"Thinking...\n\nPlease Wait...")
        self.user_input.configure(state=tk.DISABLED)
        t = threading.Thread(target=self.process_message, args=(a,))
        t.start()
        
    # For this function, have it open a file selection window, then send the image to gpt vision along with the entered text in the window.
    # Should Function like the discord bot
    def initiate_image_model(self):
        user_input = self.user_input.get("1.0", tk.END).strip()
        filetypes = [
            ("Supported Files", "*.png *.jpg *.jpeg"),
            ("All Files", "*.*")
        ]
        image_path = filedialog.askopenfilename(filetypes=filetypes)
        if image_path:
            self.user_input.delete("1.0", tk.END)  # Clear all the text in the widget.
            self.send_button.configure(state=tk.DISABLED)
            self.voice_button.configure(state=tk.DISABLED)
            self.user_input.unbind("<Return>")
            self.user_input.insert(tk.END, f"Thinking...\n\nPlease Wait...")
            self.user_input.configure(state=tk.DISABLED)
            t = threading.Thread(target=self.process_message, args=(user_input, image_path,))
            t.start()
        
    def initiate_record_audio(self):
        self.is_recording = True
        self.user_input.delete("1.0", tk.END)  # Clear all the text in the widget.
        self.user_input.insert(tk.END, f"Press and hold the Right Alt key to record...")
        self.send_button.configure(state=tk.DISABLED)
        self.voice_button.configure(state=tk.DISABLED)
        self.user_input.unbind("<Return>")
        audio_thread = threading.Thread(target=self.record_audio)
        audio_thread.start()
        
    def record_audio(self):
        print("Press and hold the Right Alt key to record...")

     #   self.user_input.insert(tk.END, f"Press and hold the Right Alt key to record...")
        filename = 'audio'

        # Initialize variables
        duration = None  # Variable duration
        sample_rate = 44100  # 44.1kHz
        channels = 2  # Stereo
        dtype = np.int16  # 16-bit PCM format
        audio_data = np.empty((0, channels), dtype=dtype)

        while True:
            if keyboard.is_pressed('right alt'):
                if len(audio_data) == 0:
                    print("Recording...")
                
                # Record 100ms chunks while the key is down
                audio_chunk = sd.rec(int(sample_rate * 0.1), samplerate=sample_rate, channels=channels, dtype=dtype)
                sd.wait()
                
                # Append chunk to audio data
                audio_data = np.vstack([audio_data, audio_chunk])

            elif len(audio_data) > 0:
                print("Stopped recording.")
                break

        # Save audio as a WAV file first
        write('audio.wav', sample_rate, audio_data)

        # Use FFmpeg to convert WAV to MP3
        subprocess.run(['ffmpeg', '-i', 'audio.wav', 'audio.mp3'])
        print(f"Saved as {filename}.mp3")
        
        model_stt = whisper.load_model("base")
        result = model_stt.transcribe("audio.mp3")
        a = result["text"]
        os.remove("audio.wav")
        os.remove("audio.mp3")
        # Display "Thinking..." in the input field
    #    self.thinking_label.grid(row=2, column=2, pady=3)
        self.user_input.delete("1.0", tk.END)
        self.user_input.insert(tk.END, f"Thinking...\n\nPlease Wait...")
        self.user_input.configure(state=tk.DISABLED)
        t = threading.Thread(target=self.process_message, args=(a,))
        t.start()


    def process_message(self, a, image_path=None):
        self.conversation_text.insert(tk.END, f"\nYou: {a}\n\n")
        self.conversation_text.yview(tk.END)
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)

        bot_name = settings.get('Current_Ui_Bot_Name', '')
        username = settings.get('Current_Ui_Username', '')
        user_id = settings.get('Current_Ui_User_ID', '')
        if image_path is not None:
            print(f"Processing message: {a}, Image path: {image_path}")
        if self.is_agent_mode_checked():
            asyncio.run_coroutine_threadsafe(self.async_agent_task(a, username, user_id, bot_name, self.handle_response, image_path), self.loop)
        else:
            asyncio.run_coroutine_threadsafe(self.async_chatbot_task(a, username, user_id, bot_name, self.handle_response, image_path), self.loop)

    def handle_response(self, response):
        # Schedule UI update in the main thread
        self.conversation_text.after(0, self.update_ui, response)
            # Retrieve the TTS model setting from the dictionary
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings_dict = json.load(f)
        tts_model = settings_dict.get('TTS', 'gTTS')
        if self.is_tts_checked():
            if tts_model == 'barkTTS':
                audio_thread = threading.Thread(target=audio_player)
                audio_thread.start()
                TTS_Generation(response)
            else:
                t = threading.Thread(target=TTS_Generation, args=(response,))
                t.start()

    def update_ui(self, response):
        if isinstance(response, str):
            formatted_response = response.replace('\\n', '\n')
        else:
            formatted_response = str(response)

        self.conversation_text.insert(tk.END, "Response: " + formatted_response + "\n\n")

        self.conversation_text.yview(tk.END)
        self.user_input.delete(0, tk.END)
        self.user_input.focus()
        self.user_input.configure(state=tk.NORMAL)
        self.user_input.delete("1.0", tk.END)
        self.is_recording = False 
        self.send_button.configure(state=tk.NORMAL)
        self.voice_button.configure(state=tk.NORMAL)
        self.thinking_label.pack_forget()
    #    self.user_input.delete(0, tk.END)
        self.bind_right_alt_key()
        self.bind_enter_key()

    async def async_chatbot_task(self, a, username, user_id, bot_name, callback, image_path):
        try:
            response = await Aetherius_Chatbot(a, username, user_id, bot_name, image_path)
            
            self.conversation_text.after(0, callback, response)
        except:
            traceback.print_exc()
        
    async def async_agent_task(self, a, username, user_id, bot_name, callback, image_path):
        try:
            response = await Aetherius_Agent(a, username, user_id, bot_name, image_path)
            self.conversation_text.after(0, callback, response)
        except:
            traceback.print_exc()
        
    def open_websearch_window(self):
        websearch_window = tk.Toplevel(self)
        websearch_window.title("Web Search")

        query_label = tk.Label(websearch_window, text="Enter your query:")
        query_label.pack()

        query_entry = tk.Entry(websearch_window)
        query_entry.pack()

        results_label = tk.Label(websearch_window, text="Search results: (Not Working Yet, Results in Terminal)")
        results_label.pack()

        results_text = tk.Text(websearch_window)
        results_text.pack()

        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        API = settings.get('API', 'AetherNode')
        backend_model = settings.get('Model_Backend', 'Llama_2_Chat')
        LLM_Model = settings.get('LLM_Model', 'AetherNode')
        bot_name = settings.get('Current_Ui_Bot_Name', '')
        username = settings.get('Current_Ui_Username', '')
        user_id = settings.get('Current_Ui_User_ID', '')
        def perform_search():
            query = query_entry.get()

            def update_results(paragraph):
                # Update the GUI with the new paragraph
                results_text.insert(tk.END, f"{paragraph}\n\n")
                results_text.yview(tk.END)
            #    self.update_results(results_text, paragraph)

            def search_task():
                # Call the modified GPT_4_Tasklist_Web_Search function with the callback
                GPT_4_Tasklist_Web_Search(query, results_callback=update_results) # LATER Replace with Aetherius API Webcall

            t = threading.Thread(target=search_task)
            t.start()
            
        def perform_scrape():
            query = query_entry.get()

            async def async_wrapper():
                await async_chunk_text_from_url(query, user_id, bot_name)  # Assuming this is an async function you've defined elsewhere

            def update_results(paragraph):
                # Update the GUI with the new paragraph
                results_text.insert(tk.END, f"{paragraph}\n\n")
                results_text.yview(tk.END)

            def search_task():
                asyncio.run(async_wrapper())  # This will run the async function in an event loop

            t = threading.Thread(target=search_task)
            t.start()

        scrape_button = tk.Button(websearch_window, text="Scrape", command=perform_scrape)
        scrape_button.pack()

        search_button = tk.Button(websearch_window, text="Search", command=perform_search)
        search_button.pack()
        
        
        
        
        
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
            destination_folders = ["./Upload/EPUB", "./Upload/PDF", "./Upload/TXT", "./Upload/SCANS", "./Upload/VIDEOS"]
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
                ("Supported Files", "*.epub *.pdf *.txt *.png *.jpg *.jpeg *.mp4 *.mkv *.flv *.avi"),
                ("All Files", "*.*")
            ]
            file_path = filedialog.askopenfilename(filetypes=filetypes)
            if file_path:
                process_file(file_path)

        def process_file(file_path):
            file_name = os.path.basename(file_path)  # Extracting just the filename from the full path
            extension = os.path.splitext(file_name)[1].lower()  # Extracting and converting the file extension to lowercase
            
            # Directory assignment based on file extension
            if extension == ".epub":
                destination_folder = "./Upload/EPUB"
            elif extension == ".pdf":
                destination_folder = "./Upload/PDF"
            elif extension == ".txt":
                destination_folder = "./Upload/TXT"
            elif extension in [".png", ".jpg", ".jpeg"]:
                destination_folder = "./Upload/SCANS"
            elif extension in [".mp4", ".mkv", ".flv", ".avi"]:
                destination_folder = "./Upload/VIDEOS"
            else:
                update_results(f"Unsupported file type: {extension}")
                return

            # Destination path
            destination_path = os.path.join(destination_folder, file_name)

            # File copy operation
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
                asyncio.run(GPT_4_Text_Extract())

            t = threading.Thread(target=search_task)
            t.start()
                

        def update_results(text):
            results_text.insert(tk.END, text + "\n")
            results_text.see(tk.END)

        file_button = tk.Button(fileprocess_window, text="Browse", command=select_file)
        file_button.pack()

        search_button = tk.Button(fileprocess_window, text="Process", command=perform_search)
        search_button.pack()
        
        
    def handle_menu_selection(self, event):
        selection = self.menu.get()
        if selection == "Edit Font":
            self.Edit_Font()
        elif selection == "Edit Font Size":
            self.Edit_Font_Size()
            
            
    def handle_login_menu_selection(self, event):
        try:
            selection = self.login_menu.get()
            if selection == "Choose Bot Name":
                self.choose_bot_name()
            elif selection == "Choose Username":
                self.choose_username() 
            elif selection == "Choose User ID":
                self.choose_user_id() 
            elif selection == "Edit Main Prompt":
                self.Edit_Main_Prompt()
            elif selection == "Edit Secondary Prompt":
                self.Edit_Secondary_Prompt()
            elif selection == "Edit Greeting Prompt":
                self.Edit_Greeting_Prompt()
        except Exception as e:
            print(f"Error in handle_login_menu_selection: {e}")
            
            
    def handle_db_menu_selection(self, event):
        print("Combobox selected!")
        selection = self.db_menu.get()
        if selection == "Cadence DB":
            self.open_cadence_window()
        elif selection == "Heuristics DB":
            self.open_heuristics_window()
        elif selection == "Long Term Memory DB":
            self.open_long_term_window()
        elif selection == "DB Deletion":
            self.open_deletion_window()  

        
    # Selects which Open Ai model to use.   # LATER REPLACE WITH MODEL BACKEND SELECTION 
    def Model_Selection(self):
        file_path = "./config/model.txt"
        dark_bg_color = "#2B2B2B"
        light_text_color = "#ffffff"
        
        with open(file_path, 'r', encoding='utf-8') as file:
            prompt_contents = file.read()
        
        top = tk.Toplevel(self)
        top.configure(bg=dark_bg_color)
        top.title("Select a Model")
        
        models_label = customtkinter.CTkLabel(top, text="Available Models: gpt_35, gpt_35_16, gpt_4")
        models_label.pack()
        
        prompt_text = tk.Text(top, height=10, width=60, bg=dark_bg_color, fg=light_text_color)
        prompt_text.insert(tk.END, prompt_contents)
        prompt_text.pack()
        
        def save_prompt():
            new_prompt = prompt_text.get("1.0", tk.END).strip()
            with open(file_path, 'w') as file:
                file.write(new_prompt)
            self.conversation_text.delete("1.0", tk.END)
            self.display_conversation_history()
        
        save_button = customtkinter.CTkButton(top, text="Save", command=save_prompt)
        save_button.pack()
        
        
    # Change Font Style, called in create widgets
    def Edit_Font(self):
        file_path = "./Aetherius_API/chatbot_settings.json" 
        dark_bg_color = "#2B2B2B"
        light_text_color = "#ffffff"

        # Read font_value from the JSON file instead of the .txt file
        with open(file_path, 'r', encoding='utf-8') as file:
            settings = json.load(file)
            font_value = settings.get("font", "")  # Default to an empty string if the key is not found

        fonts = font.families()

        top = tk.Toplevel(self)
        top.configure(bg=dark_bg_color)
        top.title("Edit Font")

        font_listbox = tk.Listbox(top, bg=dark_bg_color, fg=light_text_color)
        font_listbox.pack()
        for font_name in fonts:
            font_listbox.insert(tk.END, font_name)
            
        label = customtkinter.CTkLabel(top, text="Enter the Font Name:")
        label.pack()

        font_entry = tk.Entry(top, bg=dark_bg_color, fg=light_text_color)
        font_entry.insert(tk.END, font_value)
        font_entry.pack()

        def save_font():
            new_font = font_entry.get()
            if new_font in fonts:
                # Update the JSON file
                settings["font"] = new_font
                with open(file_path, 'w', encoding='utf-8') as file:
                    json.dump(settings, file, indent=4, ensure_ascii=False)
                self.update_font_settings()
            top.destroy()
            
        save_button = customtkinter.CTkButton(top, text="Save", command=save_font)
        save_button.pack()

        

    # Change Font Size, called in create widgets
    def Edit_Font_Size(self):
        json_file_path = "./Aetherius_API/chatbot_settings.json"  # Change the path to your JSON file
        dark_bg_color = "#2B2B2B"
        light_text_color = "#ffffff"

        # Read the JSON file to get the font size
        with open(json_file_path, 'r', encoding='utf-8') as file:
            settings_dict = json.load(file)
            font_size_value = settings_dict.get("font_size", "")  # Provide a default value if "font_size" is not present

        top = tk.Toplevel(self)
        top.configure(bg=dark_bg_color)
        top.title("Edit Font Size")

        label = customtkinter.CTkLabel(top, text="Enter the Font Size:")
        label.pack()

        self.font_size_entry = tk.Entry(top, bg=dark_bg_color, fg=light_text_color)
        self.font_size_entry.insert(tk.END, font_size_value)
        self.font_size_entry.pack()

        def save_font_size():
            new_font_size = self.font_size_entry.get()
            if new_font_size.isdigit():
                # Update the JSON file with the new font size
                settings_dict["font_size"] = new_font_size
                with open(json_file_path, 'w', encoding='utf-8') as file:
                    json.dump(settings_dict, file, indent=4)
                self.update_font_settings()
            top.destroy()

        save_button = customtkinter.CTkButton(top, text="Save", command=save_font_size)
        save_button.pack()

        top.mainloop()
        
        
    # Change Conversation Length, called in create widgets
    def Set_Conv_Length(self):
        file_path = "./Aetherius_API/chatbot_settings.json"  # Point to the JSON file instead of the TXT file
        dark_bg_color = "#2B2B2B"
        light_text_color = "#ffffff"

        # Read the value from the JSON file
        with open(file_path, 'r', encoding='utf-8') as file:
            settings = json.load(file)
            font_size_value = settings.get("Conversation_Length", "2")

        top = tk.Toplevel(self)
        top.configure(bg=dark_bg_color)
        top.title("Set Converation Length")

        label = customtkinter.CTkLabel(top, text="(Lengths longer than 2 tend to break smaller models.\nEnter desired conversation length:")
        label.pack()

        self.font_size_entry = tk.Entry(top, bg=dark_bg_color, fg=light_text_color)
        self.font_size_entry.insert(tk.END, font_size_value)
        self.font_size_entry.pack()

        def save_conv_length():
            new_font_size = self.font_size_entry.get()
            if new_font_size.isdigit():
                # Update the JSON file instead of the TXT file
                settings["Conversation_Length"] = new_font_size
                with open(file_path, 'w', encoding='utf-8') as file:
                    json.dump(settings, file, indent=4)
            top.destroy()

        save_button = customtkinter.CTkButton(top, text="Save", command=save_conv_length)
        save_button.pack()

        top.mainloop()
        
        
    # Change Host, called in create widgets # LATER Add a place for editing Oobabooga Hosts
    def Set_Host(self):
        file_path = "./Aetherius_API/chatbot_settings.json"  # Point to the JSON file
        dark_bg_color = "#2B2B2B"
        light_text_color = "#ffffff"

        # Use json to read the host value
        with open(file_path, 'r', encoding='utf-8') as file:
            settings = json.load(file)
            host_value = settings.get("HOST_AetherNode", "")  # Replace 'HOST_AetherNode' with the actual key if different

        top = tk.Toplevel(self)
        top.configure(bg=dark_bg_color)
        top.title("Set AetherNode Host")

        # Replace label with a read-only Text widget to allow selection
        label_text = "(Default Localhost: http://127.0.0.1:8000)\nEnter the Non-Streaming URL from the Oobabooga Public Api Google Colab.  To use multiple hosts, separate them with a space.  The fastest Host should be first:"
        
        # Adjust the appearance of the Text widget
        label = tk.Text(top, height=3, wrap=tk.WORD, bg=dark_bg_color, fg=light_text_color, bd=0, padx=10, pady=10, relief=tk.FLAT, highlightthickness=0)
        label.insert(tk.END, label_text)
        label.configure(state=tk.DISABLED)  # Make it read-only
        label.pack(pady=10)

        self.host_entry = tk.Entry(top, bg=dark_bg_color, fg=light_text_color, width=50)
        self.host_entry.insert(tk.END, host_value)
        self.host_entry.pack(padx=10, pady=10)

        def copy_to_clipboard(widget):
            try:
                selected_text = widget.selection_get()
                top.clipboard_clear()
                top.clipboard_append(selected_text)
            except tk.TclError:
                pass  # Nothing is selected

        def paste_from_clipboard(widget):
            clipboard_text = top.clipboard_get()
            widget.insert(tk.INSERT, clipboard_text)

        # Create context menu
        context_menu = tk.Menu(top, tearoff=0)
        context_menu.add_command(label="Copy", command=lambda: copy_to_clipboard(focused_widget))
        context_menu.add_command(label="Paste", command=lambda: paste_from_clipboard(focused_widget))

        def show_context_menu(event):
            global focused_widget
            focused_widget = event.widget
            context_menu.post(event.x_root, event.y_root)

        # Bind right-click to show the context menu
        label.bind("<Button-3>", show_context_menu)
        self.host_entry.bind("<Button-3>", show_context_menu)

        def save_host():
            new_host = self.host_entry.get()
            settings["HOST_Oobabooga"] = new_host  # Replace 'HOST_Oobabooga' with the actual key if different
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(settings, file, indent=4)
            top.destroy()

        save_button = customtkinter.CTkButton(top, text="Save", command=save_host)
        save_button.pack(pady=10)

        top.mainloop()
        
        
    def Set_Embed(self):
        # File path to the JSON settings file
        json_file_path = "./Aetherius_API/chatbot_settings.json"

        # Load the JSON file
        with open(json_file_path, 'r', encoding='utf-8') as f:
            settings_dict = json.load(f)

        # Retrieve the embedding model setting from the JSON object
        embedding_model = settings_dict.get('Embeddings', 'Embeddings_Sentence_Xformer')
        dark_bg_color = "#2B2B2B"
        light_text_color = "#ffffff"

        # No need to open the txt file anymore, we have the value from JSON
        host_value = embedding_model  # The value is now loaded from the JSON file

        top = tk.Toplevel(self)
        top.configure(bg=dark_bg_color)
        top.title("Set Embedding Model")

        # Replace label with a read-only Text widget to allow selection
        label_text = "Options: Embeddings_Sentence_Xformer\nEnter what embedding provider you wish to use:"

        # Adjust the appearance of the Text widget
        label = tk.Text(top, height=3, wrap=tk.WORD, bg=dark_bg_color, fg=light_text_color, bd=0, padx=10, pady=10, relief=tk.FLAT, highlightthickness=0)
        label.insert(tk.END, label_text)
        label.configure(state=tk.DISABLED)  # Make it read-only
        label.pack(pady=10)

        self.host_entry = tk.Entry(top, bg=dark_bg_color, fg=light_text_color, width=50)
        self.host_entry.insert(tk.END, host_value)
        self.host_entry.pack(padx=10, pady=10)

        def copy_to_clipboard(widget):
            try:
                selected_text = widget.selection_get()
                top.clipboard_clear()
                top.clipboard_append(selected_text)
            except tk.TclError:
                pass  # Nothing is selected

        def paste_from_clipboard(widget):
            clipboard_text = top.clipboard_get()
            widget.insert(tk.INSERT, clipboard_text)

        # Create context menu
        context_menu = tk.Menu(top, tearoff=0)
        context_menu.add_command(label="Copy", command=lambda: copy_to_clipboard(focused_widget))
        context_menu.add_command(label="Paste", command=lambda: paste_from_clipboard(focused_widget))

        def show_context_menu(event):
            global focused_widget
            focused_widget = event.widget
            context_menu.post(event.x_root, event.y_root)

        # Bind right-click to show the context menu
        label.bind("<Button-3>", show_context_menu)
        self.host_entry.bind("<Button-3>", show_context_menu)

        def save_host():
            new_host = self.host_entry.get()
            with open(file_path, 'w') as file:
                file.write(new_host)
            top.destroy()

        save_button = customtkinter.CTkButton(top, text="Save", command=save_host)
        save_button.pack(pady=10)

        top.mainloop()
        
        
    def Set_TTS(self):
        json_file_path = "./Aetherius_API/chatbot_settings.json"  # Change this to the path of your JSON file
        dark_bg_color = "#2B2B2B"
        light_text_color = "#ffffff"

        with open(json_file_path, 'r', encoding='utf-8') as file:  # Ensure utf-8 encoding
            settings = json.load(file)
            host_value = settings.get('TTS', '')  # Read the TTS value from the JSON object

        top = tk.Toplevel(self)
        top.configure(bg=dark_bg_color)
        top.title("Set TTS Model")

        # Replace label with a read-only Text widget to allow selection
        label_text = "Options: gTTS(Google), elevenTTS(Elevenlabs), coquiaiTTS(Voice Cloning)\n(See cloning folder in API for setup info)\nEnter what TTS provider you wish to use:"
        
        # Adjust the appearance of the Text widget
        label = tk.Text(top, height=3, wrap=tk.WORD, bg=dark_bg_color, fg=light_text_color, bd=0, padx=10, pady=10, relief=tk.FLAT, highlightthickness=0)
        label.insert(tk.END, label_text)
        label.configure(state=tk.DISABLED)  # Make it read-only
        label.pack(pady=10)

        self.host_entry = tk.Entry(top, bg=dark_bg_color, fg=light_text_color, width=50)
        self.host_entry.insert(tk.END, host_value)
        self.host_entry.pack(padx=10, pady=10)

        def copy_to_clipboard(widget):
            try:
                selected_text = widget.selection_get()
                top.clipboard_clear()
                top.clipboard_append(selected_text)
            except tk.TclError:
                pass  # Nothing is selected

        def paste_from_clipboard(widget):
            clipboard_text = top.clipboard_get()
            widget.insert(tk.INSERT, clipboard_text)

        # Create context menu
        context_menu = tk.Menu(top, tearoff=0)
        context_menu.add_command(label="Copy", command=lambda: copy_to_clipboard(focused_widget))
        context_menu.add_command(label="Paste", command=lambda: paste_from_clipboard(focused_widget))

        def show_context_menu(event):
            global focused_widget
            focused_widget = event.widget
            context_menu.post(event.x_root, event.y_root)

        # Bind right-click to show the context menu
        label.bind("<Button-3>", show_context_menu)
        self.host_entry.bind("<Button-3>", show_context_menu)



        def save_host():
            new_host = self.host_entry.get()
            settings["TTS"] = new_host  # Replace 'HOST_Oobabooga' with the actual key if different
            with open(json_file_path, 'w', encoding='utf-8') as file:
                json.dump(settings, file, indent=4)
            top.destroy()


        save_button = customtkinter.CTkButton(top, text="Save", command=save_host)
        save_button.pack(pady=10)

        top.mainloop()
        

    def update_font_settings(self):
        # Load the JSON file
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings_dict = json.load(f)
            
        # Extract font and font size from JSON
        font_config = settings_dict.get('font', '')
        font_size = settings_dict.get('font_size', '')
        
        # Fallback to size 10 if no font size
        try:
            font_size_config = int(font_size)
        except:
            font_size_config = 10

        font_style = (f"{font_config}", font_size_config)

        self.conversation_text.configure(font=font_style)
        self.user_input.configure(font=(f"{font_config}", 10))
        
        
    def copy_selected_text(self):
        selected_text = self.conversation_text.get(tk.SEL_FIRST, tk.SEL_LAST)
        self.clipboard_clear()
        self.clipboard_append(selected_text)
    
    def bind_enter_key(self):
        self.user_input.bind("<Return>", lambda event: self.send_message())
        

    def bind_right_alt_key(self):
        self.user_input.bind("<Alt_R>", lambda event: self.check_and_record_audio())
        
    def check_and_record_audio(self):
        if not self.is_recording:
            self.initiate_record_audio()
        
        
    def insert_newline_with_space(self, event):
        # Check if the Shift key is pressed and the Enter key is pressed.
        if event.state == 1 and event.keysym == "Return":
            # Insert a newline followed by a space at the current cursor position.
            event.widget.insert(tk.INSERT, "\n ")
            return "break"  # Prevent the default behavior (sending the message). 
            
            
    def handle_memory_selection(self, choice):
        # This function will be triggered when a new mode is selected
        selection = choice  # Assuming 'choice' is the parameter that holds the selected value

        # Define the path to the JSON file
        json_file_path = './Aetherius_API/chatbot_settings.json'

        # Read the current settings from the JSON file
        with open(json_file_path, 'r') as file:
            settings = json.load(file)

        # Update the memory_mode in settings based on the selection
        if selection == "Auto":
            settings['memory_mode'] = "Auto"
            print("Auto Memory Upload mode selected!")
        elif selection == "Forced":
            settings['memory_mode'] = "Forced"
            print("Forced Memory Upload mode selected!")
        elif selection == "None":
            settings['memory_mode'] = "None"
            print("Memory Upload Disabled.")

        # Write the updated settings back to the JSON file
        with open(json_file_path, 'w') as file:
            json.dump(settings, file, indent=4)
            
            
    def is_agent_mode_checked(self):
        return self.agent_mode_var.get()
            
            
    def is_external_resources_checked(self):
        return self.external_resources_var.get()
        
    def is_tts_checked(self):
        return self.tts_var.get()
        
        
    def handle_tools_menu_selection(self, choice):
        selection = self.tools_menu.get()
        if selection == "Web Search":
            self.open_websearch_window()
        elif selection == "File Process":
            self.open_fileprocess_window()
            
            
    def handle_loop_menu_selection(self, choice):
        try:
            selection = self.loop_menu.get()
            if selection == "Inner_Monologue":
                # Logic for Inner_Monologue
                pass
            elif selection == "Intuition":
                # Logic for Intuition
                pass
            elif selection == "Response":
                # Logic for Response
                pass
        except Exception as e:
            print(f"Error in handle_loop_menu_selection: {e}")
            
            
    def create_widgets(self):
        # Load settings from JSON file
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)

        # Get font and font size from the JSON settings
        font_config = settings.get('font', 'default_font')
        font_size = settings.get('font_size', 'default_size')

        self.memory_mode = "Training"
        try:
            font_size_config = int(font_size)
        except:
            font_size_config = 10
        font_style = (f"{font_config}", font_size_config)
        customtkinter.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
        
        self.settings_frame = customtkinter.CTkFrame(self)
        self.settings_frame.grid(row=0, column=0, rowspan=2, sticky=tk.W+tk.N)
        
        
        self.top_frame = customtkinter.CTkFrame(self)  # Use customtkinter.CTkFrame
        self.top_frame.grid(row=0, column=1, columnspan=2, sticky=tk.W+tk.E)
        dark_bg_color = "#2B2B2B"
        light_text_color = "#ffffff"
        self.top_frame.grid_columnconfigure(0, weight=1)
        self.top_frame.grid_columnconfigure(1, weight=1)
        self.top_frame.grid_columnconfigure(2, weight=1)
        self.top_frame.grid_columnconfigure(3, weight=1)
        self.top_frame.grid_columnconfigure(4, weight=1)


        def handle_login_menu_selection(choice):
            try:
                selection = self.login_menu.get()
                if selection == "Choose Bot Name":
                    self.choose_bot_name()
                elif selection == "Choose Username":
                    self.choose_username()
                elif selection == "Choose User ID":
                    self.choose_user_id()
            except Exception as e:
                print(f"Error in handle_login_menu_selection: {e}")
                
        # Login dropdown Menu
        self.login_menu = customtkinter.CTkComboBox(self.settings_frame, width=115, values=["Choose Bot Name", "Choose Username", "Choose User ID", "Edit Main Prompt", "Edit Secondary Prompt", "Edit Greeting Prompt"], state="readonly", command=self.handle_login_menu_selection)
        self.login_menu.grid(row=0, column=0, padx=5, pady=9, sticky=tk.W+tk.E)
        self.login_menu.set("Bot Config")
        self.login_menu.bind("<<ComboboxSelected>>", self.handle_login_menu_selection)
        
        def open_file_menu(file_path):
            # Return "N/A" if the current selection is "Loop Selection"
            current_selection = self.loop_menu.get()
            if current_selection == "Loop Selection":
                return "N/A"
            try:
                with open(file_path, 'r') as file:
                    return file.read().strip()
            except:
                print(f"Error reading from {file_path}")
                return "Unknown"
        
 
        
        def handle_loop_menu_selection(event=None):
            current_selection = self.loop_menu.get()

            # Check if current selection is "Loop Selection"
            if current_selection == "Loop Selection":
                self.temperature_value.set("Temperature: N/A")
                self.scale_widget.set(1.0)  # Setting the slider to a neutral position, adjust if necessary
                
                self.rep_pen_value.set("Repetition Penalty: N/A")
                self.rep_pen_scale_widget.set(1.0)  # Setting the slider to a neutral position, adjust if necessary

                self.max_tokens_value.set("Max Tokens: N/A")
                self.max_tokens_scale_widget.set(1000)  # Setting the slider to a neutral position, adjust if necessary
                self.top_p_value.set("Top P: N/A")
                self.top_p_scale_widget.set(0.5)  # Neutral position for top_p slider (mid-point between 0.00 and 1.00)
                self.top_k_value.set("Top K: N/A")
                self.top_k_scale_widget.set(50)  # Mid value for top_k
                self.min_tokens_value.set("Min Tokens: N/A")
                self.min_tokens_scale_widget.set(40)  # Setting the slider to a neutral position, adjust if necessary
                return
                
                

            # Otherwise, update based on file values:
            
            # LATER Change all Generation settings to use Json Files.
            
            # For Temperature:
            temp_file_path = "./Aetherius_API/Generation_Settings/Oobabooga/settings.json"
            try:
                with open(temp_file_path, 'r') as file:
                    data = json.load(file)
                    current_value = float(data.get(f'{current_selection}_temperature', 0.7))  # Replace 'temperature' with the actual key
                    self.scale_widget.set(current_value)
                    self.temperature_value.set(f"Temperature: {current_value:.2f}")

                    font_size_config = 12  # Replace with your actual font size
                    self.temperature_label = customtkinter.CTkLabel(self.settings_frame, text=f"Temperature: {current_value:.2f}", font=('bold', font_size_config))
                    self.temperature_label.grid(row=3, column=0, padx=5, pady=1, sticky=tk.W+tk.E)
            except Exception as e:
                print(f"Error reading {temp_file_path}: {e}")

                
            # For Top P:
            top_p_file_path = "./Aetherius_API/Generation_Settings/Oobabooga/settings.json"
            try:
                with open(top_p_file_path, 'r') as file:
                    data = json.load(file)
                    current_value = float(data.get(f'{current_selection}_top_p', 0))  # Replace 'top_p' with the actual key
                    self.top_p_scale_widget.set(current_value)
                    self.top_p_value.set(f"Top P: {current_value:.2f}")

                    font_size_config = 12  # Replace with your actual font size
                    self.top_p_label = customtkinter.CTkLabel(self.settings_frame, text=f"Top P: {current_value:.2f}", font=('bold', font_size_config))
                    self.top_p_label.grid(row=5, column=0, padx=5, pady=1, sticky=tk.W+tk.E)
            except Exception as e:
                print(f"Error reading {top_p_file_path}: {e}")
                
                
            # For Top K:
            top_k_file_path = "./Aetherius_API/Generation_Settings/Oobabooga/settings.json"
            try:
                with open(top_k_file_path, 'r') as file:
                    data = json.load(file)
                    current_value = int(data.get(f'{current_selection}_top_k', 0))  # Replace 'top_k' with the actual key
                    self.top_k_scale_widget.set(current_value)
                    self.top_k_value.set(f"Top K: {current_value}")

                    font_size_config = 12  # Replace with your actual font size
                    self.top_k_label = customtkinter.CTkLabel(self.settings_frame, text=f"Top K: {current_value}", font=('bold', font_size_config))
                    self.top_k_label.grid(row=7, column=0, padx=5, pady=1, sticky=tk.W+tk.E)
            except Exception as e:
                print(f"Error reading {top_k_file_path}: {e}")
                
                
            # For Repetition Penalty:
            rep_pen_file_path = "./Aetherius_API/Generation_Settings/Oobabooga/settings.json"
            try:
                with open(rep_pen_file_path, 'r') as file:
                    data = json.load(file)
                    current_value = float(data.get(f'{current_selection}_rep_pen', 0))  # Replace 'rep_pen' with the actual key
                    self.rep_pen_scale_widget.set(current_value)
                    self.rep_pen_value.set(f"Repetition Penalty: {current_value:.2f}")

                    font_size_config = 12  # Replace with your actual font size
                    self.rep_pen_label = customtkinter.CTkLabel(self.settings_frame, text=f"Repetition Penalty: {current_value:.2f}", font=('bold', font_size_config))
                    self.rep_pen_label.grid(row=9, column=0, padx=5, pady=1, sticky=tk.W+tk.E)
            except Exception as e:
                print(f"Error reading {rep_pen_file_path}: {e}")
                
                
            # For Min Tokens:
            min_token_file_path = "./Aetherius_API/Generation_Settings/Oobabooga/settings.json"
            try:
                with open(min_token_file_path, 'r') as file:
                    data = json.load(file)
                    current_value = int(data.get(f'{current_selection}_min_tokens', 0))  # Replace 'min_tokens' with the actual key
                    self.min_tokens_scale_widget.set(current_value)
                    self.min_tokens_value.set(f"Min Tokens: {current_value}")

                    font_size_config = 12  # Replace with your actual font size
                    # Update this line if you need to show something else
                    self.min_tokens_label = customtkinter.CTkLabel(self.settings_frame, text=f"Min Tokens: {current_value}", font=('bold', font_size_config))
                    self.min_tokens_label.grid(row=11, column=0, padx=5, pady=1, sticky=tk.W+tk.E)
            except Exception as e:
                print(f"Error reading {min_token_file_path}: {e}")
                
                
            # For Max Tokens:
            token_file_path = "./Aetherius_API/Generation_Settings/Oobabooga/settings.json"
            try:
                with open(token_file_path, 'r') as file:
                    data = json.load(file)
                    current_value = int(data.get(f'{current_selection}_max_tokens', 0))  # Replace 'max_tokens' with the actual key
                    self.max_tokens_scale_widget.set(current_value)
                    self.max_tokens_value.set(f"Max Tokens: {current_value}")

                    font_size_config = 12  # Replace with your actual font size
                    self.tokens_label = customtkinter.CTkLabel(self.settings_frame, text=f"Max Tokens: {current_value}", font=('bold', font_size_config))
                    self.tokens_label.grid(row=13, column=0, padx=5, pady=1, sticky=tk.W+tk.E)
            except Exception as e:
                print(f"Error reading {token_file_path}: {e}")
                
                
        self.parm_title_label = customtkinter.CTkLabel(self.settings_frame, text=f"Parameter Settings:", font=('bold', font_size_config))
        self.parm_title_label.grid(row=1, column=0, padx=5, sticky=tk.W+tk.E)
 

        
        self.loop_menu = customtkinter.CTkComboBox(self.settings_frame, width=115, values=["Loop Selection", "Inner_Monologue", "Intuition", "Response"], state="readonly", command=handle_loop_menu_selection)
        self.loop_menu.grid(row=2, column=0, padx=5, pady=9, sticky=tk.W+tk.E)
        self.loop_menu.set("Loop Selection")
        self.loop_menu.bind("<<ComboboxSelected>>", handle_loop_menu_selection)
        
        
# LATER REPLACEC WITH JSON
        def update_value(value):
            current_selection = self.loop_menu.get()
            file_path = "./Aetherius_API/Generation_Settings/Oobabooga/settings.json"
            formatted_value = f"{float(value):.2f}"  # Format the value to two decimal places
            try:
                with open(file_path, 'r') as file:
                    data = json.load(file)
                data[f"{current_selection}_temperature"] = formatted_value
                with open(file_path, 'w') as file:
                    json.dump(data, file, indent=4)
                temperature_value = data.get(f"{current_selection}_temperature", "Unknown")

                self.temperature_value.set(f"Temperature: {temperature_value}")  # update the label with value from JSON
            except Exception as e:
                print(f"Error writing to or reading from {file_path}: {e}")
            self.temperature_label = customtkinter.CTkLabel(
                self.settings_frame, 
                text=f"Temperature: {temperature_value}", 
                font=('bold', font_size_config)
            )
            self.temperature_label.grid(row=3, column=0, padx=5, pady=1, sticky=tk.W+tk.E)

        # Adjusted the range and resolution of the slider for the new values
        self.scale_widget = customtkinter.CTkSlider(self.settings_frame, from_=0.00, to=2.0, number_of_steps=40, command=update_value, width=140)
        self.scale_widget.grid(row=4, column=0, padx=5, pady=3, sticky=tk.W+tk.E)
        

        
        
        def update_top_p(value):
            current_selection = self.loop_menu.get()
            file_path = "./Aetherius_API/Generation_Settings/Oobabooga/settings.json"
            formatted_value = f"{float(value):.2f}"

            try:
                # Read existing JSON data
                with open(file_path, 'r') as file:
                    data = json.load(file)

                # Update the specific key
                data[f"{current_selection}_top_p"] = formatted_value

                # Write the updated data back to the file
                with open(file_path, 'w') as file:
                    json.dump(data, file, indent=4)

                # Load the top_p value from the JSON file
                top_p_value = data.get(f"{current_selection}_top_p", "Unknown")

                self.top_p_value.set(f"Top P: {top_p_value}")  # update the label with value from JSON
            except Exception as e:
                print(f"Error writing to or reading from {file_path}: {e}")
            self.top_p_label = customtkinter.CTkLabel(
                self.settings_frame, 
                text=f"Top P: {top_p_value}", 
                font=('bold', font_size_config)
            )
            self.top_p_label.grid(row=5, column=0, padx=5, pady=1, sticky=tk.W+tk.E)
                

        self.top_p_scale_widget = customtkinter.CTkSlider(self.settings_frame, from_=0.00, to=1.00, number_of_steps=100, command=update_top_p, width=140)
        self.top_p_scale_widget.grid(row=6, column=0, padx=5, pady=3, sticky=tk.W+tk.E)
        
        
        # Function to update top_k value when the slider is moved
        def update_top_k(value):
            current_selection = self.loop_menu.get()
            file_path = "./Aetherius_API/Generation_Settings/Oobabooga/settings.json"
            formatted_value = f"{int(value)}"
            try:
                # Read existing JSON data
                with open(file_path, 'r') as file:
                    data = json.load(file)

                # Update the specific key
                data[f"{current_selection}_top_k"] = formatted_value

                # Write the updated data back to the file
                with open(file_path, 'w') as file:
                    json.dump(data, file, indent=4)

                # Load the top_p value from the JSON file
                top_k_value = data.get(f"{current_selection}_top_k", "Unknown")

                self.top_k_value.set(f"Top K: {top_k_value}")  # update the label with value from JSON
            except Exception as e:
                print(f"Error writing to or reading from {file_path}: {e}")
            self.top_k_label = customtkinter.CTkLabel(
                self.settings_frame, 
                text=f"Top K: {top_k_value}", 
                font=('bold', font_size_config)
            )
            self.top_k_label.grid(row=7, column=0, padx=5, pady=1, sticky=tk.W+tk.E)
            
            
        self.top_k_scale_widget = customtkinter.CTkSlider(self.settings_frame, from_=0, to=100, number_of_steps=100, command=update_top_k, width=140)  # 101 steps for the range 0 to 100 inclusive
        self.top_k_scale_widget.grid(row=8, column=0, padx=5, pady=3, sticky=tk.W+tk.E)
        
        def update_rep_pen(value):
        
            current_selection = self.loop_menu.get()
            file_path = "./Aetherius_API/Generation_Settings/Oobabooga/settings.json"
            formatted_value = f"{float(value):.2f}"
            try:
                # Read existing JSON data
                with open(file_path, 'r') as file:
                    data = json.load(file)

                # Update the specific key
                data[f"{current_selection}_rep_pen"] = formatted_value

                # Write the updated data back to the file
                with open(file_path, 'w') as file:
                    json.dump(data, file, indent=4)

                # Load the top_p value from the JSON file
                rep_pen_value = data.get(f"{current_selection}_rep_pen", "Unknown")

                self.rep_pen_value.set(f"Repetition Penalty: {rep_pen_value}")  # update the label with value from JSON
            except Exception as e:
                print(f"Error writing to or reading from {file_path}: {e}")
            self.rep_pen_label = customtkinter.CTkLabel(
                self.settings_frame, 
                text=f"Repetition Penalty: {rep_pen_value}", 
                font=('bold', font_size_config)
            )
            self.rep_pen_label.grid(row=9, column=0, padx=5, pady=1, sticky=tk.W+tk.E)
        

        # You might want to adjust the range and steps based on the desired range for repetition penalty.
        self.rep_pen_scale_widget = customtkinter.CTkSlider(self.settings_frame, from_=0.0, to=2.0, number_of_steps=40, command=update_rep_pen, width=140)
        self.rep_pen_scale_widget.grid(row=10, column=0, padx=5, pady=3, sticky=tk.W+tk.E)
        
        
        def update_min_tokens(value):
            current_selection = self.loop_menu.get()
            file_path = "./Aetherius_API/Generation_Settings/Oobabooga/settings.json"
            formatted_value = f"{int(value)}"
            try:
                # Read existing JSON data
                with open(file_path, 'r') as file:
                    data = json.load(file)

                # Update the specific key
                data[f"{current_selection}_min_tokens"] = formatted_value

                # Write the updated data back to the file
                with open(file_path, 'w') as file:
                    json.dump(data, file, indent=4)

                # Load the top_p value from the JSON file
                min_tokens_value = data.get(f"{current_selection}_min_tokens", "Unknown")

                self.min_tokens_value.set(f"Minimum Tokens: {min_tokens_value}")  # update the label with value from JSON
            except Exception as e:
                print(f"Error writing to or reading from {file_path}: {e}")
            self.min_tokens_label = customtkinter.CTkLabel(
                self.settings_frame, 
                text=f"Minimum Tokens: {min_tokens_value}", 
                font=('bold', font_size_config)
            )
            self.min_tokens_label.grid(row=11, column=0, padx=5, pady=1, sticky=tk.W+tk.E)


        # Assuming you want a range of 0 to 1000 tokens. Adjust the range and steps accordingly.
        self.min_tokens_scale_widget = customtkinter.CTkSlider(self.settings_frame, from_=0, to=1000, number_of_steps=100, command=update_min_tokens, width=140)
        self.min_tokens_scale_widget.grid(row=12, column=0, padx=5, pady=3, sticky=tk.W+tk.E)
        
        
        def update_tokens(value):
            current_selection = self.loop_menu.get()
            file_path = "./Aetherius_API/Generation_Settings/Oobabooga/settings.json"
            formatted_value = f"{int(value)}"
            try:
                # Read existing JSON data
                with open(file_path, 'r') as file:
                    data = json.load(file)

                # Update the specific key
                data[f"{current_selection}_max_tokens"] = formatted_value

                # Write the updated data back to the file
                with open(file_path, 'w') as file:
                    json.dump(data, file, indent=4)

                # Load the top_p value from the JSON file
                max_tokens_value = data.get(f"{current_selection}_max_tokens", "Unknown")

                self.max_tokens_value.set(f"Maximum Tokens: {max_tokens_value}")  # update the label with value from JSON
            except Exception as e:
                print(f"Error writing to or reading from {file_path}: {e}")
            self.max_tokens_label = customtkinter.CTkLabel(
                self.settings_frame, 
                text=f"Maximum Tokens: {max_tokens_value}", 
                font=('bold', font_size_config)
            )
            self.max_tokens_label.grid(row=13, column=0, padx=5, pady=1, sticky=tk.W+tk.E)


        # Assuming you want a range of 0 to 1000 tokens. Adjust the range and steps accordingly.
        self.max_tokens_scale_widget = customtkinter.CTkSlider(self.settings_frame, from_=10, to=2000, number_of_steps=100, command=update_tokens, width=140)
        self.max_tokens_scale_widget.grid(row=14, column=0, padx=5, pady=3, sticky=tk.W+tk.E)
        
        
        


        def handle_db_menu_selection(choice):
            print("Combobox selected!")
            selection = self.db_menu.get()
            if selection == "Cadence DB":
                self.open_cadence_window()
            elif selection == "Heuristics DB":
                self.open_heuristics_window()
            elif selection == "Long Term Memory DB":
                self.open_long_term_window()
            elif selection == "DB Deletion":
                self.open_deletion_window()  
        
        # DB Management Dropdown menu
        self.db_menu = customtkinter.CTkComboBox(self.top_frame, values=["Cadence DB", "Heuristics DB", "Long Term Memory DB", "DB Deletion"], state="readonly", command=handle_db_menu_selection)
        self.db_menu.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        self.db_menu.set("DB Management")
        self.db_menu.bind("<<ComboboxSelected>>", self.handle_db_menu_selection)
        
        # Edit Conversation Button
        self.update_history_button = customtkinter.CTkButton(self.top_frame, text="Edit\nConversation", command=self.Edit_Conversation)  # Use customtkinter.CTkButton
        self.update_history_button.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W+tk.E)

        
        # Delete Conversation Button
        self.delete_history_button = customtkinter.CTkButton(self.top_frame, text="Clear\nConversation", command=self.delete_conversation_history)
        self.delete_history_button.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W+tk.E)
        
        def handle_menu_selection(choice):
            selection = self.menu.get()
            if selection == "Edit Font":
                self.Edit_Font()
            elif selection == "Edit Font Size":
                self.Edit_Font_Size()
            elif selection == "Set Conv Length":
                self.Set_Conv_Length()
            elif selection == "Set AetherNode HOST":
                self.Set_Host()
            elif selection == "Set Embedding Model":
                self.Set_Embed()
            elif selection == "Set TTS Model":
                self.Set_TTS()
        
        # Config Dropdown Menu
        self.menu = customtkinter.CTkComboBox(self.top_frame, values=["Set AetherNode HOST", "Set Embedding Model", "Set TTS Model", "Edit Font", "Edit Font Size", "Set Conv Length"], state="readonly", command=handle_menu_selection)
        self.menu.grid(row=0, column=4, padx=5, pady=5, sticky=tk.W+tk.E)
        self.menu.set("Config Menu")
        self.menu.bind("<<ComboboxSelected>>", self.handle_menu_selection)
        
        
        
        self.conversation_text = tk.Text(self, bg=dark_bg_color, fg=light_text_color, insertbackground=light_text_color, wrap=tk.WORD)
        self.conversation_text.grid(row=1, column=1, rowspan=2, sticky=tk.W+tk.E+tk.N+tk.S)  # Making it expandable in all directions
        self.conversation_text.configure(font=font_style)
        self.conversation_text.bind("<Key>", lambda e: "break")  # Disable keyboard input
        self.conversation_text.bind("<Button>", lambda e: "break")  # Disable mouse input
        
        self.conversation_scrollbar = tk.Scrollbar(self, command=self.conversation_text.yview)
        self.conversation_scrollbar.grid(row=1, column=2, rowspan=2, sticky=tk.N+tk.S)
        self.conversation_text.configure(yscrollcommand=self.conversation_scrollbar.set)

        self.input_frame = tk.Frame(self, bg=dark_bg_color)
        self.input_frame.grid(row=3, column=1, columnspan=2, sticky=tk.W+tk.E)

        # Set the initial height for the user input Text widget.
        initial_input_height = 5  # Adjust this value as needed.

        self.user_input = tk.Text(self.input_frame, bg=dark_bg_color, fg=light_text_color, insertbackground=light_text_color, height=initial_input_height, wrap=tk.WORD, yscrollcommand=True)  # Use customtkinter.CTkText
        self.user_input.configure(font=(f"{font_config}", 12))
        self.user_input.grid(row=1, rowspan=2, column=0, sticky=tk.W+tk.E+tk.N+tk.S)

        # Bind the new function to handle Shift + Enter event.
        self.user_input.bind("<Shift-Return>", self.insert_newline_with_space)

        # Create a scrollbar for the user input Text widget.
        scrollbar = tk.Scrollbar(self.input_frame, command=self.user_input.yview)
        scrollbar.grid(row=1, rowspan=2, column=1, sticky=tk.N+tk.S)
        

        # Attach the scrollbar to the user input Text widget.
        self.user_input.configure(yscrollcommand=scrollbar.set)

        self.thinking_label = customtkinter.CTkLabel(self.input_frame, text="Thinking...")
        
        def handle_memory_selection(choice):
            # This function will be triggered when a new mode is selected
            selection = choice  # Assuming 'choice' is the parameter that holds the selected value

            # Define the path to the JSON file
            json_file_path = './Aetherius_API/chatbot_settings.json'

            # Read the current settings from the JSON file
            with open(json_file_path, 'r') as file:
                settings = json.load(file)

            # Update the memory_mode in settings based on the selection
            if selection == "Auto":
                settings['memory_mode'] = "Auto"
                print("Auto Memory Upload mode selected!")
            elif selection == "Forced":
                settings['memory_mode'] = "Forced"
                print("Forced Memory Upload mode selected!")
            elif selection == "None":
                settings['memory_mode'] = "None"
                print("Memory Upload Disabled.")

            # Write the updated settings back to the JSON file
            with open(json_file_path, 'w') as file:
                json.dump(settings, file, indent=4)

        self.tts_var = tk.BooleanVar(value=False)
        

        self.voice_button = customtkinter.CTkButton(self.input_frame, text="Voice", command=self.initiate_record_audio, width=50)  
        self.voice_button.grid(row=2, column=3, padx=5)

        self.send_button = customtkinter.CTkButton(self.input_frame, text="Send", command=self.send_message, width=120)  
        self.send_button.grid(row=2, column=2, padx=5, pady=3)
        
        self.mode_menu = customtkinter.CTkComboBox(self.input_frame, values=["Auto", "Forced", "None"], state="readonly", command=self.handle_memory_selection, width=120)
        self.mode_menu.grid(row=1, column=2, padx=5, pady=10, sticky=tk.W+tk.E)
        self.mode_menu.set("Memory Mode")
        self.mode_menu.bind("<<ComboboxSelected>>", handle_memory_selection)
        
    #    self.tts_check = customtkinter.CTkCheckBox(self.input_frame, variable=self.tts_var, text="TTS", width=12)
    #    self.tts_check.grid(row=1, column=3, padx=5)
    
        self.voice_button = customtkinter.CTkButton(self.input_frame, text="Image", command=self.initiate_image_model, width=50)  
        self.voice_button.grid(row=1, column=3, padx=5)
    
    #    self.tts_check = customtkinter.CTkCheckBox(self.input_frame, variable=self.tts_var, text="TTS", width=12)
    #    self.tts_check.grid(row=1, column=3, padx=5)
        
        
    #    def toggle_db_checkboxes():
    #        if self.agent_mode_var.get() == 1:  # if External Resources is checked
    #            self.external_resources_check.configure(state=tk.NORMAL)
    #        else:
    #            self.external_resources_check.configure(state=tk.DISABLED)
                # Uncheck the other checkboxes
    #            self.external_resources_var.set(0)

        self.tools_frame = customtkinter.CTkFrame(self)
        self.tools_frame.grid(row=2, column=0, sticky=tk.W+tk.N)
        
        self.tools_menu = customtkinter.CTkComboBox(self.tools_frame, values=["Web Search", "File Process"], state="readonly", command=self.handle_tools_menu_selection)
    #    self.tools_menu = customtkinter.CTkComboBox(self.tools_frame, values=["None"], state="readonly")
        self.tools_menu.grid(row=0, column=0, padx=5, sticky=tk.W+tk.E)
        self.tools_menu.set("Tools")
        self.tools_menu.bind("<<ComboboxSelected>>", self.handle_tools_menu_selection)
        
        self.checkmarks_frame = customtkinter.CTkFrame(self)
        self.checkmarks_frame.grid(row=3, column=0, sticky=tk.W+tk.N)
        
        self.agent_mode_var = tk.BooleanVar(value=False)
    #    self.external_resources_var = tk.BooleanVar(value=False)


    #    self.agent_mode_check = customtkinter.CTkCheckBox(self.checkmarks_frame, text="Agent Mode", variable=self.agent_mode_var, command=toggle_db_checkboxes)
        self.agent_mode_check = customtkinter.CTkCheckBox(self.checkmarks_frame, text="Agent Mode", variable=self.agent_mode_var)
        self.agent_mode_check.grid(row=0, column=0, sticky=tk.W, padx=25)
        
        self.tts_check = customtkinter.CTkCheckBox(self.checkmarks_frame, variable=self.tts_var, text="TTS", width=12)
        self.tts_check.grid(row=1, column=0, sticky=tk.W, padx=25)

    #    self.external_resources_check = customtkinter.CTkCheckBox(self.checkmarks_frame, text="External Resources", variable=self.external_resources_var, state=tk.DISABLED)
    #    self.external_resources_check.grid(row=1, column=0, sticky=tk.W, padx=25)


        

        # Make user_input expandable and send_button fixed
    #    self.input_frame.grid_rowconfigure(0, weight=0)  # Mode selection menu (doesn't expand vertically)
        self.input_frame.grid_rowconfigure(1, weight=1) 

        
        self.input_frame.grid_columnconfigure(0, weight=1)
        self.input_frame.grid_columnconfigure(1, weight=0) 
        self.input_frame.grid_columnconfigure(2, weight=0) 

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=5)
        self.grid_rowconfigure(2, weight=0)

        self.bind_right_alt_key()
        self.bind_enter_key()
        self.conversation_text.bind("<1>", lambda event: self.conversation_text.focus_set())
        self.conversation_text.bind("<Button-3>", self.show_context_menu)
        
    def are_both_web_and_file_db_checked(self):
        return self.is_web_db_checked() and self.is_file_db_checked()
        
        
    
            
    def update_inner_monologue(self, output_one):
        self.conversation_text.insert(tk.END, f"Inner Monologue: {output_one}\n\n")
        self.conversation_text.yview(tk.END)
        
        

            
            
def Aetherius_GUI():
    try:
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        bot_name = settings.get('Current_Ui_Bot_Name', '')
        username = settings.get('Current_Ui_Username', '')
        user_id = settings.get('Current_Ui_User_ID', '')
        base_path = "./Aetherius_ApI/Chatbot_Prompts"
        base_prompts_path = os.path.join(base_path, "Base")
        user_bot_path = os.path.join(base_path, username, bot_name)
        json_file_path = './config/chatbot_settings.json'
        
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        bot_name = settings.get('Current_Ui_Bot_Name', '')
        username = settings.get('Current_Ui_Username', '')
        user_id = settings.get('Current_Ui_User_ID', '')
        
        base_path = "./Aetherius_API/Chatbot_Prompts"
        base_prompts_path = os.path.join(base_path, "Base")
        user_bot_path = os.path.join(base_path, user_id, bot_name)

        # Custom functions (import_functions_from_script, get_script_path_from_file, set_dark_ancient_theme, ChatBotApplication)
        # should be defined or imported here.

        HOST = settings.get('HOST_AetherNode', 'default_value_if_not_found')
        URI = f'{HOST}/generate-text/'
        set_dark_ancient_theme()
        root = tk.Tk()
        root.resizable(True, True)
        app = ChatBotApplication(root)
        app.master.geometry('980x700')  # Set the initial window size
        root.mainloop()
    
    except Exception as e:
        print("An error occurred in Aetherius_GUI:")
        traceback.print_exc()
    
    
    
    
    
    
    
    
