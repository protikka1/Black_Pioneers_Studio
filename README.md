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
python3 -m venv .venv
source .venv/bin/activate
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

## Streamlit Community Cloud deployment

1. Sign in at https://share.streamlit.io/ and connect the GitHub account.
2. Select **Create app** and deploy from this repository:
   - Repository: `protikka1/Black_Pioneers_Studio`
   - Branch: `main` (or the preparation branch when testing before merge)
   - Main file: `app.py`
   - Advanced settings: Python **3.12**
3. Click **Deploy** and inspect the build logs. Python packages are installed from
   `requirements.txt`; FFmpeg and Linux caption fonts are installed from `packages.txt`.
4. Create one pioneer, enter a short script, upload an image, generate a video,
   and download the MP4. Edge TTS requires an outgoing network connection.

Use `app.py` as the cloud entry point. The Mac desktop launcher and its generated
application bundles are for local use.

### Data and access

The app creates a new SQLite database on first run. Your local `pioneers.db` and
media are ignored by Git and are not uploaded during deployment. Treat the local
cloud filesystem as temporary: download videos and export pioneer CSVs from Tools.
Use an external database and object storage for durable production data.

The current app has a shared pioneer collection and no application-level login.
Use it with trusted users; configure platform access before storing private work.
Community Cloud resources are limited, so test short videos first. For regular
1080 × 1920 video production, use a host with sufficient CPU/RAM and persistent storage.

Temporary cleanup is blocked while any render is queued or running. Render audio,
video output, and caption workspaces are isolated to prevent concurrent jobs from
writing to the same files. Caption timing is estimated from equal chunks of the
script rather than speech alignment.

### Other Streamlit hosts

The `Procfile` startup command is:

```text
web: streamlit run app.py --server.port ${PORT:-8501} --server.address 0.0.0.0
```

Install dependencies from `requirements.txt`, install FFmpeg and a supported font,
and allow writes to `temp/`, `output/`, and `database/`. Use persistent storage for
SQLite and generated media on a production host.

### Validation

GitHub Actions installs the Python dependencies and `packages.txt` system packages,
compiles the application modules, and runs the tests on Python 3.12. Before publishing,
also verify one real narration/video render on the deployed server.

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
