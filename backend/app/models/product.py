from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_code = Column(String(50), unique=True, nullable=False, index=True) # e.g. PROD-PARA-500
    product_name = Column(String(150), nullable=False) # e.g. Paracetamol 500mg Tablets
    description = Column(Text, nullable=True)
    batch_size = Column(Integer, nullable=False, default=10000) # units per batch
    standard_production_time = Column(Float, nullable=False, default=4.0) # hours per batch
    required_materials = Column(JSON, nullable=False, default=dict) # { "MAT-API-PARA": 50.0, "MAT-EXC-STARCH": 10.0 }
    status = Column(String(20), nullable=False, default="ACTIVE") # ACTIVE, INACTIVE
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    orders = relationship("ProductionOrder", back_populates="product")
    batches = relationship("ProductionBatch", back_populates="product")
