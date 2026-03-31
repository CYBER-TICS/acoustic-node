import os
import time
import subprocess
from datetime import datetime, timezone

import joblib
import librosa
import numpy as np

from gps_reader import get_gps_data
from api_client import send_event

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

    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=N_MFCC)
    mfcc_mean = np.mean(mfcc.T, axis=0)

    zcr = np.mean(librosa.feature.zero_crossing_rate(y))
    spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
    rms = np.mean(librosa.feature.rms(y=y))

    features = np.hstack([mfcc_mean, zcr, spectral_centroid, rms])
    return features


def get_predicted_label(prediction_value):
    try:
        return CLASS_MAP.get(int(prediction_value), str(prediction_value))
    except Exception:
        return str(prediction_value)


def send_heartbeat():
    lat, lon = get_gps_data(timeout_seconds=2)

    payload = {
        "node_id": NODE_ID,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "lat": lat,
        "lon": lon,
        "event_class": "HEARTBEAT",
        "confidence": 1.0,
        "status": "online"
    }

    ok = send_event(payload)
    print("Heartbeat sent:", ok)


def send_alert(confidence: float):
    lat, lon = get_gps_data(timeout_seconds=3)

    payload = {
        "node_id": NODE_ID,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "lat": lat,
        "lon": lon,
        "event_class": TARGET_CLASS_NAME,
        "confidence": float(confidence),
        "status": "alert"
    }

    ok = send_event(payload)
    print("Alert sent:", ok)


def main():
    print("Starting acoustic node...")
    model = joblib.load(MODEL_PATH)
    print("Model loaded")

    last_alert_time = 0.0
    last_heartbeat_time = 0.0

    while True:
        try:
            now = time.time()

            if now - last_heartbeat_time >= HEARTBEAT_INTERVAL_SECONDS:
                send_heartbeat()
                last_heartbeat_time = now

            ok = record_audio(TEMP_WAV_PATH)
            if not ok:
                time.sleep(1)
                continue

            features = extract_features(TEMP_WAV_PATH).reshape(1, -1)

            prediction = model.predict(features)[0]
            predicted_label = get_predicted_label(prediction)

            if hasattr(model, "predict_proba"):
                probs = model.predict_proba(features)[0]
                confidence = float(np.max(probs))
            else:
                confidence = 1.0

            print(f"Predicted: {predicted_label} | Confidence: {confidence:.2f}")

            if predicted_label == TARGET_CLASS_NAME and confidence >= CONFIDENCE_THRESHOLD:
                if now - last_alert_time >= COOLDOWN_SECONDS:
                    print("TARGET DETECTED")
                    send_alert(confidence)
                    last_alert_time = now

            time.sleep(0.3)

        except KeyboardInterrupt:
            print("Stopped by user")
            break

        except Exception as e:
            print("Runtime error:", e)
            time.sleep(1)


if __name__ == "__main__":
    main()