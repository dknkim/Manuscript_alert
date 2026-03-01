"""Health check endpoint — /api/v1/health."""

from __future__ import annotations

from fastapi import APIRouter

from backend.src.models.schemas import StatusResponse


router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health")
def health_check() -> StatusResponse:
    return StatusResponse(status="ok")
