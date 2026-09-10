from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.alert import Alert
from app.schemas.alert import AlertCreate
from app.utils.logger import logger

class AlertService:
    @staticmethod
    def create_alert(
        db: Session,
        alert_in: AlertCreate
    ) -> Alert:
        # Check if an unresolved identical alert already exists to prevent spam
        existing = db.query(Alert).filter(
            Alert.machine_id == alert_in.machine_id,
            Alert.alert_type == alert_in.alert_type,
            Alert.is_resolved == False
        ).first()

        if existing:
            # Upgrade severity if higher
            severity_ranks = {"INFO": 0, "WARNING": 1, "HIGH": 2, "CRITICAL": 3}
            if severity_ranks.get(alert_in.severity, 0) > severity_ranks.get(existing.severity, 0):
                existing.severity = alert_in.severity
                existing.message = alert_in.message
                db.commit()
                db.refresh(existing)
            return existing

        alert = Alert(
            machine_id=alert_in.machine_id,
            alert_type=alert_in.alert_type,
            severity=alert_in.severity,
            title=alert_in.title,
            message=alert_in.message,
            created_at=datetime.now(timezone.utc)
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        logger.warning(f"Generated [{alert.severity}] alert for Machine {alert.machine_id}: {alert.title}")
        return alert

    @staticmethod
    def get_alerts(
        db: Session,
        machine_id: Optional[str] = None,
        severity: Optional[str] = None,
        alert_type: Optional[str] = None,
        is_resolved: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Alert]:
        query = db.query(Alert)
        if machine_id:
            query = query.filter(Alert.machine_id == machine_id)
        if severity:
            query = query.filter(Alert.severity == severity.upper())
        if alert_type:
            query = query.filter(Alert.alert_type == alert_type.upper())
        if is_resolved is not None:
            query = query.filter(Alert.is_resolved == is_resolved)
        return query.order_by(Alert.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def acknowledge_alert(db: Session, alert_id: str, user_id: str) -> Alert:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            return None
        alert.is_acknowledged = True
        alert.acknowledged_by = user_id
        alert.acknowledged_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(alert)
        return alert

    @staticmethod
    def resolve_alert(db: Session, alert_id: str, user_id: str) -> Alert:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            return None
        alert.is_resolved = True
        alert.resolved_by = user_id
        alert.resolved_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(alert)
        return alert
