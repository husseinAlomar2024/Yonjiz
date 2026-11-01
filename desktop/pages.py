"""Login, workspace and admin pages for the native desktop app."""

from __future__ import annotations

import calendar as pycalendar
from datetime import datetime, timedelta
from typing import Callable, Optional

from PySide6.QtCore import QDate, Qt, QTime, Signal
from PySide6.QtGui import QColor, QTextCharFormat
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QCalendarWidget,
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from desktop import theme
from desktop.service import DesktopError, DesktopService
from desktop.widgets import (
    BrandWidget,
    ClockCard,
    ProgressRing,
    RegisterDialog,
    SeatCard,
    StatCard,
    TaskCard,
    TaskDialog,
    button,
    label,
    priority_name,
    repolish,
)


def clear_layout(layout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.hide()
            widget.deleteLater()
        child = item.layout()
        if child is not None:
            clear_layout(child)


def card() -> QFrame:
    frame = QFrame()
    frame.setObjectName("Card")
    return frame


def section_heading(text: str) -> QLabel:
    item = label(text, "SectionHeading")
    item.setStyleSheet(
        f"font-family: '{theme.DISPLAY}'; font-size: 34px; font-weight: 500;"
        f" color: {theme.INK}; letter-spacing: -0.8px;"
    )
    return item


def priority_colour(value: int) -> str:
    return {1: "#7d837f", 2: theme.FOREST, 3: "#48627f", 4: "#8f6212", 5: "#a14321"}.get(
        value, theme.MUTED
    )


class LoginPage(QWidget):
    logged_in = Signal(dict)

    def __init__(self, service: DesktopService, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.service = service
        self.setObjectName("LoginPage")
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        aside = QFrame()
        aside.setFixedWidth(560)
        aside.setStyleSheet(
            f"QFrame {{ background: {theme.FOREST_DEEP}; }}"
            "QLabel { background: transparent; }"
        )
        aside_layout = QVBoxLayout(aside)
        aside_layout.setContentsMargins(48, 42, 48, 40)
        aside_layout.setSpacing(0)
        aside_layout.addWidget(BrandWidget(light=True))
        aside_layout.addStretch(1)

        eyebrow = label("A QUIETER WORKSPACE", "Eyebrow")
        eyebrow.setStyleSheet(
            "color: rgba(255,253,246,0.55); font-size: 10px; letter-spacing: 1.6px;"
        )
        aside_layout.addWidget(eyebrow)
        hero = QLabel("The day is yours.")
        hero.setStyleSheet(
            f"font-family: '{theme.DISPLAY}'; font-size: 53px; color: #fffdf6;"
            " letter-spacing: -1.6px;"
        )
        aside_layout.addWidget(hero)
        hero2 = QLabel("Pick up a thread.")
        hero2.setStyleSheet(
            f"font-family: '{theme.DISPLAY}'; font-size: 53px; color: #e7a082;"
            " font-style: italic; letter-spacing: -1.6px;"
        )
        aside_layout.addWidget(hero2)
        copy = QLabel(
            "Your tasks, deadlines and calendar live on this computer.\n"
            "No internet, no cloud, no server."
        )
        copy.setWordWrap(True)
        copy.setStyleSheet(
            "color: rgba(255,253,246,0.58); font-size: 13px; line-height: 1.5;"
            " margin-top: 16px;"
        )
        aside_layout.addWidget(copy)
        aside_layout.addSpacing(28)

        feature_card = QFrame()
        feature_card.setObjectName("FeatureCard")
        feature_card.setStyleSheet(
            "QFrame#FeatureCard { background: rgba(255,253,246,0.055);"
            " border: 1px solid rgba(255,253,246,0.12); border-radius: 15px; }"
        )
        f_layout = QVBoxLayout(feature_card)
        f_layout.setContentsMargins(16, 13, 16, 13)
        for mark, title, detail in [
            ("◷", "A clock that stays present", "Analog warmth, digital precision."),
            ("▦", "A calendar with only your dates", "Quiet dots, not crowded grids."),
            ("♙", "One protected main admin", "Local accounts, clear hierarchy."),
        ]:
            row = QHBoxLayout()
            ico = QLabel(mark)
            ico.setFixedWidth(22)
            ico.setStyleSheet("color: #e7a082; font-size: 17px;")
            row.addWidget(ico)
            text = QVBoxLayout()
            text.setSpacing(0)
            t = QLabel(title)
            t.setStyleSheet("color: rgba(255,253,246,0.85); font-size: 12px; font-weight: 600;")
            d = QLabel(detail)
            d.setStyleSheet("color: rgba(255,253,246,0.38); font-size: 11px;")
            text.addWidget(t)
            text.addWidget(d)
            row.addLayout(text, 1)
            f_layout.addLayout(row)
        aside_layout.addWidget(feature_card)
        aside_layout.addStretch(2)
        foot = QLabel("Quiet by design. Built for the work that matters.")
        foot.setStyleSheet(
            f"font-family: '{theme.DISPLAY}'; font-style: italic;"
            " color: rgba(255,253,246,0.28); font-size: 11px;"
        )
        aside_layout.addWidget(foot)
        root.addWidget(aside)

        right = QWidget()
        right.setObjectName("LoginRight")
        right.setStyleSheet(f"#LoginRight {{ background: {theme.CANVAS}; }}")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(48, 40, 48, 40)
        right_layout.addStretch(1)
        login_card = QFrame()
        login_card.setObjectName("Card")
        login_card.setFixedWidth(480)
        card_layout = QVBoxLayout(login_card)
        card_layout.setContentsMargins(34, 32, 34, 28)
        card_layout.setSpacing(0)
        card_layout.addWidget(label("ACCOUNT ACCESS", "Eyebrow"))
        title = QLabel("Log in.")
        title.setStyleSheet(
            f"font-family: '{theme.DISPLAY}'; font-size: 48px; color: {theme.INK};"
            " letter-spacing: -1.5px; margin-top: 4px;"
        )
        card_layout.addWidget(title)
        sub = QLabel("Open your local workspace. Everything stays on this PC.")
        sub.setWordWrap(True)
        sub.setStyleSheet(f"color: {theme.MUTED}; font-size: 12px; margin-bottom: 16px;")
        card_layout.addWidget(sub)

        card_layout.addWidget(self._field_label("Username"))
        self.username = QLineEdit()
        self.username.setPlaceholderText("your_username")
        self.username.setMinimumHeight(46)
        card_layout.addWidget(self.username)
        card_layout.addSpacing(10)
        card_layout.addWidget(self._field_label("Password"))
        password_row = QHBoxLayout()
        password_row.setSpacing(6)
        self.password = QLineEdit()
        self.password.setPlaceholderText("Your password")
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setMinimumHeight(46)
        self.password.returnPressed.connect(self._submit)
        password_row.addWidget(self.password, 1)
        self.show_password = button("Show", "SecondaryButton")
        self.show_password.setCheckable(True)
        self.show_password.setFixedWidth(68)
        self.show_password.setMinimumHeight(46)
        self.show_password.setToolTip("Show or hide the password")
        self.show_password.toggled.connect(self._toggle_password)
        password_row.addWidget(self.show_password)
        card_layout.addLayout(password_row)

        self.error = QLabel("")
        self.error.setWordWrap(True)
        self.error.setStyleSheet(
            f"color: {theme.DANGER}; background: {theme.DANGER_SOFT};"
            " border-radius: 6px; padding: 7px 9px; font-size: 11px; margin-top: 10px;"
        )
        self.error.hide()
        card_layout.addWidget(self.error)
        card_layout.addSpacing(14)

        sign_in = button("Open my workspace  →", "PrimaryButton")
        sign_in.setMinimumHeight(52)
        sign_in.clicked.connect(self._submit)
        card_layout.addWidget(sign_in)
        card_layout.addSpacing(10)
        create_row = QHBoxLayout()
        create_row.addStretch(1)
        create = button("Create a local account", "TextButton")
        create.clicked.connect(self._register)
        create_row.addWidget(create)
        create_row.addStretch(1)
        card_layout.addLayout(create_row)
        card_layout.addSpacing(14)
        offline = QLabel("●  OFFLINE  ·  NO SERVER  ·  NO INTERNET")
        offline.setAlignment(Qt.AlignCenter)
        offline.setStyleSheet(
            f"color: {theme.MUTED_LIGHT}; font-size: 8px; letter-spacing: 0.7px;"
            f" border-top: 1px solid {theme.LINE}; padding-top: 13px;"
        )
        card_layout.addWidget(offline)

        right_layout.addWidget(login_card, 0, Qt.AlignHCenter)
        right_layout.addStretch(2)
        root.addWidget(right, 1)
        self.username.setFocus()

    @staticmethod
    def _field_label(text: str) -> QLabel:
        item = QLabel(text)
        item.setStyleSheet(
            f"color: {theme.INK_SOFT}; font-size: 11px; font-weight: 700;"
        )
        return item

    def reset(self) -> None:
        self.error.hide()
        self.password.clear()
        self.show_password.setChecked(False)
        self.password.setEchoMode(QLineEdit.Password)
        self.show_password.setText("Show")
        self.username.setFocus()

    def _toggle_password(self, shown: bool) -> None:
        self.password.setEchoMode(QLineEdit.Normal if shown else QLineEdit.Password)
        self.show_password.setText("Hide" if shown else "Show")

    def _submit(self) -> None:
        self.error.hide()
        try:
            snapshot = self.service.login(
                self.username.text(), self.password.text()
            )
        except Exception as exc:
            self.error.setText(str(exc))
            self.error.show()
            return
        self.password.clear()
        self.logged_in.emit(snapshot)

    def _register(self) -> None:
        dialog = RegisterDialog(self.service, self)
        dialog.registered.connect(self._registered)
        dialog.exec()

    def _registered(self, snapshot: dict) -> None:
        self.logged_in.emit(snapshot)


class WorkspacePage(QWidget):
    def __init__(
        self,
        service: DesktopService,
        notify: Callable[[str], None],
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.service = service
        self.notify = notify
        self.snapshot: dict = {}
        self.date_filter: Optional[QDate] = None
        self.status_filter = "all"
        self._marked_dates: list[QDate] = []
        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content = QWidget()
        scroll.setWidget(content)
        outer.addWidget(scroll)

        shell = QHBoxLayout(content)
        shell.setContentsMargins(26, 24, 26, 30)
        shell.setSpacing(20)
        shell.setAlignment(Qt.AlignTop)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(336)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(0, 0, 0, 0)
        side.setSpacing(13)
        self.clock = ClockCard()
        side.addWidget(self.clock)

        cal_card = card()
        cal_layout = QVBoxLayout(cal_card)
        cal_layout.setContentsMargins(16, 14, 16, 12)
        cal_layout.setSpacing(5)
        head = QHBoxLayout()
        head.addWidget(label("DEADLINE CALENDAR", "Eyebrow"))
        head.addStretch(1)
        self.today_button = button("Today", "TextButton")
        self.today_button.clicked.connect(self._select_today)
        head.addWidget(self.today_button)
        cal_layout.addLayout(head)
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(False)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.calendar.setHorizontalHeaderFormat(QCalendarWidget.ShortDayNames)
        self.calendar.setFirstDayOfWeek(Qt.Sunday)
        self.calendar.setMinimumHeight(260)
        self.calendar.setMaximumHeight(300)
        self.calendar.selectionChanged.connect(self._calendar_changed)
        cal_layout.addWidget(self.calendar)
        legend = QHBoxLayout()
        legend.addWidget(self._legend("● Deadline", theme.CLAY))
        legend.addWidget(self._legend("● Overdue", theme.DANGER))
        legend.addWidget(self._legend("● Done", theme.MUTED_LIGHT))
        legend.addStretch(1)
        self.clear_date_button = button("Clear date", "TextButton")
        self.clear_date_button.clicked.connect(self._clear_date)
        self.clear_date_button.hide()
        legend.addWidget(self.clear_date_button)
        cal_layout.addLayout(legend)
        side.addWidget(cal_card)

        prog = QFrame()
        prog.setObjectName("ProgressCard")
        p_layout = QHBoxLayout(prog)
        p_layout.setContentsMargins(15, 13, 15, 13)
        p_layout.setSpacing(12)
        self.ring = ProgressRing()
        p_layout.addWidget(self.ring)
        p_text = QVBoxLayout()
        p_text.setSpacing(1)
        p_text.addWidget(label("DAY PROGRESS", "Eyebrow"))
        self.progress_title = label("A fresh start")
        self.progress_title.setStyleSheet(
            f"font-size: 13px; font-weight: 700; color: {theme.INK};"
        )
        p_text.addWidget(self.progress_title)
        self.progress_detail = label("Add a task to begin.", "Muted")
        self.progress_detail.setWordWrap(True)
        p_text.addWidget(self.progress_detail)
        p_layout.addLayout(p_text, 1)
        side.addWidget(prog)
        side.addStretch(1)
        shell.addWidget(sidebar)

        main = QVBoxLayout()
        main.setSpacing(12)
        date = datetime.now().strftime("%A, %B %d, %Y").upper()
        self.date_label = label(date, "EyebrowClay")
        main.addWidget(self.date_label)
        greeting_row = QHBoxLayout()
        greeting = QVBoxLayout()
        greeting.setSpacing(3)
        self.heading = QLabel("Hello.")
        self.heading.setStyleSheet(
            f"font-family: '{theme.DISPLAY}'; font-size: 47px; color: {theme.INK};"
            " letter-spacing: -1.4px;"
        )
        greeting.addWidget(self.heading)
        self.lede = QLabel(
            "Here’s the shape of your day. Keep it light, or give something a deadline."
        )
        self.lede.setStyleSheet(f"color: {theme.MUTED}; font-size: 12px;")
        greeting.addWidget(self.lede)
        greeting_row.addLayout(greeting, 1)
        self.new_button = button("+  New task", "PrimaryButton")
        self.new_button.setMinimumHeight(41)
        self.new_button.clicked.connect(self.new_task)
        greeting_row.addWidget(self.new_button, 0, Qt.AlignBottom)
        main.addLayout(greeting_row)

        stats = QHBoxLayout()
        stats.setSpacing(8)
        self.stat_total = StatCard("All tasks", 0, "in your workspace")
        self.stat_open = StatCard("Open", 0, "still in motion", "open")
        self.stat_today = StatCard("Due today", 0, "on today’s list", "today")
        self.stat_overdue = StatCard("Overdue", 0, "needs a little care", "overdue")
        for stat in (self.stat_total, self.stat_open, self.stat_today, self.stat_overdue):
            stats.addWidget(stat)
        main.addLayout(stats)

        panel = card()
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(16, 14, 16, 14)
        panel_layout.setSpacing(9)
        head = QHBoxLayout()
        title_row = QHBoxLayout()
        title_row.setSpacing(7)
        tasks_heading = label("Your tasks", "CardHeading")
        title_row.addWidget(tasks_heading)
        self.count_label = label("0")
        self.count_label.setStyleSheet(
            f"background: {theme.PAPER_SOFT}; color: {theme.MUTED};"
            " border-radius: 8px; padding: 2px 7px; font-size: 11px; font-weight: 700;"
        )
        title_row.addWidget(self.count_label, 0, Qt.AlignVCenter)
        head.addLayout(title_row)
        head.addStretch(1)
        self.search = QLineEdit()
        self.search.setObjectName("SearchField")
        self.search.setPlaceholderText("⌕  Search tasks")
        self.search.setFixedWidth(190)
        self.search.textChanged.connect(self._render_tasks)
        head.addWidget(self.search)
        self.sort = QComboBox()
        self.sort.addItems(["Smart order", "By deadline", "By priority", "Newest first"])
        self.sort.setFixedWidth(130)
        self.sort.currentIndexChanged.connect(self._render_tasks)
        head.addWidget(self.sort)
        panel_layout.addLayout(head)

        filters = QHBoxLayout()
        self.filter_group = QButtonGroup(self)
        self.filter_group.setExclusive(True)
        for key, text in [
            ("all", "All"), ("open", "Open"), ("complete", "Done"), ("overdue", "Overdue")
        ]:
            b = button(text, "FilterButton")
            b.setCheckable(True)
            b.setProperty("filter", key)
            if key == "all":
                b.setChecked(True)
            b.clicked.connect(lambda checked, k=key: self._set_filter(k))
            self.filter_group.addButton(b)
            filters.addWidget(b)
        filters.addStretch(1)
        self.summary = label("", "Tiny")
        filters.addWidget(self.summary)
        panel_layout.addLayout(filters)

        self.active_date = label("", "Tiny")
        self.active_date.setStyleSheet(
            f"color: #7f5b1f; background: #fdf8ec; border: 1px solid {theme.GOLD_SOFT};"
            " border-radius: 7px; padding: 5px 8px; font-size: 11px;"
        )
        self.active_date.hide()
        panel_layout.addWidget(self.active_date)

        self.task_container = QWidget()
        self.task_layout = QVBoxLayout(self.task_container)
        self.task_layout.setContentsMargins(0, 0, 0, 0)
        self.task_layout.setSpacing(6)
        panel_layout.addWidget(self.task_container)
        main.addWidget(panel)
        self.footnote = label(
            "Tip: deadlines are optional. Turn one on only when a date matters.",
            "Tiny",
        )
        self.footnote.setAlignment(Qt.AlignCenter)
        main.addWidget(self.footnote)
        shell.addLayout(main, 1)
        self._select_today(initial=True)

    def _legend(self, text: str, colour: str) -> QLabel:
        item = label(text)
        item.setStyleSheet(f"color: {color_muted(colour)}; font-size: 10px;")
        return item

    def set_snapshot(self, snapshot: dict) -> None:
        self.snapshot = snapshot
        user = snapshot["user"]
        hour = datetime.now().hour
        greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
        self.heading.setText(f"{greeting}, {user['first_name']}.")
        self._render_all()

    def _select_today(self, initial: bool = False) -> None:
        today = QDate.currentDate()
        self.calendar.setSelectedDate(today)
        if initial:
            self.date_filter = None
            self.clear_date_button.hide()
            self.active_date.hide()
        else:
            self.date_filter = today
            self.clear_date_button.show()
            self.active_date.setText(f"Showing  {today.toString('dddd, MMM d')}")
            self.active_date.show()
        self._render_tasks()

    def _clear_date(self) -> None:
        self.date_filter = None
        self.clear_date_button.hide()
        self.active_date.hide()
        self._render_tasks()

    def _calendar_changed(self) -> None:
        if not self.snapshot:
            return
        selected = self.calendar.selectedDate()
        self.date_filter = selected
        self.clear_date_button.show()
        self.active_date.setText(f"Showing  {selected.toString('dddd, MMM d')}")
        self.active_date.show()
        self._render_tasks()

    def _set_filter(self, key: str) -> None:
        self.status_filter = key
        self._render_tasks()

    def _render_all(self) -> None:
        self._render_stats()
        self._render_calendar_marks()
        self._render_tasks()

    def _render_stats(self) -> None:
        tasks = self.snapshot.get("tasks", [])
        complete = sum(1 for task in tasks if task["complete"])
        now = datetime.now().astimezone()
        today_count = 0
        overdue = 0
        for task in tasks:
            if task["complete"] or not task.get("deadline"):
                continue
            dt = parse_deadline(task["deadline"])
            if dt is None:
                continue
            if dt.date() == now.date():
                today_count += 1
            if dt < now:
                overdue += 1
        self.stat_total.set_value(len(tasks))
        self.stat_open.set_value(len(tasks) - complete)
        self.stat_today.set_value(today_count)
        self.stat_overdue.set_value(overdue)
        pct = round(complete / len(tasks) * 100) if tasks else 0
        self.ring.set_value(pct)
        if not tasks:
            self.progress_title.setText("A fresh start")
            self.progress_detail.setText("Add a task to begin.")
        elif pct == 100:
            self.progress_title.setText("Everything, done.")
            self.progress_detail.setText("A clean sweep. Make some room.")
        elif pct >= 60:
            self.progress_title.setText("Well under way")
            self.progress_detail.setText(f"{complete} of {len(tasks)} tasks complete.")
        elif pct:
            self.progress_title.setText("Finding a rhythm")
            self.progress_detail.setText(f"{complete} of {len(tasks)} tasks complete.")
        else:
            self.progress_title.setText("Ready when you are")
            self.progress_detail.setText(f"{len(tasks)} tasks waiting.")

    def _render_calendar_marks(self) -> None:
        for date in self._marked_dates:
            self.calendar.setDateTextFormat(date, QTextCharFormat())
        self._marked_dates.clear()
        for task in self.snapshot.get("tasks", []):
            if not task.get("deadline"):
                continue
            dt = parse_deadline(task["deadline"])
            if dt is None:
                continue
            date = QDate(dt.year, dt.month, dt.day)
            if date in self._marked_dates:
                continue
            fmt = QTextCharFormat()
            if task["complete"]:
                fmt.setForeground(QColor(theme.MUTED_LIGHT))
            elif dt < datetime.now().astimezone():
                fmt.setBackground(QColor(theme.DANGER_SOFT))
                fmt.setForeground(QColor(theme.DANGER))
            else:
                fmt.setBackground(QColor(theme.CLAY_SOFT))
                fmt.setForeground(QColor("#9b3f21"))
            fmt.setFontWeight(700)
            self.calendar.setDateTextFormat(date, fmt)
            self._marked_dates.append(date)

    def _visible_tasks(self) -> list[dict]:
        tasks = list(self.snapshot.get("tasks", []))
        query = self.search.text().strip().lower()
        now = datetime.now().astimezone()
        result = []
        for task in tasks:
            if query and query not in (task["title"] + " " + task["description"]).lower():
                continue
            if self.status_filter == "open" and task["complete"]:
                continue
            if self.status_filter == "complete" and not task["complete"]:
                continue
            if self.status_filter == "overdue":
                dt = parse_deadline(task.get("deadline")) if task.get("deadline") else None
                if task["complete"] or dt is None or dt >= now:
                    continue
            if self.date_filter is not None:
                if not task.get("deadline"):
                    continue
                dt = parse_deadline(task["deadline"])
                if dt is None or QDate(dt.year, dt.month, dt.day) != self.date_filter:
                    continue
            result.append(task)

        mode = self.sort.currentIndex()
        if mode == 1:
            result.sort(key=lambda t: (t["complete"], t["deadline"] or "9999"))
        elif mode == 2:
            result.sort(key=lambda t: (t["complete"], -t["priority"], t["created_at"] or ""))
        elif mode == 3:
            result.sort(key=lambda t: (t["complete"], t["created_at"] or ""), reverse=True)
        else:
            result.sort(
                key=lambda t: (
                    t["complete"],
                    t["deadline"] is None,
                    t["deadline"] or "",
                    -t["priority"],
                    t["created_at"] or "",
                )
            )
        return result

    def _render_tasks(self) -> None:
        clear_layout(self.task_layout)
        all_tasks = self.snapshot.get("tasks", [])
        visible = self._visible_tasks()
        for task in visible:
            widget = TaskCard(task)
            widget.toggled.connect(self._toggle_task)
            widget.edit_requested.connect(self._edit_task)
            widget.delete_requested.connect(self._delete_task)
            self.task_layout.addWidget(widget)
        if not visible:
            empty = QWidget()
            box = QVBoxLayout(empty)
            box.setContentsMargins(0, 30, 0, 26)
            box.setSpacing(5)
            icon = QLabel("✦")
            icon.setAlignment(Qt.AlignCenter)
            icon.setStyleSheet(f"color: {theme.CLAY}; font-size: 28px;")
            box.addWidget(icon)
            head = QLabel("A clear page." if not all_tasks else "Nothing matches that view.")
            head.setAlignment(Qt.AlignCenter)
            head.setStyleSheet(
                f"font-family: '{theme.DISPLAY}'; font-size: 26px; color: {theme.INK};"
            )
            box.addWidget(head)
            text = QLabel(
                "Add the first thing you want to make room for. A deadline is optional."
                if not all_tasks
                else "Try a different filter or date."
            )
            text.setAlignment(Qt.AlignCenter)
            text.setWordWrap(True)
            text.setStyleSheet(f"color: {theme.MUTED}; font-size: 12px;")
            box.addWidget(text)
            if not all_tasks:
                add = button("Add your first task", "SecondaryButton")
                add.clicked.connect(self.new_task)
                box.addWidget(add, 0, Qt.AlignHCenter)
            self.task_layout.addWidget(empty)
        self.task_layout.addStretch(1)
        self.count_label.setText(str(len(visible)))
        self.summary.setText(
            f"{len(visible)} of {len(all_tasks)} shown"
            if visible != all_tasks
            else f"{len(all_tasks)} tasks"
        )

    def new_task(self) -> None:
        dialog = TaskDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            try:
                self.snapshot = self.service.create_task(dialog.payload())
                self._render_all()
                self.notify("Task added.")
            except Exception as exc:
                QMessageBox.warning(self, "YONJIZ", str(exc))

    def _edit_task(self, task: dict) -> None:
        dialog = TaskDialog(task, self)
        if dialog.exec() == QDialog.Accepted:
            try:
                self.snapshot = self.service.update_task(task["id"], dialog.payload())
                self._render_all()
                self.notify("Task updated.")
            except Exception as exc:
                QMessageBox.warning(self, "YONJIZ", str(exc))

    def _toggle_task(self, task_id: int) -> None:
        try:
            self.snapshot = self.service.toggle_task(task_id)
            self._render_all()
        except Exception as exc:
            QMessageBox.warning(self, "YONJIZ", str(exc))

    def _delete_task(self, task: dict) -> None:
        answer = QMessageBox.question(
            self,
            "Delete task",
            f'Delete “{task["title"]}”? This cannot be undone.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        try:
            self.snapshot = self.service.delete_task(task["id"])
            self._render_all()
            self.notify("Task deleted.")
        except Exception as exc:
            QMessageBox.warning(self, "YONJIZ", str(exc))


def color_muted(colour: str) -> str:
    return colour if colour != theme.CLAY else "#a14321"


def parse_deadline(raw: Optional[str]) -> Optional[datetime]:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone()
    except ValueError:
        return None


class AdminPage(QWidget):
    def __init__(
        self,
        service: DesktopService,
        notify: Callable[[str], None],
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.service = service
        self.notify = notify
        self.data: dict = {}
        self.current_user_id: Optional[int] = None
        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content = QWidget()
        scroll.setWidget(content)
        outer.addWidget(scroll)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 26, 30, 28)
        layout.setSpacing(12)

        eyebrow = label("CONTROL ROOM", "Eyebrow")
        layout.addWidget(eyebrow)
        heading = QLabel("The people and<br><i>the work.</i>")
        heading.setTextFormat(Qt.RichText)
        heading.setStyleSheet(
            f"font-family: '{theme.DISPLAY}'; font-size: 54px; color: {theme.INK};"
            " letter-spacing: -1.5px; line-height: 0.9;"
        )
        layout.addWidget(heading)
        self.lede = QLabel(
            "A compact view of every account and task. Three seats, one protected main admin."
        )
        self.lede.setStyleSheet(f"color: {theme.MUTED}; font-size: 12px;")
        layout.addWidget(self.lede)
        layout.addSpacing(4)

        self.seat_row = QHBoxLayout()
        self.seat_row.setSpacing(9)
        layout.addLayout(self.seat_row)

        self.kpi_row = QHBoxLayout()
        self.kpi_row.setSpacing(8)
        layout.addLayout(self.kpi_row)

        users_panel = card()
        up_layout = QVBoxLayout(users_panel)
        up_layout.setContentsMargins(16, 14, 16, 12)
        up_layout.setSpacing(8)
        up_head = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(0)
        title_box.addWidget(label("DIRECTORY", "Eyebrow"))
        title_box.addWidget(section_heading("People"))
        up_head.addLayout(title_box)
        up_head.addStretch(1)
        self.user_search = QLineEdit()
        self.user_search.setObjectName("SearchField")
        self.user_search.setPlaceholderText("⌕  Find a person")
        self.user_search.setFixedWidth(190)
        self.user_search.textChanged.connect(self._filter_users)
        up_head.addWidget(self.user_search)
        up_layout.addLayout(up_head)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["PERSON", "ACCESS", "STATUS", "TASKS", "JOINED", "ACTIONS"]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for col, width in [(1, 150), (2, 100), (3, 70), (4, 115), (5, 265)]:
            self.table.horizontalHeader().setSectionResizeMode(col, QHeaderView.Fixed)
            self.table.setColumnWidth(col, width)
        self.table.setMinimumHeight(180)
        self.table.setMaximumHeight(290)
        up_layout.addWidget(self.table)
        foot = QLabel(
            "The main admin is permanently protected. Other admins can hire or demote admins, but never the main admin."
        )
        foot.setWordWrap(True)
        foot.setStyleSheet(
            f"color: {theme.MUTED}; background: {theme.PAPER_SOFT};"
            f" border-top: 1px solid {theme.LINE}; padding: 8px 2px; font-size: 10px;"
        )
        up_layout.addWidget(foot)
        layout.addWidget(users_panel)

        lower = QHBoxLayout()
        lower.setSpacing(10)
        self.recent_panel = card()
        rp = QVBoxLayout(self.recent_panel)
        rp.setContentsMargins(15, 12, 15, 12)
        rp.setSpacing(4)
        rp.addWidget(label("ACROSS ACCOUNTS", "Eyebrow"))
        rp.addWidget(section_heading("Recent tasks"))
        self.recent_box = QVBoxLayout()
        rp.addLayout(self.recent_box)
        lower.addWidget(self.recent_panel, 1)

        self.activity_panel = card()
        ap = QVBoxLayout(self.activity_panel)
        ap.setContentsMargins(15, 12, 15, 12)
        ap.setSpacing(4)
        ap.addWidget(label("ACCOUNTABILITY", "Eyebrow"))
        ap.addWidget(section_heading("Recent activity"))
        self.activity_box = QVBoxLayout()
        ap.addLayout(self.activity_box)
        lower.addWidget(self.activity_panel, 1)

        safety = QFrame()
        safety.setObjectName("SafetyCard")
        safety.setStyleSheet(
            f"QFrame#SafetyCard {{ background: {theme.FOREST_DEEP}; border-radius: 16px; }}"
            "QFrame#SafetyCard QLabel { background: transparent; }"
        )
        sp = QVBoxLayout(safety)
        sp.setContentsMargins(18, 16, 18, 16)
        sp.setSpacing(5)
        shield = QLabel("◈")
        shield.setStyleSheet(f"color: {theme.CLAY}; font-size: 22px;")
        sp.addWidget(shield)
        why = QLabel("Why three?")
        why.setStyleSheet(
            f"font-family: '{theme.DISPLAY}'; font-size: 24px; color: #fffdf6;"
        )
        sp.addWidget(why)
        why_text = QLabel(
            "Seat 1 is reserved for the protected main admin. Seats 2 and 3 can be "
            "hired and released — never the main account."
        )
        why_text.setWordWrap(True)
        why_text.setStyleSheet("color: rgba(255,253,246,0.55); font-size: 11px;")
        sp.addWidget(why_text)
        sp.addStretch(1)
        lower.addWidget(safety, 1)
        layout.addLayout(lower)
        layout.addStretch(1)

    def refresh(self, data: dict, current_user_id: Optional[int] = None) -> None:
        self.data = data
        if current_user_id is not None:
            self.current_user_id = current_user_id
        self._render_seats()
        self._render_kpis()
        self._render_table()
        self._render_recent()
        self._render_activity()

    def _render_seats(self) -> None:
        clear_layout(self.seat_row)
        for seat in self.data.get("seats", []):
            widget = SeatCard(seat)
            widget.action.connect(self._seat_action)
            self.seat_row.addWidget(widget, 1)

    def _render_kpis(self) -> None:
        clear_layout(self.kpi_row)
        items = [
            ("PEOPLE", self.data.get("active_users", 0), "active accounts"),
            ("ALL TASKS", self.data.get("total_todos", 0), "across every account"),
            ("COMPLETED", self.data.get("completed_todos", 0), "finished tasks"),
            ("OVERDUE", self.data.get("overdue_todos", 0), "past their deadline"),
        ]
        for title, value, foot in items:
            widget = StatCard(title, value, foot, "overdue" if title == "OVERDUE" else "")
            self.kpi_row.addWidget(widget, 1)

    def _render_table(self) -> None:
        users = self.data.get("users", [])
        self.table.setRowCount(0)
        for person in users:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setRowHeight(row, 62)
            self.table.setItem(row, 0, QTableWidgetItem(""))
            self.table.setCellWidget(row, 0, self._person_widget(person))
            access = QLabel(
                "MAIN ADMIN · 1" if person["is_primary_admin"]
                else f"ADMIN · {person['admin_slot']}" if person["role"] == "admin"
                else "USER"
            )
            access.setObjectName("RoleBadge")
            access.setProperty(
                "role", "primary" if person["is_primary_admin"] else "admin" if person["role"] == "admin" else "user"
            )
            access.setAlignment(Qt.AlignCenter)
            self.table.setCellWidget(row, 1, self._center(access))
            status = QLabel("●  Active" if person["is_active"] else "●  Inactive")
            status.setStyleSheet(
                f"color: {theme.SUCCESS if person['is_active'] else theme.MUTED_LIGHT};"
                " font-size: 11px;"
            )
            self.table.setCellWidget(row, 2, self._center(status))
            tasks = QLabel(f"{person['completed_count']}/{person['task_count']}")
            tasks.setStyleSheet(f"color: {theme.INK_SOFT}; font-size: 11px; font-weight: 600;")
            self.table.setCellWidget(row, 3, self._center(tasks))
            joined = QLabel((person.get("created_at") or "")[:10])
            joined.setStyleSheet(f"color: {theme.MUTED}; font-size: 10px;")
            self.table.setCellWidget(row, 4, self._center(joined))
            self.table.setCellWidget(row, 5, self._actions_widget(person))
        self._filter_users(self.user_search.text())

    @staticmethod
    def _center(widget: QWidget) -> QWidget:
        wrap = QWidget()
        layout = QHBoxLayout(wrap)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.addWidget(widget, 0, Qt.AlignCenter)
        return wrap

    def _person_widget(self, person: dict) -> QWidget:
        wrap = QWidget()
        layout = QHBoxLayout(wrap)
        layout.setContentsMargins(3, 2, 3, 2)
        layout.setSpacing(7)
        avatar = QLabel(person["initials"])
        avatar.setFixedSize(30, 30)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(
            f"background: {'#9b3f21' if person['is_primary_admin'] else theme.CLAY};"
            "color: #fffdf6; border-radius: 15px; font-size: 10px; font-weight: 700;"
        )
        layout.addWidget(avatar)
        copy = QVBoxLayout()
        copy.setSpacing(0)
        name = QLabel(
            person["full_name"]
            + ("  YOU" if person["id"] == self.current_user_id else "")
        )
        name.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {theme.INK};")
        copy.addWidget(name)
        username = QLabel(f"@{person['username']}  ·  {person['email']}")
        username.setStyleSheet(f"color: {theme.MUTED}; font-size: 10px;")
        copy.addWidget(username)
        layout.addLayout(copy, 1)
        return wrap

    def _actions_widget(self, person: dict) -> QWidget:
        wrap = QWidget()
        layout = QHBoxLayout(wrap)
        layout.setContentsMargins(3, 2, 3, 2)
        layout.setSpacing(3)
        if person["is_primary_admin"]:
            lock = QLabel("◈  Untouchable")
            lock.setObjectName("ProtectedLabel")
            layout.addWidget(lock)
        elif person["id"] == self.current_user_id:
            layout.addWidget(label("You", "Tiny"))
        else:
            if person["role"] == "user":
                promote = button("Make admin", "TableAction")
                promote.setEnabled(bool(self.data.get("free_slots")) and person["is_active"])
                promote.clicked.connect(lambda _, uid=person["id"]: self._role(uid, "promote"))
                layout.addWidget(promote)
                toggle = button("Deactivate" if person["is_active"] else "Activate", "TableAction")
                toggle.clicked.connect(
                    lambda _, uid=person["id"], active=person["is_active"]: self._status(uid, not active)
                )
                layout.addWidget(toggle)
            else:
                demote = button("Demote", "TableAction")
                demote.clicked.connect(lambda _, uid=person["id"]: self._role(uid, "demote"))
                layout.addWidget(demote)
            delete = button("×", "TableDanger")
            delete.setToolTip("Delete account")
            delete.clicked.connect(lambda _, uid=person["id"], name=person["username"]: self._delete_user(uid, name))
            layout.addWidget(delete)
        layout.addStretch(1)
        return wrap

    def _filter_users(self, query: str) -> None:
        q = query.strip().lower()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            person = self.data.get("users", [])[row] if row < len(self.data.get("users", [])) else {}
            hay = f"{person.get('full_name','')} {person.get('username','')} {person.get('email','')}".lower()
            self.table.setRowHidden(row, bool(q) and q not in hay)

    def _render_recent(self) -> None:
        clear_layout(self.recent_box)
        tasks = self.data.get("recent_tasks", [])
        if not tasks:
            self.recent_box.addWidget(label("No tasks have been added yet.", "Muted"))
        for task in tasks:
            row = QWidget()
            layout = QHBoxLayout(row)
            layout.setContentsMargins(0, 4, 0, 4)
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {priority_colour(task['priority'])}; font-size: 8px;")
            layout.addWidget(dot)
            text = QVBoxLayout()
            text.setSpacing(0)
            title = QLabel(task["title"])
            title.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {theme.INK};")
            text.addWidget(title)
            meta = QLabel(f"@{task['owner']}  ·  {'Done' if task['complete'] else 'No deadline' if not task.get('deadline') else task['deadline'][:10]}")
            meta.setStyleSheet(f"color: {theme.MUTED}; font-size: 10px;")
            text.addWidget(meta)
            layout.addLayout(text, 1)
            delete = button("×", "TableDanger")
            delete.clicked.connect(lambda _, tid=task["id"]: self._delete_todo(tid))
            layout.addWidget(delete)
            self.recent_box.addWidget(row)
        self.recent_box.addStretch(1)

    def _render_activity(self) -> None:
        clear_layout(self.activity_box)
        labels = {
            "admin.promote": "Admin promoted",
            "admin.demote": "Admin demoted",
            "admin.developer_access": "Developer access",
            "admin.cli": "Admin created via CLI",
            "admin.primary_created": "Main admin established",
            "user.activate": "Account activated",
            "user.deactivate": "Account deactivated",
            "user.delete": "Account deleted",
            "todo.delete": "Task deleted",
        }
        for entry in self.data.get("audit", []):
            item = QWidget()
            layout = QVBoxLayout(item)
            layout.setContentsMargins(0, 3, 0, 3)
            layout.setSpacing(0)
            action = QLabel(labels.get(entry["action"], entry["action"]))
            action.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {theme.INK};")
            layout.addWidget(action)
            if entry.get("target_label"):
                target = QLabel(entry["target_label"])
                target.setStyleSheet(f"color: {theme.MUTED}; font-size: 10px;")
                layout.addWidget(target)
            meta = QLabel(f"{entry['actor']}  ·  {entry['created_at'][:16].replace('T', ' ')} UTC")
            meta.setStyleSheet(f"color: {theme.MUTED_LIGHT}; font-size: 8px;")
            layout.addWidget(meta)
            self.activity_box.addWidget(item)
        if not self.data.get("audit"):
            self.activity_box.addWidget(label("Admin actions will appear here.", "Muted"))
        self.activity_box.addStretch(1)

    def _seat_action(self, user_id: int, action: str) -> None:
        self._role(user_id, action)

    def _role(self, user_id: int, action: str) -> None:
        try:
            self.data = self.service.change_role(user_id, action)
            self.refresh(self.data)
            self.notify("Admin role updated.")
        except Exception as exc:
            QMessageBox.warning(self, "YONJIZ", str(exc))

    def _status(self, user_id: int, active: bool) -> None:
        try:
            self.data = self.service.change_status(user_id, active)
            self.refresh(self.data)
            self.notify("Account updated.")
        except Exception as exc:
            QMessageBox.warning(self, "YONJIZ", str(exc))

    def _delete_user(self, user_id: int, username: str) -> None:
        answer = QMessageBox.question(
            self,
            "Delete account",
            f"Permanently delete @{username} and all of their tasks?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        try:
            self.data = self.service.delete_user(user_id)
            self.refresh(self.data)
            self.notify("Account deleted.")
        except Exception as exc:
            QMessageBox.warning(self, "YONJIZ", str(exc))

    def _delete_todo(self, todo_id: int) -> None:
        try:
            self.data = self.service.delete_admin_todo(todo_id)
            self.refresh(self.data)
            self.notify("Task deleted.")
        except Exception as exc:
            QMessageBox.warning(self, "YONJIZ", str(exc))
