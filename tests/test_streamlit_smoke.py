import ast
import sqlite3
import py_compile
import unittest
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch

import desktop_launcher
from black_pioneers_studio import media
from database.migrations import apply_migrations


ROOT_DIR = Path(__file__).resolve().parents[1]
APP_FILE = ROOT_DIR / "app.py"
LAUNCHER_FILE = ROOT_DIR / "desktop_launcher.py"
PACKAGE_MODULES = [
    ROOT_DIR / "black_pioneers_studio" / "paths.py",
    ROOT_DIR / "black_pioneers_studio" / "models.py",
    ROOT_DIR / "black_pioneers_studio" / "media.py",
    ROOT_DIR / "black_pioneers_studio" / "jobs.py",
    ROOT_DIR / "black_pioneers_studio" / "captions.py",
    ROOT_DIR / "black_pioneers_studio" / "narration.py",
    ROOT_DIR / "black_pioneers_studio" / "rendering.py",
    ROOT_DIR / "database" / "__init__.py",
    ROOT_DIR / "database" / "connection.py",
    ROOT_DIR / "database" / "migrations.py",
    ROOT_DIR / "database" / "pioneer_repository.py",
    ROOT_DIR / "database" / "video_repository.py",
    ROOT_DIR / "database" / "db.py",
]


class StreamlitSmokeTests(unittest.TestCase):
    def test_app_file_compiles(self) -> None:
        py_compile.compile(str(APP_FILE), doraise=True)

    def test_launcher_compiles(self) -> None:
        py_compile.compile(str(LAUNCHER_FILE), doraise=True)

    def test_package_modules_compile(self) -> None:
        for module_path in PACKAGE_MODULES:
            py_compile.compile(str(module_path), doraise=True)

    def test_main_function_is_defined(self) -> None:
        module_ast = ast.parse(APP_FILE.read_text(encoding="utf-8"))
        function_names = {
            node.name
            for node in module_ast.body
            if isinstance(node, ast.FunctionDef)
        }
        self.assertIn("main", function_names)

    def test_safe_folder_helper_is_defined(self) -> None:
        self.assertEqual(media.make_safe_folder_name("Hiram Revels"), "hiram_revels")

    def test_migrations_create_expected_schema(self) -> None:
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row

        apply_migrations(connection)

        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(pioneers)").fetchall()
        }
        for column_name in ("achievement", "biography", "folder_path", "updated_at"):
            self.assertIn(column_name, columns)

    def test_launcher_prefers_configured_project_root(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "app.py").write_text("print('hello')\n", encoding="utf-8")

            with patch.dict("os.environ", {"BLACK_PIONEERS_ROOT": temp_dir}):
                self.assertEqual(desktop_launcher._resolve_project_root(), root.resolve())

    def test_launcher_prefers_port_env_var(self) -> None:
        with patch.dict("os.environ", {"PORT": "9123", "BLACK_PIONEERS_PORT": "8502"}):
            self.assertEqual(desktop_launcher._resolve_port(), 9123)


if __name__ == "__main__":
    unittest.main()
