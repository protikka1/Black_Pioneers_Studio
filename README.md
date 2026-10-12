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

### Mac desktop app and DMG

The packaged desktop release includes Python, Streamlit and its browser assets,
the studio modules, MoviePy, Edge TTS, and FFmpeg. Installed users do not need
Python, Homebrew, a virtual environment, or the source checkout. It opens a local
Streamlit server in the default browser; Microsoft narration still needs internet.

From the repository on your Mac, use the existing `.venv` and build:

```bash
bash scripts/build_mac_dmg.sh
```

The script installs the pinned build tool, builds and verifies the `.app`, then
creates and verifies `dist/Black-Pioneers-Studio-macos-x86_64.dmg` on an Intel Mac
(or `...-arm64.dmg` on Apple Silicon). Build on the target architecture and oldest
macOS version you intend to support. Native Python packages must support that OS.
The first build can take several minutes; PyInstaller reports progress in Terminal.

Open the DMG and drag **Black Pioneers Studio.app** onto **Applications**, then
launch it from Applications. To build only the application:

```bash
bash scripts/build_mac_desktop_app.sh
```

New desktop data is stored outside the installed app:

```text
~/Library/Application Support/BlackPioneersStudio/database/pioneers.db
~/Library/Application Support/BlackPioneersStudio/output/pioneers/
~/Library/Application Support/BlackPioneersStudio/temp/
```

This is a new desktop collection. The existing development database, uploaded
media, and MLK video are not moved or included in the installer. Save copies of
those files before attempting any separate migration. Development and cloud runs
continue using their repository directory unless `BLACK_PIONEERS_DATA_DIR` is set.

Diagnostics: `~/Library/Logs/BlackPioneersStudio.log`. The build-time verifier runs
from a temporary directory with Python, virtual-environment variables, and Homebrew
removed from PATH, checks imports and FFmpeg, renders a short test video with captions and local audio,
and starts the packaged web server.
No build is reported as verified if these checks fail. To stop the desktop server,
quit its launcher; closing the browser tab alone does not stop the launcher.

GitHub Actions also builds unsigned Intel and Apple Silicon test installers through
`.github/workflows/mac-package.yml`. Download these from a successful run's Artifacts.
Those runners use macOS 15; they do not certify compatibility with Monterey 12.
Run the local build/verification command on Monterey before promising support there.

### Signed distribution

Without a signing identity the app receives PyInstaller's local ad-hoc signature.
For a public download, use an Apple Developer ID Application certificate and an
already configured notarytool Keychain profile:

```bash
BLACK_PIONEERS_CODESIGN_IDENTITY="Developer ID Application: Your Name (TEAMID)" \
BLACK_PIONEERS_NOTARY_PROFILE="your-existing-keychain-profile" \
bash scripts/build_mac_dmg.sh
```

The script signs the app and disk image, submits the disk image for notarization,
and staples the result. Do not put Apple credentials or certificates in Git.
Public redistribution must also preserve the bundled dependencies' licenses and
satisfy the source-distribution requirements of the FFmpeg build you distribute.

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
Uploads are capped at 50 MB per file. One video renders at a time, with at most
four running/queued requests. Community Cloud resources are limited, so test short
videos first. For regular
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

## Server test and public-release checklist

For the first Community Cloud test, set app sharing to **Private** in Streamlit
settings and grant access only to the test users. GitHub repository visibility
does not protect the shared studio collection.

Validate: all six navigation pages; create a fictional pioneer; render one short
with an image and JennyNeural narration; preview/download the MP4; confirm captions
and audio; export the pioneer CSV; verify failed renders release their queue slot.
Download every output you need to keep before restarting or redeploying.

A merged/tested build is not a complete public-production service. Permanent cloud
database/media storage and backups still require an external service configuration.
Public desktop distribution additionally requires signing/notarization, dependency
license compliance, and native OS compatibility tests. Do not distribute untested
Windows/Linux installers; those are separate platform releases.
