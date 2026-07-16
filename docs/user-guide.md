# User Guide

This guide explains how to install, run, and use **Black Pioneers Studio** to produce educational YouTube Shorts about Black American pioneers.

> **Documentation status** — this guide describes the repository as it currently stands.  
> `backup_app.py` contains the complete, working pipeline.  
> `app.py` is the in-progress multi-page redesign; video generation is **not yet connected** in that file.

---

## Table of Contents

- [Installation and startup](#installation-and-startup)
- [Choosing an entry point](#choosing-an-entry-point)
- [Creating a Short with backup\_app.py](#creating-a-short-with-backup_apppy)
  - [Step 1 — Pioneer and script](#step-1--pioneer-and-script)
  - [Step 2 — Upload assets](#step-2--upload-assets)
  - [Step 3 — Background music and voice](#step-3--background-music-and-voice)
  - [Step 4 — Generate the Short](#step-4--generate-the-short)
- [Previewing and downloading your video](#previewing-and-downloading-your-video)
- [Generated Shorts database view](#generated-shorts-database-view)
- [Using app.py (multi-page shell)](#using-apppy-multi-page-shell)
- [Supported file formats](#supported-file-formats)
- [Practical media recommendations](#practical-media-recommendations)
- [Common errors and recovery steps](#common-errors-and-recovery-steps)

---

## Installation and startup

### Requirements

- Python 3.9 or later
- FFmpeg installed and available on your `PATH`
- Internet access (Microsoft Edge TTS contacts Microsoft servers at generation time)

### Install FFmpeg

| Platform | Command |
|---|---|
| macOS (Homebrew) | `brew install ffmpeg` |
| Ubuntu / Debian | `sudo apt install ffmpeg` |
| Windows | Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add the `bin/` folder to `PATH` |

Verify with `ffmpeg -version`.

### Set up the Python environment

```bash
# Clone the repository
git clone https://github.com/protikka1/Black_Pioneers_Studio.git
cd Black_Pioneers_Studio

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate          # macOS / Linux
# .\venv\Scripts\Activate.ps1    # Windows PowerShell

# Install dependencies
pip install -r requirements.txt
```

### Start the application

```bash
# Complete generation pipeline (recommended)
streamlit run backup_app.py

# Multi-page UI shell (video generation not connected)
streamlit run app.py
```

Streamlit opens a browser tab automatically. If it does not, visit `http://localhost:8501`.

---

## Choosing an entry point

| Entry point | What it does |
|---|---|
| `backup_app.py` | Single-page form — fills in pioneer details, uploads media, configures voice, and generates an MP4 with one click. **Use this for actual video production.** |
| `app.py` | Multi-page sidebar navigation (Dashboard, Create Pioneer, Create Short, Video Library, Settings). The UI is functional but the database and video-generation functions are **placeholders**. No videos are produced. |

---

## Creating a Short with backup\_app.py

Run `streamlit run backup_app.py` and fill in the four sections described below.

### Step 1 — Pioneer and script

| Field | Required | Notes |
|---|---|---|
| Pioneer name | ✅ | Used as the output folder name. Special characters are replaced with underscores. |
| Category | ❌ | Organisational label (e.g. "Politics and Government"). |
| Project title | ❌ | Defaults to "Black Pioneers: First in American History". |
| Video title | ✅ | Used in the output filename. |
| Script / narration text | ✅ | The full spoken narration. The app shows a live character count and estimated narration duration (words ÷ 2.4 ≈ seconds). |

### Step 2 — Upload assets

Upload one or more image or video files. All uploaded files become the visual background of the Short.

- Each asset is displayed for an equal share of the total narration duration.
- Images are centre-cropped to 9:16 and resized to 1080 × 1920.
- Video clips are centre-cropped and looped if shorter than the required duration.
- **At least one asset is required.**

Supported formats: JPG, JPEG, PNG, WEBP, MP4, MOV, M4V.

### Step 3 — Background music and voice

| Control | Description | Default |
|---|---|---|
| Background music | Optional MP3, WAV, or M4A file. Looped if shorter than the video. | None |
| Narration voice | American Male, American Female, or British Female | American Male |
| Voice speed | Slider from −20 % to +30 %, step 5 % | +5 % |
| Music volume | Slider from 0.0 to 0.5 | 0.10 |

### Step 4 — Generate the Short

Click **Create YouTube Short**. A progress panel shows each stage:

1. Saving uploaded media to a temporary job folder.
2. Generating Edge TTS narration (requires internet).
3. Processing images / video clips.
4. Generating caption overlay images.
5. Compositing the final video with MoviePy.
6. Writing the MP4 to `generated/<pioneer_name>/`.
7. Saving a record to `database/pioneers.db`.

Generation typically takes 30 seconds to several minutes depending on script length and hardware.

---

## Previewing and downloading your video

After a successful generation, `backup_app.py` displays:

- An inline video player for immediate preview.
- A **Download MP4** button to save the file locally.
- The absolute file path in a code block (useful for finding the file in Finder or Explorer).

If you close the page before downloading, the file is still on disk at `generated/<pioneer_name>/<video_title>_YYYYMMDD_HHMMSS.mp4`.

---

## Generated Shorts database view

Below the creation form, `backup_app.py` shows a table of every generated Short stored in `database/pioneers.db`. It includes pioneer name, category, video title, duration, status, creation date, and file path.

A dropdown lets you select and preview any previously generated Short directly in the browser. If the file path is valid but the file has been moved or deleted, a warning is shown instead.

---

## Using app.py (multi-page shell)

`app.py` provides a sidebar with five pages. All pages display UI elements but **no data is persisted** and **no video is generated**:

| Page | Current behaviour |
|---|---|
| Dashboard | Shows metrics (all zeros) and an empty pioneer list. |
| Create Pioneer | Form saves to a placeholder function that returns `1` without writing to a database. |
| Create Short | Form with pioneer selector, script, and media uploaders. On submission, displays a message that the video pipeline will be connected in a later module. |
| Video Library | Placeholder — shows an info message. |
| Settings | Displays output and temp directory paths; frame-rate selector is active but has no effect. |

---

## Supported file formats

### Images (background assets)

| Format | Extension |
|---|---|
| JPEG | `.jpg`, `.jpeg` |
| PNG | `.png` |
| WebP | `.webp` |

### Video (background assets)

| Format | Extension |
|---|---|
| MPEG-4 | `.mp4` |
| QuickTime | `.mov` |
| MPEG-4 Audio | `.m4v` |

### Audio (background music only)

| Format | Extension |
|---|---|
| MP3 | `.mp3` |
| WAV | `.wav` |
| MPEG-4 Audio | `.m4a` |

---

## Practical media recommendations

- **Image resolution:** Use images at 1080 × 1920 or larger. Smaller images are upscaled.
- **Image aspect ratio:** Any ratio works — the app centre-crops to 9:16. Avoid placing important subjects near the edges of wide landscape photos.
- **Video clips:** Short clips (5–15 s) work well. Longer clips are trimmed to fit; very short clips are looped.
- **Music volume:** Keep background music at 0.05–0.15 so the narration remains audible.
- **Script length:** Aim for 30–90 seconds of narration (roughly 70–220 words at the default speed). YouTube Shorts must be 60 seconds or under to appear in the Shorts feed; longer videos will be treated as regular uploads.
- **File size:** There is no explicit upload limit, but very large files will slow processing.
- **Rights:** Only upload media you have the rights to use. See the [Security and media rights](../README.md#security-and-media-rights) section.

---

## Common errors and recovery steps

| Symptom | Likely cause | Fix |
|---|---|---|
| Page shows `st.exception` with an FFmpeg error | FFmpeg not installed or not on PATH | Install FFmpeg and restart the terminal; see [Installation and startup](#installation-and-startup). |
| `edge_tts` or `aiohttp` error during generation | No internet connection | Connect to the internet and try again. Edge TTS requires network access. |
| Captions render in a small default font | System fonts not found (non-macOS) | Install Arial or place a TTF font at one of the paths listed in `backup_app.py:load_font()`. See [`docs/troubleshooting.md`](troubleshooting.md#missing-fonts). |
| "No supported image or video assets were found" | All uploaded files have unsupported extensions | Re-upload in a supported format (see [Supported file formats](#supported-file-formats)). |
| Video file not found in the database view | File was moved or deleted | Move the file back, or the record can be ignored — it does not affect future generation. |
| `pip install` fails with a build error | Python version, missing C compiler, or OS headers | See [`docs/troubleshooting.md`](troubleshooting.md#dependency-installation). |
| Output folder is empty after generation | Exception during generation (check the `st.exception` panel) | Fix the underlying error; the temp folder is cleaned up regardless. |

For a detailed symptom list, see [`docs/troubleshooting.md`](troubleshooting.md).
