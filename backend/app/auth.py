"""Authentication decorator."""
from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from flask import current_app, g, request

from .errors import ApiError
from .security import TokenError, jwt_decode


def require_auth[F: Callable[..., Any]](fn: F) -> F:
    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any):
        header = request.headers.get("Authorization", "")
        scheme, _, token = header.partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise ApiError(401, "unauthorized", "Missing bearer token")
        try:
            payload = jwt_decode(token, current_app.config["SECRET_KEY"])
        except TokenError as exc:
            raise ApiError(401, "unauthorized", f"Invalid token: {exc}") from exc
        sub = payload.get("sub")
        if not isinstance(sub, int):
            raise ApiError(401, "unauthorized", "Invalid token subject")
        g.user_id = sub
        return fn(*args, **kwargs)

    return wrapper  # type: ignore[return-value]
