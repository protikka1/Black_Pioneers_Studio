# Configuration Reference

This document describes the configuration constants, paths, voice options, and output settings used in **Black Pioneers Studio**.

> **Documentation status** — all values are derived from the actual source files. Neither entry point reads environment variables at this time. `python-dotenv` is listed in `requirements.txt` but is not imported or invoked.

---

## Table of Contents

- [Configuration constants in backup\_app.py](#configuration-constants-in-backup_apppy)
- [Configuration constants in app.py](#configuration-constants-in-apppy)
- [Voice options and narration rate](#voice-options-and-narration-rate)
- [Resolution and FPS settings](#resolution-and-fps-settings)
- [Output settings](#output-settings)
- [Directory paths](#directory-paths)
- [Environment variables](#environment-variables)

---

## Configuration constants in backup\_app.py

All constants are defined near the top of `backup_app.py` (lines ~26–50).

```python
PROJECT_TITLE = "Black Pioneers: First in American History"

BASE_DIR = Path(__file__).resolve().parent   # repository root

DATABASE_DIR = BASE_DIR / "database"
DATABASE_FILE = DATABASE_DIR / "pioneers.db"

GENERATED_DIR = BASE_DIR / "generated"
TEMP_DIR      = BASE_DIR / "temp"

WIDTH  = 1080   # pixels
HEIGHT = 1920   # pixels
FPS    = 30     # frames per second

SUPPORTED_IMAGES = {".jpg", ".jpeg", ".png", ".webp"}
SUPPORTED_VIDEOS = {".mp4", ".mov", ".m4v"}

VOICE_OPTIONS = {
    "American Male":   "en-US-GuyNeural",
    "American Female": "en-US-JennyNeural",
    "British Female":  "en-GB-SoniaNeural",
}
```

To change a constant, edit `backup_app.py` directly. There is no external configuration file.

---

## Configuration constants in app.py

```python
PROJECT_TITLE = "Black Pioneers: First in American History"

BASE_DIR   = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output" / "pioneers"
TEMP_DIR   = BASE_DIR / "temp"
```

`app.py` does not define video dimensions or voice options because the generation pipeline is not yet connected.

---

## Voice options and narration rate

### Available voices

| Label (UI) | Edge TTS voice ID | Accent |
|---|---|---|
| American Male | `en-US-GuyNeural` | US English, male |
| American Female | `en-US-JennyNeural` | US English, female |
| British Female | `en-GB-SoniaNeural` | British English, female |

Voices are provided by Microsoft Edge TTS (`edge-tts` package). An internet connection is required at generation time.

### Voice rate (speed)

The UI renders a slider with the following parameters:

| Parameter | Value |
|---|---|
| Minimum | −20 % |
| Maximum | +30 % |
| Step | 5 % |
| Default | +5 % |

The selected integer is formatted as `f"{value:+d}%"` (e.g. `"+5%"`, `"-10%"`) and passed directly to `edge_tts.Communicate(rate=...)`.

Valid Edge TTS rate strings range from `"-100%"` to `"+100%"`. Values outside that range may produce an error from the Edge TTS service.

### Music volume

| Parameter | Value |
|---|---|
| Minimum | 0.0 |
| Maximum | 0.5 |
| Step | 0.05 |
| Default | 0.10 |

The value is passed to `AudioFileClip.with_volume_scaled()`. A value of `0.10` means the music plays at 10 % of its original volume, keeping the narration dominant.

---

## Resolution and FPS settings

| Constant | Value | Notes |
|---|---|---|
| `WIDTH` | 1080 px | Standard YouTube Shorts width |
| `HEIGHT` | 1920 px | Standard YouTube Shorts height (9:16) |
| `FPS` | 30 | Frames per second |

These values are hardcoded. To change them, edit `backup_app.py` directly and ensure your source assets are high enough resolution to avoid upscaling artefacts.

---

## Output settings

The final video is written by `final_video.write_videofile(...)` with the following hardcoded parameters:

| Parameter | Value |
|---|---|
| Video codec | `libx264` |
| Audio codec | `aac` |
| Video bitrate | `7000k` |
| Audio bitrate | `192k` |
| Encoding preset | `medium` |
| CPU threads | `4` |
| FPS | `30` (from `FPS` constant) |

The output file is named:

```
generated/<safe_pioneer_name>/<safe_video_title>_YYYYMMDD_HHMMSS.mp4
```

where `safe_pioneer_name` and `safe_video_title` are produced by `safe_filename()` (lower-case, alphanumeric and underscores only).

---

## Directory paths

| Path | Created by | Gitignored |
|---|---|---|
| `database/pioneers.db` | `backup_app.py:initialize_database()` | ✅ `database/*.db` |
| `generated/` | `backup_app.py:generate_short()` | ✅ `generated/*` (`.gitkeep` kept) |
| `temp/` | `backup_app.py:initialize_directories()`, `app.py:configure_application()` | ✅ `temp/*` (`.gitkeep` kept) |
| `output/pioneers/` | `app.py:configure_application()` | ❌ not explicitly ignored (empty) |
| `assets/images/` | Static (placeholder) | ✅ `assets/images/*` (`.gitkeep` kept) |
| `assets/music/` | Static (placeholder) | ✅ `assets/music/*` (`.gitkeep` kept) |
| `assets/video/` | Static (placeholder) | ✅ `assets/video/*` (`.gitkeep` kept) |

---

## Environment variables

`python-dotenv` (`python-dotenv==1.2.2`) is listed in `requirements.txt` but is **not imported or used** in either `app.py` or `backup_app.py`. No environment variables are read by the application.

If you add `.env` support in the future:

- Import `load_dotenv` at the top of the entry point: `from dotenv import load_dotenv; load_dotenv()`.
- Never commit the `.env` file. It is already listed in `.gitignore`.
- Document any new variables in this file.

There are no required environment variables in the current implementation.
