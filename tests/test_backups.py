"""Tests for the /api/backups endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_list_backups_empty(client: TestClient) -> None:
    resp = client.get("/api/backups")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_and_list_backup(client: TestClient) -> None:
    # Creating a backup triggers save_settings which creates a backup
    resp = client.post("/api/backups/create")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    resp2 = client.get("/api/backups")
    backups = resp2.json()
    assert len(backups) >= 1
    assert backups[0]["name"].startswith("settings_backup_")


def test_restore_backup(client: TestClient) -> None:
    # Create a backup first
    client.post("/api/backups/create")

    backups = client.get("/api/backups").json()
    assert len(backups) >= 1

    resp = client.post("/api/backups/restore", json={"path": backups[0]["path"]})
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_restore_backup_not_found(client: TestClient) -> None:
    resp = client.post("/api/backups/restore", json={"path": "/tmp/nonexistent.py"})
    assert resp.status_code == 404


def test_delete_backup(client: TestClient) -> None:
    client.post("/api/backups/create")
    backups = client.get("/api/backups").json()
    assert len(backups) >= 1

    resp = client.request("DELETE", "/api/backups", json={"path": backups[0]["path"]})
    assert resp.status_code == 200

    # Verify gone
    backups2 = client.get("/api/backups").json()
    assert len(backups2) == len(backups) - 1


def test_delete_backup_not_found(client: TestClient) -> None:
    resp = client.request(
        "DELETE", "/api/backups", json={"path": "/tmp/nonexistent.py"}
    )
    assert resp.status_code == 404
