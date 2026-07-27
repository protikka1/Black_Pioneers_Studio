import unittest

from black_pioneers_studio.captions import split_script_into_captions


class CaptionTests(unittest.TestCase):
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
