import os
import joblib
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from sklearn.model_selection import cross_val_score
from prepare_data import load_dataset

MODEL_PATH = "models/audio_pipeline.pkl2"

def main():
    print("Loading training dataset...")
    X_train, y_train = load_dataset("data/train")

    print("\nLoading test dataset...")
    X_test, y_test = load_dataset("data/test")

    if len(X_train) == 0 or len(X_test) == 0:
        print("Dataset is empty. Check your folders.")
        return

    print("\nBuilding pipeline...")

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("model", RandomForestClassifier(
            n_estimators=300,
            max_depth=12,
            min_samples_split=4,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        ))
    ])

    print("Training model...")
    pipeline.fit(X_train, y_train)

    print("\nRunning cross-validation on training data...")
    cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring="accuracy")
    print("Cross-validation scores:", np.round(cv_scores, 4))
    print("Cross-validation mean:", np.round(cv_scores.mean(), 4))

    print("\nEvaluating model on test set...")
    y_pred = pipeline.predict(X_test)

    print("\nAccuracy:", accuracy_score(y_test, y_pred))

    print("\nClassification Report:")
    print(classification_report(
        y_test,
        y_pred,
        target_names=["ambiente", "motor_objetivo"]
    ))

    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    os.makedirs("models", exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)

    print(f"\nModel saved at: {MODEL_PATH}")


if __name__ == "__main__":
    main()