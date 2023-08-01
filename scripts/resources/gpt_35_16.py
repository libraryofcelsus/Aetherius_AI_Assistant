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


def gpt3_embedding(content, engine='text-embedding-ada-002'):
    max_retry = 7
    retry = 0
    while True:
        try:
            content = content.encode(encoding='ASCII', errors='ignore').decode()  # fix any UNICODE errors
            response = openai.Embedding.create(input=content, engine=engine)
            vector = response['data'][0]['embedding']  # this is a normal list
            return vector
        except Exception as oops:
            retry += 1
            if retry >= max_retry:
                print(f"Exiting due to an error in ChatGPT: {oops}")
                exit(1)
            print(f'Error communicating with OpenAI: "{oops}" - Retrying in {2 ** (retry - 1) * 5} seconds...')
            sleep(2 ** (retry - 1) * 5)
    
    
def chatgpt200_completion(messages, model="gpt-3.5-turbo-16k", temp=0.2):
    max_retry = 7
    retry = 0
    while  True:
        try:
            response = openai.ChatCompletion.create(model=model, messages=messages, max_tokens=300)
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
            
            
def chatgpt250_completion(messages, model="gpt-3.5-turbo-16k", temp=0.45):
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
            
            
def chatgpt_tasklist_completion(messages, model="gpt-3.5-turbo-16k", temp=0.3):
    max_retry = 7
    retry = 0
    while True:
        try:
            response = openai.ChatCompletion.create(model=model, messages=messages)
            text = response['choices'][0]['message']['content']
            temperature = temp
            return text
        except Exception as oops:
            while True:
                try:
                    response = openai.ChatCompletion.create(model="gpt-3.5-turbo-16k", messages=messages, max_tokens=1000)
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
                    
                    
def chatgpt35_completion(messages, model="gpt-3.5-turbo", temp=0.3):
    max_retry = 7
    retry = 0
    while True:
        try:
            response = openai.ChatCompletion.create(model=model, messages=messages)
            text = response['choices'][0]['message']['content']
            temperature = temp
            return text
        except Exception as oops:
            while True:
                try:
                    response = openai.ChatCompletion.create(model="gpt-3.5-turbo-16k", messages=messages, max_tokens=500)
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
                    
                    
            
                
def chatgptyesno_completion(messages, model="gpt-3.5-turbo-16k", temp=0.0):
    max_retry = 7
    retry = 0
    while True:
        try:
            response = openai.ChatCompletion.create(model=model, messages=messages, max_tokens=1)
            text = response['choices'][0]['message']['content']
            temperature = temp
        #    filename = '%s_chat.txt' % time()
        #    if not os.path.exists('chat_logs'):
        #        os.makedirs('chat_logs')
        #    save_file('chat_logs/%s' % filename, str(messages) + '\n\n==========\n\n' + text)
            return text
        except Exception as oops:
            retry += 1
            if retry >= max_retry:
                print(f"Exiting due to an error in ChatGPT: {oops}")
                exit(1)
            print(f'Error communicating with OpenAI: "{oops}" - Retrying in {2 ** (retry - 1) * 5} seconds...')
            sleep(2 ** (retry - 1) * 5)
            
            
def chatgptselector_completion(messages, model="gpt-3.5-turbo-16k", temp=0.1):
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
            return text
        except Exception as oops:
            while True:
                try:
                    response = openai.ChatCompletion.create(model="gpt-3.5-turbo-16k", messages=messages, max_tokens=4)
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
            
                    
                    
def chatgptresponse_completion(messages, model="gpt-3.5-turbo-16k", temp=0.5):
    max_retry = 7
    retry = 0
    while True:
        try:
            response = openai.ChatCompletion.create(model=model, messages=messages, max_tokens=1000)
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
   
                    
def chatgptsummary_completion(messages, model="gpt-3.5-turbo-16k", temp=0.1):
    max_retry = 5
    retry = 0
    while True:
        try:
            response = openai.ChatCompletion.create(model=model, messages=messages, max_tokens=500)
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
            
            
def chatgptauto_completion(messages, model="gpt-3.5-turbo-16k", temp=0.35):
    max_retry = 7
    retry = 0
    while  True:
        try:
            response = openai.ChatCompletion.create(model=model, messages=messages)
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
            
            
def chatgptconsolidation_completion(messages, model="gpt-3.5-turbo-16k", temp=0.1):
    max_retry = 5
    retry = 0
    while True:
        try:
            response = openai.ChatCompletion.create(model=model, messages=messages, max_tokens=1000)
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