from __future__ import annotations

import asyncio
import re
import shutil
import sqlite3
import textwrap
import uuid
from datetime import datetime
from pathlib import Path

import edge_tts
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from moviepy import (
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    VideoFileClip,
    concatenate_audioclips,
    concatenate_videoclips,
)


# =========================================================
# Configuration
# =========================================================

PROJECT_TITLE = "Black Pioneers: First in American History"

BASE_DIR = Path(__file__).resolve().parent
DATABASE_DIR = BASE_DIR / "database"
DATABASE_FILE = DATABASE_DIR / "pioneers.db"

GENERATED_DIR = BASE_DIR / "generated"
TEMP_DIR = BASE_DIR / "temp"

WIDTH = 1080
HEIGHT = 1920
FPS = 30

SUPPORTED_IMAGES = {".jpg", ".jpeg", ".png", ".webp"}
SUPPORTED_VIDEOS = {".mp4", ".mov", ".m4v"}

VOICE_OPTIONS = {
    "American Male": "en-US-GuyNeural",
    "American Female": "en-US-JennyNeural",
    "British Female": "en-GB-SoniaNeural",
}


# =========================================================
# General utilities
# =========================================================

def initialize_directories() -> None:
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)


def safe_filename(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_") or "untitled"


def save_uploaded_file(uploaded_file, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)

    with destination.open("wb") as file:
        file.write(uploaded_file.getbuffer())

    return destination


# =========================================================
# SQLite database
# =========================================================

def get_database_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_FILE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database() -> None:
    with get_database_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS pioneers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT,
                project_title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(name, project_title)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS video_shorts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pioneer_id INTEGER NOT NULL,
                video_title TEXT NOT NULL,
                script_text TEXT NOT NULL,
                video_short_path TEXT NOT NULL,
                duration_seconds REAL,
                voice_name TEXT,
                status TEXT NOT NULL DEFAULT 'generated',
                created_at TEXT NOT NULL,
                FOREIGN KEY (pioneer_id)
                    REFERENCES pioneers(id)
                    ON DELETE CASCADE
            )
            """
        )


def get_or_create_pioneer(
    name: str,
    category: str,
    project_title: str,
) -> int:
    created_at = datetime.now().isoformat(timespec="seconds")

    with get_database_connection() as connection:
        existing = connection.execute(
            """
            SELECT id
            FROM pioneers
            WHERE name = ? AND project_title = ?
            """,
            (name.strip(), project_title.strip()),
        ).fetchone()

        if existing:
            connection.execute(
                """
                UPDATE pioneers
                SET category = ?
                WHERE id = ?
                """,
                (category.strip(), existing["id"]),
            )
            return int(existing["id"])

        cursor = connection.execute(
            """
            INSERT INTO pioneers (
                name,
                category,
                project_title,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                name.strip(),
                category.strip(),
                project_title.strip(),
                created_at,
            ),
        )

        return int(cursor.lastrowid)


def save_video_record(
    pioneer_id: int,
    video_title: str,
    script_text: str,
    video_path: Path,
    duration_seconds: float,
    voice_name: str,
) -> None:
    with get_database_connection() as connection:
        connection.execute(
            """
            INSERT INTO video_shorts (
                pioneer_id,
                video_title,
                script_text,
                video_short_path,
                duration_seconds,
                voice_name,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pioneer_id,
                video_title.strip(),
                script_text.strip(),
                str(video_path),
                round(duration_seconds, 2),
                voice_name,
                "generated",
                datetime.now().isoformat(timespec="seconds"),
            ),
        )


def load_video_records() -> list[sqlite3.Row]:
    with get_database_connection() as connection:
        return connection.execute(
            """
            SELECT
                video_shorts.id,
                pioneers.name AS pioneer_name,
                pioneers.category,
                pioneers.project_title,
                video_shorts.video_title,
                video_shorts.video_short_path,
                video_shorts.duration_seconds,
                video_shorts.status,
                video_shorts.created_at
            FROM video_shorts
            JOIN pioneers
                ON pioneers.id = video_shorts.pioneer_id
            ORDER BY video_shorts.id DESC
            """
        ).fetchall()


# =========================================================
# Text-to-speech
# =========================================================

async def generate_narration_async(
    text: str,
    voice: str,
    output_path: Path,
    rate: str,
) -> None:
    communication = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate,
    )

    await communication.save(str(output_path))


def generate_narration(
    text: str,
    voice: str,
    output_path: Path,
    rate: str,
) -> None:
    asyncio.run(
        generate_narration_async(
            text=text,
            voice=voice,
            output_path=output_path,
            rate=rate,
        )
    )


# =========================================================
# Image processing
# =========================================================

def prepare_vertical_image(
    source_path: Path,
    destination_path: Path,
) -> Path:
    with Image.open(source_path) as source:
        image = source.convert("RGB")

        source_ratio = image.width / image.height
        target_ratio = WIDTH / HEIGHT

        if source_ratio > target_ratio:
            new_width = int(image.height * target_ratio)
            left = (image.width - new_width) // 2

            image = image.crop(
                (
                    left,
                    0,
                    left + new_width,
                    image.height,
                )
            )
        else:
            new_height = int(image.width / target_ratio)
            top = (image.height - new_height) // 2

            image = image.crop(
                (
                    0,
                    top,
                    image.width,
                    top + new_height,
                )
            )

        image = image.resize(
            (WIDTH, HEIGHT),
            Image.Resampling.LANCZOS,
        )

        image.save(destination_path, quality=95)

    return destination_path


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


# =========================================================
# Caption generation
# =========================================================

def split_script_into_captions(
    script: str,
    words_per_caption: int = 8,
) -> list[str]:
    words = script.replace("\n", " ").split()

    return [
        " ".join(words[index:index + words_per_caption])
        for index in range(0, len(words), words_per_caption)
    ]


def create_caption_image(
    text: str,
    destination_path: Path,
) -> Path:
    caption_height = 500

    canvas = Image.new(
        "RGBA",
        (WIDTH, caption_height),
        (0, 0, 0, 0),
    )

    draw = ImageDraw.Draw(canvas)
    font = load_font(68)

    wrapped_text = textwrap.fill(text, width=25)

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

    draw.rounded_rectangle(
        background_box,
        radius=30,
        fill=(0, 0, 0, 185),
    )

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


# =========================================================
# Video processing
# =========================================================

def prepare_video_clip(
    source_path: Path,
    required_duration: float,
):
    clip = VideoFileClip(str(source_path))

    source_ratio = clip.w / clip.h
    target_ratio = WIDTH / HEIGHT

    if source_ratio > target_ratio:
        crop_width = int(clip.h * target_ratio)
        x_center = clip.w / 2

        clip = clip.cropped(
            x_center=x_center,
            width=crop_width,
        )
    else:
        crop_height = int(clip.w / target_ratio)
        y_center = clip.h / 2

        clip = clip.cropped(
            y_center=y_center,
            height=crop_height,
        )

    clip = clip.resized(new_size=(WIDTH, HEIGHT))

    if clip.duration >= required_duration:
        return clip.subclipped(0, required_duration)

    copies_needed = int(required_duration / clip.duration) + 1

    repeated = concatenate_videoclips(
        [clip for _ in range(copies_needed)],
        method="compose",
    )

    return repeated.subclipped(0, required_duration)


def create_background_video(
    asset_paths: list[Path],
    duration: float,
    job_directory: Path,
):
    duration_per_asset = duration / len(asset_paths)
    clips = []

    for index, asset_path in enumerate(asset_paths):
        extension = asset_path.suffix.lower()

        if extension in SUPPORTED_IMAGES:
            prepared_path = (
                job_directory /
                f"prepared_image_{index:04d}.jpg"
            )

            prepare_vertical_image(
                asset_path,
                prepared_path,
            )

            clip = (
                ImageClip(str(prepared_path))
                .with_duration(duration_per_asset)
            )

            clips.append(clip)

        elif extension in SUPPORTED_VIDEOS:
            clip = prepare_video_clip(
                asset_path,
                duration_per_asset,
            )

            clips.append(clip)

    if not clips:
        raise ValueError("No supported image or video assets were found.")

    return concatenate_videoclips(
        clips,
        method="compose",
    ).with_duration(duration)


def create_caption_clips(
    script: str,
    duration: float,
    job_directory: Path,
):
    captions = split_script_into_captions(script)

    if not captions:
        return []

    caption_duration = duration / len(captions)
    caption_clips = []

    for index, caption_text in enumerate(captions):
        caption_path = (
            job_directory /
            f"caption_{index:04d}.png"
        )

        create_caption_image(
            caption_text,
            caption_path,
        )

        caption_clip = (
            ImageClip(str(caption_path))
            .with_start(index * caption_duration)
            .with_duration(caption_duration)
            .with_position(("center", 1250))
        )

        caption_clips.append(caption_clip)

    return caption_clips


def create_final_audio(
    narration_path: Path,
    music_path: Path | None,
    duration: float,
    music_volume: float,
):
    narration = AudioFileClip(str(narration_path))

    if not music_path:
        return narration

    music = AudioFileClip(str(music_path))

    if music.duration < duration:
        copies_needed = int(duration / music.duration) + 1

        music = concatenate_audioclips(
            [music for _ in range(copies_needed)]
        )

    music = (
        music
        .subclipped(0, duration)
        .with_volume_scaled(music_volume)
    )

    return CompositeAudioClip(
        [
            music,
            narration,
        ]
    )


def generate_short(
    pioneer_name: str,
    video_title: str,
    script: str,
    asset_paths: list[Path],
    music_path: Path | None,
    voice: str,
    voice_rate: str,
    music_volume: float,
    job_directory: Path,
) -> tuple[Path, float]:
    narration_path = job_directory / "narration.mp3"

    generate_narration(
        text=script,
        voice=voice,
        output_path=narration_path,
        rate=voice_rate,
    )

    narration_clip = AudioFileClip(str(narration_path))
    duration = narration_clip.duration
    narration_clip.close()

    background_video = create_background_video(
        asset_paths=asset_paths,
        duration=duration,
        job_directory=job_directory,
    )

    caption_clips = create_caption_clips(
        script=script,
        duration=duration,
        job_directory=job_directory,
    )

    final_video = CompositeVideoClip(
        [background_video, *caption_clips],
        size=(WIDTH, HEIGHT),
    ).with_duration(duration)

    final_audio = create_final_audio(
        narration_path=narration_path,
        music_path=music_path,
        duration=duration,
        music_volume=music_volume,
    )

    final_video = final_video.with_audio(final_audio)

    pioneer_folder = (
        GENERATED_DIR /
        safe_filename(pioneer_name)
    )

    pioneer_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = pioneer_folder / (
        f"{safe_filename(video_title)}_"
        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    )

    final_video.write_videofile(
        str(output_path),
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        bitrate="7000k",
        audio_bitrate="192k",
        preset="medium",
        threads=4,
    )

    final_video.close()
    background_video.close()
    final_audio.close()

    return output_path, duration


# =========================================================
# Streamlit interface
# =========================================================

def render_application() -> None:
    st.set_page_config(
        page_title="Black Pioneers Studio",
        page_icon="🎬",
        layout="wide",
    )

    st.title("Black Pioneers Studio")
    st.caption(PROJECT_TITLE)

    with st.container(border=True):
        st.subheader("1. Pioneer and Script")

        column_one, column_two = st.columns(2)

        with column_one:
            pioneer_name = st.text_input(
                "Pioneer name",
                placeholder="Example: Hiram Revels",
            )

            category = st.text_input(
                "Category",
                placeholder="Example: Politics and Government",
            )

        with column_two:
            project_title = st.text_input(
                "Project title",
                value=PROJECT_TITLE,
            )

            video_title = st.text_input(
                "Video title",
                placeholder="First African American U.S. Senator",
            )

        script_text = st.text_area(
            "Script / narration text",
            height=220,
            placeholder=(
                "Enter the complete narration script for the Short."
            ),
        )

        st.caption(
            f"Characters: {len(script_text)} | "
            f"Estimated narration: "
            f"{max(1, round(len(script_text.split()) / 2.4))} seconds"
        )

    with st.container(border=True):
        st.subheader("2. Assets / Media")

        media_files = st.file_uploader(
            "Upload images or video clips",
            type=[
                "jpg",
                "jpeg",
                "png",
                "webp",
                "mp4",
                "mov",
                "m4v",
            ],
            accept_multiple_files=True,
        )

        if media_files:
            st.success(
                f"{len(media_files)} media file(s) selected."
            )

    with st.container(border=True):
        st.subheader("3. Background Music and Voice")

        music_file = st.file_uploader(
            "Upload optional background music",
            type=["mp3", "wav", "m4a"],
            accept_multiple_files=False,
        )

        voice_label = st.selectbox(
            "Narration voice",
            options=list(VOICE_OPTIONS.keys()),
        )

        voice_rate_value = st.slider(
            "Voice speed",
            min_value=-20,
            max_value=30,
            value=5,
            step=5,
        )

        music_volume = st.slider(
            "Background music volume",
            min_value=0.0,
            max_value=0.5,
            value=0.10,
            step=0.05,
        )

    with st.container(border=True):
        st.subheader("4. Create Short")

        create_button = st.button(
            "Create YouTube Short",
            type="primary",
            use_container_width=True,
        )

        if create_button:
            errors = []

            if not pioneer_name.strip():
                errors.append("Pioneer name is required.")

            if not video_title.strip():
                errors.append("Video title is required.")

            if not script_text.strip():
                errors.append("Script text is required.")

            if not media_files:
                errors.append(
                    "At least one image or video asset is required."
                )

            if errors:
                for error in errors:
                    st.error(error)

                return

            job_id = uuid.uuid4().hex
            job_directory = TEMP_DIR / job_id
            job_directory.mkdir(parents=True, exist_ok=True)

            try:
                with st.status(
                    "Creating YouTube Short...",
                    expanded=True,
                ) as status:
                    st.write("Saving uploaded media...")

                    asset_paths = []

                    for index, media_file in enumerate(media_files):
                        destination = (
                            job_directory /
                            f"asset_{index:04d}_"
                            f"{safe_filename(media_file.name)}"
                            f"{Path(media_file.name).suffix.lower()}"
                        )

                        asset_paths.append(
                            save_uploaded_file(
                                media_file,
                                destination,
                            )
                        )

                    saved_music_path = None

                    if music_file:
                        saved_music_path = save_uploaded_file(
                            music_file,
                            job_directory /
                            f"background_music"
                            f"{Path(music_file.name).suffix.lower()}",
                        )

                    st.write("Generating narration and captions...")

                    output_path, duration = generate_short(
                        pioneer_name=pioneer_name,
                        video_title=video_title,
                        script=script_text,
                        asset_paths=asset_paths,
                        music_path=saved_music_path,
                        voice=VOICE_OPTIONS[voice_label],
                        voice_rate=f"{voice_rate_value:+d}%",
                        music_volume=music_volume,
                        job_directory=job_directory,
                    )

                    st.write("Saving database record...")

                    pioneer_id = get_or_create_pioneer(
                        name=pioneer_name,
                        category=category,
                        project_title=project_title,
                    )

                    save_video_record(
                        pioneer_id=pioneer_id,
                        video_title=video_title,
                        script_text=script_text,
                        video_path=output_path,
                        duration_seconds=duration,
                        voice_name=VOICE_OPTIONS[voice_label],
                    )

                    status.update(
                        label="Short created successfully.",
                        state="complete",
                        expanded=False,
                    )

                st.success(
                    f"Saved under pioneer: {pioneer_name}"
                )

                st.video(str(output_path))

                with output_path.open("rb") as video_file:
                    st.download_button(
                        label="Download MP4",
                        data=video_file.read(),
                        file_name=output_path.name,
                        mime="video/mp4",
                        use_container_width=True,
                    )

                st.code(str(output_path))

            except Exception as error:
                st.exception(error)

            finally:
                shutil.rmtree(
                    job_directory,
                    ignore_errors=True,
                )

    st.divider()
    st.subheader("Generated Shorts Database")

    records = load_video_records()

    if records:
        table_data = [
            {
                "Pioneer": record["pioneer_name"],
                "Category": record["category"],
                "Video Title": record["video_title"],
                "Duration": record["duration_seconds"],
                "Status": record["status"],
                "Created": record["created_at"],
                "File": record["video_short_path"],
            }
            for record in records
        ]

        st.dataframe(
            table_data,
            use_container_width=True,
            hide_index=True,
        )

        selected_video = st.selectbox(
            "Preview an existing generated Short",
            options=[
                record["video_short_path"]
                for record in records
            ],
        )

        selected_path = Path(selected_video)

        if selected_path.exists():
            st.video(str(selected_path))
        else:
            st.warning(
                "The database record exists, but the video file "
                "was not found."
            )
    else:
        st.info("No Shorts have been generated yet.")


# =========================================================
# Program entry point
# =========================================================

if __name__ == "__main__":
    initialize_directories()
    initialize_database()
    render_application()
