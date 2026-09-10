from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class InventoryMaterial(Base):
    __tablename__ = "inventory_materials"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    material_code = Column(String(50), unique=True, nullable=False, index=True) # e.g. MAT-API-PARA
    material_name = Column(String(150), nullable=False) # e.g. Paracetamol Active Pharmaceutical Ingredient
    category = Column(String(50), nullable=False) # API, EXCIPIENT, PACKAGING, SOLVENT
    quantity = Column(Float, nullable=False, default=0.0) # current available stock
    unit = Column(String(20), nullable=False, default="kg") # kg, liters, units
    reorder_level = Column(Float, nullable=False, default=100.0) # minimum threshold
    supplier = Column(String(150), nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    batch_number = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    transactions = relationship("InventoryTransaction", back_populates="material", cascade="all, delete-orphan")

class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    material_id = Column(String(36), ForeignKey("inventory_materials.id", ondelete="CASCADE"), nullable=False, index=True)
    transaction_type = Column(String(30), nullable=False) # RECEIVE, CONSUME, RESERVE, ADJUST
    quantity = Column(Float, nullable=False) # positive or negative delta
    balance_after = Column(Float, nullable=False)
    reference_type = Column(String(30), nullable=True) # PRODUCTION_BATCH, MANUAL, PURCHASE_ORDER
    reference_id = Column(String(50), nullable=True)
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    material = relationship("InventoryMaterial", back_populates="transactions")
