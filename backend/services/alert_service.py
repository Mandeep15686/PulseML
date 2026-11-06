"""Creates and resolves alerts based on drift reports."""
from __future__ import annotations
import uuid
from sqlalchemy.orm import Session
from backend.models.orm import Alert, AlertSeverity, DriftReport


class AlertService:

    @staticmethod
    def create_alerts_from_report(db: Session, report: DriftReport) -> list[Alert]:
        alerts = []

        # Prediction drift alerts
        pred = report.prediction_drift or {}
        for method, result in pred.items():
            if isinstance(result, dict) and result.get("drifted"):
                severity = AlertSeverity.HIGH if result.get("severity") == "critical" else AlertSeverity.MEDIUM
                alert = Alert(
                    id         = str(uuid.uuid4()),
                    model_id   = report.model_id,
                    severity   = severity,
                    drift_type = "prediction_drift",
                    message    = f"Prediction distribution drift detected ({method}): "
                                 f"{result.get('statistic') or result.get('psi') or '—'}",
                    feature    = None,
                )
                alerts.append(alert)

        # Performance drift alerts
        perf = report.performance_drift or {}
        for metric, v in perf.get("metrics", {}).items():
            if v.get("drifted"):
                alert = Alert(
                    id         = str(uuid.uuid4()),
                    model_id   = report.model_id,
                    severity   = AlertSeverity.HIGH,
                    drift_type = "performance_drift",
                    message    = f"Performance degradation: {metric} dropped {v['drop_pct']:.1f}% "
                                 f"({v['reference']:.4f} → {v['current']:.4f})",
                    feature    = metric,
                )
                alerts.append(alert)

        for alert in alerts:
            db.add(alert)
        db.commit()
        return alerts

    @staticmethod
    def resolve_alert(db: Session, alert_id: str) -> Alert | None:
        from datetime import datetime
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            return None
        alert.is_resolved = True
        alert.resolved_at = datetime.utcnow()
        db.commit()
        db.refresh(alert)
        return alert
