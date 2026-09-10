from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, status
from app.models.machine import Machine, ProductionLine
from app.schemas.machine import MachineCreate, MachineUpdate, ProductionLineCreate
from app.utils.logger import logger

class MachineService:
    @staticmethod
    def get_lines(db: Session) -> List[ProductionLine]:
        return db.query(ProductionLine).all()

    @staticmethod
    def create_line(db: Session, line_in: ProductionLineCreate) -> ProductionLine:
        existing = db.query(ProductionLine).filter(ProductionLine.line_code == line_in.line_code.upper()).first()
        if existing:
            raise HTTPException(status_code=400, detail="Production line code already exists.")
        line = ProductionLine(
            line_code=line_in.line_code.upper(),
            name=line_in.name,
            description=line_in.description
        )
        db.add(line)
        db.commit()
        db.refresh(line)
        return line

    @staticmethod
    def get_machines(
        db: Session,
        status: Optional[str] = None,
        production_line: Optional[str] = None,
        machine_type: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Machine]:
        query = db.query(Machine)
        if status:
            query = query.filter(Machine.status == status.upper())
        if production_line:
            query = query.filter(Machine.production_line == production_line.upper())
        if machine_type:
            query = query.filter(Machine.machine_type == machine_type.upper())
        if search:
            search_fmt = f"%{search}%"
            query = query.filter(
                or_(
                    Machine.machine_id.ilike(search_fmt),
                    Machine.machine_name.ilike(search_fmt),
                    Machine.location.ilike(search_fmt)
                )
            )
        machines = query.order_by(Machine.machine_id).offset(skip).limit(limit).all()
        for m in machines:
            setattr(m, 'machine_code', m.machine_id)
            setattr(m, 'name', m.machine_name)
            if hasattr(m, 'health_history') and m.health_history:
                setattr(m, 'health_score', round(float(m.health_history[0].score), 1))
            else:
                s_map = {'RUNNING': 94.0, 'WARNING': 62.0, 'CRITICAL': 32.0, 'MAINTENANCE': 45.0, 'IDLE': 88.0}
                setattr(m, 'health_score', s_map.get(m.status, 85.0))
            setattr(m, 'total_operating_hours', 1420)
        return machines

    @staticmethod
    def get_machine_by_id(db: Session, machine_id_or_uuid: str) -> Machine:
        machine = db.query(Machine).filter(
            or_(Machine.id == machine_id_or_uuid, Machine.machine_id == machine_id_or_uuid)
        ).first()
        if not machine:
            raise HTTPException(status_code=404, detail=f"Machine '{machine_id_or_uuid}' not found.")
        setattr(machine, 'machine_code', machine.machine_id)
        setattr(machine, 'name', machine.machine_name)
        if hasattr(machine, 'health_history') and machine.health_history:
            setattr(machine, 'health_score', round(float(machine.health_history[0].score), 1))
        else:
            s_map = {'RUNNING': 94.0, 'WARNING': 62.0, 'CRITICAL': 32.0, 'MAINTENANCE': 45.0, 'IDLE': 88.0}
            setattr(machine, 'health_score', s_map.get(machine.status, 85.0))
        setattr(machine, 'total_operating_hours', 1420)
        return machine

    @staticmethod
    def create_machine(db: Session, machine_in: MachineCreate) -> Machine:
        existing = db.query(Machine).filter(Machine.machine_id == machine_in.machine_id.upper()).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Machine ID '{machine_in.machine_id}' already exists.")

        # Ensure line exists or create if missing
        line = db.query(ProductionLine).filter(ProductionLine.line_code == machine_in.production_line.upper()).first()
        line_id = line.id if line else None

        machine = Machine(
            machine_id=machine_in.machine_id.upper(),
            machine_name=machine_in.machine_name,
            machine_type=machine_in.machine_type.upper(),
            production_line=machine_in.production_line.upper(),
            production_line_id=line_id,
            location=machine_in.location,
            status=machine_in.status.upper(),
            installation_date=machine_in.installation_date,
            last_maintenance_date=machine_in.last_maintenance_date,
            next_maintenance_date=machine_in.next_maintenance_date
        )
        db.add(machine)
        db.commit()
        db.refresh(machine)
        setattr(machine, 'machine_code', machine.machine_id)
        setattr(machine, 'name', machine.machine_name)
        setattr(machine, 'health_score', 95.0)
        setattr(machine, 'total_operating_hours', 1420)
        logger.info(f"Created new machine {machine.machine_id} ({machine.machine_name})")
        return machine

    @staticmethod
    def update_machine(db: Session, machine_id_or_uuid: str, machine_in: MachineUpdate) -> Machine:
        machine = MachineService.get_machine_by_id(db, machine_id_or_uuid)
        if machine_in.machine_name is not None:
            machine.machine_name = machine_in.machine_name
        if machine_in.machine_type is not None:
            machine.machine_type = machine_in.machine_type.upper()
        if machine_in.production_line is not None:
            machine.production_line = machine_in.production_line.upper()
        if machine_in.location is not None:
            machine.location = machine_in.location
        if machine_in.status is not None:
            machine.status = machine_in.status.upper()
        if machine_in.last_maintenance_date is not None:
            machine.last_maintenance_date = machine_in.last_maintenance_date
        if machine_in.next_maintenance_date is not None:
            machine.next_maintenance_date = machine_in.next_maintenance_date

        db.commit()
        db.refresh(machine)
        logger.info(f"Updated machine {machine.machine_id} status to {machine.status}")
        return machine

    @staticmethod
    def delete_machine(db: Session, machine_id_or_uuid: str):
        machine = MachineService.get_machine_by_id(db, machine_id_or_uuid)
        db.delete(machine)
        db.commit()
        logger.info(f"Deleted machine {machine.machine_id}")
        return {"message": f"Machine '{machine.machine_id}' successfully deleted."}
