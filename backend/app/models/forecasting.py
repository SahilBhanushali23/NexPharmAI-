from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class DemandForecast(Base):
    __tablename__ = "demand_forecasts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    forecast_date = Column(DateTime, nullable=False, index=True)
    horizon_days = Column(Integer, nullable=False) # 7, 30, 90
    predicted_demand = Column(Float, nullable=False) # Units projected
    lower_bound = Column(Float, nullable=False) # Confidence interval lower
    upper_bound = Column(Float, nullable=False) # Confidence interval upper
    confidence_level = Column(Float, nullable=False, default=0.95)
    model_type = Column(String(50), nullable=False, default="ARIMA/Prophet Ensemble")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
