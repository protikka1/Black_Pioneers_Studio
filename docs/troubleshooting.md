# Troubleshooting

This document provides actionable symptoms, causes, and fixes for common issues encountered with **Black Pioneers Studio**.

---

## Table of Contents

- [Dependency installation](#dependency-installation)
- [FFmpeg and MoviePy issues](#ffmpeg-and-moviepy-issues)
- [Edge TTS and network issues](#edge-tts-and-network-issues)
- [Missing fonts](#missing-fonts)
- [Unsupported media files](#unsupported-media-files)
- [Missing output files](#missing-output-files)
- [SQLite and database issues](#sqlite-and-database-issues)
- [Windows-specific issues](#windows-specific-issues)
- [Streamlit issues](#streamlit-issues)

---

## Dependency installation

### `pip install -r requirements.txt` fails with a build error

**Symptom:** `error: command 'gcc' failed` or `Microsoft Visual C++ 14.0 or greater is required`.

**Cause:** Pillow or another package requires a C compiler that is not installed.

**Fix:**

- **macOS:** Install Xcode Command Line Tools: `xcode-select --install`
- **Ubuntu / Debian:** `sudo apt install build-essential python3-dev`
- **Windows:** Install [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/).

---

### `pip install` fails with a Pillow version conflict

**Symptom:** `ERROR: Cannot install pillow>=12.0 and moviepy==2.2.1 because these package versions have conflicting dependencies.`

**Cause:** `moviepy==2.2.1` requires `pillow<12.0`.

**Fix:** Do not upgrade Pillow above 11.x while using MoviePy 2.2.1. The pinned `requirements.txt` sets `pillow==11.3.0`, which is compatible. If you have manually upgraded Pillow, reinstall from the pinned file:

```bash
pip install -r requirements.txt --force-reinstall
```

---

### Python version error on startup

**Symptom:** `SyntaxError` or `ImportError` on an `f-string` or `match` statement.

**Cause:** Python version is below 3.9.

**Fix:** Install Python 3.9 or later and recreate the virtual environment.

```bash
python3 --version      # must be 3.9+
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## FFmpeg and MoviePy issues

### `FileNotFoundError: [WinError 2] The system cannot find the file specified` during video generation

**Symptom:** MoviePy raises a `FileNotFoundError` mentioning `ffmpeg`.

**Cause:** FFmpeg is not installed or not on `PATH`.

**Fix:**

1. Install FFmpeg (see [User Guide — Install FFmpeg](user-guide.md#install-ffmpeg)).
2. Verify: `ffmpeg -version`
3. Restart the terminal and Streamlit after installing.

---

### `OSError: MoviePy error: the file ... does not have a video stream`

**Symptom:** This error appears when processing a video asset.

**Cause:** The uploaded file is corrupted, uses an unsupported codec, or has the wrong extension.

**Fix:** Re-encode the video with FFmpeg:

```bash
ffmpeg -i input.mov -c:v libx264 -c:a aac output.mp4
```

Then re-upload the converted file.

---

### Video generation hangs indefinitely

**Symptom:** The Streamlit progress panel stops advancing and the page is unresponsive.

**Cause:** MoviePy encoding can take several minutes on slow hardware or with long scripts. FFmpeg may also hang on certain inputs.

**Fix:**

1. Wait at least 5 minutes before concluding the process has hung.
2. If the terminal shows no FFmpeg progress, press `Ctrl+C` in the terminal to stop Streamlit, then restart.
3. Try a shorter script or fewer/smaller assets.

---

## Edge TTS and network issues

### `aiohttp.ClientConnectorError` or `edge_tts.exceptions.NoAudioReceived`

**Symptom:** An exception panel appears during the "Generating narration and captions..." step.

**Cause:** No internet connection, or the Microsoft Edge TTS service is temporarily unavailable.

**Fix:**

1. Confirm internet access: `curl https://www.bing.com`
2. If behind a corporate proxy, set `HTTP_PROXY` / `HTTPS_PROXY` environment variables.
3. Wait a few minutes and retry — the service has occasional brief outages.

---

### `RuntimeError: This event loop is already running`

**Symptom:** `asyncio`-related error during TTS generation.

**Cause:** Some environments (Jupyter, certain IDE integrations) run their own event loop that conflicts with `asyncio.run()`.

**Fix:** Run the app from a plain terminal, not from inside a Jupyter notebook or an IDE's integrated terminal that manages its own event loop.

---

## Missing fonts

### Captions appear very small or in a pixelated font

**Symptom:** Caption text in the generated video is very small (about 10 px) and uses a bitmap font.

**Cause:** `backup_app.py:load_font()` hard-codes macOS font paths. On Linux or Windows, none of the candidate paths exist, so Pillow falls back to `ImageFont.load_default()`.

**Candidate paths checked:**

```
/System/Library/Fonts/Supplemental/Arial Bold.ttf
/System/Library/Fonts/Supplemental/Arial.ttf
/System/Library/Fonts/Helvetica.ttc
```

**Fix (Linux):**

```bash
# Install Microsoft core fonts
sudo apt install ttf-mscorefonts-installer fontconfig
fc-cache -f -v
```

Then add the Linux font path to `load_font()` in `backup_app.py`:

```python
"/usr/share/fonts/truetype/msttcorefonts/Arial_Bold.ttf",
"/usr/share/fonts/truetype/msttcorefonts/Arial.ttf",
```

**Fix (Windows):** Arial is typically already installed. Add the Windows path:

```python
"C:/Windows/Fonts/arialbd.ttf",
"C:/Windows/Fonts/arial.ttf",
```

**Alternative (any platform):** Place any TTF font file in `assets/fonts/` and add that path as the first candidate in `load_font()`.

---

## Unsupported media files

### "No supported image or video assets were found"

**Symptom:** This error message appears after clicking **Create YouTube Short**.

**Cause:** All uploaded files have unsupported extensions.

**Fix:** Re-upload files in a supported format:

- Images: `.jpg`, `.jpeg`, `.png`, `.webp`
- Videos: `.mp4`, `.mov`, `.m4v`

If the file has the correct extension but the error persists, the file may be corrupted. Try opening it in an image viewer or media player first.

---

### Streamlit file uploader rejects the file

**Symptom:** The file uploader shows "File type not allowed".

**Cause:** The file extension is not in the allowed list for that uploader.

**Fix:** The `backup_app.py` uploader accepts `jpg`, `jpeg`, `png`, `webp`, `mp4`, `mov`, `m4v` for media and `mp3`, `wav`, `m4a` for music. Convert the file to a supported format before uploading.

---

## Missing output files

### The generated video file cannot be found on disk

**Symptom:** Generation completes but you cannot locate the MP4.

**Cause/Fix:**

1. Check the absolute path shown in the code block at the bottom of the success panel.
2. On macOS, use Finder → Go → Go to Folder (`⌘ Shift G`) and paste the path.
3. On Windows, paste the path into File Explorer's address bar (note: paths use `/` separators; replace with `\`).
4. If the path starts with `/home/runner/` or a Docker path, the application is running inside a container — copy the file out using `docker cp` or a volume mount.

---

### The database shows a record but the file is gone

**Symptom:** The Generated Shorts table shows a row, but the preview area says "The database record exists, but the video file was not found."

**Cause:** The MP4 was moved, renamed, or deleted after generation.

**Fix:** The record in the database is informational only. Move the file back to the path shown in the `video_short_path` column, or generate a new Short — the old record will not prevent new generation.

---

## SQLite and database issues

### `OperationalError: no such table: pioneers`

**Symptom:** SQLite error on startup or first use.

**Cause:** `initialize_database()` was not called, or the database file is from an incompatible version.

**Fix:** Delete `database/pioneers.db` and restart `backup_app.py`. The file is recreated with the correct schema on startup.

```bash
rm database/pioneers.db
streamlit run backup_app.py
```

---

### `IntegrityError: UNIQUE constraint failed`

**Symptom:** Rare; appears if concurrent generation attempts write the same pioneer name and project title simultaneously.

**Cause:** Race condition on the `UNIQUE(name, project_title)` constraint in the `pioneers` table.

**Fix:** Run only one instance of `backup_app.py` at a time. The `get_or_create_pioneer()` function handles the normal upsert case correctly for sequential requests.

---

### The database file grows large over time

**Symptom:** `database/pioneers.db` is several hundred MB.

**Cause:** `script_text` (full narration) is stored in every `video_shorts` row, and many Shorts have been generated.

**Fix:** Run `VACUUM` on the database to reclaim space:

```bash
sqlite3 database/pioneers.db "VACUUM;"
```

---

## Windows-specific issues

### `streamlit : The term 'streamlit' is not recognized`

**Symptom:** PowerShell error after installing dependencies.

**Cause:** The virtual environment's `Scripts/` directory is not on `PATH`, or the environment was not activated.

**Fix:**

```powershell
.\venv\Scripts\Activate.ps1
streamlit run backup_app.py
```

If activation is blocked by execution policy:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

---

### Path separators in the database

**Symptom:** The `video_short_path` column stores Windows-style paths (`C:\Users\...`), but the file cannot be opened.

**Cause:** The path was stored with backslashes and is being read on a different system or after a directory move.

**Fix:** The path is informational. Locate the file manually using the pioneer name and video title to find it under `generated/`.

---

### `OSError: [WinError 145] The directory is not empty` during cleanup

**Symptom:** A Python traceback after video generation on Windows.

**Cause:** On Windows, `shutil.rmtree` can occasionally fail if a file in `temp/` is still locked by a process.

**Fix:** This is a non-critical error — the video has already been generated and saved. You can safely delete the leftover `temp/<uuid>/` folder manually. The `ignore_errors=True` flag in `shutil.rmtree` should suppress most cases; if you see this consistently, it may indicate that MoviePy is not releasing file handles promptly. Ensure you are using `moviepy==2.2.1` from `requirements.txt`.
