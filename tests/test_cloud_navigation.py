import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


class CloudNavigationTests(unittest.TestCase):
    def test_all_pages_load_with_an_empty_cloud_database(self):
        root = Path(__file__).resolve().parents[1]
        with TemporaryDirectory() as folder:
            env = dict(os.environ, BLACK_PIONEERS_DATA_DIR=folder)
            code = """
from streamlit.testing.v1 import AppTest
app = AppTest.from_file('app.py').run(timeout=30)
assert not app.exception, app.exception
for page in ['Create Pioneer', 'Create Short', 'Video Library', 'Tools', 'Settings', 'Dashboard']:
    app.sidebar.radio[0].set_value(page).run(timeout=30)
    assert not app.exception, (page, app.exception)
"""
            subprocess.run([sys.executable, "-c", code], cwd=root, env=env,
                           check=True, timeout=120, capture_output=True, text=True)
