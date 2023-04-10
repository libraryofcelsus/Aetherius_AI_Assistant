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


def DB_Upload_Secondary_World_Info():
    # key = input("Enter OpenAi API KEY:")
    vdb = pinecone.Index("aetherius")
    index_info = vdb.describe_index_stats()
    print('Pinecone DB Info')
    print(index_info)
    bot_name = open_file('prompt_bot_name.txt')
    if not os.path.exists('nexus/world_info_nexus'):
        os.makedirs('nexus/wi_nexus')
    while True:
        payload = list()
        a = input(f'\n\nUSER: ')
        if a == 'Exit':
            print('\n\nSYSTEM: Are you sure you want to exit?')
            while True:
                print('        Press Y for yes, N for no, or C to cancel.')
                user_input = input("'Y' or 'N': ")
                if user_input == 'y':
                    return
                elif user_input == 'n':
                    return
                elif user_input == 'c':
                    print('\n\nSYSTEM: Exit Cancelled')
                    a = input(f'\n\nUSER: ')
                    break
            else:
                pass
        vector = gpt3_embedding(a)
        timestamp = time()
        timestring = timestamp_to_datetime(timestamp)
        unique_id = str(uuid4())
        metadata = {'speaker': '{bot_name}', 'time': timestamp, 'message': a, 'timestring': timestring,
                    'uuid': unique_id}
        save_json('nexus/world_info_nexus/%s.json' % unique_id, metadata)
        payload.append((unique_id, vector))
        vdb.upsert(payload, namespace='world_info')
        print('\n\nSYSTEM: Upload Successful!')