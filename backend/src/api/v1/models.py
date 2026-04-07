"""Model preset endpoints — /api/v1/models."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any

import asyncpg
from fastapi import APIRouter, Depends, HTTPException

from backend.src.api.auth import CurrentUser
from backend.src.api.deps import get_db_pool, get_models_dir, get_settings_service
from backend.src.db import models as db
from backend.src.models.schemas import SaveModelRequest, StatusResponse
from backend.src.services.settings_service import SettingsService


router = APIRouter(prefix="/api/v1/models", tags=["models"])

ModelsDir = Annotated[Path, Depends(get_models_dir)]
SettingsSvc = Annotated[SettingsService, Depends(get_settings_service)]
DBPool = Annotated[asyncpg.Pool | None, Depends(get_db_pool)]


@router.get("")
async def list_models(
    models_dir: ModelsDir, pool: DBPool, user: CurrentUser
) -> list[dict[str, str]]:
    if pool is not None:
        return await db.list_model_presets(pool, user)
    # File-based fallback
    os.makedirs(models_dir, exist_ok=True)
    result: list[dict[str, str]] = []
    for f in sorted(os.listdir(models_dir)):
        if f.endswith(".json"):
            path = os.path.join(models_dir, f)
            mod_time = os.path.getmtime(path)
            result.append(
                {
                    "name": f.replace(".json", "").replace("_", " "),
                    "filename": f,
                    "modified": datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M"),
                }
            )
    return result


@router.post("")
async def save_model(
    req: SaveModelRequest, models_dir: ModelsDir, svc: SettingsSvc, pool: DBPool, user: CurrentUser
) -> dict[str, str]:
    clean = "".join(c for c in req.name if c.isalnum() or c in (" ", "-", "_")).rstrip()
    if not clean:
        raise HTTPException(status_code=400, detail="Invalid model name")
    db_name = clean.replace(" ", "_")
    filename = db_name + ".json"

    if pool is not None:
        settings: dict[str, Any] = await db.get_settings(pool, user) or svc.load_settings()
        await db.save_model_preset(pool, db_name, settings, user)
        return {"status": "ok", "filename": filename}

    # File-based fallback
    os.makedirs(models_dir, exist_ok=True)
    path = os.path.join(models_dir, filename)
    settings = svc.load_settings()
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(settings, fh, indent=2, ensure_ascii=False)
    return {"status": "ok", "filename": os.path.basename(path)}


@router.post("/{filename}/load")
async def load_model(
    filename: str, models_dir: ModelsDir, svc: SettingsSvc, pool: DBPool, user: CurrentUser
) -> StatusResponse:
    db_name = filename.replace(".json", "")

    if pool is not None:
        preset = await db.get_model_preset(pool, db_name, user)
        if preset is None:
            raise HTTPException(status_code=404, detail="Model not found")
        await db.save_settings(pool, preset, user)
        return StatusResponse(status="ok")

    # File-based fallback
    path = os.path.join(models_dir, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Model not found")
    with open(path, encoding="utf-8") as fh:
        loaded: dict[str, Any] = json.load(fh)
    if not svc.save_settings(loaded):
        raise HTTPException(status_code=500, detail="Failed to apply model settings")
    return StatusResponse(status="ok")


@router.get("/{filename}/preview")
async def preview_model(
    filename: str, models_dir: ModelsDir, pool: DBPool, user: CurrentUser
) -> dict[str, Any]:
    db_name = filename.replace(".json", "")

    if pool is not None:
        preset = await db.get_model_preset(pool, db_name, user)
        if preset is None:
            raise HTTPException(status_code=404, detail="Model not found")
        return preset

    # File-based fallback
    path = os.path.join(models_dir, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Model not found")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


@router.delete("/{filename}")
async def delete_model(
    filename: str, models_dir: ModelsDir, pool: DBPool, user: CurrentUser
) -> StatusResponse:
    db_name = filename.replace(".json", "")

    if pool is not None:
        deleted = await db.delete_model_preset(pool, db_name, user)
        if not deleted:
            raise HTTPException(status_code=404, detail="Model not found")
        return StatusResponse(status="ok")

    # File-based fallback
    path = os.path.join(models_dir, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Model not found")
    os.remove(path)
    return StatusResponse(status="ok")
