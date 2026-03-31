import os
import joblib

MODEL_PATH = "models/audio_pipeline.pkl"
CLASSES = ["ambiente", "motor_objetivo"]

from prepare_data import extract_features

def main():
    if not os.path.exists(MODEL_PATH):
        print("Model not found. Train first.")
        return

    model = joblib.load(MODEL_PATH)

    folder = "data/predict"

    if not os.path.exists(folder):
        print("Missing data/predict folder")
        return

    files = [f for f in os.listdir(folder) if f.lower().endswith(".wav")]

    if not files:
        print("No .wav files found in data/predict")
        return

    for file_name in files:
        file_path = os.path.join(folder, file_name)

        try:
            features = extract_features(file_path).reshape(1, -1)

            pred = model.predict(features)[0]
            probs = model.predict_proba(features)[0]
            confidence = probs[pred]

            predicted_class = CLASSES[pred]

            print(f"\nFile: {file_name}")
            print(f"Predicted: {predicted_class}")
            print(f"Confidence: {confidence:.2f}")

            if predicted_class == "motor_objetivo":
                print("⚠️ ALERT: target sound detected")
            else:
                print("OK: ambient sound")

        except Exception as e:
            print(f"Error processing {file_name}: {e}")


if __name__ == "__main__":
    main()