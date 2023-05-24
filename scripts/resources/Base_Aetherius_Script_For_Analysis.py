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
# import speech_recognition as sr
# from gtts import gTTS
# from playsound import playsound
# import pyttsx3
# from pydub import AudioSegment
# from pydub.playback import play
# from pydub import effects


def Base_Aetherius_Script_For_Analysis():
    vdb = pinecone.Index("aetherius")
    # # Number of Messages before conversation is summarized, higher number, higher api cost. Change to 3 when using GPT 3.5 due to token usage.
    conv_length = 4
    m = multiprocessing.Manager()
    lock = m.Lock()
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
                conversation.append({'role': 'assistant', 'content': "%s" % response_two})
                conversation.append({'role': 'assistant', 'content': '%s.' % conv_summary})
            pass
        else:
            conversation.append({'role': 'assistant', 'content': "%s" % greeting_msg})
            print("\n%s" % greeting_msg)
        # # User Input Voice
    #    yn_voice = input(f'\n\nPress Enter to Speak')
    #    if yn_voice == "":
    #        with sr.Microphone() as source:
    #            print("\nSpeak now")
    #            audio = r.listen(source)
    #            try:
    #                text = r.recognize_google(audio)
    #                print("\nUSER: " + text)
    #            except sr.UnknownValueError:
    #                print("Google Speech Recognition could not understand audio")
    #                print("\nSYSTEM: Press Left Alt to Speak to Aetherius")
    #                break
    #            except sr.RequestError as e:
    #                print("Could not request results from Google Speech Recognition service; {0}".format(e))
    #                break
    #    else:
    #        print('Leave Field Empty')
    #    a = (f'\n\nUSER: {text}')
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
                    vdb.delete(delete_all=True, namespace=f'{username}_short_term_memory')
                    vdb.delete(delete_all=True, namespace=f'{username}_short_term_memory')
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
        # # Check for Exit then summarize current conversation
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
                        vdb.upsert(payload, namespace=f'{username}_consol_counter')
                        payload.clear()
                    payload.append((unique_id, vector_input))   
                    vdb.upsert(payload, namespace=f'{username}')
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
        "memory_type": "explicit_long_term"}, top_k=3, namespace=f'{username}'),
                        db_term_result.update({_index: load_conversation_explicit_long_term_memory(results)}),
                        results := vdb.query(vector=db_term[_index], filter={
        "memory_type": "implicit_long_term"}, top_k=2, namespace=f'{username}'),
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
        "memory_type": "episodic"}, top_k=5, namespace=f'{username}'),
                    load_conversation_episodic_memory)
                ),
                executor.submit(lambda: (
                    vdb.query(vector=vector_input, filter={
        "memory_type": "explicit_short_term"}, top_k=8, namespace=f'{username}_short_term_memory'),
                    load_conversation_explicit_short_term_memory)
                ),
                executor.submit(lambda: (
                    vdb.query(vector=vector_input, filter={
        "memory_type": "flashbulb"}, top_k=2, namespace=f'{username}'),
                    load_conversation_flashbulb_memory)
                ),
                executor.submit(lambda: (
                    vdb.query(vector=vector_input, filter={
        "memory_type": "heuristics"}, top_k=5, namespace=f'{username}'),
                    load_conversation_heuristics)
                ),
            ]
            # Handle results
        #    db_search_1 = futures[len(lines)].result()[1](futures[len(lines)].result()[0])
        #    db_search_2 = futures[len(lines) + 1].result()[1](futures[len(lines) + 1].result()[0])
        #    db_search_3 = futures[len(lines) + 2].result()[1](futures[len(lines) + 2].result()[0])
        #    db_search_4 = futures[len(lines) + 3].result()[1](futures[len(lines) + 3].result()[0])
            try:
                db_search_1 = futures[len(lines)].result()[1](futures[len(lines)].result()[0])
                db_search_2 = futures[len(lines) + 1].result()[1](futures[len(lines) + 1].result()[0])
                db_search_3 = futures[len(lines) + 2].result()[1](futures[len(lines) + 2].result()[0])
                db_search_4 = futures[len(lines) + 3].result()[1](futures[len(lines) + 3].result()[0])
            except IndexError as e:
                print(f"Caught an IndexError: {e}")
                print(f"Length of futures: {len(futures)}")
                print(f"Length of lines: {len(lines)}")
            except Exception as e:
                print(f"Caught an exception: {e}")
        # # Inner Monologue Generation
        print(db_search_1)
        print(db_search_2)
        print(db_search_3)
        print(db_search_4)
        conversation.append({'role': 'assistant', 'content': "MEMORIES: %s;%s;%s;\n\nHEURISTICS: %s;\nUSER MESSAGE: %s;\nBased on %s's memories and the user, %s's message, compose a brief silent soliloquy as %s's inner monologue that reflects on %s's deepest contemplations and emotions in relation to the user's message.\n\nINNER_MONOLOGUE: " % (db_search_1, db_search_2, db_search_3, db_search_4, a, bot_name, username, bot_name, bot_name)})
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
        "memory_type": "episodic"}, top_k=5, namespace=f'{username}')
            future2 = executor.submit(vdb.query, vector=vector_input, filter={
        "memory_type": "explicit_short_term"}, top_k=10, namespace=f'{username}_short_term_memory')
            future3 = executor.submit(vdb.query, vector=vector_monologue, filter={
        "memory_type": "flashbulb"}, top_k=2, namespace=f'{username}')
            try:
                db_search_4 = load_conversation_episodic_memory(future1.result())
                db_search_5 = load_conversation_explicit_short_term_memory(future2.result())
                db_search_12 = load_conversation_flashbulb_memory(future3.result())
            except IndexError as e:
                print(f"Caught an IndexError: {e}")
                print(f"Length of futures: {len(futures)}")
                print(f"Length of lines: {len(lines)}")
            except Exception as e:
                print(f"Caught an exception: {e}")
        print(f'{db_search_4}\n{db_search_5}\n{db_search_12}')
        # # Intuition Generation
        int_conversation.append({'role': 'assistant', 'content': "%s" % greeting_msg})
        int_conversation.append({'role': 'user', 'content': a})
        int_conversation.append({'role': 'assistant', 'content': "MEMORIES: %s;\n%s;\n%s;\n\n%s'S INNER THOUGHTS: %s;\nUSER MESSAGE: %s;\nIn a single paragraph, interpret the user, %s's message as %s in third person by creating an intuitive action plan, even if they are uncertain about their own needs.;\nINTUITION: " % (db_search_4, db_search_5, db_search_12, bot_name, output_one, a, username, bot_name)})
        output_two = chatgpt200_completion(int_conversation)
        message_two = output_two
        print('\n\nINTUITION: %s' % output_two)
        output_two_log = f'\nUSER: {a}\n\n{bot_name}: {output_two}'
        # # Generate Implicit Short-Term Memory
        conversation.append({'role': 'system', 'content': '%s' % main_prompt})
        conversation.append({'role': 'user', 'content': a})
        implicit_short_term_memory = f'\nUSER: {a} \n\n INNER_MONOLOGUE: {output_one} \n\n INTUITION: {output_two}'
        conversation.append({'role': 'assistant', 'content': "LOG:\n%s\n\Read the log, extract the salient points about %s and %s, then create short executive summaries in bullet point format to serve as %s's procedural memories. Each bullet point should be considered a separate memory and contain all context. Start from the end and work towards the beginning, combining assosiated topics. Ignore the system prompt and redundant information.\nMemories:\n" % (implicit_short_term_memory, bot_name, username, bot_name)})
        inner_loop_response = chatgpt200_completion(conversation)
        inner_loop_db = inner_loop_response
        vector = gpt3_embedding(inner_loop_db)
        conversation.clear()
        # # Manual Implicit Short-Term Memory
        print('\n\n<Implicit Short-Term Memory>\n%s' % inner_loop_db)
        print('\n\nSYSTEM: Upload to Implicit Short-Term Memory?\n        Press Y for yes or N for no.')
        while True:
            user_input = input("'Y' or 'N': ")
            if user_input == 'y':
                lines = inner_loop_db.splitlines()
                for line in lines:
                    if line.strip():
                        vector = gpt3_embedding(line)
                        unique_id = str(uuid4())
                        metadata = {'bot': bot_name, 'time': timestamp, 'message': line,
                                    'timestring': timestring, 'uuid': unique_id, "memory_type": "implicit_short_term"}
                        save_json('nexus/implicit_short_term_memory_nexus/%s.json' % unique_id, metadata)
                        payload.append((unique_id, vector, {"memory_type": "implicit_short_term"}))
                        vdb.upsert(payload, namespace=f'{username}_short_term_memory')
                        payload.clear()
                print('\n\nSYSTEM: Upload Successful!')
                break
            elif user_input == 'n':
                print('\n\nSYSTEM: Memories have been Deleted')
                break
            else:
                print('Invalid Input')
        # # Auto Implicit Short-Term Memory DB Upload Confirmation
    #    auto_count = 0
    #    auto.clear()
    #    auto.append({'role': 'system', 'content': '%s' % main_prompt})
    #    auto.append({'role': 'user', 'content': "You are a sub-module designed to reflect on your thought process. You are only able to respond with integers on a scale of 1-10, being incapable of printing letters. Respond with: 1 if you understand. Respond with: 2 if you do not."})
    #    auto.append({'role': 'assistant', 'content': "1"})
    #    auto.append({'role': 'user', 'content': a})
    #    auto.append({'role': 'assistant', 'content': "Inner Monologue: %s\nIntuition: %s" % (output_one, output_two)})
    #    auto.append({'role': 'assistant', 'content': "Thoughts on input: I will now review the user's message and my reply, rating if whether my thoughts are both pertinent to the user's inquiry and my growth with a number on a scale of 1-10. I will now give my response in digit form for an integer only input: "})
    #    auto_int = None
    #    while auto_int is None:
    #        automemory = chatgptyesno_completion(auto)
    #        if is_integer(automemory):
    #            auto_int = int(automemory)
    #            if auto_int > 7:
    #                lines = inner_loop_db.splitlines()
    #                for line in lines:
    #                    vector = gpt3_embedding(inner_loop_db)
    #                    unique_id = str(uuid4())
    #                    metadata = {'bot': bot_name, 'time': timestamp, 'message': inner_loop_db,
    #                                'timestring': timestring, 'uuid': unique_id, "memory_type": "implicit_short_term"}
    #                    save_json('nexus/implicit_short_term_memory_nexus/%s.json' % unique_id, metadata)
    #                    payload.append((unique_id, vector, {"memory_type": "implicit_short_term"}))
    #                    vdb.upsert(payload, namespace=f'{username}_short_term_memory')
    #                    payload.clear()
    #                print('\n\nSYSTEM: Auto-memory upload Successful!')
    #                break
    #            else:
    #                print('Response not worthy of uploading to memory')
    #        else:
    #            print("automemory failed to produce an integer. Retrying...")
    #            auto_int = None
    #            auto_count += 1
    #            if auto_count > 2:
    #                print('Auto Memory Failed')
    #                break
    #    else:
    #        pass   
        # # Update Second Conversation List for Response
        print('\n%s is thinking...\n' % bot_name)
        if 'response_two' in locals():
            conversation2.append({'role': 'assistant', 'content': "%s" % response_two})
        else:
            conversation2.append({'role': 'system', 'content': '%s' % main_prompt})
            conversation2.append({'role': 'assistant', 'content': '%s' % greeting_msg})
            # # Generate Cadence
            index_info = vdb.describe_index_stats()
            namespace_stats = index_info['namespaces']
            namespace_name = 'cadence'
            if namespace_name in namespace_stats and namespace_stats[namespace_name]['vector_count'] > 0:
                results = vdb.query(vector=vector_input, filter={"memory_type": "cadence"}, top_k=2, namespace=f'{username}')
                db_search_6 = load_conversation_cadence(results)
    #        print(db_search_6)
                conversation2.append({'role': 'assistant', 'content': "I will extract the cadence from the following messages and mimic it to the best of my ability: %s" % db_search_6})
        conversation2.append({'role': 'user', 'content': a})  
        # # Memory DB Search
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future1 = executor.submit(vdb.query, vector=vector_monologue, filter={
        "memory_type": "implicit_long_term"}, top_k=5, namespace=f'{username}')
            future2 = executor.submit(vdb.query, vector=vector_input, filter={
        "memory_type": "episodic"}, top_k=10, namespace=f'{username}')
            future3 = executor.submit(vdb.query, vector=vector_monologue, filter={
        "memory_type": "flashbulb"}, top_k=2, namespace=f'{username}')
            try:
                db_search_8 = load_conversation_implicit_long_term_memory(future1.result())
                db_search_10 = load_conversation_episodic_memory(future2.result())
                db_search_11 = load_conversation_flashbulb_memory(future3.result())
                print(f'{db_search_8}\n{db_search_10}\n{db_search_11}')
            except IndexError as e:
                print(f"Caught an IndexError: {e}")
                print(f"Length of futures: {len(futures)}")
                print(f"Length of lines: {len(lines)}")
            except Exception as e:
                print(f"Caught an exception: {e}")
        # # Generate Aetherius's Response
        conversation2.append({'role': 'assistant', 'content': "SUBCONSIOUS: %s\n%s;\n\nFLASHBULB MEMORIES: %s;\nINNER THOUGHTS: %s\n\n%s  I am in the middle of a conversation with my user, %s. USER MESSAGE: %s; I will do my best to speak naturally and show emotional intelligence. I will intuit %s's needs: %s;\nMy current message window is limited to 2300 characters.\nI will now give a response with the diction of a real person: " % (db_search_8, db_search_10, db_search_11, output_one, second_prompt, username, a, username, output_two)})
        response_two = chatgptresponse_completion(conversation2)
        print('\n\n%s: %s' % (bot_name, response_two))
        complete_message = f'\nUSER: {a}\n\nINNER_MONOLOGUE: {output_one}\n\nINTUITION: {output_two}\n\n{bot_name}: {response_two}'
        final_message = f'\nUSER: {a}\n\n{bot_name}: {response_two}'
        # # TTS 
    #    tts = gTTS(response_two)
        # TTS save to file in .mp3 format
    #    counter2 += 1
    #    filename = f"{counter2}.mp3"
    #    tts.save(filename)
            # TTS repeats chatGPT response  
    #    sound = AudioSegment.from_file(filename, format="mp3")
    #    octaves = 0.18
    #    new_sample_rate = int(sound.frame_rate * (1.7 ** octaves))
    #    mod_sound = sound._spawn(sound.raw_data, overrides={'frame_rate': new_sample_rate})
    #    mod_sound = mod_sound.set_frame_rate(44100)
    #    play(mod_sound)
    #    os.remove(filename)
        # # Save Chat Logs
        filename = '%s_inner_monologue.txt' % timestamp
        save_file('logs/inner_monologue_logs/%s' % filename, output_log)
        filename = '%s_intuition.txt' % timestamp
        save_file('logs/intuition_logs/%s' % filename, output_two_log)
        filename = '%s_response.txt' % timestamp
        save_file('logs/final_response_logs/%s' % filename, final_message)
        filename = '%s_chat.txt' % timestamp
        save_file('logs/complete_chat_logs/%s' % filename, complete_message)
        # # Generate Short-Term Memories
        db_msg = f'\nUSER: {a} \n\n INNER_MONOLOGUE: {output_one} \n\n {bot_name}: {response_two}'
        summary.append({'role': 'user', 'content': "LOG:\n%s\n\Read the log and create short executive summaries in bullet point format to serve as %s's explicit memories. Each bullet point should be considered a separate memory and contain all context. Start from the end and work towards the beginning, combining assosiated topics.\nMemories:\n" % (db_msg, bot_name)})
        db_upload = chatgptsummary_completion(summary)
        db_upsert = db_upload
        # # Manual Short-Term Memory DB Upload Confirmation
        print('\n\n<DATABASE INFO>\n%s' % db_upsert)
        print('\n\nSYSTEM: Upload to short term memory? \n        Press Y for yes or N for no.')
        while True:
            user_input = input("'Y' or 'N': ")
            if user_input == 'y':
                lines = db_upsert.splitlines()
                for line in lines:
                    if line.strip():
                        vector = gpt3_embedding(line)
                        unique_id = str(uuid4())
                        metadata = {'bot': bot_name, 'time': timestamp, 'message': line,
                                    'timestring': timestring, 'uuid': unique_id, "memory_type": "explicit_short_term"}
                        save_json('nexus/explicit_short_term_memory_nexus/%s.json' % unique_id, metadata)
                        payload.append((unique_id, vector, {"memory_type": "explicit_short_term"}))
                        vdb.upsert(payload, namespace=f'{username}_short_term_memory')
                        payload.clear()
                print('\n\nSYSTEM: Upload Successful!')
                break
            elif user_input == 'n':
                print('\n\nSYSTEM: Memories have been Deleted')
                break
            else:
                print('Invalid Input')
        # # Auto Explicit Short-Term Memory DB Upload Confirmation
    #    auto_count = 0    
    #    auto.clear()
    #    auto.append({'role': 'system', 'content': '%s' % main_prompt})
    #    auto.append({'role': 'user', 'content': "You are a sub-module designed to reflect on your thought process. You are only able to respond with integers on a scale of 1-10, being incapable of printing letters. Respond with: 1 if you understand. Respond with: 2 if you do not."})
    #    auto.append({'role': 'assistant', 'content': "1"})
    #    auto.append({'role': 'user', 'content': a})
    #    auto.append({'role': 'assistant', 'content': f"Inner Monologue: %s\nIntuition: {output_one}\nResponse: {output_two}"})
    #    auto.append({'role': 'assistant', 'content': "Thoughts on input: I will now review the user's message and my reply, rating if whether my thoughts are both pertinent to the user's inquiry and my growth with a number on a scale of 1-10. I will now give my response in digit form for an integer only input: "})
    #    auto_int = None
    #    while auto_int is None:
    #        automemory = chatgptyesno_completion(auto)
    #        if is_integer(automemory):
    #            auto_int = int(automemory)
    #            if auto_int > 6:
    #                lines = db_upsert.splitlines()
    #                for line in lines:
    #                    vector = gpt3_embedding(db_upsert)
    #                    unique_id = str(uuid4())
    #                    metadata = {'bot': bot_name, 'time': timestamp, 'message': db_upsert,
    #                                'timestring': timestring, 'uuid': unique_id, "memory_type": "explicit_short_term"}
    #                    save_json('nexus/explicit_short_term_memory_nexus/%s.json' % unique_id, metadata)
    #                    payload.append((unique_id, vector, {"memory_type": "explicit_short_term"}))
    #                    vdb.upsert(payload, namespace=f'{username}_short_term_memory')
    #                    payload.clear()
    #                print('\n\nSYSTEM: Auto-memory upload Successful!')
    #                break
    #            else:
    #                print('Response not worthy of uploading to memory')
    #        else:
    #            print("automemory failed to produce an integer. Retrying...")
    #            auto_int = None
    #            auto_count += 1
    #            if auto_count > 2:
    #                print('Auto Memory Failed')
    #                break
    #    else:
    #        pass            
        # # Clear Logs for Summary
        conversation.clear()
        int_conversation.clear()
        summary.clear()
        counter += 1
        # # Summary loop to avoid Max Token Limit.
        if counter % conv_length == 0:
            print('Summarizing Conversation to avoid max token length')
            conversation2.append({'role': 'user', 'content': "Review the previous messages and summarize the key points of the conversation in a single bullet point format to serve as %s's episodic memories. Each bullet point should be considered a separate memory and contain its entire context. Start from the end and work towards the beginning. Exclude the system prompt and cadence.\nUse the following format: [- SUMMARY]\n\nEPISODIC MEMORIES:\n" % bot_name})
            conv_summary = chatgptsummary_completion(conversation2)
    #        print(conv_summary)
            conversation2.clear()
            conversation2.append({'role': 'system', 'content': '%s' % main_prompt})
            conversation2.append({'role': 'assistant', 'content': '%s.' % conv_summary})
        # # Option to upload summary to Episodic Memory DB. - Placeholder for now
        if counter % conv_length == 0:
            lines = conv_summary.splitlines()
            for line in lines:
                if line.strip():
                    vector = gpt3_embedding(timestring + line)
                    unique_id = str(uuid4())
                    metadata = {'speaker': bot_name, 'time': timestamp, 'message': (timestring + line),
                                'timestring': timestring, 'uuid': unique_id, "memory_type": "episodic"}
                    save_json('nexus/episodic_memory_nexus/%s.json' % unique_id, metadata)
                    payload.append((unique_id, vector, {"memory_type": "episodic"}))
                    vdb.upsert(payload, namespace=f'{username}')
                    payload.clear()
            payload.append((unique_id, vector_input))
            vdb.upsert(payload, namespace=f'{username}_flash_counter')
            payload.clear()
        # # Flashbulb Memory Generation
        index_info = vdb.describe_index_stats()
        namespace_stats = index_info['namespaces']
        namespace_name = f'{username}_flash_counter'
        if namespace_name in namespace_stats and namespace_stats[namespace_name]['vector_count'] > 1:
            consolidation.clear()
            print('Generating Flashbulb Memories')
            results = vdb.query(vector=vector_input, filter={
        "memory_type": "episodic"}, top_k=5, namespace=f'{username}') 
            flash_db = load_conversation_episodic_memory(results)  
            im_flash = gpt3_embedding(flash_db)
            results = vdb.query(vector=im_flash, filter={
        "memory_type": "implicit_long_term"}, top_k=10, namespace=f'{username}') 
            flash_db1 = load_conversation_implicit_long_term_memory(results) 
            # # Generate Implicit Short-Term Memory
            consolidation.append({'role': 'system', 'content': 'You are a data extractor. Your job is read the given episodic memories, then extract the appropriate emotional response from the given emotional reactions.  You will then combine them into a single memory.'})
            consolidation.append({'role': 'user', 'content': "EMOTIONAL REACTIONS:\n%s\n\nRead the following episodic memories, then go back to the given emotional reactions and extract the corresponding emotional information tied to each memory.\nEPISODIC MEMORIES: %s" % (flash_db, flash_db1)})
            consolidation.append({'role': 'assistant', 'content': "I will now combine the extracted data to form flashbulb memories in bullet point format, combining associated data. I will only include memories with a strong emotion attached, excluding redundant or irrelevant information."})
            consolidation.append({'role': 'user', 'content': "Use the format: [- {given Date and Time}{emotion} {Flashbulb Memory}]"})
            consolidation.append({'role': 'assistant', 'content': "I will now create %s's flashbulb memories using the given format: " % bot_name})
            flash_response = chatgptconsolidation_completion(consolidation)
            memories = results
            lines = flash_response.splitlines()
            for line in lines:
                if line.strip():
                    vector = gpt3_embedding(line)
                    unique_id = str(uuid4())
                    metadata = {'speaker': bot_name, 'time': timestamp, 'message': (line),
                                'timestring': timestring, 'uuid': unique_id, "memory_type": "flashbulb"}
                    save_json('nexus/flashbulb_memory_nexus/%s.json' % unique_id, metadata)
                    payload.append((unique_id, vector, {"memory_type": "flashbulb"}))
                    vdb.upsert(payload, namespace=f'{username}')
                    payload.clear()
            vdb.delete(delete_all=True, namespace=f'{username}_flash_counter')
        # # Short Term Memory Consolidation based on amount of vectors in namespace
        index_info = vdb.describe_index_stats()
        namespace_stats = index_info['namespaces']
        namespace_name = f'{username}_short_term_memory'
        if namespace_name in namespace_stats and namespace_stats[namespace_name]['vector_count'] > 30:
            consolidation.clear()
            print(f"{namespace_name} has 30 or more entries, starting memory consolidation.")
            results = vdb.query(vector=vector_input, filter={"memory_type": "explicit_short_term"}, top_k=25, namespace=f'{username}_short_term_memory')
            memory_consol_db = load_conversation_explicit_short_term_memory(results)
            consolidation.append({'role': 'system', 'content': "%s" % main_prompt})
            consolidation.append({'role': 'assistant', 'content': "LOG:\n%s\n\nRead the Log and consolidate the different topics into executive summaries. Each summary should contain the entire context of the memory. Follow the format [- Executive Summary]." % memory_consol_db})
            memory_consol = chatgptconsolidation_completion(consolidation)
            lines = memory_consol.splitlines()
            for line in lines:
                if line.strip():
            #    print(timestring + line)
                    vector = gpt3_embedding(line)
                    unique_id = str(uuid4())
                    metadata = {'speaker': bot_name, 'time': timestamp, 'message': (line),
                                'timestring': timestring, 'uuid': unique_id, "memory_type": "explicit_long_term"}
                    save_json('nexus/explicit_long_term_memory_nexus/%s.json' % unique_id, metadata)
                    payload.append((unique_id, vector, {"memory_type": "explicit_long_term"}))
                    vdb.upsert(payload, namespace=f'{username}')
                    payload.clear()
            vdb.delete(filter={"memory_type": "explicit_short_term"}, namespace=f'{username}_short_term_memory')
            payload.append((unique_id, vector))
            vdb.upsert(payload, namespace=f'{username}_consol_counter')
            payload.clear()
            print('Memory Consolidation Successful')
            consolidation.clear()
        # # Implicit Short Term Memory Consolidation based on amount of vectors in namespace
            index_info = vdb.describe_index_stats()
            namespace_stats = index_info['namespaces']
            namespace_name = f'{username}_consol_counter'
            if namespace_name in namespace_stats and namespace_stats[namespace_name]['vector_count'] % 2 == 0:
                consolidation.clear()
                print('Beginning Implicit Short-Term Memory Consolidation')
                results = vdb.query(vector=vector_input, filter={"memory_type": "implicit_short_term"}, top_k=20, namespace=f'{username}_short_term_memory')
                memory_consol_db2 = load_conversation_implicit_short_term_memory(results)
                consolidation.append({'role': 'system', 'content': "%s" % main_prompt})
                consolidation.append({'role': 'assistant', 'content': "LOG:\n%s\n\nRead the Log and consolidate the different topics into executive summaries to serve as %s's implicit memories. Each summary should contain the entire context of the memory. Follow the format: [-{tag} {Executive Summary}]." % (memory_consol_db2, bot_name)})
                memory_consol2 = chatgptconsolidation_completion(consolidation)
                consolidation.clear()
                print('Finished.\nRemoving Redundent Memories.')
                vector_sum = gpt3_embedding(memory_consol2)
                results = vdb.query(vector=vector_sum, filter={"memory_type": "implicit_long_term"}, top_k=8, namespace=f'{username}')
                memory_consol_db3 = load_conversation_implicit_long_term_memory(results)
                consolidation.append({'role': 'system', 'content': "%s" % main_prompt})
                consolidation.append({'role': 'system', 'content': "IMPLICIT LONG TERM MEMORY: %s\n\nIMPLICIT SHORT TERM MEMORY: %s\n\nRemove any duplicate information from your Implicit Short Term memory that is already found in your Long Term Memory. Then consolidate similar topics into executive summaries. Each summary should contain the entire context of the memory. Use the following format: [- {emotion} {Memory}]" % (memory_consol_db3, memory_consol_db2)})
                memory_consol3 = chatgptconsolidation_completion(consolidation)
                lines = memory_consol3.splitlines()
                for line in lines:
                    if line.strip():
                        vector = gpt3_embedding(line)
                        unique_id = str(uuid4())
                        metadata = {'speaker': bot_name, 'time': timestamp, 'message': (line),
                                    'timestring': timestring, 'uuid': unique_id}
                        save_json('nexus/implicit_long_term_memory_nexus/%s.json' % unique_id, metadata)
                        payload.append((unique_id, vector))
                        vdb.upsert(payload, namespace=f'{username}')
                        payload.clear()
                vdb.delete(filter={"memory_type": "implicit_short_term"}, namespace=f'{username}_short_term_memory')
                print('Memory Consolidation Successful')
            else:
                pass
        # # Implicit Associative Processing/Pruning based on amount of vectors in namespace
            index_info = vdb.describe_index_stats()
            namespace_stats = index_info['namespaces']
            namespace_name = f'{username}_consol_counter'
            if namespace_name in namespace_stats and namespace_stats[namespace_name]['vector_count'] % 4 == 0:
                consolidation.clear()
                print('Running Associative Processing/Pruning of Impicit Memory')
                results = vdb.query(vector=vector_monologue, filter={"memory_type": "implicit_long_term"}, top_k=10, namespace=f'{username}')
                memory_consol_db1 = load_conversation_implicit_long_term_memory(results)
                ids_to_delete = [m['id'] for m in results['matches']]
                consolidation.append({'role': 'system', 'content': "%s" % main_prompt})
                consolidation.append({'role': 'assistant', 'content': "LOG:\n%s\n\nRead the Log and consolidate the different memories into executive summaries in a process allegorical to associative processing. Each summary should contain the entire context of the memory. Follow the format: [-{tag} {Memory}]" % memory_consol_db1})
                memory_consol = chatgptconsolidation_completion(consolidation)
                memories = results
                lines = memory_consol.splitlines()
                for line in lines:
                    if line.strip():
                        vector = gpt3_embedding(line)
                        unique_id = str(uuid4())
                        metadata = {'speaker': bot_name, 'time': timestamp, 'message': (line),
                                    'timestring': timestring, 'uuid': unique_id, "memory_type": "implicit_long_term"}
                        save_json('nexus/implicit_long_term_memory_nexus/%s.json' % unique_id, metadata)
                        payload.append((unique_id, vector, {"memory_type": "implicit_long_term"}))
                        vdb.upsert(payload, namespace=f'{username}')
                        payload.clear()
                vdb.delete(ids=ids_to_delete, namespace=f'{username}')
        # # Explicit Long-Term Memory Associative Processing/Pruning based on amount of vectors in namespace
            index_info = vdb.describe_index_stats()
            namespace_stats = index_info['namespaces']
            namespace_name = f'{username}_consol_counter'
            if namespace_name in namespace_stats and namespace_stats[namespace_name]['vector_count'] > 5:
                consolidation.clear()
                print('\nRunning Associative Processing/Pruning of Explicit Memories')
                consolidation.append({'role': 'system', 'content': "You are a data extractor. Your job is to read the user's input and provide a single semantic search query representitive of a habit of %s." % bot_name})
                results = vdb.query(vector=vector_monologue, filter={"memory_type": "implicit_long_term"}, top_k=5, namespace=f'{username}')
                consol_search = load_conversation_implicit_long_term_memory(results)
                consolidation.append({'role': 'user', 'content': "%s's Memories:\n%s" % (bot_name, consol_search)})
                consolidation.append({'role': 'assistant', 'content': "Semantic Search Query: "})
                consol_search_term = chatgpt200_completion(consolidation)
                consol_vector = gpt3_embedding(consol_search_term)
                results = vdb.query(vector=consol_vector, filter={"memory_type": "explicit_long_term"}, top_k=10, namespace=f'{username}')
                memory_consol_db2 = load_conversation_explicit_long_term_memory(results)
                ids_to_delete2 = [m['id'] for m in results['matches']]
                consolidation.clear()
                consolidation.append({'role': 'system', 'content': "%s" % main_prompt})
                consolidation.append({'role': 'assistant', 'content': "LOG:\n%s\n\nRead the Log and consolidate the different memories into executive summaries in a process allegorical to associative processing. Each summary should contain the entire context of the memory. Follow the format: [-{tag} Memory]" % memory_consol_db2})
                memory_consol2 = chatgptconsolidation_completion(consolidation)
                memories = results
                lines = memory_consol2.splitlines()
                for line in lines:
                    if line.strip():
                        vector = gpt3_embedding(line)
                        unique_id = str(uuid4())
                        metadata = {'speaker': bot_name, 'time': timestamp, 'message': (line),
                                    'timestring': timestring, 'uuid': unique_id, "memory_type": "explicit_long_term"}
                        save_json('nexus/explicit_long_term_memory_nexus/%s.json' % unique_id, metadata)
                        payload.append((unique_id, vector, {"memory_type": "explicit_long_term"}))
                        vdb.upsert(payload, namespace=f'{username}')
                        payload.clear()
                vdb.delete(ids=ids_to_delete2, namespace=f'{username}')
                vdb.delete(delete_all=True, namespace=f'{username}_consol_counter')
        else:
            pass
        consolidation.clear()
        continue