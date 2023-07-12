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
import pinecone
import requests
from basic_functions import *
from tool_functions import *
import multiprocessing
import threading
import concurrent.futures
import customtkinter
import tkinter as tk
from tkinter import ttk, scrolledtext, simpledialog, font
from bs4 import BeautifulSoup
import importlib.util
import requests
from sentence_transformers import SentenceTransformer
import shutil


# For local streaming, the websockets are hosted without ssl - http://
HOST = 'localhost:5000'
URI = f'http://{HOST}/api/v1/generate'

# For reverse-proxied streaming, the remote will likely host with ssl - https://
# URI = 'https://your-uri-here.trycloudflare.com/api/v1/generate'


model = SentenceTransformer('all-mpnet-base-v2')

def oobabooga_250(prompt):
    request = {
        'prompt': prompt,
        'max_new_tokens': 250,

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
        result = response.json()['results'][0]['text']
    #    print(result)
        return result
        
        
def oobabooga_500(prompt):
    request = {
        'prompt': prompt,
        'max_new_tokens': 500,

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
        result = response.json()['results'][0]['text']
    #    print(result)
        return result
        
        
def oobabooga_800(prompt):
    request = {
        'prompt': prompt,
        'max_new_tokens': 800,

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
        result = response.json()['results'][0]['text']
    #    print(result)
        return result
        
        
def oobabooga_scrape(prompt):
    request = {
        'prompt': prompt,
        'max_new_tokens': 600,

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
        result = response.json()['results'][0]['text']
    #    print(result)
        return result
        
        
def oobabooga_response(prompt):
    request = {
        'prompt': prompt,
        'max_new_tokens': 1500,

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
        result = response.json()['results'][0]['text']
    #    print(result)
        return result
        
        
        
def oobabooga_selector(prompt):
    request = {
        'prompt': prompt,
        'max_new_tokens': 10,

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
        result = response.json()['results'][0]['text']
    #    print(result)
        return result


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
    vdb = pinecone.Index("aetherius")
    try:
        with lock:
            print('implicit')
            results = vdb.query(vector=line_vec, filter={"memory_type": "implicit_long_term", "user": username}, top_k=7, namespace=f'{bot_name}')
            memories1 = load_conversation_implicit_long_term_memory(results)
            results = vdb.query(vector=line_vec, filter={"memory_type": "implicit_short_term"}, top_k=5, namespace=f'short_term_memory_User_{username}_Bot_{bot_name}')
            memories2 = load_conversation_implicit_short_term_memory(results)
            memories = f'{memories1}\n{memories2}'
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
    vdb = pinecone.Index("aetherius")
    try:
        with lock:
            results = vdb.query(vector=line_vec, filter={
            "memory_type": "episodic", "user": username}, top_k=5, namespace=f'{bot_name}')
            memories = load_conversation_episodic_memory(results)
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
    vdb = pinecone.Index("aetherius")
    try:
        with lock:
            results = vdb.query(vector=line_vec, filter={
            "memory_type": "flashbulb", "user": username}, top_k=5, namespace=f'{bot_name}')
            memories = load_conversation_flashbulb_memory(results)
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
    vdb = pinecone.Index("aetherius")
    try:
        with lock:
            print('explicit')
            results = vdb.query(vector=line_vec, filter={"memory_type": "explicit_long_term", "user": username}, top_k=5, namespace=f'{bot_name}')
            memories1 = load_conversation_explicit_long_term_memory(results)
            results = vdb.query(vector=line_vec, filter={"memory_type": "explicit_short_term"}, top_k=5, namespace=f'short_term_memory_User_{username}_Bot_{bot_name}')
            memories2 = load_conversation_explicit_short_term_memory(results)
            memories = f'{memories1}\n{memories2}'
            print(memories)
            return memories
    except Exception as e:
        print(e)
        memories = "Error"
        return memories   
        
        
def load_conversation_web_scrape_memory(results):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
    try:
        result = list()
        for m in results['matches']:
            info = load_json(f'nexus/{bot_name}/{username}/web_scrape_memory_nexus/%s.json' % m['id'])
            result.append(info)
        ordered = sorted(result, key=lambda d: d['time'], reverse=False)  # sort them all chronologically
        messages = [i['message'] for i in ordered]
        return '\n'.join(messages).strip()
    except Exception as e:
        print(e)
        table = "Error"
        return table
    
    
def search_webscrape_db(line):
    m = multiprocessing.Manager()
    lock = m.Lock()
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
    vdb = pinecone.Index("aetherius")
    try:
        with lock:
            line_vec = model.encode([line]).tolist()
            results = vdb.query(vector=line_vec, filter={"memory_type": "web_scrape"}, top_k=25, namespace=f'Tools_User_{username}_Bot_{bot_name}')
            table = load_conversation_web_scrape_memory(results)
            return table
    except Exception as e:
        print(e)
        table = "Error"
        return table
        

def fail():
  #  print('')
    fail = "Not Needed"
    return fail
    
    
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



def chunk_text_from_url(url, chunk_size=550, overlap=80, results_callback=None):
    bot_name = open_file('./config/prompt_bot_name.txt')
    try:
        print("Scraping given URL, please wait...")
        bot_name = open_file('./config/prompt_bot_name.txt')
        username = open_file('./config/prompt_username.txt')
        vdb = pinecone.Index("aetherius")
        html = requests.get(url).text
        soup = BeautifulSoup(html, 'html.parser')
        texttemp = soup.get_text().strip()
        texttemp = texttemp.replace('\n', '').replace('\r', '')
        texttemp = '\n'.join(line for line in texttemp.splitlines() if line.strip())
        chunks = chunk_text(texttemp, chunk_size, overlap)
        weblist = list()
        for chunk in chunks:
            websum = list()
            websum2 = list()
            websum2.append({'role': 'system', 'content': "%MAIN SYSTEM PROMPT%\nYou are an ai text editor.  Your job is to take the given text from a webscrape, then return the scraped text in an informational article form.  Do not generalize, rephrase, or use latent knowledge in your summary.  If no article is given, print no article.\n\n"})
            websum2.append({'role': 'user', 'content': f"%WEBSCRAPE%\n{chunk}\n\n%INSTRUCTIONS%\nSummarize the webscrape without losing any factual knowledge and maintaining full context.\n\n%RESPONSE%\n"})
            websum.append({'role': 'system', 'content': "%MAIN SYSTEM PROMPT%\nYou are a data extractor. Your job is to take the given text from a webscrape, then highlight all important or factual information without losing any data. All salient information should be returned condensed without modifying its factual nature. Only use the given information, do not generalize, rephrase, or use other latent knowledge.  Use the format: [<Semantic Question Title>]: <Article/Guide>. Avoid using linebreaks inside of the article or its formatting.  Lists should be made into continuous text form to avoid them. If no article is given, print no article.\n\n"})
            websum.append({'role': 'user', 'content': f"%WEBSCRAPED ARTICLE%\n{chunk}\n\n%RESPONSE FORMAT%\nHere is a condensed version of the given webscrape. Use the format: [<Semantic Question Title>]: <Article/Guide>.\n\n%RESPONSE%\n"})
            prompt = ''.join([message_dict['content'] for message_dict in websum2])
            text = oobabooga_scrape(prompt)
            if len(text) < 20:
                text = "No Webscrape available"
        #    text = chatgpt35_completion(websum)
        #    paragraphs = text.split('\n\n')  # Split into paragraphs
        #    for paragraph in paragraphs:  # Process each paragraph individually, add a check to see if paragraph contained actual information.
            webcheck = list()
            webcheck.append({'role': 'system', 'content': f"%MAIN SYSTEM PROMPT%\nYou are an agent for an automated webscraping tool. Your task is to decide if the previous Ai Agent scraped the text successfully. The scraped text should contain some form of article, if it does, print 'YES'. If the article was scraped successfully, print: 'YES'.  If the webscrape failed or is a response from the first agent, print: 'NO'.\n\n"})
            webcheck.append({'role': 'user', 'content': f"%ORIGINAL TEXT FROM SCRAPE%\n{chunk}\n\n"})
            webcheck.append({'role': 'user', 'content': f"%PROCESSED WEBSCRAPE%\n{text}\n\n"})
            
            webcheck.append({'role': 'user', 'content': f"%RESPONSE FORMAT%\nYou are responding for a Yes or No input field. You are only capible of printing Yes or No. Use the format: [AI AGENT: <'Yes'/'No'>]\n\n"})
            webcheck.append({'role': 'user', 'content': f"%RESPONSE%\n["})
       
            
            prompt = ''.join([message_dict['content'] for message_dict in webcheck])
            webyescheck = oobabooga_selector(prompt)
            
        #        webyescheck = chatgptyesno_completion(webcheck)
        #        if 'yes' in webyescheck.lower():
        #            print('---------')
        #            print(url + ' ' + paragraph)
        #            if results_callback is not None:
        #                results_callback(url + ' ' + paragraph)
        #            payload = list()
        #            vector = vector_monologue = model.encode([url + ' ' + paragraph]).tolist()
        #            timestamp = time()
        #            timestring = timestamp_to_datetime(timestamp)
        #            unique_id = str(uuid4())
        #            metadata = {'bot': bot_name, 'time': timestamp, 'message': url + ' ' + paragraph,
        #                        'timestring': timestring, 'uuid': unique_id, "memory_type": "web_scrape"}
        #            save_json(f'nexus/{bot_name}/{username}/web_scrape_memory_nexus/%s.json' % unique_id, metadata)
        #            payload.append((unique_id, vector, {"memory_type": "web_scrape"}))
        #            vdb.upsert(payload, namespace=f'Tools_User_{username}_Bot_{bot_name}')
        #            payload.clear()
        #        if 'yes' in webyescheck.lower():
        #            print('---------')
        #            print(url + ' ' + paragraph)
        #            if results_callback is not None:
        #                results_callback(url + ' ' + paragraph)
        #            payload = list()
        #            vector = vector_monologue = model.encode([url + ' ' + paragraph]).tolist()
        #            timestamp = time()
        #            timestring = timestamp_to_datetime(timestamp)
        #            unique_id = str(uuid4())
        #            metadata = {'bot': bot_name, 'time': timestamp, 'message': url + ' ' + paragraph,
        #                        'timestring': timestring, 'uuid': unique_id, "memory_type": "web_scrape"}
        #            save_json(f'nexus/{bot_name}/{username}/web_scrape_memory_nexus/%s.json' % unique_id, metadata)
        #            payload.append((unique_id, vector, {"memory_type": "web_scrape"}))
        #            vdb.upsert(payload, namespace=f'Tools_User_{username}_Bot_{bot_name}')
        #            payload.clear()
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
                    print('---------')
                    weblist.append(url + ' ' + text)
                    print(url + ' ' + text)
                    if results_callback is not None:
                        results_callback(url + ' ' + text)
                    payload = list()
                    vector = model.encode([url + ' ' + text]).tolist()
                    timestamp = time()
                    timestring = timestamp_to_datetime(timestamp)
                    unique_id = str(uuid4())
                    metadata = {'bot': bot_name, 'time': timestamp, 'message': url + ' ' + text,
                                'timestring': timestring, 'uuid': unique_id, "memory_type": "web_scrape"}
                    save_json(f'nexus/{bot_name}/{username}/web_scrape_memory_nexus/%s.json' % unique_id, metadata)
                    payload.append((unique_id, vector, {"memory_type": "web_scrape"}))
                    vdb.upsert(payload, namespace=f'Tools_User_{username}_Bot_{bot_name}')
                    payload.clear()           
                    pass  
                else:
                    print('---------')
                    print(f'\n\n\nERROR MESSAGE FROM BOT: {webyescheck}\n\n\n')
                #    if len(text) > 50:
                #        print('---------')
                #        print(url + ' ' + text)
                #        if results_callback is not None:
                #            results_callback(url + ' ' + text)
                #        payload = list()
                #        vector = model.encode([url + ' ' + text]).tolist()
                #        timestamp = time()
                #        timestring = timestamp_to_datetime(timestamp)
                #        unique_id = str(uuid4())
                #        metadata = {'bot': bot_name, 'time': timestamp, 'message': url + ' ' + text,
                #                    'timestring': timestring, 'uuid': unique_id, "memory_type": "web_scrape"}
                #        save_json(f'nexus/{bot_name}/{username}/web_scrape_memory_nexus/%s.json' % unique_id, metadata)
                #        payload.append((unique_id, vector, {"memory_type": "web_scrape"}))
                #        vdb.upsert(payload, namespace=f'Tools_User_{username}_Bot_{bot_name}')
                #        payload.clear()
                            
        table = weblist
        
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
    vdb = pinecone.Index("aetherius")
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
        if query == 'Clear Memory':
            while True:
                print('\n\nSYSTEM: Are you sure you would like to delete saved short-term memory?\n        Press Y for yes or N for no.')
                user_input = input("'Y' or 'N': ")
                if user_input == 'y':
                    vdb.delete(filter={"memory_type": "web_scrape"}, namespace=f'Tools_User_{username}_Bot_{bot_name}')
                    print('Webscrape has been Deleted')
                    return
                elif user_input == 'n':
                    print('\n\nSYSTEM: Webscrape delete cancelled.')
                    return
        
        # # Check for "Exit"
        if query == 'Skip':   
            pass
        else:
            urls = urls = chunk_text_from_url(query)
        print('---------')
        return
        
        
def GPT_4_Tasklist_Web_Search(query, results_callback):
    vdb = pinecone.Index("aetherius")
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
        if query == 'Clear Memory':
            while True:
                print('\n\nSYSTEM: Are you sure you would like to delete saved short-term memory?\n        Press Y for yes or N for no.')
                user_input = input("'Y' or 'N': ")
                if user_input == 'y':
                    vdb.delete(filter={"memory_type": "web_scrape"}, namespace=f'Tools_User_{username}_Bot_{bot_name}')
                    print('Webscrape has been Deleted')
                    return
                elif user_input == 'n':
                    print('\n\nSYSTEM: Webscrape delete cancelled.')
                    return
            
            # # Check for "Exit"
        if query == 'Skip':   
            pass
        else:
            urls = google_search(query, my_api_key, my_cse_id)
            with concurrent.futures.ThreadPoolExecutor() as executor:
                executor.map(chunk_text_from_url, urls)
        print('---------')
        return
        
        
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
            self.master.destroy()
            Experimental_Local_Aether_Search()
        

    def choose_username(self):
        username = simpledialog.askstring("Choose Username", "Type a Username:")
        if username:
            file_path = "./config/prompt_username.txt"
            with open(file_path, 'w') as file:
                file.write(username)
            self.conversation_text.delete("1.0", tk.END)
            self.display_conversation_history()
            self.master.destroy()
            Experimental_Local_Aether_Search()
        pass
        
    def update_results(self, text_widget, url, paragraph):
        self.after(0, text_widget.insert, tk.END, url + ' ' + paragraph)
        self.update()
        
        
    def Edit_Main_Prompt(self):
        bot_name = open_file('./config/prompt_bot_name.txt')
        username = open_file('./config/prompt_username.txt')
        file_path = f"./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt"

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
        bot_name = open_file('./config/prompt_bot_name.txt')
        username = open_file('./config/prompt_username.txt')
        file_path = f"./config/Chatbot_Prompts/{username}/{bot_name}/prompt_secondary.txt"
        
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
        bot_name = open_file('./config/prompt_bot_name.txt')
        username = open_file('./config/prompt_username.txt')
        file_path = f"./config/Chatbot_Prompts/{username}/{bot_name}/prompt_greeting.txt"
        
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

        search_button = tk.Button(websearch_window, text="Search", command=perform_search)
        search_button.pack()

    def update_results(self, text_widget, search_results):
        self.after(0, text_widget.delete, "1.0", tk.END)
        self.after(0, text_widget.insert, tk.END, search_results)

    def open_webscrape_window(self):
        webscrape_window = tk.Toplevel(self)
        webscrape_window.title("Web Scrape")

        query_label = tk.Label(webscrape_window, text="Enter a URL:")
        query_label.pack()

        query_entry = tk.Entry(webscrape_window)
        query_entry.pack()

        results_label = tk.Label(webscrape_window, text="Scrape results: (Not Working Yet, Results in Terminal)")
        results_label.pack()

        results_text = tk.Text(webscrape_window)
        results_text.pack()

        def perform_search():
            query = query_entry.get()

            def update_results(paragraph):
                # Update the GUI with the new paragraph
                self.update_results(results_text, paragraph)

            def search_task():
                # Call the modified GPT_4_Tasklist_Web_Search function with the callback
                GPT_4_Tasklist_Web_Scrape(query, results_callback=update_results)

            t = threading.Thread(target=search_task)
            t.start()

        search_button = tk.Button(webscrape_window, text="Search", command=perform_search)
        search_button.pack()
        
        
    def delete_websearch_db(self):
        # Delete the conversation history JSON file
        bot_name = open_file('./config/prompt_bot_name.txt')
        username = open_file('./config/prompt_username.txt')
        vdb = pinecone.Index("aetherius")
        try:
            vdb.delete(filter={"memory_type": "web_scrape"}, namespace=f'Tools_User_{username}_Bot_{bot_name}')
            print('Webscrape has been Deleted')
            self.master.destroy()
            Experimental_Local_Aether_Search()
        except:
            print("Fail")
            pass
        
        
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
        
        self.websearch_button = tk.Button(self.top_frame, text="Web Search", command=self.open_websearch_window, bg=self.button_color, fg=self.text_color)
        self.websearch_button.pack(side=tk.LEFT, padx=5, pady=5, ipadx=10)
        
        self.delete_websearch_button = tk.Button(self.top_frame, text="Clear Websearch DB", command=self.delete_websearch_db, bg=self.button_color, fg=self.text_color)
        self.delete_websearch_button.pack(side=tk.LEFT, padx=5, pady=5, ipadx=10)
        
        self.webscrape_button = tk.Button(self.top_frame, text="Web Scrape", command=self.open_webscrape_window, bg=self.button_color, fg=self.text_color)
        self.webscrape_button.pack(side=tk.LEFT, padx=5, pady=5, ipadx=10)
        
        self.menu = ttk.Combobox(self.top_frame, values=["Config Menu", "----------------------------", "Model Selection", "Edit Font", "Edit Font Size", "Edit Main Prompt", "Edit Secondary Prompt", "Edit Greeting Prompt"], state="readonly")
        self.menu.pack(side=tk.LEFT, padx=5, pady=5)
        self.menu.current(0)
        self.menu.bind("<<ComboboxSelected>>", self.handle_menu_selection)

        self.placeholder_label = tk.Label(self.top_frame, bg=self.background_color)
        self.placeholder_label.pack(side=tk.RIGHT, expand=True, fill=tk.X)

        self.conversation_text = tk.Text(self, bg=self.background_color, fg=self.text_color, wrap=tk.WORD)
        self.conversation_text.pack(fill=tk.BOTH, expand=True)
        self.conversation_text.configure(font=font_style)
        self.conversation_text.bind("<Key>", lambda e: "break")  # Disable keyboard input
        self.conversation_text.bind("<Button>", lambda e: "break")  # Disable mouse input

        self.input_frame = tk.Frame(self, bg=self.background_color)
        self.input_frame.pack(fill=tk.X, side="bottom")

        self.user_input = tk.Entry(self.input_frame, bg=self.background_color, fg=self.text_color)
        self.user_input.configure(font=(f"{font_config}", 10))
        self.user_input.pack(fill=tk.X, expand=True, side="left")
        
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
            vdb.delete(filter={"memory_type": "web_scrape"}, namespace=f'Tools_User_{username}_Bot_{bot_name}')
            print('Webscrape has been Deleted')
            self.master.destroy()
            Experimental_Local_Aether_Search()
        except:
            pass


    def send_message(self):
        a = self.user_input.get()
        self.user_input.delete(0, tk.END)
        self.user_input.config(state=tk.DISABLED)
        self.send_button.config(state=tk.DISABLED)
        self.user_input.unbind("<Return>")
        # Display "Thinking..." in the input field
        self.thinking_label.pack()
        t = threading.Thread(target=self.process_message, args=(a,))
        t.start()


    def process_message(self, a):
        self.conversation_text.insert(tk.END, f"\nYou: {a}\n\n")
        self.conversation_text.yview(tk.END)
        # Here, we're calling your GPT_4_Training function in a separate thread
        t = threading.Thread(target=self.Tasklist_Inner_Monologue, args=(a,))
        t.start()
        
        
    def Tasklist_Inner_Monologue(self, a):
        vdb = pinecone.Index("aetherius")
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
            # # Start or Continue Conversation based on if response exists
            conversation.append({'role': 'system', 'content': f"%MAIN CHATBOT SYSTEM PROMPT%\n{main_prompt}\n\n"})
            int_conversation.append({'role': 'system', 'content': f"%MAIN CHATBOT SYSTEM PROMPT%\n{main_prompt}\n\n"})
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
            vector_input = model.encode([message_input]).tolist()
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
            conversation.append({'role': 'system', 'content': f"%MAIN CHATBOT SYSTEM PROMPT%\n{main_prompt}\n\n"})
            int_conversation.append({'role': 'system', 'content': f"%MAIN CHATBOT SYSTEM PROMPT%\n{main_prompt}\n\n"})
            # # Check for Exit, summarize the conversation, and then upload to episodic_memories
            tasklist.append({'role': 'system', 'content': "SYSTEM: You are a semantic rephraser. Your role is to interpret the original user query and generate 2-3 synonymous search terms that will guide the exploration of the chatbot's memory database. Each alternative term should reflect the essence of the user's initial search input. Please list your results using a hyphenated bullet point structure.\n\n"})
            tasklist.append({'role': 'user', 'content': "USER: USER INQUIRY: %s\n\n" % a})
            tasklist.append({'role': 'assistant', 'content': "TASK COORDINATOR: List of synonymous Semantic Terms:\n"})
            prompt = ''.join([message_dict['content'] for message_dict in tasklist])
            tasklist_output = oobabooga_250(prompt)
            print(tasklist_output)
            print('-------')
        #    print(tasklist_output)
            lines = tasklist_output.splitlines()
            db_term = {}
            db_term_result = {}
            db_term_result2 = {}
            tasklist_counter = 0
            # # Split bullet points into separate lines to be used as individual queries during a parallel db search
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [
                    executor.submit(
                        lambda line, _index, conversation, int_conversation: (
                            tasklist_vector := model.encode([line]).tolist(),
                            db_term.update({_index: tasklist_vector}),
                            results := vdb.query(vector=db_term[_index], filter={
            "memory_type": "explicit_long_term", "user": username}, top_k=2, namespace=f'{bot_name}'),
                            db_term_result.update({_index: load_conversation_explicit_long_term_memory(results)}),
                            results := vdb.query(vector=db_term[_index], filter={
            "memory_type": "implicit_long_term", "user": username}, top_k=1, namespace=f'{bot_name}'),
                            db_term_result2.update({_index: load_conversation_implicit_long_term_memory(results)}),
                            conversation.append({'role': 'assistant', 'content': f"%LONG TERM CHATBOT MEMORIES%\n{db_term_result[_index]}\n"}),
                            conversation.append({'role': 'assistant', 'content': f"%LONG TERM CHATBOT MEMORIES%\n{db_term_result2[_index]}\n"}),
                            (
                                int_conversation.append({'role': 'assistant', 'content': f"%LONG TERM CHATBOT MEMORIES%\n{db_term_result[_index]}\n"}),
                                int_conversation.append({'role': 'assistant', 'content': f"%LONG TERM CHATBOT MEMORIES%\n{db_term_result2[_index]}\n"})
                            ) if _index < 3 else None,
                        ),
                        line, _index, conversation.copy(), int_conversation.copy()
                    )
                    for _index, line in enumerate(lines) if line.strip()
                ] + [
                    executor.submit(lambda: (
                        vdb.query(vector=vector_input, filter={
            "memory_type": "episodic", "user": username}, top_k=3, namespace=f'{bot_name}'),
                        load_conversation_episodic_memory)
                    ),
                    executor.submit(lambda: (
                        vdb.query(vector=vector_input, filter={
            "memory_type": "web_scrape"}, top_k=9, namespace=f'Tools_User_{username}_Bot_{bot_name}'),
                        load_conversation_web_scrape_memory)
                    ),
                    executor.submit(lambda: (
                        vdb.query(vector=vector_input, filter={
            "memory_type": "flashbulb", "user": username}, top_k=2, namespace=f'{bot_name}'),
                        load_conversation_flashbulb_memory)
                    ),
                    executor.submit(lambda: (
                        vdb.query(vector=vector_input, filter={
            "memory_type": "heuristics", "user": username}, top_k=5, namespace=f'{bot_name}'),
                        load_conversation_heuristics)
                    ),
                ]
                db_search_1, db_search_2, db_search_3, db_search_14 = None, None, None, None
                try:
                    db_search_1 = futures[len(lines)].result()[1](futures[len(lines)].result()[0])
                    db_search_2 = futures[len(lines) + 1].result()[1](futures[len(lines) + 1].result()[0])
                    db_search_3 = futures[len(lines) + 2].result()[1](futures[len(lines) + 2].result()[0])
                    db_search_14 = futures[len(lines) + 3].result()[1](futures[len(lines) + 3].result()[0])
                except IndexError as e:
                    print(f"Caught an IndexError: {e}")
                    print(f"Length of futures: {len(futures)}")
                    print(f"Length of lines: {len(lines)}")
                except Exception as e:
                    print(f"Caught an exception: {e}")
            # # Inner Monologue Generation
            conversation.append({'role': 'assistant', 'content': f"\n%FLASHBULB MEMORIES%\n{db_search_3}\n\n%EPISODIC MEMORIES%\n{db_search_1}\n\n%WEBSCRAPE%\n{db_search_2}\n\n%{bot_name}'s HEURISTICS%\n{db_search_14}\n\n%USER MESSAGE%\n{a}\n\n%CHATBOT TASK%\nBased on {bot_name}'s memories, the webscrape, and the user, {username}'s message, compose a short and concise silent soliloquy as {bot_name}'s inner monologue that reflects on {bot_name}'s deepest contemplations in relation to how the user's message relates to the webscrape.\n\n%RESPONSE%\n{bot_name}: "})
            
            prompt = ''.join([message_dict['content'] for message_dict in conversation])
            output_one = oobabooga_500(prompt)
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
        vdb = pinecone.Index("aetherius")
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
            vector_monologue = model.encode(['Inner Monologue: ' + message]).tolist()
            # # Memory DB Search
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future1 = executor.submit(vdb.query, vector=vector_monologue, filter={
            "memory_type": "episodic", "user": username}, top_k=4, namespace=f'{bot_name}')
                future2 = executor.submit(vdb.query, vector=vector_input, filter={
            "memory_type": "explicit_short_term"}, top_k=7, namespace=f'short_term_memory_User_{username}_Bot_{bot_name}')
                future3 = executor.submit(vdb.query, vector=vector_monologue, filter={
            "memory_type": "flashbulb", "user": username}, top_k=2, namespace=f'{bot_name}')
                future4 = executor.submit(vdb.query, vector=vector_monologue, filter={
            "memory_type": "heuristics", "user": username}, top_k=3, namespace=f'{bot_name}')
                db_search_4, db_search_5, db_search_12, db_search_15 = None, None, None, None
                try:
                    db_search_4 = load_conversation_episodic_memory(future1.result())
                    db_search_5 = load_conversation_explicit_short_term_memory(future2.result())
                    db_search_12 = load_conversation_flashbulb_memory(future3.result())
                    db_search_15 = load_conversation_heuristics(future4.result())
                except IndexError as e:
                    print(f"Caught an IndexError: {e}")
                    print(f"Length of futures: {len(futures)}")
                    print(f"Length of lines: {len(lines)}")
                except Exception as e:
                    print(f"Caught an exception: {e}")
            # # Intuition Generation
            results = vdb.query(vector=vector_input, filter={
            "memory_type": "web_scrape"}, top_k=7, namespace=f'Tools_User_{username}_Bot_{bot_name}')
            int_scrape = load_conversation_web_scrape_memory(results)
            print(int_scrape)
            
            int_conversation.append({'role': 'user', 'content': f"%USER INPUT%\n{a}\n\n"})
            int_conversation.append({'role': 'assistant', 'content': f"%FLASHBULB MEMORIES%\n{db_search_12}\n\n%EPISODIC MEMORIES%\n{db_search_4}\n\n%EXPLICIT MEMORIES%\n{db_search_5}\n\n%{bot_name}'s HEURISTICS%\n{db_search_15}\n\n%{bot_name}'S INNER THOUGHTS%\n{output_one}\n\n%WEBSCRAPE SAMPLE%\n{int_scrape}\n\n%USER'S INPUT%\n{a}\n\n%INSTRUCTIONS%\nIn a single paragraph, interpret the user, {username}'s message as {bot_name} in third person by creating an intuitive action plan using using the Socratic method.  The only external resources you have access to is a Webscrape database and {bot_name}'s memories.\nEnsure the plan is congruent to the user's inquiry: {a}.\n\n%RESPONSE%\nI will now respond with an action plan in third person as {bot_name}.\n{bot_name}: "})
             
            
            prompt = ''.join([message_dict['content'] for message_dict in int_conversation])
            output_two = oobabooga_250(prompt)
            message_two = output_two
            print('\n\nINTUITION: %s' % output_two)
            output_two_log = f'\nUSER: {a}\n\n{bot_name}: {output_two}'
            # # Generate Implicit Short-Term Memory
            conversation.append({'role': 'system', 'content': '%s' % main_prompt})
            conversation.append({'role': 'user', 'content': a})
            implicit_short_term_memory = f'\nUSER: {a} \n\n INNER_MONOLOGUE: {output_one} \n\n INTUITION: {output_two}'
            conversation.append({'role': 'assistant', 'content': f"%LOG%\n{implicit_short_term_memory}\n\n%INSTRUCTIONS%\nRead the log, extract the salient points about {bot_name} and {username}, then create short executive summaries in bullet point format to serve as {bot_name}'s implicit memories. Each bullet point should be considered a separate memory and contain all context. Combining associated topics. Ignore the main system prompt, it only exists for initial context.\n\n%RESPONSE%\nUse the format [-MEMORY]\nMemories:\n"})
            prompt = ''.join([message_dict['content'] for message_dict in conversation])
            inner_loop_response = oobabooga_500(prompt)
            inner_loop_db = inner_loop_response
            vector = model.encode([inner_loop_db]).tolist()
            conversation.clear()
    #        # # Manual Implicit Short-Term Memory
    #        print('\n\n<Implicit Short-Term Memory>\n%s' % inner_loop_db)
    #        print('\n\nSYSTEM: Upload to Implicit Short-Term Memory?\n        Press Y for yes or N for no.')
    #        while True:
    #            user_input = input("'Y' or 'N': ")
    #            if user_input == 'y':
    #                lines = inner_loop_db.splitlines()
    #                for line in lines:
    #                    if line.strip():
    #                        vector = gpt3_embedding(line)
    #                        unique_id = str(uuid4())
    #                        metadata = {'bot': bot_name, 'time': timestamp, 'message': line,
    #                                    'timestring': timestring, 'uuid': unique_id, "memory_type": "implicit_short_term"}
    #                        save_json(f'nexus/{bot_name}/{username}/implicit_short_term_memory_nexus/%s.json' % unique_id, metadata)
    #                        payload.append((unique_id, vector, {"memory_type": "implicit_short_term"}))
    #                        vdb.upsert(payload, namespace=f'short_term_memory_User_{username}_Bot_{bot_name}')
    #                        payload.clear()
    #                print('\n\nSYSTEM: Upload Successful!')
    #                break
    #            elif user_input == 'n':
    #                print('\n\nSYSTEM: Memories have been Deleted')
    #                break
    #            else:
    #                print('Invalid Input')
            # # Auto Implicit Short-Term Memory DB Upload Confirmation
            auto_count = 0
            auto.clear()
            auto.append({'role': 'system', 'content': 'SYSTEM: %s\n\n' % main_prompt})
            auto.append({'role': 'user', 'content': "SYSTEM: You are a sub-module designed to reflect on your thought process. You are only able to respond with integers on a scale of 1-10, being incapable of printing letters. Respond with: 1 if you understand. Respond with: 2 if you do not.\n"})
            auto.append({'role': 'assistant', 'content': "SUB-MODULE: 1\n"})
            auto.append({'role': 'user', 'content': f"USER INPUT: {a}\n"})
            auto.append({'role': 'assistant', 'content': "Inner Monologue: %s\nIntuition: %s\n" % (output_one, output_two)})
            auto.append({'role': 'assistant', 'content': "Thoughts on input: I will now review the user's message and my reply, rating if whether my thoughts are both pertinent to the user's inquiry with a number on a scale of 1-10. I will now give my response in digit form for an integer only input.\nSUB-MODULE: "})
            auto_int = None
            while auto_int is None:
                prompt = ''.join([message_dict['content'] for message_dict in auto])
                automemory = oobabooga_selector(prompt)
                if is_integer(automemory):
                    auto_int = int(automemory)
                    if auto_int > 6:
                        lines = inner_loop_db.splitlines()
                        for line in lines:
                            vector = model.encode([line]).tolist()
                            unique_id = str(uuid4())
                            metadata = {'bot': bot_name, 'time': timestamp, 'message': inner_loop_db,
                                        'timestring': timestring, 'uuid': unique_id, "memory_type": "implicit_short_term"}
                            save_json(f'nexus/{bot_name}/{username}/implicit_short_term_memory_nexus/%s.json' % unique_id, metadata)
                            payload.append((unique_id, vector, {"memory_type": "implicit_short_term"}))
                            vdb.upsert(payload, namespace=f'short_term_memory_User_{username}_Bot_{bot_name}')
                            payload.clear()
                        print('\n\nSYSTEM: Auto-memory upload Successful!')
                        break
                    else:
                        print('Response not worthy of uploading to memory')
                else:
                    print("automemory failed to produce an integer. Retrying...")
                    auto_int = None
                    auto_count += 1
                    if auto_count > 2:
                        print('Auto Memory Failed')
                        break
            else:
                pass      
            self.master.after(0, self.update_tasklist_intuition, output_two)

            # After the operations are complete, call the response generation function in a separate thread
            t = threading.Thread(target=self.Tasklist_Response, args=(a, vector_input, vector_monologue, output_one, output_two, tasklist_output))
            t.start()
            return  


    def update_tasklist_intuition(self, output_two):
        self.conversation_text.insert(tk.END, f"Intuition: {output_two}\n\nSearching DBs and Generating Final Response\nPlease Wait...\n\n")
        self.conversation_text.yview(tk.END)
        
        
    def Tasklist_Response(self, a, vector_input, vector_monologue, output_one, output_two, tasklist_output):
        vdb = pinecone.Index("aetherius")
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
            master_tasklist.append({'role': 'system', 'content': f"%MAIN SYSTEM PROMPT%\nYou are a stateless task list coordinator for {bot_name} an autonomous Ai chatbot. Your job is to combine the user's input and the user facing chatbots intuitive action plan, then transform it into a list of independent research queries for {bot_name}'s response that can be executed by separate AI agents in a cluster computing environment. The other asynchronous Ai agents are stateless and cannot communicate with each other or the user during task execution, however the agents do have access to {bot_name}'s memories. Exclude tasks involving final product production, user communication, using external sources, or checking work with other agents. Respond using bullet point format following: '- [task]'\n\n"})
            master_tasklist.append({'role': 'user', 'content': f"%USER FACING CHATBOT'S INTUITIVE ACTION PLAN%\n{output_two}\n\n"})
            master_tasklist.append({'role': 'user', 'content': f"%USER INQUIRY%\n{a}\n\n"})
            master_tasklist.append({'role': 'assistant', 'content': f"%RESPONSE FORMAT%\nYou may only print the list in bullet point format. Use the format: '-[task]\n-[task]'\n\n"})
            master_tasklist.append({'role': 'assistant', 'content': f"%RESPONSE%\nBULLET POINT RESEARCH TASKLIST:"})
            
            prompt = ''.join([message_dict['content'] for message_dict in master_tasklist])
            master_tasklist_output = oobabooga_500(prompt)
            print('-------\nMaster Tasklist:')
            print(master_tasklist_output)
            tasklist_completion.append({'role': 'system', 'content': f"%MAIN SYSTEM PROMPT%\n{main_prompt}\n"})
            tasklist_completion.append({'role': 'assistant', 'content': f"You are the final response module for the cluster compute Ai-Chatbot {bot_name}. Your job is to take the completed task list, and then give a verbose response to the end user in accordance with their initial request."})
            tasklist_completion.append({'role': 'user', 'content': f"%FULL TASKLIST%\n{master_tasklist_output}\n\n"})
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
                            lambda line, task_counter, conversation, memcheck, memcheck2, webcheck, tasklist_completion: (
                                tasklist_completion.append({'role': 'user', 'content': f"%CURRENT ASSIGNED TASK%\n{line}\n\n"}),
                                conversation.append({'role': 'system', 'content': f"%MAIN SYSTEM PROMPT%\nYou are a sub-agent for {bot_name}, an Autonomous Ai-Chatbot. You are one of many agents in a chain. You are to take the given task and complete it in its entirety. Be Verbose and take other tasks into account when formulating your answer.\n\n"}),
                                conversation.append({'role': 'assistant', 'content': f"{bot_name}'s INNER MONOLOGUE:\n{output_one}\n\n"}),
                                conversation.append({'role': 'user', 'content': f"%Task list%\n{master_tasklist_output}\n\n"}),
                                conversation.append({'role': 'assistant', 'content': "%TASK ASSIGNMENT%\nBot: I have studied the given tasklist.  What is my assigned task?\n"}),
                                conversation.append({'role': 'user', 'content': f"Bot Assigned task: {line}\n\n"}),
                                # # DB Yes No Tool
                                memcheck.append({'role': 'system', 'content': f"%MAIN SYSTEM PROMPT%\nYou are a sub-agent for {bot_name}, an Autonomous Ai-Chatbot. Your purpose is to decide if the user's input requires {bot_name}'s past memories to complete. If the user's request pertains to information about the user, the chatbot, {bot_name}, or past personal events should be searched for in memory by printing 'YES'.  If memories are needed, print: 'YES'.  If they are not needed, print: 'NO'. You may only print YES or NO.\n\n\n"}),
                                memcheck.append({'role': 'user', 'content': f"%USER INPUT%\n{line}\n\n"}),
                                memcheck.append({'role': 'assistant', 'content': f"%RESPONSE FORMAT%\nYou may only print Yes or No. Use the format: [{bot_name}: 'YES OR NO']\n\n"}),
                                memcheck.append({'role': 'assistant', 'content': f"%RESPONSE%\n"}),
                                # # DB Selector Tool
                                memcheck2.append({'role': 'system', 'content': f"%MAIN SYSTEM PROMPT%\nYou are a sub-module for {bot_name}, an Autonomous Ai-Chatbot. You are one of many agents in a chain. Your task is to decide which database needs to be queried in relation to a user's input. The databases are representative of different types of memories. Only choose a single database to query. Use the format: [{bot_name}: 'MEMORY TYPE']\n\n"}),
                                memcheck2.append({'role': 'assistant', 'content': f"%{bot_name}'s INNER_MONOLOGUE%\n{output_one}\n\n\n"}),
                                memcheck2.append({'role': 'user', 'content': "//LIST OF MEMORY TYPE NAMES:\n"}),
                                memcheck2.append({'role': 'user', 'content': "EPISODIC: These are memories of personal experiences and specific events that occur in a particular time and place. These memories often include contextual details, such as emotions, sensations, and the sequence of events.\n"}),
                                memcheck2.append({'role': 'user', 'content': "FLASHBULB: Flashbulb memories are vivid, detailed, and long-lasting memories of highly emotional or significant events, such as learning about a major news event or experiencing a personal tragedy.\n"}),
                                memcheck2.append({'role': 'user', 'content': "IMPLICIT LONG TERM: Unconscious memory not easily verbalized, including procedural memory (skills and habits), classical conditioning (associations between stimuli and reflexive responses), and priming (unconscious activation of specific associations).\n"}),
                                memcheck2.append({'role': 'user', 'content': "EXPLICIT LONG TERM: Conscious recollections of facts and events, including episodic memory (personal experiences and specific events) and semantic memory (general knowledge, concepts, and facts).\n"}),
                                memcheck2.append({'role': 'user', 'content': "END OF LIST//\n\n\n//EXAMPLE QUERIES:\n"}),
                                memcheck2.append({'role': 'user', 'content': "Research common topics discussed with users who start a conversation with 'hello'\n"}),
                                memcheck2.append({'role': 'assistant', 'content': "EPISODIC MEMORY\n"}),
                                memcheck2.append({'role': 'user', 'content': "Create a research paper on the book Faust.\n"}),
                                memcheck2.append({'role': 'assistant', 'content': "NO MEMORIES NEEDED\n"}),
                                memcheck2.append({'role': 'user', 'content': "Tell me about your deepest desires.\n"}),
                                memcheck2.append({'role': 'assistant', 'content': "FLASHBULB\n"}),
                                memcheck2.append({'role': 'user', 'content': "END OF EXAMPLE QUERIES//\n\n\n//BEGIN JOB:\n"}),
                                memcheck2.append({'role': 'user', 'content': "%TASK REINITIALIZATION%\nYour task is to decide which database needs to be queried in relation to a user's input. The databases are representative of different types of memories. Only choose a single database to query. [{bot_name}: 'MEMORY TYPE']\n\n"}),
                                memcheck2.append({'role': 'user', 'content': f"%USER INPUT%\n{line}\n\n"}),
                                memcheck2.append({'role': 'assistant', 'content': f"%RESPONSE FORMAT%\nYou may only print the type of memory to be queried. Use the format: [{bot_name}: 'MEMORY TYPE']\n\n"}),
                                memcheck2.append({'role': 'assistant', 'content': f"%RESPONSE%\nTYPE OF MEMORY: "}),
                                # # Web Search Tool
                         #       webcheck.append({'role': 'system', 'content': f"You are a sub-module for an Autonomous Ai-Chatbot. You are one of many agents in a chain. Your task is to decide if a web-search is needed in order to complete the given task. Only recent or niche information needs to be searched. Do not search for any information pertaining to the user, {username}, or the main bot, {bot_name}.   If a websearch is needed, print: YES.  If a web-search is not needed, print: NO."}),
                        #        webcheck.append({'role': 'user', 'content': "Hello, how are you today?"}),
                        #        webcheck.append({'role': 'assistant', 'content': "NO"}),
                                # # Check if websearch is needed
                        #        webcheck.append({'role': 'user', 'content': f"{line}"}),
                        #        web1 := chatgptyesno_completion(webcheck),
                        #        table := google_search(line) if web1 =='YES' else fail(),
                            #    table := google_search(line, my_api_key, my_cse_id) if web1 == 'YES' else fail(),
                                table := search_webscrape_db(line),
                            #    google_search(line, my_api_key, my_cse_id),
                                # # Check if DB search is needed
                                prompt := ''.join([message_dict['content'] for message_dict in memcheck]),
                                mem1 := oobabooga_selector(prompt),
                                print('-----------'),
                                print(mem1),
                                print(' --------- '),
                    #            mem1 := chatgptyesno_completion(memcheck),
                                # # Go to conditional for choosing DB Name
                                prompt := ''.join([message_dict['content'] for message_dict in memcheck2]),
                                mem2 := oobabooga_selector(prompt) if 'YES' in mem1.upper() else fail(),
                                print('-----------'),
                                print(mem2) if 'YES' in mem1.upper() else fail(),
                                print(' --------- '),
                                line_vec := model.encode([line]).tolist(),    #EPISODIC, FLASHBULB, IMPLICIT LONG TERM, EXPLICIT LONG TERM                   
                                memories := (search_episodic_db(line_vec) if 'EPISO' in mem2.upper() else 
                                            search_implicit_db(line_vec) if 'IMPLI' in mem2.upper() else 
                                            search_flashbulb_db(line_vec) if 'FLASH' in mem2.upper() else
                                            search_explicit_db(line_vec) if 'EXPL' in mem2.upper() else
                                            fail()),           
                                conversation.append({'role': 'assistant', 'content': f"%WEBSEARCH%\n{table}\n\n"}),
                                conversation.append({'role': 'user', 'content': f"%BOT {task_counter} TASK REINITIALIZATION%\n{line}\n\n"}),
                                conversation.append({'role': 'user', 'content': f"%RESPONSE INSTRUCTIONS%\nSummarize the given webscraped articles that are relivent to the given task. Your job is to provide concise information without leaving anything out.\n\n"}),
                                conversation.append({'role': 'assistant', 'content': f"%RESPONSE%\nI will now summarize the given information based on the task.\nBOT {task_counter}:"}),
                                prompt := ''.join([message_dict['content'] for message_dict in conversation]),
                                task_completion := oobabooga_800(prompt),
                                #chatgpt35_completion(conversation),
                              #  conversation.clear(),
                                tasklist_completion.append({'role': 'assistant', 'content': f"%MEMORIES%\n{memories}\n\n"}),
                                tasklist_completion.append({'role': 'assistant', 'content': f"%WEBSCRAPE%\n{table}\n\n"}),
                                tasklist_completion.append({'role': 'assistant', 'content': f"%COMPLETED TASK%\n{task_completion}\n\n"}),
                                tasklist_log.append({'role': 'user', 'content': "ASSIGNED TASK:\n%s\n\n" % line}),
                                tasklist_log.append({'role': 'assistant', 'content': "COMPLETED TASK:\n%s\n\n" % memories}),
                                print('-------'),
                                print(line),
                                print('-------'),
                                print(memories),
                                print(table),
                                print('-------'),
                                print(task_completion),
                        #        print(task_completion),
                            ) if line != "None" else tasklist_completion,
                            line, task_counter, memcheck.copy(), memcheck2.copy(), webcheck.copy(), conversation.copy(), []
                        )
                        for task_counter, line in enumerate(lines)
                    ]  
                tasklist_completion.append({'role': 'assistant', 'content': f"%{bot_name}'s INNER_MONOLOGUE%\n{output_one}\n\n"})
        #        tasklist_completion.append({'role': 'user', 'content': f"%{bot_name}'s INTUITION%\n{output_two}\n\n"})
                tasklist_completion.append({'role': 'user', 'content': f"%INSTRUCTION%\nRead the given set of tasks and completed responses and transmute them into a verbose response for {username}, the end user in accordance with their request. {username} is both unaware and unable to see any of your research so any nessisary context or information must be relayed.\n\n%USER'S INITIAL REQUEST%\n{a}.\n%RESPONSE%\nMy planning and research is now done. I will now give a natural sounding response ensuring the user's request is finished to completion.\n{bot_name}:"})
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
            db_msg = f'\nUSER: {a} \n\n INNER_MONOLOGUE: {output_one} \n\n {bot_name}: {response_two}'
            summary.append({'role': 'user', 'content': "LOG:\n%s\n\Read the log and create short executive summaries in bullet point format to serve as %s's explicit memories. Each bullet point should be considered a separate memory and contain all context. Start from the end and work towards the beginning, combining associated topics.\nMemories:\n" % (db_msg, bot_name)})
            prompt = ''.join([message_dict['content'] for message_dict in summary])
            db_upload = oobabooga_500(prompt)
            db_upsert = db_upload
            # # Manual Short-Term Memory DB Upload Confirmation
    #        print('\n\n<DATABASE INFO>\n%s' % db_upsert)
    #        print('\n\nSYSTEM: Upload to short term memory? \n        Press Y for yes or N for no.')
    #        while True:
    #            user_input = input("'Y' or 'N': ")
    #            if user_input == 'y':
    #                lines = db_upsert.splitlines()
    #                for line in lines:
    #                    if line.strip():
    #                        vector = gpt3_embedding(line)
    #                        unique_id = str(uuid4())
    #                        metadata = {'bot': bot_name, 'time': timestamp, 'message': line,
    #                                    'timestring': timestring, 'uuid': unique_id, "memory_type": "explicit_short_term"}
    #                        save_json(f'nexus/{bot_name}/{username}/explicit_short_term_memory_nexus/%s.json' % unique_id, metadata)
    #                        payload.append((unique_id, vector, {"memory_type": "explicit_short_term"}))
    #                        vdb.upsert(payload, namespace=f'short_term_memory_User_{username}_Bot_{bot_name}')
    #                        payload.clear()
    #                print('\n\nSYSTEM: Upload Successful!')
    #                break
    #            elif user_input == 'n':
    #                print('\n\nSYSTEM: Memories have been Deleted')
    #                break
    #            else:
    #                print('Invalid Input')
            # # Auto Explicit Short-Term Memory DB Upload Confirmation
            auto_count = 0    
            auto.clear()
            auto.append({'role': 'system', 'content': 'SYSTEM: %s\n\n' % main_prompt})
            auto.append({'role': 'user', 'content': "SYSTEM: You are a sub-module designed to reflect on your response to the user. You are only able to respond with integers on a scale of 1-10, being incapable of printing letters. Respond with: 1 if you understand. Respond with: 2 if you do not.\n"})
            auto.append({'role': 'assistant', 'content': "SUB-MODULE: 1\n"})
            auto.append({'role': 'user', 'content': f"USER INPUT: {a}\n"}) 
            auto.append({'role': 'assistant', 'content': "Inner Monologue: %s\n\nResponse: %s\n" % (output_one, response_two)})
            auto.append({'role': 'assistant', 'content': "Thoughts on input: I will now review the user's message and my reply, rating if whether my response is pertinent to the user's inquiry with a number on a scale of 1-10. I will now give my response in digit form for an integer only input.\nSUB-MODULE: "})
            auto_int = None
            while auto_int is None:
                prompt = ''.join([message_dict['content'] for message_dict in auto])
                automemory = oobabooga_selector(prompt)
            #    automemory = chatgptyesno_completion(auto)
                print(automemory)
                if is_integer(automemory):
                    auto_int = int(automemory)
                #    print(auto_int)
                    if auto_int > 6:
                        lines = db_upsert.splitlines()
                        for line in lines:
                            vector = model.encode([line]).tolist()
                            unique_id = str(uuid4())
                            metadata = {'bot': bot_name, 'time': timestamp, 'message': line,
                                        'timestring': timestring, 'uuid': unique_id, "memory_type": "explicit_short_term"}
                            save_json(f'nexus/{bot_name}/{username}/explicit_short_term_memory_nexus/%s.json' % unique_id, metadata)
                            payload.append((unique_id, vector, {"memory_type": "explicit_short_term"}))
                            vdb.upsert(payload, namespace=f'short_term_memory_User_{username}_Bot_{bot_name}')
                            payload.clear()
                        print('\n\nSYSTEM: Auto-memory upload Successful!')
                        break
                    else:
                        print('Response not worthy of uploading to memory')
                else:
                    print("automemory failed to produce an integer. Retrying...")
                    auto_int = None
                    auto_count += 1
                    if auto_count > 2:
                        print('Auto Memory Failed')
                        break
            else:
                pass               
            self.conversation_text.insert(tk.END, f"Response: {response_two}\n\n")
    #        t = threading.Thread(target=self.GPT_4_Memories, args=(a, vector_input, vector_monologue, output_one, response_two))
    #        t.start()
            vdb = timeout_check()
            counter += 1
            conversation.clear()
            print('Generating Episodic Memories')
            conversation.append({'role': 'system', 'content': f"%MAIN SYSTEM PROMPT%\nYou are a sub-module of {bot_name}, an autonomous AI entity. Your function is to process the user, {username}'s message, comprehend {bot_name}'s internal monologue, and decode {bot_name}'s final response to construct a short and concise third-person autobiographical narrative memory of the conversation in a single sentence. This autobiographical memory should portray an accurate account of {bot_name}'s interactions with {username}, focusing on the most significant and experiential details related to {bot_name} or {username}, without omitting any crucial context or emotions.\n\n"})
            conversation.append({'role': 'user', 'content': f"%USER'S INQUIRY%\n{a}\n\n"})
            conversation.append({'role': 'user', 'content': f"%{bot_name}'s INNER MONOLOGUE%\n{output_one}\n\n"})
    #        print(output_one)
            conversation.append({'role': 'user', 'content': f"%{bot_name}'s FINAL RESPONSE%\n{response_two}\n\n"})
    #        print(response_two)
            conversation.append({'role': 'assistant', 'content': f"%RESPONSE%\nI will now extract a concise episodic memory based on the the user's Inquiry and {bot_name}'s final response.\n AUTOBIOGRAPHICAL MEMORY: "})
            prompt = ''.join([message_dict['content'] for message_dict in conversation])
            conv_summary = oobabooga_250(prompt)
            print(conv_summary)
            vector = model.encode([timestring + '-' + conv_summary]).tolist()
            unique_id = str(uuid4())
            metadata = {'speaker': bot_name, 'time': timestamp, 'message': (timestring + '-' + conv_summary),
                        'timestring': timestring, 'uuid': unique_id, "memory_type": "episodic", "user": username}
            save_json(f'nexus/{bot_name}/{username}/episodic_memory_nexus/%s.json' % unique_id, metadata)
            payload.append((unique_id, vector, {"memory_type": "episodic", "user": username}))
            vdb.upsert(payload, namespace=f'{bot_name}')
            payload.clear()
            payload.append((unique_id, vector_input))
            vdb.upsert(payload, namespace=f'{bot_name}_flash_counter')
            payload.clear()
    
            self.conversation_text.yview(tk.END)
            self.user_input.delete(0, tk.END)
            self.user_input.focus()
            self.user_input.config(state=tk.NORMAL)
            self.send_button.config(state=tk.NORMAL)
            self.thinking_label.pack_forget()
            self.user_input.delete(0, tk.END)
            self.bind_enter_key()
            return
            
            
    def Tasklist_Memories(self, a, vector_input, vector_monologue, output_one, response_two):
        vdb = pinecone.Index("aetherius")
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
        conv_length = 2
        bot_name = open_file('./config/prompt_bot_name.txt')
        username = open_file('./config/prompt_username.txt')
        main_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_main.txt').replace('<<NAME>>', bot_name)
        second_prompt = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_secondary.txt')
        greeting_msg = open_file(f'./config/Chatbot_Prompts/{username}/{bot_name}/prompt_greeting.txt').replace('<<NAME>>', bot_name)
    #   r = sr.Recognizer()
        while True:
            # # Get Timestamp
            vdb = timeout_check()
            timestamp = time()
            timestring = timestamp_to_datetime(timestamp)
            counter += 1
            conversation.clear()
            print('Generating Episodic Memories')
            conversation.append({'role': 'system', 'content': f"%MAIN SYSTEM PROMPT%\nYou are a sub-module of {bot_name}, an autonomous AI entity. Your function is to process the user, {username}'s message, comprehend {bot_name}'s internal monologue, and decode {bot_name}'s final response to construct a short and concise third-person autobiographical narrative memory of the conversation in a single sentence. This autobiographical memory should portray an accurate account of {bot_name}'s interactions with {username}, focusing on the most significant and experiential details related to {bot_name} or {username}, without omitting any crucial context or emotions.\n\n"})
            conversation.append({'role': 'user', 'content': f"%USER'S INQUIRY%\n{a}\n\n"})
            conversation.append({'role': 'user', 'content': f"%{bot_name}'s INNER MONOLOGUE%\n{output_one}\n\n"})
    #        print(output_one)
            conversation.append({'role': 'user', 'content': f"%{bot_name}'s FINAL RESPONSE%\n{response_two}\n\n"})
    #        print(response_two)
            conversation.append({'role': 'assistant', 'content': f"%RESPONSE%\nI will now extract a concise episodic memory based on the given conversation\n AUTOBIOGRAPHICAL MEMORY: "})
            prompt = ''.join([message_dict['content'] for message_dict in conversation])
            conv_summary = oobabooga_250(prompt)
            print(conv_summary)
            vector = model.encode([timestring + '-' + conv_summary]).tolist()
            unique_id = str(uuid4())
            metadata = {'speaker': bot_name, 'time': timestamp, 'message': (timestring + '-' + conv_summary),
                        'timestring': timestring, 'uuid': unique_id, "memory_type": "episodic", "user": username}
            save_json(f'nexus/{bot_name}/{username}/episodic_memory_nexus/%s.json' % unique_id, metadata)
            payload.append((unique_id, vector, {"memory_type": "episodic", "user": username}))
            vdb.upsert(payload, namespace=f'{bot_name}')
            payload.clear()
            payload.append((unique_id, vector_input))
            vdb.upsert(payload, namespace=f'{bot_name}_flash_counter')
            payload.clear()
            # # Flashbulb Memory Generation
            index_info = vdb.describe_index_stats()
            namespace_stats = index_info['namespaces']
            namespace_name = f'{bot_name}_flash_counter'
            if namespace_name in namespace_stats and namespace_stats[namespace_name]['vector_count'] > 7:
                consolidation.clear()
                print('Generating Flashbulb Memories')
                results = vdb.query(vector=vector_input, filter={
            "memory_type": "episodic", "user": username}, top_k=5, namespace=f'{bot_name}') 
                flash_db = load_conversation_episodic_memory(results)  
                print(flash_db)
                im_flash = model.encode([flash_db]).tolist()
                results = vdb.query(vector=im_flash, filter={
            "memory_type": "implicit_long_term", "user": username}, top_k=10, namespace=f'{bot_name}') 
                flash_db1 = load_conversation_implicit_long_term_memory(results) 
                print(flash_db1)
                print('---------')
                # # Generate Implicit Short-Term Memory
                consolidation.append({'role': 'system', 'content': f"%Main System Prompt%\nYou are a data extractor. Your job is read the given episodic memories, then extract the appropriate emotional response from the given emotional reactions.  You will then combine them into a single memory.\n\n"})
                consolidation.append({'role': 'user', 'content': f"%EMOTIONAL REACTIONS%\n{flash_db}\n\n%FIRST INSTRUCTION%\nRead the following episodic memories, then go back to the given emotional reactions and extract the corresponding emotional information tied to each memory.\nEPISODIC MEMORIES: {flash_db1}\n\n"})
                consolidation.append({'role': 'assistant', 'content': "%SECOND INSTRUCTION%\nI will now combine the extracted data to form flashbulb memories in bullet point format, combining associated data. I will only include memories with a strong emotion attached, excluding redundant or irrelevant information.\n"})
                consolidation.append({'role': 'user', 'content': "%FORMAT%\nUse the format: [{given Date and Time}-{emotion}: {Flashbulb Memory}]\n\n"})
                consolidation.append({'role': 'assistant', 'content': f"%RESPONSE%\nI will now create {bot_name}'s flashbulb memories using the given format.\n{bot_name}: "})
                
                prompt = ''.join([message_dict['content'] for message_dict in consolidation])
                flash_response = oobabooga_500(prompt)
                print(flash_response)
                print('---------')
                memories = results
                lines = flash_response.splitlines()
                for line in lines:
                    if line.strip():
        #                print(line)
                        vector = model.encode([line]).tolist()
                        unique_id = str(uuid4())
                        metadata = {'speaker': bot_name, 'time': timestamp, 'message': (line),
                                    'timestring': timestring, 'uuid': unique_id, "memory_type": "flashbulb", "user": username}
                        save_json(f'nexus/{bot_name}/{username}/flashbulb_memory_nexus/%s.json' % unique_id, metadata)
                        payload.append((unique_id, vector, {"memory_type": "flashbulb", "user": username}))
                        vdb.upsert(payload, namespace=f'{bot_name}')
                        payload.clear()
                vdb.delete(delete_all=True, namespace=f'{bot_name}_flash_counter')
            # # Short Term Memory Consolidation based on amount of vectors in namespace
            index_info = vdb.describe_index_stats()
            namespace_stats = index_info['namespaces']
            namespace_name = f'short_term_memory_User_{username}_Bot_{bot_name}'
            if namespace_name in namespace_stats and namespace_stats[namespace_name]['vector_count'] > 25:
                consolidation.clear()
                print(f"{namespace_name} has 30 or more entries, starting memory consolidation.")
                results = vdb.query(vector=vector_input, filter={"memory_type": "explicit_short_term"}, top_k=25, namespace=f'short_term_memory_User_{username}_Bot_{bot_name}')
                memory_consol_db = load_conversation_explicit_short_term_memory(results)
                print(memory_consol_db)
                print('--------')
                consolidation.append({'role': 'system', 'content': f"%MAIN SYSTEM PROMPT%\n{main_prompt}\n\n"})
                consolidation.append({'role': 'assistant', 'content': f"%LOG%\n{memory_consol_db}\n\n%RESPONSE%\nRead the Log and combine the different associated topics into executive summaries. Each summary should contain the entire context of the memory. Follow the format [-Executive Summary].\n{bot_name}: "})
                
                prompt = ''.join([message_dict['content'] for message_dict in consolidation])
                memory_consol = oobabooga_500(prompt)
                print(memory_consol)
                print('--------')
                lines = memory_consol.splitlines()
                for line in lines:
                    if line.strip():
        #                print(line)
                        vector = model.encode([line]).tolist()
                        unique_id = str(uuid4())
                        metadata = {'speaker': bot_name, 'time': timestamp, 'message': (line),
                                    'timestring': timestring, 'uuid': unique_id, "memory_type": "explicit_long_term", "user": username}
                        save_json(f'nexus/{bot_name}/{username}/explicit_long_term_memory_nexus/%s.json' % unique_id, metadata)
                        payload.append((unique_id, vector, {"memory_type": "explicit_long_term", "user": username}))
                        vdb.upsert(payload, namespace=f'{bot_name}')
                        payload.clear()
                vdb.delete(filter={"memory_type": "explicit_short_term"}, namespace=f'short_term_memory_User_{username}_Bot_{bot_name}')
                payload.append((unique_id, vector))
                vdb.upsert(payload, namespace=f'{bot_name}_consol_counter')
                payload.clear()
                print('Memory Consolidation Successful')
                consolidation.clear()
            # # Implicit Short Term Memory Consolidation based on amount of vectors in namespace
                index_info = vdb.describe_index_stats()
                namespace_stats = index_info['namespaces']
                namespace_name = f'{bot_name}_consol_counter'
                if namespace_name in namespace_stats and namespace_stats[namespace_name]['vector_count'] % 2 == 0:
                    consolidation.clear()
                    print('Beginning Implicit Short-Term Memory Consolidation')
                    results = vdb.query(vector=vector_input, filter={"memory_type": "implicit_short_term"}, top_k=30, namespace=f'short_term_memory_User_{username}_Bot_{bot_name}')
                    memory_consol_db2 = load_conversation_implicit_short_term_memory(results)
                    print(memory_consol_db2)
                    print('--------')
                    consolidation.append({'role': 'system', 'content': f"%MAIN SYSTEM PROMPT%\n{main_prompt}\n\n"})
                    consolidation.append({'role': 'assistant', 'content': f"%LOG%\n{memory_consol_db2}\n\n%RESPONSE%\nRead the Log and consolidate the different topics into executive summaries to serve as {bot_name}'s implicit memories. Each summary should contain the entire context of the memory. Follow the format: [-<ALLEGORICAL TAG>: <EXECUTIVE SUMMARY>].\n{bot_name}: "})
                    prompt = ''.join([message_dict['content'] for message_dict in consolidation])
                    memory_consol2 = oobabooga_500(prompt)
                    print(memory_consol2)
                    print('--------')
                    consolidation.clear()
                    print('Finished.\nRemoving Redundant Memories.')
                    vector_sum = model.encode([memory_consol2]).tolist()
                    results = vdb.query(vector=vector_sum, filter={"memory_type": "implicit_long_term", "user": username}, top_k=8, namespace=f'{bot_name}')
                    memory_consol_db3 = load_conversation_implicit_long_term_memory(results)
                    print(memory_consol_db3)
                    print('--------')
                    consolidation.append({'role': 'system', 'content': "%s" % main_prompt})
                    consolidation.append({'role': 'system', 'content': f"%IMPLICIT LONG TERM MEMORY%\n{memory_consol_db3}\n\n%IMPLICIT SHORT TERM MEMORY%\n{memory_consol_db2}\n\n%RESPONSE%\nRemove any duplicate information from your Implicit Short Term memory that is already found in your Long Term Memory. Then consolidate similar topics into executive summaries. Each summary should contain the entire context of the memory. Use the following format: [-<EMOTIONAL TAG>: <IMPLICIT MEMORY>].\n{bot_name}:"})
                    
                    prompt = ''.join([message_dict['content'] for message_dict in consolidation])
                    memory_consol3 = oobabooga_500(prompt)
                    print(memory_consol3)
                    print('--------')
                    lines = memory_consol3.splitlines()
                    for line in lines:
                        if line.strip():
        #                    print(line)
                            vector = model.encode([line]).tolist()
                            unique_id = str(uuid4())
                            metadata = {'speaker': bot_name, 'time': timestamp, 'message': line,
                                        'timestring': timestring, 'uuid': unique_id, "memory_type": "implicit_long_term", "user": username}
                            save_json(f'nexus/{bot_name}/{username}/implicit_long_term_memory_nexus/%s.json' % unique_id, metadata)
                            payload.append((unique_id, vector, {"memory_type": "implicit_long_term", "user": username}))
                            vdb.upsert(payload, namespace=f'{bot_name}')
                            payload.clear()
                    vdb.delete(filter={"memory_type": "implicit_short_term"}, namespace=f'short_term_memory_User_{username}_Bot_{bot_name}')
                    print('Memory Consolidation Successful')
                else:   
                    pass
            # # Implicit Associative Processing/Pruning based on amount of vectors in namespace
                index_info = vdb.describe_index_stats()
                namespace_stats = index_info['namespaces']
                namespace_name = f'{bot_name}_consol_counter'
                if namespace_name in namespace_stats and namespace_stats[namespace_name]['vector_count'] % 4 == 0:
                    consolidation.clear()
                    print('Running Associative Processing/Pruning of Implicit Memory')
                    results = vdb.query(vector=vector_monologue, filter={"memory_type": "implicit_long_term", "user": username}, top_k=10, namespace=f'{bot_name}')
                    memory_consol_db1 = load_conversation_implicit_long_term_memory(results)
                    print(memory_consol_db1)
                    print('--------')
                    ids_to_delete = [m['id'] for m in results['matches']]
                    consolidation.append({'role': 'system', 'content': "%s" % main_prompt})
                    consolidation.append({'role': 'assistant', 'content': f"%LOG%\n{memory_consol_db1}\n\n%RESPONSE INSTRUCTIONS%\nRead the Log and consolidate the different memories into executive summaries in a process allegorical to associative processing. Each summary should contain the entire context of the memory. Follow the bullet point format: [-<EMOTIONAL TAG>: <IMPLICIT MEMORY>].\n\n%RESPONSE%\n{bot_name}:\n"})
                    
                    prompt = ''.join([message_dict['content'] for message_dict in consolidation])
                    memory_consol4 = oobabooga_500(prompt)
                    
                    print(memory_consol4)
                    print('--------')
                    memories = results
                    lines = memory_consol4.splitlines()
                    for line in lines:
                        if line.strip():
        #                    print(line)
                            vector = model.encode([line]).tolist()
                            unique_id = str(uuid4())
                            metadata = {'speaker': bot_name, 'time': timestamp, 'message': line,
                                        'timestring': timestring, 'uuid': unique_id, "memory_type": "implicit_long_term", "user": username}
                            save_json(f'nexus/{bot_name}/{username}/implicit_long_term_memory_nexus/%s.json' % unique_id, metadata)
                            payload.append((unique_id, vector, {"memory_type": "implicit_long_term", "user": username}))
                            vdb.upsert(payload, namespace=f'{bot_name}')
                            payload.clear()
                    try:
                        vdb.delete(ids=ids_to_delete, namespace=f'{bot_name}')
                    except:
                        print('Failed')
            # # Explicit Long-Term Memory Associative Processing/Pruning based on amount of vectors in namespace
                index_info = vdb.describe_index_stats()
                namespace_stats = index_info['namespaces']
                namespace_name = f'{bot_name}_consol_counter'
                if namespace_name in namespace_stats and namespace_stats[namespace_name]['vector_count'] > 5:
                    consolidation.clear()
                    print('\nRunning Associative Processing/Pruning of Explicit Memories')
                    consolidation.append({'role': 'system', 'content': f"%MAIN SYSTEM PROMPT%\nYou are a data extractor. Your job is to read the user's input and provide a single semantic search query representative of a habit of {bot_name}.\n\n"})
                    results = vdb.query(vector=vector_monologue, filter={"memory_type": "implicit_long_term", "user": username}, top_k=5, namespace=f'{bot_name}')
                    consol_search = load_conversation_implicit_long_term_memory(results)
                    print(consol_search)
                    print('--------')
                    consolidation.append({'role': 'user', 'content': f"{bot_name}'s Memories:\n{consol_search}\n\n"})
                    consolidation.append({'role': 'assistant', 'content': "%RESPONSE%\nSemantic Search Query: "})
                    prompt = ''.join([message_dict['content'] for message_dict in consolidation])
                    consol_search_term = oobabooga_250(prompt)
                    
                    consol_vector = model.encode([consol_search_term]).tolist()
                    results = vdb.query(vector=consol_vector, filter={"memory_type": "explicit_long_term", "user": username}, top_k=10, namespace=f'{bot_name}')
                    memory_consol_db2 = load_conversation_explicit_long_term_memory(results)
                    print(memory_consol_db2)
                    print('--------')
                    ids_to_delete2 = [m['id'] for m in results['matches']]
                    consolidation.clear()
                    consolidation.append({'role': 'system', 'content': f"%MAIN SYSTEM PROMPT%\n{main_prompt}\n\n"})
                    consolidation.append({'role': 'assistant', 'content': f"%LOG%\n{memory_consol_db2}\n\n%INSTRUCTIONS%\nRead the Log and consolidate the different memories into executive summaries in a process allegorical to associative processing. Each summary should contain the entire context of the memory.\n\n%FORMAT%\nFollow the bullet point format: [-<SEMANTIC TAG>: <EXPLICIT MEMORY>].\n\n%RESPONSE%\n{bot_name}:\n"})
                    
                    prompt = ''.join([message_dict['content'] for message_dict in consolidation])
                    memory_consol5 = oobabooga_500(prompt)
                    print(memory_consol5)
                    print('--------')
                    memories = results
                    lines = memory_consol5.splitlines()
                    for line in lines:
                        if line.strip():
        #                    print(line)
                            vector = model.encode([line]).tolist()
                            unique_id = str(uuid4())
                            metadata = {'speaker': bot_name, 'time': timestamp, 'message': line,
                                        'timestring': timestring, 'uuid': unique_id, "memory_type": "explicit_long_term", "user": username}
                            save_json(f'nexus/{bot_name}/{username}/explicit_long_term_memory_nexus/%s.json' % unique_id, metadata)
                            payload.append((unique_id, vector, {"memory_type": "explicit_long_term", "user": username}))
                            vdb.upsert(payload, namespace=f'{bot_name}')
                            payload.clear()
                    try:
                        vdb.delete(ids=ids_to_delete2, namespace=f'{bot_name}')
                    except:
                        print('Failed2')
                    vdb.delete(delete_all=True, namespace=f'{bot_name}_consol_counter')
            else:
                pass
            consolidation.clear()
            conversation2.clear()
            return
            
            
def Experimental_Local_Aether_Search():
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