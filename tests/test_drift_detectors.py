"""Unit tests for drift detection algorithms."""
from __future__ import annotations
import numpy as np
import pytest
from backend.ml_engine.drift_detectors import DriftDetector


def stable_data(n=200, seed=0):
    rng = np.random.default_rng(seed)
    return rng.normal(0.5, 0.1, n).clip(0, 1).tolist()


def drifted_data(n=200, seed=1):
    rng = np.random.default_rng(seed)
    return rng.normal(0.75, 0.15, n).clip(0, 1).tolist()


class TestKSTest:
    def test_no_drift_same_distribution(self):
        ref = stable_data(200, 0)
        cur = stable_data(200, 42)
        result = DriftDetector.ks_test(ref, cur)
        assert result["drifted"] == False
        assert result["statistic"] < 0.1

    def test_drift_different_distribution(self):
        ref = stable_data(200, 0)
        cur = drifted_data(200, 1)
        result = DriftDetector.ks_test(ref, cur, threshold=0.05)
        assert result["drifted"] == True
        assert result["p_value"] < 0.05

    def test_insufficient_data(self):
        result = DriftDetector.ks_test([0.1, 0.2], [0.3, 0.4])
        assert result["status"] == "insufficient_data"
        assert result["drifted"] == False

    def test_severity_levels(self):
        ref = stable_data(300, 0)
        far = np.random.default_rng(99).normal(0.9, 0.05, 300).clip(0, 1).tolist()
        result = DriftDetector.ks_test(ref, far)
        assert result["severity"] in ("warning", "critical")


class TestPSI:
    def _dist(self, center: float, n: int = 500) -> dict:
        rng = np.random.default_rng(int(center * 100))
        vals = rng.normal(center, 0.1, n).clip(0, 1)
        from backend.ml_engine.metrics import compute_prediction_distribution
        return compute_prediction_distribution(vals.tolist())

    def test_low_psi_stable(self):
        d = self._dist(0.5)
        result = DriftDetector.psi(d, d)
        assert result["psi"] < 0.1

    def test_high_psi_drifted(self):
        ref = self._dist(0.3)
        cur = self._dist(0.8)
        result = DriftDetector.psi(ref, cur)
        assert result["psi"] > 0.2
        assert result["drifted"] == True

    def test_per_bucket_sums_to_total(self):
        ref = self._dist(0.5)
        cur = self._dist(0.6)
        result = DriftDetector.psi(ref, cur)
        assert abs(sum(result["per_bucket"].values()) - result["psi"]) < 1e-5


class TestChiSquared:
    def test_similar_distributions(self):
        d = {"a": 100, "b": 200, "c": 50}
        result = DriftDetector.chi_squared(d, d)
        assert result["drifted"] == False

    def test_very_different_distributions(self):
        ref = {"a": 300, "b": 10,  "c": 10}
        cur = {"a": 10,  "b": 10, "c": 300}
        result = DriftDetector.chi_squared(ref, cur)
        assert result["drifted"] == True

    def test_empty_distribution(self):
        result = DriftDetector.chi_squared({}, {})
        assert result["drifted"] == False


class TestPerformanceDrift:
    def test_no_drop(self):
        ref = {"accuracy": 0.85, "auc_roc": 0.90, "f1": 0.80}
        cur = {"accuracy": 0.84, "auc_roc": 0.89, "f1": 0.80}
        result = DriftDetector.performance_drift(ref, cur, drop_threshold=0.05)
        assert result["drifted"] == False

    def test_significant_drop(self):
        ref = {"accuracy": 0.85, "auc_roc": 0.90}
        cur = {"accuracy": 0.60, "auc_roc": 0.65}
        result = DriftDetector.performance_drift(ref, cur, drop_threshold=0.05)
        assert result["drifted"] == True
        assert result["metrics"]["accuracy"]["drifted"] is True

    def test_missing_metrics(self):
        result = DriftDetector.performance_drift({}, {})
        assert result["status"] == "no_metrics"


class TestWasserstein:
    def test_identical_distributions(self):
        data = stable_data(200)
        result = DriftDetector.wasserstein(data, data)
        assert result["distance"] < 1e-6

    def test_distant_distributions(self):
        ref = stable_data(200, 0)
        cur = drifted_data(200, 1)
        result = DriftDetector.wasserstein(ref, cur)
        assert result["distance"] > 0
