"""Tests for /api/v1/health endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_v1_health(client: TestClient) -> None:
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
