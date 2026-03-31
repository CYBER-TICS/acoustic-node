import os
import time
import subprocess
from datetime import datetime, timezone
from gps_reader import get_gps_data

import joblib
import librosa
import numpy as np
import requests

# =========================
# CONFIG
# =========================
MODEL_PATH = "/home/buma/acoustic-node/modelo.pkl"

# Micrófono USB detectado:
# > 1 GM303: USB Audio (hw:3,0), ALSA
AUDIO_DEVICE = "hw:3,0"

# Captura real del mic
CAPTURE_SAMPLE_RATE = 48000
CHANNELS = 1
CHUNK_DURATION_SECONDS = 2
TEMP_WAV_PATH = "/home/buma/acoustic-node/temp.wav"

# Procesamiento para el modelo
TARGET_SAMPLE_RATE = 16000
N_MFCC = 20   # si tu modelo fue entrenado con 20
# N_MFCC = 13 # usa esto si tu modelo fue entrenado con 13

# Clases del modelo
TARGET_CLASS_NAME = "motor_objetivo"

# Lógica de alertas
CONFIDENCE_THRESHOLD = 0.80
COOLDOWN_SECONDS = 8

# Server en tu PC
SERVER_URL = "http://10.44.149.139:8000/api/events"
API_KEY = "123456"

# Nodo y coordenadas temporales

NODE_ID = "acoustic-node-001"
lat, lon = get_gps_data()

payload = {
    "node_id": NODE_ID,
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "lat": lat if lat else 0,
    "lon": lon if lon else 0,
    "event_class": TARGET_CLASS_NAME,
    "confidence": float(confidence),
    "status": "alert"
}






# =========================
# HELPERS
# =========================
def record_audio(output_path: str) -> bool:
    """
    Graba un chunk de audio usando arecord.
    """
    cmd = [
        "arecord",
        "-D", AUDIO_DEVICE,
        "-f", "S16_LE",
        "-r", str(CAPTURE_SAMPLE_RATE),
        "-c", str(CHANNELS),
        "-d", str(CHUNK_DURATION_SECONDS),
        output_path
    ]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )

        if result.returncode != 0:
            print("❌ arecord failed:")
            print(result.stderr.strip())
            return False

        if not os.path.exists(output_path):
            print("❌ temp.wav was not created")
            return False

        if os.path.getsize(output_path) <= 44:
            print("❌ Recorded file is too small or empty")
            return False

        return True

    except Exception as e:
        print(f"❌ Exception while recording: {e}")
        return False


def extract_features(file_path: str) -> np.ndarray:
    """
    Carga el audio, lo re-muestrea a 16k, extrae MFCC + features básicas.
    Debe coincidir con la lógica con la que entrenaste el modelo.
    """
    y, sr = librosa.load(file_path, sr=TARGET_SAMPLE_RATE, mono=True)

    if y is None or len(y) < TARGET_SAMPLE_RATE * 0.5:
        raise ValueError("Audio too short or invalid")

    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=N_MFCC)
    mfcc_mean = np.mean(mfcc.T, axis=0)

    zcr = np.mean(librosa.feature.zero_crossing_rate(y))
    spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
    rms = np.mean(librosa.feature.rms(y=y))

    features = np.hstack([mfcc_mean, zcr, spectral_centroid, rms])
    return features


def send_alert(confidence: float) -> None:
    """
    Envía alerta al backend.
    """
    payload = {
        "node_id": NODE_ID,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "lat": LATITUDE,
        "lon": LONGITUDE,
        "event_class": TARGET_CLASS_NAME,
        "confidence": float(confidence),
        "status": "alert"
    }

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }

    try:
        response = requests.post(
            SERVER_URL,
            json=payload,
            headers=headers,
            timeout=5
        )

        print(f"📡 Alert sent: {response.status_code} {response.text}")

    except Exception as e:
        print(f"❌ Error sending alert: {e}")


def get_predicted_label(model, prediction_value):
    """
    Normaliza la salida del modelo.
    Si el modelo devuelve string, usa string.
    Si devuelve entero y tiene classes_, traduce con classes_.
    """
    if isinstance(prediction_value, str):
        return prediction_value

    if hasattr(model, "classes_"):
        try:
            return str(model.classes_[prediction_value])
        except Exception:
            pass

    return str(prediction_value)


# =========================
# MAIN
# =========================
def main():
    print("====================================")
    print(" Acoustic Node - Raspberry Live Mic ")
    print("====================================")
    print(f"Model: {MODEL_PATH}")
    print(f"Audio device: {AUDIO_DEVICE}")
    print(f"Server: {SERVER_URL}")
    print(f"Node ID: {NODE_ID}")
    print("Starting...")

    if not os.path.exists(MODEL_PATH):
        print(f"❌ Model file not found: {MODEL_PATH}")
        return

    try:
        model = joblib.load(MODEL_PATH)
        print("✅ Model loaded")
    except Exception as e:
        print(f"❌ Could not load model: {e}")
        return

    last_alert_time = 0.0

    while True:
        try:
            ok = record_audio(TEMP_WAV_PATH)
            if not ok:
                time.sleep(1)
                continue

            features = extract_features(TEMP_WAV_PATH).reshape(1, -1)

            prediction = model.predict(features)[0]
            predicted_label = get_predicted_label(model, prediction)

            confidence = 0.0
            if hasattr(model, "predict_proba"):
                probs = model.predict_proba(features)[0]
                confidence = float(np.max(probs))
            else:
                confidence = 1.0

            print(f"Predicted: {predicted_label} | Confidence: {confidence:.2f}")

            now = time.time()

            if predicted_label == TARGET_CLASS_NAME and confidence >= CONFIDENCE_THRESHOLD:
                if now - last_alert_time >= COOLDOWN_SECONDS:
                    print("🚨 TARGET DETECTED")
                    send_alert(confidence)
                    last_alert_time = now
                else:
                    remaining = COOLDOWN_SECONDS - (now - last_alert_time)
                    print(f"⏳ Cooldown active: {remaining:.1f}s remaining")

            time.sleep(0.3)

        except KeyboardInterrupt:
            print("\n🛑 Stopped by user")
            break

        except Exception as e:
            print(f"❌ Runtime error: {e}")
            time.sleep(1)


if __name__ == "__main__":
    main()