"""Model preset endpoints — /api/v1/models."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from backend.src.api.deps import get_models_dir, get_settings_service
from backend.src.models.schemas import SaveModelRequest, StatusResponse
from backend.src.services.settings_service import SettingsService


router = APIRouter(prefix="/api/v1/models", tags=["models"])

ModelsDir = Annotated[Path, Depends(get_models_dir)]
SettingsSvc = Annotated[SettingsService, Depends(get_settings_service)]


@router.get("")
def list_models(models_dir: ModelsDir) -> list[dict[str, str]]:
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
                    "modified": datetime.fromtimestamp(mod_time).strftime(
                        "%Y-%m-%d %H:%M"
                    ),
                }
            )
    return result


@router.post("")
def save_model(
    req: SaveModelRequest, models_dir: ModelsDir, svc: SettingsSvc
) -> dict[str, str]:
    os.makedirs(models_dir, exist_ok=True)
    clean = "".join(c for c in req.name if c.isalnum() or c in (" ", "-", "_")).rstrip()
    if not clean:
        raise HTTPException(status_code=400, detail="Invalid model name")
    path = os.path.join(models_dir, f"{clean.replace(' ', '_')}.json")
    settings: dict[str, Any] = svc.load_settings()
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(settings, fh, indent=2, ensure_ascii=False)
    return {"status": "ok", "filename": os.path.basename(path)}


@router.post("/{filename}/load")
def load_model(
    filename: str, models_dir: ModelsDir, svc: SettingsSvc
) -> StatusResponse:
    path = os.path.join(models_dir, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Model not found")
    with open(path, encoding="utf-8") as fh:
        loaded: dict[str, Any] = json.load(fh)
    if not svc.save_settings(loaded):
        raise HTTPException(status_code=500, detail="Failed to apply model settings")
    return StatusResponse(status="ok")


@router.get("/{filename}/preview")
def preview_model(filename: str, models_dir: ModelsDir) -> dict[str, Any]:
    path = os.path.join(models_dir, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Model not found")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


@router.delete("/{filename}")
def delete_model(filename: str, models_dir: ModelsDir) -> StatusResponse:
    path = os.path.join(models_dir, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Model not found")
    os.remove(path)
    return StatusResponse(status="ok")
