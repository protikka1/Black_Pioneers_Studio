from __future__ import annotations

import csv
import io
import os
import shutil
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

import streamlit as st

from black_pioneers_studio.jobs import RenderJobManager
from database.connection import initialize_database
from database.pioneer_repository import (
    create_pioneer,
    get_all_pioneers,
    update_pioneer_folder,
)
from database.video_repository import count_generated_shorts, list_generated_videos
from black_pioneers_studio.media import (
    get_or_create_pioneer_folder,
    make_safe_folder_name,
    save_uploaded_file,
)
from black_pioneers_studio.paths import (
    CAPTION_MAX_OPACITY,
    HEIGHT,
    OUTPUT_DIR,
    PIONEERS_OUTPUT_DIR,
    PROJECT_TITLE,
    TEMP_DIR,
    ensure_runtime_directories,
)
from black_pioneers_studio.rendering import build_render_fingerprint, generate_short


@st.cache_resource
def get_render_job_manager() -> RenderJobManager:
    return RenderJobManager(max_workers=2)


def get_caption_max_opacity() -> int:
    if CAPTION_MAX_OPACITY <= 0:
        raise ValueError("CAPTION_MAX_OPACITY must be greater than zero.")
    return CAPTION_MAX_OPACITY


def opacity_to_percentage(opacity: int) -> int:
    return int(opacity / get_caption_max_opacity() * 100)


def percentage_to_opacity(percentage: int) -> int:
    return int(percentage / 100 * get_caption_max_opacity())


def configure_application() -> None:
    """Configure Streamlit and create required directories."""

    st.set_page_config(
        page_title="Black Pioneers Studio",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    ensure_runtime_directories()
    initialize_database()


def render_sidebar() -> str:
    """Render the main application navigation."""

    st.sidebar.title("Black Pioneers Studio")
    st.sidebar.caption(PROJECT_TITLE)

    pioneers = get_all_pioneers()
    if pioneers:
        pioneer_by_name: dict[str, dict[str, object]] = {
            str(pioneer["name"]): pioneer
            for pioneer in pioneers
        }
        pioneer_names = sorted(pioneer_by_name.keys())

        default_name = st.session_state.get("selected_pioneer_name")
        default_index = 0
        if default_name in pioneer_names:
            default_index = pioneer_names.index(default_name)

        selected_name = st.sidebar.selectbox(
            "Pioneers collection",
            options=pioneer_names,
            index=default_index,
            help="Choose a saved pioneer profile.",
            key="sidebar_pioneer_selector",
        )

        st.session_state["selected_pioneer_name"] = selected_name
        st.session_state["selected_pioneer_id"] = int(
            str(pioneer_by_name[selected_name]["id"])
        )
    else:
        st.sidebar.info("No pioneers yet. Add one from Create Pioneer.")

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

    pioneer_by_name: dict[str, dict[str, object]] = {
        str(pioneer["name"]): pioneer
        for pioneer in pioneers
    }
    pioneer_names = sorted(pioneer_by_name.keys())

    default_name = st.session_state.get("selected_pioneer_name")
    default_index = 0
    if default_name in pioneer_names:
        default_index = pioneer_names.index(default_name)

    selected_name = st.selectbox(
        "Pioneers collection",
        options=pioneer_names,
        index=default_index,
        help="Choose a saved pioneer profile.",
        key="dashboard_pioneer_selector",
    )
    if selected_name is None:
        return

    selected_pioneer = pioneer_by_name[selected_name]
    st.session_state["selected_pioneer_name"] = selected_name
    st.session_state["selected_pioneer_id"] = int(str(selected_pioneer["id"]))

    show_preview = st.checkbox(
        "Show selected pioneer preview",
        value=st.session_state.get("dashboard_show_preview", False),
        key="dashboard_show_preview",
    )

    if show_preview:
        st.caption("Selected pioneer preview")
        with st.container(border=True):
            st.markdown(f"### {selected_pioneer['name']}")

            if selected_pioneer["achievement"]:
                st.write(selected_pioneer["achievement"])

            st.caption(f"Category: {selected_pioneer['category'] or 'Not specified'}")

            if selected_pioneer.get("biography"):
                with st.expander("Biography"):
                    st.write(str(selected_pioneer["biography"]).strip())

        st.divider()

    st.caption("Pioneer collection")

    collection_rows = []
    for pioneer in pioneers:
        if show_preview and int(str(pioneer["id"])) == st.session_state["selected_pioneer_id"]:
            continue

        achievement = str(pioneer.get("achievement") or "").strip()
        if len(achievement) > 90:
            achievement = f"{achievement[:87]}..."

        collection_rows.append(
            {
                "Name": str(pioneer["name"]),
                "Category": str(pioneer.get("category") or "Not specified"),
                "Achievement": achievement or "-",
            }
        )

    if collection_rows:
        st.dataframe(collection_rows, hide_index=True)


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
    job_manager = get_render_job_manager()
    pioneers = get_all_pioneers()

    if not pioneers:
        st.warning("Create at least one pioneer before generating a video.")
        return

    pioneer_by_name: dict[str, dict[str, object]] = {
        str(pioneer["name"]): pioneer
        for pioneer in pioneers
    }
    pioneer_names = sorted(pioneer_by_name.keys())

    default_name = st.session_state.get("selected_pioneer_name")
    default_index = 0
    if default_name in pioneer_names:
        default_index = pioneer_names.index(default_name)

    selected_name = st.selectbox(
        "Pioneers collection",
        options=pioneer_names,
        index=default_index,
        help="Choose a saved pioneer profile.",
    )
    if selected_name is None:
        st.warning("Select a pioneer to continue.")
        return

    st.session_state["selected_pioneer_name"] = selected_name
    st.session_state["selected_pioneer_id"] = int(
        str(pioneer_by_name[selected_name]["id"])
    )

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

    current_form_signature = (
        selected_name,
        script.strip(),
        voice,
        narration_rate,
        round(music_volume, 4),
        tuple((uploaded.name, uploaded.size) for uploaded in (images or [])),
        tuple((uploaded.name, uploaded.size) for uploaded in (video_assets or [])),
        (music.name, music.size) if music else None,
    )

    active_job_id = st.session_state.get("active_render_job_id")
    active_job = job_manager.get_job(active_job_id) if active_job_id else None
    job_is_active = active_job is not None and active_job.status in {"queued", "running"}
    preview_signature = st.session_state.get("active_render_preview_signature")

    if (
        active_job is not None
        and active_job.status in {"completed", "failed"}
        and preview_signature is not None
        and preview_signature != current_form_signature
    ):
        st.session_state.pop("active_render_job_id", None)
        st.session_state.pop("active_render_preview_signature", None)
        active_job = None
        job_is_active = False

    if active_job is not None:
        st.caption(f"Render job: {active_job.job_id}")
        st.progress(active_job.progress, text=f"Status: {active_job.status}")
        if st.button("Clear Preview", key="clear_render_preview"):
            st.session_state.pop("active_render_job_id", None)
            st.session_state.pop("active_render_preview_signature", None)
            st.rerun()

        if active_job.status == "completed" and active_job.output_path is not None:
            output_path = active_job.output_path
            st.success("Short created successfully.")
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
            if st.button("Clear Completed Job"):
                st.session_state.pop("active_render_job_id", None)
                st.session_state.pop("active_render_preview_signature", None)
                st.rerun()
        elif active_job.status == "failed":
            error_message = active_job.error_message or "Unknown rendering error."
            st.error(f"Unable to generate short: {error_message}")
            if "readable duration" in error_message:
                st.info(
                    "One of the uploaded videos appears unreadable or has no duration. "
                    "Try another video file or convert it to MP4 (H.264 + AAC)."
                )
            if "ffmpeg" in error_message.lower():
                st.info("FFmpeg is required for video rendering and must be installed on your system.")
            if st.button("Clear Failed Job"):
                st.session_state.pop("active_render_job_id", None)
                st.session_state.pop("active_render_preview_signature", None)
                st.rerun()
        else:
            st.info("Rendering in background. Use Refresh while this page remains responsive.")
            st.button("Refresh Job Status", key="refresh_render_job_status")

    if st.button("Generate Short", type="primary", disabled=job_is_active):
        if not script.strip():
            st.error("A narration script is required.")
            return

        if not images and not video_assets:
            st.error("Upload at least one image or video asset.")
            return

        selected_pioneer = pioneer_by_name[selected_name]
        pioneer_folder = get_or_create_pioneer_folder(selected_pioneer)
        selected_pioneer_id = int(str(selected_pioneer["id"]))

        uploaded_assets = [*(images or []), *(video_assets or [])]
        words_per_caption = st.session_state.get("caption_words_per_caption", 8)
        caption_y = st.session_state.get("caption_y_position", 1250)
        caption_font_size = st.session_state.get("caption_font_size", 68)
        caption_bg_opacity = st.session_state.get("caption_bg_opacity", 185)

        job_directory = TEMP_DIR / uuid.uuid4().hex
        job_directory.mkdir(parents=True, exist_ok=True)

        try:
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

            request_key = build_render_fingerprint(
                pioneer_name=selected_name,
                script=script.strip(),
                asset_paths=asset_paths,
                music_path=saved_music_path,
                voice=voice,
                narration_rate=narration_rate,
                music_volume=music_volume,
                words_per_caption=words_per_caption,
                caption_y=caption_y,
                caption_font_size=caption_font_size,
                caption_bg_opacity=caption_bg_opacity,
            )

            def render_task(report_progress):
                try:
                    report_progress(0.15)
                    output_path, _duration = generate_short(
                        pioneer_name=selected_name,
                        script=script.strip(),
                        asset_paths=asset_paths,
                        music_path=saved_music_path,
                        voice=voice,
                        narration_rate=narration_rate,
                        music_volume=music_volume,
                        pioneer_folder=pioneer_folder,
                        job_directory=job_directory,
                        words_per_caption=words_per_caption,
                        caption_y=caption_y,
                        caption_font_size=caption_font_size,
                        caption_bg_opacity=caption_bg_opacity,
                    )
                    report_progress(0.95)
                    return output_path
                finally:
                    shutil.rmtree(job_directory, ignore_errors=True)

            job = job_manager.run_render_job(
                pioneer_id=selected_pioneer_id,
                task=render_task,
                request_key=request_key,
            )
            st.session_state["active_render_job_id"] = job.job_id
            if job.status in {"queued", "running"}:
                st.success(f"Render job queued: {job.job_id}")
            else:
                st.success(f"Reusing existing render job: {job.job_id}")
            st.session_state["active_render_preview_signature"] = current_form_signature
            st.rerun()
        except Exception as exc:
            st.error(f"Unable to generate short: {exc}")
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
    """Display tools and utilities: caption layer settings, database export, and storage cleanup."""

    st.title("Tools")

    # ---- Caption Layer Settings ----------------------------------------
    st.subheader("Caption Layer")
    st.caption("These settings apply to automatically generated captions in new videos.")

    col1, col2 = st.columns(2)

    with col1:
        words_per_caption = st.slider(
            "Words per caption",
            min_value=4,
            max_value=16,
            value=st.session_state.get("caption_words_per_caption", 8),
            step=1,
            help="Number of words shown per caption card.",
        )

        caption_font_size = st.slider(
            "Caption font size",
            min_value=40,
            max_value=96,
            value=st.session_state.get("caption_font_size", 68),
            step=4,
            help="Font size for caption text in pixels.",
        )

    with col2:
        caption_y = st.slider(
            "Caption vertical position",
            min_value=900,
            max_value=1700,
            value=st.session_state.get("caption_y_position", 1250),
            step=50,
            help=f"Distance in pixels from the top of the frame ({HEIGHT}px tall). 1250 is the lower third.",
        )

        bg_opacity_pct = st.slider(
            "Caption background opacity",
            min_value=0,
            max_value=100,
            value=opacity_to_percentage(st.session_state.get("caption_bg_opacity", 185)),
            step=5,
            format="%d%%",
            help="Opacity of the dark background box behind caption text.",
        )

    if st.button("Apply Caption Settings", type="primary"):
        st.session_state["caption_words_per_caption"] = words_per_caption
        st.session_state["caption_y_position"] = caption_y
        st.session_state["caption_font_size"] = caption_font_size
        st.session_state["caption_bg_opacity"] = percentage_to_opacity(bg_opacity_pct)
        st.success("Caption layer settings saved. They will be used for all new videos.")

    if st.button("Reset Caption Defaults"):
        for key in ("caption_words_per_caption", "caption_y_position", "caption_font_size", "caption_bg_opacity"):
            st.session_state.pop(key, None)
        st.success("Caption settings reset to defaults.")

    st.divider()

    # ---- Database Tools ------------------------------------------------
    st.subheader("Database")

    pioneers = get_all_pioneers()
    st.metric("Total pioneers", len(pioneers))

    if pioneers:
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=["id", "name", "category", "achievement", "biography", "created_at"],
        )
        writer.writeheader()
        for pioneer in pioneers:
            writer.writerow({
                "id": pioneer["id"],
                "name": pioneer["name"],
                "category": pioneer["category"] or "",
                "achievement": pioneer["achievement"] or "",
                "biography": pioneer["biography"] or "",
                "created_at": pioneer["created_at"],
            })

        st.download_button(
            label="Export pioneers as CSV",
            data=output.getvalue().encode(),
            file_name=f"pioneers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.divider()

    # ---- Storage Utilities --------------------------------------------
    st.subheader("Storage")

    def _dir_size_mb(path: Path) -> float:
        if not path.exists():
            return 0.0
        return sum(f.stat().st_size for f in path.rglob("*") if f.is_file()) / (1024 * 1024)

    temp_mb = _dir_size_mb(TEMP_DIR)
    generated_count = len(list(PIONEERS_OUTPUT_DIR.rglob("*.mp4"))) if PIONEERS_OUTPUT_DIR.exists() else 0

    col3, col4 = st.columns(2)
    col3.metric("Temp directory size", f"{temp_mb:.1f} MB")
    col4.metric("Generated videos", generated_count)

    if st.button("Clear temporary files", disabled=temp_mb == 0):
        failed: list[str] = []

        for root, directories, files in os.walk(TEMP_DIR, topdown=False):
            root_path = Path(root)

            for file_name in files:
                temp_file = root_path / file_name
                try:
                    temp_file.unlink()
                except OSError as exc:
                    failed.append(f"{temp_file.relative_to(TEMP_DIR)}: {exc}")

            for directory_name in directories:
                temp_directory = root_path / directory_name
                try:
                    temp_directory.rmdir()
                except OSError as exc:
                    failed.append(f"{temp_directory.relative_to(TEMP_DIR)}: {exc}")

        if failed:
            st.warning("Some files could not be deleted:\n" + "\n".join(failed))
        else:
            st.success("Temporary files cleared.")
        st.rerun()


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
