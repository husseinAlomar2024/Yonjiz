"""Small HTTP helpers shared by routers."""

from __future__ import annotations

from urllib.parse import quote


def safe_next(value: str | None, default: str = "/todos") -> str:
    """Only allow same-site relative paths as post-login destinations."""

    if not value:
        return default
    value = value.strip()
    if not value.startswith("/") or value.startswith("//") or "\\" in value:
        return default
    if any(ord(char) < 32 for char in value):
        return default
    return value


def redirect_url(path: str, message: str | None = None, kind: str = "success") -> str:
    if not message:
        return path
    joiner = "&" if "?" in path else "?"
    return f"{path}{joiner}message={quote(message)}&kind={quote(kind)}"
