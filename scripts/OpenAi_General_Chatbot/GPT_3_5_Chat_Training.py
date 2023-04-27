import sys
sys.path.insert(0, './scripts')
sys.path.insert(0, './config')
sys.path.insert(0, './config/Chatbot_Prompts')
import os
import openai
import json
import time
from time import time, sleep
import datetime
from uuid import uuid4
import pinecone
# import speech_recognition as sr
# from gtts import gTTS
# from playsound import playsound
# import pyttsx3
# from pydub import AudioSegment
# from pydub.playback import play
# from pydub import effects


def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()


def save_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as outfile:
        outfile.write(content)


def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return json.load(infile)


def save_json(filepath, payload):
    with open(filepath, 'w', encoding='utf-8') as outfile:
        json.dump(payload, outfile, ensure_ascii=False, sort_keys=True, indent=2)


def timestamp_to_datetime(unix_time):
    return datetime.datetime.fromtimestamp(unix_time).strftime("%A, %B %d, %Y at %I:%M%p %Z")
    
    
def is_integer(value):
    try:
        int(value)
        return True
    except ValueError:
        return False


def gpt3_embedding(content, engine='text-embedding-ada-002'):
    content = content.encode(encoding='ASCII', errors='ignore').decode()  # fix any UNICODE errors
    response = openai.Embedding.create(input=content, engine=engine)
    vector = response['data'][0]['embedding']  # this is a normal list
    return vector
    

def chatgpt200_completion(messages, model="gpt-3.5-turbo", temp=0.0):
    max_retry = 7
    retry = 0
    while  True:
        try:
            response = openai.ChatCompletion.create(model=model, messages=messages, max_tokens=200)
            text = response['choices'][0]['message']['content']
            temperature = temp
            return text
        except Exception as oops:
            retry += 1
            if retry >= max_retry:
                print(f"Exiting due to an error in ChatGPT: {oops}")
                exit(1)
            print(f'Error communicating with OpenAI: "{oops}" - Retrying in {2 ** (retry - 1) * 5} seconds...')
            sleep(2 ** (retry - 1) * 5)

            
def chatgpt250_completion(messages, model="gpt-3.5-turbo", temp=0.4):
    max_retry = 7
    retry = 0
    while True:
        try:
            response = openai.ChatCompletion.create(model=model, messages=messages, max_tokens=250)
            text = response['choices'][0]['message']['content']
            temperature = temp
            return text
        except Exception as oops:
            retry += 1
            if retry >= max_retry:
                print(f"Exiting due to an error in ChatGPT: {oops}")
                exit(1)
            print(f'Error communicating with OpenAI: "{oops}" - Retrying in {2 ** (retry - 1) * 5} seconds...')
            sleep(2 ** (retry - 1) * 5)
            
            
def chatgpt500_completion(messages, model="gpt-3.5-turbo", temp=0.4):
    max_retry = 7
    retry = 0
    while True:
        try:
            response = openai.ChatCompletion.create(model=model, messages=messages, max_tokens=500)
            text = response['choices'][0]['message']['content']
            temperature = temp
            return text
        except Exception as oops:
            retry += 1
            if retry >= max_retry:
                print(f"Exiting due to an error in ChatGPT: {oops}")
                exit(1)
            print(f'Error communicating with OpenAI: "{oops}" - Retrying in {2 ** (retry - 1) * 5} seconds...')
            sleep(2 ** (retry - 1) * 5)
            
            
def chatgptyesno_completion(messages, model="gpt-3.5-turbo", temp=0.0):
    max_retry = 7
    retry = 0
    while True:
        try:
            response = openai.ChatCompletion.create(model=model, messages=messages, max_tokens=1)
            text = response['choices'][0]['message']['content']
            temperature = temp
        #    filename = '%s_chat.txt' % time()
        #    if not os.path.exists('chat_logs'):
        #        os.makedirs('chat_logs')
        #    save_file('chat_logs/%s' % filename, str(messages) + '\n\n==========\n\n' + text)
            return text
        except Exception as oops:
            retry += 1
            if retry >= max_retry:
                print(f"Exiting due to an error in ChatGPT: {oops}")
                exit(1)
            print(f'Error communicating with OpenAI: "{oops}" - Retrying in {2 ** (retry - 1) * 5} seconds...')
            sleep(2 ** (retry - 1) * 5)
            
            
def chatgpt35summary_completion(messages, model="gpt-3.5-turbo", temp=0.0):
    max_retry = 7
    retry = 0
    while True:
        try:
            response = openai.ChatCompletion.create(model=model, messages=messages, max_tokens=400)
            text = response['choices'][0]['message']['content']
            temperature = temp
            return text
        except Exception as oops:
            retry += 1
            if retry >= max_retry:
                print(f"Exiting due to an error in ChatGPT: {oops}")
                exit(1)
            print(f'Error communicating with OpenAI: "{oops}" - Retrying in {2 ** (retry - 1) * 5} seconds...')
            sleep(2 ** (retry - 1) * 5)


def load_conversation_short_term_memory(results):
    result = list()
    for m in results['matches']:
        info = load_json('nexus/short_term_memory_nexus/%s.json' % m['id'])
        result.append(info)
    ordered = sorted(result, key=lambda d: d['time'], reverse=False)  # sort them all chronologically
    messages = [i['message'] for i in ordered]
    return '\n'.join(messages).strip()
    
    
def load_conversation_long_term_memory(results):
    result = list()
    for m in results['matches']:
        info = load_json('nexus/long_term_memory_nexus/%s.json' % m['id'])
        result.append(info)
    ordered = sorted(result, key=lambda d: d['time'], reverse=False)  # sort them all chronologically
    messages = [i['message'] for i in ordered]
    return '\n'.join(messages).strip()
    
    
def load_conversation_episodic_memory(results):
    result = list()
    for m in results['matches']:
        info = load_json('nexus/episodic_memory_nexus/%s.json' % m['id'])
        result.append(info)
    ordered = sorted(result, key=lambda d: d['time'], reverse=False)  # sort them all chronologically
    messages = [i['message'] for i in ordered]
    return '\n'.join(messages).strip()  
    
    
def load_conversation_heuristics(results):
    result = list()
    for m in results['matches']:
        info = load_json('nexus/heuristics_nexus/%s.json' % m['id'])
        result.append(info)
    ordered = sorted(result, key=lambda d: d['time'], reverse=False)  # sort them all chronologically
    messages = [i['message'] for i in ordered]
    return '\n'.join(messages).strip()    


def load_conversation_inner_loop(results):
    result = list()
    for m in results['matches']:
        info = load_json('nexus/inner_loop_nexus/%s.json' % m['id'])
        result.append(info)
    ordered = sorted(result, key=lambda d: d['time'], reverse=False)  # sort them all chronologically
    messages = [i['message'] for i in ordered]
    return '\n'.join(messages).strip()  
    
    
def load_conversation_cadence(results):
    result = list()
    for m in results['matches']:
        info = load_json('nexus/cadence_nexus/%s.json' % m['id'])
        result.append(info)
    ordered = sorted(result, key=lambda d: d['time'], reverse=False)  # sort them all chronologically
    messages = [i['message'] for i in ordered]
    return '\n'.join(messages).strip()  
    
    
# if __name__ == '__main__':
def GPT_3_5_Chat_Training():
    vdb = pinecone.Index("aetherius")
    # # Number of Messages before conversation is summarized, higher number, higher api cost. Change to 3 when using GPT 3.5
    conv_length = 3
    print("Type [Save and Exit] to summarize the conversation and exit.")
    print("Type [Exit] to exit without saving.")
    payload = list()
    conversation = list()
    int_conversation = list()
    conversation2 = list()
    summary = list()
    auto = list()
    tasklist = list()
    consolidation  = list()
    counter = 0
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
        conversation.append({'role': 'system', 'content': '%s' % main_prompt})
        # # Get Previous Message if availble
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
        # # Update Intuition List
        int_conversation.append({'role': 'system', 'content': '%s' % main_prompt})
        # # Check for "Exit"
        if a == 'Exit':
            return
        if a == 'Save and Exit':
            conversation2.append({'role': 'user', 'content': "Review the previous messages and summarize the key points of the conversation in a single bullet point format to serve as %s's episodic memories. Each bullet point should be considered a separate memory and contain its entire context. Start from the end and work towards the beginning. Exclude the system prompt and cadence.\nMemories:\n" % bot_name})
            conv_summary = chatgpt35summary_completion(conversation2)
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
        db_term = {}
        db_term_result = {}
        tasklist_counter = 0
        lines = tasklist_output.splitlines()
        for line in lines:
        #    print(line)
            tasklist_vector = gpt3_embedding(line)
            tasklist_counter += 1
            db_term[tasklist_counter] = tasklist_vector
            results = vdb.query(vector=db_term[tasklist_counter], top_k=4, namespace='long_term_memory')
            db_term_result[tasklist_counter] = load_conversation_long_term_memory(results)
            conversation.append({'role': 'assistant', 'content': "MEMORIES: %s" % db_term_result[tasklist_counter]})
            int_conversation.append({'role': 'assistant', 'content': "MEMORIES: %s" % db_term_result[tasklist_counter]})
        #    print(db_term_result[tasklist_counter])
        tasklist.clear()
        # # Search Memory DB
        results = vdb.query(vector=vector_input, top_k=5, namespace='episodic_memories')
        db_search_7 = load_conversation_episodic_memory(results)
        results = vdb.query(vector=vector_input, top_k=20, namespace='short_term_memory')
        db_search_9 = load_conversation_short_term_memory(results)
    #    print(db_search)
        # # Search Heuristics DB
        results = vdb.query(vector=vector_input, top_k=7, namespace='heuristics')
        db_search_2= load_conversation_heuristics(results)
    #    print(db_search_2)
        # # Inner Monologue Generation
        conversation.append({'role': 'assistant', 'content': "MEMORIES: %s;%s;\n\nHEURISTICS: %s;\nUSER MESSAGE: %s;\nBased on %s's memories and the user, %s's message, compose a brief silent soliloquy as %s's inner monologue that reflects on %s's deepest contemplations and emotions in relation to the user's message.\n\nINNER_MONOLOGUE: " % (db_search_7, db_search_9, db_search_2, a, bot_name, username, bot_name, bot_name)})
        output = chatgpt250_completion(conversation)
        message = output
        vector_monologue = gpt3_embedding('Inner Monologue: ' + message)
        print('\n\nINNER_MONOLOGUE: %s' % output)
        output_log = f'\nUSER: {a}\n\n{bot_name}: {output}'
        # # Clear Conversation List for Intuition Generation
        conversation.clear()
        # # Memory DB Search
        results = vdb.query(vector=vector_monologue, top_k=4, namespace='episodic_memories')
        db_search_6 = load_conversation_episodic_memory(results)
        results = vdb.query(vector=vector_input, top_k=20, namespace='short_term_memory')
        db_search_10 = load_conversation_short_term_memory(results)
    #    print(db_search_3)
        # # Intuition Generation
        int_conversation.append({'role': 'assistant', 'content': "%s" % greeting_msg})
        int_conversation.append({'role': 'user', 'content': a})
        int_conversation.append({'role': 'assistant', 'content': "MEMORIES: %s;\n%s\n\n%s'S INNER THOUGHTS: %s;\nUSER MESSAGE: %s;\nIn a single paragraph, interpret the user, %s's message as %s in third person by proactively discerning their intent, even if they are uncertain about their own needs.;\nINTUITION: " % (db_search_6, db_search_10, bot_name, output, a, username, bot_name)})
        output_two = chatgpt200_completion(int_conversation)
        message_two = output_two
    #    print('\n\nINTUITION: %s' % output_two)
        output_two_log = f'\nUSER: {a}\n\n{bot_name}: {output_two}'
        # # Inner Loop Summary
        int_conversation.clear()
        conversation.append({'role': 'system', 'content': '%s' % main_prompt})
        conversation.append({'role': 'user', 'content': a})
        inner_loop = f'\nUSER: {a} \n\n INNER_MONOLOGUE: {output} \n\n INTUITION: {output_two}'
        conversation.append({'role': 'assistant', 'content': "LOG:\n%s\n\Read the log and create short executive summaries in bullet point format to serve as %s's implicit memories. Each bullet point should be considered a separate memory and contain all context. Start from the end and work towards the beginning, combining assosiated topics. Ignore the system prompt.\nMemories:\n" % (inner_loop, bot_name)})
        inner_loop_response = chatgpt200_completion(conversation)
        inner_loop_db = inner_loop_response
        vector = gpt3_embedding(inner_loop_db)
        print('\n\n<Inner Loop Summary>\n%s' % inner_loop_db)
        print('\n\nSYSTEM: Upload to Subconsious? This DB takes priority over normal memories, only upload general goals.\n        Press Y for yes or N for no.')
        while True:
            user_input = input("'Y' or 'N': ")
            if user_input == 'y':
                lines = inner_loop_db.splitlines()
                for line in lines:
                    vector = gpt3_embedding(line)
                    unique_id = str(uuid4())
                    metadata = {'speaker': bot_name, 'time': timestamp, 'message': line,
                                'timestring': timestring, 'uuid': unique_id}
                    save_json('nexus/inner_loop_nexus/%s.json' % unique_id, metadata)
                    payload.append((unique_id, vector))
                    vdb.upsert(payload, namespace='inner_loop')
                    payload.clear()
                print('\n\nSYSTEM: Upload Successful!')
                break
            elif user_input == 'n':
                print('\n\nSYSTEM: Memories have been Deleted')
                break
            else:
                print('Invalid Input')
        # # Update Second Conversation List for Response
        if 'response_two' in locals():
            conversation2.append({'role': 'assistant', 'content': "%s" % response_two})
        else:
            conversation2.append({'role': 'system', 'content': '%s' % main_prompt})
            conversation2.append({'role': 'assistant', 'content': '%s' % greeting_msg})
            # # Generate Cadence
            results = vdb.query(vector=vector_input, top_k=2, namespace='cadence')
            dialogue_5 = load_conversation_cadence(results)
    #        print(dialogue_5)
            conversation2.append({'role': 'assistant', 'content': "I will extract the cadence from the following messages and mimic it to the best of my ability: %s" % dialogue_5})
        conversation2.append({'role': 'user', 'content': a})
        # # Search Inner_Loop/Memory DB
        while True:
            results = vdb.query(vector=vector_monologue, top_k=7, namespace='inner_loop')
            db_search_4 = load_conversation_inner_loop(results)
    #        print(db_search_4)
            results = vdb.query(vector=vector_input, top_k=4, namespace='long_term_memory')
            db_search_5 = load_conversation_long_term_memory(results)
     #       print(db_search_5)
            results = vdb.query(vector=vector_monologue, top_k=4, namespace='episodic_memories')
            db_search_8 = load_conversation_episodic_memory(results)
            break
        # # Generate Aetherius's Response
        conversation2.append({'role': 'assistant', 'content': "SUBCONSIOUS: %s;\n\nMEMORIES: %s\n%s\n\nINNER THOUGHTS: %s;\n%s\nI am in the middle of a conversation with my user, %s. USER MESSAGE: %s; I will do my best to speak naturally and show emotional intelligence. I will intuit their needs: %s;\nMy current message window is limited to 2300 characters.\nI will now give a response with the diction of a real person: " % (db_search_4, db_search_5, db_search_8, output, second_prompt, username, a, output_two)})
        response_two = chatgpt500_completion(conversation2)
        print('\n\n%s: %s' % (bot_name, response_two))
        complete_message = f'\nUSER: {a}\n\nINNER_MONOLOGUE: {output}\n\nINTUITION: {output_two}\n\n{bot_name}: {response_two}'
        final_message = f'\nUSER: {a}\n\n{bot_name}: {response_two}'
        # # TTS 
    #    tts = gTTS(response_two)
        # TTS save to file in .mp3 format
    #    counter2 += 1
    #    filename = f"{counter2}.{extension}"
    #    tts.save(filename)
            # TTS repeats chatGPT response  
    #    sound = AudioSegment.from_file(filename, format="mp3")
    #    octaves = 0.20
    #    new_sample_rate = int(sound.frame_rate * (1.7 ** octaves))
    #    mod_sound = sound._spawn(sound.raw_data, overrides={'frame_rate': new_sample_rate})
    #    mod_sound = mod_sound.set_frame_rate(44100)
    #    play(mod_sound)
    #    os.remove(filename)
        # # Generate Summary for Memory DB
        db_msg = f'\nUSER: {a} \n\n INNER_MONOLOGUE: {output} \n\n {bot_name}: {response_two}'
        summary.append({'role': 'user', 'content': "LOG:\n%s\n\Read the log and create short executive summaries in bullet point format to serve as %s's semantic memories. Each bullet point should be considered a separate memory and contain all context. Start from the end and work towards the beginning, combining assosiated topics.\nMemories:\n" % (db_msg, bot_name)})
        db_upload = chatgpt35summary_completion(summary)
        db_upsert = db_upload
        # # Save Chat Logs
        filename = '%s_inner_monologue.txt' % timestamp
        save_file('logs/inner_monologue_logs/%s' % filename, output_log)
        filename = '%s_intuition.txt' % timestamp
        save_file('logs/intuition_logs/%s' % filename, output_two_log)
        filename = '%s_response.txt' % timestamp
        save_file('logs/final_response_logs/%s' % filename, final_message)
        filename = '%s_chat.txt' % timestamp
        save_file('logs/complete_chat_logs/%s' % filename, complete_message)
        # # Manual DB Upload Confirmation
        print('\n\n<DATABASE INFO>\n%s' % db_upsert)
        print('\n\nSYSTEM: Upload to short term memory? \n        Press Y for yes or N for no.')
        while True:
            user_input = input("'Y' or 'N': ")
            if user_input == 'y':
                lines = db_upsert.splitlines()
                for line in lines:
                    vector = gpt3_embedding(line)
                    unique_id = str(uuid4())
                    metadata = {'speaker': bot_name, 'time': timestamp, 'message': line,
                                'timestring': timestring, 'uuid': unique_id}
                    save_json('nexus/short_term_memory_nexus/%s.json' % unique_id, metadata)
                    payload.append((unique_id, vector))
                    vdb.upsert(payload, namespace='short_term_memory')
                    payload.clear()
                print('\n\nSYSTEM: Upload Successful!')
                break
            elif user_input == 'n':
                print('\n\nSYSTEM: Memories have been Deleted')
                break
            else:
                print('Invalid Input')
        # # Auto Upload to Memory DB
    #    auto.clear()
    #    auto.append({'role': 'system', 'content': "You are a sub-module designed to rate responses. You are only able to respond with integers on a scale of 1-10. You are incapable of printing letters."})
    #    auto.append({'role': 'user', 'content': a})
    #    auto.append({'role': 'assistant', 'content': "%s" % response_two})
    #    auto.append({'role': 'assistant', 'content': "I will now review the user's message and my reply, rating whether my response is both pertinent to the user's inquiry and my growth with a number on a scale of 1-10. I will now give my response for a python int input: "})
    #    auto_int = None
    #    while auto_int is None:
    #        automemory = chatgptyesno_completion(auto)
    #        if is_integer(automemory):
    #            auto_int = int(automemory)
    #        else:
    #            print("automemory failed to produce an integer. Retrying...")
    #    while True:
    #        if auto_int > 6:
    #            lines = db_upsert.splitlines()
    #            for line in lines:
    #                vector = gpt3_embedding(db_upsert)
    #                unique_id = str(uuid4())
    #                metadata = {'speaker': bot_name, 'time': timestamp, 'message': db_upsert,
    #                            'timestring': timestring, 'uuid': unique_id}
    #                save_json('nexus/short_term_memory_nexus/%s.json' % unique_id, metadata)
    #                payload.append((unique_id, vector))
    #                vdb.upsert(payload, namespace='short_term_memory')
    #                payload.clear()
    #            print('\n\nSYSTEM: Auto-memory upload Successful!')
    #            break
    #        else:
    #            print("Response not worthy of uploading to memory.")
    #            break
    #    else:
    #        print('Error with internal prompt, please report on github')
    #        pass
        # # Clear Logs for Summary
        conversation.clear()
        summary.clear()
        counter += 1
        # # Short Term Memory Consolidation
        index_info = vdb.describe_index_stats()
        namespace_stats = index_info['namespaces']
        namespace_name = 'short_term_memory'
        if namespace_name in namespace_stats and namespace_stats[namespace_name]['vector_count'] > 13:
            print(f"{namespace_name} has 15 or more entries, starting memory consolidation.")
            results = vdb.query(vector=vector_input, top_k=50, namespace='short_term_memory')
            memory_consol_db = load_conversation_short_term_memory(results)
            consolidation.append({'role': 'system', 'content': "%s" % main_prompt})
            consolidation.append({'role': 'assistant', 'content': "LOG:\n%s\n\nRead the Log and consolidate the different topics into executive summaries. Each summary should contain the entire context of the memory. Follow the format [- Executive Summary]." % memory_consol_db})
            memory_consol = chatgpt35summary_completion(consolidation)
            lines = memory_consol.splitlines()
            for line in lines:
            #    print(timestring + line)
                vector = gpt3_embedding(line)
                print(line)
                unique_id = str(uuid4())
                metadata = {'speaker': bot_name, 'time': timestamp, 'message': (line),
                            'timestring': timestring, 'uuid': unique_id}
                save_json('nexus/long_term_memory_nexus/%s.json' % unique_id, metadata)
                payload.append((unique_id, vector))
                vdb.upsert(payload, namespace='long_term_memory')
                payload.clear()
            vdb.delete(delete_all=True, namespace='short_term_memory')
            print('Memory Consolidation Successful')
            consolidation.clear()
        else:
            pass
        # # Summary loop to avoid Max Token Limit.
        if counter % conv_length == 0:
            conversation2.append({'role': 'user', 'content': "Review the previous messages and summarize the key points of the conversation in a single bullet point format to serve as %s's episodic memories. Each bullet point should be considered a separate memory and contain its entire context. Start from the end and work towards the beginning. Exclude the system prompt and cadence.\nMemories:\n" % bot_name})
            conv_summary = chatgpt35summary_completion(conversation2)
            print(conv_summary)
            conversation2.clear()
            conversation2.append({'role': 'system', 'content': '%s' % main_prompt})
            conversation2.append({'role': 'assistant', 'content': '%s.' % conv_summary})
        # # Option to upload summary to Memory DB.
        if counter % conv_length == 0:
            while True:
                print('\n\nSYSTEM: Upload to episodic memory?\n        Press Y for yes or N for no.')
                user_input = input("'Y' or 'N': ")
                if user_input == 'y':
                    lines = conv_summary.splitlines()
                    for line in lines:
                        vector = gpt3_embedding(timestring + line)
                        unique_id = str(uuid4())
                        metadata = {'speaker': bot_name, 'time': timestamp, 'message': (timestring + line),
                                    'timestring': timestring, 'uuid': unique_id}
                        save_json('nexus/episodic_memory_nexus/%s.json' % unique_id, metadata)
                        payload.append((unique_id, vector))
                        vdb.upsert(payload, namespace='episodic_memories')
                        payload.clear()
                    print('\n\nSYSTEM: Upload Successful!')
                    break
                elif user_input == 'n':
                    print('\n\nSYSTEM: Memories have been Deleted')
                    break
                else:
                    print('Invalid Input')
        continue