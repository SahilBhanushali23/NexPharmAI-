from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class ProductionOrder(Base):
    __tablename__ = "production_orders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_code = Column(String(50), unique=True, nullable=False, index=True) # e.g. ORD-2026-001
    product_id = Column(String(36), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False) # Total units ordered
    priority = Column(String(20), nullable=False, default="MEDIUM") # LOW, MEDIUM, HIGH, URGENT
    due_date = Column(DateTime, nullable=False)
    status = Column(String(30), nullable=False, default="PLANNED") # PLANNED, SCHEDULED, RUNNING, COMPLETED, ON_HOLD, CANCELLED
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    product = relationship("Product", back_populates="orders")
    batches = relationship("ProductionBatch", back_populates="order", cascade="all, delete-orphan")

class ProductionBatch(Base):
    __tablename__ = "production_batches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_number = Column(String(50), unique=True, nullable=False, index=True) # e.g. BATCH-2026-101
    order_id = Column(String(36), ForeignKey("production_orders.id", ondelete="SET NULL"), nullable=True, index=True)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    machine_id = Column(String(36), ForeignKey("machines.id", ondelete="SET NULL"), nullable=True, index=True)
    schedule_id = Column(String(36), ForeignKey("production_schedules.id", ondelete="SET NULL"), nullable=True, index=True)
    quantity = Column(Integer, nullable=False)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    status = Column(String(30), nullable=False, default="PLANNED") # PLANNED, IN_PROGRESS, COMPLETED, QUARANTINED, REJECTED
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    order = relationship("ProductionOrder", back_populates="batches")
    product = relationship("Product", back_populates="batches")
    machine = relationship("Machine", back_populates="batches")
    schedule = relationship("ProductionSchedule", back_populates="batches")
    quality_predictions = relationship("QualityPrediction", back_populates="batch")

class ProductionSchedule(Base):
    __tablename__ = "production_schedules"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    schedule_name = Column(String(100), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    status = Column(String(30), nullable=False, default="ACTIVE") # DRAFT, ACTIVE, SUPERSEDED, CANCELLED
    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    total_makespan_hours = Column(Float, nullable=False, default=0.0)
    optimizer_status = Column(String(50), nullable=False, default="OPTIMAL") # OPTIMAL, FEASIBLE, INFEASIBLE
    schedule_metadata = Column(JSON, nullable=True) # Full schedule assignments and constraints

    batches = relationship("ProductionBatch", back_populates="schedule")
    revisions = relationship("ScheduleRevision", back_populates="schedule", cascade="all, delete-orphan", order_by="desc(ScheduleRevision.created_at)")

class ScheduleRevision(Base):
    __tablename__ = "schedule_revisions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    schedule_id = Column(String(36), ForeignKey("production_schedules.id", ondelete="CASCADE"), nullable=False, index=True)
    revision_number = Column(Integer, nullable=False)
    trigger_event = Column(String(100), nullable=False) # MACHINE_CRITICAL_HEALTH, ANOMALY_TRIGGER, INVENTORY_SHORTAGE, MANUAL
    reason = Column(Text, nullable=False) # e.g. "Machine M-001 entered critical health state due to elevated failure probability."
    changes_summary = Column(JSON, nullable=True) # Details of affected batches and reassignments
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    schedule = relationship("ProductionSchedule", back_populates="revisions")
