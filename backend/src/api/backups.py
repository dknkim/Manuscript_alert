"""Backup endpoints."""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, HTTPException

from backend.src.config import settings_service
from backend.src.models.schemas import RestoreBackupRequest, StatusResponse


router = APIRouter(prefix="/api/backups", tags=["backups"])


@router.get("")
def list_backups() -> list[dict[str, str]]:
    """List available settings backups."""
    backups: list[str] = settings_service.list_backups()
    result: list[dict[str, str]] = []
    for bp in backups[:10]:
        name: str = os.path.basename(bp)
        date_str: str = name.replace("settings_backup_", "").replace(".py", "")
        result.append({"path": bp, "name": name, "date": date_str})
    return result


@router.post("/restore")
def restore_backup(data: RestoreBackupRequest) -> StatusResponse:
    """Restore a backup."""
    if not data.path or not os.path.exists(data.path):
        raise HTTPException(status_code=404, detail="Backup not found")
    ok: bool = settings_service.restore_backup(data.path)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to restore backup")
    return StatusResponse(status="ok")


@router.post("/create")
def create_backup() -> StatusResponse:
    """Create a manual backup."""
    settings: dict[str, Any] = settings_service.load_settings()
    ok: bool = settings_service.save_settings(settings)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to create backup")
    return StatusResponse(status="ok")


@router.delete("")
def delete_backup(data: RestoreBackupRequest) -> StatusResponse:
    """Delete a backup."""
    if not data.path or not os.path.exists(data.path):
        raise HTTPException(status_code=404, detail="Backup not found")
    os.remove(data.path)
    return StatusResponse(status="ok")
