import torch
import pyaudio
import wave
from TTS.api import TTS
import numpy as np
import re
import traceback

# Function to play audio
def play_audio(filename):
    # Set up the audio stream
    p = pyaudio.PyAudio()

    # Open the audio file
    wf = wave.open(filename, 'rb')

    # Create a PyAudio stream
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    # Read and play audio chunks
    chunk_size = 1024
    audio_chunk = wf.readframes(chunk_size)

    while len(audio_chunk) > 0:
        stream.write(audio_chunk)
        audio_chunk = wf.readframes(chunk_size)

    # Close the stream
    stream.stop_stream()
    stream.close()

    # Close PyAudio
    p.terminate()


def number_to_words(n):
    under_20 = ['Zero', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen']
    tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety', 'Hundred']
    above_1000 = {100: 'Hundred', 10**3: 'Thousand', 10**6: 'Million', 10**9: 'Billion'}
    
    if n < 20:
        return under_20[n]
    elif n < 100:
        return tens[n // 10] + ('' if n % 10 == 0 else ' ' + under_20[n % 10])
    else:
        max_key = max([key for key in above_1000.keys() if key <= n])
        return number_to_words(n // max_key) + ' ' + above_1000[max_key] + ('' if n % max_key == 0 else ' ' + number_to_words(n % max_key))

def TTS_Generation(query):
    try:
        # Remove emotes surrounded by asterisks from the query
        cleaned_query = re.sub(r'\*.*?\*', '', query)

        # Replace numbers with words
        numbers = re.findall(r'\b\d+\b', cleaned_query)
        for number in numbers:
            word = number_to_words(int(number))
            cleaned_query = cleaned_query.replace(number, word, 1)

        # Get device
        device = "cuda" if torch.cuda.is_available() else "cpu"

        # List available 🐸TTS models and choose the first one
    #    model_name = TTS().list_models()[0]

        # Init TTS
      #  tts = TTS(model_name).to(device)

        # Initialize TTS with the target model name
        tts = TTS(model_name="tts_models/multilingual/multi-dataset/your_tts", progress_bar=True).to(device)

        # Run TTS with cleaned query
        tts.tts_to_file(cleaned_query, speaker_wav="./Aetherius_API/Cloning/audio.wav", language="en", file_path="output.wav")

        # Play the audio
        play_audio("output.wav")
    except Exception as e:
        print(e)
        traceback.print_exc()