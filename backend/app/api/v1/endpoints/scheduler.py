from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, RoleChecker
from app.models.user import User
from app.models.production import ProductionSchedule, ScheduleRevision
from app.schemas.production import (
    ScheduleGenerateRequest,
    ScheduleResponse,
    ScheduleRevisionResponse,
    RescheduleRequest
)
from app.services.scheduler import ProductionSchedulerService

router = APIRouter()
operator_or_above = RoleChecker(["ADMIN", "PRODUCTION_MANAGER", "MAINTENANCE_MANAGER", "QUALITY_MANAGER", "OPERATOR"])
manager_or_admin = RoleChecker(["ADMIN", "PRODUCTION_MANAGER"])

def extract_assignments(sched: ProductionSchedule) -> list:
    assignments = sched.schedule_metadata.get("assignments", []) if sched.schedule_metadata else []
    if not assignments and sched.batches:
        for b in sched.batches:
            assignments.append({
                "batch_number": b.batch_number,
                "order_code": b.order.order_code if b.order else "N/A",
                "product_name": b.product.product_name if b.product else "N/A",
                "machine_id": b.machine.machine_id if b.machine else "N/A",
                "machine_name": b.machine.machine_name if b.machine else "N/A",
                "start_time": b.start_time.strftime("%Y-%m-%d %H:%M") if b.start_time else "TBD",
                "end_time": b.end_time.strftime("%Y-%m-%d %H:%M") if b.end_time else "TBD",
                "duration_hours": max(1.0, (b.end_time - b.start_time).total_seconds() / 3600) if (b.end_time and b.start_time) else 4.0,
                "status": b.status
            })
    return assignments

@router.post("/generate", response_model=ScheduleResponse, summary="Run Google OR-Tools AI Production Scheduler")
def generate_schedule(
    req: ScheduleGenerateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(manager_or_admin)
):
    sched = ProductionSchedulerService.generate_schedule(db, horizon_days=req.horizon_days)
    assignments = extract_assignments(sched)
    conflicts = sched.schedule_metadata.get("conflicts", []) if sched.schedule_metadata else []
    return {
        "id": sched.id,
        "schedule_name": sched.schedule_name,
        "version": sched.version,
        "status": sched.status,
        "generated_at": sched.generated_at,
        "total_makespan_hours": sched.total_makespan_hours,
        "optimizer_status": sched.optimizer_status,
        "assignments": assignments,
        "conflicts": conflicts
    }

@router.get("/active", response_model=Optional[ScheduleResponse], summary="Get current active production schedule")
def get_active_schedule(
    db: Session = Depends(get_db),
    _: User = Depends(operator_or_above)
):
    sched = db.query(ProductionSchedule).filter(ProductionSchedule.status == "ACTIVE").order_by(ProductionSchedule.generated_at.desc()).first()
    if not sched:
        return None
    assignments = extract_assignments(sched)
    conflicts = sched.schedule_metadata.get("conflicts", []) if sched.schedule_metadata else []
    return {
        "id": sched.id,
        "schedule_name": sched.schedule_name,
        "version": sched.version,
        "status": sched.status,
        "generated_at": sched.generated_at,
        "total_makespan_hours": sched.total_makespan_hours,
        "optimizer_status": sched.optimizer_status,
        "assignments": assignments,
        "conflicts": conflicts
    }


@router.get("/revisions", response_model=List[ScheduleRevisionResponse], summary="List all schedule revisions and change logs")
def list_schedule_revisions(
    db: Session = Depends(get_db),
    _: User = Depends(operator_or_above)
):
    return db.query(ScheduleRevision).order_by(ScheduleRevision.created_at.desc()).all()

@router.post("/reschedule", response_model=Optional[ScheduleRevisionResponse], summary="Trigger dynamic rescheduling for a degraded machine")
def trigger_dynamic_reschedule(
    req: RescheduleRequest,
    db: Session = Depends(get_db),
    _: User = Depends(manager_or_admin)
):
    reason = req.trigger_reason or f"Manual rescheduling request triggered for Machine {req.machine_id}"
    rev = ProductionSchedulerService.automatic_reschedule_on_machine_incident(db, req.machine_id, reason)
    if not rev:
        raise HTTPException(status_code=400, detail="No active schedule to revise or machine not found.")
    return rev
