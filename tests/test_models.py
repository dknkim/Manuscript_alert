"""Tests for the /api/models endpoints — model preset CRUD."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_list_models_empty(client: TestClient) -> None:
    resp = client.get("/api/models")
    assert resp.status_code == 200
    assert resp.json() == []


def test_save_and_list_model(client: TestClient) -> None:
    # Save
    resp = client.post("/api/models", json={"name": "My Test Model"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["filename"] == "My_Test_Model.json"

    # List
    resp2 = client.get("/api/models")
    models = resp2.json()
    assert len(models) == 1
    assert models[0]["name"] == "My Test Model"


def test_save_model_invalid_name(client: TestClient) -> None:
    resp = client.post("/api/models", json={"name": "!!!"})
    assert resp.status_code == 400


def test_preview_model(client: TestClient) -> None:
    # Save first
    client.post("/api/models", json={"name": "Preview Test"})

    resp = client.get("/api/models/Preview_Test.json/preview")
    assert resp.status_code == 200
    data = resp.json()
    assert "keywords" in data


def test_preview_model_not_found(client: TestClient) -> None:
    resp = client.get("/api/models/nonexistent.json/preview")
    assert resp.status_code == 404


def test_load_model(client: TestClient) -> None:
    client.post("/api/models", json={"name": "Load Test"})

    resp = client.post("/api/models/Load_Test.json/load")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_load_model_not_found(client: TestClient) -> None:
    resp = client.post("/api/models/nonexistent.json/load")
    assert resp.status_code == 404


def test_delete_model(client: TestClient) -> None:
    client.post("/api/models", json={"name": "Delete Me"})

    resp = client.delete("/api/models/Delete_Me.json")
    assert resp.status_code == 200

    # Verify gone
    resp2 = client.get("/api/models")
    assert resp2.json() == []


def test_delete_model_not_found(client: TestClient) -> None:
    resp = client.delete("/api/models/nonexistent.json")
    assert resp.status_code == 404
