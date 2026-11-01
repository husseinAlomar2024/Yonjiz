"""Reusable native widgets for the YONJIZ desktop app."""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Optional

from PySide6.QtCore import QDateTime, QPointF, QRectF, QSize, Qt, QTime, QTimer, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QIcon,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from desktop import theme
from desktop.paths import brand_mark_path, icon_path


def repolish(widget: QWidget) -> None:
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


def label(text: str = "", name: str = "", parent: Optional[QWidget] = None) -> QLabel:
    item = QLabel(text, parent)
    if name:
        item.setObjectName(name)
    item.setWordWrap(False)
    return item


def button(text: str, name: str = "GhostButton", parent: Optional[QWidget] = None) -> QPushButton:
    item = QPushButton(text, parent)
    item.setObjectName(name)
    item.setCursor(Qt.PointingHandCursor)
    return item


def priority_name(value: int) -> str:
    return {1: "VERY LOW", 2: "LOW", 3: "MEDIUM", 4: "HIGH", 5: "CRITICAL"}.get(
        value, "MEDIUM"
    )


def parse_utc(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone()


class BrandWidget(QWidget):
    def __init__(
        self,
        compact: bool = False,
        light: bool = False,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        mark = QLabel()
        mark.setFixedSize(36 if not compact else 32, 36 if not compact else 32)
        mark.setStyleSheet(
            f"background: {'rgba(255,253,246,0.10)' if light else theme.FOREST};"
            f" border-radius: {10 if compact else 11}px;"
            + (" border: 1px solid rgba(255,253,246,0.22);" if light else "")
        )
        icon = QIcon(str(brand_mark_path()))
        mark.setPixmap(icon.pixmap(22 if compact else 25, 22 if compact else 25))
        mark.setAlignment(Qt.AlignCenter)
        layout.addWidget(mark)

        copy = QVBoxLayout()
        copy.setContentsMargins(0, 0, 0, 0)
        copy.setSpacing(0)
        name = label("YONJIZ.", "BrandName")
        name.setStyleSheet(
            f"font-family: '{theme.DISPLAY}'; font-size: {21 if compact else 23}px;"
            f" font-weight: 600; color: {'#fffdf6' if light else theme.INK};"
            " letter-spacing: -0.8px;"
        )
        arabic = label("ينجز", "BrandArabic")
        arabic.setStyleSheet(
            f"font-size: 14px; font-weight: 700;"
            f" color: {'rgba(255,253,246,0.65)' if light else theme.MUTED};"
        )
        copy.addWidget(name)
        copy.addWidget(arabic)
        layout.addLayout(copy)
        layout.addStretch(1)


class AnalogClock(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedSize(150, 150)
        self._now = datetime.now()

    def tick(self, now: datetime) -> None:
        self._now = now
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        side = min(self.width(), self.height()) - 8
        rect = QRectF((self.width() - side) / 2, (self.height() - side) / 2, side, side)
        painter.setPen(QPen(QColor(255, 253, 246, 52), 1))
        painter.setBrush(QColor(8, 34, 26, 72))
        painter.drawEllipse(rect)

        center = rect.center()
        radius = side / 2
        painter.setPen(QPen(QColor(255, 253, 246, 58), 1))
        for i in range(60):
            angle = math.radians(i * 6 - 90)
            outer = radius - 8
            inner = radius - (13 if i % 5 == 0 else 10)
            start = QPointF(
                center.x() + math.cos(angle) * inner,
                center.y() + math.sin(angle) * inner,
            )
            end = QPointF(
                center.x() + math.cos(angle) * outer,
                center.y() + math.sin(angle) * outer,
            )
            painter.drawLine(start, end)

        hour = self._now.hour % 12 + self._now.minute / 60
        minute = self._now.minute + self._now.second / 60
        second = self._now.second
        self._hand(painter, center, hour * 30, radius * 0.25, QColor("#fff8eb"), 3)
        self._hand(painter, center, minute * 6, radius * 0.36, QColor(255, 248, 235, 210), 2)
        self._hand(painter, center, second * 6, radius * 0.42, QColor(theme.CLAY), 1)
        painter.setPen(QPen(QColor(theme.FOREST_DEEP), 2))
        painter.setBrush(QColor(theme.CLAY))
        painter.drawEllipse(center, 4.5, 4.5)

    def _hand(
        self,
        painter: QPainter,
        center: QPointF,
        degrees: float,
        length: float,
        color: QColor,
        width: int,
    ) -> None:
        angle = math.radians(degrees - 90)
        end = QPointF(
            center.x() + math.cos(angle) * length,
            center.y() + math.sin(angle) * length,
        )
        painter.setPen(QPen(color, width, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(center, end)


class ClockCard(QFrame):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("ClockCard")
        self.setFixedWidth(336)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(2)

        top = QHBoxLayout()
        left = QVBoxLayout()
        left.setSpacing(1)
        eyebrow = label("LOCAL TIME", "Eyebrow")
        eyebrow.setStyleSheet(
            f"color: rgba(255,253,246,0.58); font-size: 10px; letter-spacing: 1.4px;"
        )
        left.addWidget(eyebrow)
        self.zone = label("", "Tiny")
        self.zone.setStyleSheet("color: rgba(255,253,246,0.42); font-size: 11px;")
        left.addWidget(self.zone)
        top.addLayout(left)
        top.addStretch(1)
        live = label("●  LIVE")
        live.setStyleSheet(
            f"color: rgba(255,253,246,0.62); font-size: 10px; font-weight: 700;"
            " border: 1px solid rgba(255,253,246,0.16); border-radius: 9px; padding: 3px 7px;"
        )
        top.addWidget(live, 0, Qt.AlignTop)
        layout.addLayout(top)

        self.analog = AnalogClock()
        layout.addWidget(self.analog, 0, Qt.AlignHCenter)

        self.time = QLabel("--:--")
        self.time.setAlignment(Qt.AlignCenter)
        self.time.setStyleSheet(
            f"font-family: '{theme.DISPLAY}'; font-size: 46px; font-weight: 500;"
            " color: #fffdf6; letter-spacing: -2px;"
        )
        layout.addWidget(self.time)

        self.date = QLabel("")
        self.date.setAlignment(Qt.AlignCenter)
        self.date.setStyleSheet(
            "color: rgba(255,253,246,0.55); font-size: 12px;"
        )
        layout.addWidget(self.date)

        try:
            zone = datetime.now().astimezone().tzinfo
            self.zone.setText(str(zone))
        except Exception:
            self.zone.setText("Local time")

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000)
        self._tick()

    def _tick(self) -> None:
        now = datetime.now()
        self.time.setText(now.strftime("%I:%M").lstrip("0") + f"  {now.strftime('%p')}")
        self.date.setText(now.strftime("%A, %B %d, %Y"))
        self.analog.tick(now)


class ProgressRing(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedSize(66, 66)
        self.value = 0

    def set_value(self, value: int) -> None:
        self.value = max(0, min(100, int(value)))
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(5, 5, self.width() - 10, self.height() - 10)
        painter.setPen(QPen(QColor(theme.LINE), 5))
        painter.drawEllipse(rect)
        painter.setPen(QPen(QColor(theme.FOREST), 5, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(rect, 90 * 16, -int(360 * 16 * self.value / 100))
        painter.setPen(QColor(theme.INK))
        painter.setFont(QFont(theme.DISPLAY, 9))
        painter.drawText(rect, Qt.AlignCenter, f"{self.value}%")


class StatCard(QFrame):
    def __init__(self, title: str, value: int, foot: str, accent: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("StatCard")
        self.setProperty("accent", accent)
        self.setFixedHeight(96)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(13, 10, 13, 9)
        layout.setSpacing(0)
        self.title = label(title.upper(), "StatLabel")
        self.value = label(str(value), "StatValue")
        self.foot = label(foot, "StatFoot")
        layout.addWidget(self.title)
        layout.addWidget(self.value)
        layout.addWidget(self.foot)

    def set_value(self, value: int) -> None:
        self.value.setText(str(value))


class TaskCard(QFrame):
    toggled = Signal(int)
    edit_requested = Signal(dict)
    delete_requested = Signal(dict)

    def __init__(self, task: dict, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.task = task
        self.setObjectName("TaskCard")
        self.setProperty("complete", task["complete"])
        self.setMinimumHeight(78)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 9, 9, 9)
        layout.setSpacing(9)

        self.check = QPushButton("✓")
        self.check.setObjectName("CheckButton")
        self.check.setFixedSize(21, 21)
        self.check.setCursor(Qt.PointingHandCursor)
        self.check.setProperty("checked", task["complete"])
        self.check.setToolTip("Mark as not done" if task["complete"] else "Mark as done")
        self.check.clicked.connect(lambda: self.toggled.emit(task["id"]))
        layout.addWidget(self.check, 0, Qt.AlignTop)

        body = QVBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(2)

        title_row = QHBoxLayout()
        title_row.setSpacing(7)
        title = label(task["title"], "TaskTitle")
        title.setWordWrap(True)
        title.setProperty("complete", task["complete"])
        title_row.addWidget(title, 1)
        chip = label(priority_name(task["priority"]), "PriorityChip")
        chip.setProperty("priority", task["priority"])
        title_row.addWidget(chip, 0, Qt.AlignTop)
        body.addLayout(title_row)

        if task.get("description"):
            desc = label(task["description"], "TaskDescription")
            desc.setWordWrap(True)
            desc.setMaximumHeight(30)
            body.addWidget(desc)

        meta = QHBoxLayout()
        meta.setSpacing(6)
        deadline = self._deadline_data(task)
        if deadline:
            date_label = label(f"◷ {deadline['text']}")
            date_label.setStyleSheet(
                f"color: {theme.MUTED_LIGHT}; font-size: 11px;"
            )
            meta.addWidget(date_label)
            if deadline["state"] != "none":
                badge = label(deadline["state"].upper(), "DeadlineBadge")
                badge.setProperty("state", deadline["state"])
                meta.addWidget(badge)
        else:
            no_deadline = label("No deadline")
            no_deadline.setStyleSheet(
                f"color: {theme.MUTED_LIGHT}; font-size: 11px; font-style: italic;"
            )
            meta.addWidget(no_deadline)
        meta.addStretch(1)
        body.addLayout(meta)
        layout.addLayout(body, 1)

        actions = QVBoxLayout()
        actions.setSpacing(2)
        edit = button("Edit", "TableAction")
        edit.setFixedSize(58, 27)
        edit.setToolTip("Edit task")
        edit.clicked.connect(lambda: self.edit_requested.emit(task))
        actions.addWidget(edit)
        delete = button("Delete", "TableDangerText")
        delete.setFixedSize(58, 27)
        delete.setToolTip("Delete task")
        delete.clicked.connect(lambda: self.delete_requested.emit(task))
        actions.addWidget(delete)
        action_widget = QWidget()
        action_widget.setLayout(actions)
        layout.addWidget(action_widget, 0, Qt.AlignTop)

    def _deadline_data(self, task: dict) -> Optional[dict]:
        raw = task.get("deadline")
        if not raw:
            return None
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone()
        except ValueError:
            return None
        now = datetime.now(dt.tzinfo)
        time_text = dt.strftime("%I:%M %p").lstrip("0")
        if dt.date() == now.date():
            text = f"Today, {time_text}"
        elif dt.date() == (now + timedelta(days=1)).date():
            text = f"Tomorrow, {time_text}"
        else:
            text = dt.strftime("%b %d, %I:%M %p").replace(" 0", " ")
        if task["complete"]:
            state = "done"
        elif dt < now:
            state = "overdue"
        elif dt.date() == now.date():
            state = "today"
        elif dt - now <= timedelta(hours=72):
            state = "soon"
        else:
            state = "none"
        return {"text": text, "state": state}


class SeatCard(QFrame):
    action = Signal(int, str)

    def __init__(self, seat: dict, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("SeatCard")
        primary = seat.get("primary", False)
        self.setProperty("primary", primary)
        self.setProperty("open", not seat.get("occupied", False))
        self.setMinimumHeight(160)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 11)
        layout.setSpacing(4)

        top = QHBoxLayout()
        num = label(f"Seat {seat['slot']:02d}")
        num.setStyleSheet(
            f"font-family: '{theme.DISPLAY}'; font-style: italic; font-size: 12px;"
            f" color: {theme.CLAY if primary else theme.MUTED_LIGHT};"
        )
        top.addWidget(num)
        top.addStretch(1)
        if primary:
            status = label("MAIN ADMIN", "SeatBadge")
            status.setProperty("primary", True)
        elif seat.get("occupied"):
            status = label("OCCUPIED", "SeatBadge")
        else:
            status = label("AVAILABLE", "SeatBadge")
            status.setProperty("open", True)
        top.addWidget(status)
        layout.addLayout(top)

        if seat.get("occupied"):
            user = seat["user"]
            detail = QHBoxLayout()
            avatar = QLabel(user["initials"])
            avatar.setFixedSize(38, 38)
            avatar.setAlignment(Qt.AlignCenter)
            avatar.setStyleSheet(
                "background: #9b3f21;" if user["is_primary_admin"] else "background: #c46642;"
            )
            avatar.setStyleSheet(
                f"background: {'#9b3f21' if user['is_primary_admin'] else theme.CLAY};"
                f"color: #fffdf6; border-radius: 19px; font-size: 12px; font-weight: 700;"
            )
            detail.addWidget(avatar)
            copy = QVBoxLayout()
            copy.setSpacing(0)
            name = label(user["full_name"])
            name.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {theme.INK};")
            copy.addWidget(name)
            username = label(f"@{user['username']}")
            username.setStyleSheet(f"color: {theme.MUTED}; font-size: 11px;")
            copy.addWidget(username)
            detail.addLayout(copy)
            detail.addStretch(1)
            layout.addLayout(detail)
            layout.addStretch(1)
            foot = QHBoxLayout()
            since = label(
                "Protected main account"
                if user["is_primary_admin"]
                else f"Since {(user.get('created_at') or '')[:7]}"
            )
            since.setStyleSheet(f"color: {theme.MUTED_LIGHT}; font-size: 10px;")
            foot.addWidget(since)
            foot.addStretch(1)
            if user["is_primary_admin"]:
                protected = label("🔒 PROTECTED")
                protected.setStyleSheet(
                    f"color: #9b3f21; background: {theme.CLAY_SOFT}; border-radius: 8px;"
                    " padding: 2px 7px; font-size: 8px; font-weight: 700;"
                )
                foot.addWidget(protected)
            elif seat["slot"] != 1:
                demote = button("Demote", "SeatAction")
                demote.clicked.connect(
                    lambda _, uid=user["id"]: self.action.emit(uid, "demote")
                )
                foot.addWidget(demote)
            layout.addLayout(foot)
        else:
            layout.addStretch(1)
            open_title = label("An open seat")
            open_title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {theme.INK};")
            layout.addWidget(open_title)
            hint = label("Promote a member from the directory below.")
            hint.setStyleSheet(f"color: {theme.MUTED}; font-size: 11px;")
            layout.addWidget(hint)
            layout.addStretch(1)
            slot = label(f"SLOT {seat['slot']}")
            slot.setStyleSheet(f"color: {theme.MUTED_LIGHT}; font-size: 10px;")
            layout.addWidget(slot, 0, Qt.AlignRight)


class TaskDialog(QDialog):
    def __init__(self, task: Optional[dict] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.task = task or {}
        self.setWindowTitle("Edit task" if task else "New task")
        self.setModal(True)
        self.setMinimumWidth(570)
        self.setStyleSheet(f"QDialog {{ background: {theme.PAPER}; }}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 22)
        layout.setSpacing(11)

        eyebrow = label("A GENTLE EDIT" if task else "A NEW INTENTION", "Eyebrow")
        layout.addWidget(eyebrow)
        heading = label("Edit task" if task else "Add a task", "CardHeading")
        heading.setStyleSheet(
            f"font-family: '{theme.DISPLAY}'; font-size: 32px; color: {theme.INK};"
        )
        layout.addWidget(heading)

        layout.addWidget(self._field_label("Task title"))
        self.title = QLineEdit(self.task.get("title", ""))
        self.title.setPlaceholderText("What needs doing?")
        self.title.setMaxLength(120)
        layout.addWidget(self.title)

        layout.addWidget(self._field_label("Notes  ·  optional"))
        self.description = QTextEdit(self.task.get("description", ""))
        self.description.setPlaceholderText("A little context, if it helps.")
        self.description.setFixedHeight(70)
        layout.addWidget(self.description)

        row = QHBoxLayout()
        row.setSpacing(12)
        prio_col = QVBoxLayout()
        prio_col.setSpacing(5)
        prio_col.addWidget(self._field_label("Priority"))
        self.priority = QComboBox()
        for value, name in [
            (1, "Very low"), (2, "Low"), (3, "Medium"), (4, "High"), (5, "Critical")
        ]:
            self.priority.addItem(name, value)
        current = int(self.task.get("priority", 3))
        self.priority.setCurrentIndex(max(0, min(4, current - 1)))
        prio_col.addWidget(self.priority)
        row.addLayout(prio_col, 1)

        deadline_col = QVBoxLayout()
        deadline_col.setSpacing(5)
        deadline_head = QHBoxLayout()
        deadline_head.addWidget(self._field_label("Deadline"))
        deadline_head.addStretch(1)
        self.deadline_toggle = QCheckBox("Set a deadline")
        deadline_head.addWidget(self.deadline_toggle)
        deadline_col.addLayout(deadline_head)
        self.deadline = QDateTimeEdit()
        self.deadline.setCalendarPopup(True)
        self.deadline.setDisplayFormat("MMM d, yyyy  h:mm AP")
        self.deadline.setMinimumDateTime(QDateTime.currentDateTime().addYears(-2))
        initial = QDateTime.currentDateTime().addDays(1)
        initial.setTime(QTime(17, 0))
        self.deadline.setDateTime(initial)
        self.deadline.setEnabled(False)
        self.deadline_toggle.toggled.connect(self._toggle_deadline)
        deadline_col.addWidget(self.deadline)
        row.addLayout(deadline_col, 1)
        layout.addLayout(row)

        if self.task.get("deadline"):
            try:
                parsed = datetime.fromisoformat(
                    self.task["deadline"].replace("Z", "+00:00")
                ).astimezone()
                self.deadline.setDateTime(
                    QDateTime(parsed.year, parsed.month, parsed.day, parsed.hour, parsed.minute)
                )
                self.deadline_toggle.setChecked(True)
            except ValueError:
                pass

        self.error = QLabel("")
        self.error.setStyleSheet(
            f"color: {theme.DANGER}; background: {theme.DANGER_SOFT};"
            " border-radius: 6px; padding: 6px 8px; font-size: 12px;"
        )
        self.error.hide()
        layout.addWidget(self.error)

        actions = QHBoxLayout()
        actions.addStretch(1)
        cancel = button("Cancel", "GhostButton")
        cancel.clicked.connect(self.reject)
        actions.addWidget(cancel)
        save = button("Save changes" if task else "Add task", "PrimaryButton")
        save.clicked.connect(self._validate)
        actions.addWidget(save)
        layout.addLayout(actions)
        self.title.setFocus()

    @staticmethod
    def _field_label(text: str) -> QLabel:
        item = QLabel(text)
        item.setStyleSheet(
            f"color: {theme.INK_SOFT}; font-size: 11px; font-weight: 700;"
        )
        return item

    def _toggle_deadline(self, checked: bool) -> None:
        self.deadline.setEnabled(checked)
        if checked:
            self.deadline.setFocus()

    def _validate(self) -> None:
        if not self.title.text().strip():
            self._show_error("Give this task a title.")
            return
        self.accept()

    def _show_error(self, message: str) -> None:
        self.error.setText(message)
        self.error.show()

    def payload(self) -> dict:
        deadline = None
        if self.deadline_toggle.isChecked():
            dt = self.deadline.dateTime().toPython()
            if dt.tzinfo is None:
                dt = dt.astimezone()
            deadline = dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        return {
            "title": self.title.text().strip(),
            "description": self.description.toPlainText().strip(),
            "priority": int(self.priority.currentData()),
            "deadline": deadline,
        }


class RegisterDialog(QDialog):
    registered = Signal(dict)

    def __init__(self, service, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.service = service
        self.setWindowTitle("Create local account")
        self.setModal(True)
        self.setMinimumWidth(480)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 22)
        layout.setSpacing(10)
        title = label("Create a local account", "CardHeading")
        title.setStyleSheet(f"font-family: '{theme.DISPLAY}'; font-size: 29px;")
        layout.addWidget(title)
        layout.addWidget(label("Regular account. The main admin can grant admin access.", "Muted"))
        for attr, placeholder in [
            ("full_name", "Full name"),
            ("username", "Username"),
            ("email", "Email"),
            ("password", "Password (8+ characters)"),
        ]:
            field = QLineEdit()
            field.setPlaceholderText(placeholder)
            field.setMinimumHeight(42)
            if attr == "password":
                field.setEchoMode(QLineEdit.Password)
                setattr(self, attr, field)
                row = QHBoxLayout()
                row.setSpacing(6)
                row.addWidget(field, 1)
                self.register_show_password = button("Show", "SecondaryButton")
                self.register_show_password.setCheckable(True)
                self.register_show_password.setFixedWidth(68)
                self.register_show_password.setMinimumHeight(42)
                self.register_show_password.setToolTip("Show or hide the password")
                self.register_show_password.toggled.connect(self._toggle_password)
                row.addWidget(self.register_show_password)
                layout.addLayout(row)
            else:
                setattr(self, attr, field)
                layout.addWidget(field)
        self.error = label("")
        self.error.setStyleSheet(f"color: {theme.DANGER}; font-size: 11px;")
        self.error.setWordWrap(True)
        layout.addWidget(self.error)
        actions = QHBoxLayout()
        actions.addStretch(1)
        cancel = button("Cancel", "GhostButton")
        cancel.clicked.connect(self.reject)
        actions.addWidget(cancel)
        create = button("Create account", "PrimaryButton")
        create.clicked.connect(self._create)
        actions.addWidget(create)
        layout.addLayout(actions)

    def _toggle_password(self, shown: bool) -> None:
        self.password.setEchoMode(QLineEdit.Normal if shown else QLineEdit.Password)
        self.register_show_password.setText("Hide" if shown else "Show")

    def _create(self) -> None:
        try:
            snapshot = self.service.create_account(
                self.username.text(),
                self.password.text(),
                self.full_name.text(),
                self.email.text(),
            )
        except Exception as exc:
            self.error.setText(str(exc))
            return
        self.registered.emit(snapshot)
        self.accept()
