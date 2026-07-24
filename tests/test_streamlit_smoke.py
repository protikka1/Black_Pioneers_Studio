import ast
import py_compile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
APP_FILE = ROOT_DIR / "app.py"
DB_FILE = ROOT_DIR / "database" / "db.py"


class StreamlitSmokeTests(unittest.TestCase):
    def test_app_file_compiles(self) -> None:
        py_compile.compile(str(APP_FILE), doraise=True)

    def test_database_module_compiles(self) -> None:
        py_compile.compile(str(DB_FILE), doraise=True)

    def test_main_function_is_defined(self) -> None:
        module_ast = ast.parse(APP_FILE.read_text(encoding="utf-8"))
        function_names = {
            node.name
            for node in module_ast.body
            if isinstance(node, ast.FunctionDef)
        }
        self.assertIn("main", function_names)

    def test_safe_folder_helper_is_defined(self) -> None:
        module_ast = ast.parse(APP_FILE.read_text(encoding="utf-8"))
        function_names = {
            node.name
            for node in module_ast.body
            if isinstance(node, ast.FunctionDef)
        }
        self.assertIn("make_safe_folder_name", function_names)


if __name__ == "__main__":
    unittest.main()
