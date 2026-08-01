# Black Pioneers Studio

## Overview

**Black Pioneers Studio** is a Streamlit-based project for creating educational short-form videos about Black American pioneers.

The Streamlit entry point is `app.py`. Shared logic now lives in the `black_pioneers_studio/` package.

The project is designed for the **Black Pioneers: First in American History** educational series.

---

## Project Goals

- Build a complete YouTube Shorts production studio.
- Automate repetitive video editing tasks.
- Organize pioneer profiles.
- Maintain a searchable SQLite database.
- Produce consistent educational content.

---

## Core Features

### Pioneer Management

- Add pioneer profiles
- Categorize pioneers
- Store achievement and biography notes

### Script Editor

- Enter and edit narration scripts
- Character counter
- Estimated narration duration

### Media Library

Supported formats:

#### Images

- JPG
- JPEG
- PNG
- WEBP

#### Video

- MP4
- MOV
- M4V

#### Audio

- MP3
- WAV
- M4A

### AI Narration

Powered by Microsoft Edge TTS.

- Multiple voice selections
- Adjustable speaking speed
- Automatic narration generation

### Video Generation

- Vertical output (1080 × 1920)
- AI narration
- Automatic subtitles/captions
- Background music mixing
- H.264 MP4 export

---

## Database

SQLite data is stored in:

- `database/pioneers.db` (used by both entry points)

There is no tracked `database/black_pioneers.db` file in this repository.

---

## Core Modules

- `database/connection.py` — SQLite connection setup
- `database/migrations.py` — schema and migrations
- `database/pioneer_repository.py` — pioneer persistence
- `database/video_repository.py` — generated video listing
- `black_pioneers_studio/media.py` — media files, folders, and image/video prep
- `black_pioneers_studio/narration.py` — Edge TTS narration
- `black_pioneers_studio/captions.py` — caption rendering
- `black_pioneers_studio/rendering.py` — final short generation
- `black_pioneers_studio/models.py` — shared data types
- `black_pioneers_studio/paths.py` — project paths and constants

---

## Project Structure

```text
Black_Pioneers_Studio/
├── app.py
├── README.md
├── requirements.txt
├── LICENSE
├── SECURITY.md
├── .gitignore
├── database/
│   ├── connection.py
│   ├── migrations.py
│   ├── pioneer_repository.py
│   ├── video_repository.py
│   └── db.py
├── black_pioneers_studio/
│   ├── captions.py
│   ├── media.py
│   ├── models.py
│   ├── narration.py
│   ├── paths.py
│   └── rendering.py
├── assets/
│   ├── images/
│   ├── music/
│   └── video/
├── database/
│   ├── db.py
│   └── pioneers.db                   # runtime-created, gitignored
├── generated/                        # runtime-created, gitignored
├── scripts/
│   └── update_dependencies.sh
├── temp/                             # runtime-created, gitignored
└── output/                           # runtime-created, gitignored (used by app.py)
```

---

## Technology Stack

- Python 3
- Streamlit
- SQLite
- MoviePy
- FFmpeg
- Pillow
- Edge-TTS
- Pandas
- OpenPyXL

---

## Installation

Create and activate a virtual environment, then install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Primary run command:

```bash
streamlit run app.py
```

### Local Mac Use (Desktop Launcher)

If you only need local use on macOS, you can run a dedicated launcher that starts
Streamlit and opens the app automatically in your browser.

Run launcher:

```bash
source .venv/bin/activate
python desktop_launcher.py
```

Build a macOS desktop app bundle (`.app`):

```bash
bash scripts/build_mac_desktop_app.sh
```

After build, open:

```text
dist/Black Pioneers Studio.app
```

---

## Production Deployment (Fletcher)

This repository is ready to deploy on Fletcher with Streamlit.

### Runtime command

The startup command is defined in `Procfile`:

```text
web: streamlit run app.py --server.port ${PORT:-8501} --server.address 0.0.0.0
```

### Streamlit production config

Production server settings are defined in `.streamlit/config.toml`:

- `headless = true`
- `address = "0.0.0.0"`
- `port = 8501` (platform port override supported through `PORT`)

### Fletcher requirements checklist

Before go-live, confirm:

1. Install Python dependencies from `requirements.txt`.
2. `ffmpeg` is available on `PATH` (required by MoviePy rendering).
3. Writable runtime directories are allowed for:
   - `temp/`
   - `output/`
   - `database/` (SQLite file persistence)
4. Environment exposes a web port (`PORT`) for the Streamlit process.

### CI validation

GitHub Actions workflow `.github/workflows/ci.yml` validates:

- dependency install
- `python -m py_compile app.py database/*.py black_pioneers_studio/*.py`
- smoke tests in `tests/test_streamlit_smoke.py`

---

## Workflow

1. Enter pioneer and script information.
2. Upload images and/or video clips.
3. Optionally upload background music.
4. Generate narration, captions, and final short.
5. Preview and download the rendered MP4.

---

## Roadmap

### Version 1.0

- Project management
- SQLite database
- Script editor
- Media management
- AI narration
- YouTube Shorts generation

### Version 2.0

- Automatic thumbnail generation
- Batch video generation
- Timeline editor
- Caption templates
- Voice presets

### Version 3.0

- YouTube upload integration
- Metadata generation
- Analytics dashboard
- Multi-language support
- AI-assisted script enhancement

---

## License

This project is intended for educational and historical content creation. Users are responsible for ensuring they have the necessary rights to all images, music, video, and other media used in generated content.

---

## Project

### Black Pioneers: First in American History

A digital initiative dedicated to documenting, preserving, and sharing the achievements of Black American pioneers through searchable profiles, educational resources, and short-form videos.
