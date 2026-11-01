# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files

repo = Path(SPECPATH).resolve()
assets = repo / "desktop" / "assets"
seed = repo / "seed" / "todo.db"
datas = [
    (str(assets), "desktop/assets"),
    (str(seed), "seed"),
]
datas += collect_data_files("spellchecker")

a = Analysis(
    ["desktop_app.py"],
    pathex=[str(repo)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "sqlalchemy.dialects.sqlite",
        "sqlalchemy.sql.default_comparator",
        "bcrypt",
        "jose",
        "dotenv",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["fastapi", "uvicorn", "starlette", "jinja2", "passlib", "pytest"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="YONJIZ",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(assets / "icon.ico"),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="YONJIZ",
)
