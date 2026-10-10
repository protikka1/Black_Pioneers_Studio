import unittest
from unittest.mock import patch
from PIL import ImageFont

from black_pioneers_studio.captions import load_font, split_script_into_captions


class CaptionTests(unittest.TestCase):
    def test_linux_font_preserves_requested_size(self) -> None:
        font = load_font(68)
        self.assertEqual(font.size, 68)

    def test_fallback_font_preserves_requested_size(self) -> None:
        with patch("black_pioneers_studio.captions.Path.exists", return_value=False):
            font = load_font(68)
        self.assertIsInstance(font, ImageFont.FreeTypeFont)
        self.assertEqual(font.size, 68)

    def test_splits_script_into_word_chunks(self) -> None:
        script = "one two three four five six seven"

        self.assertEqual(
            split_script_into_captions(script, words_per_caption=3),
            ["one two three", "four five six", "seven"],
        )

    def test_normalizes_newlines(self) -> None:
        script = "one two\nthree four five"

        self.assertEqual(
            split_script_into_captions(script, words_per_caption=2),
            ["one two", "three four", "five"],
        )


if __name__ == "__main__":
    unittest.main()
