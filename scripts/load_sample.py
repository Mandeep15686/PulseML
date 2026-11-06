"""
Load sample data into a running PulseML instance.
Registers the model and uploads all 6 monthly prediction batches.

Usage:
    python scripts/load_sample.py
    python scripts/load_sample.py --host http://localhost:8000
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "sample")


def post(host: str, path: str, payload: dict) -> dict:
    url  = f"{host}{path}"
    data = json.dumps(payload).encode()
    req  = urllib.request.Request(url, data=data,
                                  headers={"Content-Type": "application/json"},
                                  method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  HTTP {e.code}: {body[:200]}")
        raise


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="http://localhost:8000")
    ap.add_argument("--generate", action="store_true",
                    help="Re-generate sample data before loading")
    args = ap.parse_args()

    if args.generate or not os.path.exists(os.path.join(SAMPLE_DIR, "batches.json")):
        print("Generating sample data…")
        gen = os.path.join(SAMPLE_DIR, "generate_sample.py")
        os.system(f"{sys.executable} {gen}")

    # Load files
    with open(os.path.join(SAMPLE_DIR, "model_meta.json")) as f:
        meta = json.load(f)
    with open(os.path.join(SAMPLE_DIR, "batches.json")) as f:
        batches = json.load(f)

    # Health check
    print(f"Connecting to {args.host}…")
    try:
        with urllib.request.urlopen(f"{args.host}/api/health", timeout=5) as r:
            print(f"  Server: {json.loads(r.read())}")
    except Exception as e:
        print(f"  Cannot reach server: {e}")
        sys.exit(1)

    # Register model
    print(f"\nRegistering model '{meta['name']}'…")
    try:
        model = post(args.host, "/api/models/", meta)
        model_id = model["id"]
        print(f"  Created model id={model_id}")
    except urllib.error.HTTPError:
        # Already exists — find it
        import urllib.parse
        with urllib.request.urlopen(f"{args.host}/api/models/") as r:
            models = json.loads(r.read())
        match = next((m for m in models if m["name"] == meta["name"]), None)
        if not match:
            print("  Failed to create or find model. Aborting.")
            sys.exit(1)
        model_id = match["id"]
        print(f"  Using existing model id={model_id}")

    # Upload batches
    print("\nUploading prediction batches…")
    for label, batch in batches.items():
        print(f"  Uploading {label} ({len(batch['predictions'])} samples)…", end=" ")
        try:
            log = post(args.host, f"/api/models/{model_id}/logs/", {
                "window_label": label,
                "predictions":  batch["predictions"],
                "labels":       batch["labels"],
                "features":     batch["features"],
            })
            print(f"OK (log id={log['id'][:8]}…)")
        except Exception as e:
            print(f"SKIP ({e})")
        time.sleep(0.3)

    print(f"\nDone! Open http://localhost:5173 to explore the dashboard.")


if __name__ == "__main__":
    main()
