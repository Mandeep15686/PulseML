"""SQLAlchemy ORM models."""
from __future__ import annotations
import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean,
    ForeignKey, Text, Enum as SAEnum, JSON
)
from sqlalchemy.orm import relationship
from backend.database import Base


class TaskType(str, enum.Enum):
    BINARY_CLASSIFICATION = "binary_classification"
    MULTICLASS_CLASSIFICATION = "multiclass_classification"
    REGRESSION = "regression"


class DriftStatus(str, enum.Enum):
    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class AlertSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ModelRegistry(Base):
    __tablename__ = "model_registry"

    id          = Column(String(36), primary_key=True)
    name        = Column(String(128), nullable=False, unique=True)
    version     = Column(String(32), nullable=False, default="1.0.0")
    description = Column(Text, nullable=True)
    task_type   = Column(SAEnum(TaskType), nullable=False)
    feature_names = Column(JSON, nullable=False, default=list)
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active   = Column(Boolean, default=True)

    prediction_logs = relationship("PredictionLog", back_populates="model", cascade="all, delete-orphan")
    drift_reports   = relationship("DriftReport",   back_populates="model", cascade="all, delete-orphan")
    alerts          = relationship("Alert",          back_populates="model", cascade="all, delete-orphan")


class PredictionLog(Base):
    __tablename__ = "prediction_logs"

    id              = Column(String(36), primary_key=True)
    model_id        = Column(String(36), ForeignKey("model_registry.id", ondelete="CASCADE"), nullable=False)
    window_label    = Column(String(64), nullable=False)
    logged_at       = Column(DateTime, default=datetime.utcnow)
    n_samples       = Column(Integer, nullable=False)
    features_stats  = Column(JSON, nullable=False, default=dict)   # {feature: {mean, std, min, max, p25, p75}}
    prediction_dist = Column(JSON, nullable=False, default=dict)   # {bucket: count}
    label_dist      = Column(JSON, nullable=True, default=dict)    # {label: count} — optional
    performance     = Column(JSON, nullable=True, default=dict)    # {accuracy, auc, f1, ...}
    raw_predictions = Column(JSON, nullable=True, default=list)    # sampled scores (up to 500)
    raw_labels      = Column(JSON, nullable=True, default=list)    # sampled labels

    model = relationship("ModelRegistry", back_populates="prediction_logs")


class DriftReport(Base):
    __tablename__ = "drift_reports"

    id              = Column(String(36), primary_key=True)
    model_id        = Column(String(36), ForeignKey("model_registry.id", ondelete="CASCADE"), nullable=False)
    reference_window= Column(String(64), nullable=False)
    target_window   = Column(String(64), nullable=False)
    generated_at    = Column(DateTime, default=datetime.utcnow)
    overall_status  = Column(SAEnum(DriftStatus), default=DriftStatus.UNKNOWN)
    feature_drift   = Column(JSON, nullable=False, default=dict)
    prediction_drift= Column(JSON, nullable=False, default=dict)
    performance_drift= Column(JSON, nullable=True, default=dict)
    summary         = Column(Text, nullable=True)

    model = relationship("ModelRegistry", back_populates="drift_reports")


class Alert(Base):
    __tablename__ = "alerts"

    id          = Column(String(36), primary_key=True)
    model_id    = Column(String(36), ForeignKey("model_registry.id", ondelete="CASCADE"), nullable=False)
    severity    = Column(SAEnum(AlertSeverity), nullable=False)
    message     = Column(Text, nullable=False)
    drift_type  = Column(String(64), nullable=False)
    feature     = Column(String(128), nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)

    model = relationship("ModelRegistry", back_populates="alerts")
