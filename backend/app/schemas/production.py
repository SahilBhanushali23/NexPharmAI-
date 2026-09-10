from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class ProductBase(BaseModel):
    product_code: str
    product_name: str
    description: Optional[str] = None
    batch_size: int = 10000
    standard_production_time: float = 4.0 # hours
    required_materials: Dict[str, float] = {} # material_code -> quantity required per batch
    status: str = "ACTIVE"

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    product_name: Optional[str] = None
    description: Optional[str] = None
    batch_size: Optional[int] = None
    standard_production_time: Optional[float] = None
    required_materials: Optional[Dict[str, float]] = None
    status: Optional[str] = None

class ProductResponse(ProductBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProductionOrderCreate(BaseModel):
    order_code: str
    product_id: str
    quantity: int
    priority: str = "MEDIUM" # LOW, MEDIUM, HIGH, URGENT
    due_date: datetime
    notes: Optional[str] = None

class ProductionOrderResponse(BaseModel):
    id: str
    order_code: str
    product_id: str
    quantity: int
    priority: str
    due_date: datetime
    status: str # PLANNED, SCHEDULED, RUNNING, COMPLETED, ON_HOLD, CANCELLED
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProductionBatchResponse(BaseModel):
    id: str
    batch_number: str
    order_id: Optional[str] = None
    product_id: str
    machine_id: Optional[str] = None
    schedule_id: Optional[str] = None
    quantity: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: str # PLANNED, IN_PROGRESS, COMPLETED, QUARANTINED, REJECTED
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ScheduleGenerateRequest(BaseModel):
    horizon_days: int = 7
    allow_overtime: bool = False

class ScheduledBatchAssignment(BaseModel):
    batch_number: str
    order_code: str
    product_name: str
    machine_id: str
    machine_name: str
    start_time: str
    end_time: str
    duration_hours: float
    status: str

class ScheduleResponse(BaseModel):
    id: str
    schedule_name: str
    version: int
    status: str
    generated_at: datetime
    total_makespan_hours: float
    optimizer_status: str
    assignments: List[ScheduledBatchAssignment] = []
    conflicts: List[str] = []

    model_config = ConfigDict(from_attributes=True)

class ScheduleRevisionResponse(BaseModel):
    id: str
    schedule_id: str
    revision_number: int
    trigger_event: str
    reason: str
    changes_summary: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RescheduleRequest(BaseModel):
    machine_id: str
    trigger_reason: Optional[str] = None
