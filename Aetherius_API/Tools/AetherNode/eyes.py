import sys
sys.path.insert(0, './Aetherius_API/resources')
import os
import time
import base64
import requests

def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()

key_path = open_file('./Aetherius_API/api_keys/key_openai.txt')
api_key = key_path.strip()  # Ensure no leading/trailing whitespace

# Function to encode the image to base64
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def gpt_vision(query, image_path):
    try:
        base64_image = encode_image_to_base64(image_path)
        prompt = "You are a sub-module for an Ai agent system. Your task is to act as the eyes for the system. Ensure you give detailed and verbose descriptions of what you see so the other agents can understand. Try and keep your description within paragraph length."
        sub_prompt = " "
        if len(query) > 2:
            sub_prompt = f"\nPlease consider the user's inquiry in your response, tailoring your description to it.\nUSER INQUIRY: {query}"
        
        headers = {
          "Content-Type": "application/json",
          "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
          "model": "gpt-4-vision-preview",
          "messages": [
            {
              "role": "user",
              "content": [
                {"type": "text", "text": f"{prompt} {sub_prompt}"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
              ]
            }
          ],
          "max_tokens": 500
        }
        
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response_json = response.json()
        try:
            response_content = response_json['choices'][0]['message']['content']
        except KeyError:
            response_content = "Error processing the image. Please check the image format and try again."
        
        if len(query) < 1:
            response_content = f"The user has sent an image to you. Here is a description of the image:\n{response_content}"
        
        return response_content

    except Exception as e:
        print(e)
        response_content = "Error with Vision Module"
        return response_content
