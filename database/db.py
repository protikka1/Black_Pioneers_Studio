from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

PROJECT_TITLE = "Black Pioneers: First in American History"

DATABASE_DIR = Path(__file__).resolve().parent
DATABASE_FILE = DATABASE_DIR / "pioneers.db"


def get_database_connection() -> sqlite3.Connection:
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_FILE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _column_exists(
    connection: sqlite3.Connection,
    table_name: str,
    column_name: str,
) -> bool:
    columns = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return any(column["name"] == column_name for column in columns)


def _add_column_if_missing(
    connection: sqlite3.Connection,
    table_name: str,
    column_name: str,
    column_definition: str,
) -> None:
    if _column_exists(connection, table_name, column_name):
        return

    connection.execute(
        "ALTER TABLE "
        f"{table_name} "
        "ADD COLUMN "
        f"{column_name} {column_definition}"
    )


def initialize_database() -> None:
    with get_database_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS pioneers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT,
                achievement TEXT DEFAULT '',
                biography TEXT DEFAULT '',
                project_title TEXT NOT NULL,
                folder_path TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(name, project_title)
            )
            """
        )

        _add_column_if_missing(
            connection,
            "pioneers",
            "achievement",
            "TEXT DEFAULT ''",
        )
        _add_column_if_missing(
            connection,
            "pioneers",
            "biography",
            "TEXT DEFAULT ''",
        )
        _add_column_if_missing(
            connection,
            "pioneers",
            "folder_path",
            "TEXT DEFAULT ''",
        )
        _add_column_if_missing(
            connection,
            "pioneers",
            "updated_at",
            "TEXT DEFAULT ''",
        )

        connection.execute(
            """
            UPDATE pioneers
            SET updated_at = COALESCE(NULLIF(updated_at, ''), created_at)
            WHERE updated_at IS NULL OR updated_at = ''
            """
        )


def create_pioneer(
    name: str,
    category: str = "",
    achievement: str = "",
    biography: str = "",
) -> int:
    timestamp = datetime.now().isoformat(timespec="seconds")

    with get_database_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO pioneers (
                name,
                category,
                achievement,
                biography,
                project_title,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name.strip(),
                category.strip(),
                achievement.strip(),
                biography.strip(),
                PROJECT_TITLE,
                timestamp,
                timestamp,
            ),
        )

        return int(cursor.lastrowid)


def get_all_pioneers() -> list[dict[str, object]]:
    with get_database_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                name,
                category,
                achievement,
                biography,
                folder_path,
                created_at,
                updated_at
            FROM pioneers
            WHERE project_title = ?
            ORDER BY created_at DESC, id DESC
            """,
            (PROJECT_TITLE,),
        ).fetchall()

    return [dict(row) for row in rows]


def update_pioneer_folder(pioneer_id: int, folder_path: str) -> None:
    timestamp = datetime.now().isoformat(timespec="seconds")

    with get_database_connection() as connection:
        connection.execute(
            """
            UPDATE pioneers
            SET folder_path = ?, updated_at = ?
            WHERE id = ?
            """,
            (folder_path.strip(), timestamp, pioneer_id),
        )
