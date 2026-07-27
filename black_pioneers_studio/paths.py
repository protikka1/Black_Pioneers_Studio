from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_TITLE = "Black Pioneers: First in American History"

OUTPUT_DIR = BASE_DIR / "output" / "pioneers"
PIONEERS_OUTPUT_DIR = OUTPUT_DIR
TEMP_DIR = BASE_DIR / "temp"

WIDTH = 1080
HEIGHT = 1920
FPS = 30

CAPTION_BASE_FONT_SIZE = 68
CAPTION_BASE_WRAP_WIDTH = 25
CAPTION_MAX_OPACITY = 255


def ensure_runtime_directories() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

