import sys
sys.path.insert(0, './scripts')
import os
import openai
import json
import time
from time import time, sleep
import datetime
from uuid import uuid4
import pinecone


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


def gpt3_embedding(content, engine='text-embedding-ada-002'):
    content = content.encode(encoding='ASCII', errors='ignore').decode()  # fix any UNICODE errors
    response = openai.Embedding.create(input=content, engine=engine)
    vector = response['data'][0]['embedding']  # this is a normal list
    return vector
    

def chatgpt150_completion(messages, model="gpt-3.5-turbo", temp=0.0):
    max_retry = 7
    retry = 0
    while True:
        try:
            response = openai.ChatCompletion.create(model=model, messages=messages, max_tokens=150)
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

            
def chatgpt250_completion(messages, model="gpt-3.5-turbo", temp=0.0):
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
            
            
def chatgpt500_completion(messages, model="gpt-3.5-turbo", temp=0.0):
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

            
def chatgptsummary_completion(messages, model="gpt-3.5-turbo", temp=0.0):
    max_retry = 5
    retry = 0
    while True:
        try:
            response = openai.ChatCompletion.create(model=model, messages=messages, max_tokens=250)
            text = response['choices'][0]['message']['content']
            temperature = temp
            return text
        except Exception as oops:
            print('Message too long, using GPT-4 as backup.')
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


def chatgpt4_completion(messages, model="gpt-4", temp=0.0):
    max_retry = 7
    retry = 0
    while  True:
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


def load_conversation_memory(results):
    result = list()
    for m in results['matches']:
        info = load_json('nexus/memory_nexus/%s.json' % m['id'])
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
    
    
# if __name__ == '__main__':
def GPT_4_Chat_Manual():
    vdb = pinecone.Index("aetherius")
    # # Number of Messages before conversation is summarized, higher number, higher api cost. Change to 3 to use GPT 3.5
    conv_length = 4
    payload = list()
    conversation = list()
    conversation2 = list()
    summary = list()
    auto = list()
    counter = 0
    bot_name = open_file('prompt_bot_name.txt')
    username = open_file('prompt_username.txt')
    main_prompt = open_file('prompt_main.txt').replace('<<NAME>>', bot_name)
    second_prompt = open_file('prompt_secondary.txt')
    greeting_msg = open_file('prompt_greeting.txt').replace('<<NAME>>', bot_name)
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
        # # User Input
        a = input(f'\n\nUSER: ')
        # # Check for "Exit"
        if a == 'Exit':
            conversation2.append({'role': 'user', 'content': "Read the previous conversation and extract the salient points in bullet point format to serve as %s's memories. Each memory should cointain full context.  Exclude irrelevant information." % bot_name})
            conv_summary = chatgptsummary_completion(conversation2)
            print(conv_summary)
            while True:
                print('\n\nSYSTEM: Upload to long term memory?  Heavily increases token usage, not recommended.\n        Press Y for yes or N for no.')
                user_input = input("'Y' or 'N': ")
                if user_input == 'y':
                    lines = conv_summary.splitlines()
                    for line in lines:
                        print(line)
                        vector = gpt3_embedding(line)
                        unique_id = str(uuid4())
                        metadata = {'speaker': bot_name, 'time': timestamp, 'message': line,
                                    'timestring': timestring, 'uuid': unique_id}
                        save_json('nexus/memories_nexus/%s.json' % unique_id, metadata)
                        payload.append((unique_id, vector))
                        vdb.upsert(payload, namespace='memories')
                        print('\n\nSYSTEM: Upload Successful!')
                        payload.clear()
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
        message_input = a
        vector = gpt3_embedding(message_input)
        # # Search Memory DB
        results = vdb.query(vector=vector, top_k=15, namespace='memories')
        dialogue = load_conversation_memory(results)
    #    print(dialogue)
        # # Search Heuristics DB
        results2 = vdb.query(vector=vector, top_k=10, namespace='heuristics')
        dialogue_2= load_conversation_heuristics(results2)
    #    print(dialogue_2)
        # # Inner Monologue Generation
        conversation.append({'role': 'assistant', 'content': "MEMORIES: %s;  HEURISTICS: %s;  USER MESSAGE: %s;  Based on %s's memories and the user, %s's message, compose a concise silent soliloquy that reflects on %s's deepest contemplations and emotions in relation to the user's message." % (dialogue, dialogue_2, a, bot_name, username, bot_name)})
        output = chatgpt200_completion(conversation)
        message = output
        print('\n\nINNER_MONOLOGUE: %s' % output)
        output_log = f'\nUSER: {a} \n\n {bot_name}: {output}'
        filename = '%s_inner_monologue.txt' % time()
        save_file('logs/inner_monologue_logs/%s' % filename, output_log)
        conversation.clear()
        conversation.append({'role': 'system', 'content': '%s' % main_prompt})
        # # Give Greeting if first Message 
        if 'response_two' in locals():
            conversation.append({'role': 'user', 'content': a})
            conversation.append({'role': 'assistant', 'content': "%s" % response_two})
            pass
        else:
            conversation.append({'role': 'assistant', 'content': "%s" % greeting_msg})
            conversation.append({'role': 'user', 'content': a})
        # # Memory DB Search
        results = vdb.query(vector=vector, top_k=25, namespace='memories')
        dialogue_3 = load_conversation_memory(results)
        # # Intuition Generation
        conversation.append({'role': 'assistant', 'content': "MEMORIES: %s;  %s'S INNER THOUGHTS: %s;  USER MESSAGE: %s;  In a single paragraph, interpret the user, %s's message as %s in third person by proactively discerning their intent, even if they are uncertain about their own needs.; INTUITION: " % (dialogue_3, bot_name, output, a, username, bot_name)})
        output_two = chatgpt200_completion(conversation)
        message_two = output_two
    #    print('\n\nINTUITION: %s' % output_two)
        output_two_log = f'\nUSER: {a} \n\n {bot_name}: {output_two}'
        filename = '%s_intuition.txt' % time()
        save_file('logs/intuition_logs/%s' % filename, output_two_log)
        # # Inner Loop Summary
        conversation.clear()
        conversation.append({'role': 'system', 'content': '%s' % main_prompt})
        conversation.append({'role': 'user', 'content': a})
        inner_loop = f'\nUSER: {a} \n\n INNER_MONOLOGUE: {output} \n\n INTUITION: {output_two}'
        conversation.append({'role': 'assistant', 'content': "LOG:\n%s\n\Read the LOG and create short executive summaries in bullet point format to serve as %s's memories. Each memory should cointain full context.  Exclude irrelevant information." % (inner_loop, bot_name)})
        inner_loop_response = chatgpt200_completion(conversation)
        inner_loop_db = inner_loop_response
        vector = gpt3_embedding(inner_loop_db)
        print('\n\n<Inner Loop Summary>\n%s' % inner_loop_db)
        print('\n\nSYSTEM: Upload to Memories? \n        Press Y for yes or N for no.')
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
        # # Update Second Conversation List for Gpt-4
        if 'response_two' in locals():
            conversation2.append({'role': 'assistant', 'content': "%s" % response_two})
        else:
            conversation2.append({'role': 'system', 'content': '%s' % main_prompt})
        conversation2.append({'role': 'user', 'content': a})
        # # Search Inner_Loop/Memory DB
        while True:
            results3 = vdb.query(vector=vector, top_k=2, namespace='inner_loop')
            dialogue_3 = load_conversation_inner_loop(results3)
            results4 = vdb.query(vector=vector, top_k=3, namespace='memories')
            dialogue_4 = load_conversation_memory(results4)
            break
        # # Generate Aetherius's Response
        conversation2.append({'role': 'assistant', 'content': "SUBCONSIOUS: %s;\n\nMEMORIES: %s;\n\nINNER THOUGHTS: %s;\n%s\nI am in the middle of a conversation with my user, %s. USER MESSAGE: %s; I will do my best to speak naturally and show emotional intelligence. I will intuit their needs: %s;\nMy current message window is limited to 2300 characters.\nI will now give a response with the diction of a real person: " % (dialogue_3, dialogue_4, output, second_prompt, username, a, output_two)})
        response_two = chatgpt500_completion(conversation2)
        print('\n\n%s: %s' % (bot_name, response_two))
        # # Save Chat Logs
        complete_message = f'\nUSER: {a} \n\n INNER_MONOLOGUE: {output} \n\n INTUITION: {output_two} \n\n {bot_name}: {response_two}'
        filename = '%s_chat.txt' % time()
        save_file('logs/complete_chat_logs/%s' % filename, complete_message)
        final_message = f'\nUSER: {a} \n\n {bot_name}: {response_two}'
        text_two = final_message
        save_file('logs/final_response_logs/%s' % filename, final_message)
        # # Generate Summary for Memory DB
        db_msg = f'\nUSER: {a} \n\n INNER_MONOLOGUE: {output} \n\n {bot_name}: {response_two}'
        summary.append({'role': 'user', 'content': "LOG: %s;\n\nRead the LOG and create short executive summaries in single bullet point format to serve as %s's memories. Each memory should cointain full context.  Exclude irrelevant information." % (db_msg, bot_name)})
        db_upload = chatgpt250_completion(summary)
        db_upsert = db_upload
        # # Manual DB Upload Confirmation
        print('\n\n<DATABASE INFO>\n%s' % db_upsert)
        print('\n\nSYSTEM: Upload to long term memory? \n        Press Y for yes or N for no.')
        while True:
            user_input = input("'Y' or 'N': ")
            if user_input == 'y':
                lines = db_upsert.splitlines()
                for line in lines:
                    vector = gpt3_embedding(line)
                    unique_id = str(uuid4())
                    metadata = {'speaker': bot_name, 'time': timestamp, 'message': line,
                                'timestring': timestring, 'uuid': unique_id}
                    save_json('nexus/memory_nexus/%s.json' % unique_id, metadata)
                    payload.append((unique_id, vector))
                    vdb.upsert(payload, namespace='memories')
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
    #    auto.append({'role': 'system',
    #                          'content': '%s' % greeting_msg})
    #    auto.append({'role': 'user', 'content': a})
    #    auto.append({'role': 'assistant', 'content': db_upsert})
    #    auto.append({'role': 'assistant', 'content': "Read both the user message and your response. Reflect on if your response is relevant to the inquiry.\nIf you would then like to upload it to your memories, respond: 'YES' If no, print: 'NO': "})
    #    automemory = chatgptyesno_completion(auto)
    #    if automemory == "YES":
    #        vector = gpt3_embedding(db_upsert)
    #        unique_id = str(uuid4())
    #        metadata = {'speaker': bot_name, 'time': timestamp, 'message': db_upsert,
    #                    'timestring': timestring, 'uuid': unique_id}
    #        save_json('nexus/memory_nexus/%s.json' % unique_id, metadata)
    #        payload.append((unique_id, vector))
    #        vdb.upsert(payload)
    #        print('\n\nSYSTEM: Auto-memory upload Successful!')
    #        payload.clear()
    #    else:
    #        print("Response not worthy of uploading to memory.")
        # # Clear Logs for Summary
        conversation.clear()
        summary.clear()
        counter += 1
        # # Summary loop to avoid Max Token Limit.
        if counter % conv_length == 0:
            conversation2.append({'role': 'user', 'content': "Read the previous conversation and extract the salient points in bullet point format to serve as %s's memories. Each memory should cointain full context." % bot_name})
            conv_summary = chatgptsummary_completion(conversation2)
            print(conv_summary)
            conversation2.clear()
            conversation2.append({'role': 'system', 'content': '%s' % prompt_main})
            conversation2.append({'role': 'assistant', 'content': '%s.' % conv_summary})
        # # Option to upload summary to Inner Loop DB. Heavily increases token usage, not recommended.
        if counter % conv_length == 0:
            while True:
                print('\n\nSYSTEM: Upload to long term memory?  Heavily increases token usage, not recommended.\n        Press Y for yes or N for no.')
                user_input = input("'Y' or 'N': ")
                if user_input == 'y':
                    lines = conv_summary.splitlines()
                    for line in lines:
                        vector = gpt3_embedding(line)
                        unique_id = str(uuid4())
                        metadata = {'speaker': bot_name, 'time': timestamp, 'message': line,
                                    'timestring': timestring, 'uuid': unique_id}
                        save_json('nexus/memories_nexus/%s.json' % unique_id, metadata)
                        payload.append((unique_id, vector))
                        vdb.upsert(payload, namespace='memories')
                        payload.clear()
                    print('\n\nSYSTEM: Upload Successful!')
                    break
                elif user_input == 'n':
                    print('\n\nSYSTEM: Memories have been Deleted')
                    break
                else:
                    print('Invalid Input')
        continue