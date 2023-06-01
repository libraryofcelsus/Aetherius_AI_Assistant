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
from basic_functions import *
from gpt_4 import *
import requests
import multiprocessing
import concurrent.futures
import shutil
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from ebooklib import epub
# import speech_recognition as sr
# from gtts import gTTS
# from playsound import playsound
# import pyttsx3
# from pydub import AudioSegment
# from pydub.playback import play
# from pydub import effects
  

def chatgptselector_completion(messages, model="gpt-3.5-turbo", temp=0.2):
    max_retry = 7
    retry = 0
    m = multiprocessing.Manager()
    lock = m.Lock()
    with lock:
        try:
            response = openai.ChatCompletion.create(model=model, messages=messages, max_tokens=4)
            text = response['choices'][0]['message']['content']
            temperature = temp
        #    filename = '%s_chat.txt' % time()
        #    if not os.path.exists('chat_logs'):
        #        os.makedirs('chat_logs')
        #    save_file('chat_logs/%s' % filename, str(messages) + '\n\n==========\n\n' + text)
            print(text)
            return text
        except Exception as oops:
            retry += 1
            if retry >= max_retry:
                print(f"Exiting due to an error in ChatGPT: {oops}")
                exit(1)
            print(f'Error communicating with OpenAI: "{oops}" - Retrying in {2 ** (retry - 1) * 5} seconds...')
            sleep(2 ** (retry - 1) * 5)

    
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


def chunk_text_from_url(url, chunk_size=1000, overlap=200):
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
            websum.append({'role': 'system', 'content': "You are a Data Extractor sub-module.  You are responsible for processing text data about a role or person from web scrapes. Your tasks include identifying and highlighting significant or factual information pertaining to the most salient role or person of the given information. Website specific and Extraneous data should be discarded, and only essential details must be returned. Stick to the data provided; do not infer or generalize. Present your responses in a Running Text format. Refrain from using linebreaks within the content. Convert lists into continuous text to maintain this format. Note that the semantic question label should be a question that corresponds to the information within the article chunk.\n\nUse the following response structure:\n-[{SEMANTIC QUESTION LABEL}:{ARTICLE/INFORMATION}].\nEach chunk summary should be contained in a single paragraph. Without linebreaks between the tag and article."})
            websum.append({'role': 'user', 'content': f"ARTICLE CHUNK: {chunk}"})
            text = chatgpt35_completion(websum)
            paragraphs = text.split('\n\n')  # Split into paragraphs
            for paragraph in paragraphs:  # Process each paragraph individually, add a check to see if paragraph contained actual information.
                webcheck = list()
                weblist.append(url + ' ' + paragraph)
                webcheck.append({'role': 'system', 'content': f"You are an agent for an automated webscraping tool. You are one of many agents in a chain. Your task is to decide if the given text from a webscrape was scraped successfully. The scraped text should contain factual data or opinions pertaining to a role or character. If the given data consists of general website info or only contains a question, skip it.  If the article was scraped successfully, print: YES.  If a web-search is not needed, print: NO."})
                webcheck.append({'role': 'user', 'content': f"Is the scraped information useful to an end-user? YES/NO: {paragraph}"})
                webyescheck = chatgptyesno_completion(webcheck)
                if webyescheck == 'YES':
                    print('---------')
                    print(paragraph)
                    payload = list()
                    vector = gpt3_embedding(paragraph)
                    timestamp = time()
                    timestring = timestamp_to_datetime(timestamp)
                    unique_id = str(uuid4())
                    metadata = {'bot': bot_name, 'time': timestamp, 'message': paragraph,
                                'timestring': timestring, 'uuid': unique_id}
                    save_json(f'nexus/{bot_name}/{username}/role_extraction_nexus/%s.json' % unique_id, metadata)
                    payload.append((unique_id, vector))
                    vdb.upsert(payload, namespace=f'role_extractor_{username}')
                    payload.clear()
        table = weblist
        return table
    except Exception as e:
        print(e)
        table = "Error"
        return table  
        
        
def load_conversation_web_scrape_memory(results):
    username = open_file('./config/prompt_username.txt')
    bot_name = open_file('./config/prompt_bot_name.txt')
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
    username = open_file('./config/prompt_username.txt')
    bot_name = open_file('./config/prompt_bot_name.txt')
    vdb = pinecone.Index("aetherius")
    try:
        with lock:
            line_vec = gpt3_embedding(line)
            results = vdb.query(vector=line_vec, filter={
        "memory_type": "web_scrape"}, top_k=30, namespace=f'short_term_memory_User_{username}_Bot_{bot_name}')
            table = load_conversation_web_scrape_memory(results)
            return table
    except Exception as e:
        print(e)
        table = "Error"
        return table



def chunk_text_from_file(file_path, chunk_size=1300, overlap=150):
    try:
        print("Reading given file, please wait...")
        bot_name = open_file('./config/prompt_bot_name.txt')
        username = open_file('./config/prompt_username.txt')
        vdb = pinecone.Index("aetherius")
        file_extension = os.path.splitext(file_path)[1]
        if file_extension == '.txt':
            with open(file_path, 'r') as file:
                texttemp = file.read().replace('\n', ' ').replace('\r', '')
        elif file_extension == '.pdf':
            with open(file_path, 'rb') as file:
                pdf = PdfFileReader(file)
                texttemp = " ".join(page.extract_text() for page in pdf.pages)
        elif file_extension == '.epub':
            book = epub.read_epub(file_path)
            texts = []
            for item in book.get_items_of_type(9):  # type 9 is XHTML
                soup = BeautifulSoup(item.content, 'html.parser')
                texts.append(soup.get_text())
            texttemp = ' '.join(texts)
        else:
            print(f"Unsupported file type: {file_extension}")
            return []
        texttemp = '\n'.join(line for line in texttemp.splitlines() if line.strip())
        chunks = chunk_text(texttemp, chunk_size, overlap)
        filelist = list()
        for chunk in chunks:
            filesum = list()
            filesum.append({'role': 'system', 'content': "You are a Data Summarizer sub-module, responsible for processing text data from files. Your role includes identifying and highlighting significant or factual information. Extraneous data should be discarded, and only essential details must be returned. Stick to the data provided; do not infer or generalize.  Convert lists into a continuous text summary to maintain this format. Present your responses in a Running Text format using the following pattern: [SEMANTIC QUESTION TAG:SUMMARY]. Note that the semantic question tag should be a question that corresponds to the paired information within the summary. Always provide the two together without linebreaks."})
            filesum.append({'role': 'user', 'content': f"TEXT CHUNK: {chunk}"})
            text = chatgpt35_completion(filesum)
            paragraphs = text.split('\n\n')  # Split into paragraphs
            for paragraph in paragraphs:  # Process each paragraph individually, add a check to see if paragraph contained actual information.
                filecheck = list()
                filelist.append(file_path + ' ' + paragraph)
                filecheck.append({'role': 'system', 'content': f"You are an agent for an automated text-processing tool. You are one of many agents in a chain. Your task is to decide if the given text from a file was processed successfully. The processed text should contain factual data or opinions. If the given data only consists of an error message or a single question, skip it.  If the article was processed successfully, print: YES.  If a file-process is not needed, print: NO."})
                filecheck.append({'role': 'user', 'content': f"Is the processed information useful to an end-user? YES/NO: {paragraph}"})
                fileyescheck = chatgptyesno_completion(filecheck)
                if fileyescheck == 'YES':
                    print('---------')
                    print(file_path + ' ' + paragraph)
                    payload = list()
                    vector = gpt3_embedding(file_path + ' ' + paragraph)
                    timestamp = time()
                    timestring = timestamp_to_datetime(timestamp)
                    unique_id = str(uuid4())
                    metadata = {'bot': bot_name, 'time': timestamp, 'message': file_path + ' ' + paragraph,
                                'timestring': timestring, 'uuid': unique_id, "memory_type": "file_process"}
                    save_json(f'nexus/file_process_memory_nexus/%s.json' % unique_id, metadata)
                    payload.append((unique_id, vector, {"memory_type": "file_process"}))
                    vdb.upsert(payload, namespace=f'short_term_memory_User_{username}_Bot_{bot_name}')
                    payload.clear()
                    filecheck.clear()
        table = filelist
        return table
    except Exception as e:
        print(e)
        table = "Error"
        return table  
                      
                      
def process_files_in_directory(directory_path, finished_directory_path, chunk_size=1000, overlap=100):
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
            info = load_json('nexus/file_process_memory_nexus/%s.json' % m['id'])
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
    vdb = pinecone.Index("aetherius")
    try:
        with lock:
            line_vec = gpt3_embedding(line)
            results = vdb.query(vector=line_vec, filter={
        "memory_type": "file_process"}, top_k=30, namespace=f'short_term_memory_User_{username}_Bot_{bot_name}')
            table = load_conversation_file_process_memory(results)
            return table
    except Exception as e:
        print(e)
        table = "Error"
        return table
        
        
def load_conversation_role_extraction(results):
    username = open_file('./config/prompt_username.txt')
    bot_name = open_file('./config/prompt_bot_name.txt')
    try:
        result = list()
        for m in results['matches']:
            info = load_json(f'nexus/{bot_name}/{username}/role_extraction_nexus/%s.json' % m['id'])
            result.append(info)
        ordered = sorted(result, key=lambda d: d['time'], reverse=False)  # sort them all chronologically
        messages = [i['message'] for i in ordered]
        return '\n'.join(messages).strip()
    except Exception as e:
        print(e)
        table = "Error"
        return table
         
         
         
def process_line(line, vdb, extractor_questions, gpt3_embedding, chatgptresponse_completion, save_json, timestamp_to_datetime, bot_name, user_selection):
    question_list = list()
    question_list2 = list()
    question_list3 = list()
    line_vec = gpt3_embedding(line)
    question_list.append({'role': 'system', 'content': "You are a sub-module in an autonomous role extractor. Your job is to take the given database queries and extract information of the most salient role or person. The info will be used to form memories for the main chatbot nexus.  The memories should be in relation to the given question from the system."})
    results = vdb.query(vector=line_vec, top_k=22, namespace=f'role_extractor_{username}')
    question_db = load_conversation_role_extraction(results)
    question_list.append({'role': 'assistant', 'content': f'DATABASE QUERIES: {question_db}'})
    question_list.append({'role': 'user', 'content': f'SYSTEM QUESTION: {line}'})
    question_response = chatgptresponse_completion(question_list)
    question_list2.append({'role': 'system', 'content': "You are a sub-module in an autonomous role extractor. Your job is to take the given database query and extract the needed information to form first person memories for the main chatbot nexus.  Take the given response and extract implicit memories. Each memory should be given in first person as the most salient role or character and in bullet point format."})
    question_list2.append({'role': 'assistant', 'content': f'RESPONSE: {question_response}'})
    question_response2 = chatgptresponse_completion(question_list2)
    lines = question_response2.splitlines()
    for line in lines:
        print(line)
        payload = list()
        vector = gpt3_embedding(line)
        timestamp = time()
        timestring = timestamp_to_datetime(timestamp)
        unique_id = str(uuid4())
        metadata = {'bot': bot_name, 'time': timestamp, 'message': line,
                    'timestring': timestring, 'uuid': unique_id, "memory_type": "implicit_long_term", "user": username}
        save_json(f'nexus/{bot_name}/{username}/implicit_long_term_memory_nexus/%s.json' % unique_id, metadata)
        payload.append((unique_id, vector, {"memory_type": "implicit_long_term", "user": username}))
        vdb.upsert(payload, namespace=f'{user_selection}')
        payload.clear()
    question_list3.append({'role': 'system', 'content': "You are a sub-module in an autonomous role extractor. Your job is to take the given database query and extract the needed information to form first person memories for the main chatbot nexus as the given role or person.  Take the given response and extract explicit memories. Each memory should be given in first person as the most salient role or character and in bullet point format."})
    question_list3.append({'role': 'assistant', 'content': f'RESPONSE: {question_response}'})
    question_response3 = chatgptresponse_completion(question_list2)
    lines = question_response3.splitlines()
    for line in lines:
        print(line)
        payload = list()
        vector = gpt3_embedding(line)
        timestamp = time()
        timestring = timestamp_to_datetime(timestamp)
        unique_id = str(uuid4())
        metadata = {'bot': bot_name, 'time': timestamp, 'message': line,
                    'timestring': timestring, 'uuid': unique_id, "memory_type": "explicit_long_term", "user": username}
        save_json(f'nexus/{bot_name}/{username}/explicit_long_term_memory_nexus/%s.json' % unique_id, metadata)
        payload.append((unique_id, vector, {"memory_type": "explicit_long_term", "user": username}))
        vdb.upsert(payload, namespace=f'{user_selection}')
        payload.clear()
    question_list.clear()
    question_list2.clear()
    question_list3.clear()


def GPT_4_Role_Extractor():
    vdb = pinecone.Index("aetherius")
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
    if not os.path.exists(f'nexus/{bot_name}/{username}/web_scrape_memory_nexus'):
        os.makedirs(f'nexus/{bot_name}/{username}/web_scrape_memory_nexus')
    if not os.path.exists(f'nexus/{bot_name}/{username}/role_extraction_nexus'):
        os.makedirs(f'nexus/{bot_name}/{username}/role_extraction_nexus')
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
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
    main_prompt = open_file('./config/Chatbot_Prompts/prompt_main.txt').replace('<<NAME>>', bot_name)
    second_prompt = open_file('./config/Chatbot_Prompts/prompt_secondary.txt')
    greeting_msg = open_file('./config/Chatbot_Prompts/prompt_greeting.txt').replace('<<NAME>>', bot_name)
    extractor_questions = open_file('./config/Role_Extractor_Questions.txt')
 #   r = sr.Recognizer()
    while True:
        # # Get Timestamp
        timestamp = time()
        timestring = timestamp_to_datetime(timestamp)
    #    process_files_in_directory('./Upload/TXT', './Upload/TXT/Finished')
    #    process_files_in_directory('./Upload/PDF', './Upload/PDF/Finished')
    #    process_files_in_directory('./Upload/EPUB', './Upload/EPUB/Finished')
        print('Enter bot name you want memories to be extracted to.')
        user_selection = input(f'\n\nBot Name: ')
        print('\nType [Clear Memory] to clear extracted info.')
        print("\nType [Skip] to skip url input.")
        query = input(f'\nEnter URL to scrape for role or personality: ')
        if query == 'Clear Memory':
            while True:
                print('\n\nSYSTEM: Are you sure you would like to delete saved short-term memory?\n        Press Y for yes or N for no.')
                user_input = input("'Y' or 'N': ")
                if user_input == 'y':
                    vdb.delete(delete_all=True, namespace=f'role_extractor_{username}')
                    print('Extracted Info has been Deleted')
                    return
                elif user_input == 'n':
                    print('\n\nSYSTEM: Info delete cancelled.')
                    return
        
        # # Check for "Exit"
        if query == 'Skip':   
            pass
        else:
            urls = urls = chunk_text_from_url(query)
        print('Extracting Memories from Scraped Info, please wait...')
        with concurrent.futures.ThreadPoolExecutor() as executor:
            lines = extractor_questions.splitlines()
            futures = [executor.submit(process_line, line, vdb, extractor_questions, gpt3_embedding, chatgptresponse_completion, save_json, timestamp_to_datetime, bot_name, user_selection) for line in lines]
            concurrent.futures.wait(futures)
        
         # # Add Heuristic Extraction based off of all of the extracted memories.
    #    results = vdb.query(vector=line_vec, filter={"memory_type": "implicit_long_term", "user": username}, top_k=35, namespace=f'{user_selection}')
    #    question_db1 = load_conversation_implicit_long_term_memory(results)
        
    #    results = vdb.query(vector=line_vec, filter={"memory_type": "explicit_long_term", "user": username}, top_k=35, namespace=f'{user_selection}')
    #    question_db2 = load_conversation_explicit_long_term_memory(results)
        
        # # Based on Searches, generate 7 Heuristics
        
        