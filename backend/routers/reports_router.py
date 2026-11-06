"""Drift reports, alerts, and dashboard endpoints."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.orm import (
    ModelRegistry, PredictionLog, DriftReport, Alert, DriftStatus
)
from backend.schemas.schemas import (
    DriftReportOut, AlertOut, DashboardOut, ModelSummary, ModelOut
)
from backend.services.drift_service import DriftService
from backend.services.alert_service import AlertService

router = APIRouter(tags=["Reports & Alerts"])


# ── Drift Reports ─────────────────────────────────────────────────────────────

@router.post("/models/{model_id}/drift", response_model=DriftReportOut)
def trigger_drift(
    model_id: str,
    reference_window: str = Query(...),
    target_window: str    = Query(...),
    db: Session = Depends(get_db),
):
    """Manually trigger drift analysis between two specific windows."""
    model = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found.")

    ref_log = db.query(PredictionLog).filter(
        PredictionLog.model_id == model_id,
        PredictionLog.window_label == reference_window
    ).first()
    tgt_log = db.query(PredictionLog).filter(
        PredictionLog.model_id == model_id,
        PredictionLog.window_label == target_window
    ).first()

    if not ref_log:
        raise HTTPException(status_code=404, detail=f"Reference window '{reference_window}' not found.")
    if not tgt_log:
        raise HTTPException(status_code=404, detail=f"Target window '{target_window}' not found.")
    if reference_window == target_window:
        raise HTTPException(status_code=400, detail="Reference and target windows must differ.")

    report = DriftService.run_drift_analysis(db, model, ref_log, tgt_log)
    AlertService.create_alerts_from_report(db, report)
    return report


@router.get("/models/{model_id}/drift", response_model=list[DriftReportOut])
def list_drift_reports(model_id: str, db: Session = Depends(get_db)):
    db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first() or \
        (_ for _ in ()).throw(HTTPException(404, "Model not found."))
    return (
        db.query(DriftReport)
          .filter(DriftReport.model_id == model_id)
          .order_by(DriftReport.generated_at.desc())
          .all()
    )


@router.get("/models/{model_id}/drift/{report_id}", response_model=DriftReportOut)
def get_drift_report(model_id: str, report_id: str, db: Session = Depends(get_db)):
    report = db.query(DriftReport).filter(
        DriftReport.id == report_id, DriftReport.model_id == model_id
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    return report


# ── Alerts ────────────────────────────────────────────────────────────────────

@router.get("/models/{model_id}/alerts", response_model=list[AlertOut])
def list_alerts(
    model_id: str,
    resolved: bool = Query(False),
    db: Session = Depends(get_db),
):
    q = db.query(Alert).filter(Alert.model_id == model_id, Alert.is_resolved == resolved)
    return q.order_by(Alert.created_at.desc()).all()


@router.patch("/alerts/{alert_id}/resolve", response_model=AlertOut)
def resolve_alert(alert_id: str, db: Session = Depends(get_db)):
    alert = AlertService.resolve_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")
    return alert


@router.get("/alerts", response_model=list[AlertOut])
def list_all_alerts(
    resolved: bool = Query(False),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    return (
        db.query(Alert)
          .filter(Alert.is_resolved == resolved)
          .order_by(Alert.created_at.desc())
          .limit(limit)
          .all()
    )


# ── Dashboard ─────────────────────────────────────────────────────────────────

@router.get("/dashboard", response_model=DashboardOut)
def dashboard(db: Session = Depends(get_db)):
    models = db.query(ModelRegistry).order_by(ModelRegistry.created_at.desc()).all()
    total_alerts = db.query(Alert).count()
    open_alerts  = db.query(Alert).filter(Alert.is_resolved == False).count()

    summaries = []
    critical_count = 0

    for model in models:
        n_logs    = db.query(PredictionLog).filter(PredictionLog.model_id == model.id).count()
        n_reports = db.query(DriftReport).filter(DriftReport.model_id == model.id).count()
        n_open    = db.query(Alert).filter(Alert.model_id == model.id, Alert.is_resolved == False).count()

        latest_report = (
            db.query(DriftReport)
              .filter(DriftReport.model_id == model.id)
              .order_by(DriftReport.generated_at.desc())
              .first()
        )
        latest_status = latest_report.overall_status if latest_report else DriftStatus.UNKNOWN
        latest_window = latest_report.target_window if latest_report else None

        if latest_status == DriftStatus.CRITICAL:
            critical_count += 1

        latest_log = (
            db.query(PredictionLog)
              .filter(PredictionLog.model_id == model.id)
              .order_by(PredictionLog.logged_at.desc())
              .first()
        )

        summaries.append(ModelSummary(
            model          = ModelOut.model_validate(model),
            n_logs         = n_logs,
            n_reports      = n_reports,
            n_open_alerts  = n_open,
            latest_status  = latest_status,
            latest_window  = latest_window,
        ))

    return DashboardOut(
        total_models    = len(models),
        active_models   = sum(1 for m in models if m.is_active),
        total_alerts    = total_alerts,
        open_alerts     = open_alerts,
        critical_models = critical_count,
        models          = summaries,
    )
