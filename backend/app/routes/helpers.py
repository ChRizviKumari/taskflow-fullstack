from __future__ import annotations

import sqlite3
from typing import Any

from flask import g

from ..db import get_db
from ..errors import ApiError


def like_pattern(term: str) -> str:
    """Escape LIKE wildcards so user input is matched literally."""
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def page_response(items: list[dict[str, Any]], page: int, page_size: int, total: int) -> dict[str, Any]:
    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": (total + page_size - 1) // page_size,
    }


def owned_board(board_id: int) -> sqlite3.Row:
    """Fetch a board owned by the caller; foreign boards look like 404 (no existence leak)."""
    row = get_db().execute("SELECT * FROM boards WHERE id=? AND owner_id=?", (board_id, g.user_id)).fetchone()
    if row is None:
        raise ApiError(404, "not_found", "Board not found")
    return row


def owned_column(column_id: int) -> sqlite3.Row:
    row = get_db().execute(
        """SELECT c.* FROM columns c JOIN boards b ON b.id = c.board_id
           WHERE c.id=? AND b.owner_id=?""",
        (column_id, g.user_id),
    ).fetchone()
    if row is None:
        raise ApiError(404, "not_found", "Column not found")
    return row


def owned_task(task_id: int) -> sqlite3.Row:
    row = get_db().execute(
        """SELECT t.* FROM tasks t JOIN boards b ON b.id = t.board_id
           WHERE t.id=? AND b.owner_id=?""",
        (task_id, g.user_id),
    ).fetchone()
    if row is None:
        raise ApiError(404, "not_found", "Task not found")
    return row
