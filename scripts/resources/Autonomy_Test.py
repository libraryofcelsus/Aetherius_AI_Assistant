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
# import speech_recognition as sr
# from gtts import gTTS
# from playsound import playsound
# import pyttsx3
# from pydub import AudioSegment
# from pydub.playback import play
# from pydub import effects


def Autonomy_Test():
    vdb = pinecone.Index("aetherius")
    # # Number of Messages before conversation is summarized, higher number, higher api cost. Change to 3 when using GPT 3.5 due to token usage.
    conv_length = 4
    print("Type [Clear Memory] to clear saved short-term memory.")
    print("Type [Save and Exit] to summarize the conversation, generate episodic memories, then exit.")
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
        timestamp = time()
        timestring = timestamp_to_datetime(timestamp)
        # # Start or Continue Conversation based on if response exists
        conversation.append({'role': 'system', 'content': '%s' % main_prompt})
        int_conversation.append({'role': 'system', 'content': '%s' % main_prompt})
        if 'response_two' in locals():
            conversation.append({'role': 'user', 'content': a})
            if counter % conv_length == 0:
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
        if a == 'Save and Exit':
            conversation2.append({'role': 'user', 'content': "Review the previous messages and summarize the key points of the conversation in a single bullet point format to serve as %s's episodic memories. Each bullet point should be considered a separate memory and contain its entire context. Start from the end and work towards the beginning. Exclude the system prompt and cadence.\nUse the following format: [- SUMMARY]\n\nEPISODIC MEMORIES:" % bot_name})
            conv_summary = chatgptsummary_completion(conversation2)
            print(conv_summary)
            while True:
                print('\n\nSYSTEM: Upload to episodic memory?\n        Press Y for yes or N for no.')
                user_input = input("'Y' or 'N': ")
                if user_input == 'y':
                    lines = conv_summary.splitlines()
                    for line in lines:
                    #    print(timestring + line)
                        vector = gpt3_embedding(timestring + line)
                        unique_id = str(uuid4())
                        metadata = {'speaker': bot_name, 'time': timestamp, 'message': (timestring + line),
                                    'timestring': timestring, 'uuid': unique_id}
                        save_json('nexus/episodic_memory_nexus/%s.json' % unique_id, metadata)
                        payload.append((unique_id, vector))
                        vdb.upsert(payload, namespace='episodic_memories')
                        payload.clear()
                    payload.append((unique_id, vector_input))   
                    vdb.upsert(payload, namespace='flash_counter')
                    payload.clear()
                    print('\n\nSYSTEM: Upload Successful!')
                    return
                elif user_input == 'n':
                    print('\n\nSYSTEM: Memories have been Deleted')
                    return
                elif user_input == 'c':
                    print('\n\nSYSTEM: Exit Cancelled')
                    a = input(f'\n\nUSER: ')
                    break
            else:
                pass
        conversation.append({'role': 'user', 'content': a})        
        # # Generate Semantic Search Terms
        tasklist.append({'role': 'system', 'content': "You are a task coordinator. Your job is to take user input and create a list of 2-5 inquiries to be used for a semantic database search of a chatbot's memories. Use the format [- 'INQUIRY']."})
        tasklist.append({'role': 'user', 'content': "USER INQUIRY: %s" % a})
        tasklist.append({'role': 'assistant', 'content': "List of Semantic Search Terms: "})
        tasklist_output = chatgpt200_completion(tasklist)
    #    print(tasklist_output)
        db_term = {}
        db_term_result = {}
        db_term_result2 = {}
        tasklist_counter = 0
        # # Split bullet points into separate lines to be used as individual queries
        lines = tasklist_output.splitlines()
        for line in lines:
            if line.strip():
                tasklist_vector = gpt3_embedding(line)
                tasklist_counter += 1
                db_term[tasklist_counter] = tasklist_vector
                results = vdb.query(vector=db_term[tasklist_counter], top_k=3, namespace='long_term_memory')
                db_term_result[tasklist_counter] = load_conversation_long_term_memory(results)
                results = vdb.query(vector=db_term[tasklist_counter], top_k=2, namespace='implicit_long_term_memory')
                db_term_result2[tasklist_counter] = load_conversation_implicit_long_term_memory(results)
                conversation.append({'role': 'assistant', 'content': "MEMORIES: %s" % db_term_result[tasklist_counter]})
                conversation.append({'role': 'assistant', 'content': "MEMORIES: %s" % db_term_result2[tasklist_counter]})
                # # Stop updating conversation list for intuition loop to avoid token limit
                if tasklist_counter < 4:
                    int_conversation.append({'role': 'assistant', 'content': "MEMORIES: %s" % db_term_result[tasklist_counter]})
                    int_conversation.append({'role': 'assistant', 'content': "MEMORIES: %s" % db_term_result2[tasklist_counter]})
    #        print(db_term_result[tasklist_counter])
        tasklist.clear()
        # # Search Memory DB
        results = vdb.query(vector=vector_input, top_k=5, namespace='episodic_memories')
        db_search_1 = load_conversation_episodic_memory(results)
        results = vdb.query(vector=vector_input, top_k=8, namespace='short_term_memory')
        db_search_2 = load_conversation_short_term_memory(results)
        results = vdb.query(vector=vector_input, top_k=2, namespace='flashbulb_memory')
        db_search_13 = load_conversation_flashbulb_memory(results)
        # # Search Heuristics DB
        results = vdb.query(vector=vector_input, top_k=5, namespace='heuristics')
        db_search_3= load_conversation_heuristics(results)
        # # Inner Monologue Generation
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
        int_conversation.append({'role': 'assistant', 'content': "MEMORIES: %s;\n%s;\n%s;\n\n%s'S INNER THOUGHTS: %s;\nUSER MESSAGE: %s;\nIn a single paragraph, interpret the user, %s's message as %s in third person by creating an intuitive action plan, even if they are uncertain about their own needs.;\nINTUITION: " % (db_search_4, db_search_5, db_search_12, bot_name, output_one, a, username, bot_name)})
        output_two = chatgpt200_completion(int_conversation)
        message_two = output_two
        print('\n\nINTUITION: %s' % output_two)
        output_two_log = f'\nUSER: {a}\n\n{bot_name}: {output_two}'
        # # Test for basic Autonomous Tasklist Generation and Task Completion
        master_tasklist.append({'role': 'system', 'content': "You are a task list coordinator. Your job is to take a user facing chatbot's intuitive action plan and create a list of inquiries in bullet point format to be used for orchestrating Ai agents. Include every salient task needed up to final completion. Final completion will be handled by another agent.  Use the format: - '____'"})
        master_tasklist.append({'role': 'user', 'content': "CHATBOT'S INTUITIVE ACTION PLAN:\n%s" % output_two})
        master_tasklist.append({'role': 'user', 'content': "Do you understand your imperatives?"})
        master_tasklist.append({'role': 'assistant', 'content': "-Task list coordinator should research its own imperatives.\n-Task list coordinator should confirm if it understands it's imperatives."})
        master_tasklist.append({'role': 'user', 'content': "Very good.  Here is the user's inquiry."})
        master_tasklist.append({'role': 'user', 'content': "USER INQUIRY:\n%s" % a})
        master_tasklist_output = chatgpt_tasklist_completion(master_tasklist)
        print(master_tasklist_output)
        tasklist_completion.append({'role': 'system', 'content': "You are a final execution module. Your job is to take a completed task list, format it for the end user in accordance with their initial request, and then provide the user with a thourogh reply using the information from the tasklist."})
        tasklist_completion.append({'role': 'user', 'content': "%s" % master_tasklist_output})
        task = {}
        task_result = {}
        task_result2 = {}
        task_counter = 1
        # # Split bullet points into separate lines to be used as individual queries
        lines = master_tasklist_output.splitlines()
        for line in lines:
            if line.strip():
                tasklist_completion.append({'role': 'user', 'content': "ASSIGNED TASK:\n%s" % line})
                print(line)
                conversation.append({'role': 'system', 'content': "You are a sub-module for an Autonomous Ai-Chatbot. You are one of many agents in a chain. You are to take the given task and complete it in its entirety. Take future tasks into account when formulating your answer."})
                conversation.append({'role': 'user', 'content': "Task list:\n%s" % master_tasklist_output})
                conversation.append({'role': 'assistant', 'content': "Bot %s: I have studied the given tasklist.  What is my assigned task?" % task_counter})
                conversation.append({'role': 'user', 'content': "Bot %s's Assigned task: %s" % (task_counter, line)})
                conversation.append({'role': 'assistant', 'content': "Bot %s:" % task_counter})
                task_completion = chatgptresponse_completion(conversation)
                conversation.clear()
                task_counter += 1
                print(task_completion)
                tasklist_completion.append({'role': 'assistant', 'content': "COMPLETED TASK:\n%s" % task_completion})
        tasklist_completion.append({'role': 'user', 'content': "Take the given set of tasks and responses and format them into a final response to the user's initial inquiry.  User's initial inquiry: %s" % a})
        final_response_complete = chatgpt_tasklist_completion(tasklist_completion)
        print('\nFINAL OUTPUT:\n%s' % final_response_complete)
        consolidation.clear()
        conversation
        continue