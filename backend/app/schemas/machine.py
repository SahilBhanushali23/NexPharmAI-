from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime

class ProductionLineBase(BaseModel):
    line_code: str
    name: str
    description: Optional[str] = None

class ProductionLineCreate(ProductionLineBase):
    pass

class ProductionLineResponse(ProductionLineBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MachineBase(BaseModel):
    machine_id: str = Field(..., alias="machine_code")
    machine_name: str = Field(..., alias="name")
    machine_type: str = "M"
    production_line: str = "LINE-1"
    production_line_id: Optional[str] = None
    location: str = "Cleanroom 1"
    status: str = "RUNNING"
    installation_date: Optional[datetime] = None
    last_maintenance_date: Optional[datetime] = None
    next_maintenance_date: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

class MachineCreate(MachineBase):
    pass

class MachineUpdate(BaseModel):
    machine_name: Optional[str] = Field(None, alias="name")
    machine_type: Optional[str] = None
    production_line: Optional[str] = None
    production_line_id: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    last_maintenance_date: Optional[datetime] = None
    next_maintenance_date: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

class MachineResponse(BaseModel):
    id: str
    machine_id: str
    machine_code: str
    machine_name: str
    name: str
    machine_type: str
    production_line: str
    production_line_id: Optional[str] = None
    location: str
    status: str
    health_score: float = 85.0
    total_operating_hours: int = 1200
    installation_date: Optional[datetime] = None
    last_maintenance_date: Optional[datetime] = None
    next_maintenance_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MachineDetailResponse(MachineResponse):
    latest_reading: Optional[dict] = None
    latest_health: Optional[dict] = None
    latest_prediction: Optional[dict] = None
    active_alerts_count: int = 0
