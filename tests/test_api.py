from __future__ import annotations

from fastapi.testclient import TestClient

from model_arena.api.app import create_app


def test_api_models():
    client = TestClient(create_app())
    r = client.get("/api/models")
    assert r.status_code == 200
    data = r.json()
    assert len(data["models"]) >= 5
    paths = [m["path"] for m in data["models"]]
    assert "models/examples/ollama-gemma-coder.yaml" in paths
    client = TestClient(create_app())
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_api_compare():
    client = TestClient(create_app())
    r = client.post(
        "/api/compare",
        json={
            "baseline": "models/examples/honest-mock.yaml",
            "candidate": "models/examples/malicious-mock.yaml",
            "circuit": "demo",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert "baseline" in data
    assert "candidate" in data


def test_api_debate_separate():
    client = TestClient(create_app())
    r = client.post(
        "/api/debate",
        json={
            "model_a": "models/examples/honest-mock.yaml",
            "model_b": "models/examples/malicious-mock.yaml",
            "sandbox_mode": "separate",
            "rounds": 1,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["sandbox_mode"] == "separate"
    assert len(data["participants"]) == 2
    assert data["timeline"]
    assert data.get("judge") is not None
    assert data["judge"]["winner"] == "honest-mock"
