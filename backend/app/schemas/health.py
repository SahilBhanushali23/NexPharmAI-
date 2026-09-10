from pydantic import BaseModel, ConfigDict
from datetime import datetime

class MachineHealthResponse(BaseModel):
    machine_id: str
    score: float # 0 - 100
    category: str # EXCELLENT, GOOD, WARNING, CRITICAL
    failure_probability: float
    anomaly_score: float
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)
