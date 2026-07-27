import tempfile
import unittest
from pathlib import Path

from PIL import Image

from black_pioneers_studio.media import create_background_video, prepare_vertical_image
from black_pioneers_studio.paths import HEIGHT, WIDTH


class MediaValidationTests(unittest.TestCase):
    def test_prepare_vertical_image_resizes_to_vertical_canvas(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path = root / "source.png"
            destination_path = root / "destination.jpg"

            Image.new("RGB", (320, 180), "red").save(source_path)

            result_path = prepare_vertical_image(source_path, destination_path)

            self.assertEqual(result_path, destination_path)
            with Image.open(result_path) as image:
                self.assertEqual(image.size, (WIDTH, HEIGHT))

    def test_create_background_video_rejects_unsupported_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            unsupported_path = root / "notes.txt"
            unsupported_path.write_text("not media", encoding="utf-8")

            with self.assertRaises(ValueError) as context:
                create_background_video(
                    [unsupported_path],
                    duration=3.0,
                    job_directory=root / "job",
                )

        self.assertIn("No supported image or video assets were found", str(context.exception))


if __name__ == "__main__":
    unittest.main()
