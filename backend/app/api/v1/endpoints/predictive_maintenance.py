from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, RoleChecker
from app.models.user import User
from app.models.machine import Machine, MachineReading
from app.schemas.predictive_maintenance import PMPredictionInput, PMPredictionResponse
from app.services.predictive_maintenance import PredictiveMaintenanceService
from app.services.reading import ReadingPipelineService
from app.schemas.reading import MachineReadingCreate

router = APIRouter()
operator_or_above = RoleChecker(["ADMIN", "PRODUCTION_MANAGER", "MAINTENANCE_MANAGER", "QUALITY_MANAGER", "OPERATOR"])

@router.post("/predict", response_model=PMPredictionResponse, summary="On-demand Predictive Maintenance inference")
def predict_machine_failure(
    input_data: PMPredictionInput,
    _: User = Depends(operator_or_above)
):
    """
    Direct model inference for machine failure probability using trained production ML model.
    """
    return PredictiveMaintenanceService.predict(input_data)

@router.post("/machines/{machine_id}/predict", summary="Run prediction on machine's latest telemetry reading")
def run_machine_prediction(
    machine_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(operator_or_above)
):
    """
    Retrieves the machine's latest telemetry reading, executes failure prediction,
    updates health, and triggers alerts if necessary.
    """
    machine = db.query(Machine).filter(
        (Machine.id == machine_id) | (Machine.machine_id == machine_id)
    ).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")

    latest_reading = db.query(MachineReading).filter(
        MachineReading.machine_id == machine.id
    ).order_by(MachineReading.timestamp.desc()).first()

    if not latest_reading:
        # If no reading exists, run with standard baseline values
        reading_in = MachineReadingCreate(
            machine_id=machine.machine_id,
            machine_type=machine.machine_type,
            air_temperature=298.1,
            process_temperature=308.6,
            rotational_speed=1551.0,
            torque=42.8,
            tool_wear=0.0
        )
    else:
        reading_in = MachineReadingCreate(
            machine_id=machine.machine_id,
            machine_type=latest_reading.machine_type,
            air_temperature=latest_reading.air_temperature,
            process_temperature=latest_reading.process_temperature,
            rotational_speed=latest_reading.rotational_speed,
            torque=latest_reading.torque,
            tool_wear=latest_reading.tool_wear
        )

    return ReadingPipelineService.ingest_reading(db, reading_in)
