from __future__ import annotations

from flask import Blueprint, jsonify, request

from ..auth import require_auth
from ..db import get_db, transaction, utcnow
from ..errors import parse_model
from ..schemas import ColumnIn, TaskCreate
from .helpers import owned_column

bp = Blueprint("columns", __name__, url_prefix="/api/columns")


@bp.patch("/<int:column_id>")
@require_auth
def rename_column(column_id: int):
    owned_column(column_id)
    data = parse_model(ColumnIn, request.get_json(silent=True))
    with transaction() as db:
        db.execute("UPDATE columns SET name=? WHERE id=?", (data.name, column_id))
    row = get_db().execute("SELECT * FROM columns WHERE id=?", (column_id,)).fetchone()
    return jsonify({"column": dict(row)})


@bp.delete("/<int:column_id>")
@require_auth
def delete_column(column_id: int):
    col = owned_column(column_id)
    with transaction() as db:
        db.execute("DELETE FROM columns WHERE id=?", (column_id,))
        # close the gap so positions stay contiguous
        ids = [r[0] for r in db.execute(
            "SELECT id FROM columns WHERE board_id=? ORDER BY position", (col["board_id"],))]
        for pos, cid in enumerate(ids):
            db.execute("UPDATE columns SET position=? WHERE id=?", (pos, cid))
    return "", 204


@bp.post("/<int:column_id>/tasks")
@require_auth
def create_task(column_id: int):
    col = owned_column(column_id)
    data = parse_model(TaskCreate, request.get_json(silent=True))
    now = utcnow()
    with transaction() as db:
        pos = db.execute("SELECT COALESCE(MAX(position)+1, 0) FROM tasks WHERE column_id=?", (column_id,)).fetchone()[0]
        task_id = db.execute(
            """INSERT INTO tasks (board_id, column_id, title, description, priority, position, version, created_at, updated_at)
               VALUES (?,?,?,?,?,?,1,?,?)""",
            (col["board_id"], column_id, data.title, data.description, data.priority, pos, now, now),
        ).lastrowid
    row = get_db().execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    return jsonify({"task": dict(row)}), 201
