import unittest

from black_pioneers_studio.media import make_safe_folder_name


class FilenameSafetyTests(unittest.TestCase):
    def test_strips_whitespace_and_normalizes_case(self) -> None:
        self.assertEqual(make_safe_folder_name("  Hiram Revels  "), "hiram_revels")

    def test_collapses_punctuation(self) -> None:
        self.assertEqual(make_safe_folder_name("Mary-Ann Shadd Cary"), "mary_ann_shadd_cary")

    def test_returns_empty_string_for_non_name_input(self) -> None:
        self.assertEqual(make_safe_folder_name("!!!"), "")


if __name__ == "__main__":
    unittest.main()
