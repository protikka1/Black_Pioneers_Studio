# Black Pioneers Studio

## Overview

**Black Pioneers Studio** is a Streamlit-based project for creating educational short-form videos about Black American pioneers.

The repository currently contains two entry points:

- `backup_app.py` — the working end-to-end pipeline (media upload, narration, captions, render, SQLite history table, and video preview/download).
- `app.py` — a scaffold-style multi-page UI path that uses a simpler data model and a separate output layout.

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

## Output Paths by Entry Point

### `backup_app.py` (working pipeline)

- Generated MP4s: `generated/<safe_pioneer_name>/<safe_video_title>_<timestamp>.mp4`
- SQLite database: `database/pioneers.db`
- Temporary job files: `temp/<job_uuid>/` (cleaned up after generation)

### `app.py` (scaffold-style path)

- Per-pioneer base folder: `output/pioneers/<pioneer_id>_<safe_name>/`
- Generated MP4s: `<base_folder>/output/short_<safe_name>_<timestamp>.mp4`
- Related per-pioneer assets: `output/pioneers/<pioneer_id>_<safe_name>/{images,videos,audio,music,captions}/`
- SQLite database file: `database/pioneers.db` (accessed through helpers in `database/db.py`)
- Temporary job files: `temp/<job_uuid>/` (cleaned up after generation)

---

## Project Structure

```text
Black_Pioneers_Studio/
├── app.py
├── backup_app.py
├── README.md
├── requirements.txt
├── LICENSE
├── SECURITY.md
├── .gitignore
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

Primary run command (current working pipeline):

```bash
streamlit run backup_app.py
```

Alternative scaffold UI entry point:

```bash
streamlit run app.py
```

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
