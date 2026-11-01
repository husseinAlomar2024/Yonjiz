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

from desktop import i18n, theme
from desktop.pages import AdminPage, LoginPage, WorkspacePage
from desktop.paths import icon_path
from desktop.service import DesktopService
from desktop.widgets import BrandWidget, button, label


class MainWindow(QMainWindow):
    def __init__(self, service: DesktopService):
        super().__init__()
        self.service = service
        self.snapshot: dict = {}
        self.setWindowTitle(i18n.tr("YONJIZ · ينجز"))
        self.setWindowIcon(QIcon(str(icon_path())))
        self.resize(1440, 940)
        self.setMinimumSize(1160, 780)
        i18n.apply_direction()
        self._build_ui()
        self._shortcuts()

    def _build_ui(self) -> None:
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

        self.language_button = button(i18n.switch_label(), "GhostButton", translate=False)
        self.language_button.setToolTip("Switch language / تغيير اللغة")
        self.language_button.clicked.connect(self.toggle_language)
        top.addWidget(self.language_button)
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

        self.login_page = LoginPage(self.service)
        self.login_page.logged_in.connect(self._on_login)
        self.login_page.language_requested.connect(self.toggle_language)
        self.workspace_page = WorkspacePage(self.service, self.notify)
        self.admin_page = AdminPage(self.service, self.notify)
        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.workspace_page)
        self.stack.addWidget(self.admin_page)
        self.stack.setCurrentWidget(self.login_page)
        self.statusBar().showMessage(i18n.tr("YONJIZ desktop · local only"))

    def toggle_language(self) -> None:
        was_admin = bool(
            self.snapshot and self.stack.currentWidget() is self.admin_page
        )
        i18n.set_language("ar" if i18n.language() == "en" else "en")
        i18n.apply_direction()
        old = self.centralWidget()
        self._build_ui()
        if old is not None:
            old.hide()
            old.deleteLater()
        if self.snapshot:
            self._on_login(self.snapshot)
            if was_admin:
                self.show_admin()
        else:
            self.setWindowTitle(i18n.tr("YONJIZ · ينجز"))

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
            role = i18n.tr("Main admin")
        elif user["role"] == "admin":
            role = i18n.tr("Admin · seat {n}").format(n=user["admin_slot"])
        else:
            role = i18n.tr("Member")
        self.user_role.setText(role)
        is_admin = user["role"] == "admin"
        self.nav_admin.setVisible(is_admin)
        self.topbar.show()
        self.show_workspace()
        self.statusBar().showMessage(
            i18n.tr("Signed in locally. No internet connection required."), 4500
        )

    def show_workspace(self) -> None:
        if not self.snapshot:
            return
        self.nav_workspace.setChecked(True)
        self.nav_admin.setChecked(False)
        self.stack.setCurrentWidget(self.workspace_page)
        self.setWindowTitle(i18n.tr("Workspace · YONJIZ · ينجز"))

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
        self.setWindowTitle(i18n.tr("Admin console · YONJIZ · ينجز"))

    def logout(self) -> None:
        if self.stack.currentWidget() is self.login_page:
            return
        self.service.logout()
        self.snapshot = {}
        self.topbar.hide()
        self.stack.setCurrentWidget(self.login_page)
        self.login_page.reset()
        self.setWindowTitle(i18n.tr("YONJIZ · ينجز"))
        self.statusBar().showMessage(i18n.tr("Signed out."), 2500)

    def notify(self, message: str, error: bool = False) -> None:
        self.statusBar().showMessage(message, 5000 if not error else 7000)

