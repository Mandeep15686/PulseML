"""Pydantic v2 request/response schemas."""
from __future__ import annotations
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator
from backend.models.orm import TaskType, DriftStatus, AlertSeverity


# ── Model Registry ────────────────────────────────────────────────────────────

class ModelCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    version: str = Field("1.0.0", max_length=32)
    description: Optional[str] = None
    task_type: TaskType
    feature_names: list[str] = Field(default_factory=list)

class ModelUpdate(BaseModel):
    description: Optional[str] = None
    version: Optional[str] = None
    is_active: Optional[bool] = None

class ModelOut(BaseModel):
    id: str
    name: str
    version: str
    description: Optional[str]
    task_type: TaskType
    feature_names: list[str]
    created_at: datetime
    updated_at: datetime
    is_active: bool
    model_config = {"from_attributes": True}


# ── Prediction Log ────────────────────────────────────────────────────────────

class PredictionLogCreate(BaseModel):
    window_label: str = Field(..., min_length=1, max_length=64,
        description="Human-readable label, e.g. '2024-W01' or 'batch-42'")
    predictions: list[float] = Field(..., min_length=1,
        description="Raw prediction scores (0–1 for classification)")
    labels: Optional[list[int]] = Field(None,
        description="Ground-truth labels (optional)")
    features: Optional[dict[str, list[float]]] = Field(None,
        description="Feature vectors: {feature_name: [val1, val2, ...]}")

    @field_validator("predictions")
    @classmethod
    def validate_preds(cls, v: list[float]) -> list[float]:
        if any(not (0.0 <= x <= 1.0) for x in v):
            raise ValueError("Predictions must be in [0, 1]")
        return v

class PredictionLogOut(BaseModel):
    id: str
    model_id: str
    window_label: str
    logged_at: datetime
    n_samples: int
    features_stats: dict[str, Any]
    prediction_dist: dict[str, Any]
    label_dist: Optional[dict[str, Any]]
    performance: Optional[dict[str, Any]]
    model_config = {"from_attributes": True}


# ── Drift Report ──────────────────────────────────────────────────────────────

class DriftReportOut(BaseModel):
    id: str
    model_id: str
    reference_window: str
    target_window: str
    generated_at: datetime
    overall_status: DriftStatus
    feature_drift: dict[str, Any]
    prediction_drift: dict[str, Any]
    performance_drift: Optional[dict[str, Any]]
    summary: Optional[str]
    model_config = {"from_attributes": True}


# ── Alert ─────────────────────────────────────────────────────────────────────

class AlertOut(BaseModel):
    id: str
    model_id: str
    severity: AlertSeverity
    message: str
    drift_type: str
    feature: Optional[str]
    created_at: datetime
    is_resolved: bool
    resolved_at: Optional[datetime]
    model_config = {"from_attributes": True}


# ── Dashboard summary ─────────────────────────────────────────────────────────

class ModelSummary(BaseModel):
    model: ModelOut
    n_logs: int
    n_reports: int
    n_open_alerts: int
    latest_status: DriftStatus
    latest_window: Optional[str]


class DashboardOut(BaseModel):
    total_models: int
    active_models: int
    total_alerts: int
    open_alerts: int
    critical_models: int
    models: list[ModelSummary]
