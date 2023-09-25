import sys
import os
import datetime
from uuid import uuid4
import requests
from basic_functions import *
from gtts import gTTS
from elevenlabs import clone, generate, play, set_api_key

    
api_key = open_file('api_keys/key_eleven_labs.txt')

set_api_key(api_key)

voice_id = 'Matthew'
    
def TTS_Generation(query):
    try:
        audio = generate(
            text=query,
            voice=voice_id,
            model='eleven_multilingual_v2',
        )

        play(audio)

    except Exception as e:
        print(e)