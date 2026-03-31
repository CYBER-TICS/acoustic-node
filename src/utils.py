import os

def list_wav_files(folder):
    return [f for f in os.listdir(folder) if f.lower().endswith(".wav")]