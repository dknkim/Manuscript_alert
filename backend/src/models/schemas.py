"""Pydantic request/response models for the API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class FetchRequest(BaseModel):
    data_sources: dict[str, bool]
    search_mode: str = "Brief"


class SaveSettingsRequest(BaseModel):
    settings: dict[str, Any]


class SaveModelRequest(BaseModel):
    name: str


class ArchivePaperRequest(BaseModel):
    paper: dict[str, Any]


class UnarchivePaperRequest(BaseModel):
    title: str
    date: str


class RestoreBackupRequest(BaseModel):
    path: str


class StatusResponse(BaseModel):
    status: str
