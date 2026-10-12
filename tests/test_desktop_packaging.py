import os
from pathlib import Path
import socket
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

import desktop_launcher as launcher


class DesktopPackagingTests(unittest.TestCase):
    def test_installed_app_ignores_original_checkout(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            bundled = root / "bundle" / "studio"
            original = root / "checkout"
            bundled.mkdir(parents=True)
            original.mkdir()
            (bundled / "app.py").write_text("bundled")
            (original / "app.py").write_text("original")
            with patch.object(sys, "frozen", True, create=True), patch.object(
                sys, "_MEIPASS", str(root / "bundle"), create=True
            ), patch.dict(os.environ, {"BLACK_PIONEERS_ROOT": str(original)}):
                self.assertEqual(launcher._resolve_project_root(), bundled)

    def test_installed_app_fails_when_bundled_source_missing(self):
        with TemporaryDirectory() as folder, patch.object(sys, "frozen", True, create=True), patch.object(
            sys, "_MEIPASS", folder, create=True
        ):
            with self.assertRaises(FileNotFoundError):
                launcher._resolve_project_root()

    def test_bundled_ffmpeg_overrides_developer_environment(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "studio").mkdir()
            (root / "studio" / "app.py").write_text("test")
            (root / "bin").mkdir()
            (root / "bin" / "ffmpeg").touch()
            with patch.object(sys, "frozen", True, create=True), patch.object(
                sys, "_MEIPASS", folder, create=True
            ), patch.dict(os.environ, {"FFMPEG_BINARY": "/missing/developer/ffmpeg"}):
                launcher._prepare_environment()
                self.assertEqual(os.environ["FFMPEG_BINARY"], str(root / "bin" / "ffmpeg"))
                self.assertTrue(os.environ["PATH"].startswith(str(root / "bin")))

    def test_frozen_server_uses_own_executable(self):
        with patch.object(sys, "frozen", True, create=True):
            self.assertEqual(launcher._server_command(9123), [sys.executable, "--serve", "9123"])

    def test_data_and_database_follow_external_runtime_directory(self):
        with TemporaryDirectory() as folder:
            env = dict(os.environ, BLACK_PIONEERS_DATA_DIR=folder)
            check = (
                "from black_pioneers_studio.paths import DATA_DIR,OUTPUT_DIR,TEMP_DIR;"
                "from database.connection import DATABASE_FILE;"
                "from pathlib import Path;"
                "import os;"
                "assert DATA_DIR==Path(os.environ['BLACK_PIONEERS_DATA_DIR']).resolve();"
                "assert DATA_DIR in OUTPUT_DIR.parents and DATA_DIR in TEMP_DIR.parents;"
                "assert DATA_DIR in DATABASE_FILE.parents"
            )
            subprocess.run([sys.executable, "-c", check], env=env, check=True)

    def test_busy_port_selects_another_port(self):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            busy = sock.getsockname()[1]
            self.assertNotEqual(launcher._available_port(busy), busy)

    def test_startup_stops_waiting_when_child_exits(self):
        self.assertFalse(launcher._wait_for_http("http://127.0.0.1:1", process=Mock(poll=lambda: 1)))

    def test_server_loads_local_configuration_before_starting(self):
        from streamlit.web import bootstrap
        with patch.object(launcher, "_prepare_environment", return_value=Path("/bundle/studio")), patch.object(
            bootstrap, "load_config_options"
        ) as load, patch.object(bootstrap, "run") as run:
            launcher._serve(9123)
        options = load.call_args.args[0]
        self.assertEqual(options["server.address"], "127.0.0.1")
        self.assertEqual(options["server.port"], 9123)
        self.assertFalse(options["global.developmentMode"])
        self.assertEqual(run.call_args.args[3], options)
