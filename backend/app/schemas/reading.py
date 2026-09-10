from typing import Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class MachineReadingBase(BaseModel):
    machine_id: str
    machine_type: str # L, M, H
    air_temperature: float # Kelvin
    process_temperature: float # Kelvin
    rotational_speed: float # rpm
    torque: float # Nm
    tool_wear: float # minutes

class MachineReadingCreate(MachineReadingBase):
    timestamp: Optional[datetime] = None

class MachineReadingResponse(MachineReadingBase):
    id: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class ReadingIngestResult(BaseModel):
    reading: MachineReadingResponse
    prediction: dict
    anomaly: dict
    health: dict
    alerts_generated: list[dict]
    machine_status: str
