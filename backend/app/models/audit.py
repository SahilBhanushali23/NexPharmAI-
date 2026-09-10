from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(50), nullable=False, index=True) # CREATE, UPDATE, DELETE, RESCHEDULE, ACKNOWLEDGE, RESOLVE
    entity_name = Column(String(50), nullable=False, index=True) # Machine, ProductionOrder, Schedule, Alert
    entity_id = Column(String(50), nullable=False, index=True)
    details = Column(JSON, nullable=True) # Previous vs New state
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    user = relationship("User", back_populates="audit_logs")
