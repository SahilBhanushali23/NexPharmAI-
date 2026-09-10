from typing import Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class PMPredictionInput(BaseModel):
    machine_type: str # L, M, H
    air_temperature: float
    process_temperature: float
    rotational_speed: float
    torque: float
    tool_wear: float

class PMPredictionResponse(BaseModel):
    prediction: int # 0 = Normal, 1 = Failure Risk
    failure_probability: float # 0.0 - 1.0
    failure_percentage: float # 0.0 - 100.0%
    status: str # NORMAL, WARNING, CRITICAL
    model_name: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
