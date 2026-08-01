import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from database import connection as db_connection
from database.migrations import apply_migrations
from database.pioneer_repository import create_pioneer, get_all_pioneers, update_pioneer_folder


def _configure_temp_database(temp_dir: Path):
    database_dir = temp_dir / "database"
    database_file = database_dir / "pioneers.db"
    return patch.object(db_connection, "DATABASE_DIR", database_dir), patch.object(
        db_connection,
        "DATABASE_FILE",
        database_file,
    )


class DatabaseTests(unittest.TestCase):
    def test_crud_operations_work_against_temporary_database(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            patch_dir, patch_file = _configure_temp_database(root)

            with patch_dir, patch_file:
                pioneer_id = create_pioneer(
                    name="Hiram Revels",
                    category="Politics",
                    achievement="First Black U.S. Senator",
                    biography="Test biography",
                )

                pioneers = get_all_pioneers()
                self.assertEqual(len(pioneers), 1)
                self.assertEqual(pioneers[0]["id"], pioneer_id)
                self.assertEqual(pioneers[0]["name"], "Hiram Revels")
                self.assertEqual(pioneers[0]["achievement"], "First Black U.S. Senator")

                update_pioneer_folder(pioneer_id, str(root / "output" / "hiram_revels"))
                updated = get_all_pioneers()[0]
                self.assertEqual(updated["folder_path"], str(root / "output" / "hiram_revels"))
                self.assertTrue(updated["updated_at"])

    def test_migrations_upgrade_legacy_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_file = Path(temp_dir) / "pioneers.db"
            connection = sqlite3.connect(database_file)
            connection.row_factory = sqlite3.Row

            connection.execute(
                """
                CREATE TABLE pioneers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT,
                    project_title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                INSERT INTO pioneers (name, category, project_title, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("Hiram Revels", "Politics", "Black Pioneers: First in American History", "2024-01-01T00:00:00", ""),
            )
            connection.commit()

            apply_migrations(connection)

            columns = {
                row["name"] for row in connection.execute("PRAGMA table_info(pioneers)").fetchall()
            }
            for column_name in ("achievement", "biography", "folder_path", "updated_at"):
                self.assertIn(column_name, columns)

            migrations = connection.execute(
                "SELECT version FROM schema_migrations ORDER BY version"
            ).fetchall()
            self.assertEqual([row["version"] for row in migrations], [1, 2])

            row = connection.execute("SELECT * FROM pioneers").fetchone()
            self.assertEqual(row["folder_path"], "")
            self.assertEqual(row["updated_at"], "2024-01-01T00:00:00")


if __name__ == "__main__":
    unittest.main()
