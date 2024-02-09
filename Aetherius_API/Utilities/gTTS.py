import os
import pydub
from pydub.playback import play as pydub_play
from gtts import gTTS
import traceback

def play(audio_segment):
    pydub_play(audio_segment)
    
def TTS_Generation(query):    
    try:
        tts = gTTS(query)
        # TTS save to file in .mp3 format
        filename = "audio.mp3"  # Specify .mp3 extension
        tts.save(filename)
        # TTS repeats chatGPT response  
        sound = pydub.AudioSegment.from_file(filename, format="mp3")
        octaves = 0.08
        new_sample_rate = int(sound.frame_rate * (1.9 ** octaves))
        sound2 = sound._spawn(sound.raw_data, overrides={'frame_rate': new_sample_rate})
        sound2 = sound2.set_frame_rate(44100)
        play(sound2)
        os.remove(filename)  # Ensure this file actually got created before attempting to remove
    except Exception as e:
        print(e)
        traceback.print_exc()