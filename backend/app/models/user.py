from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.core.database import Base

user_roles_table = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", String(36), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
)

class Role(Base):
    __tablename__ = "roles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), unique=True, nullable=False, index=True) # ADMIN, PRODUCTION_MANAGER, etc.
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    users = relationship("User", secondary=user_roles_table, back_populates="roles")

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False, default="OPERATOR") # primary role shortcut
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    roles = relationship("Role", secondary=user_roles_table, back_populates="users", lazy="joined")
    audit_logs = relationship("AuditLog", back_populates="user")
    assigned_maintenance = relationship("MaintenanceRecord", back_populates="assignee")
