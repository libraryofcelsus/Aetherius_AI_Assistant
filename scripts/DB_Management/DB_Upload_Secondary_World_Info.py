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
    print("Type [Delete All Data] to delete saved World Info.")
    bot_name = open_file('prompt_bot_name.txt')
    if not os.path.exists('nexus/world_info_nexus'):
        os.makedirs('nexus/wi_nexus')
    while True:
        payload = list()
        a = input(f'\n\nUSER: ')
        if a == 'Delete All Data':
            while True:
                print('\n\nSYSTEM: Are you sure you would like to delete the saved World Information?\n        Press Y for yes or N for no.')
                user_input = input("'Y' or 'N': ")
                if user_input == 'y':
                    vdb.delete(delete_all=True, namespace="world_info")
                    while True:
                        print('All saved World Information has been Deleted')
                        return
                elif user_input == 'n':
                    print('\n\nSYSTEM: World Info delete cancelled.')
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
        metadata = {'speaker': '{bot_name}', 'time': timestamp, 'message': a, 'timestring': timestring,
                    'uuid': unique_id}
        save_json('nexus/world_info_nexus/%s.json' % unique_id, metadata)
        payload.append((unique_id, vector))
        vdb.upsert(payload, namespace='world_info')
        print('\n\nSYSTEM: Upload Successful!')