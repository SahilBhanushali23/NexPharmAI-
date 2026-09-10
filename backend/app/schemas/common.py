from typing import Generic, Optional, TypeVar, Any
from pydantic import BaseModel
from datetime import datetime

T = TypeVar("T")

class HealthResponse(BaseModel):
    status: str = "online"
    service: str = "NexPharmAI Core Engine"
    version: str = "1.0.0"
    environment: str = "development"
    timestamp: datetime

class StandardResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[T] = None
