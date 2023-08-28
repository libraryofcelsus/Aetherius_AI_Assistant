import sys
import os
import datetime
from uuid import uuid4
import requests
from basic_functions import *
from gtts import gTTS
from bark import SAMPLE_RATE, generate_audio, preload_models
from scipy.io.wavfile import write as write_wav
from IPython.display import Audio

os.environ["CUDA_VISIBLE_DEVICES"] = "0"

preload_models()

    
def TTS_Generation(query):
    try:
    
        text_prompt = query
        audio_array = generate_audio(text_prompt, history_prompt="v2/en_speaker_1")
        write_wav("bark_generation.wav", SAMPLE_RATE, audio_array)
        Audio(audio_array, rate=SAMPLE_RATE)

    except Exception as e:
        print(e)