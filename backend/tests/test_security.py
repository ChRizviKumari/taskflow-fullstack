import time

import pytest

from app.security import (TokenError, b64url_encode, hash_password, issue_token, jwt_decode,
                          jwt_encode, verify_password)

SECRET = "s3cret"


def test_jwt_roundtrip():
    token = issue_token(7, SECRET, 60)
    assert jwt_decode(token, SECRET)["sub"] == 7


def test_jwt_rejects_wrong_secret():
    with pytest.raises(TokenError):
        jwt_decode(issue_token(1, SECRET, 60), "other")


def test_jwt_rejects_expired():
    token = issue_token(1, SECRET, 10, now=time.time() - 100)
    with pytest.raises(TokenError, match="expired"):
        jwt_decode(token, SECRET)


def test_jwt_rejects_tampered_payload():
    head, _, sig = issue_token(1, SECRET, 60).split(".")
    forged = b64url_encode(b'{"sub":2,"exp":9999999999}')
    with pytest.raises(TokenError):
        jwt_decode(f"{head}.{forged}.{sig}", SECRET)


def test_jwt_rejects_alg_none():
    head = b64url_encode(b'{"alg":"none","typ":"JWT"}')
    body = b64url_encode(b'{"sub":1,"exp":9999999999}')
    with pytest.raises(TokenError, match="algorithm"):
        jwt_decode(f"{head}.{body}.", SECRET)


@pytest.mark.parametrize("bad", ["", "a.b", "a.b.c.d", "!!.!!.!!"])
def test_jwt_rejects_malformed(bad):
    with pytest.raises(TokenError):
        jwt_decode(bad, SECRET)


def test_jwt_known_structure():
    token = jwt_encode({"sub": 1, "exp": 1}, SECRET)
    assert token.count(".") == 2


def test_password_hash_and_verify():
    stored = hash_password("hunter2hunter2", 1000)
    assert stored.startswith("pbkdf2_sha256$1000$")
    assert verify_password("hunter2hunter2", stored)
    assert not verify_password("wrong", stored)
    assert hash_password("x" * 8, 1000) != hash_password("x" * 8, 1000)  # unique salts


def test_verify_password_handles_garbage():
    assert not verify_password("a", "not-a-hash")
