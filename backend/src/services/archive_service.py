"""Archive file I/O — load and save archived papers."""

from __future__ import annotations

import json
from typing import Any

from backend.src.config import ARCHIVE_DIR


def load_archive() -> dict[str, list[dict[str, Any]]]:
    """Load the full archive. Returns {date_str: [paper, ...]}."""
    archive_file = ARCHIVE_DIR / "archive.json"
    if not archive_file.exists():
        return {}
    with open(archive_file, encoding="utf-8") as fh:
        return json.load(fh)


def save_archive(archive: dict[str, list[dict[str, Any]]]) -> None:
    """Persist the archive to disk."""
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    archive_file = ARCHIVE_DIR / "archive.json"
    with open(archive_file, "w", encoding="utf-8") as fh:
        json.dump(archive, fh, indent=2, ensure_ascii=False)
