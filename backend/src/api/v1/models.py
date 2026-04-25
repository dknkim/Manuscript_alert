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


def _drop_orphaned_must_have(settings: dict[str, Any]) -> None:
    """Remove must-have keywords that no longer exist in the keyword list.

    A keyword may have been renamed or deleted in one model while the
    must-have list retained the old name, causing papers to be silently
    filtered to zero without any visible selection in the UI.
    """
    keywords: list[str] = settings.get("keywords", [])
    must_have: list[str] = settings.get("must_have_keywords", [])
    settings["must_have_keywords"] = [mk for mk in must_have if mk in keywords]

ModelsDir = Annotated[Path, Depends(get_models_dir)]
SettingsSvc = Annotated[SettingsService, Depends(get_settings_service)]
DBPool = Annotated[asyncpg.Pool | None, Depends(get_db_pool)]


@router.get("")
async def list_models(
    models_dir: ModelsDir, svc: SettingsSvc, pool: DBPool, user: CurrentUser
) -> list[dict[str, str]]:
    if pool is not None:
        presets = await db.list_model_presets(pool, user)
        if not presets:
            # No presets yet — seed Model 1 with the user's current active
            # settings (their existing keywords for pre-multi-model users, or
            # the app defaults for brand-new users). Safe for existing users:
            # the condition is false as soon as they have any saved preset.
            seed: dict[str, Any] = await db.get_settings(pool, user) or svc.load_settings()
            await db.save_model_preset(pool, "Model_1", seed, user)
            presets = await db.list_model_presets(pool, user)
        return presets
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
    if not result:
        # File-based equivalent: seed Model_1.json from current settings.
        seed = svc.load_settings()
        seed_path = os.path.join(models_dir, "Model_1.json")
        with open(seed_path, "w", encoding="utf-8") as fh:
            json.dump(seed, fh, indent=2, ensure_ascii=False)
        mod_time = os.path.getmtime(seed_path)
        result.append(
            {
                "name": "Model 1",
                "filename": "Model_1.json",
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
        _drop_orphaned_must_have(preset)
        # slot_names lives in active settings (not in model presets), so preserve
        # it when overwriting active settings with the loaded preset.
        current = await db.get_settings(pool, user)
        if current:
            slot_names = (current.get("ui_settings") or {}).get("slot_names")
            if slot_names:
                preset_ui = dict(preset.get("ui_settings") or {})
                preset_ui["slot_names"] = slot_names
                preset = {**preset, "ui_settings": preset_ui}
        await db.save_settings(pool, preset, user)
        return StatusResponse(status="ok")

    # File-based fallback
    path = os.path.join(models_dir, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Model not found")
    with open(path, encoding="utf-8") as fh:
        loaded: dict[str, Any] = json.load(fh)
    _drop_orphaned_must_have(loaded)
    # Preserve slot_names from current file-based settings
    current_file = svc.load_settings()
    slot_names = (current_file.get("ui_settings") or {}).get("slot_names")
    if slot_names:
        loaded_ui = dict(loaded.get("ui_settings") or {})
        loaded_ui["slot_names"] = slot_names
        loaded["ui_settings"] = loaded_ui
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
