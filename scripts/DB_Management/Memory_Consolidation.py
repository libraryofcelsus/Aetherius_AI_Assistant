import os
import sys
import openai
import json
import time
from time import time, sleep
import datetime
from uuid import uuid4
import pinecone


def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()


def save_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as outfile:
        outfile.write(content)


def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return json.load(infile)


def save_json(filepath, payload):
    with open(filepath, 'w', encoding='utf-8') as outfile:
        json.dump(payload, outfile, ensure_ascii=False, sort_keys=True, indent=2)


def timestamp_to_datetime(unix_time):
    return datetime.datetime.fromtimestamp(unix_time).strftime("%A, %B %d, %Y at %I:%M%p %Z")


def gpt3_embedding(content, engine='text-embedding-ada-002'):
    content = content.encode(encoding='ASCII', errors='ignore').decode()  # fix any UNICODE errors
    response = openai.Embedding.create(input=content, engine=engine)
    vector = response['data'][0]['embedding']  # this is a normal list
    return vector
    
    
def chatgpt35summary_completion(messages, model="gpt-3.5-turbo", temp=0.0):
    max_retry = 7
    retry = 0
    while True:
        try:
            response = openai.ChatCompletion.create(model=model, messages=messages, max_tokens=400)
            text = response['choices'][0]['message']['content']
            temperature = temp
            return text
        except Exception as oops:
            retry += 1
            if retry >= max_retry:
                print(f"Exiting due to an error in ChatGPT: {oops}")
                exit(1)
            print(f'Error communicating with OpenAI: "{oops}" - Retrying in {2 ** (retry - 1) * 5} seconds...')
            sleep(2 ** (retry - 1) * 5)


def load_conversation_long_term_memory(results):
    result = list()
    for m in results['matches']:
        info = load_json('nexus/long_term_memory_nexus/%s.json' % m['id'])
        result.append(info)
    ordered = sorted(result, key=lambda d: d['time'], reverse=False)  # sort them all chronologically
    messages = [i['message'] for i in ordered]
    return '\n'.join(messages).strip()
    

def Memory_Consolidation():
    # key = input("Enter OpenAi API KEY:")
    vdb = pinecone.Index("aetherius")
    index_info = vdb.describe_index_stats()
    print('Pinecone DB Info')
    print(index_info)
    print("Type a search query to consolidate memories.")
    payload = list()
    consolidation = list()
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
    main_prompt = open_file('./config/Chatbot_Prompts/prompt_main.txt').replace('<<NAME>>', bot_name)
    while True:
        timestamp = time()
        timestring = timestamp_to_datetime(timestamp)
        a = input(f'\n\nUSER: ')
        vector = gpt3_embedding(a)
        results = vdb.query(vector=vector, top_k=5, namespace='long_term_memory') 
        memory_consol_db = load_conversation_long_term_memory(results)
        ids_to_delete = [m['id'] for m in results['matches']]
        consolidation.append({'role': 'system', 'content': "%s" % main_prompt})
        consolidation.append({'role': 'assistant', 'content': "LOG:\n%s\n\nRead the Log and consolidate the different memories into executive summaries in a process allegorical to associative processing. Each summary should contain the entire context of the memory. Follow the format [- Executive Summary]." % memory_consol_db})
        consolidation.append({'role': 'assistant', 'content': "Executive Summaries:\n"})
        memory_consol = chatgpt35summary_completion(consolidation)
        print('\nOriginal Memories\n')
        print(memory_consol_db)
        print('\nConsolidated Memories\n')
        print(memory_consol)
        print('\nWould you like to replace the original memories with consolidated memories?\nY for yes or N for no.')
        while True:
            user_input = input("'Y' or 'N': ")
            if user_input == 'y':
                memories = results
                lines = memory_consol.splitlines()
                for line in lines:
                    vector = gpt3_embedding(line)
                    unique_id = str(uuid4())
                    metadata = {'speaker': bot_name, 'time': timestamp, 'message': (line),
                                'timestring': timestring, 'uuid': unique_id}
                    save_json('nexus/long_term_memory_nexus/%s.json' % unique_id, metadata)
                    payload.append((unique_id, vector))
                    vdb.upsert(payload, namespace='long_term_memory')
                    payload.clear()    
                vdb.delete(ids=ids_to_delete, namespace='long_term_memory')
                break
            elif user_input == 'n':
                print('Cancelled')
                break
            else:
                print('Invalid Input')
        print('Memory Consolidation Complete')        
        
        