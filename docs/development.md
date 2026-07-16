# Development Guide

This guide covers local development setup, running each entry point, code organisation, and how to contribute to **Black Pioneers Studio**.

> **Documentation status** — this guide describes the repository as it currently stands. There is no automated test suite; validation is done by running the application manually.

---

## Table of Contents

- [Local development setup](#local-development-setup)
- [Running each entry point](#running-each-entry-point)
- [Code organisation](#code-organisation)
- [Suggested workflow for changes](#suggested-workflow-for-changes)
- [Validation and manual testing](#validation-and-manual-testing)
- [Formatting and linting recommendations](#formatting-and-linting-recommendations)
- [Adding media fixtures without committing large files](#adding-media-fixtures-without-committing-large-files)

---

## Local development setup

### Prerequisites

- Python 3.9 or later
- FFmpeg on your `PATH` (see [User Guide — Install FFmpeg](user-guide.md#install-ffmpeg))
- Git

### Initial setup

```bash
git clone https://github.com/protikka1/Black_Pioneers_Studio.git
cd Black_Pioneers_Studio

python3 -m venv venv
source venv/bin/activate          # macOS / Linux
# .\venv\Scripts\Activate.ps1    # Windows PowerShell

pip install -r requirements.txt
```

### Verifying the environment

```bash
python -c "import streamlit, moviepy, PIL, edge_tts; print('OK')"
ffmpeg -version
```

Both commands should complete without errors.

---

## Running each entry point

### `backup_app.py` — complete pipeline

```bash
streamlit run backup_app.py
```

Opens at `http://localhost:8501`. Use this entry point to test any changes to the generation pipeline.

### `app.py` — multi-page shell

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`. Use this entry point to test UI changes or navigation.

### Choosing a different port

```bash
streamlit run backup_app.py --server.port 8502
```

---

## Code organisation

Both entry points are self-contained single files. There are no shared modules in the current codebase.

### `backup_app.py` — section layout

```
backup_app.py
│
├── Configuration constants     (lines ~26–50)
├── General utilities           (lines ~53–75)
├── SQLite layer                (lines ~78–228)
├── Text-to-speech              (lines ~231–263)
├── Image processing            (lines ~266–326)
├── Caption generation          (lines ~329–405)
├── Video processing            (lines ~408–566)
├── Orchestration               (lines ~569–649)
├── Streamlit interface         (lines ~652–935)
└── Entry point guard           (lines ~938–945)
```

### `app.py` — section layout

```
app.py
│
├── Configuration constants + placeholder DB functions
├── configure_application()
├── render_sidebar()
├── render_dashboard()
├── render_create_pioneer()
├── render_create_short()
├── render_video_library()
├── render_settings()
└── main()
```

### Key constants (both files)

| Constant | File | Value |
|---|---|---|
| `WIDTH` / `HEIGHT` | `backup_app.py` | 1080 / 1920 |
| `FPS` | `backup_app.py` | 30 |
| `DATABASE_FILE` | `backup_app.py` | `database/pioneers.db` |
| `GENERATED_DIR` | `backup_app.py` | `generated/` |
| `TEMP_DIR` | Both | `temp/` |
| `OUTPUT_DIR` | `app.py` | `output/pioneers/` |

---

## Suggested workflow for changes

### Modifying the generation pipeline (`backup_app.py`)

1. Create a branch: `git checkout -b feature/my-change`
2. Make changes to `backup_app.py`.
3. Run `streamlit run backup_app.py` and perform a full generation with a short script and one test image.
4. Confirm the MP4 is created under `generated/`, the database record appears, and cleanup leaves no files in `temp/`.
5. Commit and open a pull request.

### Modifying the UI shell (`app.py`)

1. Create a branch: `git checkout -b feature/my-ui-change`
2. Make changes to `app.py`.
3. Run `streamlit run app.py` and navigate through all five sidebar pages.
4. Confirm no Python exceptions appear in the terminal or in the browser.
5. Commit and open a pull request.

### Integrating `app.py` with the generation pipeline

The long-term goal is to replace the placeholder functions in `app.py` with the real implementations from `backup_app.py`. Suggested steps:

1. Extract the SQLite layer from `backup_app.py` into a shared module (e.g. `modules/database.py`).
2. Extract the generation pipeline into a shared module (e.g. `modules/generator.py`).
3. Import both modules in `app.py` and remove the placeholder stubs.
4. Test both entry points after each extraction step.

### Updating dependencies

Do not manually edit `requirements.txt`. Instead:

```bash
pip install <package>==<version>
pip freeze > requirements.txt
```

Check that `moviepy==2.2.1` and `pillow<12.0` remain consistent (see [architecture.md — Known limitations](architecture.md#known-limitations-and-technical-debt)).

---

## Validation and manual testing

There is no automated test suite in the repository. The following manual checks confirm the main paths work correctly.

### Smoke test — full generation

1. `streamlit run backup_app.py`
2. Fill in all required fields (pioneer name, video title, script text).
3. Upload one small JPG image.
4. Leave music empty; keep default voice and speed.
5. Click **Create YouTube Short**.
6. Confirm:
   - No exception panel appears.
   - An inline video player appears with the generated Short.
   - A **Download MP4** button is present and downloads a valid file.
   - `generated/<pioneer_name>/` contains the MP4.
   - `database/pioneers.db` contains a `pioneers` row and a `video_shorts` row.
   - `temp/` is empty (cleanup ran).

### Smoke test — app.py navigation

1. `streamlit run app.py`
2. Click each sidebar item (Dashboard, Create Pioneer, Create Short, Video Library, Settings).
3. Confirm each page loads without a Python exception.
4. On Create Pioneer, submit the form with a name — confirm the success message appears (even though no database write occurs).

### Edge cases to verify after changes

- Script with only one word (single caption).
- Very short script (< 5 seconds of narration).
- Multiple assets (test equal-duration split).
- Video asset that is shorter than the required clip duration (test looping).
- Pioneer name with special characters (test `safe_filename`).

---

## Formatting and linting recommendations

> These are **recommendations** only. No linter configuration exists in the repository.

If you want to apply consistent formatting before committing:

```bash
# Install tools (not in requirements.txt)
pip install ruff

# Check for issues
ruff check backup_app.py app.py

# Auto-fix safe issues
ruff check --fix backup_app.py app.py

# Format code (Ruff's built-in formatter)
ruff format backup_app.py app.py
```

Both files currently follow PEP 8 conventions with 4-space indentation and type annotations.

---

## Adding media fixtures without committing large files

The `.gitignore` excludes the following paths:

```
assets/images/*
assets/music/*
assets/video/*
generated/*
database/*.db
temp/*
```

Only `.gitkeep` files are committed to preserve the empty directories.

### Workflow for development media

1. Place test images, music, and video clips directly in `assets/images/`, `assets/music/`, and `assets/video/` locally.
2. Do **not** run `git add assets/images/my-test-image.jpg` — it is excluded by `.gitignore`.
3. If you need shared test fixtures for CI or contributors, document them in this file and provide a download link or generation script rather than committing the binary files.

### Keeping fixtures small

- For image tests, use a 200 × 200 px solid-colour PNG (< 5 KB).
- For music tests, use a 5-second royalty-free WAV.
- For video tests, use a 5-second MP4 at 480p.

Never commit copyrighted images, music, or video to the repository.
