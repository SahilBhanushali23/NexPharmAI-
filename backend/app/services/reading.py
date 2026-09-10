from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.machine import (
    Machine,
    MachineReading,
    MachinePrediction,
    AnomalyPrediction,
    MachineHealthHistory
)
from app.schemas.reading import MachineReadingCreate
from app.schemas.predictive_maintenance import PMPredictionInput
from app.schemas.anomaly import AnomalyInput
from app.schemas.alert import AlertCreate
from app.services.predictive_maintenance import PredictiveMaintenanceService
from app.services.anomaly import AnomalyService
from app.services.health import HealthScoringEngine
from app.services.alert import AlertService
from app.utils.logger import logger

class ReadingPipelineService:
    @staticmethod
    def ingest_reading(db: Session, reading_in: MachineReadingCreate) -> dict:
        # Find machine
        machine = db.query(Machine).filter(
            (Machine.id == reading_in.machine_id) | (Machine.machine_id == reading_in.machine_id)
        ).first()
        if not machine:
            raise HTTPException(status_code=404, detail=f"Machine '{reading_in.machine_id}' not found.")

        timestamp = reading_in.timestamp or datetime.now(timezone.utc)

        # 1. Save Machine Reading
        reading = MachineReading(
            machine_id=machine.id,
            timestamp=timestamp,
            machine_type=reading_in.machine_type.upper(),
            air_temperature=float(reading_in.air_temperature),
            process_temperature=float(reading_in.process_temperature),
            rotational_speed=float(reading_in.rotational_speed),
            torque=float(reading_in.torque),
            tool_wear=float(reading_in.tool_wear)
        )
        db.add(reading)
        db.commit()
        db.refresh(reading)

        # 2. Run Predictive Maintenance ML Model
        pm_input = PMPredictionInput(
            machine_type=reading.machine_type,
            air_temperature=reading.air_temperature,
            process_temperature=reading.process_temperature,
            rotational_speed=reading.rotational_speed,
            torque=reading.torque,
            tool_wear=reading.tool_wear
        )
        pm_result = PredictiveMaintenanceService.predict(pm_input)

        # Save PM Prediction
        pred_record = MachinePrediction(
            machine_id=machine.id,
            reading_id=reading.id,
            model_name=pm_result["model_name"],
            prediction=pm_result["prediction"],
            failure_probability=pm_result["failure_probability"],
            failure_percentage=pm_result["failure_percentage"],
            status=pm_result["status"],
            created_at=timestamp
        )
        db.add(pred_record)

        # 3. Run Anomaly Detection Model
        anomaly_input = AnomalyInput(
            air_temperature=reading.air_temperature,
            process_temperature=reading.process_temperature,
            rotational_speed=reading.rotational_speed,
            torque=reading.torque,
            tool_wear=reading.tool_wear
        )
        anomaly_result = AnomalyService.predict(anomaly_input)

        # Save Anomaly Prediction
        anomaly_record = AnomalyPrediction(
            machine_id=machine.id,
            reading_id=reading.id,
            anomaly_detected=anomaly_result["anomaly_detected"],
            anomaly_score=anomaly_result["anomaly_score"],
            severity=anomaly_result["severity"],
            timestamp=timestamp
        )
        db.add(anomaly_record)
        db.commit()

        # 4. Calculate Machine Health Score
        # Retrieve recent historical scores for smoothing
        recent_records = db.query(MachineHealthHistory).filter(
            MachineHealthHistory.machine_id == machine.id
        ).order_by(MachineHealthHistory.recorded_at.desc()).limit(3).all()
        recent_scores = [r.score for r in recent_records]

        health_score, category = HealthScoringEngine.calculate_health_score(
            failure_prob=pm_result["failure_probability"],
            anomaly_detected=anomaly_result["anomaly_detected"],
            anomaly_score=anomaly_result["anomaly_score"],
            air_temp=reading.air_temperature,
            proc_temp=reading.process_temperature,
            torque=reading.torque,
            tool_wear=reading.tool_wear,
            recent_scores=recent_scores
        )

        # Save Health Record
        health_record = HealthScoringEngine.record_health(
            db=db,
            machine_id=machine.id,
            score=health_score,
            category=category,
            failure_prob=pm_result["failure_probability"],
            anomaly_score=anomaly_result["anomaly_score"]
        )

        # 5. Update Machine Status
        old_status = machine.status
        reschedule_triggered = False
        if category == "CRITICAL":
            machine.status = "CRITICAL"
            if old_status != "CRITICAL":
                from app.services.scheduler import ProductionSchedulerService
                trigger_reason = f"Machine {machine.machine_id} entered critical health state ({health_score}/100) due to elevated failure probability ({pm_result['failure_percentage']}%)."
                ProductionSchedulerService.automatic_reschedule_on_machine_incident(db, machine.id, trigger_reason)
                reschedule_triggered = True
        elif category == "WARNING":
            if machine.status not in ["MAINTENANCE", "OFFLINE"]:
                machine.status = "WARNING"
        else:
            if machine.status in ["WARNING", "CRITICAL"]:
                machine.status = "RUNNING"

        db.commit()
        db.refresh(machine)


        # 6. Generate Alerts when necessary
        generated_alerts = []
        if pm_result["failure_probability"] >= 0.60 or pm_result["prediction"] == 1:
            alert = AlertService.create_alert(db, AlertCreate(
                machine_id=machine.id,
                alert_type="FAILURE_RISK",
                severity="CRITICAL" if pm_result["failure_probability"] >= 0.75 else "HIGH",
                title=f"High Failure Probability on {machine.machine_id}",
                message=f"Machine {machine.machine_id} exhibits {pm_result['failure_percentage']}% failure probability via {pm_result['model_name']}."
            ))
            generated_alerts.append(alert.id)

        if anomaly_result["severity"] in ["HIGH", "CRITICAL"]:
            alert = AlertService.create_alert(db, AlertCreate(
                machine_id=machine.id,
                alert_type="ANOMALY",
                severity=anomaly_result["severity"],
                title=f"Mechanical Anomaly Detected on {machine.machine_id}",
                message=f"Isolation Forest identified abnormal sensor drift (Score: {anomaly_result['anomaly_score']}, Severity: {anomaly_result['severity']})."
            ))
            generated_alerts.append(alert.id)

        if reading.tool_wear >= 220.0:
            alert = AlertService.create_alert(db, AlertCreate(
                machine_id=machine.id,
                alert_type="HIGH_TOOL_WEAR",
                severity="WARNING",
                title=f"Excessive Tool Wear on {machine.machine_id}",
                message=f"Tool wear reached {reading.tool_wear} minutes. Replacement or inspection recommended."
            ))
            generated_alerts.append(alert.id)

        if reading.torque >= 65.0:
            alert = AlertService.create_alert(db, AlertCreate(
                machine_id=machine.id,
                alert_type="HIGH_TORQUE",
                severity="WARNING",
                title=f"Torque Overload on {machine.machine_id}",
                message=f"Operating torque spike observed at {reading.torque} Nm."
            ))
            generated_alerts.append(alert.id)

        return {
            "reading_id": reading.id,
            "machine_id": machine.machine_id,
            "machine_status": machine.status,
            "previous_status": old_status,
            "prediction": pm_result,
            "anomaly": anomaly_result,
            "health": {
                "score": health_score,
                "category": category,
                "recorded_at": health_record.recorded_at.isoformat()
            },
            "alerts_generated_count": len(generated_alerts)
        }
