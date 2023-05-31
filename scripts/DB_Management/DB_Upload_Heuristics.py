import os
import sys
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


def DB_Upload_Heuristics():
    # key = input("Enter OpenAi API KEY:")
    vdb = pinecone.Index("aetherius")
    index_info = vdb.describe_index_stats()
    print('Pinecone DB Info')
    print(index_info)
    print("Type [Delete All Data] to delete saved Heuristics.")
    username = open_file('./config/prompt_username.txt')
    bot_name = open_file('./config/prompt_bot_name.txt')
    if not os.path.exists('nexus/{bot_name}/{username}/heuristics_nexus'):
        os.makedirs('nexus/{bot_name}/{username}/heuristics_nexus')
    while True:
        payload = list()
        a = input(f'\n\nUSER: ')
        if a == 'Delete All Data':
            while True:
                print('\n\nSYSTEM: Are you sure you would like to delete the saved Heuristics?\n        Press Y for yes or N for no.')
                user_input = input("'Y' or 'N': ")
                if user_input == 'y':
                    vdb.delete(filter={"memory_type": "heuristics", "user": username}, namespace=f'{bot_name}')
                    while True:
                        print('All heuristics have been Deleted')
                        return
                elif user_input == 'n':
                    print('\n\nSYSTEM: Heuristics delete cancelled.')
                    return
            else:
                pass
        if a == 'Exit':
            while True:
                return
            else:
                pass
        vector = gpt3_embedding(a)
        timestamp = time()
        timestring = timestamp_to_datetime(timestamp)
        unique_id = str(uuid4())
        metadata = {'speaker': 'AETHERIUS', 'time': timestamp, 'message': a, 'timestring': timestring,
                    'uuid': unique_id, "memory_type": "heuristics", "user": username}
        save_json('nexus/{bot_name}/{username}/heuristics_nexus/%s.json' % unique_id, metadata)
        payload.append((unique_id, vector, {"memory_type": "heuristics", "user": username}))
        vdb.upsert(payload, namespace=f'{bot_name}')
        print('\n\nSYSTEM: Upload Successful!')