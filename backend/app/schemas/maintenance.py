from typing import Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class MaintenanceBase(BaseModel):
    machine_id: str
    maintenance_type: str # PREVENTIVE, PREDICTIVE, CORRECTIVE, EMERGENCY
    reason: str
    priority: str = "MEDIUM" # LOW, MEDIUM, HIGH, CRITICAL
    assigned_to: Optional[str] = None
    scheduled_date: datetime
    notes: Optional[str] = None

class MaintenanceCreate(MaintenanceBase):
    pass

class MaintenanceUpdate(BaseModel):
    maintenance_type: Optional[str] = None
    reason: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    status: Optional[str] = None # PENDING, IN_PROGRESS, COMPLETED, CANCELLED
    notes: Optional[str] = None

class MaintenanceResponse(MaintenanceBase):
    id: str
    status: str
    completed_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
