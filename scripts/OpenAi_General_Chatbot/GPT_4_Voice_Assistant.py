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
import multiprocessing
import concurrent.futures
from gpt_4 import *
import speech_recognition as sr
from gtts import gTTS
from playsound import playsound
import pyttsx3
from pydub import AudioSegment
from pydub.playback import play
from pydub import effects


class MainConversation:
    def __init__(self, max_entries, prompt, greeting):
        self.max_entries = max_entries
        self.file_path = 'main_conversation_history.json'
        self.main_conversation = [prompt, greeting]

        # Load existing conversation from file
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as f:
                data = json.load(f)
                self.running_conversation = data.get('running_conversation', [])
        else:
            self.running_conversation = []

    def append(self, timestring, username, a, bot_name, output_one, output_two, response_two):
        # Append new entry to the running conversation
        entry = []
        entry.append(f"{timestring}-{username}: {a}")
        entry.append(f"{bot_name}'s Inner Monologue: {output_one}\n")
        entry.append(f"Intuition: {output_two}\n")
        entry.append(f"Response: {response_two}\n")

        self.running_conversation.append(entry)

        # Remove oldest entry if conversation length exceeds max entries
        while len(self.running_conversation) > self.max_entries:
            self.running_conversation.pop(0)

        self.save_to_file()

    def save_to_file(self):
        # Combine main conversation and formatted running conversation for saving to file
        data_to_save = {
            'main_conversation': self.main_conversation,
            'running_conversation': self.running_conversation
        }

        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=4)
            

    def get_conversation_history(self):
        return self.main_conversation + [message for entry in self.running_conversation for message in entry]


def GPT_4_Voice_Assistant():
    vdb = pinecone.Index("aetherius")
    # # Number of Messages before conversation is summarized, higher number, higher api cost. Change to 3 when using GPT 3.5 due to token usage.
    m = multiprocessing.Manager()
    lock = m.Lock()
    print("Type [Clear Memory] to clear saved short-term memory and conversation history.")
    print("Type [Exit] to exit to the main menu.")
    tasklist = list()
    conversation = list()
    int_conversation = list()
    conversation2 = list()
    summary = list()
    auto = list()
    payload = list()
    consolidation  = list()
    counter = 0
    counter2 = 0
    mem_counter = 0
    length_config = open_file('./config/Conversation_Length.txt')
    conv_length = int(length_config)
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
    main_prompt = open_file('./config/Chatbot_Prompts/prompt_main.txt').replace('<<NAME>>', bot_name)
    second_prompt = open_file('./config/Chatbot_Prompts/prompt_secondary.txt')
    final_prompt = open_file('./config/Chatbot_Prompts/prompt_final.txt')
    greeting_msg = open_file('./config/Chatbot_Prompts/prompt_greeting.txt').replace('<<NAME>>', bot_name)
    main_conversation = MainConversation(conv_length, main_prompt, greeting_msg)
  #  conversation_history = open_file('main_conversation_history.txt')
    r = sr.Recognizer()
    while True:
        conversation_history = main_conversation.get_conversation_history()
        # # Get Timestamp
        vdb = timeout_check()
        timestamp = time()
        timestring = timestamp_to_datetime(timestamp)
        # # Start or Continue Conversation based on if response exists
        conversation.append({'role': 'system', 'content': '%s' % main_prompt})
        int_conversation.append({'role': 'system', 'content': '%s' % main_prompt})
        if 'response_two' in locals():
            conversation.append({'role': 'user', 'content': a})
            conversation.append({'role': 'assistant', 'content': "%s" % response_two})
            pass
        else:
            conversation.append({'role': 'assistant', 'content': "%s" % greeting_msg})
            print("\n%s" % greeting_msg)
        # # User Input Voice
        yn_voice = input(f'\n\nPress Enter to Speak')
        if yn_voice == "":
            with sr.Microphone() as source:
                print("\nSpeak now")
                audio = r.listen(source)
                try:
                    text = r.recognize_google(audio)
                    print("\nUSER: " + text)
                except sr.UnknownValueError:
                    print("Google Speech Recognition could not understand audio")
                    print("\nSYSTEM: Press Left Alt to Speak to Aetherius")
                    break
                except sr.RequestError as e:
                    print("Could not request results from Google Speech Recognition service; {0}".format(e))
                    break
        else:
            print('Leave Field Empty')
        a = (f'\n\nUSER: {text}')
        # # User Input Text
    #    a = input(f'\n\nUSER: ')
        message_input = a
        vector_input = gpt3_embedding(message_input)
        # # Check for Commands
        # # Check for "Clear Memory"
        if a == 'Clear Memory':
            while True:
                print('\n\nSYSTEM: Are you sure you would like to delete saved short-term memory?\n        Press Y for yes or N for no.')
                user_input = input("'Y' or 'N': ")
                if user_input == 'y':
                    vdb.delete(delete_all=True, namespace=f'short_term_memory_User_{username}_Bot_{bot_name}')
                    file_path = 'main_conversation_history.json'
                    if os.path.exists(file_path):
                        os.remove(file_path)
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
        conversation.append({'role': 'user', 'content': a})        
        # # Generate Semantic Search Terms
        tasklist.append({'role': 'system', 'content': "You are a task coordinator. Your job is to take user input and create a list of 2-5 inquiries to be used for a semantic database search of a chatbot's memories. Use the format [- 'INQUIRY']."})
        tasklist.append({'role': 'user', 'content': "USER INQUIRY: %s" % a})
        tasklist.append({'role': 'assistant', 'content': "List of Semantic Search Terms: "})
        tasklist_output = chatgpt200_completion(tasklist)
        lines = tasklist_output.splitlines()
        db_term = {}
        db_term_result = {}
        db_term_result2 = {}
        tasklist_counter = 0
        # # Split bullet points into separate lines to be used as individual queries during a parallel db search
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(
                    lambda line, _index, conversation, int_conversation: (
                        tasklist_vector := gpt3_embedding(line),
                        db_term.update({_index: tasklist_vector}),
                        results := vdb.query(vector=db_term[_index], filter={
        "memory_type": "explicit_long_term", "user": username}, top_k=4, namespace=f'{bot_name}'),
                        db_term_result.update({_index: load_conversation_explicit_long_term_memory(results)}),
                        results := vdb.query(vector=db_term[_index], filter={
        "memory_type": "implicit_long_term", "user": username}, top_k=4, namespace=f'{bot_name}'),
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
                    vdb.query(vector=vector_input, filter={
        "memory_type": "episodic", "user": username}, top_k=7, namespace=f'{bot_name}'),
                    load_conversation_episodic_memory)
                ),
                executor.submit(lambda: (
                    vdb.query(vector=vector_input, filter={
        "memory_type": "explicit_short_term"}, top_k=6, namespace=f'short_term_memory_User_{username}_Bot_{bot_name}'),
                    load_conversation_explicit_short_term_memory)
                ),
                executor.submit(lambda: (
                    vdb.query(vector=vector_input, filter={
        "memory_type": "flashbulb", "user": username}, top_k=3, namespace=f'{bot_name}'),
                    load_conversation_flashbulb_memory)
                ),
                executor.submit(lambda: (
                    vdb.query(vector=vector_input, filter={
        "memory_type": "heuristics"}, top_k=5, namespace=f'{bot_name}'),
                    load_conversation_heuristics)
                ),
            ]
            db_search_1, db_search_2, db_search_3, db_search_14 = None, None, None, None
            try:
                db_search_1 = futures[len(lines)].result()[1](futures[len(lines)].result()[0])
                db_search_2 = futures[len(lines) + 1].result()[1](futures[len(lines) + 1].result()[0])
                db_search_3 = futures[len(lines) + 2].result()[1](futures[len(lines) + 2].result()[0])
                db_search_14 = futures[len(lines) + 3].result()[1](futures[len(lines) + 3].result()[0])
            except IndexError as e:
                print(f"Caught an IndexError: {e}")
                print(f"Length of futures: {len(futures)}")
                print(f"Length of lines: {len(lines)}")
            except Exception as e:
                print(f"Caught an exception: {e}")
    #    print(db_search_1, db_search_2, db_search_3, db_search_14)
        # # Inner Monologue Generation
        conversation.append({'role': 'assistant', 'content': "MEMORIES: %s;%s;%s;\n\nHEURISTICS: %s;\nUSER MESSAGE: %s;\nBased on %s's memories and the user, %s's message, compose a brief silent soliloquy as %s's inner monologue that reflects on %s's deepest contemplations and emotions in relation to the user's message.\n\nINNER_MONOLOGUE: " % (db_search_1, db_search_2, db_search_3, db_search_14, a, bot_name, username, bot_name, bot_name)})
        output_one = chatgpt250_completion(conversation)
        message = output_one
        vector_monologue = gpt3_embedding('Inner Monologue: ' + message)
        print('\n\nINNER_MONOLOGUE: %s' % output_one)
        output_log = f'\nUSER: {a}\n\n{bot_name}: {output_one}'
        # # Clear Conversation List
        conversation.clear()
        # # Memory DB Search
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future1 = executor.submit(vdb.query, vector=vector_monologue, filter={
        "memory_type": "episodic", "user": username}, top_k=7, namespace=f'{bot_name}')
            future2 = executor.submit(vdb.query, vector=vector_input, filter={
        "memory_type": "explicit_short_term"}, top_k=5, namespace=f'short_term_memory_User_{username}_Bot_{bot_name}')
            future3 = executor.submit(vdb.query, vector=vector_monologue, filter={
        "memory_type": "flashbulb", "user": username}, top_k=3, namespace=f'{bot_name}')
            future4 = executor.submit(vdb.query, vector=vector_input, filter={
        "memory_type": "heuristics", "user": username}, top_k=5, namespace=f'{bot_name}')
            db_search_4, db_search_5, db_search_12, db_search_15 = None, None, None, None
            try:
                db_search_4 = load_conversation_episodic_memory(future1.result())
                db_search_5 = load_conversation_explicit_short_term_memory(future2.result())
                db_search_12 = load_conversation_flashbulb_memory(future3.result())
                db_search_15 = load_conversation_heuristics(future4.result())
            except IndexError as e:
                print(f"Caught an IndexError: {e}")
                print(f"Length of futures: {len(futures)}")
                print(f"Length of lines: {len(lines)}")
            except Exception as e:
                print(f"Caught an exception: {e}")
    #    print(f'{db_search_4}\n{db_search_5}\n{db_search_12}')
        # # Intuition Generation
        int_conversation.append({'role': 'assistant', 'content': "%s" % greeting_msg})
        int_conversation.append({'role': 'user', 'content': a})
        int_conversation.append({'role': 'assistant', 'content': "MEMORIES: %s;\n%s;\n%s;\n\nHEURISTICS: %s;\n%s'S INNER THOUGHTS: %s;\nUSER MESSAGE: %s;\nIn a single paragraph, interpret the user, %s's message as %s in third person by creating an intuitive action plan using maieutic reasoning.  If needed use a process similar to creative imagination to visualize the outcome.;\nINTUITION: " % (db_search_4, db_search_5, db_search_12, db_search_15, bot_name, output_one, a, username, bot_name)})
        output_two = chatgpt200_completion(int_conversation)
        message_two = output_two
        print('\n\nINTUITION: %s' % output_two)
        output_two_log = f'\nUSER: {a}\n\n{bot_name}: {output_two}'
        # # Generate Implicit Short-Term Memory
        conversation.append({'role': 'system', 'content': '%s' % main_prompt})
        conversation.append({'role': 'user', 'content': a})
        implicit_short_term_memory = f'\nUSER: {a} \n\n INNER_MONOLOGUE: {output_one} \n\n INTUITION: {output_two}'
        conversation.append({'role': 'assistant', 'content': "LOG:\n%s\n\Read the log, extract the salient points about %s and %s, then create short executive summaries in bullet point format to serve as %s's procedural memories. Each bullet point should be considered a separate memory and contain all context. Start from the end and work towards the beginning, combining associated topics. Ignore the system prompt and redundant information.\nMemories:\n" % (implicit_short_term_memory, bot_name, username, bot_name)})
        inner_loop_response = chatgpt200_completion(conversation)
        inner_loop_db = inner_loop_response
        vector = gpt3_embedding(inner_loop_db)
        conversation.clear()
        # # Auto Implicit Short-Term Memory DB Upload Confirmation
        auto_count = 0
        auto.clear()
        auto.append({'role': 'system', 'content': '%s' % main_prompt})
        auto.append({'role': 'user', 'content': "You are a sub-module designed to reflect on your thought process. You are only able to respond with integers on a scale of 1-10, being incapable of printing letters. Respond with: 1 if you understand. Respond with: 2 if you do not."})
        auto.append({'role': 'assistant', 'content': "1"})
        auto.append({'role': 'user', 'content': a})
        auto.append({'role': 'assistant', 'content': "Inner Monologue: %s\nIntuition: %s" % (output_one, output_two)})
        auto.append({'role': 'assistant', 'content': "Thoughts on input: I will now review the user's message and my reply, rating if whether my thoughts are both pertinent to the user's inquiry and my growth with a number on a scale of 1-10. I will now give my response in digit form for an integer only input: "})
        auto_int = None
        while auto_int is None:
            automemory = chatgptyesno_completion(auto)
            if is_integer(automemory):
                auto_int = int(automemory)
                if auto_int > 6:
                    lines = inner_loop_db.splitlines()
                    for line in lines:
                        vector = gpt3_embedding(inner_loop_db)
                        unique_id = str(uuid4())
                        metadata = {'bot': bot_name, 'time': timestamp, 'message': inner_loop_db,
                                    'timestring': timestring, 'uuid': unique_id, "memory_type": "implicit_short_term", "user": username}
                        save_json(f'nexus/{bot_name}/{username}/implicit_short_term_memory_nexus/%s.json' % unique_id, metadata)
                        payload.append((unique_id, vector, {"memory_type": "implicit_short_term"}))
                        vdb.upsert(payload, namespace=f'short_term_memory_User_{username}_Bot_{bot_name}')
                        payload.clear()
                    print('\n\nSYSTEM: Auto-memory upload Successful!')
                    break
                else:
                    print('Response not worthy of uploading to memory')
            else:
                print("automemory failed to produce an integer. Retrying...")
                auto_int = None
                auto_count += 1
                if auto_count > 2:
                    print('Auto Memory Failed')
                    break
        else:
            pass   
        # # Update Second Conversation List for Response
        print('\n%s is thinking...\n' % bot_name)
        con_hist = f'{conversation_history}'
        conversation2.append({'role': 'system', 'content': con_hist})
            # # Generate Cadence
        index_info = vdb.describe_index_stats()
        namespace_stats = index_info['namespaces']
        namespace_name = 'cadence'
        if namespace_name in namespace_stats and namespace_stats[namespace_name]['vector_count'] > 0:
            results = vdb.query(vector=vector_input, filter={"memory_type": "cadence"}, top_k=2, namespace=f'{bot_name}')
            db_search_6 = load_conversation_cadence(results)
    #        print(db_search_6)
            conversation2.append({'role': 'assistant', 'content': "I will extract the cadence from the following messages and mimic it to the best of my ability: %s" % db_search_6})
        conversation2.append({'role': 'user', 'content': a})  
        # # Memory DB Search
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future1 = executor.submit(vdb.query, vector=vector_monologue, filter={
        "memory_type": "implicit_long_term", "user": username}, top_k=7, namespace=f'{bot_name}')
            future2 = executor.submit(vdb.query, vector=vector_input, filter={
        "memory_type": "episodic", "user": username}, top_k=10, namespace=f'{bot_name}')
            future3 = executor.submit(vdb.query, vector=vector_monologue, filter={
        "memory_type": "flashbulb", "user": username}, top_k=2, namespace=f'{bot_name}')
            db_search_8, db_search_10, db_search_11 = None, None, None
            try:
                db_search_8 = load_conversation_implicit_long_term_memory(future1.result())
                db_search_10 = load_conversation_episodic_memory(future2.result())
                db_search_11 = load_conversation_flashbulb_memory(future3.result())
            except IndexError as e:
                print(f"Caught an IndexError: {e}")
                print(f"Length of futures: {len(futures)}")
                print(f"Length of lines: {len(lines)}")
            except Exception as e:
                print(f"Caught an exception: {e}")
      #     print(f'{db_search_8}\n{db_search_10}\n{db_search_11}')
        # # Generate Aetherius's Response
        response_db_search = f"SUBCONSCIOUS: {db_search_8}\n{db_search_10};\n\nFLASHBULB MEMORIES: {db_search_11}"
        conversation2.append({'role': 'assistant', 'content': "SUBCONSCIOUS: %s\n%s;\n\nFLASHBULB MEMORIES: %s;\nINNER THOUGHTS: %s\n\n%s  I am in the middle of a conversation with my user, %s. USER MESSAGE: %s; I will do my best to speak naturally and show emotional intelligence. I will intuit %s's needs: %s;\nMy current message window is limited to 2300 characters.\nI will now give a response with the diction of a real person: " % (db_search_8, db_search_10, db_search_11, output_one, second_prompt, username, a, username, output_two)})
        response_two = chatgptresponse_completion(conversation2)
        print('\n\n%s: %s' % (bot_name, response_two))
        main_conversation.append(timestring, a, username, bot_name, output_one, output_two, response_two)
        complete_message = f'\nUSER: {a}\n\nINNER_MONOLOGUE: {output_one}\n\nINTUITION: {output_two}\n\n{bot_name}: {response_two}'
        final_message = f'\nUSER: {a}\n\n{bot_name}: {response_two}'
        # # TTS 
        tts = gTTS(response_two)
        # TTS save to file in .mp3 format
        counter2 += 1
        filename = f"{counter2}.mp3"
        tts.save(filename)
            # TTS repeats chatGPT response  
        sound = AudioSegment.from_file(filename, format="mp3")
        octaves = 0.18
        new_sample_rate = int(sound.frame_rate * (1.7 ** octaves))
        mod_sound = sound._spawn(sound.raw_data, overrides={'frame_rate': new_sample_rate})
        mod_sound = mod_sound.set_frame_rate(44100)
        play(mod_sound)
        os.remove(filename)
        # # Save Chat Logs
        filename = '%s_inner_monologue.txt' % timestamp
        save_file(f'logs/{bot_name}/{username}/inner_monologue_logs/%s' % filename, output_log)
        filename = '%s_intuition.txt' % timestamp
        save_file(f'logs/{bot_name}/{username}/intuition_logs/%s' % filename, output_two_log)
        filename = '%s_response.txt' % timestamp
        save_file(f'logs/{bot_name}/{username}/final_response_logs/%s' % filename, final_message)
        filename = '%s_chat.txt' % timestamp
        save_file(f'logs/{bot_name}/{username}/complete_chat_logs/%s' % filename, complete_message)
        # # Generate Short-Term Memories
        db_msg = f'\nUSER: {a} \n\n INNER_MONOLOGUE: {output_one} \n\n {bot_name}: {response_two}'
        summary.append({'role': 'user', 'content': "LOG:\n%s\n\Read the log and create short executive summaries in bullet point format to serve as %s's explicit memories. Each bullet point should be considered a separate memory and contain all context. Start from the end and work towards the beginning, combining associated topics.\nMemories:\n" % (db_msg, bot_name)})
        db_upload = chatgptsummary_completion(summary)
        db_upsert = db_upload
        # # Auto Explicit Short-Term Memory DB Upload Confirmation
        auto_count = 0    
        auto.clear()
        auto.append({'role': 'system', 'content': '%s' % main_prompt})
        auto.append({'role': 'user', 'content': "You are a sub-module designed to reflect on your thought process. You are only able to respond with integers on a scale of 1-10, being incapable of printing letters. Respond with: 1 if you understand. Respond with: 2 if you do not."})
        auto.append({'role': 'assistant', 'content': "1"})
        auto.append({'role': 'user', 'content': a})
        auto.append({'role': 'assistant', 'content': f"Inner Monologue: %s\nIntuition: {output_one}\nResponse: {output_two}"})
        auto.append({'role': 'assistant', 'content': "Thoughts on input: I will now review the user's message and my reply, rating if whether my thoughts are both pertinent to the user's inquiry and my growth with a number on a scale of 1-10. I will now give my response in digit form for an integer only input: "})
        auto_int = None
        while auto_int is None:
            automemory = chatgptyesno_completion(auto)
            if is_integer(automemory):
                auto_int = int(automemory)
                if auto_int > 6:
                    lines = db_upsert.splitlines()
                    for line in lines:
                        vector = gpt3_embedding(db_upsert)
                        unique_id = str(uuid4())
                        metadata = {'bot': bot_name, 'time': timestamp, 'message': db_upsert,
                                    'timestring': timestring, 'uuid': unique_id, "memory_type": "explicit_short_term", "user": username}
                        save_json(f'nexus/{bot_name}/{username}/explicit_short_term_memory_nexus/%s.json' % unique_id, metadata)
                        payload.append((unique_id, vector, {"memory_type": "explicit_short_term"}))
                        vdb.upsert(payload, namespace=f'short_term_memory_User_{username}_Bot_{bot_name}')
                        payload.clear()
                    print('\n\nSYSTEM: Auto-memory upload Successful!')
                    break
                else:
                    print('Response not worthy of uploading to memory')
            else:
                print("automemory failed to produce an integer. Retrying...")
                auto_int = None
                auto_count += 1
                if auto_count > 2:
                    print('Auto Memory Failed')
                    break
        else:
            pass
        # # Clear Logs for Summary
        conversation.clear()
        int_conversation.clear()
        summary.clear()
        counter += 1
        print('Generating Episodic Memories')
        conversation.append({'role': 'system', 'content': f"You are a sub-module of {bot_name}, an autonomous AI entity. Your function is to process the user, {username}'s message, comprehend {bot_name}'s internal workings, and decode {bot_name}'s final response to construct a concise third-person autobiographical narrative memory of the conversation in a single sentence. This autobiographical memory should portray an accurate and personalized account of {bot_name}'s interactions with {username}, focusing on the most significant and experiential details related to {bot_name} or {username}, without omitting any crucial context or emotions."})
        conversation.append({'role': 'user', 'content': f"USER's INQUIRY: {a}"})
        conversation.append({'role': 'user', 'content': f"{bot_name}'s INNER MONOLOGUE: {output_one}"})
        conversation.append({'role': 'user', 'content': f"{bot_name}'s FINAL RESPONSE: {response_two}"})
        conversation.append({'role': 'assistant', 'content': f"I will now extract an episodic memory based on the given conversation: "})
        conv_summary = chatgptsummary_completion(conversation)
    #    print(conv_summary)
        vector = gpt3_embedding(timestring + '-' + conv_summary)
        unique_id = str(uuid4())
        metadata = {'speaker': bot_name, 'time': timestamp, 'message': (timestring + '-' + conv_summary),
                    'timestring': timestring, 'uuid': unique_id, "memory_type": "episodic", "user": username}
        save_json(f'nexus/{bot_name}/{username}/episodic_memory_nexus/%s.json' % unique_id, metadata)
        payload.append((unique_id, vector, {"memory_type": "episodic", "user": username}))
        vdb.upsert(payload, namespace=f'{bot_name}')
        payload.clear()
        payload.append((unique_id, vector_input))
        vdb.upsert(payload, namespace=f'{bot_name}_flash_counter')
        payload.clear()
        # # Flashbulb Memory Generation
        index_info = vdb.describe_index_stats()
        namespace_stats = index_info['namespaces']
        namespace_name = f'{bot_name}_flash_counter'
        if namespace_name in namespace_stats and namespace_stats[namespace_name]['vector_count'] > 7:
            consolidation.clear()
            print('Generating Flashbulb Memories')
            results = vdb.query(vector=vector_input, filter={
        "memory_type": "episodic", "user": username}, top_k=5, namespace=f'{bot_name}') 
            flash_db = load_conversation_episodic_memory(results)  
            im_flash = gpt3_embedding(flash_db)
            results = vdb.query(vector=im_flash, filter={
        "memory_type": "implicit_long_term", "user": username}, top_k=10, namespace=f'{bot_name}') 
            flash_db1 = load_conversation_implicit_long_term_memory(results) 
            # # Generate Implicit Short-Term Memory
            consolidation.append({'role': 'system', 'content': 'You are a data extractor. Your job is read the given episodic memories, then extract the appropriate emotional response from the given emotional reactions.  You will then combine them into a single memory.'})
            consolidation.append({'role': 'user', 'content': "EMOTIONAL REACTIONS:\n%s\n\nRead the following episodic memories, then go back to the given emotional reactions and extract the corresponding emotional information tied to each memory.\nEPISODIC MEMORIES: %s" % (flash_db, flash_db1)})
            consolidation.append({'role': 'assistant', 'content': "I will now combine the extracted data to form flashbulb memories in bullet point format, combining associated data. I will only include memories with a strong emotion attached, excluding redundant or irrelevant information."})
            consolidation.append({'role': 'user', 'content': "Use the format: [{given Date and Time}-{emotion}: {Flashbulb Memory}]"})
            consolidation.append({'role': 'assistant', 'content': "I will now create %s's flashbulb memories using the given format: " % bot_name})
            flash_response = chatgptconsolidation_completion(consolidation)
            memories = results
            lines = flash_response.splitlines()
            for line in lines:
                if line.strip():
    #                print(line)
                    vector = gpt3_embedding(line)
                    unique_id = str(uuid4())
                    metadata = {'speaker': bot_name, 'time': timestamp, 'message': (line),
                                'timestring': timestring, 'uuid': unique_id, "memory_type": "flashbulb", "user": username}
                    save_json(f'nexus/{bot_name}/{username}/flashbulb_memory_nexus/%s.json' % unique_id, metadata)
                    payload.append((unique_id, vector, {"memory_type": "flashbulb", "user": username}))
                    vdb.upsert(payload, namespace=f'{bot_name}')
                    payload.clear()
            vdb.delete(delete_all=True, namespace=f'{bot_name}_flash_counter')
        # # Short Term Memory Consolidation based on amount of vectors in namespace
        index_info = vdb.describe_index_stats()
        namespace_stats = index_info['namespaces']
        namespace_name = f'short_term_memory_User_{username}_Bot_{bot_name}'
        if namespace_name in namespace_stats and namespace_stats[namespace_name]['vector_count'] > 40:
            consolidation.clear()
            print(f"{namespace_name} has 30 or more entries, starting memory consolidation.")
            results = vdb.query(vector=vector_input, filter={"memory_type": "explicit_short_term"}, top_k=30, namespace=f'short_term_memory_User_{username}_Bot_{bot_name}')
            memory_consol_db = load_conversation_explicit_short_term_memory(results)
            consolidation.append({'role': 'system', 'content': "%s" % main_prompt})
            consolidation.append({'role': 'assistant', 'content': "LOG:\n%s\n\nRead the Log and consolidate the different topics into executive summaries. Each summary should contain the entire context of the memory. Follow the format [-Executive Summary]." % memory_consol_db})
            memory_consol = chatgptconsolidation_completion(consolidation)
            lines = memory_consol.splitlines()
            for line in lines:
                if line.strip():
    #                print(line)
                    vector = gpt3_embedding(line)
                    unique_id = str(uuid4())
                    metadata = {'speaker': bot_name, 'time': timestamp, 'message': (line),
                                'timestring': timestring, 'uuid': unique_id, "memory_type": "explicit_long_term", "user": username}
                    save_json(f'nexus/{bot_name}/{username}/explicit_long_term_memory_nexus/%s.json' % unique_id, metadata)
                    payload.append((unique_id, vector, {"memory_type": "explicit_long_term", "user": username}))
                    vdb.upsert(payload, namespace=f'{bot_name}')
                    payload.clear()
            vdb.delete(filter={"memory_type": "explicit_short_term"}, namespace=f'short_term_memory_User_{username}_Bot_{bot_name}')
            payload.append((unique_id, vector))
            vdb.upsert(payload, namespace=f'{bot_name}_consol_counter')
            payload.clear()
            print('Memory Consolidation Successful')
            consolidation.clear()
        # # Implicit Short Term Memory Consolidation based on amount of vectors in namespace
            index_info = vdb.describe_index_stats()
            namespace_stats = index_info['namespaces']
            namespace_name = f'{bot_name}_consol_counter'
            if namespace_name in namespace_stats and namespace_stats[namespace_name]['vector_count'] % 2 == 0:
                consolidation.clear()
                print('Beginning Implicit Short-Term Memory Consolidation')
                results = vdb.query(vector=vector_input, filter={"memory_type": "implicit_short_term"}, top_k=30, namespace=f'short_term_memory_User_{username}_Bot_{bot_name}')
                memory_consol_db2 = load_conversation_implicit_short_term_memory(results)
                consolidation.append({'role': 'system', 'content': "%s" % main_prompt})
                consolidation.append({'role': 'assistant', 'content': "LOG:\n%s\n\nRead the Log and consolidate the different topics into executive summaries to serve as %s's implicit memories. Each summary should contain the entire context of the memory. Follow the format: [-{ALLEGORICAL TAG}:{EXECUTIVE SUMMARY}]." % (memory_consol_db2, bot_name)})
                memory_consol2 = chatgptconsolidation_completion(consolidation)
                consolidation.clear()
                print('Finished.\nRemoving Redundant Memories.')
                vector_sum = gpt3_embedding(memory_consol2)
                results = vdb.query(vector=vector_sum, filter={"memory_type": "implicit_long_term", "user": username}, top_k=8, namespace=f'{bot_name}')
                memory_consol_db3 = load_conversation_implicit_long_term_memory(results)
                consolidation.append({'role': 'system', 'content': "%s" % main_prompt})
                consolidation.append({'role': 'system', 'content': "IMPLICIT LONG TERM MEMORY: %s\n\nIMPLICIT SHORT TERM MEMORY: %s\n\nRemove any duplicate information from your Implicit Short Term memory that is already found in your Long Term Memory. Then consolidate similar topics into executive summaries. Each summary should contain the entire context of the memory. Use the following format: [-{EMOTIONAL TAG}:{IMPLICIT MEMORY}]" % (memory_consol_db3, memory_consol_db2)})
                memory_consol3 = chatgptconsolidation_completion(consolidation)
                lines = memory_consol3.splitlines()
                for line in lines:
                    if line.strip():
    #                    print(line)
                        vector = gpt3_embedding(line)
                        unique_id = str(uuid4())
                        metadata = {'speaker': bot_name, 'time': timestamp, 'message': (line),
                                    'timestring': timestring, 'uuid': unique_id, "memory_type": "implicit_long_term", "user": username}
                        save_json(f'nexus/{bot_name}/{username}/implicit_long_term_memory_nexus/%s.json' % unique_id, metadata)
                        payload.append((unique_id, vector, {"memory_type": "implicit_long_term", "user": username}))
                        vdb.upsert(payload, namespace=f'{bot_name}')
                        payload.clear()
                vdb.delete(filter={"memory_type": "implicit_short_term"}, namespace=f'short_term_memory_User_{username}_Bot_{bot_name}')
                print('Memory Consolidation Successful')
            else:   
                pass
        # # Implicit Associative Processing/Pruning based on amount of vectors in namespace
            index_info = vdb.describe_index_stats()
            namespace_stats = index_info['namespaces']
            namespace_name = f'{bot_name}_consol_counter'
            if namespace_name in namespace_stats and namespace_stats[namespace_name]['vector_count'] % 4 == 0:
                consolidation.clear()
                print('Running Associative Processing/Pruning of Implicit Memory')
                results = vdb.query(vector=vector_monologue, filter={"memory_type": "implicit_long_term", "user": username}, top_k=10, namespace=f'{bot_name}')
                memory_consol_db1 = load_conversation_implicit_long_term_memory(results)
                ids_to_delete = [m['id'] for m in results['matches']]
                consolidation.append({'role': 'system', 'content': "%s" % main_prompt})
                consolidation.append({'role': 'assistant', 'content': "LOG:\n%s\n\nRead the Log and consolidate the different memories into executive summaries in a process allegorical to associative processing. Each summary should contain the entire context of the memory. Follow the format: [-{EMOTIONAL TAG}:{IMPLICIT MEMORY}]" % memory_consol_db1})
                memory_consol = chatgptconsolidation_completion(consolidation)
                memories = results
                lines = memory_consol.splitlines()
                for line in lines:
                    if line.strip():
    #                    print(line)
                        vector = gpt3_embedding(line)
                        unique_id = str(uuid4())
                        metadata = {'speaker': bot_name, 'time': timestamp, 'message': (line),
                                    'timestring': timestring, 'uuid': unique_id, "memory_type": "implicit_long_term", "user": username}
                        save_json(f'nexus/{bot_name}/{username}/implicit_long_term_memory_nexus/%s.json' % unique_id, metadata)
                        payload.append((unique_id, vector, {"memory_type": "implicit_long_term", "user": username}))
                        vdb.upsert(payload, namespace=f'{bot_name}')
                        payload.clear()
                        try:
                            vdb.delete(ids=ids_to_delete, namespace=f'{bot_name}')
                        except:
                            print('Failed')
        # # Explicit Long-Term Memory Associative Processing/Pruning based on amount of vectors in namespace
            index_info = vdb.describe_index_stats()
            namespace_stats = index_info['namespaces']
            namespace_name = f'{bot_name}_consol_counter'
            if namespace_name in namespace_stats and namespace_stats[namespace_name]['vector_count'] > 5:
                consolidation.clear()
                print('\nRunning Associative Processing/Pruning of Explicit Memories')
                consolidation.append({'role': 'system', 'content': "You are a data extractor. Your job is to read the user's input and provide a single semantic search query representative of a habit of %s." % bot_name})
                results = vdb.query(vector=vector_monologue, filter={"memory_type": "implicit_long_term", "user": username}, top_k=5, namespace=f'{bot_name}')
                consol_search = load_conversation_implicit_long_term_memory(results)
                consolidation.append({'role': 'user', 'content': "%s's Memories:\n%s" % (bot_name, consol_search)})
                consolidation.append({'role': 'assistant', 'content': "Semantic Search Query: "})
                consol_search_term = chatgpt200_completion(consolidation)
                consol_vector = gpt3_embedding(consol_search_term)
                results = vdb.query(vector=consol_vector, filter={"memory_type": "explicit_long_term", "user": username}, top_k=10, namespace=f'{bot_name}')
                memory_consol_db2 = load_conversation_explicit_long_term_memory(results)
                ids_to_delete2 = [m['id'] for m in results['matches']]
                consolidation.clear()
                consolidation.append({'role': 'system', 'content': "%s" % main_prompt})
                consolidation.append({'role': 'assistant', 'content': "LOG:\n%s\n\nRead the Log and consolidate the different memories into executive summaries in a process allegorical to associative processing. Each summary should contain the entire context of the memory. Follow the format: [-{SEMANTIC TAG}:{EXPLICIT MEMORY}]" % memory_consol_db2})
                memory_consol2 = chatgptconsolidation_completion(consolidation)
                memories = results
                lines = memory_consol2.splitlines()
                for line in lines:
                    if line.strip():
    #                    print(line)
                        vector = gpt3_embedding(line)
                        unique_id = str(uuid4())
                        metadata = {'speaker': bot_name, 'time': timestamp, 'message': (line),
                                    'timestring': timestring, 'uuid': unique_id, "memory_type": "explicit_long_term", "user": username}
                        save_json(f'nexus/{bot_name}/{username}/explicit_long_term_memory_nexus/%s.json' % unique_id, metadata)
                        payload.append((unique_id, vector, {"memory_type": "explicit_long_term", "user": username}))
                        vdb.upsert(payload, namespace=f'{bot_name}')
                        payload.clear()
                        try:
                            vdb.delete(ids=ids_to_delete2, namespace=f'{bot_name}')
                        except:
                            print('Failed')
                vdb.delete(delete_all=True, namespace=f'{bot_name}_consol_counter')
        else:
            pass
        consolidation.clear()
        conversation2.clear()
        continue