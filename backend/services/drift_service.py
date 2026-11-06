"""Orchestrates drift analysis and persists reports."""
from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from backend.models.orm import PredictionLog, DriftReport, ModelRegistry
from backend.ml_engine.drift_detectors import DriftDetector


class DriftService:

    @staticmethod
    def run_drift_analysis(
        db: Session,
        model: ModelRegistry,
        reference_log: PredictionLog,
        target_log: PredictionLog,
    ) -> DriftReport:
        """Run full drift analysis and persist report."""
        result = DriftDetector.full_report(reference_log, target_log, model.feature_names)

        report = DriftReport(
            id               = str(uuid.uuid4()),
            model_id         = model.id,
            reference_window = reference_log.window_label,
            target_window    = target_log.window_label,
            overall_status   = result["overall_status"],
            feature_drift    = result["feature_drift"],
            prediction_drift = result["prediction_drift"],
            performance_drift= result["performance_drift"],
            summary          = DriftService._build_summary(result),
        )

        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    @staticmethod
    def _build_summary(result: dict) -> str:
        lines = [f"Overall status: {result['overall_status'].upper()}"]
        pred = result.get("prediction_drift", {})
        psi  = pred.get("psi", {})
        if psi.get("psi") is not None:
            lines.append(f"Prediction PSI: {psi['psi']:.4f} ({'DRIFT' if psi['drifted'] else 'OK'})")
        ks = pred.get("ks_test", {})
        if ks.get("statistic") is not None:
            lines.append(f"KS statistic: {ks['statistic']:.4f} (p={ks['p_value']:.4f})")
        perf = result.get("performance_drift", {})
        if perf.get("metrics"):
            for m, v in perf["metrics"].items():
                if v.get("drifted"):
                    lines.append(f"⚠ {m} dropped {v['drop_pct']:.1f}%")
        return " | ".join(lines)
