from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class QualityPrediction(Base):
    __tablename__ = "quality_predictions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_id = Column(String(36), ForeignKey("production_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    temperature = Column(Float, nullable=False) # deg C
    pressure = Column(Float, nullable=False) # bar
    ph = Column(Float, nullable=False) # pH scale
    humidity = Column(Float, nullable=False) # %
    mixing_speed = Column(Float, nullable=False) # rpm
    mixing_time = Column(Float, nullable=False) # minutes
    process_features = Column(JSON, nullable=True) # Raw material attributes or spectral inputs
    quality_score = Column(Float, nullable=False) # 0 - 100
    pass_probability = Column(Float, nullable=False) # 0.0 - 1.0
    quality_risk = Column(String(20), nullable=False) # LOW, MEDIUM, HIGH
    status = Column(String(20), nullable=False, default="PASS") # PASS, REJECT, PENDING_REVIEW
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    batch = relationship("ProductionBatch", back_populates="quality_predictions")
