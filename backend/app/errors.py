"""Consistent JSON error envelope: {"error": {"code", "message", "details"?}}."""
from __future__ import annotations

from typing import Any

from flask import Flask, jsonify
from pydantic import BaseModel, ValidationError
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, details: Any = None) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.details = details


def _envelope(status: int, code: str, message: str, details: Any = None):
    body: dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        body["details"] = details
    return jsonify({"error": body}), status


def parse_model[M: BaseModel](model: type[M], data: Any) -> M:
    """Validate ``data`` with a pydantic model, raising ApiError(422) on failure."""
    if not isinstance(data, dict):
        raise ApiError(400, "bad_request", "Request body must be a JSON object")
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        raise ApiError(422, "validation_error", "Invalid input", _details(exc)) from exc


def _details(exc: ValidationError) -> list[dict[str, str]]:
    return [{"field": ".".join(str(p) for p in e["loc"]), "message": e["msg"]} for e in exc.errors()]


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ApiError)
    def _api(err: ApiError):
        return _envelope(err.status, err.code, err.message, err.details)

    @app.errorhandler(HTTPException)
    def _http(err: HTTPException):
        code = (err.name or "error").lower().replace(" ", "_")
        return _envelope(err.code or 500, code, err.description or err.name)

    @app.errorhandler(Exception)
    def _unhandled(err: Exception):
        app.logger.exception("unhandled error")
        return _envelope(500, "internal_error", "Internal server error")
