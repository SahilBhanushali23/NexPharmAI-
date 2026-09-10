import numpy as np
from datetime import datetime, timezone
from app.ai.model_loader import model_loader
from app.schemas.anomaly import AnomalyInput
from app.utils.logger import logger

class AnomalyService:
    @staticmethod
    def predict(input_data: AnomalyInput) -> dict:
        loader = model_loader
        features = [
            float(input_data.air_temperature),
            float(input_data.process_temperature),
            float(input_data.rotational_speed),
            float(input_data.torque),
            float(input_data.tool_wear)
        ]

        if loader.anomaly_model is None or loader.anomaly_scaler is None:
            # Fallback heuristic
            logger.warning("Anomaly model not loaded, using heuristic fallback")
            score = 0.40
            if input_data.rotational_speed > 2600 or input_data.rotational_speed < 1200: score += 0.25
            if input_data.torque > 65 or input_data.torque < 15: score += 0.25
            is_anomaly = 1 if score > 0.55 else 0
        else:
            X = np.array([features])
            X_scaled = loader.anomaly_scaler.transform(X)
            # Isolation forest decision_function: lower means more abnormal
            # Raw score_samples: -score_samples gives positive outlier metric
            raw_score = float(-loader.anomaly_model.score_samples(X_scaled)[0])
            pred = loader.anomaly_model.predict(X_scaled)[0] # -1 = anomaly, 1 = normal
            is_anomaly = 1 if pred == -1 else 0
            score = raw_score

        # Severity classification based on score thresholds
        thresholds = loader.anomaly_metadata.get("thresholds", {
            "NORMAL_MAX": 0.46,
            "LOW_MAX": 0.51,
            "MEDIUM_MAX": 0.58,
            "HIGH_MAX": 0.62
        })

        if score < thresholds.get("NORMAL_MAX", 0.46):
            severity = "NORMAL"
        elif score < thresholds.get("LOW_MAX", 0.51):
            severity = "LOW"
        elif score < thresholds.get("MEDIUM_MAX", 0.58):
            severity = "MEDIUM"
        elif score < thresholds.get("HIGH_MAX", 0.62):
            severity = "HIGH"
        else:
            severity = "CRITICAL"

        return {
            "anomaly_detected": is_anomaly,
            "anomaly_score": round(score, 4),
            "severity": severity,
            "timestamp": datetime.now(timezone.utc)
        }
