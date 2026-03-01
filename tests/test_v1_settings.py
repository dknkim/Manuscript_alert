"""Tests for /api/v1/settings endpoints."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient


def test_v1_get_settings(client: TestClient, mock_settings: dict[str, Any]) -> None:
    r = client.get("/api/v1/settings")
    assert r.status_code == 200
    data = r.json()
    assert data["keywords"] == mock_settings["keywords"]


def test_v1_put_settings(client: TestClient, mock_settings: dict[str, Any]) -> None:
    mock_settings["keywords"] = ["test_keyword"]
    r = client.put("/api/v1/settings", json={"settings": mock_settings})
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

    r2 = client.get("/api/v1/settings")
    assert r2.json()["keywords"] == ["test_keyword"]
