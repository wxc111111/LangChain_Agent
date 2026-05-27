import pytest
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token


def test_hash_and_verify_password():
    plain = "admin123"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed) is True
    assert verify_password("wrong", hashed) is False


def test_create_and_decode_access_token():
    data = {"sub": "1", "username": "admin", "role": "admin"}
    token = create_access_token(data)
    payload = decode_token(token)
    assert payload["sub"] == "1"
    assert payload["username"] == "admin"
    assert payload["role"] == "admin"


def test_create_and_decode_refresh_token():
    data = {"sub": "2", "username": "user1", "role": "user"}
    token = create_refresh_token(data)
    payload = decode_token(token)
    assert payload["sub"] == "2"
    assert payload["type"] == "refresh"


def test_decode_invalid_token():
    with pytest.raises(Exception):
        decode_token("invalid.token.here")
