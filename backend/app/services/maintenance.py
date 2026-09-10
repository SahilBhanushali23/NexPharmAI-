from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.maintenance import MaintenanceRecord
from app.models.machine import Machine
from app.schemas.maintenance import MaintenanceCreate, MaintenanceUpdate
from app.utils.logger import logger

class MaintenanceService:
    @staticmethod
    def create_record(db: Session, record_in: MaintenanceCreate) -> MaintenanceRecord:
        machine = db.query(Machine).filter(
            (Machine.id == record_in.machine_id) | (Machine.machine_id == record_in.machine_id)
        ).first()
        if not machine:
            raise HTTPException(status_code=404, detail="Machine not found")

        # If it's an emergency or high-priority corrective maintenance, set machine status to MAINTENANCE
        if record_in.maintenance_type in ["EMERGENCY", "CORRECTIVE"] or record_in.priority == "CRITICAL":
            machine.status = "MAINTENANCE"
            db.commit()

        record = MaintenanceRecord(
            machine_id=machine.id,
            maintenance_type=record_in.maintenance_type.upper(),
            reason=record_in.reason,
            priority=record_in.priority.upper(),
            assigned_to=record_in.assigned_to,
            scheduled_date=record_in.scheduled_date,
            status="PENDING",
            notes=record_in.notes,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        logger.info(f"Created maintenance work order for machine {machine.machine_id} ({record.maintenance_type})")
        return record

    @staticmethod
    def get_records(
        db: Session,
        machine_id: Optional[str] = None,
        status: Optional[str] = None,
        maintenance_type: Optional[str] = None,
        priority: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[MaintenanceRecord]:
        query = db.query(MaintenanceRecord)
        if machine_id:
            machine = db.query(Machine).filter(
                (Machine.id == machine_id) | (Machine.machine_id == machine_id)
            ).first()
            if machine:
                query = query.filter(MaintenanceRecord.machine_id == machine.id)
        if status:
            query = query.filter(MaintenanceRecord.status == status.upper())
        if maintenance_type:
            query = query.filter(MaintenanceRecord.maintenance_type == maintenance_type.upper())
        if priority:
            query = query.filter(MaintenanceRecord.priority == priority.upper())
        return query.order_by(MaintenanceRecord.scheduled_date.asc()).offset(skip).limit(limit).all()

    @staticmethod
    def update_record(db: Session, record_id: str, record_in: MaintenanceUpdate) -> MaintenanceRecord:
        record = db.query(MaintenanceRecord).filter(MaintenanceRecord.id == record_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="Maintenance record not found")

        if record_in.maintenance_type: record.maintenance_type = record_in.maintenance_type.upper()
        if record_in.reason: record.reason = record_in.reason
        if record_in.priority: record.priority = record_in.priority.upper()
        if record_in.assigned_to: record.assigned_to = record_in.assigned_to
        if record_in.scheduled_date: record.scheduled_date = record_in.scheduled_date
        if record_in.notes: record.notes = record_in.notes

        if record_in.status:
            record.status = record_in.status.upper()
            if record.status == "COMPLETED":
                record.completed_date = record_in.completed_date or datetime.now(timezone.utc)
                # Update machine status back to IDLE
                machine = db.query(Machine).filter(Machine.id == record.machine_id).first()
                if machine and machine.status == "MAINTENANCE":
                    machine.status = "IDLE"
                    machine.last_maintenance_date = record.completed_date
            elif record.status == "IN_PROGRESS":
                machine = db.query(Machine).filter(Machine.id == record.machine_id).first()
                if machine:
                    machine.status = "MAINTENANCE"

        record.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(record)
        return record
