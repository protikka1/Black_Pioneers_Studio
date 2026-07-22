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
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
from moviepy import (
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    VideoFileClip,
    concatenate_audioclips,
    concatenate_videoclips,
)

from database.db import (
    create_pioneer,
    get_all_pioneers,
    initialize_database,
    update_pioneer_folder,
)

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output" / "pioneers"
PIONEERS_OUTPUT_DIR = OUTPUT_DIR
TEMP_DIR = BASE_DIR / "temp"

PROJECT_TITLE = "Black Pioneers: First in American History"
WIDTH = 1080
HEIGHT = 1920
FPS = 30

SUPPORTED_IMAGES = {".jpg", ".jpeg", ".png", ".webp"}
SUPPORTED_VIDEOS = {".mp4", ".mov", ".m4v"}


def make_safe_folder_name(name: str) -> str:
    safe_name = name.strip().lower()
    safe_name = re.sub(r"[^a-z0-9]+", "_", safe_name)
    return safe_name.strip("_")


def save_uploaded_file(uploaded_file, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)

    with destination.open("wb") as file:
        file.write(uploaded_file.getbuffer())

    return destination


def count_generated_shorts() -> int:
    return len(list(PIONEERS_OUTPUT_DIR.rglob("*.mp4")))


def get_or_create_pioneer_folder(pioneer: dict[str, object]) -> Path:
    folder_path = str(pioneer.get("folder_path") or "").strip()

    if folder_path:
        folder = Path(folder_path)
    else:
        pioneer_id = int(pioneer["id"])
        safe_name = make_safe_folder_name(str(pioneer["name"])) or "pioneer"
        folder = PIONEERS_OUTPUT_DIR / f"{pioneer_id}_{safe_name}"
        update_pioneer_folder(pioneer_id=pioneer_id, folder_path=str(folder))

    for subfolder in ["images", "videos", "audio", "music", "captions", "output"]:
        (folder / subfolder).mkdir(parents=True, exist_ok=True)

    return folder


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


def prepare_vertical_image(source_path: Path, destination_path: Path) -> Path:
    with Image.open(source_path) as source:
        image = source.convert("RGB")

        # Keep the full source image visible and fill the remaining space with a soft blurred backdrop.
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


def split_script_into_captions(script: str, words_per_caption: int = 8) -> list[str]:
    words = script.replace("\n", " ").split()
    return [
        " ".join(words[index:index + words_per_caption])
        for index in range(0, len(words), words_per_caption)
    ]


def create_caption_image(text: str, destination_path: Path) -> Path:
    caption_height = 500
    canvas = Image.new("RGBA", (WIDTH, caption_height), (0, 0, 0, 0))
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

    draw.rounded_rectangle(background_box, radius=30, fill=(0, 0, 0, 185))
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

    clip = clip.resized(new_size=(WIDTH, HEIGHT))

    if clip.duration >= required_duration:
        return clip.subclipped(0, required_duration)

    copies_needed = int(required_duration / clip.duration) + 1
    repeated = concatenate_videoclips([clip for _ in range(copies_needed)], method="compose")
    return repeated.subclipped(0, required_duration)


def create_background_video(asset_paths: list[Path], duration: float, job_directory: Path):
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


def create_caption_clips(script: str, duration: float, captions_directory: Path):
    captions = split_script_into_captions(script)

    if not captions:
        return []

    caption_duration = duration / len(captions)
    caption_clips = []

    for index, caption_text in enumerate(captions):
        caption_path = captions_directory / f"caption_{index:04d}.png"
        create_caption_image(caption_text, caption_path)

        caption_clips.append(
            ImageClip(str(caption_path))
            .with_start(index * caption_duration)
            .with_duration(caption_duration)
            .with_position(("center", 1250))
        )

    return caption_clips


async def generate_narration_async(text: str, voice: str, output_path: Path, rate: str) -> None:
    communication = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    await communication.save(str(output_path))


def generate_narration(text: str, voice: str, output_path: Path, rate: str) -> None:
    asyncio.run(
        generate_narration_async(
            text=text,
            voice=voice,
            output_path=output_path,
            rate=rate,
        )
    )


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
        music = concatenate_audioclips([music for _ in range(copies_needed)])

    music = music.subclipped(0, duration).with_volume_scaled(music_volume)
    return CompositeAudioClip([music, narration])


def generate_short(
    pioneer_name: str,
    script: str,
    asset_paths: list[Path],
    music_path: Path | None,
    voice: str,
    narration_rate: int,
    music_volume: float,
    pioneer_folder: Path,
    job_directory: Path,
) -> tuple[Path, float]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    narration_output = pioneer_folder / "audio" / f"narration_{timestamp}.mp3"

    generate_narration(
        text=script,
        voice=voice,
        output_path=narration_output,
        rate=f"{narration_rate:+d}%",
    )

    narration_clip = AudioFileClip(str(narration_output))
    duration = narration_clip.duration
    narration_clip.close()

    background_video = create_background_video(asset_paths, duration, job_directory)
    caption_clips = create_caption_clips(script, duration, pioneer_folder / "captions")

    final_video = CompositeVideoClip([background_video, *caption_clips], size=(WIDTH, HEIGHT))
    final_video = final_video.with_duration(duration)

    final_audio = create_final_audio(
        narration_path=narration_output,
        music_path=music_path,
        duration=duration,
        music_volume=music_volume,
    )

    output_file = pioneer_folder / "output" / f"short_{make_safe_folder_name(pioneer_name)}_{timestamp}.mp4"

    try:
        final_video.with_audio(final_audio).write_videofile(
            str(output_file),
            fps=FPS,
            codec="libx264",
            audio_codec="aac",
            bitrate="7000k",
            audio_bitrate="192k",
            preset="medium",
            threads=4,
        )
    finally:
        final_video.close()
        background_video.close()
        final_audio.close()

    return output_file, duration


def list_generated_videos() -> list[Path]:
    videos = list(PIONEERS_OUTPUT_DIR.rglob("*.mp4"))
    return sorted(videos, key=lambda path: path.stat().st_mtime, reverse=True)


def configure_application() -> None:
    """Configure Streamlit and create required directories."""

    st.set_page_config(
        page_title="Black Pioneers Studio",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    initialize_database()


def render_sidebar() -> str:
    """Render the main application navigation."""

    st.sidebar.title("Black Pioneers Studio")
    st.sidebar.caption(PROJECT_TITLE)

    return st.sidebar.radio(
        "Navigation",
        [
            "Dashboard",
            "Create Pioneer",
            "Create Short",
            "Video Library",
            "Tools",
            "Settings",
        ],
    )


def render_dashboard() -> None:
    """Display project statistics and recent pioneers."""

    st.title("Black Pioneers Studio")
    st.subheader(PROJECT_TITLE)

    pioneers = get_all_pioneers()

    col1, col2, col3 = st.columns(3)

    col1.metric("Pioneers", len(pioneers))
    col2.metric("Generated Shorts", count_generated_shorts())
    col3.metric("Video Format", "1080 x 1920")

    st.divider()
    st.subheader("Pioneers")

    if not pioneers:
        st.info("No pioneers have been added yet.")
        return

    for pioneer in pioneers:
        with st.container(border=True):
            st.markdown(f"### {pioneer['name']}")

            if pioneer["achievement"]:
                st.write(pioneer["achievement"])

            st.caption(f"Category: {pioneer['category'] or 'Not specified'}")


def render_create_pioneer() -> None:
    st.title("Create Pioneer")

    with st.form("create_pioneer_form", clear_on_submit=True):
        name = st.text_input("Pioneer name", placeholder="Hiram Revels")
        category = st.text_input("Category", placeholder="Politics and Government")
        achievement = st.text_area(
            "Historic achievement",
            placeholder="First African American United States Senator",
        )
        biography = st.text_area("Biography or research notes", height=180)
        submitted = st.form_submit_button("Save Pioneer", type="primary")

    if not submitted:
        return

    clean_name = name.strip()

    if not clean_name:
        st.error("Pioneer name is required.")
        return

    safe_folder_name = make_safe_folder_name(clean_name)

    if not safe_folder_name:
        st.error("The pioneer name cannot be used as a folder name.")
        return

    try:
        pioneer_id = create_pioneer(
            name=clean_name,
            category=category.strip(),
            achievement=achievement.strip(),
            biography=biography.strip(),
        )

        pioneer_folder = PIONEERS_OUTPUT_DIR / f"{pioneer_id}_{safe_folder_name}"

        for subfolder in ["images", "videos", "audio", "music", "captions", "output"]:
            (pioneer_folder / subfolder).mkdir(parents=True, exist_ok=True)

        update_pioneer_folder(pioneer_id=pioneer_id, folder_path=str(pioneer_folder))

        st.session_state["selected_pioneer_id"] = pioneer_id
        st.session_state["selected_pioneer_name"] = clean_name

        st.success(f"{clean_name} was saved successfully.")
        st.info("The pioneer is now ready for media upload.")
        st.write("Saved folder:")
        st.code(str(pioneer_folder))

    except sqlite3.IntegrityError:
        st.error("A pioneer with this name already exists.")
    except Exception as exc:
        st.error(f"Unable to save pioneer: {exc}")


def render_create_short() -> None:
    """Render the Short creation workflow with full video generation."""

    st.title("Create YouTube Short")
    pioneers = get_all_pioneers()

    if not pioneers:
        st.warning("Create at least one pioneer before generating a video.")
        return

    pioneer_by_name = {pioneer["name"]: pioneer for pioneer in pioneers}

    selected_name = st.selectbox("Select pioneer", options=list(pioneer_by_name.keys()))

    script = st.text_area(
        "Narration script",
        height=220,
        placeholder=(
            "Did you know Hiram Revels became the first African "
            "American U.S. Senator in 1870?"
        ),
    )

    images = st.file_uploader(
        "Upload images",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
    )

    video_assets = st.file_uploader(
        "Upload optional video assets",
        type=["mp4", "mov", "m4v"],
        accept_multiple_files=True,
    )

    music = st.file_uploader(
        "Upload optional background music",
        type=["mp3", "wav", "m4a"],
    )

    voice = st.selectbox(
        "Narration voice",
        [
            "en-US-GuyNeural",
            "en-US-JennyNeural",
            "en-US-AriaNeural",
            "en-US-DavisNeural",
        ],
    )

    narration_rate = st.slider(
        "Narration speed",
        min_value=-30,
        max_value=30,
        value=0,
        step=5,
        format="%d%%",
    )

    music_volume = st.slider(
        "Background music volume",
        min_value=0.0,
        max_value=0.5,
        value=0.10,
        step=0.05,
    )

    st.checkbox("Generate automatic captions", value=True, disabled=True)

    if st.button("Generate Short", type="primary"):
        if not script.strip():
            st.error("A narration script is required.")
            return

        if not images and not video_assets:
            st.error("Upload at least one image or video asset.")
            return

        selected_pioneer = pioneer_by_name[selected_name]
        pioneer_folder = get_or_create_pioneer_folder(selected_pioneer)

        uploaded_assets = [*(images or []), *(video_assets or [])]

        job_directory = TEMP_DIR / uuid.uuid4().hex
        job_directory.mkdir(parents=True, exist_ok=True)

        try:
            with st.status("Generating YouTube Short...", expanded=True):
                st.write("Saving uploaded assets...")

                asset_paths = []
                for index, uploaded in enumerate(uploaded_assets):
                    asset_stem = make_safe_folder_name(Path(uploaded.name).stem) or f"asset_{index:04d}"
                    destination = job_directory / f"asset_{index:04d}_{asset_stem}{Path(uploaded.name).suffix.lower()}"
                    asset_paths.append(save_uploaded_file(uploaded, destination))

                saved_music_path = None
                if music:
                    music_stem = make_safe_folder_name(Path(music.name).stem) or "music"
                    music_destination = pioneer_folder / "music" / (
                        f"{music_stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{Path(music.name).suffix.lower()}"
                    )
                    saved_music_path = save_uploaded_file(music, music_destination)

                st.write("Rendering video and audio...")

                output_path, duration = generate_short(
                    pioneer_name=selected_name,
                    script=script.strip(),
                    asset_paths=asset_paths,
                    music_path=saved_music_path,
                    voice=voice,
                    narration_rate=narration_rate,
                    music_volume=music_volume,
                    pioneer_folder=pioneer_folder,
                    job_directory=job_directory,
                )

            st.success(f"Short created successfully in {duration:.1f} seconds.")
            st.video(str(output_path))

            with output_path.open("rb") as file:
                st.download_button(
                    label="Download MP4",
                    data=file.read(),
                    file_name=output_path.name,
                    mime="video/mp4",
                    use_container_width=True,
                )

            st.code(str(output_path))

        except Exception as exc:
            st.error(f"Unable to generate short: {exc}")
            if "ffmpeg" in str(exc).lower():
                st.info("FFmpeg is required for video rendering and must be installed on your system.")
        finally:
            shutil.rmtree(job_directory, ignore_errors=True)


def render_video_library() -> None:
    """Display generated videos."""

    st.title("Video Library")
    videos = list_generated_videos()

    if not videos:
        st.info("No generated videos found yet.")
        return

    selected_video = st.selectbox("Preview generated video", options=[str(video) for video in videos])
    selected_path = Path(selected_video)

    st.video(str(selected_path))

    with selected_path.open("rb") as file:
        st.download_button(
            label="Download Selected Video",
            data=file.read(),
            file_name=selected_path.name,
            mime="video/mp4",
            use_container_width=True,
        )

    st.caption(f"Total generated videos: {len(videos)}")


def render_settings() -> None:
    """Display application configuration."""

    st.title("Settings")

    st.text_input("Output directory", value=str(OUTPUT_DIR), disabled=True)
    st.text_input("Temporary directory", value=str(TEMP_DIR), disabled=True)

    st.selectbox("Default resolution", ["1080x1920"], disabled=True)
    st.selectbox("Default frame rate", [30, 24, 60], index=0)


def render_tools() -> None:
    """Display tools and utilities."""

    st.title("Tools")

    st.text_input("Output directory", value=str(OUTPUT_DIR), disabled=True)
    st.text_input("Temporary directory", value=str(TEMP_DIR), disabled=True)

    st.selectbox("Default resolution", ["1080x1920"], disabled=True)
    st.selectbox("Default frame rate", [30, 24, 60], index=0)


def main() -> None:
    configure_application()

    selected_page = render_sidebar()

    if selected_page == "Dashboard":
        render_dashboard()
    elif selected_page == "Create Pioneer":
        render_create_pioneer()
    elif selected_page == "Create Short":
        render_create_short()
    elif selected_page == "Video Library":
        render_video_library()
    elif selected_page == "Tools":
        render_tools()
    elif selected_page == "Settings":
        render_settings()


if __name__ == "__main__":
    main()
