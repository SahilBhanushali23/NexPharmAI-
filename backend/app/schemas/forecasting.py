from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class ForecastGenerateRequest(BaseModel):
    product_id: str
    horizon_days: int = 30 # 7, 30, 90

class ForecastItem(BaseModel):
    date: str
    predicted_demand: float
    lower_bound: float
    upper_bound: float

class DemandForecastResponse(BaseModel):
    product_id: str
    product_name: str
    product_code: str
    horizon_days: int
    forecast_status: str # "DATASET_REQUIRED" or "ACTIVE"
    training_data_status: str
    total_projected_demand: float
    forecasts: List[ForecastItem]
    generated_at: datetime
