"""Knowledge Base Pydantic models — stubs until Step 7."""

from __future__ import annotations

from pydantic import BaseModel


class KBProject(BaseModel):
    id: str
    name: str
    description: str = ""


class KBDocument(BaseModel):
    id: str
    project_id: str
    title: str
    source_type: str = ""
    filename: str = ""
