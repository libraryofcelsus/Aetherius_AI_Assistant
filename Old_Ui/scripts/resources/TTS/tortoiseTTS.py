import sys
import os
import datetime
from uuid import uuid4
import requests


import IPython

from tortoise.api import TextToSpeech
from tortoise.utils.audio import load_audio, load_voice, load_voices


tts = TextToSpeech()

text = "AHHHHHHHHHHHHHHH"

# ["ultra_fast", "fast", "standard", "high_quality"]
preset = "ultra_fast" 

voice = 'train_dotrice'


voice_samples, conditioning_latents = load_voice(voice)
gen = tts.tts_with_preset(text, voice_samples=voice_samples, conditioning_latents=conditioning_latents, 
                          preset=preset)
torchaudio.save('generated.wav', gen.squeeze(0).cpu(), 24000)
IPython.display.Audio('generated.wav')
    
    
    
# gen = tts.tts_with_preset(text, voice_samples=None, conditioning_latents=None, preset=preset)
# torchaudio.save('generated.wav', gen.squeeze(0).cpu(), 24000)
# IPython.display.Audio('generated.wav')