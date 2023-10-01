import os
import sys
sys.path.insert(0, './Aetherius_API/resources')
from Llama2_chat_Async import *
import time
import json
import importlib.util
import requests
import tkinter as tk
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, Range, MatchValue
from qdrant_client.http import models
import asyncio
import aiofiles


def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
       return file.read().strip()


# Check if Qdrant Server is Running
def check_local_server_running():
    try:
        response = requests.get("http://localhost:6333/dashboard/")
        return response.status_code == 200
    except requests.ConnectionError:
        return False

# Connect to Qdrant Server
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


# Import Aetherius's Settings
with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
    settings = json.load(f)
# Set embed size from settings to variable
embed_size = settings['embed_size']





model = SentenceTransformer('all-mpnet-base-v2')


def embeddings(query):
    vector = model.encode([query])[0].tolist()
    return vector

def fail():
  #  print('')
    fail = "Not Needed"
    return fail  


async def search_episodic_db(line_vec, username, bot_name):
    try:
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
        
        
async def search_implicit_db(line_vec, username, bot_name):
    try:
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
        
        
async def search_flashbulb_db(line_vec, username, bot_name):
    try:
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
        
        
async def search_explicit_db(line_vec, username, bot_name):
    try:
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
        except Exception as e:
            if "Not found: Collection" in str(e):
                print("Collection has no memories.")
            else:
                print(f"An unexpected error occurred: {str(e)}")
    
        try:
            hits = client.search(
                collection_name=f"Bot_{bot_name}_{username}_Explicit_Short_Term",
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
        




# Create a Description for the Module
def Memory_DB_Search_Description(username, bot_name):
    description = f"A module for searching {bot_name}'s Memories.\nThis Module is meant to be used for answering questions about {bot_name}'s past, {username}'s past, or previous interactions or events in {bot_name}'s existance."
    return description
    
    
# Add your custom code Here
async def Memory_DB_Search(host, bot_name, username, line, task_counter, output_one, output_two, master_tasklist_output, user_input):
    try:
        async with aiofiles.open('./Aetherius_API/chatbot_settings.json', mode='r', encoding='utf-8') as f:
            settings = json.loads(await f.read())
        embed_size = settings['embed_size']
        Sub_Module_Output = settings.get('Output_Sub_Module', 'False')
        # List used for returning response to main chatbot
        tasklist_completion2 = list()
        conversation = list()
        memcheck  = list()
        memcheck2 = list()
        sub_agent_completion = list()
        sub_agent_completion.append({'role': 'user', 'content': f"TASK: {line} [/INST] "})
        botnameupper = bot_name.upper()
        usernameupper = username.upper()
        task_completion = "Task Failed"
        
        try:
            conversation.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: You are a sub-agent for {bot_name}, an Autonomous Ai-Chatbot. You are one of many agents in a chain. You are to take the given task and complete it in its entirety, using the given external resources to ensure factual accuracy. Be Verbose and take other tasks into account when formulating your answer.\n"})
            conversation.append({'role': 'user', 'content': f"Task list: {master_tasklist_output}\nNow, choose a task to research.[/INST]"})
            conversation.append({'role': 'assistant', 'content': f"Bot {task_counter}: I have studied the given tasklist. The task I have chosen to complete is: {line}."})
            vector_input1 = embeddings(line)
            result = None
                # # DB Yes No Tool
            memcheck.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: You are a sub-agent for {bot_name}, an Autonomous Ai-Chatbot. Your purpose is to decide if the user's input requires {bot_name}'s past memories to complete. If the user's request pertains to information about the user, the chatbot, {bot_name}, or past personal events should be searched for in memory by printing 'YES'.  If memories are needed, print: 'YES'.  If they are not needed, print: 'NO'. You may only print YES or NO.\n\n\n"})
            memcheck.append({'role': 'user', 'content': f"USER INPUT: {line}\n\n"})
            memcheck.append({'role': 'assistant', 'content': f"RESPONSE FORMAT: You may only print Yes or No. Use the format: [{bot_name}: 'YES OR NO'][/INST]ASSISTANT: "})
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
            memcheck2.append({'role': 'assistant', 'content': f"RESPONSE FORMAT: You may only print the type of memory to be queried. Use the format: [{bot_name}: 'MEMORY TYPE'][/INST]\n\nASSISTANT: "})
                # # Check if DB search is needed
            try:
                prompt = ''.join([message_dict['content'] for message_dict in memcheck])
                mem1 = await agent_oobabooga_memyesno(prompt, username, bot_name)
            
            except Exception as e:
                mem1 = 'No'
                print(e)
            try:
                # mem1 := chatgptyesno_completion(memcheck)
                # # Go to conditional for choosing DB Name
                prompt = ''.join([message_dict['content'] for message_dict in memcheck2])
                mem2 = await agent_oobabooga_selector(prompt, username, bot_name) if 'YES' in mem1.upper() else fail()
                line_vec = embeddings(line)  # EPISODIC, FLASHBULB, IMPLICIT LONG TERM, EXPLICIT LONG TERM
                mem2_upper = mem2.upper()

                if 'EPISO' in mem2_upper:
                    result = await search_episodic_db(line_vec, username, bot_name)
                    conversation.append({'role': 'assistant', 'content': f"MEMORIES: {result}\n\n"})
                elif 'IMPLI' in mem2_upper:
                    result = await search_implicit_db(line_vec, username, bot_name)
                    conversation.append({'role': 'assistant', 'content': f"MEMORIES: {result}\n\n"})
                elif 'FLASH' in mem2_upper:
                    result = await search_flashbulb_db(line_vec, username, bot_name)
                    conversation.append({'role': 'assistant', 'content': f"MEMORIES: {result}\n\n"})
                elif 'EXPL' in mem2_upper:
                    result = await search_explicit_db(line_vec, username, bot_name)
                    conversation.append({'role': 'assistant', 'content': f"MEMORIES: {result}\n\n"})
                else:
                    result = ('No Memories')

            except Exception as e:
                print(e)
            conversation.append({'role': 'user', 'content': f"[INST] SYSTEM: Summarize the pertinent information from the given memories related to the given task. Present the summarized data in a single, easy-to-understand paragraph. Do not generalize, expand upon, or use any latent knowledge in your summary, only return a truncated version of previously given information. [/INST] Bot {task_counter}: Sure, here is a short summary combining the relevant information needed to complete the given task: "})
            conversation.append({'role': 'assistant', 'content': f"BOT {task_counter}: Sure, here's an overview of the scraped text: "})
            prompt = ''.join([message_dict['content'] for message_dict in conversation])
            task_completion = await agent_oobabooga_process_line_response(host, prompt, username, bot_name)
            # chatgpt35_completion(conversation),
            conversation.clear()
            sub_agent_completion.append({'role': 'assistant', 'content': f"COMPLETED TASK: {task_completion} [INST] "})
            if Sub_Module_Output == 'True':
                print(line)
                print('-------')
                print(task_completion)
            return sub_agent_completion
        except Exception as e:
            print(f'Failed with error: {e}')
            conversation.append({'role': 'system', 'content': f"ERROR WITH MEMORY DB FUNCTION"})
            return conversation

    except Exception as e:
        print(f'Failed with error: {e}')
        error = 'ERROR WITH PROCESS LINE FUNCTION'
        return error