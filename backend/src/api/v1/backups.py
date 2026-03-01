"""Backup endpoints — /api/v1/backups."""

from __future__ import annotations

import os
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from backend.src.api.deps import get_settings_service
from backend.src.models.schemas import RestoreBackupRequest, StatusResponse
from backend.src.services.settings_service import SettingsService


router = APIRouter(prefix="/api/v1/backups", tags=["backups"])

SettingsSvc = Annotated[SettingsService, Depends(get_settings_service)]


@router.get("")
def list_backups(svc: SettingsSvc) -> list[dict[str, str]]:
    backups = svc.list_backups()
    result: list[dict[str, str]] = []
    for bp in backups[:10]:
        name = os.path.basename(bp)
        date_str = name.replace("settings_backup_", "").replace(".py", "")
        result.append({"path": bp, "name": name, "date": date_str})
    return result


@router.post("/restore")
def restore_backup(data: RestoreBackupRequest, svc: SettingsSvc) -> StatusResponse:
    if not data.path or not os.path.exists(data.path):
        raise HTTPException(status_code=404, detail="Backup not found")
    if not svc.restore_backup(data.path):
        raise HTTPException(status_code=500, detail="Failed to restore backup")
    return StatusResponse(status="ok")


@router.post("/create")
def create_backup(svc: SettingsSvc) -> StatusResponse:
    settings: dict[str, Any] = svc.load_settings()
    if not svc.save_settings(settings):
        raise HTTPException(status_code=500, detail="Failed to create backup")
    return StatusResponse(status="ok")


@router.delete("")
def delete_backup(data: RestoreBackupRequest) -> StatusResponse:
    if not data.path or not os.path.exists(data.path):
        raise HTTPException(status_code=404, detail="Backup not found")
    os.remove(data.path)
    return StatusResponse(status="ok")
