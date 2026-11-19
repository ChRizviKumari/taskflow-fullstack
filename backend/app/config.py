"""Application configuration."""
from __future__ import annotations

import os
from typing import Any


def default_config() -> dict[str, Any]:
    return {
        "SECRET_KEY": os.environ.get("TASKFLOW_SECRET", "dev-only-change-me"),
        "DATABASE": os.environ.get("TASKFLOW_DB", "taskflow.db"),
        "JWT_TTL_SECONDS": int(os.environ.get("TASKFLOW_JWT_TTL", "3600")),
        "PBKDF2_ITERATIONS": int(os.environ.get("TASKFLOW_PBKDF2_ITERATIONS", "200000")),
        "CORS_ORIGIN": os.environ.get("TASKFLOW_CORS_ORIGIN", "http://localhost:5173"),
    }
