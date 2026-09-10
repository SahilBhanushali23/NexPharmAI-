from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.quality import QualityPrediction
from app.models.production import ProductionBatch
from app.models.alert import Alert
from app.schemas.quality import QualityPredictInput
from app.schemas.alert import AlertCreate
from app.services.alert import AlertService
from app.utils.logger import logger

class BatchQualityService:
    @staticmethod
    def predict_batch_quality(db: Session, input_data: QualityPredictInput) -> QualityPrediction:
        batch = db.query(ProductionBatch).filter(
            (ProductionBatch.id == input_data.batch_id) | (ProductionBatch.batch_number == input_data.batch_id)
        ).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")

        # Empirical pharmaceutical process engineering quality scoring model
        # Target ideal operating envelope:
        # Temp: 22-25 C, Pressure: 1.0-1.2 bar, pH: 6.8-7.2, Humidity: 40-50%, Mixing: 300 rpm, 45 min
        score = 100.0
        
        # Temperature deviation
        if input_data.temperature < 20.0 or input_data.temperature > 28.0:
            score -= abs(input_data.temperature - 24.0) * 2.5

        # Pressure deviation
        if input_data.pressure < 0.9 or input_data.pressure > 1.5:
            score -= abs(input_data.pressure - 1.0) * 15.0

        # pH critical deviation
        if input_data.ph < 6.5 or input_data.ph > 7.5:
            score -= abs(input_data.ph - 7.0) * 18.0

        # Humidity deviation
        if input_data.humidity > 60.0 or input_data.humidity < 35.0:
            score -= abs(input_data.humidity - 45.0) * 0.8

        score = max(0.0, min(100.0, round(score, 1)))
        pass_prob = round(score / 100.0, 4)

        if score >= 85.0:
            quality_risk = "LOW"
            status = "PASS"
        elif score >= 65.0:
            quality_risk = "MEDIUM"
            status = "PENDING_REVIEW"
        else:
            quality_risk = "HIGH"
            status = "REJECT"

        record = QualityPrediction(
            batch_id=batch.id,
            temperature=input_data.temperature,
            pressure=input_data.pressure,
            ph=input_data.ph,
            humidity=input_data.humidity,
            mixing_speed=input_data.mixing_speed,
            mixing_time=input_data.mixing_time,
            process_features=input_data.process_features,
            quality_score=score,
            pass_probability=pass_prob,
            quality_risk=quality_risk,
            status=status,
            created_at=datetime.now(timezone.utc)
        )
        db.add(record)
        
        # If quality risk is HIGH, update batch status to QUARANTINED and create alert
        if status == "REJECT":
            batch.status = "QUARANTINED"
            AlertService.create_alert(db, AlertCreate(
                alert_type="QUALITY_RISK",
                severity="HIGH",
                title=f"Quality Alert: Batch {batch.batch_number} Quarantined",
                message=f"Predicted quality score ({score}/100) dropped below release threshold. pH={input_data.ph}, Temp={input_data.temperature}C."
            ))

        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_quality_predictions(db: Session, batch_id: str = None) -> list[QualityPrediction]:
        query = db.query(QualityPrediction)
        if batch_id:
            batch = db.query(ProductionBatch).filter(
                (ProductionBatch.id == batch_id) | (ProductionBatch.batch_number == batch_id)
            ).first()
            if batch:
                query = query.filter(QualityPrediction.batch_id == batch.id)
        return query.order_by(QualityPrediction.created_at.desc()).all()
