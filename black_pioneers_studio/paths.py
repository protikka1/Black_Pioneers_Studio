from __future__ import annotations

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.environ.get("BLACK_PIONEERS_DATA_DIR") or (
    Path.home() / "Library" / "Application Support" / "BlackPioneersStudio"
    if getattr(sys, "frozen", False) else BASE_DIR
)).expanduser().resolve()
PROJECT_TITLE = "Black Pioneers: First in American History"

OUTPUT_DIR = DATA_DIR / "output" / "pioneers"
PIONEERS_OUTPUT_DIR = OUTPUT_DIR
TEMP_DIR = DATA_DIR / "temp"

WIDTH = 1080
HEIGHT = 1920
FPS = 30

CAPTION_BASE_FONT_SIZE = 68
CAPTION_BASE_WRAP_WIDTH = 25
CAPTION_MAX_OPACITY = 255


def ensure_runtime_directories() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

