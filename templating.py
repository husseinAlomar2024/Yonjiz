"""Shared Jinja environment and template filters."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from fastapi.templating import Jinja2Templates

from config import ADMIN_LIMIT, APP_NAME


BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def utc_iso(value: Optional[datetime]) -> str:
    if value is None:
        return ""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def utc_label(value: Optional[datetime], fmt: str = "%b %d, %H:%M UTC") -> str:
    if value is None:
        return ""
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value.strftime(fmt)


def priority_label(value: int) -> str:
    return {
        1: "Very low",
        2: "Low",
        3: "Medium",
        4: "High",
        5: "Critical",
    }.get(value, f"Priority {value}")


def priority_key(value: int) -> str:
    return {
        1: "very-low",
        2: "low",
        3: "medium",
        4: "high",
        5: "critical",
    }.get(value, "medium")


def compact_number(value: int) -> str:
    return f"{value:,}"


templates.env.filters["utc_iso"] = utc_iso
templates.env.filters["utc_label"] = utc_label
templates.env.filters["priority_label"] = priority_label
templates.env.filters["priority_key"] = priority_key
templates.env.filters["compact"] = compact_number
templates.env.globals.update(
    app_name=APP_NAME,
    admin_limit=ADMIN_LIMIT,
)


def flash_redirect_url(path: str, message: str, kind: str = "success") -> str:
    joiner = "&" if "?" in path else "?"
    return f"{path}{joiner}message={quote(message)}&kind={quote(kind)}"
