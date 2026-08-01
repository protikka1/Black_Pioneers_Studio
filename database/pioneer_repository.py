from __future__ import annotations

from datetime import datetime

from black_pioneers_studio.models import PioneerRecord
from black_pioneers_studio.paths import PROJECT_TITLE

from .connection import get_connection, initialize_database


def create_pioneer(
    name: str,
    category: str = "",
    achievement: str = "",
    biography: str = "",
) -> int:
    initialize_database()
    timestamp = datetime.now().isoformat(timespec="seconds")

    with get_connection() as connection:
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


def get_all_pioneers() -> list[PioneerRecord]:
    initialize_database()

    with get_connection() as connection:
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
    initialize_database()
    timestamp = datetime.now().isoformat(timespec="seconds")

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE pioneers
            SET folder_path = ?, updated_at = ?
            WHERE id = ?
            """,
            (folder_path.strip(), timestamp, pioneer_id),
        )

