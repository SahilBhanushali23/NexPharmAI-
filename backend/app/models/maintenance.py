from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    machine_id = Column(String(36), ForeignKey("machines.id", ondelete="CASCADE"), nullable=False, index=True)
    maintenance_type = Column(String(30), nullable=False) # PREVENTIVE, PREDICTIVE, CORRECTIVE, EMERGENCY
    reason = Column(String(255), nullable=False)
    priority = Column(String(20), nullable=False, default="MEDIUM") # LOW, MEDIUM, HIGH, CRITICAL
    assigned_to = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    scheduled_date = Column(DateTime, nullable=False)
    completed_date = Column(DateTime, nullable=True)
    status = Column(String(30), nullable=False, default="PENDING") # PENDING, IN_PROGRESS, COMPLETED, CANCELLED
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    machine = relationship("Machine", back_populates="maintenance_records")
    assignee = relationship("User", back_populates="assigned_maintenance")
