import os
import sys
sys.path.insert(0, './scripts/resources')
import time
import json
import importlib.util
import requests
import tkinter as tk
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, Range, MatchValue
from qdrant_client.http import models


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


# Import Aetherius's Settings
with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
    settings = json.load(f)
# Set embed size from settings to variable
embed_size = settings['embed_size']


# Import Modules From Aetherius
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
# Import Embedding Module
script_path = get_script_path_from_file(json_file_path, "embedding_model")
import_functions_from_script(script_path, "embedding_module")


# Create a Description for the Module
def Example_Template_Description():
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
    description = f"A module serving as an example on how to create a sub-agent for {bot_name}.(The first sentence should state what the module is.)\nThis Module is meant to serve as an example for developers so they can create a custom sub-agent.(The second sentence should provide a breif description on the sub-agent.)\nThis module contains the basic setup needed for sub-agent creation.(The Third sentence should describe the functions of the Module.)"
    return description
    
    
# Add your custom code Here
def Example_Template(self, host, bot_name, username, line, task_counter, output_one, output_two, master_tasklist_output, a):
    try:
        # List used for returning response to main chatbot
        sub_agent_completion = list()
        sub_agent_completion.append({'role': 'user', 'content': f"TASK: {line} [/INST] "})
        

        # Replace the Below Code with your desired script.
        conversation.append({'role': 'system', 'content': f"{line} [/INST]"})
        prompt = ''.join([message_dict['content'] for message_dict in conversation])
        
        
        
        
        # Set Final response to "task_completion", must return a list
        task_completion = oobabooga_response(host, prompt)
        

        
        # Update Aetherius's main chatbot window with results.
        self.conversation_text.insert(tk.END, f"Task {task_counter}: {line}\n")
        self.conversation_text.insert(tk.END, f"Task Completion: {task_completion}\n")
        self.conversation_text.insert(tk.END, f"------------------------------------------------------------------------------------------------------------------\n")
        # Print Output to Debug Console
        print(line)
        print('-------')
        print(task_completion)
        sub_agent_completion.append({'role': 'assistant', 'content': f"COMPLETED TASK: {task_completion} [INST] "})
        return sub_agent_completion
    except Exception as e:
        print(f'Failed with error: {e}')
        error = 'ERROR WITH PROCESS LINE FUNCTION'
        return error