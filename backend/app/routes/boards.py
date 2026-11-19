from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from ..auth import require_auth
from ..db import get_db, transaction, utcnow
from ..errors import ApiError, parse_model
from ..schemas import BoardIn, PageQuery
from .helpers import like_pattern, owned_board, page_response

bp = Blueprint("boards", __name__, url_prefix="/api/boards")

DEFAULT_COLUMNS = ("To Do", "In Progress", "Done")


@bp.get("")
@require_auth
def list_boards():
    q = parse_model(PageQuery, request.args.to_dict())
    where, params = "owner_id = ?", [g.user_id]
    if q.q:
        where += " AND name LIKE ? ESCAPE '\\'"
        params.append(like_pattern(q.q))
    db = get_db()
    total = db.execute(f"SELECT COUNT(*) FROM boards WHERE {where}", params).fetchone()[0]
    rows = db.execute(
        f"""SELECT b.*, (SELECT COUNT(*) FROM tasks t WHERE t.board_id = b.id) AS task_count
            FROM boards b WHERE {where} ORDER BY b.id DESC LIMIT ? OFFSET ?""",
        [*params, q.page_size, (q.page - 1) * q.page_size],
    ).fetchall()
    return jsonify(page_response([dict(r) for r in rows], q.page, q.page_size, total))


@bp.post("")
@require_auth
def create_board():
    data = parse_model(BoardIn, request.get_json(silent=True))
    with transaction() as db:
        board_id = db.execute(
            "INSERT INTO boards (owner_id, name, created_at) VALUES (?,?,?)",
            (g.user_id, data.name, utcnow()),
        ).lastrowid
        for pos, name in enumerate(DEFAULT_COLUMNS):
            db.execute("INSERT INTO columns (board_id, name, position) VALUES (?,?,?)", (board_id, name, pos))
    return jsonify({"board": _board_detail(board_id)}), 201


def _board_detail(board_id: int) -> dict:
    db = get_db()
    board = dict(db.execute("SELECT * FROM boards WHERE id=?", (board_id,)).fetchone())
    cols = db.execute(
        """SELECT c.*, (SELECT COUNT(*) FROM tasks t WHERE t.column_id = c.id) AS task_count
           FROM columns c WHERE c.board_id=? ORDER BY c.position""",
        (board_id,),
    ).fetchall()
    board["columns"] = [dict(c) for c in cols]
    return board


@bp.get("/<int:board_id>")
@require_auth
def get_board(board_id: int):
    owned_board(board_id)
    return jsonify({"board": _board_detail(board_id)})


@bp.patch("/<int:board_id>")
@require_auth
def rename_board(board_id: int):
    owned_board(board_id)
    data = parse_model(BoardIn, request.get_json(silent=True))
    with transaction() as db:
        db.execute("UPDATE boards SET name=? WHERE id=?", (data.name, board_id))
    return jsonify({"board": _board_detail(board_id)})


@bp.delete("/<int:board_id>")
@require_auth
def delete_board(board_id: int):
    owned_board(board_id)
    with transaction() as db:
        db.execute("DELETE FROM boards WHERE id=?", (board_id,))
    return "", 204


@bp.post("/<int:board_id>/columns")
@require_auth
def create_column(board_id: int):
    from ..schemas import ColumnIn

    owned_board(board_id)
    data = parse_model(ColumnIn, request.get_json(silent=True))
    with transaction() as db:
        pos = db.execute("SELECT COALESCE(MAX(position)+1, 0) FROM columns WHERE board_id=?", (board_id,)).fetchone()[0]
        col_id = db.execute(
            "INSERT INTO columns (board_id, name, position) VALUES (?,?,?)", (board_id, data.name, pos)
        ).lastrowid
    row = get_db().execute("SELECT * FROM columns WHERE id=?", (col_id,)).fetchone()
    return jsonify({"column": dict(row)}), 201


@bp.get("/<int:board_id>/tasks")
@require_auth
def list_tasks(board_id: int):
    from ..schemas import TaskQuery

    owned_board(board_id)
    q = parse_model(TaskQuery, request.args.to_dict())
    where, params = ["t.board_id = ?"], [board_id]
    if q.q:
        where.append("(t.title LIKE ? ESCAPE '\\' OR t.description LIKE ? ESCAPE '\\')")
        params += [like_pattern(q.q)] * 2
    if q.column_id is not None:
        where.append("t.column_id = ?")
        params.append(q.column_id)
    if q.priority:
        where.append("t.priority = ?")
        params.append(q.priority)
    clause = " AND ".join(where)
    db = get_db()
    total = db.execute(f"SELECT COUNT(*) FROM tasks t WHERE {clause}", params).fetchone()[0]
    rows = db.execute(
        f"""SELECT t.* FROM tasks t JOIN columns c ON c.id = t.column_id
            WHERE {clause} ORDER BY c.position, t.position, t.id LIMIT ? OFFSET ?""",
        [*params, q.page_size, (q.page - 1) * q.page_size],
    ).fetchall()
    return jsonify(page_response([dict(r) for r in rows], q.page, q.page_size, total))
