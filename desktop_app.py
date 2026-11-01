"""YONJIZ desktop entry point.

This is a native Qt application. It talks to SQLite directly; it does not
start FastAPI, Uvicorn, a browser, a localhost server or any network service.
"""

from __future__ import annotations

import os
import shutil
import sys
import traceback
from pathlib import Path

from desktop.paths import data_dir, icon_path, resource_dir


def _bootstrap_paths() -> Path:
    data = data_dir()
    data.mkdir(parents=True, exist_ok=True)
    db_path = data / "todo.db"
    frozen = getattr(sys, "frozen", False)
    if frozen and not db_path.exists():
        seed = resource_dir() / "seed" / "todo.db"
        if seed.exists():
            shutil.copy2(seed, db_path)
        else:
            db_path.touch()
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
    os.environ["YONJIZ_DATA_DIR"] = str(data)
    os.environ["SECRET_KEY"] = "desktop-local-value-not-used-for-network"
    os.environ["ADMIN_ACCESS_KEY"] = "desktop-local-value-not-used-for-network"
    return data


DATA_DIR = _bootstrap_paths()

from database import init_db  # noqa: E402
from desktop.main_window import MainWindow  # noqa: E402
from desktop.service import DesktopService  # noqa: E402
from desktop import theme  # noqa: E402

from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtGui import QFont, QIcon  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402


def _install_exception_log() -> None:
    log_path = DATA_DIR / "desktop-error.log"

    def handler(exc_type, exc_value, exc_tb):
        text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        try:
            log_path.write_text(text, encoding="utf-8")
        except OSError:
            pass
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = handler


def main() -> int:
    init_db()
    _install_exception_log()

    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "YONJIZ.Desktop.1"
            )
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setApplicationName("YONJIZ")
    app.setApplicationDisplayName("YONJIZ · ينجز")
    app.setOrganizationName("YONJIZ")
    app.setStyle("Fusion")
    app.setWindowIcon(QIcon(str(icon_path())))
    app.setFont(QFont(theme.SANS, 12))
    app.setStyleSheet(theme.QSS)

    service = DesktopService()
    window = MainWindow(service)
    window.show()
    if "--smoke-test" in sys.argv:
        def finish_smoke() -> None:
            try:
                window.grab().save(str(DATA_DIR / "desktop-smoke.png"))
                (DATA_DIR / "desktop-smoke.log").write_text(
                    f"visible={window.isVisible()}\n"
                    f"title={window.windowTitle()}\n"
                    f"size={window.width()}x{window.height()}\n",
                    encoding="utf-8",
                )
            finally:
                app.quit()

        QTimer.singleShot(1500, finish_smoke)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
