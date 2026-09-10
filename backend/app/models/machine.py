from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base

class ProductionLine(Base):
    __tablename__ = "production_lines"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    line_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    machines = relationship("Machine", back_populates="production_line_rel")

class Machine(Base):
    __tablename__ = "machines"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    machine_id = Column(String(50), unique=True, nullable=False, index=True) # e.g. M-101, L1-GRAN-01
    machine_name = Column(String(100), nullable=False)
    machine_type = Column(String(10), nullable=False) # L, M, H (matches AI4I 2020 dataset)
    production_line = Column(String(50), nullable=False) # code or reference
    production_line_id = Column(String(36), ForeignKey("production_lines.id", ondelete="SET NULL"), nullable=True)
    location = Column(String(100), nullable=False, default="Cleanroom 1")
    status = Column(String(30), nullable=False, default="IDLE") # RUNNING, IDLE, WARNING, CRITICAL, MAINTENANCE, OFFLINE
    installation_date = Column(DateTime, nullable=True)
    last_maintenance_date = Column(DateTime, nullable=True)
    next_maintenance_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    production_line_rel = relationship("ProductionLine", back_populates="machines")
    readings = relationship("MachineReading", back_populates="machine", cascade="all, delete-orphan", order_by="desc(MachineReading.timestamp)")
    predictions = relationship("MachinePrediction", back_populates="machine", cascade="all, delete-orphan", order_by="desc(MachinePrediction.created_at)")
    anomalies = relationship("AnomalyPrediction", back_populates="machine", cascade="all, delete-orphan", order_by="desc(AnomalyPrediction.timestamp)")
    health_history = relationship("MachineHealthHistory", back_populates="machine", cascade="all, delete-orphan", order_by="desc(MachineHealthHistory.recorded_at)")
    maintenance_records = relationship("MaintenanceRecord", back_populates="machine")
    alerts = relationship("Alert", back_populates="machine")
    batches = relationship("ProductionBatch", back_populates="machine")

class MachineReading(Base):
    __tablename__ = "machine_readings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    machine_id = Column(String(36), ForeignKey("machines.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    machine_type = Column(String(10), nullable=False) # L, M, H
    air_temperature = Column(Float, nullable=False) # Kelvin
    process_temperature = Column(Float, nullable=False) # Kelvin
    rotational_speed = Column(Float, nullable=False) # rpm
    torque = Column(Float, nullable=False) # Nm
    tool_wear = Column(Float, nullable=False) # minutes

    machine = relationship("Machine", back_populates="readings")

class MachinePrediction(Base):
    __tablename__ = "machine_predictions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    machine_id = Column(String(36), ForeignKey("machines.id", ondelete="CASCADE"), nullable=False, index=True)
    reading_id = Column(String(36), ForeignKey("machine_readings.id", ondelete="SET NULL"), nullable=True)
    model_name = Column(String(50), nullable=False, default="XGBoost")
    prediction = Column(Integer, nullable=False) # 0 = Normal, 1 = Failure Risk
    failure_probability = Column(Float, nullable=False) # 0.0 - 1.0
    failure_percentage = Column(Float, nullable=False) # 0.0 - 100.0%
    status = Column(String(30), nullable=False) # NORMAL, WARNING, CRITICAL
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    machine = relationship("Machine", back_populates="predictions")

class AnomalyPrediction(Base):
    __tablename__ = "anomaly_predictions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    machine_id = Column(String(36), ForeignKey("machines.id", ondelete="CASCADE"), nullable=False, index=True)
    reading_id = Column(String(36), ForeignKey("machine_readings.id", ondelete="SET NULL"), nullable=True)
    anomaly_detected = Column(Integer, nullable=False) # 1 = Anomaly, 0 = Normal
    anomaly_score = Column(Float, nullable=False) # Continuous score
    severity = Column(String(20), nullable=False) # NORMAL, LOW, MEDIUM, HIGH, CRITICAL
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    machine = relationship("Machine", back_populates="anomalies")

class MachineHealthHistory(Base):
    __tablename__ = "machine_health_history"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    machine_id = Column(String(36), ForeignKey("machines.id", ondelete="CASCADE"), nullable=False, index=True)
    score = Column(Float, nullable=False) # 0 - 100
    category = Column(String(20), nullable=False) # EXCELLENT, GOOD, WARNING, CRITICAL
    failure_probability = Column(Float, nullable=False)
    anomaly_score = Column(Float, nullable=False)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    machine = relationship("Machine", back_populates="health_history")
