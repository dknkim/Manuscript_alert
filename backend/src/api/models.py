"""Model preset endpoints."""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException

from backend.src.config import MODELS_DIR, settings_service
from backend.src.models.schemas import SaveModelRequest, StatusResponse


router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("")
def list_models() -> list[dict[str, str]]:
    """List saved model presets."""
    os.makedirs(MODELS_DIR, exist_ok=True)
    models: list[dict[str, str]] = []
    for f in sorted(os.listdir(MODELS_DIR)):
        if f.endswith(".json"):
            path: str = os.path.join(MODELS_DIR, f)
            mod_time: float = os.path.getmtime(path)
            models.append(
                {
                    "name": f.replace(".json", "").replace("_", " "),
                    "filename": f,
                    "modified": datetime.fromtimestamp(mod_time).strftime(
                        "%Y-%m-%d %H:%M"
                    ),
                }
            )
    return models


@router.post("")
def save_model(req: SaveModelRequest) -> dict[str, str]:
    """Save current settings as a named model."""
    os.makedirs(MODELS_DIR, exist_ok=True)
    clean: str = "".join(
        c for c in req.name if c.isalnum() or c in (" ", "-", "_")
    ).rstrip()
    if not clean:
        raise HTTPException(status_code=400, detail="Invalid model name")
    path: str = os.path.join(MODELS_DIR, f"{clean.replace(' ', '_')}.json")
    settings: dict[str, Any] = settings_service.load_settings()
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(settings, fh, indent=2, ensure_ascii=False)
    return {"status": "ok", "filename": os.path.basename(path)}


@router.post("/{filename}/load")
def load_model(filename: str) -> StatusResponse:
    """Load a model preset as current settings."""
    path: str = os.path.join(MODELS_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Model not found")
    with open(path, encoding="utf-8") as fh:
        loaded: dict[str, Any] = json.load(fh)
    ok: bool = settings_service.save_settings(loaded)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to apply model settings")
    return StatusResponse(status="ok")


@router.get("/{filename}/preview")
def preview_model(filename: str) -> dict[str, Any]:
    """Preview a model preset."""
    path: str = os.path.join(MODELS_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Model not found")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


@router.delete("/{filename}")
def delete_model(filename: str) -> StatusResponse:
    """Delete a model preset."""
    path: str = os.path.join(MODELS_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Model not found")
    os.remove(path)
    return StatusResponse(status="ok")
