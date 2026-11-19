from __future__ import annotations

import sqlite3

from flask import Blueprint, current_app, g, jsonify, request

from ..auth import require_auth
from ..db import get_db, transaction, utcnow
from ..errors import ApiError, parse_model
from ..schemas import LoginIn, RegisterIn
from ..security import hash_password, issue_token, verify_password

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _public(row: sqlite3.Row) -> dict:
    return {"id": row["id"], "email": row["email"], "name": row["name"], "created_at": row["created_at"]}


def _token(user_id: int) -> str:
    cfg = current_app.config
    return issue_token(user_id, cfg["SECRET_KEY"], cfg["JWT_TTL_SECONDS"])


@bp.post("/register")
def register():
    data = parse_model(RegisterIn, request.get_json(silent=True))
    email = data.email.lower()
    pw_hash = hash_password(data.password, current_app.config["PBKDF2_ITERATIONS"])
    try:
        with transaction() as db:
            cur = db.execute(
                "INSERT INTO users (email, name, password_hash, created_at) VALUES (?,?,?,?)",
                (email, data.name, pw_hash, utcnow()),
            )
            user_id = cur.lastrowid
    except sqlite3.IntegrityError as exc:
        raise ApiError(409, "email_taken", "An account with this email already exists") from exc
    row = get_db().execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    return jsonify({"user": _public(row), "token": _token(user_id)}), 201


@bp.post("/login")
def login():
    data = parse_model(LoginIn, request.get_json(silent=True))
    row = get_db().execute("SELECT * FROM users WHERE email=?", (data.email.lower(),)).fetchone()
    # Same error for unknown user and wrong password (no account enumeration).
    if row is None or not verify_password(data.password, row["password_hash"]):
        raise ApiError(401, "invalid_credentials", "Invalid email or password")
    return jsonify({"user": _public(row), "token": _token(row["id"])})


@bp.get("/me")
@require_auth
def me():
    row = get_db().execute("SELECT * FROM users WHERE id=?", (g.user_id,)).fetchone()
    if row is None:
        raise ApiError(401, "unauthorized", "User no longer exists")
    return jsonify({"user": _public(row)})
