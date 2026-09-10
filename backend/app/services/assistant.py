from typing import Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.machine import Machine, MachinePrediction, AnomalyPrediction, MachineHealthHistory
from app.models.maintenance import MaintenanceRecord
from app.models.inventory import InventoryMaterial
from app.models.production import ProductionSchedule, ProductionBatch, ProductionOrder, ScheduleRevision
from app.models.alert import Alert
from app.core.config import settings
from app.utils.logger import logger

class DecisionAssistantService:
    @staticmethod
    def answer_query(db: Session, query_text: str) -> Dict[str, Any]:
        q = query_text.lower().strip()
        data_context = {}
        answer = ""

        # 1. "Which machine has the highest failure risk?" / "failure risk"
        if "highest failure risk" in q or "failure risk" in q or "highest risk" in q:
            highest_pred = db.query(MachinePrediction).order_by(MachinePrediction.failure_probability.desc()).first()
            if highest_pred:
                machine = db.query(Machine).filter(Machine.id == highest_pred.machine_id).first()
                mach_id = machine.machine_id if machine else highest_pred.machine_id
                answer = (
                    f"Machine **{mach_id}** currently has the highest failure risk at "
                    f"**{highest_pred.failure_percentage}%** (Failure Probability: {highest_pred.failure_probability}), "
                    f"evaluated by the {highest_pred.model_name} model. Machine status is currently **{machine.status if machine else 'UNKNOWN'}**."
                )
                data_context = {
                    "machine_id": mach_id,
                    "failure_percentage": highest_pred.failure_percentage,
                    "status": machine.status if machine else "UNKNOWN"
                }
            else:
                answer = "No failure risk predictions have been generated yet. Telemetry readings are needed."

        # 2. "Which machines need maintenance?" / "maintenance"
        elif "need maintenance" in q or "needs maintenance" in q or "pending maintenance" in q:
            unhealthy_machines = db.query(Machine).filter(Machine.status.in_(["WARNING", "CRITICAL", "MAINTENANCE"])).all()
            pending_maint = db.query(MaintenanceRecord).filter(MaintenanceRecord.status == "PENDING").all()
            
            mach_names = [f"**{m.machine_id}** ({m.machine_name} - Status: {m.status})" for m in unhealthy_machines]
            if mach_names:
                answer = (
                    f"The following machines require maintenance attention based on real-time health telemetry:\n"
                    f"- " + "\n- ".join(mach_names) + "\n\n"
                    f"There are currently **{len(pending_maint)}** scheduled pending work orders in the system."
                )
                data_context = {"unhealthy_machines": [m.machine_id for m in unhealthy_machines]}
            else:
                answer = "All machines are currently operating in normal healthy state (RUNNING/IDLE) with no critical maintenance flags."

        # 3. "Which machines are currently available?" / "available"
        elif "available" in q or "machine availability" in q:
            available = db.query(Machine).filter(Machine.status.in_(["RUNNING", "IDLE"])).all()
            if available:
                lines = [f"- **{m.machine_id}** ({m.machine_name}, Line: {m.production_line}, Status: {m.status})" for m in available]
                answer = f"Currently, **{len(available)}** machines are available for production:\n" + "\n".join(lines)
                data_context = {"available_machines": [m.machine_id for m in available]}
            else:
                answer = "No machines are currently available. All units are either in MAINTENANCE, OFFLINE, or CRITICAL state."

        # 4. "Why was the schedule changed?" / "reschedule" / "revision"
        elif "schedule changed" in q or "reschedule" in q or "revision" in q or "why was" in q:
            latest_revision = db.query(ScheduleRevision).order_by(ScheduleRevision.created_at.desc()).first()
            if latest_revision:
                answer = (
                    f"The schedule was automatically updated under **Revision #{latest_revision.revision_number}**.\n\n"
                    f"**Trigger Event**: `{latest_revision.trigger_event}`\n"
                    f"**Audit Justification**: \"{latest_revision.reason}\"\n"
                    f"**Timestamp**: {latest_revision.created_at.strftime('%Y-%m-%d %H:%M UTC')}"
                )
                data_context = latest_revision.changes_summary or {}
            else:
                answer = "No dynamic schedule revisions have been triggered yet. The primary baseline schedule is currently active."

        # 5. "What materials are low?" / "inventory" / "low stock"
        elif "materials" in q or "low stock" in q or "shortage" in q:
            low_materials = db.query(InventoryMaterial).filter(
                InventoryMaterial.quantity <= InventoryMaterial.reorder_level
            ).all()
            if low_materials:
                lines = [
                    f"- **{m.material_name}** (`{m.material_code}`): Current Stock = **{m.quantity} {m.unit}** (Reorder Threshold: {m.reorder_level} {m.unit})"
                    for m in low_materials
                ]
                answer = f"The following **{len(low_materials)}** materials have fallen below safety reorder levels:\n" + "\n".join(lines)
                data_context = {"low_materials": [m.material_code for m in low_materials]}
            else:
                answer = "All registered pharmaceutical raw materials and excipients are currently adequately stocked above safety thresholds."

        # 6. "What is today's production schedule?" / "schedule"
        elif "production schedule" in q or "today's schedule" in q or "schedule" in q:
            active_sched = db.query(ProductionSchedule).filter(ProductionSchedule.status == "ACTIVE").first()
            if active_sched and active_sched.schedule_metadata and "assignments" in active_sched.schedule_metadata:
                assignments = active_sched.schedule_metadata["assignments"]
                lines = [
                    f"- Batch **{a.get('batch_number')}** ({a.get('product_name')}): Assigned to **{a.get('machine_id')}**, Window: {a.get('start_time')} to {a.get('end_time')}"
                    for a in assignments[:5]
                ]
                answer = (
                    f"Active schedule: **{active_sched.schedule_name}** (Makespan: {active_sched.total_makespan_hours}h, Status: {active_sched.optimizer_status}).\n"
                    f"Scheduled jobs:\n" + "\n".join(lines)
                )
                if len(assignments) > 5:
                    answer += f"\n*(and {len(assignments) - 5} more batches scheduled)*"
                data_context = {"schedule_id": active_sched.id, "total_batches": len(assignments)}
            else:
                answer = "No active production schedule is currently generated. You can trigger optimization from the Scheduler module."

        # 7. "What anomalies happened?" / "anomalies"
        elif "anomal" in q:
            anomalies = db.query(AnomalyPrediction).filter(AnomalyPrediction.anomaly_detected == 1).order_by(AnomalyPrediction.timestamp.desc()).limit(5).all()
            if anomalies:
                lines = [
                    f"- Machine **{a.machine_id}** at {a.timestamp.strftime('%H:%M:%S')}: Severity = **{a.severity}** (Score: {a.anomaly_score})"
                    for a in anomalies
                ]
                answer = f"Found **{len(anomalies)}** recent mechanical anomalies detected by Isolation Forest:\n" + "\n".join(lines)
                data_context = {"anomaly_count": len(anomalies)}
            else:
                answer = "No mechanical anomalies have been detected. All sensor vectors are within normal multivariate tolerances."

        # 8. "Which production orders are delayed?" / "orders"
        elif "delayed" in q or "orders" in q:
            orders = db.query(ProductionOrder).filter(ProductionOrder.status.in_(["PLANNED", "ON_HOLD"])).all()
            if orders:
                lines = [
                    f"- Order **{o.order_code}**: Status = `{o.status}`, Priority = {o.priority}, Due: {o.due_date.strftime('%Y-%m-%d')}"
                    for o in orders
                ]
                answer = f"Current pending / held production orders:\n" + "\n".join(lines)
                data_context = {"orders_count": len(orders)}
            else:
                answer = "All production orders are on track and scheduled."

        # Default fallback intelligent responder querying live counts
        else:
            total_m = db.query(Machine).count()
            running_m = db.query(Machine).filter(Machine.status == "RUNNING").count()
            active_alerts = db.query(Alert).filter(Alert.is_resolved == False).count()
            answer = (
                f"I am the NexPharmAI Operations Intelligence Assistant. "
                f"I am connected live to your factory database containing **{total_m}** machines ({running_m} running) "
                f"and **{active_alerts}** active alerts.\n\n"
                f"You can ask me questions such as:\n"
                f"- *'Which machine has the highest failure risk?'*\n"
                f"- *'Which machines need maintenance?'*\n"
                f"- *'Which machines are currently available?'*\n"
                f"- *'Why was the schedule changed?'*\n"
                f"- *'What materials are low?'*\n"
                f"- *'What is today's production schedule?'*"
            )

        return {
            "query": query_text,
            "answer": answer,
            "data_context": data_context,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
