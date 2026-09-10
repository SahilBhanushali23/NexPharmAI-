from typing import Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class AnomalyInput(BaseModel):
    air_temperature: float
    process_temperature: float
    rotational_speed: float
    torque: float
    tool_wear: float

class AnomalyResponse(BaseModel):
    anomaly_detected: int # 0 = Normal, 1 = Anomaly
    anomaly_score: float
    severity: str # NORMAL, LOW, MEDIUM, HIGH, CRITICAL
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
