from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, RoleChecker
from app.models.user import User
from app.models.machine import Machine, MachineReading, AnomalyPrediction
from app.schemas.anomaly import AnomalyInput, AnomalyResponse
from app.services.anomaly import AnomalyService

router = APIRouter()
operator_or_above = RoleChecker(["ADMIN", "PRODUCTION_MANAGER", "MAINTENANCE_MANAGER", "QUALITY_MANAGER", "OPERATOR"])

@router.post("/predict", response_model=AnomalyResponse, summary="Direct Isolation Forest anomaly inference")
def predict_anomaly(
    input_data: AnomalyInput,
    _: User = Depends(operator_or_above)
):
    return AnomalyService.predict(input_data)

@router.post("/machines/{machine_id}/anomaly-check", response_model=AnomalyResponse, summary="Run anomaly check on machine latest sensor data")
def run_machine_anomaly_check(
    machine_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(operator_or_above)
):
    machine = db.query(Machine).filter(
        (Machine.id == machine_id) | (Machine.machine_id == machine_id)
    ).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")

    latest_reading = db.query(MachineReading).filter(
        MachineReading.machine_id == machine.id
    ).order_by(MachineReading.timestamp.desc()).first()

    if not latest_reading:
        input_data = AnomalyInput(
            air_temperature=298.1,
            process_temperature=308.6,
            rotational_speed=1551.0,
            torque=42.8,
            tool_wear=0.0
        )
    else:
        input_data = AnomalyInput(
            air_temperature=latest_reading.air_temperature,
            process_temperature=latest_reading.process_temperature,
            rotational_speed=latest_reading.rotational_speed,
            torque=latest_reading.torque,
            tool_wear=latest_reading.tool_wear
        )

    res = AnomalyService.predict(input_data)
    
    # Store record
    record = AnomalyPrediction(
        machine_id=machine.id,
        reading_id=latest_reading.id if latest_reading else None,
        anomaly_detected=res["anomaly_detected"],
        anomaly_score=res["anomaly_score"],
        severity=res["severity"],
        timestamp=res["timestamp"]
    )
    db.add(record)
    db.commit()

    return res

@router.get("/machines/{machine_id}/history", response_model=List[AnomalyResponse], summary="Retrieve historical anomaly checks")
def get_anomaly_history(
    machine_id: str,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(operator_or_above)
):
    machine = db.query(Machine).filter(
        (Machine.id == machine_id) | (Machine.machine_id == machine_id)
    ).first()
    if not machine:
        return []
    return db.query(AnomalyPrediction).filter(
        AnomalyPrediction.machine_id == machine.id
    ).order_by(AnomalyPrediction.timestamp.desc()).limit(limit).all()
