import sys
sys.path.insert(0, './scripts')
sys.path.insert(0, './config')
sys.path.insert(0, './config/Chatbot_Prompts')
sys.path.insert(0, './scripts/resources')
import os
import json
import time
from time import time, sleep
import datetime
from uuid import uuid4
import os
import subprocess
import whisper
import traceback
import torch



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
    datetime_obj = datetime.fromtimestamp(unix_time)
    datetime_str = datetime_obj.strftime("%A, %B %d, %Y at %I:%M%p %Z")
    return datetime_str
    
    
def is_integer(value):
    try:
        int(value)
        return True
    except ValueError:
        return False


def fail():
      #  print('')
    fail = "Not Needed"
    return fail
        
        
def Extract_Audio_From_Video(video_filename):
    try:
        # Check for CUDA
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        # Load both Whisper models
        model_stt = whisper.load_model("tiny").to(device)  # Move the model to the device

        # Define folders
        video_folder = './Upload/VIDEOS/Finished'
        audio_folder = './Upload/AUDIOS'
        os.makedirs(audio_folder, exist_ok=True)

        # Check if video file exists
        video_path = os.path.join(video_folder, video_filename)
        if not os.path.exists(video_path):
            print(f"Error: {video_path} does not exist.")
            return None, None

        # Extract Audio from Video
        audio_path = os.path.join(audio_folder, video_filename.split('.')[0] + '.mp3')
        command = [
            "ffmpeg",
            "-hwaccel", "cuda",  # hardware acceleration
            "-i", video_path,
            "-q:a", "0",
            "-map", "a",
            "-vn",
            audio_path
        ]
        subprocess.run(command)

        # Transcribe audio using the small model
        transcript_result = model_stt.transcribe(audio_path)

        if isinstance(transcript_result, dict):
            transcript_result = str(transcript_result)

        # Load audio and process it
        audio = whisper.load_audio(audio_path).to(device)
        audio = whisper.pad_or_trim(audio)

        # Make log-Mel spectrogram
        mel = whisper.log_mel_spectrogram(audio).to(device)

        # Detect the spoken language
        _, probs = model_stt.detect_language(mel)  # Assuming model_stt has the detect_language method
        detected_language = max(probs, key=probs.get)
        print(f"Detected language: {detected_language}")

        # Decode the audio
        options = whisper.DecodingOptions()
        decode_result = whisper.decode(model_stt, mel, options)

        if isinstance(decode_result, dict) and 'text' in decode_result:
            decode_result = decode_result['text']

        # Create the txt file
        txt_filename = video_filename.split('.')[0] + '.txt'
        txt_path = os.path.join(video_folder, txt_filename)

        with open(txt_path, 'w') as f:
            f.write("Transcript Result:\n")
            f.write(transcript_result)
            f.write("\n\nDecode Result:\n")
            f.write(decode_result)

        print(f"Text has been written to {txt_path}")

        return transcript_result, decode_result

    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        line_number = traceback.tb_lineno(exc_traceback)
        print(f"An error occurred: {e} at line {line_number}")
        traceback.print_exc()
        return None, None
