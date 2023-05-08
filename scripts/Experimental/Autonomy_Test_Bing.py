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
import concurrent.futures
# import speech_recognition as sr
# from gtts import gTTS
# from playsound import playsound
# import pyttsx3
# from pydub import AudioSegment
# from pydub.playback import play
# from pydub import effects


    
def bing_search(query):
    subscription_key = open_file('api_keys/key_bing.txt')
    assert subscription_key
    search_url = "https://api.bing.microsoft.com/v7.0/search"

    headers = {"Ocp-Apim-Subscription-Key": subscription_key}
    params = {"q": query, "textDecorations": True, "textFormat": "HTML"}

    response = requests.get(search_url, headers=headers, params=params)
    response.raise_for_status()
    search_results = response.json()
    return search_results



def Autonomy_Test_Bing():
    vdb = pinecone.Index("aetherius")
    # # Number of Messages before conversation is summarized, higher number, higher api cost. Change to 3 when using GPT 3.5 due to token usage.
    conv_length = 4
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
    counter = 0
    counter2 = 0
    mem_counter = 0
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
    main_prompt = open_file('./config/Chatbot_Prompts/prompt_main.txt').replace('<<NAME>>', bot_name)
    second_prompt = open_file('./config/Chatbot_Prompts/prompt_secondary.txt')
    greeting_msg = open_file('./config/Chatbot_Prompts/prompt_greeting.txt').replace('<<NAME>>', bot_name)
 #   r = sr.Recognizer()
    while True:
        # # Get Timestamp
        vdb = timeout_check()
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
                conversation.append({'role': 'assistant', 'content': '%s.' % conv_summary})
            pass
        else:
            conversation.append({'role': 'assistant', 'content': "%s" % greeting_msg})
            print("\n%s" % greeting_msg)
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
                    vdb.delete(delete_all=True, namespace="short_term_memory")
                    vdb.delete(delete_all=True, namespace="implicit_short_term_memory")
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
        tasklist.append({'role': 'system', 'content': "You are a task coordinator. Your job is to take user input and create a list of 2-5 inquiries to be used for a semantic database search of a chatbot's memories. Use the format [- 'INQUIRY']."})
        tasklist.append({'role': 'user', 'content': "USER INQUIRY: %s" % a})
        tasklist.append({'role': 'assistant', 'content': "List of Semantic Search Terms: "})
        tasklist_output = chatgpt200_completion(tasklist)
    #    print(tasklist_output)
        lines = tasklist_output.splitlines()
        db_term = {}
        db_term_result = {}
        db_term_result2 = {}
        tasklist_counter = 0
        # # Split bullet points into separate lines to be used as individual queries
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(
                    lambda line, _index, conversation, int_conversation: (
                        tasklist_vector := gpt3_embedding(line),
                        db_term.update({_index: tasklist_vector}),
                        results := vdb.query(vector=db_term[_index], top_k=3, namespace='long_term_memory'),
                        db_term_result.update({_index: load_conversation_long_term_memory(results)}),
                        results := vdb.query(vector=db_term[_index], top_k=2, namespace='implicit_long_term_memory'),
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
                    vdb.query(vector=vector_input, top_k=5, namespace='episodic_memories'),
                    load_conversation_episodic_memory)
                ),
                executor.submit(lambda: (
                    vdb.query(vector=vector_input, top_k=8, namespace='short_term_memory'),
                    load_conversation_short_term_memory)
                ),
                executor.submit(lambda: (
                    vdb.query(vector=vector_input, top_k=2, namespace='flashbulb_memory'),
                    load_conversation_flashbulb_memory)
                ),
                executor.submit(lambda: (
                    vdb.query(vector=vector_input, top_k=5, namespace='heuristics'),
                    load_conversation_heuristics)
                ),
            ]
            # Handle results
            db_search_1 = futures[len(lines)].result()[1](futures[len(lines)].result()[0])
            db_search_2 = futures[len(lines) + 1].result()[1](futures[len(lines) + 1].result()[0])
            db_search_3 = futures[len(lines) + 2].result()[1](futures[len(lines) + 2].result()[0])
            db_search_4 = futures[len(lines) + 3].result()[1](futures[len(lines) + 3].result()[0])
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
        results = vdb.query(vector=vector_monologue, top_k=5, namespace='episodic_memories')
        db_search_4 = load_conversation_episodic_memory(results)
        results = vdb.query(vector=vector_input, top_k=10, namespace='short_term_memory')
        db_search_5 = load_conversation_short_term_memory(results)
        results = vdb.query(vector=vector_monologue, top_k=2, namespace='flashbulb_memory')
        db_search_12 = load_conversation_flashbulb_memory(results)
        # # Intuition Generation
        int_conversation.append({'role': 'assistant', 'content': "%s" % greeting_msg})
        int_conversation.append({'role': 'user', 'content': a})
        int_conversation.append({'role': 'assistant', 'content': "MEMORIES: %s;\n%s;\n%s;\n\n%s'S INNER THOUGHTS: %s;\nUSER MESSAGE: %s;\nIn a single paragraph, interpret the user, %s's message as %s in third person by creating an intuitive plan on what information needs to be researched, even if the user is uncertain about their own needs.;\nINTUITION: " % (db_search_4, db_search_5, db_search_12, bot_name, output_one, a, username, bot_name)})
        output_two = chatgpt200_completion(int_conversation)
        message_two = output_two
        print('\n\nINTUITION: %s' % output_two)
        output_two_log = f'\nUSER: {a}\n\n{bot_name}: {output_two}'
        # # Test for basic Autonomous Tasklist Generation and Task Completion
        master_tasklist.append({'role': 'system', 'content': "You are a stateless task list coordinator. Your job is to take the user's input and transform it into a list of independent research queries that can be executed by separate AI agents in a cluster computing environment. The other asynchronous Ai agents are also stateless and cannot communicate with each other or the user during task execution. Exclude tasks involving final product production, hallucinations, user communication, or checking work with other agents. Respond using the following format: '- [task]'"})
        master_tasklist.append({'role': 'user', 'content': "USER FACING CHATBOT'S INTUITIVE ACTION PLAN:\n%s" % output_two})
        master_tasklist.append({'role': 'user', 'content': "USER INQUIRY:\n%s" % a})
        master_tasklist.append({'role': 'user', 'content': "SEMANTICALLY SIMILAR INQUIRIES:\n%s" % tasklist_output})
        master_tasklist.append({'role': 'assistant', 'content': "TASK LIST:"})
        master_tasklist_output = chatgpt_tasklist_completion(master_tasklist)
        print(master_tasklist_output)
        tasklist_completion.append({'role': 'system', 'content': "You are the final response module of a cluster compute Ai-Chatbot. Your job is to take the completed task list, and give a verbose response to the end user in accordance with their initial request."})
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
                        lambda line, task_counter, conversation, tasklist_completion: (
                            tasklist_completion.append({'role': 'user', 'content': "ASSIGNED TASK:\n%s" % line}),
                            conversation.append({'role': 'system', 'content': "You are a sub-module for an Autonomous Ai-Chatbot. You are one of many agents in a chain. You are to take the given task and complete it in its entirety. Take other tasks into account when formulating your answer."}),
                            conversation.append({'role': 'user', 'content': "Task list:\n%s" % master_tasklist_output}),
                            conversation.append({'role': 'assistant', 'content': "Bot %s: I have studied the given tasklist.  What is my assigned task?" % task_counter}),
                            conversation.append({'role': 'user', 'content': "Bot %s's Assigned task: %s" % (task_counter, line)}),
                            results := bing_search(line),
                            rows := "\n".join(["""<tr>
                                                <td><a href=\"{0}\">{1}</a></td>
                                                <td>{2}</td>
                                                </tr>""".format(v["url"], v["name"], v["snippet"])
                                            for v in results["webPages"]["value"]]),
                            table := "<table>{0}</table>".format(rows),
                            conversation.append({'role': 'assistant', 'content': "WEBSEARCH: %s" % table}),
                            conversation.append({'role': 'user', 'content': "Bot %s Task Reinitialization: %s" % (task_counter, line)}),
                            conversation.append({'role': 'assistant', 'content': "Bot %s's Response:" % task_counter}),
                            task_completion := chatgpt35_completion(conversation),
                            conversation.clear(),
                            tasklist_completion.append({'role': 'assistant', 'content': "COMPLETED TASK:\n%s" % task_completion}),
                            tasklist_log.append({'role': 'user', 'content': "ASSIGNED TASK:\n%s\n\n" % line}),
                            tasklist_log.append({'role': 'assistant', 'content': "WEBSEARCH:\n%s\n\n" % table}),
                            tasklist_log.append({'role': 'assistant', 'content': "COMPLETED TASK:\n%s\n\n" % task_completion}),
                            print(line),
                            print(table),
                            print(task_completion),
                        ) if line != "None" else tasklist_completion,
                        line, task_counter, conversation.copy(), []
                    )
                    for task_counter, line in enumerate(lines)
                ]
            tasklist_completion.append({'role': 'user', 'content': "Take the given set of tasks and completed responses and transmute them into a verbose response for the end user in accordance with their request. The end user is both unaware and unable to see any of your research. User's initial request: %s" % a})
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
        continue
