from __future__ import annotations

from flask import Blueprint, jsonify, request

from ..auth import require_auth
from ..db import get_db, transaction, utcnow
from ..errors import ApiError, parse_model
from ..schemas import TaskPatch
from .helpers import owned_task

bp = Blueprint("tasks", __name__, url_prefix="/api/tasks")


@bp.get("/<int:task_id>")
@require_auth
def get_task(task_id: int):
    return jsonify({"task": dict(owned_task(task_id))})


def _renumber(db, column_id: int, ordered_ids: list[int]) -> None:
    for pos, tid in enumerate(ordered_ids):
        db.execute("UPDATE tasks SET position=? WHERE id=?", (pos, tid))


@bp.patch("/<int:task_id>")
@require_auth
def update_task(task_id: int):
    current = owned_task(task_id)
    data = parse_model(TaskPatch, request.get_json(silent=True))
    fields = data.model_dump(exclude_unset=True, exclude_none=True)
    expected = fields.pop("version")
    new_col = fields.pop("column_id", None)
    new_pos = fields.pop("position", None)

    with transaction() as db:
        # Re-read inside the write lock; the version check is the optimistic lock.
        row = db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        if row is None:
            raise ApiError(404, "not_found", "Task not found")
        if row["version"] != expected:
            raise ApiError(409, "version_conflict", "Task was modified by someone else",
                           {"current_version": row["version"], "current": dict(row)})

        target_col = new_col if new_col is not None else row["column_id"]
        if target_col != row["column_id"]:
            ok = db.execute("SELECT 1 FROM columns WHERE id=? AND board_id=?", (target_col, current["board_id"])).fetchone()
            if ok is None:
                raise ApiError(422, "validation_error", "Invalid input",
                               [{"field": "column_id", "message": "column does not belong to this board"}])

        if target_col != row["column_id"] or new_pos is not None:
            src = [r[0] for r in db.execute(
                "SELECT id FROM tasks WHERE column_id=? AND id<>? ORDER BY position, id", (row["column_id"], task_id))]
            if target_col != row["column_id"]:
                _renumber(db, row["column_id"], src)
                dest = [r[0] for r in db.execute(
                    "SELECT id FROM tasks WHERE column_id=? ORDER BY position, id", (target_col,))]
            else:
                dest = src
            idx = len(dest) if new_pos is None else min(new_pos, len(dest))
            dest.insert(idx, task_id)
            fields["column_id"] = target_col
            _renumber(db, target_col, dest)

        sets = [f"{k}=?" for k in fields]
        params = list(fields.values())
        db.execute(
            f"UPDATE tasks SET {', '.join(sets + ['version=version+1', 'updated_at=?'])} WHERE id=? AND version=?",
            [*params, utcnow(), task_id, expected],
        )
    return jsonify({"task": dict(get_db().execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone())})


@bp.delete("/<int:task_id>")
@require_auth
def delete_task(task_id: int):
    row = owned_task(task_id)
    with transaction() as db:
        db.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        ids = [r[0] for r in db.execute(
            "SELECT id FROM tasks WHERE column_id=? ORDER BY position, id", (row["column_id"],))]
        _renumber(db, row["column_id"], ids)
    return "", 204
