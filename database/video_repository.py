from __future__ import annotations

from pathlib import Path

from black_pioneers_studio.paths import PIONEERS_OUTPUT_DIR


def list_generated_videos() -> list[Path]:
    videos = list(PIONEERS_OUTPUT_DIR.rglob("*.mp4"))
    return sorted(videos, key=lambda path: path.stat().st_mtime, reverse=True)


def count_generated_shorts() -> int:
    from black_pioneers_studio.cloud import current_backend
    backend = current_backend()
    return len(backend.media(generated=True)) if backend else len(list_generated_videos())

