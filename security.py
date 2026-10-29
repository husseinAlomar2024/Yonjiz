"""Password hashing and JWT helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY


BCRYPT_MAX_BYTES = 72


class InvalidTokenError(Exception):
    pass


def hash_password(password: str) -> str:
    encoded = password.encode("utf-8")
    if len(encoded) > BCRYPT_MAX_BYTES:
        raise ValueError("Password is longer than 72 UTF-8 bytes.")
    return bcrypt.hashpw(encoded, bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            password.encode("utf-8")[:BCRYPT_MAX_BYTES],
            hashed_password.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False


def create_access_token(*, user_id: int, username: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "username": username,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise InvalidTokenError("Invalid or expired session.") from exc

    subject = payload.get("sub")
    if not subject:
        raise InvalidTokenError("Session is missing a subject.")
    try:
        user_id = int(subject)
    except (TypeError, ValueError) as exc:
        raise InvalidTokenError("Session subject is invalid.") from exc
    return {"user_id": user_id, "username": payload.get("username")}


def cookie_max_age() -> int:
    return ACCESS_TOKEN_EXPIRE_MINUTES * 60
