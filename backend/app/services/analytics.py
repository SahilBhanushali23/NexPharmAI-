from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.machine import Machine, MachineReading, MachinePrediction, AnomalyPrediction, MachineHealthHistory
from app.models.production import ProductionOrder, ProductionBatch, ProductionSchedule
from app.models.maintenance import MaintenanceRecord
from app.models.quality import QualityPrediction
from app.models.inventory import InventoryMaterial, InventoryTransaction
from app.models.alert import Alert

class AnalyticsService:
    @staticmethod
    def get_dashboard_summary(db: Session) -> Dict[str, Any]:
        # 1. Machine Counts by status
        machines = db.query(Machine).all()
        total_machines = len(machines)
        running_machines = sum(1 for m in machines if m.status == "RUNNING")
        warning_machines = sum(1 for m in machines if m.status == "WARNING")
        critical_machines = sum(1 for m in machines if m.status == "CRITICAL")
        maintenance_machines = sum(1 for m in machines if m.status == "MAINTENANCE")
        idle_machines = sum(1 for m in machines if m.status == "IDLE")

        # 2. Plant OEE Calculation
        # Availability: Ratio of operating machines vs total active machines
        total_active = total_machines if total_machines > 0 else 1
        availability = max(0.0, min(1.0, (running_machines + idle_machines) / total_active))

        # Performance: Efficiency based on recent sensor speeds vs baseline (1500 rpm)
        recent_readings = db.query(MachineReading).order_by(MachineReading.timestamp.desc()).limit(100).all()
        if recent_readings:
            avg_rpm = sum(r.rotational_speed for r in recent_readings) / len(recent_readings)
            performance = max(0.5, min(1.0, avg_rpm / 1550.0))
        else:
            performance = 0.95

        # Quality: Pass rate of inspected batches
        quality_records = db.query(QualityPrediction).all()
        if quality_records:
            pass_count = sum(1 for q in quality_records if q.status == "PASS")
            quality_rate = pass_count / len(quality_records)
        else:
            quality_rate = 0.98

        overall_oee = round(availability * performance * quality_rate * 100, 1)

        # 3. Alerts
        active_alerts = db.query(Alert).filter(Alert.is_resolved == False).all()
        critical_alerts = sum(1 for a in active_alerts if a.severity == "CRITICAL")

        # 4. Batches & Orders
        total_orders = db.query(ProductionOrder).count()
        completed_orders = db.query(ProductionOrder).filter(ProductionOrder.status == "COMPLETED").count()
        total_batches = db.query(ProductionBatch).count()
        running_batches = db.query(ProductionBatch).filter(ProductionBatch.status == "IN_PROGRESS").count()

        # 5. Inventory Low Stock
        low_stock_count = db.query(InventoryMaterial).filter(
            InventoryMaterial.quantity <= InventoryMaterial.reorder_level
        ).count()

        # 6. Failure & Anomaly Rates
        total_predictions = db.query(MachinePrediction).count()
        failure_predictions = db.query(MachinePrediction).filter(MachinePrediction.prediction == 1).count()
        failure_rate = round((failure_predictions / total_predictions * 100), 1) if total_predictions > 0 else 0.0

        total_anomalies = db.query(AnomalyPrediction).count()
        detected_anomalies = db.query(AnomalyPrediction).filter(AnomalyPrediction.anomaly_detected == 1).count()
        anomaly_rate = round((detected_anomalies / total_anomalies * 100), 1) if total_anomalies > 0 else 0.0

        return {
            "machines": {
                "total": total_machines,
                "running": running_machines,
                "warning": warning_machines,
                "critical": critical_machines,
                "maintenance": maintenance_machines,
                "idle": idle_machines
            },
            "oee": {
                "overall": overall_oee,
                "availability": round(availability * 100, 1),
                "performance": round(performance * 100, 1),
                "quality": round(quality_rate * 100, 1)
            },
            "production": {
                "total_orders": total_orders,
                "completed_orders": completed_orders,
                "total_batches": total_batches,
                "running_batches": running_batches
            },
            "alerts": {
                "active_total": len(active_alerts),
                "critical": critical_alerts
            },
            "inventory": {
                "low_stock_warnings": low_stock_count
            },
            "reliability": {
                "failure_rate": failure_rate,
                "anomaly_rate": anomaly_rate
            }
        }

    @staticmethod
    def get_machine_oee(db: Session, machine_id: str) -> Dict[str, Any]:
        machine = db.query(Machine).filter(
            (Machine.id == machine_id) | (Machine.machine_id == machine_id)
        ).first()
        if not machine:
            return {}

        # Machine availability
        is_avail = 1.0 if machine.status in ["RUNNING", "IDLE"] else (0.2 if machine.status == "WARNING" else 0.0)

        # Performance from latest reading
        latest_reading = db.query(MachineReading).filter(
            MachineReading.machine_id == machine.id
        ).order_by(MachineReading.timestamp.desc()).first()

        performance = 0.95
        if latest_reading:
            performance = max(0.5, min(1.0, latest_reading.rotational_speed / 1550.0))

        # Quality rate
        batches = db.query(ProductionBatch).filter(ProductionBatch.machine_id == machine.id).all()
        quality_rate = 0.98

        oee = round(is_avail * performance * quality_rate * 100, 1)

        return {
            "machine_id": machine.machine_id,
            "machine_name": machine.machine_name,
            "status": machine.status,
            "oee": oee,
            "availability": round(is_avail * 100, 1),
            "performance": round(performance * 100, 1),
            "quality": round(quality_rate * 100, 1)
        }
