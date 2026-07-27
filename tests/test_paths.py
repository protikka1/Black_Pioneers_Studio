import tempfile
import unittest
from datetime import datetime
import json
from pathlib import Path
from unittest.mock import patch

from black_pioneers_studio import paths
from black_pioneers_studio.rendering import generate_short


class _FakeAudioClip:
    def __init__(self, duration: float = 1.25) -> None:
        self.duration = duration

    def close(self) -> None:
        return None


class _FakeVideoClip:
    def __init__(self) -> None:
        self.written_to: str | None = None

    def with_duration(self, _duration: float):
        return self

    def with_audio(self, _audio):
        return self

    def write_videofile(self, filename: str, **_kwargs) -> None:
        self.written_to = filename

    def close(self) -> None:
        return None


class OutputPathTests(unittest.TestCase):
    def test_generate_short_uses_safe_filename_and_timestamp(self) -> None:
        fixed_time = datetime(2026, 7, 26, 18, 7, 55)

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            pioneer_folder = root / "output"
            job_directory = root / "temp"
            pioneer_folder.mkdir()
            job_directory.mkdir()

            fake_video = _FakeVideoClip()

            with patch("black_pioneers_studio.rendering.datetime") as mocked_datetime, patch(
                "black_pioneers_studio.rendering.AudioFileClip",
                side_effect=lambda *_args, **_kwargs: _FakeAudioClip(),
            ), patch(
                "black_pioneers_studio.rendering.create_background_video",
                return_value=fake_video,
            ), patch(
                "black_pioneers_studio.rendering.create_caption_clips",
                return_value=[],
            ), patch(
                "black_pioneers_studio.rendering.create_final_audio",
                return_value=(_FakeAudioClip(), [_FakeAudioClip()]),
            ), patch(
                "black_pioneers_studio.rendering.CompositeVideoClip",
                return_value=fake_video,
            ), patch(
                "black_pioneers_studio.rendering.generate_narration",
                return_value=None,
            ):
                mocked_datetime.now.return_value = fixed_time
                output_path, _duration = generate_short(
                    pioneer_name="Hiram Revels",
                    script="one two three",
                    asset_paths=[root / "input.png"],
                    music_path=None,
                    voice="en-US-GuyNeural",
                    narration_rate=0,
                    music_volume=0.1,
                    pioneer_folder=pioneer_folder,
                    job_directory=job_directory,
                )

        self.assertEqual(
            output_path,
            pioneer_folder / "output" / "short_hiram_revels_20260726_180755.mp4",
        )

    def test_generate_short_reuses_cached_output_instead_of_regenerating(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            pioneer_folder = root / "output"
            output_dir = pioneer_folder / "output"
            output_dir.mkdir(parents=True)
            job_directory = root / "temp"
            job_directory.mkdir()

            asset_path = root / "input.png"
            asset_path.write_bytes(b"image-bytes")
            cached_output = output_dir / "short_hiram_revels_cached.mp4"
            cached_output.write_bytes(b"video-bytes")

            fingerprint = "fingerprint-123"
            (output_dir / "render_cache.json").write_text(
                json.dumps({fingerprint: str(cached_output)}),
                encoding="utf-8",
            )

            with patch(
                "black_pioneers_studio.rendering.build_render_fingerprint",
                return_value=fingerprint,
            ), patch(
                "black_pioneers_studio.rendering._probe_video_duration",
                return_value=3.5,
            ), patch(
                "black_pioneers_studio.rendering.generate_narration",
            ) as generate_narration_mock:
                output_path, duration = generate_short(
                    pioneer_name="Hiram Revels",
                    script="one two three",
                    asset_paths=[asset_path],
                    music_path=None,
                    voice="en-US-GuyNeural",
                    narration_rate=0,
                    music_volume=0.1,
                    pioneer_folder=pioneer_folder,
                    job_directory=job_directory,
                )

        self.assertEqual(output_path, cached_output)
        self.assertEqual(duration, 3.5)
        generate_narration_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
