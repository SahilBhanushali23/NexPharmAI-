from typing import Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class AlertBase(BaseModel):
    machine_id: Optional[str] = None
    alert_type: str # FAILURE_RISK, ANOMALY, HIGH_TEMPERATURE, etc.
    severity: str # INFO, WARNING, HIGH, CRITICAL
    title: str
    message: str

class AlertCreate(AlertBase):
    pass

class AlertResponse(AlertBase):
    id: str
    is_acknowledged: bool
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    is_resolved: bool
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
