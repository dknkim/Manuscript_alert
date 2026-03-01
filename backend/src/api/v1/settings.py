"""Settings endpoints — /api/v1/settings."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from backend.src.api.deps import get_settings_service
from backend.src.models.schemas import SaveSettingsRequest, StatusResponse
from backend.src.services.settings_service import SettingsService


router = APIRouter(prefix="/api/v1", tags=["settings"])

SettingsSvc = Annotated[SettingsService, Depends(get_settings_service)]


@router.get("/settings")
def get_settings(svc: SettingsSvc) -> dict[str, Any]:
    return svc.load_settings()


@router.put("/settings")
def save_settings(req: SaveSettingsRequest, svc: SettingsSvc) -> StatusResponse:
    if not svc.save_settings(req.settings):
        raise HTTPException(status_code=500, detail="Failed to save settings")
    return StatusResponse(status="ok")
