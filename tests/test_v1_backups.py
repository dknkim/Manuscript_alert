"""Tests for the /api/v1/backups endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_v1_list_backups_empty(client: TestClient) -> None:
    resp = client.get("/api/v1/backups")
    assert resp.status_code == 200
    assert resp.json() == []


def test_v1_create_and_list_backup(client: TestClient) -> None:
    resp = client.post("/api/v1/backups/create")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    resp2 = client.get("/api/v1/backups")
    backups = resp2.json()
    assert len(backups) >= 1
    assert backups[0]["name"].startswith("settings_backup_")


def test_v1_restore_backup(client: TestClient) -> None:
    client.post("/api/v1/backups/create")

    backups = client.get("/api/v1/backups").json()
    assert len(backups) >= 1

    resp = client.post("/api/v1/backups/restore", json={"path": backups[0]["path"]})
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_v1_restore_backup_not_found(client: TestClient) -> None:
    resp = client.post("/api/v1/backups/restore", json={"path": "/tmp/nonexistent.py"})
    assert resp.status_code == 404


def test_v1_delete_backup(client: TestClient) -> None:
    client.post("/api/v1/backups/create")
    backups = client.get("/api/v1/backups").json()
    assert len(backups) >= 1

    resp = client.request("DELETE", "/api/v1/backups", json={"path": backups[0]["path"]})
    assert resp.status_code == 200

    backups2 = client.get("/api/v1/backups").json()
    assert len(backups2) == len(backups) - 1


def test_v1_delete_backup_not_found(client: TestClient) -> None:
    resp = client.request("DELETE", "/api/v1/backups", json={"path": "/tmp/nonexistent.py"})
    assert resp.status_code == 404
