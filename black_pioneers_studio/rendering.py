from __future__ import annotations

import gc
import hashlib
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from moviepy import (
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    VideoFileClip,
    concatenate_audioclips,
)

from .captions import create_caption_clips
from .media import create_background_video, make_safe_folder_name
from .narration import generate_narration
from .paths import FPS, HEIGHT, WIDTH

_CACHE_FILE_NAME = "render_cache.json"
_CACHE_LOCK = threading.Lock()


def _safe_close(clip: Any) -> None:
    close = getattr(clip, "close", None)
    if callable(close):
        close()


def _safe_close_many(*clips: Any) -> None:
    seen: set[int] = set()
    for clip in clips:
        if clip is None:
            continue
        clip_id = id(clip)
        if clip_id in seen:
            continue
        seen.add(clip_id)
        _safe_close(clip)


def _hash_file(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as file:
        while chunk := file.read(1024 * 1024):
            sha.update(chunk)
    return sha.hexdigest()


def _asset_signature(path: Path) -> dict[str, str | int]:
    if not path.exists():
        return {"missing": str(path)}

    return {
        "sha256": _hash_file(path),
        "size": path.stat().st_size,
        "suffix": path.suffix.lower(),
    }


def build_render_fingerprint(
    *,
    pioneer_name: str,
    script: str,
    asset_paths: list[Path],
    music_path: Path | None,
    voice: str,
    narration_rate: int,
    music_volume: float,
    words_per_caption: int,
    caption_y: int,
    caption_font_size: int,
    caption_bg_opacity: int,
) -> str:
    payload = {
        "pioneer_name": pioneer_name.strip(),
        "script": script.strip(),
        "assets": [_asset_signature(path) for path in asset_paths],
        "music": _asset_signature(music_path) if music_path else None,
        "voice": voice,
        "narration_rate": narration_rate,
        "music_volume": round(music_volume, 4),
        "words_per_caption": words_per_caption,
        "caption_y": caption_y,
        "caption_font_size": caption_font_size,
        "caption_bg_opacity": caption_bg_opacity,
    }
    digest_input = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(digest_input).hexdigest()


def _cache_file_path(pioneer_folder: Path) -> Path:
    return pioneer_folder / "output" / _CACHE_FILE_NAME


def _load_render_cache(pioneer_folder: Path) -> dict[str, str]:
    cache_file = _cache_file_path(pioneer_folder)
    if not cache_file.exists():
        return {}
    try:
        return json.loads(cache_file.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_render_cache(pioneer_folder: Path, cache_data: dict[str, str]) -> None:
    cache_file = _cache_file_path(pioneer_folder)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(cache_data, indent=2, sort_keys=True), encoding="utf-8")


def _find_cached_output(pioneer_folder: Path, fingerprint: str) -> Path | None:
    with _CACHE_LOCK:
        cache = _load_render_cache(pioneer_folder)
        output_path_str = cache.get(fingerprint)
        if not output_path_str:
            return None
        output_path = Path(output_path_str)
        if output_path.exists():
            return output_path
        cache.pop(fingerprint, None)
        _save_render_cache(pioneer_folder, cache)
    return None


def _record_cached_output(pioneer_folder: Path, fingerprint: str, output_path: Path) -> None:
    with _CACHE_LOCK:
        cache = _load_render_cache(pioneer_folder)
        cache[fingerprint] = str(output_path)
        _save_render_cache(pioneer_folder, cache)


def _probe_video_duration(video_path: Path) -> float:
    clip = VideoFileClip(str(video_path))
    try:
        return float(clip.duration or 0.0)
    finally:
        clip.close()


def create_final_audio(
    narration_path: Path,
    music_path: Path | None,
    duration: float,
    music_volume: float,
):
    narration = AudioFileClip(str(narration_path))

    if not music_path:
        return narration, [narration]

    music = AudioFileClip(str(music_path))
    disposable_clips: list[Any] = [narration, music]

    if music.duration < duration:
        copies_needed = int(duration / music.duration) + 1
        music = concatenate_audioclips([music for _ in range(copies_needed)])
        disposable_clips.append(music)

    music = music.subclipped(0, duration).with_volume_scaled(music_volume)
    disposable_clips.append(music)
    composite = CompositeAudioClip([music, narration])
    disposable_clips.append(composite)
    return composite, disposable_clips


def generate_short(
    pioneer_name: str,
    script: str,
    asset_paths: list[Path],
    music_path: Path | None,
    voice: str,
    narration_rate: int,
    music_volume: float,
    pioneer_folder: Path,
    job_directory: Path,
    words_per_caption: int = 8,
    caption_y: int = 1250,
    caption_font_size: int = 68,
    caption_bg_opacity: int = 185,
) -> tuple[Path, float]:
    fingerprint = build_render_fingerprint(
        pioneer_name=pioneer_name,
        script=script,
        asset_paths=asset_paths,
        music_path=music_path,
        voice=voice,
        narration_rate=narration_rate,
        music_volume=music_volume,
        words_per_caption=words_per_caption,
        caption_y=caption_y,
        caption_font_size=caption_font_size,
        caption_bg_opacity=caption_bg_opacity,
    )
    cached_output_path = _find_cached_output(pioneer_folder, fingerprint)
    if cached_output_path is not None:
        return cached_output_path, _probe_video_duration(cached_output_path)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    narration_output = pioneer_folder / "audio" / f"narration_{timestamp}.mp3"
    output_file = pioneer_folder / "output" / f"short_{make_safe_folder_name(pioneer_name)}_{timestamp}.mp4"

    narration_clip: AudioFileClip | None = None
    background_video = None
    caption_clips: list[Any] = []
    final_video = None
    final_audio = None
    final_audio_parts: list[Any] = []
    rendered_video = None

    generate_narration(
        text=script,
        voice=voice,
        output_path=narration_output,
        rate=f"{narration_rate:+d}%",
    )

    try:
        narration_clip = AudioFileClip(str(narration_output))
        duration = float(narration_clip.duration or 0.0)
        narration_clip.close()
        narration_clip = None

        background_video = create_background_video(asset_paths, duration, job_directory)
        caption_clips = create_caption_clips(
            script,
            duration,
            pioneer_folder / "captions",
            words_per_caption=words_per_caption,
            caption_y=caption_y,
            font_size=caption_font_size,
            bg_opacity=caption_bg_opacity,
        )

        final_video = CompositeVideoClip([background_video, *caption_clips], size=(WIDTH, HEIGHT))
        final_video = final_video.with_duration(duration)

        final_audio, final_audio_parts = create_final_audio(
            narration_path=narration_output,
            music_path=music_path,
            duration=duration,
            music_volume=music_volume,
        )

        rendered_video = final_video.with_audio(final_audio)
        rendered_video.write_videofile(
            str(output_file),
            fps=FPS,
            codec="libx264",
            audio_codec="aac",
            bitrate="7000k",
            audio_bitrate="192k",
            preset="medium",
            threads=4,
        )
        _record_cached_output(pioneer_folder, fingerprint, output_file)
        return output_file, duration
    finally:
        _safe_close_many(
            narration_clip,
            rendered_video,
            final_video,
            background_video,
            final_audio,
            *final_audio_parts,
            *caption_clips,
        )
        gc.collect()
