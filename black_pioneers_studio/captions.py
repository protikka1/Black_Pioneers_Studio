from __future__ import annotations

import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip

from .paths import CAPTION_BASE_FONT_SIZE, CAPTION_BASE_WRAP_WIDTH, CAPTION_MAX_OPACITY, HEIGHT, WIDTH


def load_font(size: int):
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]

    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)

    return ImageFont.load_default()


def split_script_into_captions(script: str, words_per_caption: int = 8) -> list[str]:
    words = script.replace("\n", " ").split()
    return [
        " ".join(words[index:index + words_per_caption])
        for index in range(0, len(words), words_per_caption)
    ]


def create_caption_image(
    text: str,
    destination_path: Path,
    font_size: int = 68,
    bg_opacity: int = 185,
) -> Path:
    caption_height = 500
    canvas = Image.new("RGBA", (WIDTH, caption_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    font = load_font(font_size)
    wrapped_text = textwrap.fill(
        text,
        width=max(10, int(CAPTION_BASE_WRAP_WIDTH * CAPTION_BASE_FONT_SIZE / font_size)),
    )

    bounding_box = draw.multiline_textbbox(
        (0, 0),
        wrapped_text,
        font=font,
        spacing=16,
        align="center",
        stroke_width=4,
    )

    text_width = bounding_box[2] - bounding_box[0]
    text_height = bounding_box[3] - bounding_box[1]
    text_x = (WIDTH - text_width) // 2
    text_y = (caption_height - text_height) // 2

    padding = 32
    background_box = (
        max(20, text_x - padding),
        max(20, text_y - padding),
        min(WIDTH - 20, text_x + text_width + padding),
        min(caption_height - 20, text_y + text_height + padding),
    )

    draw.rounded_rectangle(background_box, radius=30, fill=(0, 0, 0, bg_opacity))
    draw.multiline_text(
        (text_x, text_y),
        wrapped_text,
        font=font,
        fill=(255, 255, 255, 255),
        spacing=16,
        align="center",
        stroke_width=4,
        stroke_fill=(0, 0, 0, 255),
    )

    canvas.save(destination_path)
    return destination_path


def create_caption_clips(
    script: str,
    duration: float,
    captions_directory: Path,
    words_per_caption: int = 8,
    caption_y: int = 1250,
    font_size: int = 68,
    bg_opacity: int = 185,
):
    captions = split_script_into_captions(script, words_per_caption)

    if not captions:
        return []

    caption_duration = duration / len(captions)
    caption_clips = []

    for index, caption_text in enumerate(captions):
        caption_path = captions_directory / f"caption_{index:04d}.png"
        create_caption_image(caption_text, caption_path, font_size=font_size, bg_opacity=bg_opacity)
        caption_clips.append(
            ImageClip(str(caption_path))
            .with_start(index * caption_duration)
            .with_duration(caption_duration)
            .with_position(("center", caption_y))
        )

    return caption_clips

