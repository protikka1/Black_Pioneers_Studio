from __future__ import annotations

import sqlite3

from black_pioneers_studio.paths import BASE_DIR

from .migrations import apply_migrations

DATABASE_DIR = BASE_DIR / "database"
DATABASE_FILE = DATABASE_DIR / "pioneers.db"


def get_connection() -> sqlite3.Connection:
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_FILE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


get_database_connection = get_connection


def initialize_database() -> None:
    with get_connection() as connection:
        apply_migrations(connection)
