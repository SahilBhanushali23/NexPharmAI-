import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from imblearn.over_sampling import SMOTE

# Try importing CatBoost if available
try:
    from catboost import CatBoostClassifier
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False

DATASET_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../datasets/ai4i2020.csv"))
MODEL_OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../models"))

def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    # Handle possible UTF-8 BOM
    df.columns = [c.replace('\ufeff', '').strip() for c in df.columns]
    return df

def train_predictive_maintenance():
    print("=" * 70)
    print("Starting NexPharmAI Predictive Maintenance Model Training Pipeline")
    print("=" * 70)
    
    os.makedirs(MODEL_OUTPUT_DIR, exist_ok=True)
    
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(f"Dataset not found at: {DATASET_PATH}")
        
    print(f"Loading dataset: {DATASET_PATH}")
    df = pd.read_csv(DATASET_PATH)
    df = clean_column_names(df)
    
    print(f"Dataset shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    
    # 1. Target & Features separation
    target_col = "Machine failure"
    drop_cols = ["UDI", "Product ID", "Machine failure", "TWF", "HDF", "PWF", "OSF", "RNF"]
    feature_cols = [c for c in df.columns if c not in drop_cols]
    
    print(f"Selected Features: {feature_cols}")
    print(f"Target: {target_col}")
    
    X = df[feature_cols].copy()
    y = df[target_col].copy()
    
    # 2. Check Class Balance
    failure_counts = y.value_counts().to_dict()
    print(f"Target distribution: Normal (0) = {failure_counts.get(0, 0)}, Failure (1) = {failure_counts.get(1, 0)}")
    failure_rate = (failure_counts.get(1, 0) / len(y)) * 100
    print(f"Empirical Failure Rate: {failure_rate:.2f}% (High Class Imbalance)")
    
    # 3. Categorical vs Numerical split
    categorical_features = ["Type"]
    numerical_features = [c for c in feature_cols if c not in categorical_features]
    
    # Preprocessor
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numerical_features),
            ("cat", OneHotEncoder(drop="first", sparse_output=False), categorical_features)
        ]
    )
    
    # 4. Stratified Train/Test Split (80/20, random_state=42)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, stratify=y, random_state=42
    )
    print(f"Train samples: {len(X_train)} | Test samples: {len(X_test)}")
    
    # Fit preprocessor on training data
    X_train_proc = preprocessor.fit_transform(X_train)
    X_test_proc = preprocessor.transform(X_test)
    
    # Save the fitted preprocessor
    joblib.dump(preprocessor, os.path.join(MODEL_OUTPUT_DIR, "preprocessor.joblib"))
    print("Saved feature preprocessor to preprocessor.joblib")
    
    # 5. Handle class imbalance using SMOTE on training set
    print("Applying SMOTE on training set...")
    smote = SMOTE(random_state=42)
    X_train_res, y_train_res = smote.fit_resample(X_train_proc, y_train)
    print(f"Resampled training set shape: {X_train_res.shape}, Class 1 count: {sum(y_train_res == 1)}")
    
    # 6. Candidate Models
    models = {
        "XGBoost": XGBClassifier(
            n_estimators=150,
            max_depth=5,
            learning_rate=0.08,
            random_state=42,
            eval_metric="logloss"
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=150,
            max_depth=8,
            random_state=42,
            class_weight="balanced"
        ),
        "LightGBM": LGBMClassifier(
            n_estimators=150,
            max_depth=5,
            learning_rate=0.08,
            random_state=42,
            verbose=-1
        ),
        "Logistic Regression": LogisticRegression(
            max_iter=1000,
            random_state=42
        )
    }
    
    if CATBOOST_AVAILABLE:
        models["CatBoost"] = CatBoostClassifier(
            iterations=150,
            depth=5,
            learning_rate=0.08,
            random_seed=42,
            verbose=0
        )
        
    benchmark_results = {}
    best_model_name = None
    best_f1 = -1.0
    trained_models = {}
    
    print("\n--- Model Benchmark Evaluation ---")
    for name, model in models.items():
        print(f"\nTraining {name}...")
        model.fit(X_train_res, y_train_res)
        trained_models[name] = model
        
        y_pred = model.predict(X_test_proc)
        if hasattr(model, "predict_proba"):
            y_proba = model.predict_proba(X_test_proc)[:, 1]
            roc_auc = float(roc_auc_score(y_test, y_proba))
        else:
            roc_auc = 0.0
            
        acc = float(accuracy_score(y_test, y_pred))
        prec = float(precision_score(y_test, y_pred, zero_division=0))
        rec = float(recall_score(y_test, y_pred, zero_division=0))
        f1 = float(f1_score(y_test, y_pred, zero_division=0))
        cm = confusion_matrix(y_test, y_pred).tolist()
        
        benchmark_results[name] = {
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "failure_recall": round(rec, 4),
            "failure_f1": round(f1, 4),
            "roc_auc": round(roc_auc, 4),
            "confusion_matrix": cm
        }
        
        print(f"Results for {name}:")
        print(f"  Accuracy:       {acc:.4f}")
        print(f"  Precision:      {prec:.4f}")
        print(f"  Failure Recall: {rec:.4f}")
        print(f"  Failure F1:     {f1:.4f}")
        print(f"  ROC-AUC:        {roc_auc:.4f}")
        print(f"  Confusion Matrix: {cm}")
        
        # Primary selection metric for high class-imbalance failure detection: Failure F1 score
        if f1 > best_f1:
            best_f1 = f1
            best_model_name = name
            
    print("\n" + "=" * 70)
    print(f"PRODUCTION MODEL SELECTED: {best_model_name} (Failure F1: {best_f1:.4f})")
    print("=" * 70)
    
    # 7. Save Models and Metadata
    production_model = trained_models[best_model_name]
    joblib.dump(production_model, os.path.join(MODEL_OUTPUT_DIR, "predictive_maintenance_model.joblib"))
    joblib.dump(trained_models["XGBoost"], os.path.join(MODEL_OUTPUT_DIR, "xgboost_model.joblib"))
    
    metadata = {
        "model_name": best_model_name,
        "model_type": "Binary Machine Failure Classifier",
        "version": "1.0.0",
        "dataset": "AI4I 2020 Predictive Maintenance Dataset (UCI)",
        "features": feature_cols,
        "numerical_features": numerical_features,
        "categorical_features": categorical_features,
        "benchmark_comparison": benchmark_results,
        "selection_rationale": f"{best_model_name} achieved the optimal balance of Failure Recall ({benchmark_results[best_model_name]['failure_recall']}) and Failure F1 ({benchmark_results[best_model_name]['failure_f1']}) under SMOTE oversampling, maximizing undetected breakdown prevention.",
        "trained_date": pd.Timestamp.now().isoformat()
    }
    
    with open(os.path.join(MODEL_OUTPUT_DIR, "predictive_maintenance_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)
        
    print(f"Model and metadata successfully saved to: {MODEL_OUTPUT_DIR}")
    return metadata

if __name__ == "__main__":
    train_predictive_maintenance()
