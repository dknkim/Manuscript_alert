"""Knowledge Base endpoints — /api/v1/kb (stubs returning 503 until Step 7)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException


router = APIRouter(prefix="/api/v1/kb", tags=["knowledge-base"])

_NOT_IMPLEMENTED = HTTPException(
    status_code=503,
    detail="Knowledge Base not yet available. Coming in Step 7.",
)


@router.get("/projects")
def list_projects() -> None:
    raise _NOT_IMPLEMENTED


@router.post("/projects")
def create_project() -> None:
    raise _NOT_IMPLEMENTED


@router.get("/projects/{project_id}")
def get_project(project_id: str) -> None:
    raise _NOT_IMPLEMENTED


@router.delete("/projects/{project_id}")
def delete_project(project_id: str) -> None:
    raise _NOT_IMPLEMENTED


@router.post("/projects/{project_id}/documents")
def upload_document(project_id: str) -> None:
    raise _NOT_IMPLEMENTED


@router.get("/projects/{project_id}/search")
def search_kb(project_id: str) -> None:
    raise _NOT_IMPLEMENTED
