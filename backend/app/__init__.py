"""TaskFlow application factory."""
from __future__ import annotations

from typing import Any

from flask import Flask, Response, jsonify, request

from . import db
from .config import default_config
from .errors import register_error_handlers


def create_app(config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(default_config())
    if config:
        app.config.update(config)
    app.json.sort_keys = False

    db.init_app(app)
    register_error_handlers(app)

    from .routes import auth, boards, columns, tasks

    for module in (auth, boards, columns, tasks):
        app.register_blueprint(module.bp)

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    @app.after_request
    def cors(resp: Response) -> Response:
        origin = app.config["CORS_ORIGIN"]
        if origin and request.headers.get("Origin") == origin:
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
            resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, DELETE, OPTIONS"
            resp.headers["Vary"] = "Origin"
        return resp

    return app
