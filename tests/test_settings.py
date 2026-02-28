"""Tests for the /api/settings endpoints."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient


def test_get_settings(client: TestClient, mock_settings: dict[str, Any]) -> None:
    resp = client.get("/api/settings")
    assert resp.status_code == 200
    data = resp.json()
    assert "keywords" in data
    assert data["keywords"] == mock_settings["keywords"]


def test_put_settings(client: TestClient, mock_settings: dict[str, Any]) -> None:
    # Modify keywords and save
    updated = mock_settings.copy()
    updated["keywords"] = ["brain", "cognition"]
    resp = client.put("/api/settings", json={"settings": updated})
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    # Verify the change persisted
    resp2 = client.get("/api/settings")
    assert resp2.status_code == 200
    assert resp2.json()["keywords"] == ["brain", "cognition"]


def test_put_settings_empty(client: TestClient) -> None:
    resp = client.put("/api/settings", json={"settings": {}})
    assert resp.status_code == 200
