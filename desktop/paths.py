"""Resource and writable-data paths for dev and PyInstaller builds."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def resource_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parent.parent


def data_dir() -> Path:
    override = os.getenv("YONJIZ_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    if getattr(sys, "frozen", False):
        base = Path(os.getenv("LOCALAPPDATA", Path.home()))
        return base / "YONJIZ"
    return Path(__file__).resolve().parent.parent


def asset_path(name: str) -> Path:
    return resource_dir() / "desktop" / "assets" / name


def icon_path() -> Path:
    ico = resource_dir() / "desktop" / "assets" / "icon.ico"
    if ico.exists():
        return ico
    return asset_path("icon.png")


def brand_mark_path() -> Path:
    mark = resource_dir() / "desktop" / "assets" / "mark.png"
    if mark.exists():
        return mark
    return icon_path()
