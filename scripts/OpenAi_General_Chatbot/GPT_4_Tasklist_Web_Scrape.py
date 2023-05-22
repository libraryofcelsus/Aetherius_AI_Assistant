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
from bs4 import BeautifulSoup
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
    vdb = pinecone.Index("aetherius")
    try:
        with lock:
            print('implicit')
            results = vdb.query(vector=line_vec, filter={"memory_type": "implicit_long_term"}, top_k=7, namespace=f'{username}')
            memories1 = load_conversation_implicit_long_term_memory(results)
            results = vdb.query(vector=line_vec, filter={"memory_type": "implicit_short_term"}, top_k=5, namespace=f'{username}_short_term_memory')
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
    vdb = pinecone.Index("aetherius")
    try:
        with lock:
            results = vdb.query(vector=line_vec, filter={
            "memory_type": "episodic"}, top_k=5, namespace=f'{username}')
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
    vdb = pinecone.Index("aetherius")
    try:
        with lock:
            results = vdb.query(vector=line_vec, filter={
            "memory_type": "flashbulb"}, top_k=5, namespace=f'{username}')
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
    vdb = pinecone.Index("aetherius")
    try:
        with lock:
            print('explicit')
            results = vdb.query(vector=line_vec, filter={"memory_type": "explicit_long_term"}, top_k=5, namespace=f'{username}')
            memories1 = load_conversation_explicit_long_term_memory(results)
            results = vdb.query(vector=line_vec, filter={"memory_type": "explicit_short_term"}, top_k=5, namespace=f'{username}_short_term_memory')
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
            websum.append({'role': 'system', 'content': "You are a Data Extractor sub-module, responsible for processing text data from web scrapes. Your role includes identifying and highlighting significant or factual information. Extraneous data should be discarded, and only essential details must be returned. Stick to the data provided; do not infer or generalize. Present your responses in a Running Text format using the following pattern: [SEMANTIC QUESTION TAG: ARTICLE/INFORMATION]. Refrain from using linebreaks within the content. Convert lists into continuous text to maintain this format. Note that the semantic question tag should be a question that corresponds to the information within the article chunk."})
            websum.append({'role': 'user', 'content': f"ARTICLE CHUNK: {chunk}"})
            text = chatgpt35_completion(websum)
            paragraphs = text.split('\n\n')  # Split into paragraphs
            for paragraph in paragraphs:  # Process each paragraph individually, add a check to see if paragraph contained actual information.
                webcheck = list()
                weblist.append(url + ' ' + paragraph)
                webcheck.append({'role': 'system', 'content': f"You are an agent for an automated webscraping tool. You are one of many agents in a chain. Your task is to decide if the given text from a webscrape was scraped successfully. The scraped text should contain factual data or opinions. If the given data only consists of an error message or advertisments, skip it.  If the article was scraped successfully, print: YES.  If a web-search is not needed, print: NO."})
                webcheck.append({'role': 'user', 'content': f"Is the scraped information useful to an end-user? YES/NO: {paragraph}"})
                webyescheck = chatgptyesno_completion(webcheck)
                if webyescheck == 'YES':
                    print('---------')
                    print(url + ' ' + paragraph)
                    payload = list()
                    vector = gpt3_embedding(url + ' ' + paragraph)
                    timestamp = time()
                    timestring = timestamp_to_datetime(timestamp)
                    unique_id = str(uuid4())
                    metadata = {'bot': bot_name, 'time': timestamp, 'message': url + ' ' + paragraph,
                                'timestring': timestring, 'uuid': unique_id, "memory_type": "web_scrape"}
                    save_json('nexus/web_scrape_memory_nexus/%s.json' % unique_id, metadata)
                    payload.append((unique_id, vector, {"memory_type": "web_scrape"}))
                    vdb.upsert(payload, namespace=f'{username}_short_term_memory')
                    payload.clear()
        table = weblist
        return table
    except Exception as e:
        print(e)
        table = "Error"
        return table  
        
        
def load_conversation_web_scrape_memory(results):
    try:
        result = list()
        for m in results['matches']:
            info = load_json('nexus/web_scrape_memory_nexus/%s.json' % m['id'])
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
    
    
def search_webscrape_db(line):
    m = multiprocessing.Manager()
    lock = m.Lock()
    username = open_file('./config/prompt_username.txt')
    vdb = pinecone.Index("aetherius")
    try:
        with lock:
            line_vec = gpt3_embedding(line)
            results = vdb.query(vector=line_vec, filter={
        "memory_type": "web_scrape"}, top_k=30, namespace=f'{username}_short_term_memory')
            table = load_conversation_web_scrape_memory(results)
            return table
    except Exception as e:
        print(e)
        table = "Error"
        return table


def GPT_4_Tasklist_Web_Scrape():
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
    if not os.path.exists('nexus/web_scrape_memory_nexus'):
        os.makedirs('nexus/web_scrape_memory_nexus')
    if not os.path.exists('nexus/episodic_memory_nexus'):
        os.makedirs('nexus/episodic_memory_nexus')
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
    main_prompt = open_file('./config/Chatbot_Prompts/prompt_main.txt').replace('<<NAME>>', bot_name)
    second_prompt = open_file('./config/Chatbot_Prompts/prompt_secondary.txt')
    greeting_msg = open_file('./config/Chatbot_Prompts/prompt_greeting.txt').replace('<<NAME>>', bot_name)
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
        query = input(f'\nEnter URL to scrape: ')
        if query == 'Clear Memory':
            while True:
                print('\n\nSYSTEM: Are you sure you would like to delete saved short-term memory?\n        Press Y for yes or N for no.')
                user_input = input("'Y' or 'N': ")
                if user_input == 'y':
                    vdb.delete(filter={"memory_type": "web_scrape"}, namespace=f'{username}_short_term_memory')
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
        a = input(f'\n\nUSER: ')
        message_input = a
        vector_input = gpt3_embedding(message_input)
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
        # # Check for Exit, summarize the conversation, and then upload to episodic_memories
        conversation.append({'role': 'user', 'content': a})        
        # # Generate Semantic Search Terms
        tasklist.append({'role': 'system', 'content': "You are a task coordinator. Your job is to take user input and create a list of 2-5 inquiries to be used for a semantic database search. Use the format [- 'INQUIRY']."})
        tasklist.append({'role': 'user', 'content': "USER INQUIRY: %s" % a})
        tasklist.append({'role': 'assistant', 'content': "List of Semantic Search Terms: "})
        tasklist_output = chatgpt200_completion(tasklist)
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
                        tasklist_vector := gpt3_embedding(line),
                        db_term.update({_index: tasklist_vector}),
                        results := vdb.query(vector=db_term[_index], filter={
        "memory_type": "explicit_long_term"}, top_k=3, namespace=f'{username}'),
                        db_term_result.update({_index: load_conversation_explicit_long_term_memory(results)}),
                        results := vdb.query(vector=db_term[_index], filter={
        "memory_type": "implicit_long_term"}, top_k=2, namespace=f'{username}'),
                        db_term_result2.update({_index: load_conversation_implicit_long_term_memory(results)}),
                        conversation.append({'role': 'assistant', 'content': "MEMORIES: %s" % db_term_result[_index]}),
                        conversation.append({'role': 'assistant', 'content': "MEMORIES: %s" % db_term_result2[_index]}),
                        (
                            int_conversation.append({'role': 'assistant', 'content': "MEMORIES: %s" % db_term_result[_index]}),
                            int_conversation.append({'role': 'assistant', 'content': "MEMORIES: %s" % db_term_result2[_index]})
                        ) if _index < 4 else None,
                    ),
                    line, _index, conversation.copy(), int_conversation.copy()
                )
                for _index, line in enumerate(lines) if line.strip()
            ] + [
                executor.submit(lambda: (
                    vdb.query(vector=vector_input, filter={
        "memory_type": "explicit_long_term"}, top_k=5, namespace=f'{username}'),
                    load_conversation_episodic_memory)
                ),
                executor.submit(lambda: (
                    vdb.query(vector=vector_input, filter={
        "memory_type": "explicit_long_term"}, top_k=8, namespace=f'{username}'),
                    load_conversation_explicit_short_term_memory)
                ),
                executor.submit(lambda: (
                    vdb.query(vector=vector_input, filter={
        "memory_type": "explicit_long_term"}, top_k=2, namespace=f'{username}'),
                    load_conversation_flashbulb_memory)
                ),
                executor.submit(lambda: (
                    vdb.query(vector=vector_input, filter={
        "memory_type": "explicit_long_term"}, top_k=5, namespace=f'{username}'),
                    load_conversation_heuristics)
                ),
            ]
            try:
                db_search_1 = futures[len(lines)].result()[1](futures[len(lines)].result()[0])
                db_search_2 = futures[len(lines) + 1].result()[1](futures[len(lines) + 1].result()[0])
                db_search_3 = futures[len(lines) + 2].result()[1](futures[len(lines) + 2].result()[0])
                db_search_4 = futures[len(lines) + 3].result()[1](futures[len(lines) + 3].result()[0])
            except IndexError as e:
                print(f"Caught an IndexError: {e}")
                print(f"Length of futures: {len(futures)}")
                print(f"Length of lines: {len(lines)}")
            except Exception as e:
                print(f"Caught an exception: {e}")
       # # # Inner Monologue Generation
        conversation.append({'role': 'assistant', 'content': "MEMORIES: %s;%s;\n\nHEURISTICS: %s;\nUSER MESSAGE: %s;\nBased on %s's memories and the user, %s's message, compose a brief silent soliloquy as %s's inner monologue that reflects on %s's deepest contemplations and emotions in relation to the user's message.\n\nINNER_MONOLOGUE: " % (db_search_1, db_search_2, db_search_3, a, bot_name, username, bot_name, bot_name)})
        output_one = chatgpt250_completion(conversation)
        message = output_one
        vector_monologue = gpt3_embedding('Inner Monologue: ' + message)
        print('\n\nINNER_MONOLOGUE: %s' % output_one)
        output_log = f'\nUSER: {a}\n\n{bot_name}: {output_one}'
        # # Clear Conversation List
        conversation.clear()
        # # Memory DB Search
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future1 = executor.submit(vdb.query, vector=vector_monologue, filter={
        "memory_type": "episodic"}, top_k=5, namespace=f'{username}')
            future2 = executor.submit(vdb.query, vector=vector_input, filter={
        "memory_type": "explicit_short_term"}, top_k=10, namespace=f'{username}_short_term_memory')
            future3 = executor.submit(vdb.query, vector=vector_monologue, filter={
        "memory_type": "flashbulb"}, top_k=2, namespace=f'{username}')
            future4 = executor.submit(vdb.query, vector=vector_monologue, filter={
        "memory_type": "heuristics"}, top_k=3, namespace=f'{username}')
            try:
                db_search_4 = load_conversation_episodic_memory(future1.result())
                db_search_5 = load_conversation_explicit_short_term_memory(future2.result())
                db_search_12 = load_conversation_flashbulb_memory(future3.result())
                db_search_13 = load_conversation_heuristics(future4.result())
            except IndexError as e:
                print(f"Caught an IndexError: {e}")
                print(f"Length of futures: {len(futures)}")
                print(f"Length of lines: {len(lines)}")
            except Exception as e:
                print(f"Caught an exception: {e}")
        # # Intuition Generation
        results = vdb.query(vector=vector_input, filter={
        "memory_type": "web_scrape"}, top_k=7, namespace=f'{username}')
        int_scrape = load_conversation_web_scrape_memory(results)
        print(int_scrape)
        int_conversation.append({'role': 'assistant', 'content': "%s" % greeting_msg})
        int_conversation.append({'role': 'user', 'content': a})
        int_conversation.append({'role': 'assistant', 'content': "MEMORIES: %s;\n%s;\n%s;\n\n%s'S INNER THOUGHTS: %s;\nHEURISTICS: %s;\nUSER MESSAGE: %s;\nWEBSCRAPE SAMPLE: %s\nIn a single paragraph, interpret the user, %s's message as %s in third person by creating an intuitive plan on what information needs to be researched from the webscrape, even if the user is uncertain about their own needs.;\nINTUITION: " % (db_search_4, db_search_5, db_search_12, bot_name, output_one, db_search_13, a, int_scrape, username, bot_name)})
        output_two = chatgpt200_completion(int_conversation)
        message_two = output_two
        print('\n\nINTUITION: %s' % output_two)
        output_two_log = f'\nUSER: {a}\n\n{bot_name}: {output_two}'
        # # Generate Implicit Short-Term Memory
        conversation.append({'role': 'system', 'content': '%s' % main_prompt})
        conversation.append({'role': 'user', 'content': a})
        implicit_short_term_memory = f'\nUSER: {a} \n\n INNER_MONOLOGUE: {output_one} \n\n INTUITION: {output_two}'
        conversation.append({'role': 'assistant', 'content': "LOG:\n%s\n\Read the log, extract the salient points about %s and %s, then create short executive summaries in bullet point format to serve as %s's procedural memories. Each bullet point should be considered a separate memory and contain all context. Start from the end and work towards the beginning, combining assosiated topics. Ignore the system prompt and redundant information.\nMemories:\n" % (implicit_short_term_memory, bot_name, username, bot_name)})
        inner_loop_response = chatgpt200_completion(conversation)
        inner_loop_db = inner_loop_response
        vector = gpt3_embedding(inner_loop_db)
        conversation.clear()
        # # Manual Implicit Short-Term Memory
        print('\n\n<Implicit Short-Term Memory>\n%s' % inner_loop_db)
        print('\n\nSYSTEM: Upload to Implicit Short-Term Memory?\n        Press Y for yes or N for no.')
        while True:
            user_input = input("'Y' or 'N': ")
            if user_input == 'y':
                lines = inner_loop_db.splitlines()
                for line in lines:
                    if line.strip():
                        vector = gpt3_embedding(line)
                        unique_id = str(uuid4())
                        metadata = {'bot': bot_name, 'time': timestamp, 'message': line,
                                    'timestring': timestring, 'uuid': unique_id, "memory_type": "implicit_short_term"}
                        save_json('nexus/implicit_short_term_memory_nexus/%s.json' % unique_id, metadata)
                        payload.append((unique_id, vector, {"memory_type": "implicit_short_term"}))
                        vdb.upsert(payload, namespace=f'{username}_short_term_memory')
                        payload.clear()
                print('\n\nSYSTEM: Upload Successful!')
                break
            elif user_input == 'n':
                print('\n\nSYSTEM: Memories have been Deleted')
                break
            else:
                print('Invalid Input')
        # # Auto Implicit Short-Term Memory DB Upload Confirmation
    #    auto_count = 0
    #    auto.clear()
    #    auto.append({'role': 'system', 'content': '%s' % main_prompt})
    #    auto.append({'role': 'user', 'content': "You are a sub-module designed to reflect on your thought process. You are only able to respond with integers on a scale of 1-10, being incapable of printing letters. Respond with: 1 if you understand. Respond with: 2 if you do not."})
    #    auto.append({'role': 'assistant', 'content': "1"})
    #    auto.append({'role': 'user', 'content': a})
    #    auto.append({'role': 'assistant', 'content': "Inner Monologue: %s\nIntuition: %s" % (output_one, output_two)})
    #    auto.append({'role': 'assistant', 'content': "Thoughts on input: I will now review the user's message and my reply, rating if whether my thoughts are both pertinent to the user's inquiry and my growth with a number on a scale of 1-10. I will now give my response in digit form for an integer only input: "})
    #    auto_int = None
    #    while auto_int is None:
    #        automemory = chatgptyesno_completion(auto)
    #        if is_integer(automemory):
    #            auto_int = int(automemory)
    #            if auto_int > 6:
    #                lines = inner_loop_db.splitlines()
    #                for line in lines:
    #                    vector = gpt3_embedding(inner_loop_db)
    #                    unique_id = str(uuid4())
    #                    metadata = {'bot': bot_name, 'time': timestamp, 'message': inner_loop_db,
    #                                'timestring': timestring, 'uuid': unique_id, "memory_type": "implicit_short_term"}
    #                    save_json('nexus/implicit_short_term_memory_nexus/%s.json' % unique_id, metadata)
    #                    payload.append((unique_id, vector, {"memory_type": "implicit_short_term"}))
    #                    vdb.upsert(payload, namespace=f'{username}_short_term_memory')
    #                    payload.clear()
    #                print('\n\nSYSTEM: Auto-memory upload Successful!')
    #                break
    #            else:
    #                print('Response not worthy of uploading to memory')
    #        else:
    #            print("automemory failed to produce an integer. Retrying...")
    #            auto_int = None
    #            auto_count += 1
    #            if auto_count > 2:
    #                print('Auto Memory Failed')
    #                break
    #    else:
    #        pass          
        # # Test for basic Autonomous Tasklist Generation and Task Completion
        master_tasklist.append({'role': 'system', 'content': "You are a stateless task list coordinator for %s an autonomous Ai chatbot. Your job is to combine the user's input and the user facing chatbots intuitive action plan, then transform it into a list of independent research queries that can be executed by separate AI agents in a cluster computing environment. The other asynchronous Ai agents are also stateless and cannot communicate with each other or the user during task execution, they do however have access to %s's memories. Exclude tasks involving final product production, hallucinations, user communication, or checking work with other agents. Respond using the following format: '- [task]'" % (bot_name, bot_name)})
        master_tasklist.append({'role': 'user', 'content': "USER FACING CHATBOT'S INTUITIVE ACTION PLAN:\n%s" % output_two})
        master_tasklist.append({'role': 'user', 'content': "USER INQUIRY:\n%s" % a})
        master_tasklist.append({'role': 'user', 'content': "SEMANTICALLY SIMILAR INQUIRIES:\n%s" % tasklist_output})
        master_tasklist.append({'role': 'assistant', 'content': "TASK LIST:"})
        master_tasklist_output = chatgpt_tasklist_completion(master_tasklist)
        print(master_tasklist_output)
        tasklist_completion.append({'role': 'system', 'content': "{main_prompt}"})
        tasklist_completion.append({'role': 'assistant', 'content': f"You are the final response module of the cluster compute Ai-Chatbot {bot_name}. Your job is to take the completed task list, and give a verbose response to the end user in accordance with their initial request."})
        tasklist_completion.append({'role': 'user', 'content': "%s" % master_tasklist_output})
        task = {}
        task_result = {}
        task_result2 = {}
        task_counter = 1
        # # Split bullet points into separate lines to be used as individual queries
        lines = master_tasklist_output.splitlines()
        print('\n\nSYSTEM: Would you like to autonomously complete this task list?\n        Press Y for yes or N for no.')
        user_input = input("'Y' or 'N': ")
        if user_input == 'y':
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [
                    executor.submit(
                        lambda line, task_counter, conversation, memcheck, memcheck2, webcheck, tasklist_completion: (
                            tasklist_completion.append({'role': 'user', 'content': f"ASSIGNED TASK:\n{line}"}),
                            conversation.append({'role': 'system', 'content': "You are a sub-agent for {bot_name}, an Autonomous Ai-Chatbot. You are one of many agents in a chain. You are to take the given task and complete it in its entirety. Be Verbose and take other tasks into account when formulating your answer."}),
                            conversation.append({'role': 'assistant', 'content': "{bot_name}'s INNER MONOLOGUE: {output_one}"}),
                            conversation.append({'role': 'user', 'content': f"Task list:\n{master_tasklist_output}"}),
                            conversation.append({'role': 'assistant', 'content': "Bot: I have studied the given tasklist.  What is my assigned task?"}),
                            conversation.append({'role': 'user', 'content': f"Bot Assigned task: {line}"}),
                            # # DB Yes No Tool
                            memcheck.append({'role': 'system', 'content': f"You are a sub-agent for {bot_name}, an Autonomous Ai-Chatbot. You are one of many agents in a chain. Your task is to decide if the user's input requires {bot_name}'s past memories to complete. Any information pertaining to the user, {username}, or the main bot, {bot_name} should be searched for.  If past memories are needed, print: YES.  If they are not needed, print: NO."}),
                            memcheck.append({'role': 'user', 'content': f"{bot_name}'s Inner Monologue: %s"}),
                            memcheck.append({'role': 'user', 'content': f"{bot_name}'s Intuition: %s"}),
                            memcheck.append({'role': 'user', 'content': "//LIST OF EXAMPLES:"}),
                            memcheck.append({'role': 'user', 'content': "Research ways to identify user needs and interests"}),
                            memcheck.append({'role': 'assistant', 'content': "YES"}),
                            memcheck.append({'role': 'user', 'content': "Research common themes in the book Faust."}),
                            memcheck.append({'role': 'assistant', 'content': "NO"}),
                            memcheck.append({'role': 'user', 'content': f"Search {bot_name}'s memory for context."}),
                            memcheck.append({'role': 'assistant', 'content': "YES"}),
                            memcheck.append({'role': 'user', 'content': "END OF EXAMPLE LIST//"}),
                            memcheck.append({'role': 'assistant', 'content': "{bot_name} REINITIALIZATION: Your task is to decide if the user's input requires %s's past memories to complete. If past memories are needed, print: YES.  If they are not needed, print: NO."}),
                            memcheck.append({'role': 'user', 'content': "What would you like to talk about?"}),
                            memcheck.append({'role': 'assistant', 'content': "YES"}),
                            # # DB Selector Tool
                            memcheck2.append({'role': 'system', 'content': f"You are a sub-module for {bot_name}, an Autonomous Ai-Chatbot. You are one of many agents in a chain. Your task is to decide which database needs to be queried in relation to a user's input. The databases are representitive of different types of memories. Only choose a single database to query. Respond in this format: RESPONSE"}),
                            memcheck2.append({'role': 'assistant', 'content': f"{bot_name}'s INNER_MONOLOGUE: {output_one}"}),
                            memcheck2.append({'role': 'user', 'content': "//LIST OF MEMORY TYPE NAMES:"}),
                            memcheck2.append({'role': 'user', 'content': "EPISODIC: These are memories of personal experiences and specific events that occur in a particular time and place. These memories often include contextual details, such as emotions, sensations, and the sequence of events."}),
                            memcheck2.append({'role': 'user', 'content': "FLASHBULB: Flashbulb memories are vivid, detailed, and long-lasting memories of highly emotional or significant events, such as learning about a major news event or experiencing a personal tragedy."}),
                            memcheck2.append({'role': 'user', 'content': "IMPLICIT LONG TERM: Unconscious memory not easily verbalized, including procedural memory (skills and habits), classical conditioning (associations between stimuli and reflexive responses), and priming (unconscious activation of specific associations)."}),
                            memcheck2.append({'role': 'user', 'content': "EXPLICIT LONG TERM: Conscious recollections of facts and events, including episodic memory (personal experiences and specific events) and semantic memory (general knowledge, concepts, and facts)."}),
                            memcheck2.append({'role': 'user', 'content': "END OF LIST//\n\n//EXAMPLE QUERIES:"}),
                            memcheck2.append({'role': 'user', 'content': "Research common topics discussed with users who start a conversation with 'hello'"}),
                            memcheck2.append({'role': 'assistant', 'content': "EPISODIC MEMORY"}),
                            memcheck2.append({'role': 'user', 'content': "Create a research paper on the book Faust."}),
                            memcheck2.append({'role': 'assistant', 'content': "NO MEMORIES NEEDED"}),
                            memcheck2.append({'role': 'user', 'content': "Tell me about your deepest desires."}),
                            memcheck2.append({'role': 'assistant', 'content': "FLASHBULB"}),
                            memcheck2.append({'role': 'user', 'content': "END OF EXAMPLE QUERIES//\n\n//BEGIN JOB:"}),
                            memcheck2.append({'role': 'user', 'content': "JOB: Your task is to decide which database needs to be queried in relation to a user's input. The databases are representitive of different types of memories. Only choose a single database to query. Respond in this format: RESPONSE"}),
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
                            memcheck.append({'role': 'user', 'content': f"{line}"}),
                            mem1 := chatgptyesno_completion(memcheck),
                            # # Go to conditional for choosing DB Name
                            memcheck2.append({'role': 'user', 'content': f"{line}"}),
                            mem2 := chatgptselector_completion(memcheck2) if mem1 == 'YES' else fail(),
                            line_vec := gpt3_embedding(line),    #EPISODIC, FLASHBULB, IMPLICIT LONG TERM, EXPLICIT LONG TERM
                            memories := (search_episodic_db(line_vec) if mem2 == 'EPISODIC' else 
                                         search_implicit_db(line_vec) if mem2 == 'IMPLICIT LONG TERM' else 
                                         search_flashbulb_db(line_vec) if mem2 == 'FLASHBULB' else
                                         search_explicit_db(line_vec) if mem2 == 'EXPLICIT LONG TERM' else
                                         fail()),
                            conversation.append({'role': 'assistant', 'content': "WEBSEARCH: %s" % table}),
                            conversation.append({'role': 'user', 'content': "Bot %s Task Reinitialization: %s" % (task_counter, line)}),
                            conversation.append({'role': 'user', 'content': "SYSTEM: Try to relate the bot's task to the given webscraped articles. If the bot's task is an advertisment, inform the user that ads have taken their answer."}),
                            conversation.append({'role': 'assistant', 'content': "Bot %s's Response:" % task_counter}),
                            task_completion := chatgpt35_completion(conversation),
                            #chatgpt35_completion(conversation),
                          #  conversation.clear(),
                            tasklist_completion.append({'role': 'assistant', 'content': "WEBSCRAPE: %s" % table}),
                            tasklist_completion.append({'role': 'assistant', 'content': "Research for Task Completion: %s" % memories}),
                            tasklist_completion.append({'role': 'assistant', 'content': "COMPLETED TASK:\n%s" % task_completion}),
                            tasklist_log.append({'role': 'user', 'content': "ASSIGNED TASK:\n%s\n\n" % line}),
                            tasklist_log.append({'role': 'assistant', 'content': "COMPLETED TASK:\n%s\n\n" % memories}),
                            print(line),
                            print(memories),
                       #     print(table),
                            print(task_completion),
                    #        print(task_completion),
                        ) if line != "None" else tasklist_completion,
                        line, task_counter, memcheck.copy(), memcheck2.copy(), webcheck.copy(), conversation.copy(), []
                    )
                    for task_counter, line in enumerate(lines)
                ]
            tasklist_completion.append({'role': 'assistant', 'content': f"{bot_name}'s INNER_MONOLOGUE: {output_one}"})
            tasklist_completion.append({'role': 'user', 'content': f"{bot_name}'s INTUITION: {output_two}"})
            tasklist_completion.append({'role': 'user', 'content': f"Take the given set of tasks and completed responses and transmute them into a verbose response for {username}, the end user in accordance with their request. The end user is both unaware and unable to see any of your research. User's initial request: {a}"})
            print('\n\nGenerating Final Output...')
            response_two = chatgpt_tasklist_completion(tasklist_completion)
            print('\nFINAL OUTPUT:\n%s' % response_two)
            complete_message = f'\nUSER: {a}\n\nINNER_MONOLOGUE: {output_one}\n\nINTUITION: {output_two}\n\n{bot_name}: {tasklist_log}\n\nFINAL OUTPUT: {response_two}'
            filename = '%s_chat.txt' % timestamp
            save_file('logs/complete_chat_logs/%s' % filename, complete_message)
            conversation.clear()
            int_conversation.clear()
            conversation2.clear()
            tasklist_completion.clear()
            master_tasklist.clear()
            tasklist.clear()
            tasklist_log.clear()
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
        summary.append({'role': 'user', 'content': "LOG:\n%s\n\Read the log and create short executive summaries in bullet point format to serve as %s's explicit memories. Each bullet point should be considered a separate memory and contain all context. Start from the end and work towards the beginning, combining assosiated topics.\nMemories:\n" % (db_msg, bot_name)})
        db_upload = chatgptsummary_completion(summary)
        db_upsert = db_upload
        # # Manual Short-Term Memory DB Upload Confirmation
        print('\n\n<DATABASE INFO>\n%s' % db_upsert)
        print('\n\nSYSTEM: Upload to short term memory? \n        Press Y for yes or N for no.')
        while True:
            user_input = input("'Y' or 'N': ")
            if user_input == 'y':
                lines = db_upsert.splitlines()
                for line in lines:
                    if line.strip():
                        vector = gpt3_embedding(line)
                        unique_id = str(uuid4())
                        metadata = {'bot': bot_name, 'time': timestamp, 'message': line,
                                    'timestring': timestring, 'uuid': unique_id, "memory_type": "explicit_long_term"}
                        save_json('nexus/explicit_short_term_memory_nexus/%s.json' % unique_id, metadata)
                        payload.append((unique_id, vector, {"memory_type": "explicit_long_term"}))
                        vdb.upsert(payload, namespace=f'{username}_short_term_memory')
                        payload.clear()
                print('\n\nSYSTEM: Upload Successful!')
                break
            elif user_input == 'n':
                print('\n\nSYSTEM: Memories have been Deleted')
                break
            else:
                print('Invalid Input')
        # # Auto Explicit Short-Term Memory DB Upload Confirmation
    #    auto_count = 0    
    #    auto.clear()
    #    auto.append({'role': 'system', 'content': '%s' % main_prompt})
    #    auto.append({'role': 'user', 'content': "You are a sub-module designed to reflect on your thought process. You are only able to respond with integers on a scale of 1-10, being incapable of printing letters. Respond with: 1 if you understand. Respond with: 2 if you do not."})
    #    auto.append({'role': 'assistant', 'content': "1"})
    #    auto.append({'role': 'user', 'content': a})
    #    auto.append({'role': 'assistant', 'content': "Inner Monologue: %s\nIntuition: %s" % (output_one, output_two)})
    #    auto.append({'role': 'assistant', 'content': "Thoughts on input: I will now review the user's message and my reply, rating if whether my thoughts are both pertinent to the user's inquiry and my growth with a number on a scale of 1-10. I will now give my response in digit form for an integer only input: "})
    #    auto_int = None
    #    while auto_int is None:
    #        automemory = chatgptyesno_completion(auto)
    #        if is_integer(automemory):
    #            auto_int = int(automemory)
    #            if auto_int > 6:
    #                lines = db_upsert.splitlines()
    #                for line in lines:
    #                    vector = gpt3_embedding(db_upsert)
    #                    unique_id = str(uuid4())
    #                    metadata = {'bot': bot_name, 'time': timestamp, 'message': db_upsert,
    #                                'timestring': timestring, 'uuid': unique_id, "memory_type": "explicit_short_term"}
    #                    save_json('nexus/short_term_memory_nexus/%s.json' % unique_id, metadata)
    #                    payload.append((unique_id, vector, {"memory_type": "explicit_short_term"}))
    #                    vdb.upsert(payload, namespace=f'{username}_short_term_memory')
    #                    payload.clear()
    #                print('\n\nSYSTEM: Auto-memory upload Successful!')
    #                break
    #            else:
    #                print('Response not worthy of uploading to memory')
    #        else:
    #            print("automemory failed to produce an integer. Retrying...")
    #            auto_int = None
    #            auto_count += 1
    #            if auto_count > 2:
    #                print('Auto Memory Failed')
    #                break
    #    else:
    #        pass                 
        index_info = vdb.describe_index_stats()
        namespace_stats = index_info['namespaces']
        namespace_name = f'{username}_short_term_memory'
        if namespace_name in namespace_stats and namespace_stats[namespace_name]['vector_count'] > 25:
            consolidation.clear()
            print(f"{namespace_name} has 15 or more entries, starting memory consolidation.")
            results = vdb.query(vector=vector_input, filter={
        "memory_type": "explicit_short_term"}, top_k=25, namespace=f'{username}_short_term_memory')
            memory_consol_db = load_conversation_explicit_short_term_memory(results)
            consolidation.append({'role': 'system', 'content': "%s" % main_prompt})
            consolidation.append({'role': 'assistant', 'content': "LOG:\n%s\n\nRead the Log and consolidate the different topics into executive summaries. Each summary should contain the entire context of the memory. Follow the format [- Executive Summary]." % memory_consol_db})
            memory_consol = chatgptconsolidation_completion(consolidation)
            lines = memory_consol.splitlines()
            for line in lines:
                if line.strip():
            #    print(timestring + line)
                    vector = gpt3_embedding(line)
                    unique_id = str(uuid4())
                    metadata = {'bot': bot_name, 'time': timestamp, 'message': (line),
                                'timestring': timestring, 'uuid': unique_id, "memory_type": "explicit_long_term"}
                    save_json('nexus/explicit_long_term_memory_nexus/%s.json' % unique_id, metadata)
                    payload.append((unique_id, vector, {"memory_type": "explicit_long_term"}))
                    vdb.upsert(payload, namespace=f'{username}')
                    payload.clear()
            payload.append((unique_id, vector))
            vdb.upsert(payload, namespace=f'{username}_consol_counter')
            payload.clear()
            print('Explicit Short-Term Memory Consolidation Successful')
            consolidation.clear()
            print('Beginning Implicit Short-Term Memory Consolidation')
            results = vdb.query(vector=vector_input, filter={
        "memory_type": "implicit_short_term"}, top_k=20, namespace=f'{username}_short_term_memory')
            memory_consol_db2 = load_conversation_implicit_short_term_memory(results)
            consolidation.append({'role': 'system', 'content': "%s" % main_prompt})
            consolidation.append({'role': 'assistant', 'content': "LOG:\n%s\n\nRead the Log and consolidate the different topics into executive summaries to serve as %s's implicit memories. Each summary should contain the entire context of the memory. Follow the format: [-{tag} {Executive Summary}]." % (memory_consol_db2, bot_name)})
            memory_consol2 = chatgptconsolidation_completion(consolidation)
            consolidation.clear()
            print('Finished.\nRemoving Redundent Memories.')
            vector_sum = gpt3_embedding(memory_consol2)
            results = vdb.query(vector=vector_sum, filter={
        "memory_type": "implicit_long_term"}, top_k=8, namespace=f'{username}')
            memory_consol_db3 = load_conversation_implicit_long_term_memory(results)
            consolidation.append({'role': 'system', 'content': "%s" % main_prompt})
            consolidation.append({'role': 'system', 'content': "IMPLICIT LONG TERM MEMORY: %s\n\nIMPLICIT SHORT TERM MEMORY: %s\n\nRemove any duplicate information from your Implicit Short Term memory that is already found in your Long Term Memory. Then consolidate similar topics into executive summaries. Each summary should contain the entire context of the memory. Use the following format: [- {emotion} {Memory}]" % (memory_consol_db3, memory_consol_db2)})
            memory_consol3 = chatgptconsolidation_completion(consolidation)
            print(memory_consol3)
            print('\n\nSYSTEM: Upload to implicit memory?\n        Press Y for yes or N for no.')
            user_input = input("'Y' or 'N': ")
            if user_input == 'y':
                lines = memory_consol3.splitlines()
                for line in lines:
                    if line.strip():
                        vector = gpt3_embedding(line)
                        unique_id = str(uuid4())
                        metadata = {'bot': bot_name, 'time': timestamp, 'message': (line),
                                    'timestring': timestring, 'uuid': unique_id, "memory_type": "implicit_long_term"}
                        save_json('nexus/implicit_long_term_memory_nexus/%s.json' % unique_id, metadata)
                        payload.append((unique_id, vector, {"memory_type": "implicit_long_term"}))
                        vdb.upsert(payload, namespace=f'{username}')
                        payload.clear()
                vdb.delete(delete_all=True, namespace=f'{username}_short_term_memory')
                print('Memory Consolidation Successful')
            elif user_input == 'n':
                print('\n\nSYSTEM: Memories have been Deleted')
                break
            else:
                print('Invalid Input')         
        # # Implicit Associative Processing/Pruning based on amount of vectors in namespace
            index_info = vdb.describe_index_stats()
            namespace_stats = index_info['namespaces']
            namespace_name = f'{username}_consol_counter'
            if namespace_name in namespace_stats and namespace_stats[namespace_name]['vector_count'] % 2 == 0:
                consolidation.clear()
                print('Running Associative Processing/Pruning of Impicit Memory')
                results = vdb.query(vector=vector_monologue, filter={
        "memory_type": "implicit_long_term"}, top_k=10, namespace=f'{username}')
                memory_consol_db1 = load_conversation_implicit_long_term_memory(results)
                ids_to_delete = [m['id'] for m in results['matches']]
                consolidation.append({'role': 'system', 'content': "%s" % main_prompt})
                consolidation.append({'role': 'assistant', 'content': "LOG:\n%s\n\nRead the Log and consolidate the different memories into executive summaries in a process allegorical to associative processing. Each summary should contain the entire context of the memory. Follow the format: [-{tag} {Memory}]" % memory_consol_db1})
                memory_consol = chatgptconsolidation_completion(consolidation)
                print('\nOriginal Memories\n')
                print(memory_consol_db1)
                print('\nConsolidated Memories\n')
                print(memory_consol)
                print('\nWould you like to upload consolidated implicit memories to DB?\nY for yes or N for no.')
                while True:
                    user_input = input("'Y' or 'N': ")
                    if user_input == 'y':
                        memories = results
                        lines = memory_consol.splitlines()
                        for line in lines:
                            if line.strip():
                                vector = gpt3_embedding(line)
                                unique_id = str(uuid4())
                                metadata = {'bot': bot_name, 'time': timestamp, 'message': (line),
                                            'timestring': timestring, 'uuid': unique_id, "memory_type": "implicit_long_term"}
                                save_json('nexus/implicit_memory_nexus/%s.json' % unique_id, metadata)
                                payload.append((unique_id, vector, {"memory_type": "implicit_long_term"}))
                                vdb.upsert(payload, namespace=f'{username}')
                                payload.clear()
                                vdb.delete(ids=ids_to_delete, filter={
        "memory_type": "implicit_long_term"}, namespace=f'{username}')
                        break
                    elif user_input == 'n':
                        print('Cancelled')
                        break
                    else:
                        print('Invalid Input')            
        # # Explicit Long-Term Memory Associative Processing/Pruning based on amount of vectors in namespace
            index_info = vdb.describe_index_stats()
            namespace_stats = index_info['namespaces']
            namespace_name = f'{username}_consol_counter'
            if namespace_name in namespace_stats and namespace_stats[namespace_name]['vector_count'] > 2:
                consolidation.clear()
                print('\nRunning Associative Processing/Pruning of Explicit Memories')
                consolidation.append({'role': 'system', 'content': "You are a data extractor. Your job is to read the user's input and provide a single semantic search query representitive of a habit of %s." % bot_name})
                results = vdb.query(vector=vector_monologue, filter={
        "memory_type": "implicit_long_term"}, top_k=5, namespace=f'{username}')
                consol_search = load_conversation_implicit_long_term_memory(results)
                consolidation.append({'role': 'user', 'content': "%s's Memories:\n%s" % (bot_name, consol_search)})
                consolidation.append({'role': 'assistant', 'content': "Semantic Search Query: "})
                consol_search_term = chatgpt200_completion(consolidation)
                consol_vector = gpt3_embedding(consol_search_term)
                results = vdb.query(vector=consol_vector, filter={
        "memory_type": "explicit_long_term"}, top_k=10, namespace=f'{username}')
                memory_consol_db2 = load_conversation_explicit_long_term_memory(results)
                ids_to_delete2 = [m['id'] for m in results['matches']]
                consolidation.clear()
                consolidation.append({'role': 'system', 'content': "%s" % main_prompt})
                consolidation.append({'role': 'assistant', 'content': "LOG:\n%s\n\nRead the Log and consolidate the different memories into executive summaries in a process allegorical to associative processing. Each summary should contain the entire context of the memory. Follow the format: [-{tag} Memory]" % memory_consol_db2})
                memory_consol2 = chatgptconsolidation_completion(consolidation)
                print('\nOriginal Memories\n')
                print(memory_consol_db2)
                print('\nConsolidated Memories\n')
                print(memory_consol2)
                print('\nWould you like to upload consolidated explicit memories to DB?\nY for yes or N for no.')
                while True:
                    user_input = input("'Y' or 'N': ")
                    if user_input == 'y':
                        memories = results
                        lines = memory_consol2.splitlines()
                        for line in lines:
                            if line.strip():
                                vector = gpt3_embedding(line)
                                unique_id = str(uuid4())
                                metadata = {'bot': bot_name, 'time': timestamp, 'message': (line),
                                            'timestring': timestring, 'uuid': unique_id, "memory_type": "explicit_long_term"}
                                save_json('nexus/explicit_memory_nexus/%s.json' % unique_id, metadata)
                                payload.append((unique_id, vector, {"memory_type": "explicit_long_term"}))
                                vdb.upsert(payload, namespace=f'{username}')
                                payload.clear()
                                vdb.delete(ids=ids_to_delete2, namespace=f'{username}')
                        vdb.delete(delete_all=True, namespace=f'{username}_consol_counter')
                        break
                    elif user_input == 'n':
                        print('Cancelled')
                        break
                    else:
                        print('Invalid Input')
        continue
