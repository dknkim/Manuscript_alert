"""Tests for /api/v1/kb stub endpoints — all should return 503."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


KB_ROUTES = [
    ("GET", "/api/v1/kb/projects"),
    ("POST", "/api/v1/kb/projects"),
    ("GET", "/api/v1/kb/projects/test-id"),
    ("DELETE", "/api/v1/kb/projects/test-id"),
    ("POST", "/api/v1/kb/projects/test-id/documents"),
    ("GET", "/api/v1/kb/projects/test-id/search"),
]


@pytest.mark.parametrize("method,path", KB_ROUTES)
def test_kb_stubs_return_503(client: TestClient, method: str, path: str) -> None:
    r = client.request(method, path)
    assert r.status_code == 503
    assert "Step 7" in r.json()["detail"]
