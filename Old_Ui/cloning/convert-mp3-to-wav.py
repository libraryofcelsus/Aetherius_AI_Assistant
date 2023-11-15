from pydub import AudioSegment

def mp3_to_wav(mp3_file_path, wav_file_path):
    audio = AudioSegment.from_mp3(mp3_file_path)
    audio.export(wav_file_path, format="wav")

# Convert audio.mp3 to audio.wav
mp3_to_wav("audio.mp3", "audio.wav")