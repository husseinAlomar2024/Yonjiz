"""Application configuration.

Secrets are read from environment variables first.  For local development we
create stable, randomly generated secret files instead of committing a
hard-coded key.  Set SECRET_KEY and ADMIN_ACCESS_KEY in production.
"""

from __future__ import annotations

import os
import secrets
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dotenv is in requirements.txt
    load_dotenv = None


BASE_DIR = Path(__file__).resolve().parent

if load_dotenv is not None:
    load_dotenv(BASE_DIR / ".env")


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _secret(env_name: str, filename: str) -> str:
    """Use an env secret when supplied, otherwise persist a generated one."""

    env_value = os.getenv(env_name, "").strip()
    if env_value:
        return env_value

    path = BASE_DIR / filename
    if path.exists():
        stored = path.read_text(encoding="utf-8").strip()
        if stored:
            return stored

    generated = secrets.token_urlsafe(48)
    path.write_text(generated + "\n", encoding="utf-8")
    try:  # Best effort on Windows and POSIX; useful on shared hosts.
        path.chmod(0o600)
    except OSError:
        pass
    return generated


APP_NAME = os.getenv("APP_NAME", "Daymark")
SECRET_KEY = _secret("SECRET_KEY", ".secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))
COOKIE_SECURE = _env_bool("COOKIE_SECURE", False)

ADMIN_ACCESS_KEY = _secret("ADMIN_ACCESS_KEY", ".admin_access_key")
ADMIN_LIMIT = 3
DEVELOPER_EMAIL = (os.getenv("DEVELOPER_EMAIL", "").strip().lower() or None)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{(BASE_DIR / 'todo.db').as_posix()}",
)

DEFAULT_PRIORITY = 3
