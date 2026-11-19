"""HS256 JWT and PBKDF2 password hashing built on the standard library."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any


class TokenError(Exception):
    """Raised when a token is malformed, forged or expired."""


def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def b64url_decode(text: str) -> bytes:
    padding = "=" * (-len(text) % 4)
    try:
        return base64.urlsafe_b64decode(text + padding)
    except (ValueError, TypeError) as exc:
        raise TokenError("invalid base64") from exc


def _sign(message: bytes, secret: str) -> str:
    return b64url_encode(hmac.new(secret.encode(), message, hashlib.sha256).digest())


def jwt_encode(payload: dict[str, Any], secret: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    head = b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    body = b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{head}.{body}"
    return f"{signing_input}.{_sign(signing_input.encode(), secret)}"


def jwt_decode(token: str, secret: str, now: float | None = None) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        raise TokenError("malformed token")
    head_b64, body_b64, sig = parts
    try:
        header = json.loads(b64url_decode(head_b64))
        payload = json.loads(b64url_decode(body_b64))
    except (ValueError, UnicodeDecodeError) as exc:
        raise TokenError("malformed token") from exc
    # Pin the algorithm: never trust the header to pick it ("alg: none" attack).
    if not isinstance(header, dict) or header.get("alg") != "HS256":
        raise TokenError("unsupported algorithm")
    expected = _sign(f"{head_b64}.{body_b64}".encode(), secret)
    if not hmac.compare_digest(expected, sig):
        raise TokenError("bad signature")
    if not isinstance(payload, dict):
        raise TokenError("malformed payload")
    exp = payload.get("exp")
    if not isinstance(exp, (int, float)) or (now if now is not None else time.time()) >= exp:
        raise TokenError("token expired")
    return payload


def issue_token(user_id: int, secret: str, ttl: int, now: float | None = None) -> str:
    issued = int(now if now is not None else time.time())
    return jwt_encode({"sub": user_id, "iat": issued, "exp": issued + ttl}, secret)


def hash_password(password: str, iterations: int) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, iters, salt_hex, digest_hex = stored.split("$")
        if scheme != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(iters))
    except ValueError:
        return False
    return hmac.compare_digest(digest.hex(), digest_hex)
