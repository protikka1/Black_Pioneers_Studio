from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Callable

PROJECT_TITLE = "Black Pioneers: First in American History"
MIGRATION_TABLE = "schema_migrations"

Migration = Callable[[sqlite3.Connection], None]


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
        """,
        (table_name,),
    ).fetchone()
    return row is not None


def _column_exists(
    connection: sqlite3.Connection,
    table_name: str,
    column_name: str,
) -> bool:
    columns = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return any(column["name"] == column_name for column in columns)


def _ensure_migration_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {MIGRATION_TABLE} (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
        """
    )


def _current_version(connection: sqlite3.Connection) -> int:
    row = connection.execute(
        f"SELECT COALESCE(MAX(version), 0) AS version FROM {MIGRATION_TABLE}"
    ).fetchone()
    return int(row["version"] or 0)


def _record_migration(connection: sqlite3.Connection, version: int) -> None:
    connection.execute(
        f"INSERT INTO {MIGRATION_TABLE} (version, applied_at) VALUES (?, ?)",
        (version, datetime.now().isoformat(timespec="seconds")),
    )


def _migration_001_create_pioneers_table(connection: sqlite3.Connection) -> None:
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


def _migration_002_add_pioneer_columns(connection: sqlite3.Connection) -> None:
    if _table_exists(connection, "pioneers"):
        for column_name in ("achievement", "biography", "folder_path", "updated_at"):
            if not _column_exists(connection, "pioneers", column_name):
                connection.execute(
                    "ALTER TABLE pioneers ADD COLUMN "
                    f"{column_name} TEXT DEFAULT ''"
                )

        connection.execute(
            """
            UPDATE pioneers
            SET
                achievement = COALESCE(NULLIF(achievement, ''), ''),
                biography = COALESCE(NULLIF(biography, ''), ''),
                folder_path = COALESCE(NULLIF(folder_path, ''), ''),
                updated_at = COALESCE(NULLIF(updated_at, ''), created_at)
            """
        )


MIGRATIONS: tuple[tuple[int, Migration], ...] = (
    (1, _migration_001_create_pioneers_table),
    (2, _migration_002_add_pioneer_columns),
)


def apply_migrations(connection: sqlite3.Connection) -> None:
    _ensure_migration_table(connection)
    current_version = _current_version(connection)

    for version, migration in MIGRATIONS:
        if version <= current_version:
            continue
        migration(connection)
        _record_migration(connection, version)

    connection.commit()

