# Black Pioneers Studio

## Overview

**Black Pioneers Studio** is a Python-based desktop application for creating high-quality YouTube Shorts, podcasts, and educational videos about Black American pioneers.

The application automates the entire production workflow, allowing a creator to transform a written script and media assets into a fully rendered vertical video with AI narration, subtitles, background music, and organized project management.

The project is designed for the **Black Pioneers: First in American History** educational series but is built to support any historical or educational content library.

---

# Project Goals

* Build a complete YouTube Shorts production studio.
* Automate repetitive video editing tasks.
* Organize hundreds of pioneer profiles.
* Maintain a searchable SQLite database.
* Produce consistent, professional-quality educational content.
* Prepare videos for publishing on YouTube and other social media platforms.

---

# Core Features

## Pioneer Management

* Add new pioneers
* Edit pioneer profiles
* Search by name
* Search by category
* Store biography information
* Track generated videos

---

## Script Editor

* Create scripts
* Edit scripts
* Save scripts
* Load existing scripts
* Character counter
* Estimated narration duration

---

## Media Library

Supported formats:

### Images

* JPG
* JPEG
* PNG
* WEBP

### Video

* MP4
* MOV

### Audio

* MP3
* WAV
* M4A

---

## AI Narration

Powered by Microsoft Edge TTS.

Features:

* Natural AI voices
* Multiple voice selections
* Adjustable speaking speed
* Adjustable volume
* Automatic narration generation

---

## Video Generator

Creates professional YouTube Shorts automatically.

Features:

* 1080 × 1920 (9:16)
* AI narration
* Automatic subtitles
* Background music
* Image slideshow
* Video clips
* Smooth transitions
* H.264 MP4 export

---

## Database

SQLite stores:

* Pioneer information
* Scripts
* Generated videos
* Categories
* Video history
* Project metadata

---

## Output

Generated videos are stored by pioneer.

Example:

```
generated/
    hiram_revels/
        first_us_senator.mp4

    bessie_coleman/
        first_black_woman_pilot.mp4
```

---

# Project Structure

```
Black_Pioneers_Studio/
│
├── app.py
├── README.md
├── requirements.txt
├── pioneers.db
│
├── assets/
│   ├── images/
│   ├── music/
│   └── videos/
│
├── generated/
├── thumbnails/
├── database/
├── logs/
├── scripts/
├── temp/
│
├── src/
│   ├── ui.py
│   ├── database.py
│   ├── video_generator.py
│   ├── captions.py
│   ├── tts.py
│   ├── exporter.py
│   └── utils.py
│
└── config/
```

---

# Technology Stack

* Python 3
* Streamlit
* SQLite
* MoviePy
* FFmpeg
* Pillow
* Edge-TTS
* Pandas
* OpenPyXL

---

# Installation

Clone or create the project directory.

Create a virtual environment:

```bash
python3 -m venv venv
```

Activate the environment:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
streamlit run app.py
```

---

# Workflow

1. Select or create a pioneer.
2. Enter or load the script.
3. Upload images and video clips.
4. Select background music.
5. Generate AI narration.
6. Create the YouTube Short.
7. Preview the video.
8. Save the project.
9. Export the final MP4.
10. Record the generated video in the SQLite database.

---

# Roadmap

## Version 1.0

* Project management
* SQLite database
* Script editor
* Media management
* AI narration
* YouTube Shorts generation

## Version 2.0

* Automatic thumbnail generation
* Batch video generation
* Timeline editor
* Caption templates
* Voice presets

## Version 3.0

* YouTube upload integration
* Metadata generation
* Analytics dashboard
* Multi-language support
* AI-assisted script enhancement

---

# License

This project is intended for educational and historical content creation. Users are responsible for ensuring they have the necessary rights to all images, music, video, and other media used in generated content.

---

# Project

**Black Pioneers: First in American History**

A digital initiative dedicated to documenting, preserving, and sharing the achievements of Black American pioneers through searchable profiles, educational resources, and professionally produced short-form videos.
