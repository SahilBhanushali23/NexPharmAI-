from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.machine import MachineHealthHistory, Machine
from app.utils.logger import logger

class HealthScoringEngine:
    @staticmethod
    def calculate_health_score(
        failure_prob: float,
        anomaly_detected: int,
        anomaly_score: float,
        air_temp: float,
        proc_temp: float,
        torque: float,
        tool_wear: float,
        recent_scores: list[float] = None
    ) -> tuple[float, str]:
        """
        Calculates composite machine health (0-100) and operational category.
        """
        # Baseline ideal score
        base_score = 100.0

        # 1. Failure Probability penalty (up to 55 points)
        # As failure probability increases, health drops sharply
        failure_penalty = min(55.0, failure_prob * 65.0)
        base_score -= failure_penalty

        # 2. Anomaly status and score penalty (up to 25 points)
        if anomaly_detected == 1:
            base_score -= 10.0
        # normalized anomaly score penalty
        if anomaly_score > 0.50:
            anomaly_penalty = min(15.0, (anomaly_score - 0.50) * 80.0)
            base_score -= anomaly_penalty

        # 3. Tool wear penalty (up to 12 points)
        # Normal tool wear reaches 200+ min
        if tool_wear > 150:
            wear_penalty = min(12.0, (tool_wear - 150) * 0.15)
            base_score -= wear_penalty

        # 4. Thermal stress penalty (up to 8 points)
        temp_diff = proc_temp - air_temp
        if temp_diff < 8.6 or temp_diff > 12.0:
            base_score -= 5.0
        if proc_temp > 311.0: # ~38 C
            base_score -= 3.0

        # 5. Torque overload penalty
        if torque > 60.0:
            base_score -= min(10.0, (torque - 60.0) * 0.5)

        # 6. Trend smoothing with recent scores
        if recent_scores and len(recent_scores) > 0:
            avg_recent = sum(recent_scores[:3]) / len(recent_scores[:3])
            final_score = (base_score * 0.70) + (avg_recent * 0.30)
        else:
            final_score = base_score

        # Bound score between 0.0 and 100.0
        final_score = max(0.0, min(100.0, round(final_score, 1)))

        # Categorize
        if final_score >= 90.0:
            category = "EXCELLENT"
        elif final_score >= 75.0:
            category = "GOOD"
        elif final_score >= 50.0:
            category = "WARNING"
        else:
            category = "CRITICAL"

        return final_score, category

    @staticmethod
    def record_health(
        db: Session,
        machine_id: str,
        score: float,
        category: str,
        failure_prob: float,
        anomaly_score: float
    ) -> MachineHealthHistory:
        record = MachineHealthHistory(
            machine_id=machine_id,
            score=score,
            category=category,
            failure_probability=failure_prob,
            anomaly_score=anomaly_score,
            recorded_at=datetime.now(timezone.utc)
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
