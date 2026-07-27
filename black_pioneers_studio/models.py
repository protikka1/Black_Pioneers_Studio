from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict


class PioneerRecord(TypedDict):
    id: int
    name: str
    category: str
    achievement: str
    biography: str
    folder_path: str
    created_at: str
    updated_at: str


@dataclass
class RenderJob:
    job_id: str
    pioneer_id: int
    status: str
    progress: float
    output_path: Path | None
    error_message: str | None
