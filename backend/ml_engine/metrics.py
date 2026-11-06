"""Performance metric computation."""
from __future__ import annotations
import numpy as np
from typing import Optional


def compute_feature_stats(values: list[float]) -> dict:
    """Compute descriptive statistics for a numeric feature."""
    arr = np.array(values, dtype=float)
    arr = arr[~np.isnan(arr)]
    if len(arr) == 0:
        return {}
    return {
        "mean":  float(np.mean(arr)),
        "std":   float(np.std(arr)),
        "min":   float(np.min(arr)),
        "max":   float(np.max(arr)),
        "p25":   float(np.percentile(arr, 25)),
        "p50":   float(np.percentile(arr, 50)),
        "p75":   float(np.percentile(arr, 75)),
        "count": int(len(arr)),
    }


def compute_prediction_distribution(scores: list[float], n_bins: int = 10) -> dict:
    """Bucket prediction scores into histogram bins."""
    arr = np.array(scores, dtype=float)
    counts, edges = np.histogram(arr, bins=n_bins, range=(0.0, 1.0))
    dist = {}
    for i, (lo, hi) in enumerate(zip(edges[:-1], edges[1:])):
        label = f"{lo:.1f}-{hi:.1f}"
        dist[label] = int(counts[i])
    return dist


def compute_label_distribution(labels: list[int]) -> dict:
    """Count occurrences of each label."""
    from collections import Counter
    return {str(k): v for k, v in Counter(labels).items()}


def compute_performance_metrics(
    predictions: list[float],
    labels: list[int],
    task_type: str = "binary_classification",
) -> dict:
    """Compute classification or regression metrics."""
    if len(predictions) != len(labels) or len(predictions) == 0:
        return {}
    y_score = np.array(predictions, dtype=float)
    y_true  = np.array(labels, dtype=int)

    metrics: dict = {}

    if task_type in ("binary_classification",):
        y_pred = (y_score >= 0.5).astype(int)
        metrics["accuracy"] = float(np.mean(y_pred == y_true))

        # AUC-ROC (requires both classes)
        if len(np.unique(y_true)) > 1:
            try:
                from sklearn.metrics import roc_auc_score, average_precision_score, f1_score
                metrics["auc_roc"]  = float(roc_auc_score(y_true, y_score))
                metrics["avg_precision"] = float(average_precision_score(y_true, y_score))
                metrics["f1"]       = float(f1_score(y_true, y_pred, zero_division=0))
            except ImportError:
                pass

        pos_rate = float(np.mean(y_true))
        pred_pos = float(np.mean(y_pred))
        metrics["positive_rate"]  = pos_rate
        metrics["predicted_positive_rate"] = pred_pos

    elif task_type == "regression":
        residuals = y_score - y_true
        metrics["mae"]  = float(np.mean(np.abs(residuals)))
        metrics["rmse"] = float(np.sqrt(np.mean(residuals ** 2)))
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        metrics["r2"] = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0

    return metrics
