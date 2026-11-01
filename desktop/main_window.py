"""Main native window and navigation."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from desktop import theme
from desktop.pages import AdminPage, LoginPage, WorkspacePage
from desktop.paths import icon_path
from desktop.service import DesktopService
from desktop.widgets import BrandWidget, button, label


class MainWindow(QMainWindow):
    def __init__(self, service: DesktopService):
        super().__init__()
        self.service = service
        self.snapshot: dict = {}
        self.setWindowTitle("YONJIZ · ينجز")
        self.setWindowIcon(QIcon(str(icon_path())))
        self.resize(1440, 940)
        self.setMinimumSize(1160, 780)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.topbar = QFrame()
        self.topbar.setObjectName("TopBar")
        self.topbar.setFixedHeight(74)
        top = QHBoxLayout(self.topbar)
        top.setContentsMargins(22, 8, 22, 8)
        top.setSpacing(14)
        top.addWidget(BrandWidget(compact=True))
        top.addSpacing(20)
        self.nav_workspace = button("Workspace", "NavButton")
        self.nav_workspace.setCheckable(True)
        self.nav_workspace.setChecked(True)
        self.nav_workspace.clicked.connect(self.show_workspace)
        top.addWidget(self.nav_workspace)
        self.nav_admin = button("Admin", "NavButton")
        self.nav_admin.setCheckable(True)
        self.nav_admin.clicked.connect(self.show_admin)
        top.addWidget(self.nav_admin)
        top.addStretch(1)

        self.user_name = QLabel("")
        self.user_name.setStyleSheet(
            f"color: {theme.INK}; font-size: 12px; font-weight: 700;"
        )
        top.addWidget(self.user_name, 0, Qt.AlignRight)
        self.user_role = QLabel("")
        self.user_role.setStyleSheet(f"color: {theme.MUTED}; font-size: 10px;")
        top.addWidget(self.user_role, 0, Qt.AlignRight)
        self.logout_button = button("Log out", "GhostButton")
        self.logout_button.clicked.connect(self.logout)
        top.addWidget(self.logout_button)
        self.topbar.hide()
        root.addWidget(self.topbar)

        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)

        self.login_page = LoginPage(service)
        self.login_page.logged_in.connect(self._on_login)
        self.workspace_page = WorkspacePage(service, self.notify)
        self.admin_page = AdminPage(service, self.notify)
        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.workspace_page)
        self.stack.addWidget(self.admin_page)
        self.stack.setCurrentWidget(self.login_page)
        self.statusBar().showMessage("YONJIZ desktop · local only")

        self._shortcuts()

    def _shortcuts(self) -> None:
        for sequence, callback in [
            ("Ctrl+N", self._new_task),
            ("Ctrl+K", self._focus_search),
            ("Ctrl+1", self.show_workspace),
            ("Ctrl+2", self.show_admin),
            ("Ctrl+L", self.logout),
        ]:
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.activated.connect(callback)

    def _new_task(self) -> None:
        if self.stack.currentWidget() is self.workspace_page:
            self.workspace_page.new_task()

    def _focus_search(self) -> None:
        if self.stack.currentWidget() is self.workspace_page:
            self.workspace_page.search.setFocus()
            self.workspace_page.search.selectAll()

    def _on_login(self, snapshot: dict) -> None:
        self.snapshot = snapshot
        self.workspace_page.set_snapshot(snapshot)
        user = snapshot["user"]
        self.user_name.setText(user["full_name"])
        if user["is_primary_admin"]:
            role = "Main admin"
        elif user["role"] == "admin":
            role = f"Admin · seat {user['admin_slot']}"
        else:
            role = "Member"
        self.user_role.setText(role)
        is_admin = user["role"] == "admin"
        self.nav_admin.setVisible(is_admin)
        self.topbar.show()
        self.show_workspace()
        self.statusBar().showMessage("Signed in locally. No internet connection required.", 4500)

    def show_workspace(self) -> None:
        if not self.snapshot:
            return
        self.nav_workspace.setChecked(True)
        self.nav_admin.setChecked(False)
        self.stack.setCurrentWidget(self.workspace_page)
        self.setWindowTitle("Workspace · YONJIZ · ينجز")

    def show_admin(self) -> None:
        if not self.snapshot or self.snapshot["user"]["role"] != "admin":
            return
        try:
            data = self.service.admin_snapshot()
        except Exception as exc:
            self.notify(str(exc), error=True)
            return
        self.admin_page.refresh(data, self.snapshot["user"]["id"])
        self.nav_workspace.setChecked(False)
        self.nav_admin.setChecked(True)
        self.stack.setCurrentWidget(self.admin_page)
        self.setWindowTitle("Admin console · YONJIZ · ينجز")

    def logout(self) -> None:
        if self.stack.currentWidget() is self.login_page:
            return
        self.service.logout()
        self.snapshot = {}
        self.topbar.hide()
        self.stack.setCurrentWidget(self.login_page)
        self.login_page.reset()
        self.setWindowTitle("YONJIZ · ينجز")
        self.statusBar().showMessage("Signed out.", 2500)

    def notify(self, message: str, error: bool = False) -> None:
        self.statusBar().showMessage(message, 5000 if not error else 7000)

