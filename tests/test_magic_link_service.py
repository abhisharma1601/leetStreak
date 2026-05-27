import hashlib
import time

import jwt
import pytest

from app.services import magic_link_service
from app.config import settings


def test_generate_and_verify_roundtrip():
    token = magic_link_service.generate(user_id=1, assignment_id=42, action="DONE")
    payload = magic_link_service.verify(token)

    assert payload["sub"] == 1
    assert payload["aid"] == 42
    assert payload["act"] == "DONE"


def test_generate_skip_action():
    token = magic_link_service.generate(user_id=1, assignment_id=7, action="SKIP")
    payload = magic_link_service.verify(token)
    assert payload["act"] == "SKIP"


def test_verify_raises_on_tampered_signature():
    token = magic_link_service.generate(user_id=1, assignment_id=1, action="DONE")
    tampered = token[:-4] + "XXXX"
    with pytest.raises(jwt.exceptions.InvalidSignatureError):
        magic_link_service.verify(tampered)


def test_verify_raises_on_expired_token():
    payload = {
        "sub": 1,
        "aid": 1,
        "act": "DONE",
        "iat": int(time.time()) - 3600,
        "exp": int(time.time()) - 1,  # already expired
    }
    expired_token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    with pytest.raises(jwt.exceptions.ExpiredSignatureError):
        magic_link_service.verify(expired_token)


def test_verify_raises_on_wrong_secret():
    payload = {
        "sub": 1,
        "aid": 1,
        "act": "DONE",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(payload, "wrong-secret", algorithm="HS256")
    with pytest.raises(jwt.exceptions.InvalidSignatureError):
        magic_link_service.verify(token)


def test_token_hash_is_sha256_hex():
    token = "some.jwt.token"
    result = magic_link_service.token_hash(token)
    expected = hashlib.sha256(token.encode()).hexdigest()
    assert result == expected


def test_token_hash_different_tokens_differ():
    h1 = magic_link_service.token_hash("token.a.one")
    h2 = magic_link_service.token_hash("token.b.two")
    assert h1 != h2


def test_exp_is_in_the_future():
    token = magic_link_service.generate(user_id=1, assignment_id=1, action="DONE")
    payload = magic_link_service.verify(token)
    assert payload["exp"] > int(time.time())
