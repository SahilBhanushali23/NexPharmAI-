import os
import json
import joblib
import pandas as pd
import numpy as np
from app.core.config import settings
from app.utils.logger import logger

class ModelLoader:
    _instance = None

    def __init__(self):
        self.models_dir = settings.MODEL_PATH
        self.preprocessor = None
        self.pm_model = None
        self.pm_metadata = {}
        self.anomaly_model = None
        self.anomaly_scaler = None
        self.anomaly_metadata = {}
        self._load_models()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_models(self):
        try:
            prep_path = os.path.join(self.models_dir, "preprocessor.joblib")
            pm_path = os.path.join(self.models_dir, "predictive_maintenance_model.joblib")
            pm_meta_path = os.path.join(self.models_dir, "predictive_maintenance_metadata.json")

            if os.path.exists(prep_path) and os.path.exists(pm_path):
                self.preprocessor = joblib.load(prep_path)
                self.pm_model = joblib.load(pm_path)
                if os.path.exists(pm_meta_path):
                    with open(pm_meta_path, "r") as f:
                        self.pm_metadata = json.load(f)
                logger.info(f"Loaded Predictive Maintenance model ({self.pm_metadata.get('model_name', 'Default')})")
            else:
                logger.warning(f"Predictive maintenance model files not found in {self.models_dir}")

            iso_path = os.path.join(self.models_dir, "machine_anomaly_isolation_forest.joblib")
            scaler_path = os.path.join(self.models_dir, "anomaly_scaler.joblib")
            iso_meta_path = os.path.join(self.models_dir, "anomaly_metadata.json")

            if os.path.exists(iso_path) and os.path.exists(scaler_path):
                self.anomaly_model = joblib.load(iso_path)
                self.anomaly_scaler = joblib.load(scaler_path)
                if os.path.exists(iso_meta_path):
                    with open(iso_meta_path, "r") as f:
                        self.anomaly_metadata = json.load(f)
                logger.info("Loaded Isolation Forest anomaly detection model")
            else:
                logger.warning(f"Anomaly model files not found in {self.models_dir}")

        except Exception as e:
            logger.error(f"Error loading ML models: {e}")

model_loader = ModelLoader.get_instance()
