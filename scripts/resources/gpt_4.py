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

            
            
def gpt3_embedding(query, engine='text-embedding-ada-002'):
    max_counter = 7
    counter = 0
    while True:
        try:
            content = query.encode(encoding='ASCII', errors='ignore').decode()  # fix any UNICODE errors
            response = openai.Embedding.create(input=content, engine=engine)
            vector = response['data'][0]['embedding']  # this is a normal list
            return vector
        except Exception as e:
            counter +=1
            if counter >= max_counter:
                print(f"Exiting with error: {e}")
                exit()
            print(f"Retrying with error: {e} in 20 seconds...")
            sleep(20)


                    
                    
def chatgpt200_completion(query):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = openai.ChatCompletion.create(
              model="gpt-4",
              max_tokens=200,
              temperature=0.2,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            counter +=1
            if counter >= max_counter:
                print(f"Exiting with error: {e}")
                exit()
            print(f"Retrying with error: {e} in 20 seconds...")
            sleep(20)

            
            
def chatgpt250_completion(query):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = openai.ChatCompletion.create(
              model="gpt-4",
              max_tokens=250,
              temperature=0.4,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            counter +=1
            if counter >= max_counter:
                print(f"Exiting with error: {e}")
                exit()
            print(f"Retrying with error: {e} in 20 seconds...")
            sleep(20)
            
                    
                    
def chatgpt35_completion(query):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = openai.ChatCompletion.create(
              model="gpt-3.5-turbo",
              max_tokens=250,
              temperature=0.4,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = openai.ChatCompletion.create(
                      model="gpt-3.5-turbo-16k",
                      max_tokens=250,
                      temperature=0.4,
                      messages=query
                    )
                    response = (completion.choices[0].message.content)
                    return response
                except Exception as oops:
                    counter +=1
                    if counter >= max_counter:
                        print(f"Exiting with error: {e}")
                        exit()
                    print(f"Retrying with error: {e} in 20 seconds...")
                    sleep(20)
                    
                    
def chatgpt_tasklist_completion(query):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = openai.ChatCompletion.create(
              model="gpt-4",
              temperature=0.3,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            counter +=1
            if counter >= max_counter:
                print(f"Exiting with error: {e}")
                exit()
            print(f"Retrying with error: {e} in 20 seconds...")
            sleep(20)

                    
                    
def chatgptyesno_completion(query):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = openai.ChatCompletion.create(
              model="gpt-4",
              max_tokens=2,
              temperature=0.1,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            counter +=1
            if counter >= max_counter:
                print(f"Exiting with error: {e}")
                exit()
            print(f"Retrying with error: {e} in 20 seconds...")
            sleep(20)
                            
                    
def chatgptselector_completion(query):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = openai.ChatCompletion.create(
              model="gpt-4",
              max_tokens=4,
              temperature=0.1,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            counter +=1
            if counter >= max_counter:
                print(f"Exiting with error: {e}")
                exit()
            print(f"Retrying with error: {e} in 20 seconds...")
            sleep(20)
                    
            
def chatgptresponse_completion(query):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = openai.ChatCompletion.create(
              model="gpt-4",
              temperature=0.5,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            counter +=1
            if counter >= max_counter:
                print(f"Exiting with error: {e}")
                exit()
            print(f"Retrying with error: {e} in 20 seconds...")
            sleep(20)
            
            
                    
                    
def chatgptauto_completion(query):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = openai.ChatCompletion.create(
              model="gpt-4",
              max_tokens=4,
              temperature=0.35,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            counter +=1
            if counter >= max_counter:
                print(f"Exiting with error: {e}")
                exit()
            print(f"Retrying with error: {e} in 20 seconds...")
            sleep(20)   
                    
            
                    
def chatgptsummary_completion(query):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = openai.ChatCompletion.create(
              model="gpt-4",
              max_tokens=500,
              temperature=0.1,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            counter +=1
            if counter >= max_counter:
                print(f"Exiting with error: {e}")
                exit()
            print(f"Retrying with error: {e} in 20 seconds...")
            sleep(20)   
                    
                    
                    
                    
def chatgptconsolidation_completion(query):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = openai.ChatCompletion.create(
              model="gpt-4",
              max_tokens=600,
              temperature=0.1,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            counter +=1
            if counter >= max_counter:
                print(f"Exiting with error: {e}")
                exit()
            print(f"Retrying with error: {e} in 20 seconds...")
            sleep(20) 