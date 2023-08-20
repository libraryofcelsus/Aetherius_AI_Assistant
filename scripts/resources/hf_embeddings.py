import sys
import os
import datetime
from uuid import uuid4
import requests
from basic_functions import *

    
def embeddings(query):
    hf_token = open_file('api_keys/key_hf_token.txt')
    model_id = 'sentence-transformers/all-mpnet-base-v2'
    api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{model_id}"
    headers = {"Authorization": f"Bearer {hf_token}"}
    response = requests.post(api_url, headers=headers, json={"inputs": [query], "options":{"wait_for_model":True}})
    response1 = response.json()
    response2 = response1[0]
    return response2