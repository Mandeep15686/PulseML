"""
Core drift detection algorithms.

Implements:
  - KS Test        : continuous feature distribution shift
  - PSI            : prediction/feature population stability index
  - Chi-squared    : categorical or binned distribution shift
  - Wasserstein    : earth-mover distance for distribution comparison
  - Performance    : metric degradation detection
"""
from __future__ import annotations
import math
import numpy as np
from typing import Optional
from scipy import stats
from backend.config import settings


class DriftDetector:
    """Stateless drift detection engine — all methods are pure functions."""

    # ── KS Test ───────────────────────────────────────────────────────────────

    @staticmethod
    def ks_test(
        reference: list[float],
        current: list[float],
        threshold: float = None,
    ) -> dict:
        """
        Two-sample Kolmogorov-Smirnov test for continuous distributions.
        Returns statistic, p-value, drifted flag.
        """
        threshold = threshold or settings.KS_DRIFT_THRESHOLD
        ref = np.array(reference, dtype=float)
        cur = np.array(current, dtype=float)
        ref = ref[~np.isnan(ref)]
        cur = cur[~np.isnan(cur)]

        if len(ref) < settings.MIN_SAMPLES or len(cur) < settings.MIN_SAMPLES:
            return {"status": "insufficient_data", "statistic": None, "p_value": None, "drifted": False}

        stat, p_value = stats.ks_2samp(ref, cur)
        drifted = bool(stat > threshold)

        return {
            "method": "ks_test",
            "statistic": float(stat),
            "p_value": float(p_value),
            "threshold": threshold,
            "drifted": drifted,
            "severity": DriftDetector._severity(stat, threshold),
        }

    # ── PSI ───────────────────────────────────────────────────────────────────

    @staticmethod
    def psi(
        reference_dist: dict[str, int],
        current_dist: dict[str, int],
        threshold: float = None,
    ) -> dict:
        """
        Population Stability Index.
        PSI < 0.1  : no drift
        PSI < 0.2  : moderate drift (warning)
        PSI >= 0.2 : significant drift (critical)
        """
        threshold = threshold or settings.PSI_DRIFT_THRESHOLD
        buckets = set(reference_dist) | set(current_dist)
        ref_total = sum(reference_dist.values()) or 1
        cur_total = sum(current_dist.values())   or 1

        psi_value = 0.0
        per_bucket = {}
        for bucket in buckets:
            ref_pct = (reference_dist.get(bucket, 0) + 1e-6) / ref_total
            cur_pct = (current_dist.get(bucket, 0)  + 1e-6) / cur_total
            contribution = (cur_pct - ref_pct) * math.log(cur_pct / ref_pct)
            psi_value += contribution
            per_bucket[bucket] = round(contribution, 6)

        drifted = bool(psi_value > threshold)

        return {
            "method": "psi",
            "psi": float(psi_value),
            "threshold": threshold,
            "drifted": drifted,
            "severity": DriftDetector._severity(psi_value, threshold, [0.1, 0.2]),
            "per_bucket": per_bucket,
        }

    # ── Chi-Squared ───────────────────────────────────────────────────────────

    @staticmethod
    def chi_squared(
        reference_dist: dict[str, int],
        current_dist: dict[str, int],
        pvalue_threshold: float = None,
    ) -> dict:
        """Chi-squared test of homogeneity between two categorical distributions."""
        pvalue_threshold = pvalue_threshold or settings.CHISQ_PVALUE_THRESHOLD
        buckets = sorted(set(reference_dist) | set(current_dist))
        ref = np.array([reference_dist.get(b, 0) for b in buckets], dtype=float)
        cur = np.array([current_dist.get(b, 0)  for b in buckets], dtype=float)

        if ref.sum() == 0 or cur.sum() == 0:
            return {"status": "insufficient_data", "drifted": False}

        # Normalise current to same total as reference for chi-sq
        cur_scaled = cur * (ref.sum() / cur.sum())

        # Remove zero-expected cells
        mask = ref > 0
        if mask.sum() < 2:
            return {"status": "insufficient_data", "drifted": False}

        stat, p_value = stats.chisquare(cur_scaled[mask], f_exp=ref[mask])
        drifted = bool(p_value < pvalue_threshold)

        return {
            "method": "chi_squared",
            "statistic": float(stat),
            "p_value": float(p_value),
            "threshold": pvalue_threshold,
            "drifted": drifted,
            "severity": "critical" if p_value < 0.01 else ("warning" if drifted else "ok"),
        }

    # ── Wasserstein Distance ──────────────────────────────────────────────────

    @staticmethod
    def wasserstein(reference: list[float], current: list[float]) -> dict:
        """Earth-mover distance — scale-independent distributional similarity."""
        ref = np.array(reference, dtype=float)
        cur = np.array(current, dtype=float)
        ref = ref[~np.isnan(ref)]
        cur = cur[~np.isnan(cur)]

        if len(ref) < 10 or len(cur) < 10:
            return {"status": "insufficient_data", "distance": None}

        distance = float(stats.wasserstein_distance(ref, cur))
        # Normalise by reference range
        ref_range = float(np.max(ref) - np.min(ref)) or 1.0
        normalised = distance / ref_range

        return {
            "method": "wasserstein",
            "distance": distance,
            "normalised_distance": normalised,
            "drifted": normalised > 0.1,
        }

    # ── Performance Drift ─────────────────────────────────────────────────────

    @staticmethod
    def performance_drift(
        reference_metrics: dict,
        current_metrics: dict,
        drop_threshold: float = None,
    ) -> dict:
        """
        Detect degradation in model performance metrics.
        Flags if any key metric drops by more than drop_threshold (relative).
        """
        drop_threshold = drop_threshold or settings.PERFORMANCE_DROP_THRESHOLD
        if not reference_metrics or not current_metrics:
            return {"status": "no_metrics", "drifted": False}

        monitored = ["accuracy", "auc_roc", "avg_precision", "f1", "r2"]
        results = {}
        any_drifted = False

        for metric in monitored:
            if metric not in reference_metrics or metric not in current_metrics:
                continue
            ref_val = float(reference_metrics[metric])
            cur_val = float(current_metrics[metric])
            if ref_val == 0:
                continue
            relative_drop = (ref_val - cur_val) / abs(ref_val)
            drifted = bool(relative_drop > drop_threshold)
            if drifted:
                any_drifted = True
            results[metric] = {
                "reference": round(ref_val, 5),
                "current":   round(cur_val, 5),
                "drop_pct":  round(relative_drop * 100, 2),
                "drifted":   drifted,
            }

        return {
            "method": "performance_drift",
            "metrics": results,
            "drifted": bool(any_drifted),
            "threshold_pct": drop_threshold * 100,
        }

    # ── Full report ───────────────────────────────────────────────────────────

    @classmethod
    def full_report(
        cls,
        reference_log,
        target_log,
        feature_names: list[str],
    ) -> dict:
        """
        Generate a complete drift report comparing two PredictionLog rows.
        Returns all test results and an overall DriftStatus.
        """
        feature_drift = {}
        for feat in feature_names:
            ref_stats = reference_log.features_stats.get(feat, {})
            cur_stats = target_log.features_stats.get(feat, {})
            if not ref_stats or not cur_stats:
                continue
            # We stored stats only; for KS test we need raw data stored in raw_predictions
            # Use PSI on prediction distribution as a proxy when raw unavailable
            feature_drift[feat] = {"stats_ref": ref_stats, "stats_cur": cur_stats}

        # Prediction distribution drift (PSI + chi-squared)
        pred_psi    = cls.psi(reference_log.prediction_dist, target_log.prediction_dist)
        pred_chisq  = cls.chi_squared(reference_log.prediction_dist, target_log.prediction_dist)

        # Raw prediction KS test (if available)
        pred_ks = {}
        if reference_log.raw_predictions and target_log.raw_predictions:
            pred_ks = cls.ks_test(reference_log.raw_predictions, target_log.raw_predictions)
            # Also per-feature if stored
            for feat in feature_names:
                r_raw = [v for v in reference_log.raw_predictions]
                # Feature raw not separately stored — skip per-feature KS for now
                break

        # Performance drift
        perf_drift = {}
        if reference_log.performance and target_log.performance:
            perf_drift = cls.performance_drift(reference_log.performance, target_log.performance)

        # Determine overall status
        any_critical = (
            pred_psi.get("severity") == "critical"
            or pred_ks.get("severity") == "critical"
            or perf_drift.get("drifted", False)
        )
        any_warning = (
            pred_psi.get("drifted", False)
            or pred_chisq.get("drifted", False)
            or pred_ks.get("drifted", False)
        )

        if any_critical:
            overall = "critical"
        elif any_warning:
            overall = "warning"
        else:
            overall = "ok"

        return {
            "overall_status": overall,
            "feature_drift": feature_drift,
            "prediction_drift": {
                "psi":       pred_psi,
                "chi_squared": pred_chisq,
                "ks_test":   pred_ks,
            },
            "performance_drift": perf_drift,
        }

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _severity(value: float, threshold: float, levels: list[float] = None) -> str:
        if levels:
            lo, hi = levels
            if value >= hi:   return "critical"
            if value >= lo:   return "warning"
            return "ok"
        ratio = value / threshold if threshold else 0
        if ratio >= 1.5:  return "critical"
        if ratio >= 1.0:  return "warning"
        return "ok"
