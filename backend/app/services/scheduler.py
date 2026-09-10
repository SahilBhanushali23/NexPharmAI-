from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from ortools.sat.python import cp_model
from app.models.production import (
    ProductionOrder,
    ProductionBatch,
    ProductionSchedule,
    ScheduleRevision
)
from app.models.machine import Machine, MachineHealthHistory
from app.models.product import Product
from app.models.maintenance import MaintenanceRecord
from app.services.inventory import InventoryService
from app.services.alert import AlertService
from app.schemas.alert import AlertCreate
from app.utils.logger import logger

class ProductionSchedulerService:
    @staticmethod
    def generate_schedule(db: Session, horizon_days: int = 7) -> ProductionSchedule:
        """
        Runs Google OR-Tools CP-SAT Constraint Optimization to schedule pending production orders.
        """
        logger.info("Initiating Google OR-Tools Production Scheduler optimization...")

        # 1. Fetch Planned / Scheduled Orders
        orders = db.query(ProductionOrder).filter(
            ProductionOrder.status.in_(["PLANNED", "SCHEDULED"])
        ).order_by(ProductionOrder.due_date.asc()).all()

        if not orders:
            logger.info("No pending production orders to schedule.")
            sched = ProductionSchedule(
                schedule_name=f"Schedule-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}",
                version=1,
                status="ACTIVE",
                total_makespan_hours=0.0,
                optimizer_status="EMPTY",
                schedule_metadata={"message": "No planned production orders found."}
            )
            db.add(sched)
            db.commit()
            return sched

        # 2. Fetch Machines & Filter out CRITICAL / MAINTENANCE / OFFLINE
        all_machines = db.query(Machine).all()
        available_machines = [
            m for m in all_machines 
            if m.status not in ["CRITICAL", "MAINTENANCE", "OFFLINE"]
        ]

        if not available_machines:
            logger.error("No machines currently available for production scheduling!")
            AlertService.create_alert(db, AlertCreate(
                alert_type="SCHEDULING_CONFLICT",
                severity="CRITICAL",
                title="Scheduler Halted: No Available Equipment",
                message="All production equipment is currently OFFLINE, CRITICAL, or undergoing MAINTENANCE."
            ))
            sched = ProductionSchedule(
                schedule_name=f"Schedule-Blocked-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}",
                version=1,
                status="DRAFT",
                total_makespan_hours=0.0,
                optimizer_status="INFEASIBLE",
                schedule_metadata={"error": "Zero machines available due to health degradation or maintenance."}
            )
            db.add(sched)
            db.commit()
            return sched

        # 3. Build Batches from Orders and verify Inventory
        batches_to_schedule = []
        conflicts = []

        for order in orders:
            product = db.query(Product).filter(Product.id == order.product_id).first()
            if not product:
                continue

            batch_size = max(1, product.batch_size)
            needed_batches = max(1, (order.quantity + batch_size - 1) // batch_size)

            # Inventory Gating Check
            is_mat_avail, shortages = InventoryService.verify_materials_for_batches(
                db, product.required_materials, needed_batches
            )
            if not is_mat_avail:
                conflicts.extend(shortages)
                order.status = "ON_HOLD"
                AlertService.create_alert(db, AlertCreate(
                    alert_type="INVENTORY_SHORTAGE",
                    severity="HIGH",
                    title=f"Order {order.order_code} Held - Material Shortage",
                    message="; ".join(shortages)
                ))
                continue

            for b_idx in range(needed_batches):
                batches_to_schedule.append({
                    "batch_number": f"{order.order_code}-B{b_idx+1:02d}",
                    "order": order,
                    "product": product,
                    "duration_hours": max(1, int(round(product.standard_production_time)))
                })

        if not batches_to_schedule:
            sched = ProductionSchedule(
                schedule_name=f"Schedule-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}",
                version=1,
                status="ACTIVE",
                total_makespan_hours=0.0,
                optimizer_status="BLOCKED_BY_INVENTORY",
                schedule_metadata={"conflicts": conflicts}
            )
            db.add(sched)
            db.commit()
            return sched

        # 4. Formulate Constraint Programming Model (OR-Tools CP-SAT)
        model = cp_model.CpModel()
        horizon_hours = horizon_days * 24

        # Variables: start, end, interval, machine assignment
        task_vars = {}
        machine_intervals = {m.id: [] for m in available_machines}

        # Due date penalties & priority weights
        priority_weights = {"URGENT": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}

        tardiness_vars = []

        for b_idx, b_info in enumerate(batches_to_schedule):
            duration = b_info["duration_hours"]
            order = b_info["order"]
            
            # Start and End time in integer hours from schedule start
            start_var = model.NewIntVar(0, horizon_hours, f"start_{b_idx}")
            end_var = model.NewIntVar(0, horizon_hours, f"end_{b_idx}")
            interval_var = model.NewIntervalVar(start_var, duration, end_var, f"interval_{b_idx}")
            
            # Machine choice (optional intervals)
            mach_literals = []
            for m in available_machines:
                mach_lit = model.NewBoolVar(f"batch_{b_idx}_on_mach_{m.machine_id}")
                mach_literals.append(mach_lit)
                
                # Create optional interval on machine
                opt_interval = model.NewOptionalIntervalVar(
                    start_var, duration, end_var, mach_lit, f"opt_interval_{b_idx}_{m.id}"
                )
                machine_intervals[m.id].append(opt_interval)
                
            # Exactly one machine must be assigned per batch
            model.Add(sum(mach_literals) == 1)
            
            # Calculate tardiness against due date
            now_utc = datetime.now(timezone.utc)
            order_due = order.due_date
            if order_due.tzinfo is None:
                order_due = order_due.replace(tzinfo=timezone.utc)
            due_hours = max(0, int((order_due - now_utc).total_seconds() // 3600))
            
            tardiness = model.NewIntVar(0, horizon_hours, f"tardy_{b_idx}")
            model.Add(tardiness >= end_var - due_hours)
            
            weight = priority_weights.get(order.priority.upper(), 2)
            tardiness_vars.append(tardiness * weight)

            task_vars[b_idx] = {
                "start": start_var,
                "end": end_var,
                "interval": interval_var,
                "mach_literals": mach_literals,
                "info": b_info
            }

        # Constraint: No overlap on any machine
        for m_id, intervals in machine_intervals.items():
            if intervals:
                model.AddNoOverlap(intervals)

        # Objective: Minimize makespan + weighted tardiness
        makespan = model.NewIntVar(0, horizon_hours, "makespan")
        for b_idx in task_vars:
            model.Add(makespan >= task_vars[b_idx]["end"])

        total_objective = makespan + sum(tardiness_vars)
        model.Minimize(total_objective)

        # 5. Solve CP-SAT
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 10.0
        solver.parameters.num_search_workers = 4
        solver_status = solver.Solve(model)

        status_str = solver.StatusName(solver_status)
        logger.info(f"OR-Tools CP-SAT Solver Result: {status_str}")

        # Supersede any previous active schedules
        db.query(ProductionSchedule).filter(ProductionSchedule.status == "ACTIVE").update({"status": "SUPERSEDED"})

        schedule_records = []
        schedule_start_time = datetime.now(timezone.utc)
        total_makespan = 0.0

        if solver_status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            total_makespan = float(solver.Value(makespan))
            
            # Create persistent Schedule Record
            new_schedule = ProductionSchedule(
                schedule_name=f"Schedule-OPT-{schedule_start_time.strftime('%Y%m%d-%H%M')}",
                version=1,
                status="ACTIVE",
                total_makespan_hours=total_makespan,
                optimizer_status=status_str,
                schedule_metadata={"solver_status": status_str, "horizon_days": horizon_days, "conflicts": conflicts}
            )
            db.add(new_schedule)
            db.commit()
            db.refresh(new_schedule)

            # Persist each batch assignment
            assignments_list = []
            for b_idx, item in task_vars.items():
                start_h = solver.Value(item["start"])
                end_h = solver.Value(item["end"])
                b_start = schedule_start_time + timedelta(hours=start_h)
                b_end = schedule_start_time + timedelta(hours=end_h)

                assigned_mach = None
                for m_idx, lit in enumerate(item["mach_literals"]):
                    if solver.Value(lit) == 1:
                        assigned_mach = available_machines[m_idx]
                        break

                b_info = item["info"]
                order = b_info["order"]
                product = b_info["product"]

                # Upsert batch record to support dynamic rescheduling
                existing_batch = db.query(ProductionBatch).filter(
                    ProductionBatch.batch_number == b_info["batch_number"]
                ).first()

                if existing_batch:
                    batch = existing_batch
                    batch.machine_id = assigned_mach.id if assigned_mach else None
                    batch.schedule_id = new_schedule.id
                    batch.start_time = b_start
                    batch.end_time = b_end
                    batch.status = "SCHEDULED"
                    batch.notes = f"Assigned to {assigned_mach.machine_id if assigned_mach else 'N/A'}"
                else:
                    batch = ProductionBatch(
                        batch_number=b_info["batch_number"],
                        order_id=order.id,
                        product_id=product.id,
                        machine_id=assigned_mach.id if assigned_mach else None,
                        schedule_id=new_schedule.id,
                        quantity=product.batch_size,
                        start_time=b_start,
                        end_time=b_end,
                        status="SCHEDULED",
                        notes=f"Scheduled on {assigned_mach.machine_id if assigned_mach else 'N/A'}"
                    )
                    db.add(batch)

                order.status = "SCHEDULED"


                assignments_list.append({
                    "batch_number": batch.batch_number,
                    "order_code": order.order_code,
                    "product_name": product.product_name,
                    "machine_id": assigned_mach.machine_id if assigned_mach else "N/A",
                    "machine_name": assigned_mach.machine_name if assigned_mach else "N/A",
                    "start_time": b_start.strftime("%Y-%m-%d %H:%M"),
                    "end_time": b_end.strftime("%Y-%m-%d %H:%M"),
                    "duration_hours": b_info["duration_hours"],
                    "status": "SCHEDULED"
                })

            new_schedule.schedule_metadata = {
                "solver_status": status_str,
                "horizon_days": horizon_days,
                "conflicts": conflicts,
                "assignments": assignments_list
            }
            db.commit()
            db.refresh(new_schedule)
            return new_schedule
        else:
            new_schedule = ProductionSchedule(
                schedule_name=f"Schedule-Infeasible-{schedule_start_time.strftime('%Y%m%d-%H%M')}",
                version=1,
                status="DRAFT",
                total_makespan_hours=0.0,
                optimizer_status=status_str,
                schedule_metadata={"error": "Constraint satisfaction failed (over-constrained).", "conflicts": conflicts}
            )
            db.add(new_schedule)
            db.commit()
            return new_schedule

    @staticmethod
    def automatic_reschedule_on_machine_incident(
        db: Session,
        degraded_machine_id: str,
        incident_reason: str
    ) -> Optional[ScheduleRevision]:
        """
        Automatic Dynamic Rescheduling Trigger:
        When a machine health drops to CRITICAL or enters MAINTENANCE:
        1. Identifies active schedule and affected batches.
        2. Re-runs OR-Tools scheduler with degraded machine excluded.
        3. Generates a new versioned schedule revision with the exact cause recorded.
        """
        machine = db.query(Machine).filter(
            (Machine.id == degraded_machine_id) | (Machine.machine_id == degraded_machine_id)
        ).first()
        if not machine:
            return None

        # 1. Find currently active schedule
        active_schedule = db.query(ProductionSchedule).filter(
            ProductionSchedule.status == "ACTIVE"
        ).first()

        if not active_schedule:
            logger.info("No active schedule found to revise.")
            return None

        # 2. Check if this machine has assigned batches in active schedule
        affected_batches = db.query(ProductionBatch).filter(
            ProductionBatch.schedule_id == active_schedule.id,
            ProductionBatch.machine_id == machine.id,
            ProductionBatch.status.in_(["PLANNED", "SCHEDULED", "IN_PROGRESS"])
        ).all()

        logger.warning(
            f"Dynamic Rescheduler triggered for Machine {machine.machine_id}! "
            f"Found {len(affected_batches)} affected batches. Reason: {incident_reason}"
        )

        # 3. Create scheduling conflict alert
        AlertService.create_alert(db, AlertCreate(
            machine_id=machine.id,
            alert_type="SCHEDULING_CONFLICT",
            severity="CRITICAL",
            title=f"Automatic Reschedule: {machine.machine_id} Degraded",
            message=f"{incident_reason}. System is rerunning optimization to reassign {len(affected_batches)} impacted batches."
        ))

        # 4. Mark affected batches back to PLANNED for re-optimization
        for b in affected_batches:
            b.machine_id = None
            b.status = "PLANNED"
        db.commit()

        # 5. Rerun OR-Tools optimizer
        revised_schedule = ProductionSchedulerService.generate_schedule(db, horizon_days=7)

        # 6. Create immutable Schedule Revision audit record
        next_rev_num = len(active_schedule.revisions) + 1
        revision = ScheduleRevision(
            schedule_id=revised_schedule.id,
            revision_number=next_rev_num,
            trigger_event="MACHINE_DEGRADATION",
            reason=incident_reason,
            changes_summary={
                "degraded_machine": machine.machine_id,
                "reassigned_batches_count": len(affected_batches),
                "affected_batch_numbers": [b.batch_number for b in affected_batches],
                "previous_schedule_id": active_schedule.id,
                "revised_schedule_id": revised_schedule.id
            },
            created_at=datetime.now(timezone.utc)
        )
        db.add(revision)
        db.commit()
        db.refresh(revision)

        logger.info(f"Generated Schedule Revision #{revision.revision_number} successfully.")
        return revision
