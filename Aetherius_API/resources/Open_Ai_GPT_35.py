import sys
sys.path.insert(0, './Aetherius_API/resources')
sys.path.insert(0, './Aetherius_API/Chatbot_Prompts')
import os
from openai import OpenAI
from Basic_Functions import *
import json
import time
from time import time, sleep
import datetime
from uuid import uuid4

key_path = open_file('./Aetherius_API/api_keys/key_openai.txt')

service = OpenAI(api_key=key_path)

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
            


            
            
            
def Semantic_Terms_Call(query, username, bot_name):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              max_tokens=100,
              temperature=0.8,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      max_tokens=100,
                      temperature=0.8,
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
                    
                    
def Input_Expansion_Call(query, username, bot_name):
    max_counter = 7
    counter = 0

    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              max_tokens=100,
              temperature=0.8,
              messages=query
            )
            response['choices'][0]['message']['content']
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      max_tokens=100,
                      temperature=0.8,
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
                    
                    
def Domain_Selection_Call(query, username, bot_name):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              max_tokens=100,
              temperature=0.8,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      max_tokens=100,
                      temperature=0.8,
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
                    
                    
def Domain_Extraction_Call(query, username, bot_name):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              max_tokens=100,
              temperature=0.8,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      max_tokens=100,
                      temperature=0.8,
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
                    
            
            
def Inner_Monologue_Call(query, username, bot_name):
    max_counter = 7
    counter = 0
    temperature = open_file(f'./Aetherius_API/Generation_Settings/OpenAi/Inner_Monologue/temperature.txt')
    top_p = open_file(f'./Aetherius_API/Generation_Settings/OpenAi/Inner_Monologue/top_p.txt')
    rep_pen = open_file(f'./Aetherius_API/Generation_Settings/OpenAi/Inner_Monologue/rep_pen.txt')
    max_tokens = open_file(f'./Aetherius_API/Generation_Settings/OpenAi/Inner_Monologue/max_tokens.txt')
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              frequency_penalty=float(rep_pen),
              top_p=float(top_p),
              max_tokens=int(max_tokens),
              temperature=float(temperature),
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      frequency_penalty=float(rep_pen),
                      top_p=float(top_p),
                      max_tokens=int(max_tokens),
                      temperature=float(temperature),
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
                    
                    
def Intuition_Call(query, username, bot_name):
    max_counter = 7
    counter = 0
    temperature = open_file(f'./Aetherius_API/Generation_Settings/OpenAi/Intuition/temperature.txt')
    top_p = open_file(f'./Aetherius_API/Generation_Settings/OpenAi/Intuition/top_p.txt')
    rep_pen = open_file(f'./Aetherius_API/Generation_Settings/OpenAi/Intuition/rep_pen.txt')
    max_tokens = open_file(f'./Aetherius_API/Generation_Settings/OpenAi/Intuition/max_tokens.txt')
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              frequency_penalty=float(rep_pen),
              top_p=float(top_p),
              max_tokens=int(max_tokens),
              temperature=float(temperature),
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      frequency_penalty=float(rep_pen),
                      top_p=float(top_p),
                      max_tokens=int(max_tokens),
                      temperature=float(temperature),
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
                    
                    
def Agent_Intuition_Call(query, username, bot_name):
    max_counter = 7
    counter = 0
    temperature = open_file(f'./Aetherius_API/Generation_Settings/OpenAi/Intuition/temperature.txt')
    top_p = open_file(f'./Aetherius_API/Generation_Settings/OpenAi/Intuition/top_p.txt')
    rep_pen = open_file(f'./Aetherius_API/Generation_Settings/OpenAi/Intuition/rep_pen.txt')
    max_tokens = open_file(f'./Aetherius_API/Generation_Settings/OpenAi/Intuition/max_tokens.txt')
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              frequency_penalty=float(rep_pen),
              top_p=float(top_p),
              max_tokens=int(max_tokens),
              temperature=float(temperature),
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      frequency_penalty=float(rep_pen),
                      top_p=float(top_p),
                      max_tokens=int(max_tokens),
                      temperature=float(temperature),
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
                    
                    
def Episodic_Memory_Call(query, username, bot_name):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              max_tokens=300,
              temperature=0.7,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      max_tokens=300,
                      temperature=0.7,
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
                    
                    
def Flash_Memory_Call(query, username, bot_name):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              max_tokens=350,
              temperature=0.7,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      max_tokens=350,
                      temperature=0.7,
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
                    
                    
def Implicit_Memory_Call(query, username, bot_name):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              max_tokens=350,
              temperature=0.8,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      max_tokens=350,
                      temperature=0.8,
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
                    
                    
def Explicit_Memory_Call(query, username, bot_name):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              max_tokens=350,
              temperature=0.8,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      max_tokens=350,
                      temperature=0.8,
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
                    
                    
def Memory_Consolidation_Call(query, username, bot_name):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              max_tokens=500,
              temperature=0.1,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      max_tokens=500,
                      temperature=0.1,
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
                    
     
def Associative_Memory_Call(query, username, bot_name):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              max_tokens=500,
              temperature=0.1,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      max_tokens=500,
                      temperature=0.1,
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
                    
                    
def Response_Call(query, username, bot_name):
    max_counter = 7
    counter = 0
    temperature = open_file(f'./Aetherius_API/Generation_Settings/OpenAi/Response/temperature.txt')
    top_p = open_file(f'./Aetherius_API/Generation_Settings/OpenAi/Response/top_p.txt')
    rep_pen = open_file(f'./Aetherius_API/Generation_Settings/OpenAi/Response/rep_pen.txt')
    max_tokens = open_file(f'./Aetherius_API/Generation_Settings/OpenAi/Response/max_tokens.txt')
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              frequency_penalty=float(rep_pen),
              top_p=float(top_p),
              max_tokens=int(max_tokens),
              temperature=float(temperature),
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      frequency_penalty=float(rep_pen),
                      top_p=float(top_p),
                      max_tokens=int(max_tokens),
                      temperature=float(temperature),
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
                    
                    
def Auto_Call(query, username, bot_name):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              max_tokens=2,
              temperature=0.35,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      max_tokens=2,
                      temperature=0.35,
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
            
            
def Memory_Yes_No_Call(query, username, bot_name):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              max_tokens=1,
              temperature=0.1,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      max_tokens=1,
                      temperature=0.1,
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
            
            
def Bot_Personality_Check_Call(query, username, bot_name):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              max_tokens=1,
              temperature=0.1,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      max_tokens=1,
                      temperature=0.1,
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
                    
                    
def Bot_Personality_Extraction_Call(query, username, bot_name):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              max_tokens=500,
              temperature=0.3,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      max_tokens=500,
                      temperature=0.3,
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
            
            
def Bot_Personality_Generation_Call(query, username, bot_name):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              max_tokens=500,
              temperature=0.3,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      max_tokens=500,
                      temperature=0.3,
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
                    
                   
            
            
def User_Personality_Check_Call(query, username, bot_name):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              max_tokens=1,
              temperature=0.1,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      max_tokens=1,
                      temperature=0.1,
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
                    
def User_Personality_Extraction_Call(query, username, bot_name):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              max_tokens=500,
              temperature=0.3,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      max_tokens=500,
                      temperature=0.3,
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
                    
            
def User_Personality_Generation_Call(query, username, bot_name):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              max_tokens=500,
              temperature=0.3,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      max_tokens=500,
                      temperature=0.3,
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
            
            
def Selector_Call(query, username, bot_name):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              max_tokens=15,
              temperature=0.1,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      max_tokens=4,
                      temperature=0.1,
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
            
            
def Tokens_250_Call(query, username, bot_name):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              max_tokens=250,
              temperature=0.45,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      max_tokens=250,
                      temperature=0.45,
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
            
            
def Webscrape_Call(query, username, bot_name):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              max_tokens=600,
              temperature=0.2,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      max_tokens=600,
                      temperature=0.2,
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
                    
                    
def File_Processor_Call(query, username, bot_name):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              max_tokens=600,
              temperature=0.2,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      max_tokens=600,
                      temperature=0.2,
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
                    
            
            
def Agent_Semantic_Terms_Call(query, username, bot_name):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              max_tokens=100,
              temperature=0.8,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      max_tokens=100,
                      temperature=0.8,
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
            
            
def Agent_Tokens_250_Call(query, username, bot_name):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              max_tokens=250,
              temperature=0.45,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      max_tokens=250,
                      temperature=0.45,
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
            
def Agent_500_Tokens_Call(query, username, bot_name):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              max_tokens=500,
              temperature=0.45,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      max_tokens=500,
                      temperature=0.45,
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
                    
                    
def Agent_800_Tokens_Call(query, username, bot_name):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              max_tokens=800,
              temperature=0.45,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      max_tokens=800,
                      temperature=0.45,
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


def Agent_Master_Tasklist_Call(query, username, bot_name):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              temperature=0.3,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      temperature=0.3,
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


def Agent_Category_Reassign_Call(query, username, bot_name):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              max_tokens=50,
              temperature=0.3,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      max_tokens=50,
                      temperature=0.3,
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


def Agent_Response_Call(query, username, bot_name):
    max_counter = 7
    counter = 0
    temperature = open_file(f'./Aetherius_API/Generation_Settings/OpenAi/Response/temperature.txt')
    top_p = open_file(f'./Aetherius_API/Generation_Settings/OpenAi/Response/top_p.txt')
    rep_pen = open_file(f'./Aetherius_API/Generation_Settings/OpenAi/Response/rep_pen.txt')
    max_tokens = open_file(f'./Aetherius_API/Generation_Settings/OpenAi/Response/max_tokens.txt')
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              frequency_penalty=float(rep_pen),
              top_p=float(top_p),
              max_tokens=int(max_tokens),
              temperature=float(temperature),
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      frequency_penalty=float(rep_pen),
                      top_p=float(top_p),
                      max_tokens=int(max_tokens),
                      temperature=float(temperature),
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


def Agent_Line_Response_Call(query, username, bot_name):
    max_counter = 7
    counter = 0
    temperature = open_file(f'./Aetherius_API/Generation_Settings/OpenAi/Response/temperature.txt')
    top_p = open_file(f'./Aetherius_API/Generation_Settings/OpenAi/Response/top_p.txt')
    rep_pen = open_file(f'./Aetherius_API/Generation_Settings/OpenAi/Response/rep_pen.txt')
    max_tokens = open_file(f'./Aetherius_API/Generation_Settings/OpenAi/Response/max_tokens.txt')
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              frequency_penalty=float(rep_pen),
              top_p=float(top_p),
              max_tokens=int(max_tokens),
              temperature=float(temperature),
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      frequency_penalty=float(rep_pen),
                      top_p=float(top_p),
                      max_tokens=int(max_tokens),
                      temperature=float(temperature),
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


def Agent_Process_Line_Response_Call(query, username, bot_name):
    max_counter = 7
    counter = 0
    temperature = open_file(f'./Aetherius_API/Generation_Settings/OpenAi/Response/temperature.txt')
    top_p = open_file(f'./Aetherius_API/Generation_Settings/OpenAi/Response/top_p.txt')
    rep_pen = open_file(f'./Aetherius_API/Generation_Settings/OpenAi/Response/rep_pen.txt')
    max_tokens = open_file(f'./Aetherius_API/Generation_Settings/OpenAi/Response/max_tokens.txt')
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              frequency_penalty=float(rep_pen),
              top_p=float(top_p),
              max_tokens=int(max_tokens),
              temperature=float(temperature),
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      frequency_penalty=float(rep_pen),
                      top_p=float(top_p),
                      max_tokens=int(max_tokens),
                      temperature=float(temperature),
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


def Agent_Process_Line_Response_2_Call(query, username, bot_name):
    max_counter = 7
    counter = 0
    temperature = open_file(f'./Aetherius_API/Generation_Settings/OpenAi/Response/temperature.txt')
    top_p = open_file(f'./Aetherius_API/Generation_Settings/OpenAi/Response/top_p.txt')
    rep_pen = open_file(f'./Aetherius_API/Generation_Settings/OpenAi/Response/rep_pen.txt')
    max_tokens = open_file(f'./Aetherius_API/Generation_Settings/OpenAi/Response/max_tokens.txt')
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              frequency_penalty=float(rep_pen),
              top_p=float(top_p),
              max_tokens=int(max_tokens),
              temperature=float(temperature),
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      frequency_penalty=float(rep_pen),
                      top_p=float(top_p),
                      max_tokens=int(max_tokens),
                      temperature=float(temperature),
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


def Agent_Memory_DB_Check_Call(query, username, bot_name):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              max_tokens=1,
              temperature=0.1,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      max_tokens=1,
                      temperature=0.1,
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
                    
                    
def Google_Rephrase_Call(query, username, bot_name):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              max_tokens=100,
              temperature=0.6,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      max_tokens=100,
                      temperature=0.6,
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


def Agent_Webcheck_Yes_No(query, username, bot_name):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              max_tokens=1,
              temperature=0.1,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      max_tokens=1,
                      temperature=0.1,
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


def Agent_Web_Yes_No(query, username, bot_name):
    max_counter = 7
    counter = 0
    while True:
        try:
            completion = service.chat.completions.create(
              model="gpt-3.5-turbo",
              max_tokens=1,
              temperature=0.1,
              messages=query
            )
            response = (completion.choices[0].message.content)
            return response
        except Exception as e:
            while True:
                try:
                    completion = service.chat.completions.create(
                      model="gpt-3.5-turbo-16k",
                      max_tokens=1,
                      temperature=0.1,
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
