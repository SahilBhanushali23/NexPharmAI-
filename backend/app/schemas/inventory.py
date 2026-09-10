from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class InventoryMaterialBase(BaseModel):
    material_code: str # e.g. MAT-API-PARA
    material_name: str
    category: str # API, EXCIPIENT, PACKAGING, SOLVENT
    quantity: float
    unit: str = "kg"
    reorder_level: float = 100.0
    supplier: Optional[str] = None
    expiry_date: Optional[datetime] = None
    batch_number: Optional[str] = None

class InventoryMaterialCreate(InventoryMaterialBase):
    pass

class InventoryMaterialUpdate(BaseModel):
    material_name: Optional[str] = None
    category: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    reorder_level: Optional[float] = None
    supplier: Optional[str] = None
    expiry_date: Optional[datetime] = None

class InventoryMaterialResponse(InventoryMaterialBase):
    id: str
    created_at: datetime
    updated_at: datetime
    stock_status: str = "IN_STOCK" # IN_STOCK, LOW_STOCK, OUT_OF_STOCK, EXPIRED

    model_config = ConfigDict(from_attributes=True)

class StockAdjustmentRequest(BaseModel):
    quantity_delta: float
    transaction_type: str # RECEIVE, CONSUME, ADJUST
    reference_type: Optional[str] = "MANUAL"
    reference_id: Optional[str] = None
    notes: Optional[str] = None
