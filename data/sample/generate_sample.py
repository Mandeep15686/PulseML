"""
Generate realistic sample data for PulseML demonstration.

Simulates a credit-risk scoring model over 6 monthly batches where:
  - Batches 1-3: stable (reference period)
  - Batch 4:     gradual drift begins
  - Batch 5:     significant data drift
  - Batch 6:     performance degradation + severe drift

Usage:
    python data/sample/generate_sample.py
    python data/sample/generate_sample.py --seed 99 --n-batches 8
"""
from __future__ import annotations
import argparse
import json
import random
import sys
import os
import math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import numpy as np


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def generate_batch(
    n: int,
    drift_level: float = 0.0,
    perf_drop: float = 0.0,
    rng: np.random.Generator = None,
) -> dict:
    """
    drift_level : 0.0 = no drift, 1.0 = severe drift
    perf_drop   : 0.0 = no drop, 1.0 = random classifier
    """
    rng = rng or np.random.default_rng(42)

    # Feature means shift with drift
    age_mean      = 40 + drift_level * 15
    income_mean   = 55000 + drift_level * -20000
    credit_mean   = 680 + drift_level * -60
    debt_ratio_mu = 0.35 + drift_level * 0.25

    age         = rng.normal(age_mean,    12,    n).clip(18, 90)
    income      = rng.normal(income_mean, 18000, n).clip(5000, 250000)
    credit_score= rng.normal(credit_mean, 80,    n).clip(300, 850)
    debt_ratio  = rng.normal(debt_ratio_mu, 0.15, n).clip(0, 1)
    employment  = rng.binomial(1, 0.75 - drift_level * 0.3, n)

    # True probability of default
    logit = (
        -3.0
        + 0.03 * (age - 40)
        - 0.00002 * (income - 55000)
        - 0.008 * (credit_score - 680)
        + 2.5 * debt_ratio
        - 0.8 * employment
    )
    true_prob = sigmoid(logit)
    labels = rng.binomial(1, true_prob, n).tolist()

    # Model predictions (degrade with perf_drop)
    noise = rng.normal(0, perf_drop * 0.4, n)
    pred_logit = logit + noise
    predictions = sigmoid(pred_logit + drift_level * rng.normal(0, 0.5, n)).tolist()

    return {
        "predictions": [round(float(p), 6) for p in predictions],
        "labels":      [int(l) for l in labels],
        "features": {
            "age":          [round(float(v), 2) for v in age],
            "income":       [round(float(v), 2) for v in income],
            "credit_score": [round(float(v), 2) for v in credit_score],
            "debt_ratio":   [round(float(v), 4) for v in debt_ratio],
            "employment":   [int(v) for v in employment],
        },
    }


BATCHES = [
    ("2024-01", 500, 0.0,  0.0),
    ("2024-02", 480, 0.0,  0.0),
    ("2024-03", 520, 0.05, 0.0),
    ("2024-04", 490, 0.3,  0.1),
    ("2024-05", 510, 0.6,  0.25),
    ("2024-06", 470, 0.9,  0.5),
]

MODEL_META = {
    "name":         "credit_risk_scorer_v1",
    "version":      "1.0.0",
    "description":  "Credit default risk scoring model — demo with injected drift",
    "task_type":    "binary_classification",
    "feature_names":["age", "income", "credit_score", "debt_ratio", "employment"],
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed",      type=int, default=42)
    ap.add_argument("--n-batches", type=int, default=len(BATCHES))
    ap.add_argument("--out",       default=os.path.dirname(__file__))
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    out = {}

    print("Generating sample data…")
    for label, n, drift, perf in BATCHES[:args.n_batches]:
        batch = generate_batch(n, drift, perf, rng)
        out[label] = batch
        pos = sum(batch["labels"])
        mean_pred = sum(batch["predictions"]) / len(batch["predictions"])
        print(f"  {label}: n={n} positives={pos} ({pos/n*100:.1f}%) "
              f"mean_pred={mean_pred:.3f} drift={drift:.1f} perf_drop={perf:.1f}")

    # Save model meta
    meta_path = os.path.join(args.out, "model_meta.json")
    with open(meta_path, "w") as f:
        json.dump(MODEL_META, f, indent=2)
    print(f"Model meta → {meta_path}")

    # Save batches
    batches_path = os.path.join(args.out, "batches.json")
    with open(batches_path, "w") as f:
        json.dump(out, f)
    print(f"Batches    → {batches_path}")
    print(f"\nTo load into PulseML, run:")
    print(f"  python scripts/load_sample.py")


if __name__ == "__main__":
    main()
