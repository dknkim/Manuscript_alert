"""Settings endpoints — /api/v1/settings."""

from __future__ import annotations

from typing import Annotated, Any

import asyncpg
from fastapi import APIRouter, Depends, HTTPException

from backend.src.api.auth import CurrentUser
from backend.src.api.deps import get_db_pool, get_settings_service
from backend.src.db import models as db
from backend.src.models.schemas import SaveSettingsRequest, StatusResponse
from backend.src.services.settings_service import SettingsService


router = APIRouter(prefix="/api/v1", tags=["settings"])

SettingsSvc = Annotated[SettingsService, Depends(get_settings_service)]
DBPool = Annotated[asyncpg.Pool | None, Depends(get_db_pool)]


@router.get("/settings")
async def get_settings(svc: SettingsSvc, pool: DBPool, user: CurrentUser) -> dict[str, Any]:
    if pool is not None:
        result = await db.get_settings(pool, user)
        if result is not None:
            return result
    return svc.load_settings()


@router.put("/settings")
async def save_settings(
    req: SaveSettingsRequest, svc: SettingsSvc, pool: DBPool, user: CurrentUser
) -> StatusResponse:
    if pool is not None:
        await db.save_settings(pool, req.settings, user)
        return StatusResponse(status="ok")
    if not svc.save_settings(req.settings):
        raise HTTPException(status_code=500, detail="Failed to save settings")
    return StatusResponse(status="ok")
