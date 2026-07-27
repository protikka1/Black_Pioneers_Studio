from __future__ import annotations

import re
from pathlib import Path
from typing import Any, BinaryIO, cast

from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from moviepy import ImageClip, VideoFileClip, concatenate_videoclips

from .models import PioneerRecord
from .paths import HEIGHT, PIONEERS_OUTPUT_DIR, WIDTH
from database.pioneer_repository import update_pioneer_folder

SUPPORTED_IMAGES = {".jpg", ".jpeg", ".png", ".webp"}
SUPPORTED_VIDEOS = {".mp4", ".mov", ".m4v"}


def make_safe_folder_name(name: str) -> str:
    safe_name = name.strip().lower()
    safe_name = re.sub(r"[^a-z0-9]+", "_", safe_name)
    return safe_name.strip("_")


def save_uploaded_file(uploaded_file: BinaryIO, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)

    with destination.open("wb") as file:
        file.write(uploaded_file.getbuffer())

    return destination


def count_generated_shorts() -> int:
    return len(list(PIONEERS_OUTPUT_DIR.rglob("*.mp4")))


def get_or_create_pioneer_folder(pioneer: PioneerRecord) -> Path:
    folder_path = str(pioneer.get("folder_path") or "").strip()

    if folder_path:
        folder = Path(folder_path)
    else:
        pioneer_id = int(str(pioneer["id"]))
        safe_name = make_safe_folder_name(str(pioneer["name"])) or "pioneer"
        folder = PIONEERS_OUTPUT_DIR / f"{pioneer_id}_{safe_name}"
        update_pioneer_folder(pioneer_id=pioneer_id, folder_path=str(folder))

    for subfolder in ["images", "videos", "audio", "music", "captions", "output"]:
        (folder / subfolder).mkdir(parents=True, exist_ok=True)

    return folder


def prepare_vertical_image(source_path: Path, destination_path: Path) -> Path:
    with Image.open(source_path) as source:
        image = source.convert("RGB")

        background = ImageOps.fit(
            image,
            (WIDTH, HEIGHT),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )
        background = ImageEnhance.Brightness(
            background.filter(ImageFilter.GaussianBlur(radius=30))
        ).enhance(0.65)

        foreground = ImageOps.contain(
            image,
            (WIDTH, HEIGHT),
            method=Image.Resampling.LANCZOS,
        )

        canvas = background.copy()
        offset = (
            (WIDTH - foreground.width) // 2,
            (HEIGHT - foreground.height) // 2,
        )
        canvas.paste(foreground, offset)
        canvas.save(destination_path, quality=92, optimize=True)

    return destination_path


def prepare_video_clip(source_path: Path, required_duration: float):
    clip = VideoFileClip(str(source_path))
    source_ratio = clip.w / clip.h
    target_ratio = WIDTH / HEIGHT

    if source_ratio > target_ratio:
        crop_width = int(clip.h * target_ratio)
        clip = clip.cropped(x_center=clip.w / 2, width=crop_width)
    else:
        crop_height = int(clip.w / target_ratio)
        clip = clip.cropped(y_center=clip.h / 2, height=crop_height)

    clip = cast(Any, clip).resized(new_size=(WIDTH, HEIGHT))
    clip_duration = float(clip.duration or 0.0)

    if clip_duration <= 0:
        clip.close()
        raise ValueError(f"Video asset has no readable duration: {source_path}")

    if clip_duration >= required_duration:
        return clip.subclipped(0, required_duration)

    copies_needed = int(required_duration / clip_duration) + 1
    repeated = concatenate_videoclips([clip for _ in range(copies_needed)], method="compose")
    return repeated.subclipped(0, required_duration)


def create_background_video(asset_paths: list[Path], duration: float, job_directory: Path):
    if not asset_paths:
        raise ValueError("At least one image or video asset is required.")

    duration_per_asset = duration / len(asset_paths)
    clips = []

    for index, asset_path in enumerate(asset_paths):
        extension = asset_path.suffix.lower()

        if extension in SUPPORTED_IMAGES:
            prepared_path = job_directory / f"prepared_image_{index:04d}.jpg"
            prepare_vertical_image(asset_path, prepared_path)
            clips.append(ImageClip(str(prepared_path)).with_duration(duration_per_asset))
        elif extension in SUPPORTED_VIDEOS:
            clips.append(prepare_video_clip(asset_path, duration_per_asset))

    if not clips:
        raise ValueError("No supported image or video assets were found.")

    return concatenate_videoclips(clips, method="compose").with_duration(duration)


def list_generated_videos() -> list[Path]:
    videos = list(PIONEERS_OUTPUT_DIR.rglob("*.mp4"))
    return sorted(videos, key=lambda path: path.stat().st_mtime, reverse=True)
