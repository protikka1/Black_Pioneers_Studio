# Black Pioneers Studio

**Black Pioneers Studio** is a Python/Streamlit application for creating educational YouTube Shorts about Black American pioneers. It automates the workflow from a written script and uploaded media to a finished vertical video with AI narration, auto-generated captions, optional background music, and an SQLite project database.

> **Documentation status** — this README and the linked docs describe the repository as it currently stands, including known incomplete or placeholder paths. See [Known limitations](docs/architecture.md#known-limitations-and-technical-debt) for details.

---

## Table of Contents

- [Current implementation status](#current-implementation-status)
- [Prerequisites](#prerequisites)
- [Quick start](#quick-start)
- [Application entry points](#application-entry-points)
- [Features](#features)
- [Output locations](#output-locations)
- [Project structure](#project-structure)
- [Documentation](#documentation)
- [Troubleshooting](#troubleshooting)
- [Security and media rights](#security-and-media-rights)
- [Contributing](#contributing)
- [Roadmap](#roadmap)
- [License](#license)

---

## Current implementation status

| Entry point | Status |
|---|---|
| `backup_app.py` | **Complete** — full end-to-end pipeline: narration, captions, video composition, SQLite records. |
| `app.py` | **Partial** — multi-page UI shell with placeholder database functions; video generation is not yet connected. |

Use `backup_app.py` for actual video production. `app.py` is the in-progress multi-page redesign.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.9 or later | Streamlit 1.59 requires Python ≥ 3.9. |
| FFmpeg | Required by MoviePy for video encoding. Must be on your `PATH`. |
| Internet access | Required by Microsoft Edge TTS at generation time. |

Install FFmpeg before installing Python dependencies:

- **macOS (Homebrew):** `brew install ffmpeg`
- **Ubuntu/Debian:** `sudo apt install ffmpeg`
- **Windows:** Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to `PATH`.

---

## Quick start

### macOS / Linux

```bash
git clone https://github.com/protikka1/Black_Pioneers_Studio.git
cd Black_Pioneers_Studio

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

# Full generation pipeline:
streamlit run backup_app.py

# Multi-page UI shell (incomplete):
streamlit run app.py
```

### Windows PowerShell

```powershell
git clone https://github.com/protikka1/Black_Pioneers_Studio.git
cd Black_Pioneers_Studio

python -m venv venv
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt

# Full generation pipeline:
streamlit run backup_app.py
```

---

## Application entry points

### `backup_app.py` — complete pipeline

Single-page Streamlit form that covers all production steps:

1. Pioneer name, category, project title, video title.
2. Narration script with live character count and estimated duration.
3. Image / video asset upload (JPG, JPEG, PNG, WEBP, MP4, MOV, M4V).
4. Optional background music upload (MP3, WAV, M4A) with volume control.
5. Voice and speed selection via Microsoft Edge TTS.
6. Generation: narration → captions → video composition → MP4 export.
7. Inline video preview and MP4 download button.
8. Generated Shorts database table displayed at the bottom of the page.

### `app.py` — in-progress multi-page shell

Multi-page navigation (Dashboard, Create Pioneer, Create Short, Video Library, Settings) with working UI but placeholder database functions. **Video generation is not connected.** See [`docs/architecture.md`](docs/architecture.md) for the planned integration path.

---

## Features

| Feature | `backup_app.py` | `app.py` |
|---|---|---|
| Pioneer profile management | ✅ upsert via SQLite | ⚠️ form only, no persistence |
| AI narration (Edge TTS) | ✅ | ❌ not connected |
| Auto-generated captions | ✅ 8 words per card | ❌ |
| Image slideshow (9:16 crop) | ✅ | ❌ |
| Video clip support | ✅ | ❌ |
| Background music mix | ✅ | ❌ |
| MP4 export (H.264/AAC) | ✅ 1080 × 1920, 30 fps | ❌ |
| Inline preview + download | ✅ | ❌ |
| SQLite database | ✅ `database/pioneers.db` | ⚠️ initialized but empty |

---

## Output locations

| Path | Created by |
|---|---|
| `generated/<pioneer_name>/<video_title>_YYYYMMDD_HHMMSS.mp4` | `backup_app.py` |
| `database/pioneers.db` | `backup_app.py` |
| `output/pioneers/` | `app.py` (placeholder) |
| `temp/<job-uuid>/` | Both (cleaned up after each run) |

---

## Project structure

```text
Black_Pioneers_Studio/
├── app.py                  # Multi-page UI shell (incomplete)
├── backup_app.py           # Complete end-to-end pipeline
├── requirements.txt
├── README.md
├── LICENSE
├── SECURITY.md
│
├── assets/
│   ├── images/             # Placeholder images (.gitkeep)
│   ├── music/              # Placeholder music (.gitkeep)
│   └── video/              # Placeholder video (.gitkeep)
│
├── database/               # Created at runtime
│   └── pioneers.db
│
├── generated/              # MP4 output, organised by pioneer
├── temp/                   # Per-job working files (auto-cleaned)
├── scripts/                # Utility scripts
└── docs/                   # Detailed documentation (this PR)
```

---

## Documentation

| Document | Contents |
|---|---|
| [docs/user-guide.md](docs/user-guide.md) | Installation, creating pioneers, generating Shorts, previewing and downloading videos, common errors |
| [docs/architecture.md](docs/architecture.md) | Component map, generation pipeline, SQLite schema, data flow, known limitations |
| [docs/development.md](docs/development.md) | Local dev setup, running each entry point, code organisation, adding media fixtures |
| [docs/configuration.md](docs/configuration.md) | Configuration constants, voice options, resolution/FPS, output settings |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Symptoms, causes, and fixes for common issues |

---

## Troubleshooting

Quick reference — see [`docs/troubleshooting.md`](docs/troubleshooting.md) for the full guide.

| Symptom | Likely cause |
|---|---|
| `MoviePy` / FFmpeg error on startup | FFmpeg not installed or not on `PATH` |
| `edge_tts` / network error | No internet access at generation time |
| Captions use a fallback font | Arial or Helvetica not found (non-macOS) |
| Video file not found in database view | File moved or deleted after generation |
| `pip install` fails on Pillow or MoviePy | Python version mismatch or missing build tools |

---

## Security and media rights

- Do not commit `.env` files, API keys, or credentials. See [`SECURITY.md`](SECURITY.md).
- You are responsible for ensuring you have the necessary rights to all images, music, video clips, and other media you use.
- Generated content is intended for educational and historical purposes.

---

## Contributing

1. Fork the repository and create a feature branch.
2. Install dependencies in a virtual environment (`pip install -r requirements.txt`).
3. Make focused, well-described changes.
4. Test with `streamlit run backup_app.py` before submitting.
5. Open a pull request with a clear description of the change and why it is needed.

Do not commit large media files, database files, or generated videos. See `.gitignore` for excluded paths.

---

## Roadmap

### Version 1.0

- Connect `app.py` database layer to replace placeholders
- Integrate video generation pipeline into `app.py`
- Unified pioneer and video management UI

### Version 2.0

- Automatic thumbnail generation
- Batch video generation
- Caption style templates
- Voice presets

### Version 3.0

- YouTube upload integration
- Metadata generation
- Analytics dashboard
- Multi-language narration support

---

## License

This project is intended for educational and historical content creation. Users are responsible for ensuring they have the necessary rights to all media used in generated content.
