"""Prediction log upload and retrieval endpoints."""
from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.orm import ModelRegistry, PredictionLog
from backend.schemas.schemas import PredictionLogCreate, PredictionLogOut
from backend.ml_engine.metrics import (
    compute_feature_stats, compute_prediction_distribution,
    compute_label_distribution, compute_performance_metrics,
)
from backend.services.drift_service import DriftService
from backend.services.alert_service import AlertService

router = APIRouter(prefix="/models/{model_id}/logs", tags=["Prediction Logs"])


def _get_model_or_404(model_id: str, db: Session) -> ModelRegistry:
    model = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found.")
    return model


@router.post("/", response_model=PredictionLogOut, status_code=status.HTTP_201_CREATED)
def upload_log(
    model_id: str,
    payload: PredictionLogCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    model = _get_model_or_404(model_id, db)

    # Check duplicate window
    existing = db.query(PredictionLog).filter(
        PredictionLog.model_id == model_id,
        PredictionLog.window_label == payload.window_label,
    ).first()
    if existing:
        raise HTTPException(status_code=409,
            detail=f"Log for window '{payload.window_label}' already exists.")

    # Compute stats
    features_stats = {}
    if payload.features:
        for feat, vals in payload.features.items():
            features_stats[feat] = compute_feature_stats(vals)

    pred_dist = compute_prediction_distribution(payload.predictions)
    label_dist = compute_label_distribution(payload.labels) if payload.labels else {}
    performance = {}
    if payload.labels and len(payload.labels) == len(payload.predictions):
        performance = compute_performance_metrics(
            payload.predictions, payload.labels, model.task_type.value
        )

    log = PredictionLog(
        id              = str(uuid.uuid4()),
        model_id        = model_id,
        window_label    = payload.window_label,
        n_samples       = len(payload.predictions),
        features_stats  = features_stats,
        prediction_dist = pred_dist,
        label_dist      = label_dist or None,
        performance     = performance or None,
        raw_predictions = payload.predictions[:500],
        raw_labels      = (payload.labels[:500] if payload.labels else None),
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    # Auto-run drift if a previous log exists
    background_tasks.add_task(_auto_drift, model_id, log.id, db)

    return log


def _auto_drift(model_id: str, new_log_id: str, db: Session):
    """Background task: compare new log against the previous one."""
    try:
        db2 = next(get_db())
        model = db2.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
        new_log = db2.query(PredictionLog).filter(PredictionLog.id == new_log_id).first()
        if not model or not new_log:
            return

        prev_log = (
            db2.query(PredictionLog)
               .filter(PredictionLog.model_id == model_id, PredictionLog.id != new_log_id)
               .order_by(PredictionLog.logged_at.desc())
               .first()
        )
        if not prev_log:
            return

        report = DriftService.run_drift_analysis(db2, model, prev_log, new_log)
        AlertService.create_alerts_from_report(db2, report)
    except Exception:
        pass


@router.get("/", response_model=list[PredictionLogOut])
def list_logs(model_id: str, db: Session = Depends(get_db)):
    _get_model_or_404(model_id, db)
    return (
        db.query(PredictionLog)
          .filter(PredictionLog.model_id == model_id)
          .order_by(PredictionLog.logged_at.asc())
          .all()
    )


@router.get("/{log_id}", response_model=PredictionLogOut)
def get_log(model_id: str, log_id: str, db: Session = Depends(get_db)):
    _get_model_or_404(model_id, db)
    log = db.query(PredictionLog).filter(
        PredictionLog.id == log_id, PredictionLog.model_id == model_id
    ).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found.")
    return log


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_log(model_id: str, log_id: str, db: Session = Depends(get_db)):
    _get_model_or_404(model_id, db)
    log = db.query(PredictionLog).filter(
        PredictionLog.id == log_id, PredictionLog.model_id == model_id
    ).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found.")
    db.delete(log)
    db.commit()
