import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

DATASET_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../datasets/ai4i2020.csv"))
MODEL_OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../models"))

def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.replace('\ufeff', '').strip() for c in df.columns]
    return df

def train_anomaly_detection():
    print("=" * 70)
    print("Starting NexPharmAI Machine Anomaly Detection Training Pipeline")
    print("=" * 70)
    
    os.makedirs(MODEL_OUTPUT_DIR, exist_ok=True)
    
    df = pd.read_csv(DATASET_PATH)
    df = clean_column_names(df)
    
    # Train strictly on normal operating data to establish healthy behavioral baseline
    normal_df = df[df["Machine failure"] == 0].copy()
    print(f"Normal operating baseline records: {len(normal_df)}")
    
    features = [
        "Air temperature [K]",
        "Process temperature [K]",
        "Rotational speed [rpm]",
        "Torque [Nm]",
        "Tool wear [min]"
    ]
    
    X = normal_df[features].values
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    joblib.dump(scaler, os.path.join(MODEL_OUTPUT_DIR, "anomaly_scaler.joblib"))
    
    # Isolation Forest Model
    # Contamination set to 0.04 (approx expected subtle mechanical drift rate)
    iso_forest = IsolationForest(
        n_estimators=150,
        contamination=0.04,
        max_samples="auto",
        random_state=42
    )
    iso_forest.fit(X_scaled)
    
    # Save model
    model_path = os.path.join(MODEL_OUTPUT_DIR, "machine_anomaly_isolation_forest.joblib")
    joblib.dump(iso_forest, model_path)
    
    # Also save with .pkl naming as requested in specifications
    pkl_path = os.path.join(MODEL_OUTPUT_DIR, "machine_anomaly_isolation_forest.pkl")
    joblib.dump(iso_forest, pkl_path)
    
    # Compute baseline score statistics for severity thresholding
    scores = -iso_forest.score_samples(X_scaled)
    p50 = float(np.percentile(scores, 50))
    p80 = float(np.percentile(scores, 80))
    p95 = float(np.percentile(scores, 95))
    p99 = float(np.percentile(scores, 99))
    
    metadata = {
        "model_name": "Isolation Forest",
        "model_type": "Unsupervised Anomaly Detection",
        "version": "1.0.0",
        "features": features,
        "n_estimators": 150,
        "contamination": 0.04,
        "thresholds": {
            "NORMAL_MAX": p50,
            "LOW_MAX": p80,
            "MEDIUM_MAX": p95,
            "HIGH_MAX": p99
        },
        "score_percentiles": {
            "p50": round(p50, 4),
            "p80": round(p80, 4),
            "p95": round(p95, 4),
            "p99": round(p99, 4)
        },
        "trained_date": pd.Timestamp.now().isoformat()
    }
    
    with open(os.path.join(MODEL_OUTPUT_DIR, "anomaly_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)
        
    print(f"Anomaly detection model and metadata successfully saved to: {MODEL_OUTPUT_DIR}")
    print(f"Baseline thresholds: {metadata['thresholds']}")
    return metadata

if __name__ == "__main__":
    train_anomaly_detection()
