"""Settings endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from backend.src.config import settings_service
from backend.src.models.schemas import SaveSettingsRequest, StatusResponse


router = APIRouter(prefix="/api", tags=["settings"])


@router.get("/settings")
def get_settings() -> dict[str, Any]:
    """Return current settings."""
    return settings_service.load_settings()


@router.put("/settings")
def save_settings(req: SaveSettingsRequest) -> StatusResponse:
    """Save settings."""
    ok: bool = settings_service.save_settings(req.settings)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to save settings")
    return StatusResponse(status="ok")
