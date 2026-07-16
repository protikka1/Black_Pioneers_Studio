# Architecture

This document describes the internal structure, data flow, and design of **Black Pioneers Studio** as implemented in the current repository.

> **Documentation status** — this document reflects the repository as it currently stands. `backup_app.py` contains the complete pipeline. `app.py` is an in-progress multi-page redesign with placeholder functions.

---

## Table of Contents

- [Application components](#application-components)
- [End-to-end generation pipeline](#end-to-end-generation-pipeline)
- [Directory layout and data flow](#directory-layout-and-data-flow)
- [SQLite schema](#sqlite-schema)
- [Filename-safety and cleanup behaviour](#filename-safety-and-cleanup-behaviour)
- [Known limitations and technical debt](#known-limitations-and-technical-debt)

---

## Application components

### `backup_app.py` — complete pipeline

| Section | Responsibility |
|---|---|
| **Configuration constants** | Declares `BASE_DIR`, paths, `WIDTH`/`HEIGHT`/`FPS`, `SUPPORTED_*` sets, and `VOICE_OPTIONS`. |
| **General utilities** | `initialize_directories()`, `safe_filename()`, `save_uploaded_file()`. |
| **SQLite layer** | `get_database_connection()`, `initialize_database()`, `get_or_create_pioneer()`, `save_video_record()`, `load_video_records()`. |
| **Text-to-speech** | `generate_narration_async()` / `generate_narration()` — wraps `edge_tts.Communicate`. |
| **Image processing** | `prepare_vertical_image()` — crops and resizes to 1080 × 1920 using Pillow. `load_font()` — resolves a system font with fallback. |
| **Caption generation** | `split_script_into_captions()` — splits script into 8-word chunks. `create_caption_image()` — renders each chunk to a transparent PNG with a rounded dark background and white text. |
| **Video processing** | `prepare_video_clip()` — crops video to 9:16, resizes, loops if too short. `create_background_video()` — assembles all assets into a single background clip. `create_caption_clips()` — positions caption PNGs at y=1250 with timed `ImageClip` objects. `create_final_audio()` — mixes narration and optional background music. |
| **Orchestration** | `generate_short()` — calls all of the above in order and writes the final MP4. |
| **Streamlit interface** | `render_application()` — single-page form; calls orchestration on submission; displays result and database table. |

### `app.py` — multi-page shell

| Function | Status |
|---|---|
| `initialize_database()` | Placeholder — `pass`. |
| `get_all_pioneers()` | Placeholder — returns `[]`. |
| `create_pioneer()` | Placeholder — returns `1`. |
| `configure_application()` | Working — sets Streamlit page config, creates output and temp directories. |
| `render_sidebar()` | Working — navigation radio. |
| `render_dashboard()` | Working UI — reads from `get_all_pioneers()` (empty). |
| `render_create_pioneer()` | Working form — calls `create_pioneer()` (no-op). |
| `render_create_short()` | Working form — displays a "pipeline will be connected" message; no generation. |
| `render_video_library()` | Placeholder info message. |
| `render_settings()` | Working UI — shows directory paths and FPS selector (no effect). |

---

## End-to-end generation pipeline

The following describes what happens when the user clicks **Create YouTube Short** in `backup_app.py`.

```
User input (Streamlit form)
│
├─ Validation
│   └─ Pioneer name, video title, script, and at least one media asset required
│
├─ 1. Job directory created
│   └─ temp/<uuid4>/
│
├─ 2. Uploaded files saved to job directory
│   ├─ Media assets: asset_0000_<safe_name>.<ext>, asset_0001_..., ...
│   └─ Music (optional): background_music.<ext>
│
├─ 3. Edge TTS narration generated  [network required]
│   ├─ Input: script text, voice ID, rate string (e.g. "+5%")
│   └─ Output: temp/<uuid4>/narration.mp3
│
├─ 4. Narration duration measured
│   └─ AudioFileClip(narration.mp3).duration → float seconds
│
├─ 5. Background video assembled
│   ├─ Duration per asset = total_duration / len(assets)
│   ├─ Images: centre-cropped → 1080×1920 JPEG → ImageClip(duration=per_asset)
│   ├─ Videos: centre-cropped → resized → looped if needed → trimmed to per_asset
│   └─ All clips concatenated (method="compose")
│
├─ 6. Caption overlay generated
│   ├─ Script split into 8-word chunks
│   ├─ Each chunk rendered to transparent PNG (1080×500)
│   │   └─ Font: Arial Bold → Arial → Helvetica → PIL default
│   ├─ Each PNG wrapped in an ImageClip positioned at (center, 1250)
│   └─ Caption clips timed to divide total duration equally
│
├─ 7. Final audio mixed
│   ├─ Narration: full duration, unmodified volume
│   └─ Music (optional): looped to duration, scaled to music_volume, mixed as CompositeAudioClip
│
├─ 8. Final video composed
│   └─ CompositeVideoClip([background_video, *caption_clips], size=(1080,1920))
│       .with_audio(final_audio)
│
├─ 9. MP4 written to disk
│   └─ generated/<safe_pioneer_name>/<safe_video_title>_YYYYMMDD_HHMMSS.mp4
│       Codec: libx264 / AAC, bitrate 7000k / 192k, preset medium, 4 threads, 30 fps
│
├─ 10. SQLite record saved
│   ├─ pioneers: upsert (name + project_title as unique key)
│   └─ video_shorts: insert with path, duration, voice, status="generated"
│
└─ 11. Cleanup
    └─ temp/<uuid4>/ removed unconditionally (shutil.rmtree, ignore_errors=True)
```

---

## Directory layout and data flow

```text
Black_Pioneers_Studio/
│
├── backup_app.py           ← entry point for full pipeline
├── app.py                  ← entry point for multi-page shell
├── requirements.txt
│
├── assets/                 ← static assets (not generated at runtime)
│   ├── images/             ← placeholder; .gitkeep committed
│   ├── music/              ← placeholder; .gitkeep committed
│   └── video/              ← placeholder; .gitkeep committed
│
├── database/               ← created at runtime by initialize_database()
│   └── pioneers.db         ← SQLite database (ignored by .gitignore)
│
├── generated/              ← final MP4 output
│   └── <pioneer_name>/     ← one folder per pioneer (safe_filename)
│       └── <title>_YYYYMMDD_HHMMSS.mp4
│
├── temp/                   ← per-job working files
│   └── <uuid4>/            ← created per generation run, deleted on completion
│       ├── asset_0000_*.jpg/png/mp4/...
│       ├── prepared_image_0000.jpg
│       ├── caption_0000.png
│       ├── narration.mp3
│       └── background_music.*
│
└── output/                 ← used by app.py (placeholder, not yet implemented)
    └── pioneers/
```

---

## SQLite schema

Database file: `database/pioneers.db`  
Created by: `backup_app.py:initialize_database()`

### `pioneers` table

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | |
| `name` | TEXT NOT NULL | Pioneer display name |
| `category` | TEXT | Organisational label (nullable) |
| `project_title` | TEXT NOT NULL | Series title (e.g. "Black Pioneers: First in American History") |
| `created_at` | TEXT NOT NULL | ISO 8601 timestamp (seconds precision) |

Unique constraint: `(name, project_title)` — `get_or_create_pioneer()` upserts on this key.

### `video_shorts` table

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | |
| `pioneer_id` | INTEGER NOT NULL | FK → `pioneers.id` (CASCADE DELETE) |
| `video_title` | TEXT NOT NULL | User-provided title |
| `script_text` | TEXT NOT NULL | Full narration script |
| `video_short_path` | TEXT NOT NULL | Absolute path to the MP4 file |
| `duration_seconds` | REAL | Narration duration (rounded to 2 decimal places) |
| `voice_name` | TEXT | Edge TTS voice ID (e.g. `en-US-GuyNeural`) |
| `status` | TEXT NOT NULL | Always `"generated"` in the current implementation |
| `created_at` | TEXT NOT NULL | ISO 8601 timestamp (seconds precision) |

Foreign key enforcement is enabled via `PRAGMA foreign_keys = ON`.

---

## Filename-safety and cleanup behaviour

### `safe_filename(value: str) → str`

Converts a user-provided string to a safe directory or file name component:

1. Strip and lower-case the input.
2. Replace any sequence of characters outside `[a-z0-9]` with a single `_`.
3. Strip leading and trailing underscores.
4. Return `"untitled"` if the result is empty.

Example: `"Hiram Revels"` → `"hiram_revels"`.

### Temp directory cleanup

A `try/finally` block in `render_application()` calls `shutil.rmtree(job_directory, ignore_errors=True)` after every generation attempt, including failures. This means intermediate files (prepared images, caption PNGs, narration MP3) are removed regardless of outcome.

---

## Known limitations and technical debt

| Area | Description |
|---|---|
| **`app.py` / `backup_app.py` divergence** | `backup_app.py` is the working implementation; `app.py` is a cleaner multi-page redesign with placeholder functions. The two files are not integrated. The long-term intent is to connect the generation pipeline into `app.py` and retire `backup_app.py`. |
| **Platform-specific fonts** | `load_font()` hard-codes macOS font paths (`/System/Library/Fonts/Supplemental/Arial Bold.ttf`, `Arial.ttf`, `Helvetica.ttc`). On Linux or Windows these paths do not exist and Pillow falls back to its built-in bitmap font, producing small, low-quality captions. |
| **No test suite** | There are no automated tests in the repository. |
| **Absolute path stored in DB** | `video_short_path` stores the absolute file-system path at generation time. Moving the `generated/` folder or the repository breaks the path stored in the database. |
| **Single-page UI in `backup_app.py`** | `backup_app.py` is a monolithic single-page form. All Streamlit state (inputs, outputs) is lost on page reload. |
| **No `.env` support in `backup_app.py`** | `python-dotenv` is listed in `requirements.txt` but is not imported or used in either entry point. No environment variables are read. |
| **Voice rate is a percentage string** | The rate is formatted as `f"{value:+d}%"` (e.g. `"+5%"`) and passed directly to `edge_tts.Communicate`. Valid Edge TTS rate strings range from `-100%` to `+100%`. The UI limits the range to −20 % to +30 %. |
| **No caption word-wrap adaptation** | `create_caption_image()` uses `textwrap.fill(text, width=25)` regardless of font size. Long words can overflow the caption box. |
| **Bitrate and codec hardcoded** | Output bitrate (7000k video, 192k audio), codec (`libx264`/`aac`), preset (`medium`), and thread count (`4`) are hardcoded in `generate_short()`. |
