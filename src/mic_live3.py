import time
import joblib
import librosa
import numpy as np
import sounddevice as sd
from telegram_alert import send_telegram_alert
from dotenv import load_dotenv
import os

load_dotenv()

MODEL_PATH = "models/audio_model.pkl"
CLASSES = ["ambiente", "motor_objetivo"]

SAMPLE_RATE = 16000
DURATION = 2

CONFIDENCE_THRESHOLD = 0.56
COOLDOWN_SECONDS = 20

last_alert_time = 0

def extract_features(audio, sr):
    mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
    mfcc_mean = np.mean(mfcc.T, axis=0)

    zcr = np.mean(librosa.feature.zero_crossing_rate(audio))
    spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=audio, sr=sr))
    rms = np.mean(librosa.feature.rms(y=audio))

    features = np.hstack([mfcc_mean, zcr, spectral_centroid, rms])
    return features

def main():
    global last_alert_time

    device_id = os.getenv("DEVICE_ID", "NODE-001")

    print("🔄 Loading model...")
    model = joblib.load(MODEL_PATH)

    print("🎤 Listening... Press Ctrl+C to stop.")

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

            # 🔥 LÓGICA DE ALERTA
            if predicted_class == "motor_objetivo" and confidence >= CONFIDENCE_THRESHOLD:

                now = time.time()

                if now - last_alert_time >= COOLDOWN_SECONDS:

                    message = (
                        f"🚨 ACOUSTIC ALERT\n"
                        f"Device: {device_id}\n"
                        f"Class: {predicted_class}\n"
                        f"Confidence: {confidence:.2f}"
                    )

                    sent = send_telegram_alert(message)

                    if sent:
                        print("📩 Telegram alert sent")
                        last_alert_time = now
                    else:
                        print("❌ Telegram failed")

                else:
                    print("⏳ Alert detected but cooldown active")

            time.sleep(0.5)

        except KeyboardInterrupt:
            print("\n🛑 System stopped safely.")
            break

if __name__ == "__main__":
    main()