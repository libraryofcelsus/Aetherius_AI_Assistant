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
from queue import Queue
import threading
import time
from time import time, sleep
from pydub.playback import play as pydub_play
from pydub import AudioSegment
import re


preload_models()

# Audio play queue
audio_queue = Queue()

def play_audio(audio_data):
    pydub_play(audio_data)

# Function to manage audio playback
def audio_player():
    while True:
        if not audio_queue.empty():
            audio_data = audio_queue.get()
            if audio_data == "STOP":
                break
            play_audio(audio_data)
        else:
            # Sleep for a short interval before checking the queue again
            sleep(0.05)
            
def numpy_array_to_audio_segment(audio_array, sample_rate):
    audio_segment = AudioSegment(
        audio_array.tobytes(), 
        frame_rate=sample_rate,
        sample_width=audio_array.dtype.itemsize, 
        channels=1
    )
    return audio_segment

# Main TTS Generation function
def TTS_Generation(query):
    try:
        # Break text into sentences
        sentences = re.split(r'(?<=[.!?])\s+', query)
        three_sentence_groups = [' '.join(sentences[i:i+3]) for i in range(0, len(sentences), 3)]
        
        for three_sentence_group in three_sentence_groups:
            # Generate audio for each group of three sentences
            audio_array = generate_audio(three_sentence_group, history_prompt="v2/en_speaker_3")
            audio_segment = numpy_array_to_audio_segment(audio_array, SAMPLE_RATE)
            
            # Add generated audio to the queue
            audio_queue.put(audio_segment)

    except Exception as e:
        print(e)

# Start the audio player thread once and let it run indefinitely
audio_thread = threading.Thread(target=audio_player)
audio_thread.start()


