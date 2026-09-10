from fastapi import APIRouter
from datetime import datetime, timezone
from app.schemas.common import HealthResponse
from app.core.config import settings

router = APIRouter()

@router.get("/health", response_model=HealthResponse, summary="Service Health & Liveness Probe")
def health_check():
    """
    Returns the real-time operational status, service identifier, and version of NexPharmAI.
    """
    return HealthResponse(
        status="online",
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(timezone.utc)
    )
