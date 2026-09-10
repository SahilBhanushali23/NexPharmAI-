from typing import Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, RoleChecker
from app.models.user import User
from app.services.assistant import DecisionAssistantService

router = APIRouter()
operator_or_above = RoleChecker(["ADMIN", "PRODUCTION_MANAGER", "MAINTENANCE_MANAGER", "QUALITY_MANAGER", "OPERATOR"])

class AssistantQueryRequest(BaseModel):
    query: str

@router.post("/query", summary="Query the AI Decision Assistant against live factory database records")
def query_assistant(
    req: AssistantQueryRequest,
    db: Session = Depends(get_db),
    _: User = Depends(operator_or_above)
):
    return DecisionAssistantService.answer_query(db, req.query)
