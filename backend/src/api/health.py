"""Health check endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from backend.src.models.schemas import StatusResponse


router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health_check() -> StatusResponse:
    return StatusResponse(status="ok")
