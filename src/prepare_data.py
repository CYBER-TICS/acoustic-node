import os
import numpy as np
import librosa

CLASSES = ["ambiente", "motor_objetivo"]

def extract_features(file_path):
    y, sr = librosa.load(file_path, sr=16000)

    # Ignore very short audio
    if len(y) < sr * 1:
        raise ValueError("Audio too short")

    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    mfcc_mean = np.mean(mfcc.T, axis=0)

    zcr = np.mean(librosa.feature.zero_crossing_rate(y))
    spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
    rms = np.mean(librosa.feature.rms(y=y))

    features = np.hstack([mfcc_mean, zcr, spectral_centroid, rms])
    return features


def load_dataset(dataset_path):
    X = []
    y = []

    for label, class_name in enumerate(CLASSES):
        folder = os.path.join(dataset_path, class_name)

        if not os.path.exists(folder):
            print(f"Missing folder: {folder}")
            continue

        for file_name in os.listdir(folder):
            if file_name.lower().endswith(".wav"):
                file_path = os.path.join(folder, file_name)

                try:
                    features = extract_features(file_path)
                    X.append(features)
                    y.append(label)
                    print(f"Processed: {file_path}")

                except Exception as e:
                    print(f"Error processing {file_path}: {e}")

    return np.array(X), np.array(y)


if __name__ == "__main__":
    X, y = load_dataset("data/train")
    print("Dataset loaded")
    print("X shape:", X.shape)
    print("y shape:", y.shape)