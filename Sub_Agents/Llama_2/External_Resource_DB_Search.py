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


# Set to True if you want Aetherius to search the web if the information cannot be found in it's external resources database.
Search_Web = True

# Set the desired search engine to use if information cannot be found in DB
# Available Options: "Google, Bing"
Search_Engine = "Google"



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
        websearch_check = list()
        websearch_rephrase = list()
        botnameupper = bot_name.upper()
        usernameupper = username.upper()
        tasklist_completion2.append({'role': 'user', 'content': f"TASK: {line} [/INST] "})
        conversation.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: You are a sub-agent for {bot_name}, an Autonomous Ai-Chatbot. You are one of many agents in a chain. You are to take the given task and complete it in its entirety, using the given external resources to ensure factual accuracy. Be Verbose and take other tasks into account when formulating your answer.\n"})
        conversation.append({'role': 'user', 'content': f"Task list: {master_tasklist_output}\nNow, choose a task to research.[/INST]"})
        conversation.append({'role': 'assistant', 'content': f"Bot {task_counter}: I have studied the given tasklist. The task I have chosen to complete is: {line}."})
        vector_input1 = embeddings(line)
        table = "No External Resources in DB"
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
        except:
            table = "No External Resources Available"
            
        if Search_Web == True:    
            websearch_check.append({'role': 'assistant', 'content': f"You are a selection agent for an autonomous AI chatbot.  Your job is to decide if the given database queries contain the needed information to answer the user's inquiry.  Only respond with either 'YES' or 'NO'.\n\nGIVEN DATABASE QUERIES: {table}\n\nUSER INQUIRY: {a} [/INST] "})
            prompt = ''.join([message_dict['content'] for message_dict in websearch_check])
            web_check = agent_oobabooga_memory_db_check(host, prompt)
            print(web_check)
            if "NO" in web_check:
                websearch_rephrase.append({'role': 'assistant', 'content': f"Extract any salient informational requests from the user's query and rephrase them into an informational search query that will return the requested information.  Only print the search query.\nUSER INQUIRY: {line} [/INST] Google Search Query: "})
                prompt = ''.join([message_dict['content'] for message_dict in websearch_rephrase])
                rephrased_query = agent_oobabooga_google_rephrase(host, prompt)
                if '"' in rephrased_query:
                    rephrased_query = rephrased_query.replace('"', '')
                print(rephrased_query)
                if Search_Engine == "Google":
                    try:
                        my_api_key = open_file('api_keys/key_google.txt')
                        my_cse_id = open_file('api_keys/key_google_cse.txt')
                        
                        params = {
                            "key": my_api_key,
                            "cx": my_cse_id,
                            "q": rephrased_query,
                            "num": 10,
                            "snippet": True
                        }
                        
                        response = requests.get("https://www.googleapis.com/customsearch/v1", params=params)
                        
                        if response.status_code == 200:
                            data = response.json()
                            table = [item['snippet'] for item in data.get("items", [])]  # Return a list of snippets
                        else:
                            raise Exception(f"Request failed with status code {response.status_code}")
                            table = "Google Search Failed"
                    except Exception as e:
                        print(e)
                        table = "Google Search Failed.  Remind user they need to add the Google Api key to the api keys folder or disable the web-search in the External Resources Sub-Agent."
                        self.conversation_text.insert(tk.END, f"{table}\n")
                        self.conversation_text.insert(tk.END, f"------------------------------------------------------------------------------------------------------------------\n")
                        print(table)

                if Search_Engine == "Bing":
                    try:
                        subscription_key = open_file('./api_keys/key_bing.txt')
                        assert subscription_key
                        search_url = "https://api.bing.microsoft.com/v7.0/search"

                        headers = {"Ocp-Apim-Subscription-Key": subscription_key}
                        params = {"q": rephrased_query, "textDecorations": True, "textFormat": "HTML"}

                        response = requests.get(search_url, headers=headers, params=params)
                        response.raise_for_status()
                        search_results = response.json()
                        results = search_results
                        rows = "\n".join(["""<tr>
                                            <td><a href=\"{0}\">{1}</a></td>
                                            <td>{2}</td>
                                            </tr>""".format(v["url"], v["name"], v["snippet"])
                                        for v in results["webPages"]["value"]])
                        table = "<table>{0}</table>".format(rows)
                    except Exception as e:
                        print(e)
                        table = "Bing Search Failed.  Remind user they need to add the Bing Api key to the api keys folder or disable the web-search in the External Resources Sub-Agent."
                        self.conversation_text.insert(tk.END, f"{table}\n")
                        self.conversation_text.insert(tk.END, f"------------------------------------------------------------------------------------------------------------------\n")
                        print(table)

        
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