import os
import sys
sys.path.insert(0, './scripts/resources')
from Llama2_chat import *
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, Range, MatchValue
from qdrant_client.http import models
import time
import json
import importlib.util
import requests
import tkinter as tk


Search_Web = False



with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
    settings = json.load(f)
    
embed_size = settings['embed_size']

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
    # print("Connected to local Qdrant server.")
else:
    try:
        url = open_file('./api_keys/qdrant_url.txt')
        api_key = open_file('./api_keys/qdrant_api_key.txt')
        client = QdrantClient(url=url, api_key=api_key)
        client.recreate_collection(
            collection_name="Ping",
            vectors_config=VectorParams(size=1, distance=Distance.COSINE),
        )
        # print("Connected to cloud Qdrant server.")
    except:
        if not os.path.exists("./Qdrant_DB"):
            os.makedirs("./Qdrant_DB")
        client = QdrantClient(path="./Qdrant_DB")
        # print("Neither a local nor a cloud Qdrant server could be connected. Using disk storage.")


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


def get_script_path_from_file(json_path, key, base_folder='./scripts/resources/'):
    """
    Get the script path from a JSON file.

    Parameters:
    - json_path: The path to the JSON file containing the settings.
    - key: The key for the particular setting.
    - base_folder: The base folder where the script is located.
    """
    with open(json_path, 'r', encoding='utf-8') as file:
        settings = json.load(file)
    script_name = settings.get(key, "").strip()
    return f'{base_folder}{script_name}.py'

# Path to the JSON settings file
json_file_path = './config/chatbot_settings.json'

# Import for model
script_path1 = get_script_path_from_file(json_file_path, "model")
import_functions_from_script(script_path1, "model_module")

# Import for embedding model
script_path2 = get_script_path_from_file(json_file_path, "embedding_model")
import_functions_from_script(script_path2, "embedding_module")

# Import for TTS
script_path3 = get_script_path_from_file(json_file_path, "TTS", base_folder='./scripts/resources/TTS/')
import_functions_from_script(script_path3, "TTS_module")


def External_Resource_DB_Search_Description():
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    
    description = f"A module for searching {bot_name}'s External Resource Database.\nThis Module is meant to be used for verifying or searching for external information."
    return description

def External_Resource_DB_Search(self, host, bot_name, username, line, task_counter, output_one, output_two, master_tasklist_output, a):
    try:
        tasklist_completion2 = list()
        memcheck = list()
        memcheck2 = list()
        webcheck = list()
        tasklist_log = list()
        conversation = list()
        botnameupper = bot_name.upper()
        usernameupper = username.upper()
        tasklist_completion2.append({'role': 'user', 'content': f"TASK: {line} [/INST] "})
        conversation.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: You are a sub-agent for {bot_name}, an Autonomous Ai-Chatbot. You are one of many agents in a chain. You are to take the given task and complete it in its entirety, using the given external resources to ensure factual accuracy. Be Verbose and take other tasks into account when formulating your answer.\n"})
        conversation.append({'role': 'user', 'content': f"Task list: {master_tasklist_output}\nNow, choose a task to research.[/INST]"})
        conversation.append({'role': 'assistant', 'content': f"Bot {task_counter}: I have studied the given tasklist. The task I have chosen to complete is: {line}."})
        vector_input1 = embeddings(line)
        table = "No External Resources in DB"
        if self.are_both_web_and_file_db_checked():
            try:
                hits = client.search(
                    collection_name=f"Bot_{bot_name}_External_Knowledgebase",
                    query_vector=vector_input1,
                    query_filter=Filter(
                        must=[
                            FieldCondition(
                                key="user",
                                match=MatchValue(value=f"{username}")
                            )
                        ]
                    ),
                    limit=15
                )
                unsorted_table = [(hit.payload['tag'], hit.payload['message']) for hit in hits]
                sorted_table = sorted(unsorted_table, key=lambda x: x[0])  # Sort by the 'tag' field
                table = "\n".join([f"{tag} - {message}" for tag, message in sorted_table])
                # print(table)
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
                                models.FieldCondition(
                                    key="memory_type",
                                    match=models.MatchValue(value="Web_Scrape"),
                                ),
                                models.FieldCondition(
                                    key="user",
                                    match=models.MatchValue(value=f"{username}"),
                                ),
                            ]
                        ),
                        limit=15
                    )
                    unsorted_table = [(hit.payload['tag'], hit.payload['message']) for hit in hits]
                    sorted_table = sorted(unsorted_table, key=lambda x: x[0])  # Sort by the 'tag' field
                    table = "\n".join([f"{tag} - {message}" for tag, message in sorted_table])
                    # print(table)
                except Exception as e:
                    print(f"An unexpected error occurred: {str(e)}")
            elif self.is_file_db_checked():
                try:
                    hits = client.search(
                        collection_name=f"Bot_{bot_name}_External_Knowledgebase",
                        query_vector=vector_input1,
                        query_filter=Filter(
                            must=[
                                models.FieldCondition(
                                    key="memory_type",
                                    match=models.MatchValue(value="File_Scrape"),
                                ),
                                models.FieldCondition(
                                    key="user",
                                    match=models.MatchValue(value=f"{username}"),
                                ),
                            ]
                        ),
                        limit=15
                    )
                    unsorted_table = [(hit.payload['tag'], hit.payload['message']) for hit in hits]
                    sorted_table = sorted(unsorted_table, key=lambda x: x[0])  # Sort by the 'tag' field
                    table = "\n".join([f"{tag} - {message}" for tag, message in sorted_table])
                    # print(table)
                except Exception as e:
                    print(f"An unexpected error occurred: {str(e)}")
            else:
                table = "No External Resources Selected"
                # print(table)

        result = None
        if self.is_memory_db_checked():
                # # DB Yes No Tool
            memcheck.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: You are a sub-agent for {bot_name}, an Autonomous Ai-Chatbot. Your purpose is to decide if the user's input requires {bot_name}'s past memories to complete. If the user's request pertains to information about the user, the chatbot, {bot_name}, or past personal events should be searched for in memory by # printing 'YES'.  If memories are needed, # print: 'YES'.  If they are not needed, # print: 'NO'. You may only # print YES or NO.\n\n\n"})
            memcheck.append({'role': 'user', 'content': f"USER INPUT: {line}\n\n"})
            memcheck.append({'role': 'assistant', 'content': f"RESPONSE FORMAT: You may only # print Yes or No. Use the format: [{bot_name}: 'YES OR NO'][/INST]ASSISTANT: "})
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
            memcheck2.append({'role': 'assistant', 'content': f"RESPONSE FORMAT: You may only # print the type of memory to be queried. Use the format: [{bot_name}: 'MEMORY TYPE'][/INST]\n\nASSISTANT: "})
                # # Web Search Tool
            webcheck.append({'role': 'system', 'content': f"SYSTEM: You are a sub-module for {bot_name}, an Autonomous AI Chatbot. Your role is part of a chain of agents. Your task is to determine whether the given task is asking for factual data or memories. Please assume that any informational task requires factual data. You do not need to refer to {username} and {bot_name}'s memories, as they are handled by another agent. If reference information is necessary, respond with 'YES'. If reference information is not needed, respond with 'NO'.\n"})
            webcheck.append({'role': 'user', 'content': f"TASK: {line}"})
            #    webcheck.append({'role': 'user', 'content': f"USER: Is reference information needed? Please respond with either 'Yes' or 'No'."})
            webcheck.append({'role': 'assistant', 'content': f"RESPONSE FORMAT: You may only # print 'Yes' or 'No'. Use the format: [{bot_name}: 'YES OR NO'][/INST]ASSISTANT: "})
            #    prompt = ''.join([message_dict['content'] for message_dict in webcheck])
             #   web1 = agent_oobabooga_webyesno(prompt)
            #    # print(web1)
            #    # print('\n-----w-----\n')
                # table := google_search(line) if web1 =='YES' else fail()
                # table := google_search(line, my_api_key, my_cse_id) if web1 == 'YES' else fail()
            #    table = search_webscrape_db(line)

                        
                # google_search(line, my_api_key, my_cse_id)
                # # Check if DB search is needed
            prompt = ''.join([message_dict['content'] for message_dict in memcheck])
            mem1 = agent_oobabooga_memyesno(prompt)
            # print('-----------')
            # print(mem1)
            # print(' --------- ')
                # mem1 := chatgptyesno_completion(memcheck)
                # # Go to conditional for choosing DB Name
            prompt = ''.join([message_dict['content'] for message_dict in memcheck2])
            mem2 = agent_oobabooga_selector(prompt) if 'YES' in mem1.upper() else fail()
            # print('-----------')
            # print(mem2) if 'YES' in mem1.upper() else fail()
            # print(' --------- ')
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
        conversation.append({'role': 'assistant', 'content': f"[INST] INITIAL USER REQUEST: {a}\n Now please provide relevant external resources to answer the query. [/INST]"})
        conversation.append({'role': 'user', 'content': f"Bot {task_counter}: EXTERNAL RESOURCES: {table}"})
        conversation.append({'role': 'user', 'content': f"[INST] SYSTEM: Summarize the pertinent information from the given external sources related to the given task. Present the summarized data in a single, easy-to-understand paragraph. Do not generalize, expand upon, or use any latent knowledge in your summary, only return a truncated version of previously given information. [/INST] Bot {task_counter}: Sure, here is a short summary combining the relevant information needed to complete the given task: "})
        conversation.append({'role': 'assistant', 'content': f"BOT {task_counter}: Sure, here's an overview of the scraped text: "})
        prompt = ''.join([message_dict['content'] for message_dict in conversation])
        task_completion = agent_oobabooga_process_line_response(host, prompt)
            # chatgpt35_completion(conversation),
            # conversation.clear(),
            # tasklist_completion.append({'role': 'assistant', 'content': f"MEMORIES: {memories}\n\n"}),
            # tasklist_completion.append({'role': 'assistant', 'content': f"WEBSCRAPE: {table}\n\n"}),
        tasklist_completion2.append({'role': 'assistant', 'content': f"COMPLETED TASK: {task_completion} [INST] "})
        tasklist_log.append({'role': 'user', 'content': "ASSIGNED TASK:\n%s\n\n" % line})
        tasklist_log.append({'role': 'assistant', 'content': "COMPLETED TASK:\n%s\n\n" % result})
        print('-------')
        self.conversation_text.insert(tk.END, f"Task {task_counter}: {line}\n")
        self.conversation_text.insert(tk.END, f"Task Completion: {task_completion}\n")
        self.conversation_text.insert(tk.END, f"------------------------------------------------------------------------------------------------------------------\n")
        print(line)
        print('-------')
        # print(result)
        # print(table)
        # print('-------')
        print(task_completion)
        return tasklist_completion2
    except Exception as e:
        print(f'Failed with error: {e}')
        error = 'ERROR WITH PROCESS LINE FUNCTION'
        return error