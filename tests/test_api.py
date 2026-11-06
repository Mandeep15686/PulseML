"""Integration tests for all API endpoints."""
from __future__ import annotations
import pytest


MODEL_PAYLOAD = {
    "name": "test_fraud_detector",
    "version": "1.0.0",
    "description": "Test model",
    "task_type": "binary_classification",
    "feature_names": ["age", "income", "score"],
}

LOG_A = {
    "window_label": "batch-01",
    "predictions": [round(i/100, 2) for i in range(1, 101)],
    "labels": [1 if i > 60 else 0 for i in range(1, 101)],
    "features": {
        "age":    [float(20 + i % 50) for i in range(100)],
        "income": [float(30000 + i * 500) for i in range(100)],
        "score":  [float(300 + i * 5)    for i in range(100)],
    },
}

LOG_B = {
    "window_label": "batch-02",
    "predictions": [round(0.3 + i/200, 4) for i in range(100)],
    "labels": [1 if i > 40 else 0 for i in range(100)],
    "features": {
        "age":    [float(55 + i % 20) for i in range(100)],
        "income": [float(15000 + i * 100) for i in range(100)],
        "score":  [float(300 + i * 2)    for i in range(100)],
    },
}


class TestHealth:
    def test_health_ok(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestModelCRUD:
    def test_create_model(self, client):
        resp = client.post("/api/models/", json=MODEL_PAYLOAD)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == MODEL_PAYLOAD["name"]
        assert data["task_type"] == "binary_classification"
        assert len(data["id"]) == 36

    def test_duplicate_model_rejected(self, client):
        client.post("/api/models/", json=MODEL_PAYLOAD)
        resp = client.post("/api/models/", json=MODEL_PAYLOAD)
        assert resp.status_code == 409

    def test_list_models(self, client):
        resp = client.get("/api/models/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 1

    def test_get_model(self, client):
        models = client.get("/api/models/").json()
        model_id = models[0]["id"]
        resp = client.get(f"/api/models/{model_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == model_id

    def test_get_nonexistent_model(self, client):
        resp = client.get("/api/models/nonexistent-id")
        assert resp.status_code == 404

    def test_update_model(self, client):
        models = client.get("/api/models/").json()
        model_id = models[0]["id"]
        resp = client.patch(f"/api/models/{model_id}", json={"description": "Updated desc"})
        assert resp.status_code == 200
        assert resp.json()["description"] == "Updated desc"


class TestPredictionLogs:
    @pytest.fixture
    def model_id(self, client):
        resp = client.post("/api/models/", json={**MODEL_PAYLOAD, "name": "log_test_model"})
        if resp.status_code == 409:
            models = client.get("/api/models/").json()
            return next(m["id"] for m in models if m["name"] == "log_test_model")
        return resp.json()["id"]

    def test_upload_log(self, client, model_id):
        resp = client.post(f"/api/models/{model_id}/logs/", json=LOG_A)
        assert resp.status_code == 201
        data = resp.json()
        assert data["n_samples"] == 100
        assert data["window_label"] == "batch-01"
        assert "prediction_dist" in data

    def test_duplicate_window_rejected(self, client, model_id):
        client.post(f"/api/models/{model_id}/logs/", json=LOG_A)
        resp = client.post(f"/api/models/{model_id}/logs/", json=LOG_A)
        assert resp.status_code == 409

    def test_list_logs(self, client, model_id):
        resp = client.get(f"/api/models/{model_id}/logs/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_upload_second_log(self, client, model_id):
        resp = client.post(f"/api/models/{model_id}/logs/", json=LOG_B)
        assert resp.status_code == 201
        assert resp.json()["window_label"] == "batch-02"


class TestDashboard:
    def test_dashboard_returns_summary(self, client):
        resp = client.get("/api/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_models" in data
        assert "open_alerts"  in data
        assert "models" in data
        assert isinstance(data["models"], list)


class TestAlerts:
    def test_list_all_alerts(self, client):
        resp = client.get("/api/alerts")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
