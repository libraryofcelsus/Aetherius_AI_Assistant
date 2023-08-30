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
from Llama2_chat import *
import multiprocessing
import threading
import concurrent.futures
import customtkinter
import tkinter as tk
from tkinter import ttk, scrolledtext, simpledialog, font, messagebox
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


embed_size = open_file('./config/embed_size.txt')

def check_local_server_running():
    try:
        response = requests.get("http://localhost:6333/dashboard/")
        return response.status_code == 200
    except requests.ConnectionError:
        return False

        
def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
       return file.read().strip()

# Check if local server is running
if check_local_server_running():
    client = QdrantClient(url="http://localhost:6333")
    print("Connected to local Qdrant server.")
else:
    try:
        url = open_file('./api_keys/qdrant_url.txt')
        api_key = open_file('./api_keys/qdrant_api_key.txt')
        client = QdrantClient(url=url, api_key=api_key)
        client.recreate_collection(
            collection_name="Ping",
            vectors_config=VectorParams(size=1, distance=Distance.COSINE),
        )
        print("Connected to cloud Qdrant server.")
    except:
        if not os.path.exists("./Qdrant_DB"):
            os.makedirs("./Qdrant_DB")
        client = QdrantClient(path="./Qdrant_DB")
        print("Neither a local nor a cloud Qdrant server could be connected. Using disk storage.")
    
    
# For local streaming, the websockets are hosted without ssl - http://
# HOST = 'http://localhost:5000'
# HOST = https://holders-gift-stays-pictures.trycloudflare.com
# URI = f'{HOST}/api/v1/chat'

# For reverse-proxied streaming, the remote will likely host with ssl - https://
# URI = 'https://your-uri-here.trycloudflare.com/api/v1/generate'




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

def get_script_path_from_file(file_path, base_folder='./scripts/resources/'):
    """
    Get the script path from a text file.

    Parameters:
    - file_path: The path to the text file containing the script name.
    - base_folder: The base folder where the script is located.
    """
    with open(file_path, 'r') as file:
        script_name = file.read().strip()
    return f'{base_folder}{script_name}.py'

# Import for model
file_path1 = './config/model.txt'
script_path1 = get_script_path_from_file(file_path1)
import_functions_from_script(script_path1, "model_module")

# Import for embedding model
file_path2 = './config/Settings/embedding_model.txt'
script_path2 = get_script_path_from_file(file_path2)
import_functions_from_script(script_path2, "embedding_module")

# Import for TTS
file_path3 = './config/Settings/TTS.txt'
script_path3 = get_script_path_from_file(file_path3, base_folder='./scripts/resources/TTS/')
import_functions_from_script(script_path3, "TTS_module")


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
    
    
    

    
    
def google_search(query, my_api_key, my_cse_id, **kwargs):
  params = {
    "key": my_api_key,
    "cx": my_cse_id,
    "q": query,
    "num": 7,
    "snippet": True
  }
  response = requests.get("https://www.googleapis.com/customsearch/v1", params=params)
  if response.status_code == 200:
    data = response.json()
    urls = [item['link'] for item in data.get("items", [])]  # Return a list of URLs
    return urls
  else:
    raise Exception(f"Request failed with status code {response.status_code}")
       
        
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



def chunk_text_from_url(url, chunk_size=400, overlap=40, results_callback=None):
    bot_name = open_file('./config/prompt_bot_name.txt')
    try:
        print("Scraping given URL, please wait...")
        bot_name = open_file('./config/prompt_bot_name.txt')
        username = open_file('./config/prompt_username.txt')
        html = requests.get(url).text
        soup = BeautifulSoup(html, 'html.parser')
        texttemp = soup.get_text().strip()
        texttemp = texttemp.replace('\n', '').replace('\r', '')
        texttemp = '\n'.join(line for line in texttemp.splitlines() if line.strip())
        chunks = chunk_text(texttemp, chunk_size, overlap)
        weblist = list()
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
        
        for chunk in chunks:
            websum = list()
            websum.append({'role': 'system', 'content': "MAIN SYSTEM PROMPT: You are an ai text summarizer.  Your job is to take the given text from a scraped article, then return the text in a summarized article form.  Do not generalize, rephrase, or add information in your summary, keep the same semantic meaning.  If no article is given, print no article.\n\n\n"})
            websum.append({'role': 'user', 'content': f"SCRAPED ARTICLE: {chunk}\n\nINSTRUCTIONS: Summarize the article without losing any factual knowledge and maintaining full context and information. Only print the truncated article, do not include any additional text or comments. [/INST] SUMMARIZER BOT: Sure! Here is the summarized article based on the scraped text:"})
            prompt = ''.join([message_dict['content'] for message_dict in websum])
            text = scrape_oobabooga_scrape(prompt)
            if len(text) < 20:
                text = "No Webscrape available"
        #    text = chatgpt35_completion(websum)
        #    paragraphs = text.split('\n\n')  # Split into paragraphs
        #    for paragraph in paragraphs:  # Process each paragraph individually, add a check to see if paragraph contained actual information.
            webcheck = list()
            webcheck.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: You are a sub-agent for an automated webscraping tool. Your task is to decide if the previous Ai sub-agent scraped legible information. The scraped text should contain some form of article, if it does, print 'YES'.  If the webscrape failed or is illegible, print: 'NO'."})
            webcheck.append({'role': 'user', 'content': f"ORIGINAL TEXT FROM SCRAPE: {chunk}[/INST]"})
            webcheck.append({'role': 'user', 'content': f"PROCESSED WEBSCRAPE: {text}\n\n"})
            webcheck.append({'role': 'user', 'content': f"[INST]SYSTEM: You are responding for a Yes or No input field. You are only capible of printing Yes or No. Use the format: [AI AGENT: <'Yes'/'No'>][/INST]\n\nASSISTANT:"})
       
            
            prompt = ''.join([message_dict['content'] for message_dict in webcheck])
            webyescheck = agent_oobabooga_webcheckyesno(prompt)
            
            if 'no webscrape' in text.lower():
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
                if 'yes' in webyescheck.lower():
                    semanticterm = list()
                    semanticterm.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: You are a bot responsible for taging articles with a title for database queries.  Your job is to read the given text, then create a title in question form representative of what the article is about, focusing on its main subject.  The title should be semantically identical to the overview of the article and not include extraneous info.  The article is from the URL: {url}. Use the format: [<TITLE IN QUESTION FORM>].\n\n"})
                    semanticterm.append({'role': 'user', 'content': f"ARTICLE: {text}\n\n"})
                    semanticterm.append({'role': 'user', 'content': f"SYSTEM: Create a short, single question that encapsulates the semantic meaning of the Article.  Use the format: [<QUESTION TITLE>].  Please only print the title, it will be directly input in front of the article.[/INST]\n\nASSISTANT: Sure! Here's the summary of the webscrape:"})
                    prompt = ''.join([message_dict['content'] for message_dict in semanticterm])
                    semantic_db_term = scrape_oobabooga_scrape(prompt)
                    print('---------')
                    weblist.append(url + ' ' + text)
                    print(url + '\n' + semantic_db_term + '\n' + text)
                    if results_callback is not None:
                        results_callback(url + ' ' + text)
                    payload = list()
                    timestamp = time()
                    timestring = timestamp_to_datetime(timestamp)
                    # Create the collection only if it doesn't exist

                    vector1 = embeddings(semantic_db_term + ' ' + text)
                #    embedding = model.encode(query)
                    unique_id = str(uuid4())
                    point_id = unique_id + str(int(timestamp))
                    metadata = {
                        'bot': bot_name,
                        'user': username,
                        'time': timestamp,
                        'source': url,
                        'tag': semantic_db_term,
                        'message': text,
                        'timestring': timestring,
                        'uuid': unique_id,
                        'memory_type': 'Web_Scrape',
                    }
                    client.upsert(collection_name=collection_name,
                                         points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)]) 
                    payload.clear()           
                    pass  
                else:
                    print('---------')
                    print(f"\n\n\nFAILED ARTICLE: {text}")
                    print(f'\nERROR MESSAGE FROM BOT: {webyescheck}\n\n\n')                          
        table = weblist
        
        return table
    except Exception as e:
        print(e)
        table = "Error"
        return table  
        
        
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
        collection_name = f"Bot_{bot_name}_External_Knowledgebase"
        try:
            collection_info = client.get_collection(collection_name=collection_name)
            print(collection_info)
        except:
            client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=embed_size, distance=Distance.COSINE),
        )
        
        for chunk in chunks:
            filesum = list()
            filesum.append({'role': 'system', 'content': "You are a Data Summarizer sub-module, responsible for processing text data from files. Your role includes identifying and highlighting significant or factual information. Extraneous data should be discarded, and only essential details must be returned. Stick to the data provided; do not infer or generalize.  Convert lists into a continuous text summary to maintain this format. Present your responses in a Running Text format using the following pattern: [SEMANTIC QUESTION TAG:SUMMARY]. Note that the semantic question tag should be a question that corresponds to the paired information within the summary. Always provide the two together without linebreaks."})
            filesum.append({'role': 'user', 'content': f"TEXT CHUNK: {chunk}"})
            filesum = list()
            filesum.append({'role': 'system', 'content': "MAIN SYSTEM PROMPT: You are an ai text editor.  Your job is to take the given text from a file, then return the scraped text in an informational article form.  Do not generalize, rephrase, or use latent knowledge in your summary.  If no article is given, print no article.\n\n\n"})
            filesum.append({'role': 'user', 'content': f"FILE TEXT: {chunk}\n\nINSTRUCTIONS: Summarize the text scrape without losing any factual knowledge and maintaining full context. The truncated article will be directly uploaded to a Database, leave out extraneous text and personal statements.[/INST]\n\nASSISTANT: Sure! Here's the summary of the file:"})
            prompt = ''.join([message_dict['content'] for message_dict in filesum])
            text = File_Processor_oobabooga_scrape(prompt)
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
                if 'yes' in fileyescheck.lower():
                    semanticterm = list()
                    semanticterm.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: You are a bot responsible for taging articles with a title for database queries.  Your job is to read the given text, then create a title in question form representative of what the article is about.  The title should be semantically identical to the overview of the article and not include extraneous info. Use the format: [<TITLE IN QUESTION FORM>].\n\n"})
                    semanticterm.append({'role': 'user', 'content': f"ARTICLE: {text}\n\n"})
                    semanticterm.append({'role': 'user', 'content': f"SYSTEM: Create a short, single question that encapsulates the semantic meaning of the Article.  Use the format: [<QUESTION TITLE>].  Please only print the title, it will be directly input in front of the article.[/INST]\n\nASSISTANT: Sure! Here's the summary of the given article:"})
                    prompt = ''.join([message_dict['content'] for message_dict in semanticterm])
                    semantic_db_term = File_Processor_oobabooga_scrape(prompt)
                    filename = os.path.basename(file_path)
                    print('---------')
                    filelist.append(filename + ' ' + paragraph)
                    print(filename + '\n' + semantic_db_term + '\n' + paragraph)
                    payload = list()
                    timestamp = time()
                    timestring = timestamp_to_datetime(timestamp)
                    # Create the collection only if it doesn't exist

                    vector1 = embeddings(filename + '\n' + semantic_db_term + '\n' + paragraph)
                #    embedding = model.encode(query)
                    unique_id = str(uuid4())
                    point_id = unique_id + str(int(timestamp))
                    metadata = {
                        'bot': bot_name,
                        'user': username,
                        'time': timestamp,
                        'source': filename,
                        'message': paragraph,
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
        table = 'Done'
        
        return table
    except Exception as e:
        print(e)
        table = "Error"
        return table  
        
        
def search_and_chunk(query, my_api_key, my_cse_id, **kwargs):
    try:
        urls = google_search(query, my_api_key, my_cse_id, **kwargs)
        chunks = []
        for url in urls:
            chunks += chunk_text_from_url(url)
        return chunks
    except:
        print('Fail1')
    
    
def GPT_4_Tasklist_Web_Scrape(query, results_callback):
    my_api_key = open_file('api_keys/key_google.txt')
    my_cse_id = open_file('api_keys/key_google_cse.txt')
    # # Number of Messages before conversation is summarized, higher number, higher api cost. Change to 3 when using GPT 3.5 due to token usage.
    conv_length = 4
    m = multiprocessing.Manager()
    lock = m.Lock()
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
    webcheck = list()
    counter = 0
    counter2 = 0
    mem_counter = 0
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
    second_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_secondary.txt')
    greeting_msg = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_greeting.txt').replace('<<NAME>>', bot_name)
    if not os.path.exists(f'nexus/{bot_name}/{username}/web_scrape_memory_nexus'):
        os.makedirs(f'nexus/{bot_name}/{username}/web_scrape_memory_nexus')
    if not os.path.exists(f'nexus/{bot_name}/{username}/episodic_memory_nexus'):
        os.makedirs(f'nexus/{bot_name}/{username}/episodic_memory_nexus')
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
        
        # # Check for "Exit"
        if query == 'Skip':   
            pass
        else:
            urls = urls = chunk_text_from_url(query)
        print('---------')
        return
        
        
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
        
        
def GPT_4_Tasklist_Web_Search(query, results_callback):
    my_api_key = open_file('api_keys/key_google.txt')
    my_cse_id = open_file('api_keys/key_google_cse.txt')
        # # Number of Messages before conversation is summarized, higher number, higher api cost. Change to 3 when using GPT 3.5 due to token usage.
    conv_length = 4
    m = multiprocessing.Manager()
    lock = m.Lock()
    conversation = list()
    int_conversation = list()
    payload = list()
    master_tasklist = list()
    counter = 0
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
    main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
    greeting_msg = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_greeting.txt').replace('<<NAME>>', bot_name)
    if not os.path.exists(f'nexus/{bot_name}/{username}/web_scrape_memory_nexus'):
        os.makedirs(f'nexus/{bot_name}/{username}/web_scrape_memory_nexus')
    if not os.path.exists(f'nexus/{bot_name}/{username}/web_scrape_memory_nexus'):
        os.makedirs(f'nexus/{bot_name}/{username}/web_scrape_memory_nexus')
    if not os.path.exists(f'nexus/{bot_name}/{username}/episodic_memory_nexus'):
        os.makedirs(f'nexus/{bot_name}/{username}/episodic_memory_nexus')
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
        print('\nType [Clear Memory] to clear webscrape memory. (Not Enabled)')
        print("\nType [Skip] to skip url input.")
        #    query = input(f'\nEnter search term to scrape: ')
            # # Check for "Exit"
        if query == 'Skip':   
            pass
        else:
            urls = google_search(query, my_api_key, my_cse_id)
            with concurrent.futures.ThreadPoolExecutor() as executor:
                executor.map(chunk_text_from_url, urls)
        print('---------')
        return
        
        
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
        
        
def fail():
  #  print('')
    fail = "Not Needed"
    return fail  
    
    
# Function for Uploading Cadence, called in the create widgets function.
def DB_Upload_Cadence(query):
    # key = input("Enter OpenAi API KEY:")
    username = open_file('./config/prompt_username.txt')
    bot_name = open_file('./config/prompt_bot_name.txt')
    if not os.path.exists(f'nexus/{bot_name}/{username}/cadence_nexus'):
        os.makedirs(f'nexus/{bot_name}/{username}/cadence_nexus')
    while True:
        payload = list()
    #    a = input(f'\n\nUSER: ')        
        timestamp = time()
        timestring = timestamp_to_datetime(timestamp)
        bot_name = open_file('./config/prompt_bot_name.txt')
        username = open_file('./config/prompt_username.txt')
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
            'memory_type': 'Cadence',
        }
        client.upsert(collection_name=collection_name,
                             points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])    
        print('\n\nSYSTEM: Upload Successful!')
        return query
 
        
# Function for Uploading Heuristics, called in the create widgets function.
def DB_Upload_Heuristics(query):
    username = open_file('./config/prompt_username.txt')
    bot_name = open_file('./config/prompt_bot_name.txt')
    if not os.path.exists(f'nexus/{bot_name}/{username}/heuristics_nexus'):
        os.makedirs(f'nexus/{bot_name}/{username}/heuristics_nexus')
    while True:
        payload = list()
    #    a = input(f'\n\nUSER: ')        
        timestamp = time()
        timestring = timestamp_to_datetime(timestamp)
        bot_name = open_file('./config/prompt_bot_name.txt')
        username = open_file('./config/prompt_username.txt')
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
            'user': username,
            'time': timestamp,
            'message': query,
            'timestring': timestring,
            'uuid': unique_id,
            'memory_type': 'Heuristics',
        }
        client.upsert(collection_name=collection_name,
                             points=[PointStruct(id=unique_id, payload=metadata, vector=embedding)])  
        print('\n\nSYSTEM: Upload Successful!')
        return query
        
        
def upload_implicit_long_term_memories(query):
    username = open_file('./config/prompt_username.txt')
    bot_name = open_file('./config/prompt_bot_name.txt')
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
    print('\n\nSYSTEM: Upload Successful!')
    return query
        
        
def upload_explicit_long_term_memories(query):
    username = open_file('./config/prompt_username.txt')
    bot_name = open_file('./config/prompt_bot_name.txt')
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
    print('\n\nSYSTEM: Upload Successful!')
    return query
    
    
def upload_implicit_short_term_memories(query):
    username = open_file('./config/prompt_username.txt')
    bot_name = open_file('./config/prompt_bot_name.txt')
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
        
        
def upload_explicit_short_term_memories(query):
    username = open_file('./config/prompt_username.txt')
    bot_name = open_file('./config/prompt_bot_name.txt')
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
    
    
def ask_upload_implicit_memories(memories):
    username = open_file('./config/prompt_username.txt')
    bot_name = open_file('./config/prompt_bot_name.txt')
    timestamp = time()
    timestring = timestamp_to_datetime(timestamp)
    payload = list()
    result = messagebox.askyesno("Upload Memories", "Do you want to upload memories?")
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
                # Search the collection
        print('\n\nSYSTEM: Upload Successful!')
        return 'yes'
    else:
        # User clicked "No"
        print('\n\nSYSTEM: Memories have been Deleted.')
        
        
def ask_upload_explicit_memories(memories):
    username = open_file('./config/prompt_username.txt')
    bot_name = open_file('./config/prompt_bot_name.txt')
    timestamp = time()
    timestring = timestamp_to_datetime(timestamp)
    payload = list()
    result = messagebox.askyesno("Upload Memories", "Do you want to upload memories?")
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
                # Search the collection
        print('\n\nSYSTEM: Upload Successful!')
        return 'yes'
    else:
        # User clicked "No"
        print('\n\nSYSTEM: Memories have been Deleted.')
        
        
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
        return 'yes'
    else:
        # User clicked "No"
        print('\n\nSYSTEM: Memories have been Deleted.')
        return 'no'
        
        
def upload_implicit_short_term_memories(query):
    username = open_file('./config/prompt_username.txt')
    bot_name = open_file('./config/prompt_bot_name.txt')
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
        
        
def upload_explicit_short_term_memories(query):
    username = open_file('./config/prompt_username.txt')
    bot_name = open_file('./config/prompt_bot_name.txt')
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
    username = open_file('./config/prompt_username.txt')
    bot_name = open_file('./config/prompt_bot_name.txt')
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
    username = open_file('./config/prompt_username.txt')
    bot_name = open_file('./config/prompt_bot_name.txt')
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
    username = open_file('./config/prompt_username.txt')
    bot_name = open_file('./config/prompt_bot_name.txt')
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
        
        
# Running Conversation List
class MainConversation:
    def __init__(self, max_entries, prompt, greeting):
        bot_name = open_file('./config/prompt_bot_name.txt')
        username = open_file('./config/prompt_username.txt')
        self.max_entries = max_entries
        self.file_path = f'./history/{username}/{bot_name}_main_conversation_history.json'
        self.file_path2 = f'./history/{username}/{bot_name}_main_history.json'
        self.main_conversation = [prompt, greeting]

        # Load existing conversation from file
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.running_conversation = data.get('running_conversation', [])
        else:
            self.running_conversation = []

    def append(self, timestring, username, a, bot_name, response_two):
        # Append new entry to the running conversation
        entry = []
        entry.append(f"{timestring}-{username}: {a}")
        entry.append(f"Response: {response_two}")
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
        
    def show_context_menu(self, event):
        # Create the menu
        menu = tk.Menu(self, tearoff=0)
        # Right Click Menu
        menu.add_command(label="Copy", command=self.copy_selected_text)
        # Display the menu at the clicked position
        menu.post(event.x_root, event.y_root)
        
        
    def display_conversation_history(self):
        # Load the conversation history from the JSON file
        bot_name = open_file('./config/prompt_bot_name.txt')
        username = open_file('./config/prompt_username.txt')
        
        file_path = f'./history/{username}/{bot_name}_main_conversation_history.json'
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
            # Handle the case when the JSON file is not found
            greeting_msg = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_greeting.txt').replace('<<NAME>>', bot_name)
            self.conversation_text.insert(tk.END, greeting_msg + '\n\n')
        self.conversation_text.yview(tk.END)
        
        
    # #  Login Menu 
    # Edit Bot Name
    def choose_bot_name(self):
        username = open_file('./config/prompt_username.txt')

        # Check if the prompt_bot_name.txt file exists and read the current bot name
        file_path = "./config/prompt_bot_name.txt"
        current_bot_name = ""
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                current_bot_name = file.readline().strip()

        dark_bg_color = "#2B2B2B"
        light_text_color = "#ffffff"

        # Use current_bot_name as the initialvalue for the simpledialog
        bot_name = simpledialog.askstring("Choose Bot Name", "Type a Bot Name:", initialvalue=current_bot_name)
        if bot_name:
            file_path = "./config/prompt_bot_name.txt"
            with open(file_path, 'w') as file:
                file.write(bot_name)
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
            self.conversation_text.delete("1.0", tk.END)
            self.display_conversation_history() 
            self.master.destroy()
            Llama_2_Chat_Aetherius_Main()
        

    # Edit User Name
    def choose_username(self):
        bot_name = open_file('./config/prompt_bot_name.txt')
        dark_bg_color = "#2B2B2B"
        light_text_color = "#ffffff"

        # Check if the prompt_username.txt file exists and read the current username
        file_path = "./config/prompt_username.txt"
        current_username = ""
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                current_username = file.readline().strip()

        # Use current_username as the initialvalue for the simpledialog
        username = simpledialog.askstring("Choose Username", "Type a Username:", initialvalue=current_username)

        
        if username:
            file_path = "./config/prompt_username.txt"
            with open(file_path, 'w') as file:
                file.write(username)
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
            self.conversation_text.delete("1.0", tk.END)
            self.display_conversation_history()
            self.master.destroy()
            Llama_2_Chat_Aetherius_Main()
        pass
        
        
    # Edits Main Chatbot System Prompt
    def Edit_Main_Prompt(self):
        bot_name = open_file('./config/prompt_bot_name.txt')
        username = open_file('./config/prompt_username.txt')
        file_path = f"./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt"
        dark_bg_color = "#2B2B2B"
        light_text_color = "#ffffff"

        with open(file_path, 'r', encoding='utf-8') as file:
            prompt_contents = file.read()

        top = tk.Toplevel(self)
        top.configure(bg=dark_bg_color)
        top.title("Edit Main Prompt")

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
        
        
    # Edit secondary prompt (Less priority than main prompt)    
    def Edit_Secondary_Prompt(self):
        bot_name = open_file('./config/prompt_bot_name.txt')
        username = open_file('./config/prompt_username.txt')
        file_path = f"./config/Chatbot_Prompts/{username}/{bot_name}/prompt_secondary.txt"
        dark_bg_color = "#2B2B2B"
        light_text_color = "#ffffff"
        
        with open(file_path, 'r', encoding='utf-8') as file:
            prompt_contents = file.read()
        
        top = tk.Toplevel(self)
        top.configure(bg=dark_bg_color)
        top.title("Edit Secondary Prompt")
        
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
        
        
    # Edits initial chatbot greeting, called in create widgets
    def Edit_Greeting_Prompt(self):
        bot_name = open_file('./config/prompt_bot_name.txt')
        username = open_file('./config/prompt_username.txt')
        file_path = f"./config/Chatbot_Prompts/{username}/{bot_name}/prompt_greeting.txt"
        dark_bg_color = "#2B2B2B"
        light_text_color = "#ffffff"
        
        with open(file_path, 'r', encoding='utf-8') as file:
            prompt_contents = file.read()
        
        top = tk.Toplevel(self)
        top.configure(bg=dark_bg_color)
        top.title("Edit Greeting Prompt")
        
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
        
        
    # Edits running conversation list
    def Edit_Conversation(self):
        bot_name = open_file('./config/prompt_bot_name.txt')
        username = open_file('./config/prompt_username.txt')
        file_path = f"./history/{username}/{bot_name}_main_conversation_history.json"
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
        bot_name = open_file('./config/prompt_bot_name.txt')
        username = open_file('./config/prompt_username.txt')
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
            username = open_file('./config/prompt_username.txt')
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
                                    match=models.MatchValue(value=f"{username}"),
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
        bot_name = open_file('./config/prompt_bot_name.txt')
        username = open_file('./config/prompt_username.txt')
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
            username = open_file('./config/prompt_username.txt')
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
                                    match=models.MatchValue(value=f"{username}"),
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
        bot_name = open_file('./config/prompt_bot_name.txt')
        username = open_file('./config/prompt_username.txt')
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
        bot_name = open_file('./config/prompt_bot_name.txt')
        username = open_file('./config/prompt_username.txt')
        deletion_window = tk.Toplevel(self)
        deletion_window.configure(bg=dark_bg_color)
        deletion_window.title("DB Deletion Menu")
        
        
        def delete_cadence():
                # Replace 'username' and 'bot_name' with appropriate variables if available.
                # You may need to adjust 'vdb' based on how your database is initialized.
            username = open_file('./config/prompt_username.txt')
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
                                    match=models.MatchValue(value=f"{username}"),
                                ),
                            ],
                        )
                    ),
                )   
        
    
        def delete_heuristics():
                # Replace 'username' and 'bot_name' with appropriate variables if available.
                # You may need to adjust 'vdb' based on how your database is initialized.
            username = open_file('./config/prompt_username.txt')
            bot_name = open_file('./config/prompt_bot_name.txt')
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
                                    match=models.MatchValue(value=f"{username}"),
                                ),
                            ],
                        )
                    ),
                )   
                
                
        def delete_counters():
                # Replace 'username' and 'bot_name' with appropriate variables if available.
                # You may need to adjust 'vdb' based on how your database is initialized.
            username = open_file('./config/prompt_username.txt')
            bot_name = open_file('./config/prompt_bot_name.txt')
            confirm = messagebox.askyesno("Confirmation", "Are you sure you want to delete memory consolidation counters?")
            if confirm:
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
                client.delete(
                    collection_name=f"Consol_Counter_Bot_{bot_name}",
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
                
        def delete_webscrape():
                # Replace 'username' and 'bot_name' with appropriate variables if available.
                # You may need to adjust 'vdb' based on how your database is initialized.
            username = open_file('./config/prompt_username.txt')
            bot_name = open_file('./config/prompt_bot_name.txt')
            confirm = messagebox.askyesno("Confirmation", "Are you sure you want to delete the saved webscrape?")
            if confirm:
                client.delete(
                    collection_name=f"Bot_{bot_name}_External_Knowledgebase",
                    points_selector=models.FilterSelector(
                        filter=models.Filter(
                            must=[
                                models.FieldCondition(
                                    key="user",
                                    match=models.MatchValue(value=f"{username}"),
                                ),
                                models.FieldCondition(
                                    key="memory_type",
                                    match=models.MatchValue(value=f"Web_Scrape"),
                                ),
                            ],
                        )
                    ),
                ) 
                
        def delete_filescrape():
                # Replace 'username' and 'bot_name' with appropriate variables if available.
                # You may need to adjust 'vdb' based on how your database is initialized.
            username = open_file('./config/prompt_username.txt')
            bot_name = open_file('./config/prompt_bot_name.txt')
            confirm = messagebox.askyesno("Confirmation", "Are you sure you want to delete the saved scraped files?")
            if confirm:
                client.delete(
                    collection_name=f"Bot_{bot_name}_External_Knowledgebase",
                    points_selector=models.FilterSelector(
                        filter=models.Filter(
                            must=[
                                models.FieldCondition(
                                    key="user",
                                    match=models.MatchValue(value=f"{username}"),
                                ),
                                models.FieldCondition(
                                    key="memory_type",
                                    match=models.MatchValue(value=f"Web_Scrape"),
                                ),
                            ],
                        )
                    ),
                ) 

                
                
        def delete_bot():
                # Replace 'username' and 'bot_name' with appropriate variables if available.
                # You may need to adjust 'vdb' based on how your database is initialized.
            username = open_file('./config/prompt_username.txt')
            bot_name = open_file('./config/prompt_bot_name.txt')
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
                                        match=models.MatchValue(value=f"{username}"),
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
                                        match=models.MatchValue(value=f"{username}"),
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
                                        match=models.MatchValue(value=f"{username}"),
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
                                        match=models.MatchValue(value=f"{username}"),
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
                                        match=models.MatchValue(value=f"{username}"),
                                    ),
                                ],
                            )
                        ),
                    )
                except:
                    pass
                try:
                    client.delete(
                        collection_name=f"Consol_Counter_Bot_{bot_name}",
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
        bot_name = open_file('./config/prompt_bot_name.txt')
        username = open_file('./config/prompt_username.txt')
        file_path = f'./history/{username}/{bot_name}_main_conversation_history.json'
        try:
            os.remove(file_path)
            # Reload the script
            self.master.destroy()
            Llama_2_Chat_Aetherius_Main()
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
        
        model_stt = whisper.load_model("small")
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


    def process_message(self, a):
        self.conversation_text.insert(tk.END, f"\nYou: {a}\n\n")
        self.conversation_text.yview(tk.END)
        if self.is_external_resources_checked():
            t = threading.Thread(target=self.Agent_Tasklist_Inner_Monologue, args=(a,))
            t.start()
        else:
            t = threading.Thread(target=self.GPT_Inner_Monologue, args=(a,))
            t.start()
        
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

        def perform_search():
            query = query_entry.get()

            def update_results(paragraph):
                # Update the GUI with the new paragraph
                results_text.insert(tk.END, f"{paragraph}\n\n")
                results_text.yview(tk.END)
            #    self.update_results(results_text, paragraph)

            def search_task():
                # Call the modified GPT_4_Tasklist_Web_Search function with the callback
                GPT_4_Tasklist_Web_Search(query, results_callback=update_results)

            t = threading.Thread(target=search_task)
            t.start()
            
        def perform_scrape():
            query = query_entry.get()

            def update_results(paragraph):
                # Update the GUI with the new paragraph
                self.update_results(results_text, paragraph)

            def search_task():
                # Call the modified GPT_4_Tasklist_Web_Search function with the callback
                GPT_4_Tasklist_Web_Scrape(query, results_callback=update_results)

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

        
    # Selects which Open Ai model to use.    
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
        file_path = "./config/font.txt"
        dark_bg_color = "#2B2B2B"
        light_text_color = "#ffffff"

        with open(file_path, 'r', encoding='utf-8') as file:
            font_value = file.read()

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
                with open(file_path, 'w') as file:
                    file.write(new_font)
                self.update_font_settings()
            top.destroy()
            
        save_button = customtkinter.CTkButton(top, text="Save", command=save_font)
        save_button.pack()
        

    # Change Font Size, called in create widgets
    def Edit_Font_Size(self):
        file_path = "./config/font_size.txt"
        dark_bg_color = "#2B2B2B"
        light_text_color = "#ffffff"

        with open(file_path, 'r', encoding='utf-8') as file:
            font_size_value = file.read()

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
                with open(file_path, 'w') as file:
                    file.write(new_font_size)
                self.update_font_settings()
            top.destroy()

        save_button = customtkinter.CTkButton(top, text="Save", command=save_font_size)
        save_button.pack()

        top.mainloop()
        
        
    # Change Conversation Length, called in create widgets
    def Set_Conv_Length(self):
        file_path = "./config/Conversation_Length.txt"
        dark_bg_color = "#2B2B2B"
        light_text_color = "#ffffff"

        with open(file_path, 'r', encoding='utf-8') as file:
            font_size_value = file.read()

        top = tk.Toplevel(self)
        top.configure(bg=dark_bg_color)
        top.title("Set Converation Length")

        label = customtkinter.CTkLabel(top, text="(Lengths longer than 3 tend to break smaller models.)\nEnter desired conversation length:")
        label.pack()

        self.font_size_entry = tk.Entry(top, bg=dark_bg_color, fg=light_text_color)
        self.font_size_entry.insert(tk.END, font_size_value)
        self.font_size_entry.pack()

        def save_conv_length():
            new_font_size = self.font_size_entry.get()
            if new_font_size.isdigit():
                with open(file_path, 'w') as file:
                    file.write(new_font_size)
            top.destroy()

        save_button = customtkinter.CTkButton(top, text="Save", command=save_conv_length)
        save_button.pack()

        top.mainloop()
        
        
    # Change Host, called in create widgets
    def Set_Host(self):
        file_path = "./api_keys/HOST_Oobabooga.txt"
        dark_bg_color = "#2B2B2B"
        light_text_color = "#ffffff"

        with open(file_path, 'r', encoding='utf-8') as file:
            host_value = file.read()

        top = tk.Toplevel(self)
        top.configure(bg=dark_bg_color)
        top.title("Set Oobabooga Host")

        # Replace label with a read-only Text widget to allow selection
        label_text = "(Default Localhost: http://localhost:5000/api)\nEnter the Non-Streaming URL from the Oobabooga Public Api Google Colab:"
        
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
        
        
    def Set_Embed(self):
        file_path = "./config/Settings/embedding_model.txt"
        dark_bg_color = "#2B2B2B"
        light_text_color = "#ffffff"

        with open(file_path, 'r', encoding='utf-8') as file:
            host_value = file.read()

        top = tk.Toplevel(self)
        top.configure(bg=dark_bg_color)
        top.title("Set Embedding Model")

        # Replace label with a read-only Text widget to allow selection
        label_text = "Options: sentence_xformers, hf_embeddings\nEnter what embedding provider you wish to use:"
        
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
        file_path = "./config/Settings/TTS.txt"
        dark_bg_color = "#2B2B2B"
        light_text_color = "#ffffff"

        with open(file_path, 'r', encoding='utf-8') as file:
            host_value = file.read()

        top = tk.Toplevel(self)
        top.configure(bg=dark_bg_color)
        top.title("Set TTS Model")

        # Replace label with a read-only Text widget to allow selection
        label_text = "Options: gTTS(Google), elevenTTS(Elevenlabs), barkTTS(Suno-ai)\nEnter what TTS provider you wish to use:"
        
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
            self.master.destroy()
            Llama_2_Chat_Aetherius_Main()

        save_button = customtkinter.CTkButton(top, text="Save", command=save_host)
        save_button.pack(pady=10)

        top.mainloop()
        

    #Fallback to size 10 if no font size
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
        selection = self.mode_menu.get()
        if selection == "Auto":
            self.memory_mode = "Auto"
            print("Auto mode selected!")
                # Add the logic for Auto mode here
        elif selection == "Manual":
            self.memory_mode = "Manual"
            print("Manual mode selected!")
                # Add the logic for Manual mode here
        elif selection == "Training":
            self.memory_mode = "Training"
            print("Training mode selected!")
        elif selection == "None":
            self.memory_mode = "None"
            print("Memory Upload Disabled.")
            
            
    def is_external_resources_checked(self):
        return self.external_resources_var.get()

    def is_web_db_checked(self):
        return self.web_db_var.get()
        
        
    def is_tts_checked(self):
        return self.tts_var.get()
        

    def is_file_db_checked(self):
        return self.file_db_var.get()

    def is_memory_db_checked(self):
        return self.memory_db_var.get()
        
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
        font_config = open_file('./config/font.txt')
        font_size = open_file('./config/font_size.txt')
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
            except Exception as e:
                print(f"Error in handle_login_menu_selection: {e}")
                
        # Login dropdown Menu
        self.login_menu = customtkinter.CTkComboBox(self.settings_frame, width=115, values=["Choose Bot Name", "Choose Username", "Edit Main Prompt", "Edit Secondary Prompt", "Edit Greeting Prompt"], state="readonly", command=self.handle_login_menu_selection)
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

                self.tokens_value.set("Max Tokens: N/A")
                self.tokens_scale_widget.set(1000)  # Setting the slider to a neutral position, adjust if necessary
                self.top_p_value.set("Top P: N/A")
                self.top_p_scale_widget.set(0.5)  # Neutral position for top_p slider (mid-point between 0.00 and 1.00)
                self.top_k_value.set("Top K: N/A")
                self.top_k_scale_widget.set(50)  # Mid value for top_k
                self.min_tokens_value.set("Min Tokens: N/A")
                self.min_tokens_scale_widget.set(40)  # Setting the slider to a neutral position, adjust if necessary
                return
                
                

            # Otherwise, update based on file values:
            
            # For Temperature:
            temp_file_path = f"./config/Generation_Settings/{current_selection}/temperature.txt"
            try:
                with open(temp_file_path, 'r') as file:
                    current_value = float(file.read().strip())
                    self.scale_widget.set(current_value)
                    self.temperature_value.set(f"Temperature: {current_value:.2f}")
                    self.temperature_label = customtkinter.CTkLabel(self.settings_frame, text=f"Temperature: {open_file_menu(f'./config/Generation_Settings/{current_selection}/temperature.txt')}", font=('bold', font_size_config))
                    self.temperature_label.grid(row=3, column=0, padx=5, pady=1, sticky=tk.W+tk.E)
            except:
                print(f"Error reading {temp_file_path}")

                
            # For Top P:
            top_p_file_path = f"./config/Generation_Settings/{current_selection}/top_p.txt"
            try:
                with open(top_p_file_path, 'r') as file:
                    current_value = float(file.read().strip())
                    self.top_p_scale_widget.set(current_value)
                    self.top_p_value.set(f"Top P: {current_value:.2f}")
                    self.top_p_label = customtkinter.CTkLabel(self.settings_frame, text=f"Top_P: {open_file_menu(f'./config/Generation_Settings/{current_selection}/top_p.txt')}", font=('bold', font_size_config))
                    self.top_p_label.grid(row=5, column=0, padx=5, pady=1, sticky=tk.W+tk.E)
            except:
                print(f"Error reading {top_p_file_path}")
            # For Top K:
            top_k_file_path = f"./config/Generation_Settings/{current_selection}/top_k.txt"
            try:
                with open(top_k_file_path, 'r') as file:
                    current_value = int(file.read().strip())
                    self.top_k_scale_widget.set(current_value)
                    self.top_k_value.set(f"Top K: {current_value}")
                    self.top_k_label = customtkinter.CTkLabel(self.settings_frame, text=f"Top_K: {open_file_menu(f'./config/Generation_Settings/{current_selection}/top_k.txt')}", font=('bold', font_size_config))
                    self.top_k_label.grid(row=7, column=0, padx=5, pady=1, sticky=tk.W+tk.E)
            except:
                print(f"Error reading {top_k_file_path}")
                
            # For Repetition Penalty:
            rep_pen_file_path = f"./config/Generation_Settings/{current_selection}/rep_pen.txt"
            try:
                with open(rep_pen_file_path, 'r') as file:
                    current_value = float(file.read().strip())
                    self.rep_pen_scale_widget.set(current_value)
                    self.rep_pen_value.set(f"Repetition Penalty: {current_value:.2f}")
                    self.rep_pen_label = customtkinter.CTkLabel(self.settings_frame, text=f"Repetition Penalty: {open_file_menu(f'./config/Generation_Settings/{current_selection}/rep_pen.txt')}", font=('bold', font_size_config))
                    self.rep_pen_label.grid(row=9, column=0, padx=5, pady=1, sticky=tk.W+tk.E)
            except:
                print(f"Error reading {rep_pen_file_path}")
                
            # For Min Tokens:
            min_token_file_path = f"./config/Generation_Settings/{current_selection}/min_tokens.txt"
            try:
                with open(min_token_file_path, 'r') as file:
                    current_value = int(file.read().strip())
                    self.min_tokens_scale_widget.set(current_value)
                    self.min_tokens_value.set(f"Min Tokens: {current_value}")
                    self.min_tokens_label = customtkinter.CTkLabel(self.settings_frame, text=f"Min_Tokens: {open_file_menu(f'./config/Generation_Settings/{current_selection}/min_tokens.txt')}", font=('bold', font_size_config))
                    self.min_tokens_label.grid(row=11, column=0, padx=5, pady=1, sticky=tk.W+tk.E)
            except:
                print(f"Error reading {min_token_file_path}")
                
            # For Max Tokens:
            token_file_path = f"./config/Generation_Settings/{current_selection}/max_tokens.txt"
            try:
                with open(token_file_path, 'r') as file:
                    current_value = int(file.read().strip())
                    self.tokens_scale_widget.set(current_value)
                    self.tokens_value.set(f"Max Tokens: {current_value}")
                    self.tokens_label = customtkinter.CTkLabel(self.settings_frame, text=f"Max_Tokens: {open_file_menu(f'./config/Generation_Settings/{current_selection}/max_tokens.txt')}", font=('bold', font_size_config))
                    self.tokens_label.grid(row=13, column=0, padx=5, pady=1, sticky=tk.W+tk.E)
            except:
                print(f"Error reading {token_file_path}")
                
                
        self.parm_title_label = customtkinter.CTkLabel(self.settings_frame, text=f"Parameter Settings:", font=('bold', font_size_config))
        self.parm_title_label.grid(row=1, column=0, padx=5, sticky=tk.W+tk.E)
 

        
        self.loop_menu = customtkinter.CTkComboBox(self.settings_frame, width=115, values=["Loop Selection", "Inner_Monologue", "Intuition", "Response"], state="readonly", command=handle_loop_menu_selection)
        self.loop_menu.grid(row=2, column=0, padx=5, pady=9, sticky=tk.W+tk.E)
        self.loop_menu.set("Loop Selection")
        self.loop_menu.bind("<<ComboboxSelected>>", handle_loop_menu_selection)

        def update_value(value):
            # Function called when the slider value is changed.
            current_selection = self.loop_menu.get()
            file_path = f"./config/Generation_Settings/{current_selection}/temperature.txt"
            formatted_value = f"{float(value):.2f}" # Format the value to two decimal places
            try:
                with open(file_path, 'w') as file:
                    file.write(formatted_value)
                self.temperature_value.set(f"Temperature: {formatted_value}")  # update the label with formatted value
            except:
                print(f"Error writing to {file_path}")
            self.temperature_label = customtkinter.CTkLabel(self.settings_frame, text=f"Temperature: {open_file_menu(f'./config/Generation_Settings/{current_selection}/temperature.txt')}", font=('bold', font_size_config))
            self.temperature_label.grid(row=3, column=0, padx=5, pady=1, sticky=tk.W+tk.E)

        current_selection = self.loop_menu.get()
        self.temperature_value = tk.StringVar()

        # Set the initial value using "Inner Monologue" since the initial dropdown selection is "Loop Selection" which maps to "N/A"
        self.temperature_value.set(f"Temperature: {open_file_menu(f'./config/Generation_Settings/{current_selection}/temperature.txt')}")

        self.temperature_label = customtkinter.CTkLabel(self.settings_frame, text=f"Temperature: {open_file_menu(f'./config/Generation_Settings/{current_selection}/temperature.txt')}", font=('bold', font_size_config))
        self.temperature_label.grid(row=3, column=0, padx=5, pady=1, sticky=tk.W+tk.E)

        # Adjusted the range and resolution of the slider for the new values
        self.scale_widget = customtkinter.CTkSlider(self.settings_frame, from_=0.00, to=2.0, number_of_steps=40, command=update_value, width=140)
        self.scale_widget.grid(row=4, column=0, padx=5, pady=3, sticky=tk.W+tk.E)
        

        
        
        # Function to update top_p value when the slider is moved
        def update_top_p(value):
            current_selection = self.loop_menu.get()
            file_path = f"./config/Generation_Settings/{current_selection}/top_p.txt"
            formatted_value = f"{float(value):.2f}"
            try:
                with open(file_path, 'w') as file:
                    file.write(formatted_value)
                self.top_p_value.set(f"Top P: {formatted_value}")  # update the label with formatted value
                self.top_p_label = customtkinter.CTkLabel(self.settings_frame, text=f"Top_P: {open_file_menu(f'./config/Generation_Settings/{current_selection}/top_p.txt')}", font=('bold', font_size_config))
                self.top_p_label.grid(row=5, column=0, padx=5, pady=1, sticky=tk.W+tk.E)
            except:
                print(f"Error writing to {file_path}")

        # GUI Widget for Top P
        self.top_p_value = tk.StringVar()
        self.top_p_value.set("Top P: 0.50")  # Default value
        self.top_p_label = customtkinter.CTkLabel(self.settings_frame, text=f"Top_P: {open_file_menu(f'./config/Generation_Settings/{current_selection}/top_p.txt')}", font=('bold', font_size_config))
        self.top_p_label.grid(row=5, column=0, padx=5, pady=1, sticky=tk.W+tk.E)

        self.top_p_scale_widget = customtkinter.CTkSlider(self.settings_frame, from_=0.00, to=1.00, number_of_steps=100, command=update_top_p, width=140)
        self.top_p_scale_widget.grid(row=6, column=0, padx=5, pady=3, sticky=tk.W+tk.E)
        
        # Function to update top_k value when the slider is moved
        def update_top_k(value):
            current_selection = self.loop_menu.get()
            file_path = f"./config/Generation_Settings/{current_selection}/top_k.txt"
            try:
                with open(file_path, 'w') as file:
                    file.write(str(int(value)))
                self.top_k_value.set(f"Top K: {int(value)}")  # update the label with the integer value
                self.top_k_label = customtkinter.CTkLabel(self.settings_frame, text=f"Top_K: {open_file_menu(f'./config/Generation_Settings/{current_selection}/top_k.txt')}", font=('bold', font_size_config))
                self.top_k_label.grid(row=7, column=0, padx=5, pady=1, sticky=tk.W+tk.E)
            except:
                print(f"Error writing to {file_path}")

        # GUI Widget for Top K
        self.top_k_value = tk.StringVar()
        self.top_k_value.set("Top K: 50")  # Default value
        self.top_k_label = customtkinter.CTkLabel(self.settings_frame, text=f"Top_K: {open_file_menu(f'./config/Generation_Settings/{current_selection}/top_k.txt')}", font=('bold', font_size_config))
        self.top_k_label.grid(row=7, column=0, padx=5, pady=1, sticky=tk.W+tk.E)

        self.top_k_scale_widget = customtkinter.CTkSlider(self.settings_frame, from_=0, to=100, number_of_steps=101, command=update_top_k, width=140)  # 101 steps for the range 0 to 100 inclusive
        self.top_k_scale_widget.grid(row=8, column=0, padx=5, pady=3, sticky=tk.W+tk.E)
        
        def update_rep_pen(value):
            # Function called when the repetition penalty slider value is changed.
            current_selection = self.loop_menu.get()
            file_path = f"./config/Generation_Settings/{current_selection}/rep_pen.txt"
            formatted_value = f"{float(value):.2f}"
            try:
                with open(file_path, 'w') as file:
                    file.write(formatted_value) 
                self.rep_pen_value.set(f"Repetition Penalty: {formatted_value}")  # update the label with formatted value
            except:
                print(f"Error writing to {file_path}")
            self.rep_pen_label = customtkinter.CTkLabel(self.settings_frame, text=f"Repetition Penalty: {open_file_menu(f'./config/Generation_Settings/{current_selection}/rep_pen.txt')}", font=('bold', font_size_config))
            self.rep_pen_label.grid(row=9, column=0, padx=5, pady=1, sticky=tk.W+tk.E)

        self.rep_pen_value = tk.StringVar()
        self.rep_pen_value.set("Repetition Penalty: 1.0")  # Set a default value (can be adjusted)
        self.rep_pen_label = customtkinter.CTkLabel(self.settings_frame, text=f"Repetition Penalty: {open_file_menu(f'./config/Generation_Settings/{current_selection}/rep_pen.txt')}", font=('bold', font_size_config))
        self.rep_pen_label.grid(row=9, column=0, padx=5, pady=1, sticky=tk.W+tk.E)

        # You might want to adjust the range and steps based on the desired range for repetition penalty.
        self.rep_pen_scale_widget = customtkinter.CTkSlider(self.settings_frame, from_=0.0, to=2.0, number_of_steps=40, command=update_rep_pen, width=140)
        self.rep_pen_scale_widget.grid(row=10, column=0, padx=5, pady=3, sticky=tk.W+tk.E)
        
        
        def update_min_tokens(value):
            # Function called when the tokens slider value is changed.
            current_selection = self.loop_menu.get()
            file_path = f"./config/Generation_Settings/{current_selection}/min_tokens.txt"
            try:
                with open(file_path, 'w') as file:
                    file.write(str(int(value)))  # Storing the value as an integer
                self.min_tokens_value.set(f"Min Tokens: {int(value)}")  # update the label
            except:
                print(f"Error writing to {file_path}")
            self.min_tokens_label = customtkinter.CTkLabel(self.settings_frame, text=f"Min_Tokens: {open_file_menu(f'./config/Generation_Settings/{current_selection}/min_tokens.txt')}", font=('bold', font_size_config))
            self.min_tokens_label.grid(row=11, column=0, padx=5, pady=1, sticky=tk.W+tk.E)
                

        self.min_tokens_value = tk.StringVar()
        self.min_tokens_value.set("Min Tokens: 0")  # Set a default value (can be adjusted)
        self.min_tokens_label = customtkinter.CTkLabel(self.settings_frame, text=f"Min_Tokens: {open_file_menu(f'./config/Generation_Settings/{current_selection}/min_tokens.txt')}", font=('bold', font_size_config))
        self.min_tokens_label.grid(row=11, column=0, padx=5, pady=1, sticky=tk.W+tk.E)

        # Assuming you want a range of 0 to 1000 tokens. Adjust the range and steps accordingly.
        self.min_tokens_scale_widget = customtkinter.CTkSlider(self.settings_frame, from_=0, to=1000, number_of_steps=100, command=update_min_tokens, width=140)
        self.min_tokens_scale_widget.grid(row=12, column=0, padx=5, pady=3, sticky=tk.W+tk.E)
        
        
        def update_tokens(value):
            # Function called when the tokens slider value is changed.
            current_selection = self.loop_menu.get()
            file_path = f"./config/Generation_Settings/{current_selection}/max_tokens.txt"
            try:
                with open(file_path, 'w') as file:
                    file.write(str(int(value)))  # Storing the value as an integer
                self.tokens_value.set(f"Max Tokens: {int(value)}")  # update the label
            except:
                print(f"Error writing to {file_path}")
            self.tokens_label = customtkinter.CTkLabel(self.settings_frame, text=f"Max_Tokens: {open_file_menu(f'./config/Generation_Settings/{current_selection}/max_tokens.txt')}", font=('bold', font_size_config))
            self.tokens_label.grid(row=13, column=0, padx=5, pady=1, sticky=tk.W+tk.E)
                

        self.tokens_value = tk.StringVar()
        self.tokens_value.set("Max Tokens: 0")  # Set a default value (can be adjusted)
        self.tokens_label = customtkinter.CTkLabel(self.settings_frame, text=f"Max_Tokens: {open_file_menu(f'./config/Generation_Settings/{current_selection}/max_tokens.txt')}", font=('bold', font_size_config))
        self.tokens_label.grid(row=13, column=0, padx=5, pady=1, sticky=tk.W+tk.E)

        # Assuming you want a range of 0 to 1000 tokens. Adjust the range and steps accordingly.
        self.tokens_scale_widget = customtkinter.CTkSlider(self.settings_frame, from_=10, to=2000, number_of_steps=100, command=update_tokens, width=140)
        self.tokens_scale_widget.grid(row=14, column=0, padx=5, pady=3, sticky=tk.W+tk.E)
        
        
        


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
            elif selection == "Set Oobabooga HOST":
                self.Set_Host()
            elif selection == "Set Embedding Model":
                self.Set_Embed()
            elif selection == "Set TTS Model":
                self.Set_TTS()
        
        # Config Dropdown Menu
        self.menu = customtkinter.CTkComboBox(self.top_frame, values=["Set Oobabooga HOST", "Set Embedding Model", "Set TTS Model", "Edit Font", "Edit Font Size", "Set Conv Length"], state="readonly", command=handle_menu_selection)
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
            selection = self.mode_menu.get()
            if selection == "Auto":
                memory_mode = "Auto"
                print("Auto mode selected!")
                # Add the logic for Auto mode here
            elif selection == "Manual":
                memory_mode = "Manual"
                print("Manual mode selected!")
                # Add the logic for Manual mode here
            elif selection == "Training":
                memory_mode = "Training"
                print("Training mode selected!")
            elif selection == "None":
                memory_mode = "None"
                print("Memory Upload Disabled.")

        self.tts_var = tk.BooleanVar(value=False)
        

        self.voice_button = customtkinter.CTkButton(self.input_frame, text="Voice", command=self.initiate_record_audio, width=50)  
        self.voice_button.grid(row=2, column=3, padx=5)

        self.send_button = customtkinter.CTkButton(self.input_frame, text="Send", command=self.send_message, width=120)  
        self.send_button.grid(row=2, column=2, padx=5, pady=3)
        
        self.mode_menu = customtkinter.CTkComboBox(self.input_frame, values=["Auto", "Manual", "Training", "None"], state="readonly", command=self.handle_memory_selection, width=120)
        self.mode_menu.grid(row=1, column=2, padx=5, pady=10, sticky=tk.W+tk.E)
        self.mode_menu.set("Memory Mode")
        self.mode_menu.bind("<<ComboboxSelected>>", handle_memory_selection)
        
        self.tts_check = customtkinter.CTkCheckBox(self.input_frame, variable=self.tts_var, text="TTS", width=12)
        self.tts_check.grid(row=1, column=3, padx=5)
        
        
        def toggle_db_checkboxes():
            if self.external_resources_var.get() == 1:  # if External Resources is checked
                self.web_db_check.configure(state=tk.NORMAL)
                self.file_db_check.configure(state=tk.NORMAL)
                self.memory_db_check.configure(state=tk.NORMAL)
            else:
                self.web_db_check.configure(state=tk.DISABLED)
                self.file_db_check.configure(state=tk.DISABLED)
                self.memory_db_check.configure(state=tk.DISABLED)

                # Uncheck the other checkboxes
                self.web_db_var.set(0)
                self.file_db_var.set(0)
                self.memory_db_var.set(0)
                
        self.tools_frame = customtkinter.CTkFrame(self)
        self.tools_frame.grid(row=2, column=0, sticky=tk.W+tk.N)
        
        self.tools_menu = customtkinter.CTkComboBox(self.tools_frame, values=["Web Search", "File Process"], state="readonly", command=self.handle_tools_menu_selection)
        self.tools_menu.grid(row=0, column=0, padx=5, sticky=tk.W+tk.E)
        self.tools_menu.set("Tools")
        self.tools_menu.bind("<<ComboboxSelected>>", self.handle_tools_menu_selection)
        
        self.checkmarks_frame = customtkinter.CTkFrame(self)
        self.checkmarks_frame.grid(row=3, column=0, sticky=tk.W+tk.N)
        
        self.external_resources_var = tk.BooleanVar(value=False)
        self.web_db_var = tk.BooleanVar(value=False)
        self.file_db_var = tk.BooleanVar(value=False)
        self.memory_db_var = tk.BooleanVar(value=False)


        self.external_resources_check = customtkinter.CTkCheckBox(self.checkmarks_frame, text="Agent Mode", variable=self.external_resources_var, command=toggle_db_checkboxes)
        self.external_resources_check.grid(row=0, column=0, sticky=tk.W, padx=25)

        self.web_db_check = customtkinter.CTkCheckBox(self.checkmarks_frame, text="Web DB", variable=self.web_db_var, state=tk.DISABLED)
        self.web_db_check.grid(row=1, column=0, sticky=tk.W, padx=25)

        self.file_db_check = customtkinter.CTkCheckBox(self.checkmarks_frame, text="File DB", variable=self.file_db_var, state=tk.DISABLED)
        self.file_db_check.grid(row=2, column=0, sticky=tk.W, padx=25)

        self.memory_db_check = customtkinter.CTkCheckBox(self.checkmarks_frame, text="Memory DB", variable=self.memory_db_var, state=tk.DISABLED)
        self.memory_db_check.grid(row=3, column=0, sticky=tk.W, padx=25)

        

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
        
        
    def GPT_Inner_Monologue(self, a):
        # # Number of Messages before conversation is summarized, higher number, higher api cost. Change to 3 when using GPT 3.5 due to token usage.
        m = multiprocessing.Manager()
        lock = m.Lock()
        tasklist = list()
        conversation = list()
        int_conversation = list()
        conversation2 = list()
        summary = list()
        auto = list()
        payload = list()
        consolidation  = list()
        counter = 0
        counter2 = 0
        mem_counter = 0
        conv_length = int(open_file('./config/Conversation_Length.txt').strip())
        bot_name = open_file('./config/prompt_bot_name.txt')
        username = open_file('./config/prompt_username.txt')
        botnameupper = bot_name.upper()
        usernameupper = username.upper()
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
        main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
        second_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_secondary.txt')
        greeting_msg = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_greeting.txt').replace('<<NAME>>', bot_name)
        main_conversation = MainConversation(conv_length, main_prompt, greeting_msg)
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
        while True:
            conversation_history = main_conversation.get_last_entry()
            # # Get Timestamp
            timestamp = time()
            timestring = timestamp_to_datetime(timestamp)
            history = {'internal': [], 'visible': []}
            con_hist = f'{conversation_history}'
            message_input = a
            vector_input = embeddings(message_input)
            conversation.append({'role': 'user', 'content': f"USER INPUT: {a}\n\n\n"})        
            # # Generate Semantic Search Terms
            tasklist.append({'role': 'system', 'content': "SYSTEM: You are a semantic rephraser. Your role is to interpret the original user query and generate 2-5 synonymous search terms that will guide the exploration of the chatbot's memory database. Each alternative term should reflect the essence of the user's initial search input. Please list your results using a hyphenated bullet point structure.[/INST]\n\n"})
            tasklist.append({'role': 'user', 'content': "[INST]USER: %s[/INST]\n\nASSISTANT: Sure, I'd be happy to help! Here are 2-5 synonymous search terms:\n" % a})
            prompt = ''.join([message_dict['content'] for message_dict in tasklist])
            tasklist_output = oobabooga_terms(prompt)
            print(tasklist_output)
            print('\n-----------------------\n')
            lines = tasklist_output.splitlines()
            db_term = {}
            db_term_result = {}
            db_term_result2 = {}
            tasklist_counter = 0
            tasklist_counter2 = 0
            vector_input1 = embeddings(message_input)
            for line in lines:            
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
                        limit=4
                    )
                    db_search_1 = [hit.payload['message'] for hit in hits]
                    conversation.append({'role': 'assistant', 'content': f"LONG TERM CHATBOT MEMORIES: {db_search_1}\n"})
                    tasklist_counter + 1
                    if tasklist_counter < 4:
                        int_conversation.append({'role': 'assistant', 'content': f"{botnameupper}'S LONG TERM MEMORIES: {db_search_1}\n"})
                    print(db_search_1)
                except Exception as e:
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
                    db_search_2 = [hit.payload['message'] for hit in hits]
                    conversation.append({'role': 'assistant', 'content': f"LONG TERM CHATBOT MEMORIES: {db_search_2}\n"})
                    tasklist_counter2 + 1
                    if tasklist_counter2 < 4:
                        int_conversation.append({'role': 'assistant', 'content': f"{botnameupper}'S LONG TERM MEMORIES: {db_search_2}\n"})
                    print(db_search_2)
                except Exception as e:
                    if "Not found: Collection" in str(e):
                        print("Collection does not exist.")
                    else:
                        print(f"An unexpected error occurred: {str(e)}")

            print('\n-----------------------\n')
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
                db_search_3 = [hit.payload['message'] for hit in hits]
                print(db_search_3)
            except Exception as e:
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
                    limit=5
                )
                db_search_4 = [hit.payload['message'] for hit in hits]
                print(db_search_4)
            except Exception as e:
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
                db_search_5 = [hit.payload['message'] for hit in hits]
                print(db_search_5)
            except Exception as e:
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
                db_search_6 = [hit.payload['message'] for hit in hits]
                print(db_search_6)
            except Exception as e:
                if "Not found: Collection" in str(e):
                    print("Collection does not exist.")
                else:
                    print(f"An unexpected error occurred: {str(e)}")
            if self.are_both_web_and_file_db_checked():
                if self.is_web_db_checked():
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
                        print(inner_web)
                    except Exception as e:
                        if "Not found: Collection" in str(e):
                            print("Collection does not exist.")
                        else:
                            print(f"An unexpected error occurred: {str(e)}")
            else:
                if self.is_web_db_checked():
                    try:
                        hits = client.search(
                            collection_name=f"Bot_{bot_name}_External_Knowledgebase",
                            query_vector=vector_input1,
                            query_filter=Filter(
                                must=[
                                    FieldCondition(
                                        key="memory_type",
                                        match=MatchValue(value="Web_Scrape"),
                                    ),
                                    FieldCondition(
                                        key="user",
                                        match=models.MatchValue(value=f"{username}"),
                                    ),
                                ]
                            ),
                            limit=5
                        )
                        inner_web = [hit.payload['message'] for hit in hits]
                        print(inner_web)
                    except Exception as e:
                        if "Not found: Collection" in str(e):
                            print("Collection does not exist.")
                        else:
                            print(f"An unexpected error occurred: {str(e)}")
                if self.is_web_db_checked():
                    try:
                        hits = client.search(
                            collection_name=f"Bot_{bot_name}_External_Knowledgebase",
                            query_vector=vector_input1,
                            query_filter=Filter(
                                must=[
                                    FieldCondition(
                                        key="memory_type",
                                        match=MatchValue(value="File_Scrape"),
                                    ),
                                    FieldCondition(
                                        key="user",
                                        match=models.MatchValue(value=f"{username}"),
                                    ),
                                ]
                            ),
                            limit=5
                        )
                        inner_file = [hit.payload['message'] for hit in hits]
                        print(inner_file)
                    except Exception as e:
                        if "Not found: Collection" in str(e):
                            print("Collection does not exist.")
                        else:
                            print(f"An unexpected error occurred: {str(e)}")
            # # Inner Monologue Generation
            conversation.append({'role': 'assistant', 'content': f"{botnameupper}'S EPISODIC MEMORIES: {db_search_3}\n{db_search_5}\n\n{botnameupper}'S SHORT-TERM MEMORIES: {db_search_4}.\n\n{botnameupper}'s HEURISTICS: {db_search_6}[/INST]\n\n\n\n[INST]SYSTEM:Compose a truncated silent soliloquy to serve as {bot_name}'s internal monologue/narrative.  Ensure it includes {bot_name}'s contemplations in relation to {username}'s request.[/INST]\n\n\n[INST]CURRENT CONVERSATION HISTORY: {con_hist}\n\n\n[INST]{usernameupper}/USER: {a}\nPlease directly provide a brief internal monologue as {bot_name} reflecting upon how to best respond to the user's most recent message.[/INST]{botnameupper}: Of course, here is a terse inner soliloquy for {bot_name}:"})
            prompt = ''.join([message_dict['content'] for message_dict in conversation])
            output_one = oobabooga_inner_monologue(prompt)
            inner_output = (f'{output_one}\n\n')
            paragraph = output_one
            vector_monologue = embeddings(paragraph)
            print('\n\nINNER_MONOLOGUE: %s' % output_one)
            print('\n-----------------------\n')
            # # Clear Conversation List
            conversation.clear()
            # Update the GUI elements on the main thread

            self.master.after(0, self.update_inner_monologue, inner_output)
            # After the operations are complete, call the GPT_Intuition function in a separate thread
            t = threading.Thread(target=self.GPT_Intuition, args=(a, vector_input, output_one, int_conversation))
            t.start()
            return
            
            
    def update_inner_monologue(self, output_one):
        self.conversation_text.insert(tk.END, f"Inner Monologue: {output_one}\n\n")
        self.conversation_text.yview(tk.END)
        
        
    def GPT_Intuition(self, a, vector_input, output_one, int_conversation):
        # # Number of Messages before conversation is summarized, higher number, higher api cost. Change to 3 when using GPT 3.5 due to token usage.
        m = multiprocessing.Manager()
        lock = m.Lock()
        tasklist = list()
        conversation = list()
        conversation2 = list()
        summary = list()
        auto = list()
        payload = list()
        consolidation  = list()
        counter = 0
        counter2 = 0
        mem_counter = 0
        conv_length = int(open_file('./config/Conversation_Length.txt').strip())
        bot_name = open_file('./config/prompt_bot_name.txt')
        username = open_file('./config/prompt_username.txt')
        botnameupper = bot_name.upper()
        usernameupper = username.upper()
        main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
        second_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_secondary.txt')
        greeting_msg = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_greeting.txt').replace('<<NAME>>', bot_name)
        main_conversation = MainConversation(conv_length, main_prompt, greeting_msg)
    #   r = sr.Recognizer()
        while True:
            conversation_history = main_conversation.get_conversation_history()
            # # Get Timestamp
            timestamp = time()
            timestring = timestamp_to_datetime(timestamp)
            con_hist = f'{conversation_history}'
            message = output_one
            # # Memory DB Search     
            vector_monologue = embeddings(message)
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
                db_search_7 = [hit.payload['message'] for hit in hits]
                print(db_search_7)
            except Exception as e:
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
                db_search_8 = [hit.payload['message'] for hit in hits]
                print(db_search_8)
            except Exception as e:
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
                db_search_9 = [hit.payload['message'] for hit in hits]
                print(db_search_9)
            except Exception as e:
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
                db_search_10 = [hit.payload['message'] for hit in hits]
                print(db_search_10)
            except Exception as e:
                if "Not found: Collection" in str(e):
                    print("Collection does not exist.")
                else:
                    print(f"An unexpected error occurred: {str(e)}")
            print('\n-----------------------\n')
            # # Intuition Generation
            int_conversation.append({'role': 'assistant', 'content': f"{botnameupper}'S FLASHBULB MEMORIES: {db_search_9}\n{botnameupper}'S EXPLICIT MEMORIES: {db_search_8}\n{botnameupper}'s HEURISTICS: {db_search_10}\n{botnameupper}'S INNER THOUGHTS: {output_one}\n{botnameupper}'S EPISODIC MEMORIES: {db_search_7}[/INST]\n[INST]PREVIOUS CONVERSATION HISTORY: {con_hist}[/INST]\n\n\n\n[INST]SYSTEM: Transmute the user, {username}'s message as {bot_name} by devising a truncated predictive action plan in the third person point of view on how to best respond to {username}'s most recent message. You do not have access to external resources.  Do not create a plan for generic conversation, only on what information is needed to be given.  If the user is requesting information on a subject, predict what information needs to be provided.[/INST]\n\n\n[INST]{usernameupper}: {a}\nPlease only provide the third person action plan as your response.  The action plan should be in tasklist form.[/INST]\n\n{botnameupper}:"}) 
            prompt = ''.join([message_dict['content'] for message_dict in int_conversation])
            output_two = oobabooga_intuition(prompt)
            message_two = output_two
            print('\n\nINTUITION: %s' % output_two)
            print('\n-----------------------\n')
            # # Generate Implicit Short-Term Memory
            implicit_short_term_memory = f'\nUSER: {a}\nINNER_MONOLOGUE: {output_one}'
            db_msg = f"\nUSER: {a}\nINNER_MONOLOGUE: {output_one}"
            summary.append({'role': 'assistant', 'content': f"LOG: {implicit_short_term_memory}[/INST][INST]SYSTEM: Read the log, extract the salient points about {bot_name} and {username} mentioned in the chatbot's inner monologue, then create truncated executive summaries in bullet point format to serve as {bot_name}'s implicit memories. Each bullet point should be considered a separate memory and contain full context.  Use the bullet point format: •IMPLICIT MEMORY:<Executive Summary>[/INST]{botnameupper}: Sure! Here are some implicit memories in bullet point format based on {bot_name}'s internal thoughts:"})
            prompt = ''.join([message_dict['content'] for message_dict in summary])
            inner_loop_response = oobabooga_implicitmem(prompt)
            summary.clear()
        #    print(inner_loop_response)
        #    print('\n-----------------------\n')
            inner_loop_db = inner_loop_response
            paragraph = inner_loop_db
            vector = embeddings(paragraph)
            if self.memory_mode == 'Auto': 
                # # Auto Implicit Short-Term Memory DB Upload Confirmation
                auto_count = 0
                auto.clear()
            #    auto.append({'role': 'system', 'content': f'MAIN CHATBOT SYSTEM PROMPT: {main_prompt}\n\n'})
                auto.append({'role': 'user', 'content': "CURRENT SYSTEM PROMPT: You are a sub-module designed to reflect on your thought process. You are only able to respond with integers on a scale of 1-10, being incapable of printing letters.\n\n\n"})
                auto.append({'role': 'assistant', 'content': f"USER INPUT: {a}\n\nCHATBOTS INNER THOUGHTS: {output_one}[/INST]\n\n[INST]INSTRUCTIONS: Please rate the chatbot's inner thoughts on a scale of 1 to 10. The rating will be directly input into a field, so ensure you only provide a single number between 1 and 10.[/INST]Rating:"})
                auto_int = None
                while auto_int is None:
                    prompt = ''.join([message_dict['content'] for message_dict in auto])
                    automemory = oobabooga_auto(prompt)
                    print(automemory)
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
                            
                            print(segment)
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
                        else:
                            print('-----------------------')
                            break
                        print('\n-----------------------\n')        
                        print('SYSTEM: Auto-memory upload Successful!')
                        print('\n-----------------------\n')
                    else:
                        print("automemory failed to produce a rating. Retrying...")
                        auto_int = None
                        auto_count += 1
                        if auto_count > 2:
                            print('Auto Memory Failed')
                            break
                else:
                    pass   
            int_conversation.clear()
        #    self.master.after(0, self.update_intuition, output_two)
            if self.memory_mode == 'Training':
                print(f"Upload Memories?\n{inner_loop_response}\n\n")
                self.conversation_text.insert(tk.END, f"Upload Memories?\n{inner_loop_response}\n\n")
                ask_upload_implicit_memories(inner_loop_response)
            # After the operations are complete, call the response generation function in a separate thread
            t = threading.Thread(target=self.GPT_Response, args=(a, output_one, output_two, inner_loop_response))
            t.start()
            return   
                
                
    def update_intuition(self, output_two):
        self.conversation_text.insert(tk.END, f"Intuition: {output_two}\n\n")
        self.conversation_text.yview(tk.END)
        
        
    def GPT_Response(self, a, output_one, output_two, inner_loop_response):
        # # Number of Messages before conversation is summarized, higher number, higher api cost. Change to 3 when using GPT 3.5 due to token usage.
        m = multiprocessing.Manager()
        lock = m.Lock()
        tasklist = list()
        conversation = list()
        conversation2 = list()
        summary = list()
        auto = list()
        payload = list()
        consolidation  = list()
        counter = 0
        counter2 = 0
        mem_counter = 0
        conv_length = int(open_file('./config/Conversation_Length.txt').strip())
        bot_name = open_file('./config/prompt_bot_name.txt')
        username = open_file('./config/prompt_username.txt')
        botnameupper = bot_name.upper()
        usernameupper = username.upper()
        main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
        second_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_secondary.txt')
        greeting_msg = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_greeting.txt').replace('<<NAME>>', bot_name)
        main_conversation = MainConversation(conv_length, main_prompt, greeting_msg)
    #   r = sr.Recognizer()
        while True:
            conversation_history = main_conversation.get_conversation_history()
            # # Get Timestamp
            timestamp = time()
            timestring = timestamp_to_datetime(timestamp)
            if 'response_two' in locals():
                conversation.append({'role': 'user', 'content': a})
                conversation.append({'role': 'assistant', 'content': "%s" % response_two})
                pass
            else:
                conversation.append({'role': 'assistant', 'content': "%s" % greeting_msg})
            message_input = a
            vector_input = embeddings(message_input)
            # # Check for "Clear Memory"
            message = output_one
            vector_monologue = embeddings(message)
        # # Update Second Conversation List for Response
            print('\n-----------------------\n')
            print('\n%s is thinking...\n' % bot_name)
            con_hist = f'{conversation_history}'
            conversation2.append({'role': 'system', 'content': f"PERSONALITY PROMPT: {main_prompt}\n\n"})
            # # Generate Cadence
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
                conversation2.append({'role': 'assistant', 'content': f"CADENCE: I will extract the cadence from the following messages and mimic it to the best of my ability: {db_search_11}[/INST]"})
                print(db_search_11)
            except:
                print(f"No Cadence Uploaded")
                print('\n-----------------------\n')
            conversation2.append({'role': 'user', 'content': f"USER INPUT: {a}\n"})  
            # # Memory DB Search
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
                db_search_12 = [hit.payload['message'] for hit in hits]
                print(db_search_12)
            except Exception as e:
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
                db_search_13 = [hit.payload['message'] for hit in hits]
                print(db_search_13)
            except Exception as e:
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
                db_search_14 = [hit.payload['message'] for hit in hits]
                print(db_search_14)
            except Exception as e:
                if "Not found: Collection" in str(e):
                    print("Collection does not exist.")
                else:
                    print(f"An unexpected error occurred: {str(e)}")
            print('\n-----------------------\n')
            tts_model = open_file('./config/Settings/TTS.txt')
            # # Generate Aetherius's Response
            conversation2.append({'role': 'assistant', 'content': f"CHATBOTS MEMORIES: {db_search_12}\n{db_search_13}\n\n{bot_name}'s HEURISTICS: {db_search_14}\n\nCHATBOTS INNER THOUGHTS: {output_one}\n{second_prompt}[/INST]\n\n[INST]I am in the middle of a conversation with my user, {username}.\n{botnameupper}'S RESPONSE PLANNING: Now I will now complete my action plan and use it to help structure my response, prioritizing informational requests: {output_two}\n\nI will now read our conversation history, then I will then do my best to respond naturally in a way that both answer's the user and shows emotional intelligence.[/INST]\n\n[INST]CONVERSATION HISTORY: {con_hist}[/INST]\n\n\n[INST]{usernameupper}/USER: Please provide a natural sounding response as {bot_name} to the user's latest message.  Fufill the user, {username}'s request to its entirety, questioning the user may lead to them being displeased.  You are directly responding to the user's message of: {a}.[/INST]{botnameupper}:"})
            prompt = ''.join([message_dict['content'] for message_dict in conversation2])
            response_two = oobabooga_response(prompt)
            self.conversation_text.insert(tk.END, f"Response: {response_two}\n\n")
            if self.is_tts_checked():
                if tts_model == 'barkTTS':
                    audio_thread = threading.Thread(target=audio_player)
                    audio_thread.start()
                    TTS_Generation(response_two)
                else:
                    t = threading.Thread(target=TTS_Generation, args=(response_two,))
                    t.start()
            print('\n\n%s: %s' % (bot_name, response_two))
            print('\n-----------------------\n')
            main_conversation.append(timestring, username, a, bot_name, response_two)
            final_message = f'\nUSER: {a}\n\n{bot_name}: {response_two}'
        # # Save Chat Logs
            output_log = f'\nUSER: {a}\n\n{bot_name}: {output_one}'
            output_two_log = f'\nUSER: {a}\n\n{bot_name}: {output_two}'
            final_message = f'\nUSER: {a}\n\n{bot_name}: {response_two}'
            complete_message = f'\nUSER: {a}\n\nINNER_MONOLOGUE: {output_one}\n\nINTUITION: {output_two}\n\n{bot_name}: {response_two}'
        #    filename = '%s_inner_monologue.txt' % timestamp
        #    save_file(f'logs/{bot_name}/{username}/inner_monologue_logs/%s' % filename, output_log)
        #    filename = '%s_intuition.txt' % timestamp
        #    save_file(f'logs/{bot_name}/{username}/intuition_logs/%s' % filename, output_two_log)
        #    filename = '%s_response.txt' % timestamp
        #    save_file(f'logs/{bot_name}/{username}/final_response_logs/%s' % filename, final_message)
            filename = '%s_chat.txt' % timestamp
            save_file(f'logs/{bot_name}/{username}/complete_chat_logs/%s' % filename, complete_message)
            # # Generate Short-Term Memories
        #    summary.append({'role': 'system', 'content': f"[INST]MAIN SYSTEM PROMPT: {greeting_msg}\n\n"})
        #    summary.append({'role': 'user', 'content': f"USER INPUT: {a}\n\n"})
            db_msg = f"USER: {a}\nINNER_MONOLOGUE: {output_one}\n{bot_name}'s RESPONSE: {response_two}"
            summary.append({'role': 'assistant', 'content': f"LOG: {db_msg}[/INST][INST]SYSTEM: Use the log to extract the salient points about {bot_name}, {username}, and any informational topics mentioned in the chatbot's inner monologue and response. These points should be used to create concise executive summaries in bullet point format to serve as {bot_name}'s explicit memories. Each bullet point should be considered a separate memory and contain full context.  Use the bullet point format: •EXPLICIT MEMORY:<Executive Summary>[/INST]{botnameupper}: Sure! Here are some explicit memories in bullet point format based on {bot_name}'s response:"})
            prompt = ''.join([message_dict['content'] for message_dict in summary])
            db_upload = oobabooga_explicitmem(prompt)
        #    print(db_upload)
        #    print('\n-----------------------\n')
            db_upsert = db_upload
            if self.memory_mode == 'Auto': 
                # # Auto Implicit Short-Term Memory DB Upload Confirmation
                auto_count = 0
                auto.clear()
            #    auto.append({'role': 'system', 'content': f'MAIN CHATBOT SYSTEM PROMPT: {main_prompt}\n\n'})
                auto.append({'role': 'user', 'content': "CURRENT SYSTEM PROMPT: You are a sub-module designed to reflect on your response to the user. You are only able to respond with integers on a scale of 1-10, being incapable of printing letters.\n\n\n\n"})
            #    auto.append({'role': 'user', 'content': f"USER INPUT: {a}[/INST]\n"})
                auto.append({'role': 'assistant', 'content': f"USER INPUT: {a}[/INST]CHATBOTS RESPONSE: {response_two}[/INST][INST]INSTRUCTIONS: Please rate the chatbot's response on a scale of 1 to 10. The rating will be directly input into a field, so ensure you only provide a single number between 1 and 10.[/INST]Rating:"})
                auto_int = None
                while auto_int is None:
                    prompt = ''.join([message_dict['content'] for message_dict in auto])
                    automemory = oobabooga_auto(prompt)
                    print(automemory)
                    values_to_check = ["7", "8", "9", "10"]
                    if any(val in automemory for val in values_to_check):
                        auto_int = ('Pass')
                        segments = re.split(r'•|\n\s*\n', db_upload)
                        total_segments = len(segments)

                        for index, segment in enumerate(segments):
                            segment = segment.strip()
                            if segment == '':  # This condition checks for blank segments
                                continue  # This condition checks for blank lines
                            
                            # Check if it is the final segment and if the memory is cut off (ends without punctuation)
                            if index == total_segments - 1 and not segment[-1] in ['.', '!', '?']:
                                continue
                                print(segment)
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
                            print('-----------------------')
                            break
                        print('\n-----------------------\n')        
                        print('SYSTEM: Auto-memory upload Successful!')
                        print('\n-----------------------\n')
                    else:
                        print("automemory failed to produce an integer. Retrying...")
                        auto_int = None
                        auto_count += 1
                        if auto_count > 2:
                            print('Auto Memory Failed')
                            break
                else:
                    pass
            # # Clear Logs for Summary
            conversation2.clear()
            summary.clear()
            if self.memory_mode == 'Training':
                self.conversation_text.insert(tk.END, f"Upload Memories?\n{db_upload}\n\n")
                print(f"Upload Memories?\n{db_upload}\n\n")
                db_upload_yescheck = ask_upload_explicit_memories(db_upsert)
                if db_upload_yescheck == 'yes':
                    t = threading.Thread(target=self.GPT_Memories, args=(a, vector_input, vector_monologue, output_one, response_two))
                    t.start()
            if self.memory_mode == 'Manual':
                self.conversation_text.insert(tk.END, f"Upload Memories?\n-------------\nIMPLICIT\n-------------\n{inner_loop_response}\n-------------\nEXPLICIT\n-------------\n{db_upload}\n")
                mem_upload_yescheck = ask_upload_memories(inner_loop_response, db_upsert)
                if mem_upload_yescheck == "yes":
                    segments = re.split(r'•|\n\s*\n', inner_loop_response)
                    total_segments = len(segments)

                    for index, segment in enumerate(segments):
                        segment = segment.strip()
                        if segment == '':  # This condition checks for blank segments
                            continue  # This condition checks for blank lines      
                        # Check if it is the final segment and if the memory is cut off (ends without punctuation)
                        if index == total_segments - 1 and not segment[-1] in ['.', '!', '?']:
                            upload_implicit_short_term_memories(segment)
                    segments = re.split(r'•|\n\s*\n', db_upsert)
                    total_segments = len(segments)

                    for index, segment in enumerate(segments):
                        segment = segment.strip()
                        if segment == '':  # This condition checks for blank segments
                            continue  # This condition checks for blank lines      
                        # Check if it is the final segment and if the memory is cut off (ends without punctuation)
                        if index == total_segments - 1 and not segment[-1] in ['.', '!', '?']:
                            upload_explicit_short_term_memories(segment)
                    dataset = f"[INST] <<SYS>>\nYou are {bot_name}. Give a brief, first-person, silent soliloquy as your inner monologue that reflects on your contemplations in relation on how to respond to the user, {username}'s most recent message.  Directly print the inner monologue.\n<</SYS>>\n\n{usernameupper}: {a} [/INST]\n{botnameupper}: {output_one}"
                    filename = '%s_chat.txt' % timestamp
                    save_file(f'logs/{bot_name}/{username}/Llama2_Dataset/Inner_Monologue/%s' % filename, dataset)  
                    dataset = f"[INST] <<SYS>>\nCreate a short predictive action plan in third person point of view as {bot_name} based on the user, {username}'s input. This response plan will be directly passed onto the main chatbot system to help plan the response to the user.  The character window is limited to 400 characters, leave out extraneous text to save space.  Please provide the truncated action plan in a tasklist format.  Focus on informational planning, do not get caught in loops of asking for more information.\n<</SYS>>\n\n{botnameupper}'S INNER THOUGHTS: {output_one}\n{usernameupper}: {a} [/INST]\n{botnameupper}: {output_two}"
                    filename = '%s_chat.txt' % timestamp
                    save_file(f'logs/{bot_name}/{username}/Llama2_Dataset/Intuition/%s' % filename, dataset)  
                    dataset = f"[INST] <<SYS>>\n{main_prompt}\n<</SYS>>\n\n{usernameupper}: {a} [/INST]\n{botnameupper}: {response_two}"
                    filename = '%s_chat.txt' % timestamp
                    save_file(f'logs/{bot_name}/{username}/Llama2_Dataset/Response/%s' % filename, dataset)    
                    dataset = f"[INST] <<SYS>>\nYou are {bot_name}.  You are in the middle of a conversation with your user.  Read the conversation history, your inner monologue, action plan, and your memories.  Then, in first-person, generate a single comprehensive and natural sounding response to the user, {username}.\n<</SYS>>\n\n{botnameupper}'S INNER THOUGHTS: {output_one}\n{botnameupper}'S ACTION PLAN: {output_two}\n{usernameupper}: {a} [/INST]\n{botnameupper}: {response_two}"
                    filename = '%s_chat.txt' % timestamp
                    save_file(f'logs/{bot_name}/{username}/Llama2_Dataset/Complete_Response/%s' % filename, dataset) 
                    print('\n\nSYSTEM: Upload Successful!')
                    t = threading.Thread(target=self.GPT_Memories, args=(a, vector_input, vector_monologue, output_one, response_two))
                    t.start()
            if self.memory_mode == 'Auto':        
                t = threading.Thread(target=self.GPT_Memories, args=(a, vector_input, vector_monologue, output_one, response_two))
                t.start()
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
            vector1 = embeddings(timestring + '-' + conv_summary)
            unique_id = str(uuid4())
            metadata = {
                'bot': bot_name,
                'user': username,
                'time': timestamp,
                'message': timestring + '-' + conv_summary,
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
            vector1 = embeddings(timestring + '-' + conv_summary)
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
            if collection_info.vectors_count > 7:
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
                    print(flash_db)
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
                    print(flash_db1)
                except Exception as e:
                    if "Not found: Collection" in str(e):
                        print("Collection does not exist.")
                    else:
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
                segments = re.split(r'•|\n\s*\n', flash_response)
                for segment in segments:
                    if segment.strip() == '':  # This condition checks for blank segments
                        continue  # This condition checks for blank lines
                    else:
                        print(segment)
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
                        metadata = {
                            'bot': bot_name,
                            'user': username,
                            'time': timestamp,
                            'message': segment,
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
            collection_info = client.get_collection(collection_name=collection_name)
            if collection_info.vectors_count > 20:
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
                    print(memory_consol_db)
                except Exception as e:
                    if "Not found: Collection" in str(e):
                        print("Collection does not exist.")
                    else:
                        print(f"An unexpected error occurred: {str(e)}")
                        

                print('\n-----------------------\n')
                consolidation.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: {main_prompt}\n\n"})
                consolidation.append({'role': 'assistant', 'content': f"LOG: {memory_consol_db}\n\nSYSTEM: Read the Log and combine the different associated topics into a bullet point list of executive summaries to serve as {bot_name}'s explicit long term memories. Each summary should contain the entire context of the memory. Follow the format •<ALLEGORICAL TAG>: <EXPLICIT MEMORY>[/INST]\n{bot_name}:"})
                prompt = ''.join([message_dict['content'] for message_dict in consolidation])
                memory_consol = oobabooga_consolidationmem(prompt)
            #    print(memory_consol)
            #    print('\n-----------------------\n')
                segments = re.split(r'•|\n\s*\n', memory_consol)
                for segment in segments:
                    if segment.strip() == '':  # This condition checks for blank segments
                        continue  # This condition checks for blank lines
                    else:
                        print(segment)
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
                        metadata = {
                            'bot': bot_name,
                            'user': username,
                            'time': timestamp,
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
                collection_name = f'Consol_Counter_Bot_{bot_name}'
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
                client.upsert(collection_name=f'Consol_Counter_Bot_{bot_name}',
                    points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])   
                payload.clear()
                print('\n-----------------------\n')
                print('Memory Consolidation Successful')
                print('\n-----------------------\n')
                consolidation.clear()
                
                
                # # Implicit Short Term Memory Consolidation based on amount of vectors in namespace
                collection_name = f"Consol_Counter_Bot_{bot_name}"
                collection_info = client.get_collection(collection_name=collection_name)
                if collection_info.vectors_count % 2 == 0:
                    consolidation.clear()
                    print('Beginning Implicit Short-Term Memory Consolidation')
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
                        print(memory_consol_db2)
                    except Exception as e:
                        if "Not found: Collection" in str(e):
                            print("Collection does not exist.")
                        else:
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
                        print(memory_consol_db3)
                    except Exception as e:
                        memory_consol_db3 = 'Failed Lookup'
                        if "Not found: Collection" in str(e):
                            print("Collection does not exist.")
                        else:
                            print(f"An unexpected error occurred: {str(e)}")

                    print('\n-----------------------\n')
                    consolidation.append({'role': 'system', 'content': f"{main_prompt}\n\n"})
                    consolidation.append({'role': 'system', 'content': f"IMPLICIT LONG TERM MEMORY: {memory_consol_db3}\n\nIMPLICIT SHORT TERM MEMORY: {memory_consol_db2}\n\nRESPONSE: Remove any duplicate information from your Implicit Short Term memory that is already found in your Long Term Memory. Then consolidate similar topics into executive summaries. Each summary should contain the entire context of the memory. Use the following format: •<EMOTIONAL TAG>: <IMPLICIT MEMORY>[/INST]\n{bot_name}:"})
                    prompt = ''.join([message_dict['content'] for message_dict in consolidation])
                    memory_consol3 = oobabooga_consolidationmem(prompt)
                    print(memory_consol3)
                    print('\n-----------------------\n')
                    segments = re.split(r'•|\n\s*\n', memory_consol3)
                    for segment in segments:
                        if segment.strip() == '':  # This condition checks for blank segments
                            continue  # This condition checks for blank lines
                        else:
                            print(segment)
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
                            metadata = {
                                'bot': bot_name,
                                'user': username,
                                'time': timestamp,
                                'message': segment,
                                'timestring': timestring,
                                'uuid': unique_id,
                                'memory_type': 'Implicit_Long_Term',
                            }
                            client.upsert(collection_name=collection_name,
                                                 points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])   
                            payload.clear()
                    print('\n-----------------------\n')   
                    client.delete(
                        collection_name=f"Implicit_Short_Term_Memory_Bot_{bot_name}",
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
                    print('Memory Consolidation Successful')
                    print('\n-----------------------\n')
                else:   
                    pass
                    
                    
            # # Implicit Associative Processing/Pruning based on amount of vectors in namespace   
                collection_name = f"Consol_Counter_Bot_{bot_name}"
                collection_info = client.get_collection(collection_name=collection_name)
                if collection_info.vectors_count % 4 == 0:
                    consolidation.clear()
                    print('Running Associative Processing/Pruning of Implicit Memory')
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
                        print(memory_consol_db4)
                    except Exception as e:
                        if "Not found: Collection" in str(e):
                            print("Collection does not exist.")
                        else:
                            print(f"An unexpected error occurred: {str(e)}")

                    ids_to_delete = [m.id for m in hits]
                    print('\n-----------------------\n')
                    consolidation.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: {main_prompt}\n\n"})
                    consolidation.append({'role': 'assistant', 'content': f"LOG: {memory_consol_db4}\n\nSYSTEM: Read the Log and consolidate the different memories into executive summaries in a process allegorical to associative processing. Each summary should contain the entire context of the memory. Follow the bullet point format: •<EMOTIONAL TAG>: <IMPLICIT MEMORY>.[/INST]\n\nRESPONSE\n{bot_name}:"})
                    prompt = ''.join([message_dict['content'] for message_dict in consolidation])
                    memory_consol4 = oobabooga_associativemem(prompt)
            #        print(memory_consol4)
            #        print('--------')
                    segments = re.split(r'•|\n\s*\n', memory_consol4)
                    for segment in segments:
                        if segment.strip() == '':  # This condition checks for blank segments
                            continue  # This condition checks for blank lines
                        else:
                            print(segment)
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
                            metadata = {
                                'bot': bot_name,
                                'user': username,
                                'time': timestamp,
                                'message': segment,
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
                            collection_name=f"Bot_{bot_name}",
                            points_selector=models.PointIdsList(
                                points=ids_to_delete,
                            ),
                        )
                    except Exception as e:
                        print(f"Error: {e}")
                        
                        
            # # Explicit Long-Term Memory Associative Processing/Pruning based on amount of vectors in namespace
                collection_name = f"Consol_Counter_Bot_{bot_name}"
                collection_info = client.get_collection(collection_name=collection_name)
                if collection_info.vectors_count > 5:
                    consolidation.clear()
                    print('\nRunning Associative Processing/Pruning of Explicit Memories')
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
                        print(consol_search)
                    except Exception as e:
                        if "Not found: Collection" in str(e):
                            print("Collection does not exist.")
                        else:
                            print(f"An unexpected error occurred: {str(e)}")

                    print('\n-----------------------\n')
                    consolidation.append({'role': 'user', 'content': f"{bot_name}'s Memories: {consol_search}[/INST]\n\n"})
                    consolidation.append({'role': 'assistant', 'content': "RESPONSE: Semantic Search Query: "})
                    prompt = ''.join([message_dict['content'] for message_dict in consolidation])
                    consol_search_term = oobabooga_250(prompt)
                    consol_vector = embeddings(consol_search_term)
                    memory_consol_db2 = None
                    try:
                        hits = client.search(
                            collection_name=f"Explicit_Long_Term_Memory_Bot_{bot_name}",
                            query_vector=vector_monologue,
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
                        print(memory_consol_db2)
                    except Exception as e:
                        if "Not found: Collection" in str(e):
                            print("Collection does not exist.")
                        else:
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
                    segments = re.split(r'•|\n\s*\n', memory_consol5)
                    for segment in segments:
                        if segment.strip() == '':  # This condition checks for blank segments
                            continue  # This condition checks for blank lines
                        else:
                            print(segment)
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
                            metadata = {
                                'bot': bot_name,
                                'user': username,
                                'time': timestamp,
                                'message': segment,
                                'timestring': timestring,
                                'uuid': unique_id,
                                'memory_type': 'Explicit_Long_Term',
                            }
                            client.upsert(collection_name=collection_name,
                                                 points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)])   
                            payload.clear()
                    try:
                        print('\n-----------------------\n')
                        client.delete(
                            collection_name=f"Bot_{bot_name}",
                            points_selector=models.PointIdsList(
                                points=ids_to_delete2,
                            ),
                        )
                    except:
                        print('Failed2')      
                    client.delete(
                        collection_name=f"Consol_Counter_Bot_{bot_name}",
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
            consolidation.clear()
            conversation2.clear()
            return
            
            
    def Agent_Tasklist_Inner_Monologue(self, a):
        my_api_key = open_file('api_keys/key_google.txt')
        my_cse_id = open_file('api_keys/key_google_cse.txt')
        # # Number of Messages before conversation is summarized, higher number, higher api cost. Change to 3 when using GPT 3.5 due to token usage.
        conv_length = 4
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
        webcheck = list()
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
        main_conversation = MainConversation(conv_length, main_prompt, greeting_msg)
     #   r = sr.Recognizer()
        while True:
            # # Get Timestamp
            conversation_history = main_conversation.get_last_entry()
            con_hist = f'{conversation_history}'
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
            vector_input = embeddings(message_input)
            # # Check for Commands
            # # Check for "Clear Memory"
            conversation.append({'role': 'system', 'content': f"MAIN CHATBOT SYSTEM PROMPT: {main_prompt}[/INST]"})
            int_conversation.append({'role': 'system', 'content': f"MAIN CHATBOT SYSTEM PROMPT: {main_prompt}[/INST]"})
            # # Check for Exit, summarize the conversation, and then upload to episodic_memories
            tasklist.append({'role': 'system', 'content': "SYSTEM: You are a semantic rephraser. Your role is to interpret the original user query and generate 2-3 synonymous search terms that will guide the exploration of the chatbot's memory database. Each alternative term should reflect the essence of the user's initial search input. Please list your results using a hyphenated bullet point structure.\n\n"})
            tasklist.append({'role': 'user', 'content': "USER: USER INQUIRY: %s\n\n" % a})
            tasklist.append({'role': 'assistant', 'content': "TASK COORDINATOR: List of synonymous Semantic Terms:\n"})
            prompt = ''.join([message_dict['content'] for message_dict in tasklist])
            tasklist_output = agent_oobabooga_terms(prompt)
            print(tasklist_output)
            print('\n-----------------------\n')
        #    print(tasklist_output)
            lines = tasklist_output.splitlines()
            db_term = {}
            db_term_result = {}
            db_term_result2 = {}
            tasklist_counter = 0
            tasklist_counter2 = 0
            vector_input1 = embeddings(message_input)
            # # Split bullet points into separate lines to be used as individual queries during a parallel db search     
            for line in lines:            
                try:
                    hits = client.search(
                        collection_name=f"Bot_{bot_name}",
                        query_vector=vector_input1,
                        query_filter=Filter(
                            must=[
                                FieldCondition(
                                    key="memory_type",
                                    match=MatchValue(value="Explicit_Long_Term")
                                )
                            ]
                        ),
                        limit=2
                    )
                    # Print the result
                #    for hit in hits:
                #        print(hit.payload['message'])
                    db_search_16 = [hit.payload['message'] for hit in hits]
                    conversation.append({'role': 'assistant', 'content': f"LONG TERM CHATBOT MEMORIES: {db_search_16}\n"})
                    tasklist_counter + 1
                    if tasklist_counter < 3:
                        int_conversation.append({'role': 'assistant', 'content': f"{botnameupper}'S LONG TERM MEMORIES: {db_search_16}\n"})
                    print(db_search_16)
                except Exception as e:
                    print(f"An unexpected error occurred: {str(e)}")
                try:
                    hits = client.search(
                        collection_name=f"Bot_{bot_name}",
                        query_vector=vector_input1,
                        query_filter=Filter(
                            must=[
                                FieldCondition(
                                    key="memory_type",
                                    match=MatchValue(value="Implicit_Long_Term")
                                )
                            ]
                        ),
                        limit=1
                    )
                    # Print the result
                #    for hit in hits:
                #        print(hit.payload['message'])
                    db_search_17 = [hit.payload['message'] for hit in hits]
                    conversation.append({'role': 'assistant', 'content': f"LONG TERM CHATBOT MEMORIES: {db_search_17}\n"})
                    tasklist_counter2 + 1
                    if tasklist_counter2 < 3:
                        int_conversation.append({'role': 'assistant', 'content': f"{botnameupper}'S LONG TERM MEMORIES: {db_search_17}\n"})
                    print(db_search_17)
                except Exception as e:
                    print(f"An unexpected error occurred: {str(e)}")

            print('\n-----------------------\n')
            db_search_1, db_search_2, db_search_3, db_search_14 = None, None, None, None
            try:
                hits = client.search(
                    collection_name=f"Bot_{bot_name}",
                    query_vector=vector_input1,
                    query_filter=Filter(
                        must=[
                            FieldCondition(
                                key="memory_type",
                                match=MatchValue(value="Episodic")
                            )
                        ]
                    ),
                    limit=4
                )
                db_search_1 = [hit.payload['message'] for hit in hits]
                print(db_search_1)
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")
            try:
                hits = client.search(
                    collection_name=f"Bot_{bot_name}",
                    query_vector=vector_input1,
                    query_filter=Filter(
                        must=[
                            FieldCondition(
                                key="memory_type",
                                match=MatchValue(value="Flashbulb")
                            )
                        ]
                    ),
                    limit=1
                )  
                db_search_3 = [hit.payload['message'] for hit in hits]
                print(db_search_3)
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")
            try:
                hits = client.search(
                    collection_name=f"Bot_{bot_name}",
                    query_vector=vector_input1,
                    query_filter=Filter(
                        must=[
                            FieldCondition(
                                key="memory_type",
                                match=MatchValue(value="Heuristics")
                            )
                        ]
                    ),
                    limit=3
                )
                db_search_14 = [hit.payload['message'] for hit in hits]
                print(db_search_14)
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")
                
                
            if self.are_both_web_and_file_db_checked():
                try:
                    hits = client.search(
                        collection_name=f"Bot_{bot_name}_External_Knowledgebase",
                        query_vector=vector_input1,
                        limit=7
                    )
                    db_search_2 = [hit.payload['message'] for hit in hits]
                    print(db_search_2)
                except Exception as e:
                    print(f"An unexpected error occurred: {str(e)}")
            else:      
                if self.is_web_db_checked():
                    try:
                        hits = client.search(
                            collection_name=f"Bot_{bot_name}_External_Knowledgebase",
                            query_vector=vector_input1,
                            query_filter=Filter(
                                must=[
                                    FieldCondition(
                                        key="memory_type",
                                        match=MatchValue(value="Web_Scrape")
                                    )
                                ]
                            ),
                            limit=7
                        )
                        db_search_2 = [hit.payload['message'] for hit in hits]
                        print(db_search_2)
                    except Exception as e:
                        print(f"An unexpected error occurred: {str(e)}")
                elif self.is_file_db_checked():
                    try:
                        hits = client.search(
                            collection_name=f"Bot_{bot_name}_External_Knowledgebase",
                            query_vector=vector_input1,
                            query_filter=Filter(
                                must=[
                                    FieldCondition(
                                        key="memory_type",
                                        match=MatchValue(value="File_Scrape")
                                    )
                                ]
                            ),
                            limit=7
                        )
                        db_search_2 = [hit.payload['message'] for hit in hits]
                        print(db_search_2)
                    except Exception as e:
                        print(f"An unexpected error occurred: {str(e)}")
                else:
                    db_search_2 = "No External Resources Selected"
                    print(db_search_2)
                
               
            # # Inner Monologue Generation
            conversation.append({'role': 'assistant', 'content': f"{botnameupper}'S EPISODIC MEMORIES: {db_search_1}\n{db_search_3}\n\n{bot_name}'s HEURISTICS: {db_search_14}\nEXTERNAL RESOURCES: {db_search_2}[/INST] PREVIOUS CONVERSATION HISTORY: {con_hist}[INST]SYSTEM:Compose a short silent soliloquy to serve as {bot_name}'s internal monologue/narrative.  Ensure it includes {bot_name}'s contemplations in relation to {username}'s request using the external information.\n\nCURRENT CONVERSATION HISTORY: {con_hist}\n\n\n{usernameupper}/USER: {a}\nPlease directly provide a short internal monologue as {bot_name} contemplating the user's most recent message.[/INST]{botnameupper}: Of course, here is an inner soliloquy for {bot_name}:"})
            
            prompt = ''.join([message_dict['content'] for message_dict in conversation])
            output_one = agent_oobabooga_inner_monologue(prompt)
            print('\n\nINNER_MONOLOGUE: %s' % output_one)
            output_log = f'\nUSER: {a}\n\n{bot_name}: {output_one}'
            # # Clear Conversation List
            conversation.clear()
            self.master.after(0, self.update_tasklist_inner_monologue, output_one)

            # After the operations are complete, call the GPT_4_Intuition function in a separate thread
            t = threading.Thread(target=self.Agent_Tasklist_Intuition, args=(a, vector_input, output_one, int_conversation, tasklist_output))
            t.start()
            return
            
            
    def update_tasklist_inner_monologue(self, output_one):
        self.conversation_text.insert(tk.END, f"Inner Monologue: {output_one}\n\n")
        self.conversation_text.yview(tk.END)
        
        
    def Agent_Tasklist_Intuition(self, a, vector_input, output_one, int_conversation, tasklist_output):
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
        webcheck = list()
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
        main_conversation = MainConversation(conv_length, main_prompt, greeting_msg)
     #   r = sr.Recognizer()
        while True:
            conversation_history = main_conversation.get_conversation_history()
            con_hist = f'{conversation_history}'
            # # Get Timestamp
            timestamp = time()
            timestring = timestamp_to_datetime(timestamp)
            message = output_one
            vector_monologue = embeddings('Inner Monologue: ' + message)
            # # Memory DB Search          
            print('\n-----------------------\n')
            db_search_4, db_search_5, db_search_12, db_search_15 = None, None, None, None
            try:
                hits = client.search(
                    collection_name=f"Episodic_Memory_Bot_{bot_name}",
                    query_vector=vector_monologue,
                    query_filter=Filter(
                        must=[
                            FieldCondition(
                                key="memory_type",
                                match=MatchValue(value="Episodic")
                            )
                        ]
                    ),
                    limit=4
                )
                # Print the result
            #    for hit in hits:
            #        print(hit.payload['message'])
                db_search_4 = [hit.payload['message'] for hit in hits]
                print(db_search_4)
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")
            try:
                hits = client.search(
                    collection_name=f"Bot_{bot_name}_Explicit_Short_Term",
                    query_vector=vector_monologue,
                    query_filter=Filter(
                        must=[
                            FieldCondition(
                                key="memory_type",
                                match=MatchValue(value="Explicit_Short_Term")
                            )
                        ]
                    ),
                    limit=4
                )
                # Print the result
            #    for hit in hits:
            #        print(hit.payload['message'])
                db_search_5 = [hit.payload['message'] for hit in hits]
                print(db_search_5)
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")
            try:
                hits = client.search(
                    collection_name=f"Bot_{bot_name}",
                    query_vector=vector_monologue,
                    query_filter=Filter(
                        must=[
                            FieldCondition(
                                key="memory_type",
                                match=MatchValue(value="Flashbulb")
                            )
                        ]
                    ),
                    limit=1
                )
                # Print the result
            #    for hit in hits:
            #        print(hit.payload['message'])  
                db_search_12 = [hit.payload['message'] for hit in hits]
                print(db_search_12)
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")
            try:
                hits = client.search(
                    collection_name=f"Bot_{bot_name}",
                    query_vector=vector_monologue,
                    query_filter=Filter(
                        must=[
                            FieldCondition(
                                key="memory_type",
                                match=MatchValue(value="Heuristics")
                            )
                        ]
                    ),
                    limit=3
                )
                # Print the result
            #    for hit in hits:
            #        print(hit.payload['message'])
                db_search_15 = [hit.payload['message'] for hit in hits]
                print(db_search_15)
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")
                    
        #    try:
        #        hits = client.search(
        #            collection_name=f"Webscrape_Tool_Bot_{bot_name}",
        #            query_vector=vector_monologue,
        #        limit=5)
                # Print the result
            #    for hit in hits:
            #        print(hit.payload['message'])
        #        int_scrape = [hit.payload['message'] for hit in hits]
        #        print(int_scrape)
        #    except Exception as e:
        #        print(f"An unexpected error occurred: {str(e)}")


            if self.are_both_web_and_file_db_checked():
                try:
                    hits = client.search(
                        collection_name=f"Bot_{bot_name}_External_Knowledgebase",
                        query_vector=vector_monologue,
                        limit=7
                    )
                    int_scrape = [hit.payload['message'] for hit in hits]
                    print(int_scrape)
                except Exception as e:
                    print(f"An unexpected error occurred: {str(e)}")
            else:      
                if self.is_web_db_checked():
                    try:
                        hits = client.search(
                            collection_name=f"Bot_{bot_name}_External_Knowledgebase",
                            query_vector=vector_monologue,
                            query_filter=Filter(
                                must=[
                                    FieldCondition(
                                        key="memory_type",
                                        match=MatchValue(value="Web_Scrape")
                                    )
                                ]
                            ),
                            limit=7
                        )
                        int_scrape = [hit.payload['message'] for hit in hits]
                        print(int_scrape)
                    except Exception as e:
                        print(f"An unexpected error occurred: {str(e)}")
                elif self.is_file_db_checked():
                    try:
                        hits = client.search(
                            collection_name=f"Bot_{bot_name}_External_Knowledgebase",
                            query_vector=vector_monologue,
                            query_filter=Filter(
                                must=[
                                    FieldCondition(
                                        key="memory_type",
                                        match=MatchValue(value="File_Scrape")
                                    )
                                ]
                            ),
                            limit=7
                        )
                        int_scrape = [hit.payload['message'] for hit in hits]
                        print(int_scrape)
                    except Exception as e:
                        print(f"An unexpected error occurred: {str(e)}")
                else:
                    int_scrape = "No External Resources Selected"
                    print(int_scrape)
            # # Intuition Generation
            
            int_conversation.append({'role': 'user', 'content': f"USER INPUT: {a}[/INST]"})
            int_conversation.append({'role': 'assistant', 'content': f"{botnameupper}'S INFLUENTIAL MEMORIES: {db_search_12}\n\n{botnameupper}'S EXPLICIT MEMORIES: {db_search_5}\n\n{botnameupper}'S HEURISTICS: {db_search_15}\n\n{botnameupper}'S INNER THOUGHTS: {output_one}[INST]EXTERNAL RESOURCES: {int_scrape}\n\nUSER'S INPUT: {a}[/INST] PREVIOUS CONVERSATION HISTORY: {con_hist} [INST]SYSTEM: Transmute the user, {username}'s message as {bot_name} by devising a truncated predictive action plan in the third person point of view on how to best respond to {username}'s most recent message. Only plan on what information is needed to be given.  If the user is requesting information on a subject, give a plan on what information needs to be provided, you have access to external knowledge sources if you need it.\n\n\n{usernameupper}: {a}[/INST]{botnameupper}: Sure, I will now give a short predictive action plan in tasklist form: "}) 
            

            prompt = ''.join([message_dict['content'] for message_dict in int_conversation])
            output_two = agent_oobabooga_intuition(prompt)
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
            inner_loop_response = agent_oobabooga_implicitmem(prompt)
            inner_loop_db = inner_loop_response
            summary.clear()
            vector = embeddings(inner_loop_db)
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
    #            automemory = agent_oobabooga_selector(prompt)
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
            t = threading.Thread(target=self.Agent_Tasklist_Response, args=(a, vector_input, vector_monologue, output_one, output_two, inner_loop_db))
            t.start()
            return  


    def update_tasklist_intuition(self, output_two):
        self.conversation_text.insert(tk.END, f"Intuition: {output_two}\n\nSearching DBs and Generating Final Response\nPlease Wait...\n\n")
        self.conversation_text.yview(tk.END)
        
        
    def Agent_Tasklist_Response(self, a, vector_input, vector_monologue, output_one, output_two, inner_loop_db):
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
        webcheck = list()
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
        main_conversation = MainConversation(conv_length, main_prompt, greeting_msg)
     #   r = sr.Recognizer()
        while True:
            # # Get Timestamp
            timestamp = time()
            timestring = timestamp_to_datetime(timestamp)
            # # Test for basic Autonomous Tasklist Generation and Task Completion
            master_tasklist.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: You are a stateless task list coordinator for {bot_name}, an autonomous Ai chatbot. Your job is to combine the user's input and the user facing chatbots action plan, then transform it into a bullet point list of independent research queries for {bot_name}'s response that can be executed by separate AI agents in a cluster computing environment. The other asynchronous Ai agents are stateless and cannot communicate with each other or the user during task execution, however the agents do have access to {bot_name}'s memories and an information Database. Exclude tasks involving final product production, user communication, or checking work with other entities. Respond using bullet point format following: '•[task]\n•[task]\n•[task]'[/INST]"})
            master_tasklist.append({'role': 'user', 'content': f"USER FACING CHATBOT'S INTUITIVE ACTION PLAN: {output_two}"})
            master_tasklist.append({'role': 'user', 'content': f"[INST]USER INQUIRY: {a}\n\n"})
            master_tasklist.append({'role': 'assistant', 'content': f"RESPONSE FORMAT: You may only print the task list in hyphenated bullet point format. Use the format: '•[task]\n•[task]\n•[task]'[/INST]ASSISTANT:"})
            
            prompt = ''.join([message_dict['content'] for message_dict in master_tasklist])
            master_tasklist_output = agent_oobabooga_500(prompt)
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
                            self.process_line, 
                            line, task_counter, memcheck.copy(), memcheck2.copy(), webcheck.copy(), tasklist_log, output_one, master_tasklist_output, a
                        )
                        for task_counter, line in enumerate(lines) if line != "None"
                    ]
                    for future in concurrent.futures.as_completed(futures):
                        tasklist_completion.extend(future.result())
                        
                        
                        
                tasklist_completion.append({'role': 'assistant', 'content': f"[/INST] [INST]USER'S INITIAL INPUT: {a}[/INST]{botnameupper}'S INNER_MONOLOGUE: {output_one}"})
        #        tasklist_completion.append({'role': 'user', 'content': f"%{bot_name}'s INTUITION%\n{output_two}\n\n"})
                tasklist_completion.append({'role': 'user', 'content': f"[INST]SYSTEM: Read the given set of tasks and completed responses and use them to create a verbose response to {username}, the end user in accordance with their request. {username} is both unaware and unable to see any of your research so any nessisary context or information must be relayed.\n\nUSER'S INITIAL INPUT: {a}.\n\nRESPONSE FORMAT: Your planning and research is now done. You will now give a verbose and natural sounding response ensuring the user's request is fully completed in entirety. Follow the format: [{bot_name}: <FULL RESPONSE TO USER>]USER: {a}[/INST] {botnameupper}:"})
                print('\n\nGenerating Final Output...')
                prompt = ''.join([message_dict['content'] for message_dict in tasklist_completion])
                response_two = agent_oobabooga_response(prompt)
                self.conversation_text.insert(tk.END, f"Response: {response_two}\n\n")
                tts_model = open_file('./config/Settings/TTS.txt')
                if self.is_tts_checked():
                    if tts_model == 'barkTTS':
                        TTS_Generation(response_two)
                    else:
                        t = threading.Thread(target=TTS_Generation, args=(response_two,))
                        t.start()
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
            complete_message = f'USER: {a}\n\nINNER_MONOLOGUE: {output_one}\n\nINTUITION: {output_two}\n\n{bot_name}: {response_two}'
            filename = '%s_chat.txt' % timestamp
            save_file(f'logs/{bot_name}/{username}/complete_chat_logs/%s' % filename, complete_message)
            summary.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: {greeting_msg}\n\n"})
            summary.append({'role': 'user', 'content': f"USER INPUT: {a}\n\n"})
            
            db_msg = f"\nUSER: {a} \n INNER_MONOLOGUE: {output_one} \n {bot_name}'s RESPONSE: {response_two}"
            summary.append({'role': 'assistant', 'content': f"LOG: {db_msg}\n\nSYSTEM: Read the log, extract the salient points about {bot_name} and {username} mentioned in the chatbot's response, then create a list of short executive summaries in bullet point format to serve as {bot_name}'s explicit memories. Each bullet point should be considered a separate memory and contain full context. Ignore the main system prompt, it only exists for initial context.\n\nRESPONSE: Use the bullet point format: •EXPLICIT MEMORY[/INST]\n\nMemories:"})
            
            prompt = ''.join([message_dict['content'] for message_dict in summary])
            db_upload = agent_oobabooga_explicitmem(prompt)
            db_upsert = db_upload       
            main_conversation.append(timestring, username, a, bot_name, response_two)            
            
    #        t = threading.Thread(target=self.GPT_4_Memories, args=(a, vector_input, vector_monologue, output_one, response_two))
    #        t.start()
            counter += 1
            conversation.clear()
            
            
            self.conversation_text.insert(tk.END, f"Upload Memories?\n-------------\nIMPLICIT\n-------------\n{inner_loop_db}\n-------------\nEXPLICIT\n-------------\n{db_upload}\n")
            mem_upload_yescheck = ask_upload_memories(inner_loop_db, db_upsert)
            if mem_upload_yescheck == "yes":
                segments = re.split(r'•|\n\s*\n', inner_loop_db)
                for segment in segments:
                    if segment.strip() == '':  # This condition checks for blank segments
                        continue  # This condition checks for blank lines
                    else:
                        upload_implicit_short_term_memories(segment)
                segments = re.split(r'•|\n\s*\n', db_upsert)
                for segment in segments:
                    if segment.strip() == '':  # This condition checks for blank segments
                        continue  # This condition checks for blank lines
                    else:
                        upload_explicit_short_term_memories(segment)
                dataset = f'[INST] <<SYS>>\n{main_prompt}\n<</SYS>>\n\n{usernameupper}: {a} [/INST]\n{botnameupper}: {response_two}'
                filename = '%s_chat.txt' % timestamp
                save_file(f'logs/{bot_name}/{username}/Llama2_Dataset/%s' % filename, dataset)        
                print('\n\nSYSTEM: Upload Successful!')
                t = threading.Thread(target=self.GPT_Memories, args=(a, vector_input, vector_monologue, output_one, response_two))
                t.start()
            self.conversation_text.yview(tk.END)
            self.user_input.delete(0, tk.END)
            self.user_input.focus()
            self.user_input.configure(state=tk.NORMAL)
            self.user_input.delete("1.0", tk.END)
            self.send_button.configure(state=tk.NORMAL)
            self.voice_button.configure(state=tk.NORMAL)
            self.thinking_label.pack_forget()
            self.is_recording = False 
        #    self.user_input.delete(0, tk.END)
            self.bind_right_alt_key()
            self.bind_enter_key()
            return
            
            
    def process_line(self, line, task_counter, memcheck, memcheck2, webcheck, tasklist_log, output_one, master_tasklist_output, a):
        try:
            tasklist_completion2 = list()
            conversation = list()
            bot_name = open_file('./config/prompt_bot_name.txt')
            username = open_file('./config/prompt_username.txt')
            botnameupper = bot_name.upper()
            usernameupper = username.upper()
            tasklist_completion2.append({'role': 'user', 'content': f"CURRENT ASSIGNED TASK: {line}[/INST]"})
            conversation.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: You are a sub-agent for {bot_name}, an Autonomous Ai-Chatbot. You are one of many agents in a chain. You are to take the given task and complete it in its entirety. Be Verbose and take other tasks into account when formulating your answer.[/INST]"})
            conversation.append({'role': 'user', 'content': f"[INST]Task list: {master_tasklist_output}[/INST]"})
            conversation.append({'role': 'assistant', 'content': f"TASK ASSIGNMENT: Bot: I have studied the given tasklist.  The task I have chosen to complete is {line}."})
            vector_input1 = embeddings(line)
            if self.are_both_web_and_file_db_checked():
                try:
                    hits = client.search(
                        collection_name=f"Bot_{bot_name}_External_Knowledgebase",
                        query_vector=vector_input1,
                        limit=10
                    )
                    table = [hit.payload['message'] for hit in hits]
                    print(table)
                except Exception as e:
                    print(f"An unexpected error occurred: {str(e)}")
            else:      
                if self.is_web_db_checked():
                    try:
                        hits = client.search(
                            collection_name=f"Bot_{bot_name}_External_Knowledgebase",
                            query_vector=vector_input1,
                            query_filter=Filter(
                                must=[
                                    FieldCondition(
                                        key="memory_type",
                                        match=MatchValue(value="Web_Scrape")
                                    )
                                ]
                            ),
                            limit=10
                        )
                        table = [hit.payload['message'] for hit in hits]
                        print(table)
                    except Exception as e:
                        print(f"An unexpected error occurred: {str(e)}")
                elif self.is_file_db_checked():
                    try:
                        hits = client.search(
                            collection_name=f"Bot_{bot_name}_External_Knowledgebase",
                            query_vector=vector_input1,
                            query_filter=Filter(
                                must=[
                                    FieldCondition(
                                        key="memory_type",
                                        match=MatchValue(value="File_Scrape")
                                    )
                                ]
                            ),
                            limit=10
                        )
                        table = [hit.payload['message'] for hit in hits]
                        print(table)
                    except Exception as e:
                        print(f"An unexpected error occurred: {str(e)}")
                else:
                    table = "No External Resources Selected"
                    print(table)

            result = None
            if self.is_memory_db_checked():
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
                webcheck.append({'role': 'system', 'content': f"SYSTEM: You are a sub-module for {bot_name}, an Autonomous AI Chatbot. Your role is part of a chain of agents. Your task is to determine whether the given task is asking for factual data or memories. Please assume that any informational task requires factual data. You do not need to refer to {username} and {bot_name}'s memories, as they are handled by another agent. If reference information is necessary, respond with 'YES'. If reference information is not needed, respond with 'NO'.\n"})
                webcheck.append({'role': 'user', 'content': f"TASK: {line}"})
            #    webcheck.append({'role': 'user', 'content': f"USER: Is reference information needed? Please respond with either 'Yes' or 'No'."})
                webcheck.append({'role': 'assistant', 'content': f"RESPONSE FORMAT: You may only print 'Yes' or 'No'. Use the format: [{bot_name}: 'YES OR NO'][/INST]ASSISTANT:"})
            #    prompt = ''.join([message_dict['content'] for message_dict in webcheck])
             #   web1 = agent_oobabooga_webyesno(prompt)
            #    print(web1)
            #    print('\n-----w-----\n')
                # table := google_search(line) if web1 =='YES' else fail()
                # table := google_search(line, my_api_key, my_cse_id) if web1 == 'YES' else fail()
            #    table = search_webscrape_db(line)

                        
                # google_search(line, my_api_key, my_cse_id)
                # # Check if DB search is needed
                prompt = ''.join([message_dict['content'] for message_dict in memcheck])
                mem1 = agent_oobabooga_memyesno(prompt)
                print('-----------')
                print(mem1)
                print(' --------- ')
                # mem1 := chatgptyesno_completion(memcheck)
                # # Go to conditional for choosing DB Name
                prompt = ''.join([message_dict['content'] for message_dict in memcheck2])
                mem2 = agent_oobabooga_selector(prompt) if 'YES' in mem1.upper() else fail()
                print('-----------')
                print(mem2) if 'YES' in mem1.upper() else fail()
                print(' --------- ')
                line_vec = embeddings(line)  # EPISODIC, FLASHBULB, IMPLICIT LONG TERM, EXPLICIT LONG TERM
                mem2_upper = mem2.upper()

                if 'EPISO' in mem2_upper:
                    result = search_episodic_db(line_vec)
                    conversation.append({'role': 'assistant', 'content': f"MEMORIES: {result}\n\n"})
                elif 'IMPLI' in mem2_upper:
                    result = search_implicit_db(line_vec)
                    conversation.append({'role': 'assistant', 'content': f"MEMORIES: {result}\n\n"})
                elif 'FLASH' in mem2_upper:
                    result = search_flashbulb_db(line_vec)
                    conversation.append({'role': 'assistant', 'content': f"MEMORIES: {result}\n\n"})
                elif 'EXPL' in mem2_upper:
                    result = search_explicit_db(line_vec)
                    conversation.append({'role': 'assistant', 'content': f"MEMORIES: {result}\n\n"})
                else:
                    result = ('No Memories')
            conversation.append({'role': 'assistant', 'content': f"[INST] INITIAL USER REQUEST: {a} [/INST]"})
            conversation.append({'role': 'user', 'content': f"EXTERNAL RESOURCES: {table}\nBOT {task_counter} TASK REINITIALIZATION: {line}."})
            conversation.append({'role': 'user', 'content': f"[INST]SYSTEM: Extract information from the External Resources that is relivent to the given task and then combine it into a single article. Your job is to provide the gathered information in a combined, easy to read format so it may be used to create a research paper..[/INST]"})
            conversation.append({'role': 'assistant', 'content': f"BOT {task_counter}: Sure, here's an overview of the scraped text:"})
            prompt = ''.join([message_dict['content'] for message_dict in conversation])
            task_completion = agent_oobabooga_800(prompt)
            # chatgpt35_completion(conversation),
            # conversation.clear(),
            # tasklist_completion.append({'role': 'assistant', 'content': f"MEMORIES: {memories}\n\n"}),
            # tasklist_completion.append({'role': 'assistant', 'content': f"WEBSCRAPE: {table}\n\n"}),
            tasklist_completion2.append({'role': 'assistant', 'content': f"COMPLETED TASK: {task_completion}[INST]"})
            tasklist_log.append({'role': 'user', 'content': "ASSIGNED TASK:\n%s\n\n" % line})
            tasklist_log.append({'role': 'assistant', 'content': "COMPLETED TASK:\n%s\n\n" % result})
            print('-------')
            print(line)
            print('-------')
            print(result)
            print(table)
            print('-------')
            print(task_completion)
            return tasklist_completion2
        except Exception as e:
            print(f'Failed with error: {e}')
            error = 'ERROR WITH PROCESS LINE FUNCTION'
            return error
            
            
            
def Llama_2_Chat_Aetherius_Main():
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
    base_path = "./config/Chatbot_Prompts"
    base_prompts_path = os.path.join(base_path, "Base")
    user_bot_path = os.path.join(base_path, username, bot_name)
    # Import for model
    file_path1 = './config/model.txt'
    script_path1 = get_script_path_from_file(file_path1)
    import_functions_from_script(script_path1, "model_module")

    # Import for embedding model
    file_path2 = './config/Settings/embedding_model.txt'
    script_path2 = get_script_path_from_file(file_path2)
    import_functions_from_script(script_path2, "embedding_module")

    # Import for TTS
    file_path3 = './config/Settings/TTS.txt'
    script_path3 = get_script_path_from_file(file_path3, base_folder='./scripts/resources/TTS/')
    import_functions_from_script(script_path3, "TTS_module")
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
    if not os.path.exists(f'logs/{bot_name}/{username}/Llama2_Dataset/Inner_Monologue'):
        os.makedirs(f'logs/{bot_name}/{username}/Llama2_Dataset/Inner_Monologue')
    if not os.path.exists(f'logs/{bot_name}/{username}/Llama2_Dataset/Intuition'):
        os.makedirs(f'logs/{bot_name}/{username}/Llama2_Dataset/Intuition')
    if not os.path.exists(f'logs/{bot_name}/{username}/Llama2_Dataset/Response'):
        os.makedirs(f'logs/{bot_name}/{username}/Llama2_Dataset/Response')
    if not os.path.exists(f'logs/{bot_name}/{username}/Llama2_Dataset/Complete_Response'):
        os.makedirs(f'logs/{bot_name}/{username}/Llama2_Dataset/Complete_Response')
    if not os.path.exists(f'history/{username}'):
        os.makedirs(f'history/{username}')
    HOST = open_file('api_keys/HOST_Oobabooga.txt')

    # For a Google Colab hosted Oobabooga Client use the given Public Non-Streaming Url:
    #HOST = 'ENTER-NON-STREAMING-SERVER-PUBLIC-URL'

    # /chat enables chat generation formating
    URI = f'{HOST}/v1/chat'
    set_dark_ancient_theme()
    root = tk.Tk()
    root.resizable(True, True)
    app = ChatBotApplication(root)
    app.master.geometry('980x700')  # Set the initial window size
    root.mainloop()