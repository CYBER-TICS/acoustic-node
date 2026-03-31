import os
import time
import subprocess
from datetime import datetime, timezone

import joblib
import librosa
import numpy as np

from gps_reader import get_gps_data
from api_client import send_event

# =========================
# CONFIG
# =========================
MODEL_PATH = "/home/buma/acoustic-node/audio_pipeline.pkl"

AUDIO_DEVICE = "hw:3,0"
CAPTURE_SAMPLE_RATE = 48000
CHANNELS = 1
CHUNK_DURATION_SECONDS = 2
TEMP_WAV_PATH = "/home/buma/acoustic-node/temp.wav"

TARGET_SAMPLE_RATE = 16000
N_MFCC = 20

CLASS_MAP = {
    0: "ambiente",
    1: "motor_objetivo"
}
TARGET_CLASS_NAME = "motor_objetivo"

CONFIDENCE_THRESHOLD = 0.80
COOLDOWN_SECONDS = 8
HEARTBEAT_INTERVAL_SECONDS = 120

NODE_ID = "acoustic-node-001"


# =========================
# HELPERS
# =========================
def record_audio(output_path: str) -> bool:
    cmd = [
        "arecord",
        "-D", AUDIO_DEVICE,
        "-f", "S16_LE",
        "-r", str(CAPTURE_SAMPLE_RATE),
        "-c", str(CHANNELS),
        "-d", str(CHUNK_DURATION_SECONDS),
        output_path
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        check=False
    )

    if result.returncode != 0:
        print("arecord failed:", result.stderr.strip())
        return False

    return os.path.exists(output_path) and os.path.getsize(output_path) > 44


def extract_features(file_path: str) -> np.ndarray:
    y, sr = librosa.load(file_path, sr=TARGET_SAMPLE_RATE, mono=True)

    if y is None or len(y) < TARGET_SAMPLE_RATE * 0.5:
        raise ValueError("Audio too short or invalid")

    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=N_MFCC)
    mfcc_mean = np.mean(mfcc.T, axis=0)

    zcr = np.mean(librosa.feature.zero_crossing_rate(y))
    spectral