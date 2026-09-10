from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    machine_id = Column(String(36), ForeignKey("machines.id", ondelete="SET NULL"), nullable=True, index=True)
    alert_type = Column(String(50), nullable=False, index=True)
    # Types: FAILURE_RISK, ANOMALY, HIGH_TEMPERATURE, HIGH_TORQUE, HIGH_TOOL_WEAR, MAINTENANCE_DUE, MACHINE_OFFLINE, QUALITY_RISK, INVENTORY_SHORTAGE, SCHEDULING_CONFLICT
    severity = Column(String(20), nullable=False, index=True) # INFO, WARNING, HIGH, CRITICAL
    title = Column(String(150), nullable=False)
    message = Column(String(500), nullable=False)
    is_acknowledged = Column(Boolean, default=False, nullable=False)
    acknowledged_by = Column(String(36), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    is_resolved = Column(Boolean, default=False, nullable=False)
    resolved_by = Column(String(36), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    machine = relationship("Machine", back_populates="alerts")
