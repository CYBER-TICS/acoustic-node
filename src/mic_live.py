import os
import time
import joblib
import librosa
import numpy as np
import sounddevice as sd
from dotenv import load_dotenv
from datetime import datetime
from api_client import send_event

load_dotenv()

MODEL_PATH = "models/audio_pipeline.pkl"
CLASSES = ["ambiente", "motor_objetivo"]

SAMPLE_RATE = 16000
DURATION = 2 # seconds per audio window

CONFIDENCE_THRESHOLD = 0.58
REQUIRED_CONSECUTIVE_DETECTIONS = 1
COOLDOWN_SECONDS = 20

last_alert_time = 0
detection_counter = 0


def extract_features(audio, sr):
    if len(audio) < sr * 1:
        raise ValueError("Audio too short")

    mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
    mfcc_mean = np.mean(mfcc.T, axis=0)

    zcr = np.mean(librosa.feature.zero_crossing_rate(audio))
    spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=audio, sr=sr))
    rms = np.mean(librosa.feature.rms(y=audio))

    features = np.hstack([mfcc_mean, zcr, spectral_centroid, rms])
    return features


def main():
    global last_alert_time
    global detection_counter

    device_id = os.getenv("DEVICE_ID", "NODE-001")

    print("Loading model from:", MODEL_PATH)

    if not os.path.exists(MODEL_PATH):
        print("Model file not found:", MODEL_PATH)
        return

    try:
        model = joblib.load(MODEL_PATH)
        print("Model loaded successfully.")
    except Exception as e:
        print("Error loading model:", e)
        return

    print("Listening... Press Ctrl+C to stop.")

    while True:
        try:
            audio = sd.rec(
                int(DURATION * SAMPLE_RATE),
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="float32"
            )
            sd.wait()

            audio = audio.flatten()

            features = extract_features(audio, SAMPLE_RATE).reshape(1, -1)

            pred = model.predict(features)[0]
            probs = model.predict_proba(features)[0]
            confidence = probs[pred]
            predicted_class = CLASSES[pred]

            print(f"\nDetected: {predicted_class} | Confidence: {confidence:.2f}")

            if predicted_class == "motor_objetivo" and confidence >= CONFIDENCE_THRESHOLD:
                detection_counter += 1
                print(
                    f"Detection counter: "
                    f"{detection_counter}/{REQUIRED_CONSECUTIVE_DETECTIONS}"
                )
            else:
                detection_counter = 0

            if detection_counter >= REQUIRED_CONSECUTIVE_DETECTIONS:
                now = time.time()

                if now - last_alert_time >= COOLDOWN_SECONDS:
                    local_time = datetime.now().astimezone()

                    payload = {
                        "node_id": device_id,
                        "timestamp": local_time.isoformat(),
                        "lat": 24.53027,
                        "lon": 54.99454,
                        "event_class": predicted_class,
                        "confidence": float(confidence),
                        "status": "alert"
                    }

                    sent = send_event(payload)

                    if sent:
                        print("API event sent")
                        last_alert_time = now
                    else:
                        print("API event failed")
                else:
                    print("Alert detected, but cooldown is active")

                detection_counter = 0

            time.sleep(0.5)

        except KeyboardInterrupt:
            print("\nSystem stopped safely.")
            break
        except Exception as e:
            print("Runtime error:", e)
            time.sleep(1)


if __name__ == "__main__":
    main()