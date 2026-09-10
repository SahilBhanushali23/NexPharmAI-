from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class QualityPredictInput(BaseModel):
    batch_id: str
    temperature: float # deg C
    pressure: float # bar
    ph: float # pH
    humidity: float # %
    mixing_speed: float # rpm
    mixing_time: float # minutes
    process_features: Optional[Dict[str, Any]] = None

class QualityPredictResponse(BaseModel):
    id: str
    batch_id: str
    quality_score: float # 0 - 100
    pass_probability: float # 0.0 - 1.0
    quality_risk: str # LOW, MEDIUM, HIGH
    status: str # PASS, REJECT, PENDING_REVIEW
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
