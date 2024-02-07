import sys
sys.path.insert(0, './Aetherius_API/resources')
import os
from openai import OpenAI
import time
from time import time, sleep

def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()

key_path = open_file('./Aetherius_API/api_keys/key_openai.txt')

service2 = OpenAI(api_key=key_path)
    
    
def gpt_vision(query, image_path):
    try:
        prompt = "You are a sub-module for an Ai agent system.  Your task is to act as the eyes for the system.  Ensure you give detailed and verbose descriptions of what you see so the other agents can understand.  Try and keep your description within paragraph length."
        sub_prompt = " "
        if len(query) > 2:
            sub_prompt = f"\nPlease consider the user's inquiry in your response, tailoring your description to it.\nUSER INQUIRY: {query}"
        response = service2.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"{prompt} {sub_prompt}"},
                        {
                            "type": "image_url",
                            "image_url": image_path,
                        },
                    ],
                }
            ],
            max_tokens=500,
        )

        response = response.choices[0].message.content
        if len(query) < 1:
            response = f"The user has sent an image to you.  Here is a description of the image:\n{response}"
        print(response)
        return response
    except Exception as e:
        print(f"ERROR WITH VISION: {e}")