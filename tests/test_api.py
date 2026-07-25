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
