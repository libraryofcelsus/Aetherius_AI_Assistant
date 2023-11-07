import sounddevice as sd
import numpy as np
import wavio

# Parameters
RATE = 44100    # samples per second
CHANNELS = 2    # number of channels (1: mono, 2: stereo)
DURATION = 30   # duration in seconds
FILENAME = "audio.wav"

def record_audio():
    print("Press Enter to start recording...")
    input()  # Wait for Enter press

    print(f"Recording for {DURATION} seconds...")
    audio_data = sd.rec(int(DURATION * RATE), samplerate=RATE, channels=CHANNELS, dtype=np.int16)
    sd.wait()  # Wait until recording is finished
    print("Recording complete.")

    print(f"Saving to {FILENAME}...")
    wavio.write(FILENAME, audio_data, RATE)
    print(f"{FILENAME} saved successfully!")

if __name__ == "__main__":
    record_audio()