from pathlib import Path

import streamlit as st

PROJECT_TITLE = "Black Pioneers: First in American History"


def initialize_database() -> None:
    """Initialize the database."""
    pass


def get_all_pioneers():
    """Get all pioneers from the database."""
    return []


def create_pioneer(
    name: str, category: str, achievement: str, biography: str
) -> int:
    """Create a new pioneer in the database."""
    return 1


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output" / "pioneers"
TEMP_DIR = BASE_DIR / "temp"


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
    col2.metric("Generated Shorts", 0)
    col3.metric("Video Format", "1080 × 1920")

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

            st.caption(
                f"Category: {pioneer['category'] or 'Not specified'}"
            )


def render_create_pioneer() -> None:
    """Display the pioneer creation form."""

    st.title("Create Pioneer")

    with st.form("create_pioneer_form", clear_on_submit=True):
        name = st.text_input(
            "Pioneer name",
            placeholder="Example: Hiram Revels",
        )

        category = st.text_input(
            "Category",
            placeholder="Example: Politics & Government",
        )

        achievement = st.text_area(
            "Historic achievement",
            placeholder="First African American U.S. Senator",
        )

        biography = st.text_area(
            "Biography or research notes",
            height=180,
        )

        submitted = st.form_submit_button(
            "Save Pioneer",
            type="primary",
        )

    if submitted:
        if not name.strip():
            st.error("Pioneer name is required.")
            return

        try:
            pioneer_id = create_pioneer(
                name=name.strip(),
                category=category.strip(),
                achievement=achievement.strip(),
                biography=biography.strip(),
            )

            pioneer_directory = OUTPUT_DIR / str(pioneer_id)
            pioneer_directory.mkdir(parents=True, exist_ok=True)

            st.success(f"{name.strip()} was added successfully.")

        except Exception as exc:
            st.error(f"Unable to save pioneer: {exc}")


def render_create_short() -> None:
    """Display the first version of the Short creation workflow."""

    st.title("Create YouTube Short")

    pioneers = get_all_pioneers()

    if not pioneers:
        st.warning("Create at least one pioneer before generating a video.")
        return

    pioneer_names = {
        pioneer["name"]: pioneer["id"]
        for pioneer in pioneers
    }

    selected_name = st.selectbox(
        "Select pioneer",
        options=list(pioneer_names.keys()),
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

    st.checkbox(
        "Generate automatic captions",
        value=True,
        disabled=True,
    )

    if st.button("Generate Short", type="primary"):
        if not script.strip():
            st.error("A narration script is required.")
            return

        if not images and not video_assets:
            st.error("Upload at least one image or video asset.")
            return

        st.info(
            "The video-generation pipeline will be connected in the "
            "next module."
        )

        st.json(
            {
                "pioneer_id": pioneer_names[selected_name],
                "pioneer": selected_name,
                "script_length": len(script),
                "image_count": len(images or []),
                "video_asset_count": len(video_assets or []),
                "background_music": music.name if music else None,
                "voice": voice,
                "narration_rate": narration_rate,
                "resolution": "1080x1920",
            }
        )


def render_video_library() -> None:
    """Display generated videos."""

    st.title("Video Library")
    st.info("Generated pioneer videos will appear here.")


def render_settings() -> None:
    """Display application configuration."""

    st.title("Settings")

    st.text_input(
        "Output directory",
        value=str(OUTPUT_DIR),
        disabled=True,
    )

    st.text_input(
        "Temporary directory",
        value=str(TEMP_DIR),
        disabled=True,
    )

    st.selectbox(
        "Default resolution",
        ["1080x1920"],
        disabled=True,
    )

    st.selectbox(
        "Default frame rate",
        [30, 24, 60],
        index=0,
    )


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
    elif selected_page == "Settings":
        render_settings()


if __name__ == "__main__":
    main()
