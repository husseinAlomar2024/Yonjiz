"""Colours, fonts and Qt stylesheet for YONJIZ desktop."""

from __future__ import annotations

FOREST = "#174b3b"
FOREST_DEEP = "#10392d"
FOREST_LIGHT = "#256553"
FOREST_WASH = "#e7efe9"
CLAY = "#c46642"
CLAY_SOFT = "#f9e8df"
CANVAS = "#f4f1ea"
PAPER = "#fffdf8"
PAPER_SOFT = "#faf7f0"
INK = "#18231f"
INK_SOFT = "#33413b"
MUTED = "#747f79"
MUTED_LIGHT = "#98a19c"
LINE = "#e5dfd3"
LINE_STRONG = "#d7cec0"
GOLD = "#b9832c"
GOLD_SOFT = "#fbf1d9"
DANGER = "#ae443d"
DANGER_SOFT = "#fae9e7"
SUCCESS = "#24704f"
SUCCESS_SOFT = "#e6f1eb"

SANS = "Segoe UI"
DISPLAY = "Palatino Linotype"
MONO = "Cascadia Code"


QSS = f"""
* {{
    font-family: "{SANS}";
    color: {INK_SOFT};
    outline: none;
}}
QMainWindow, QWidget {{
    background: {CANVAS};
}}
QLabel {{
    background: transparent;
}}
QFrame#Card, QFrame#TaskCard, QFrame#SeatCard, QFrame#StatCard,
QFrame#Panel, QFrame#ProgressCard {{
    background: {PAPER};
    border: 1px solid {LINE};
    border-radius: 18px;
}}
QFrame#TaskCard {{
    background: {PAPER_SOFT};
    border-radius: 12px;
}}
QFrame#TaskCard:hover {{
    background: {PAPER};
    border-color: {LINE_STRONG};
}}
QFrame#TaskCard[complete="true"] {{
    background: #f7f5ef;
}}
QFrame#ClockCard {{
    background: {FOREST_DEEP};
    border: 1px solid {FOREST_DEEP};
    border-radius: 20px;
}}
QFrame#Sidebar {{
    background: transparent;
    border: none;
}}
QFrame#TopBar {{
    background: {PAPER};
    border: none;
    border-bottom: 1px solid {LINE};
}}
QLabel#BrandName {{
    font-family: "{DISPLAY}";
    font-size: 23px;
    font-weight: 600;
    color: {INK};
    letter-spacing: -0.8px;
}}
QLabel#BrandArabic {{
    font-size: 13px;
    font-weight: 700;
    color: {MUTED};
}}
QLabel#DisplayHeading {{
    font-family: "{DISPLAY}";
    font-size: 42px;
    font-weight: 500;
    color: {INK};
    letter-spacing: -1.4px;
}}
QLabel#AdminHeading {{
    font-family: "{DISPLAY}";
    font-size: 46px;
    font-weight: 500;
    color: {INK};
    letter-spacing: -1.6px;
}}
QLabel#CardHeading {{
    font-family: "{DISPLAY}";
    font-size: 24px;
    font-weight: 600;
    color: {INK};
    letter-spacing: -0.6px;
}}
QLabel#SectionHeading {{
    font-family: "{DISPLAY}";
    font-size: 28px;
    font-weight: 500;
    color: {INK};
    letter-spacing: -0.8px;
}}
QLabel#Eyebrow {{
    font-size: 9px;
    font-weight: 700;
    color: {MUTED};
    letter-spacing: 1.6px;
    text-transform: uppercase;
}}
QLabel#EyebrowClay {{
    font-size: 9px;
    font-weight: 700;
    color: {CLAY};
    letter-spacing: 1.6px;
    text-transform: uppercase;
}}
QLabel#Muted {{
    color: {MUTED};
    font-size: 11px;
}}
QLabel#Tiny {{
    color: {MUTED_LIGHT};
    font-size: 9px;
}}
QLabel#TaskTitle {{
    font-size: 13px;
    font-weight: 650;
    color: {INK};
}}
QLabel#TaskTitle[complete="true"] {{
    color: {MUTED};
    text-decoration: line-through;
}}
QLabel#TaskDescription {{
    color: {MUTED};
    font-size: 10px;
}}
QLabel#PriorityChip {{
    border-radius: 8px;
    padding: 2px 7px;
    font-size: 8px;
    font-weight: 700;
    letter-spacing: 0.4px;
}}
QLabel#PriorityChip[priority="1"] {{ background: #f0eee9; color: #7d837f; }}
QLabel#PriorityChip[priority="2"] {{ background: {FOREST_WASH}; color: {FOREST}; }}
QLabel#PriorityChip[priority="3"] {{ background: #edf1f7; color: #48627f; }}
QLabel#PriorityChip[priority="4"] {{ background: {GOLD_SOFT}; color: #8f6212; }}
QLabel#PriorityChip[priority="5"] {{ background: {CLAY_SOFT}; color: #a14321; }}
QLabel#DeadlineBadge {{
    border-radius: 8px;
    padding: 2px 6px;
    font-size: 8px;
    font-weight: 700;
}}
QLabel#DeadlineBadge[state="overdue"] {{ background: {DANGER_SOFT}; color: {DANGER}; }}
QLabel#DeadlineBadge[state="today"] {{ background: {GOLD_SOFT}; color: #8a5b0e; }}
QLabel#DeadlineBadge[state="soon"] {{ background: {FOREST_WASH}; color: {FOREST}; }}
QLabel#DeadlineBadge[state="done"] {{ background: {SUCCESS_SOFT}; color: {SUCCESS}; }}
QLabel#DeadlineBadge[state="none"] {{ background: transparent; color: {MUTED_LIGHT}; padding-left: 0; }}

QPushButton {{
    border: none;
    border-radius: 10px;
    padding: 9px 15px;
    font-size: 11px;
    font-weight: 650;
    background: transparent;
}}
QPushButton#PrimaryButton {{
    background: {FOREST};
    color: #fffdf6;
    padding: 12px 22px;
    border-radius: 22px;
}}
QPushButton#PrimaryButton:hover {{ background: {FOREST_DEEP}; }}
QPushButton#PrimaryButton:pressed {{ background: #0a2b22; }}
QPushButton#SecondaryButton {{
    background: {PAPER};
    border: 1px solid {LINE_STRONG};
    color: {INK_SOFT};
    border-radius: 18px;
    padding: 9px 16px;
}}
QPushButton#SecondaryButton:hover {{
    border-color: {FOREST};
    color: {FOREST};
}}
QPushButton#GhostButton {{
    background: transparent;
    color: {MUTED};
    border-radius: 16px;
}}
QPushButton#GhostButton:hover {{
    background: {PAPER_SOFT};
    color: {INK};
}}
QPushButton#TextButton {{
    background: transparent;
    color: {FOREST};
    padding: 3px 4px;
    font-size: 10px;
}}
QPushButton#TextButton:hover {{ text-decoration: underline; }}
QPushButton#DangerTextButton {{
    background: transparent;
    color: {DANGER};
    padding: 3px 4px;
    font-size: 10px;
}}
QPushButton#DangerTextButton:hover {{ text-decoration: underline; }}
QPushButton#NavButton {{
    background: transparent;
    color: {MUTED};
    border-radius: 15px;
    padding: 8px 14px;
    font-size: 11px;
}}
QPushButton#NavButton:hover {{ color: {INK}; background: {PAPER_SOFT}; }}
QPushButton#NavButton:checked {{
    color: {FOREST};
    background: {FOREST_WASH};
    font-weight: 700;
}}
QPushButton#FilterButton {{
    background: transparent;
    color: {MUTED};
    border-radius: 12px;
    padding: 6px 12px;
    font-size: 10px;
}}
QPushButton#FilterButton:hover {{ color: {INK}; }}
QPushButton#FilterButton:checked {{
    background: {PAPER};
    color: {INK};
    border: 1px solid {LINE};
}}
QPushButton#CircleButton {{
    background: transparent;
    border: 1px solid {LINE_STRONG};
    border-radius: 12px;
    color: {MUTED};
    font-size: 15px;
    padding: 0;
}}
QPushButton#CircleButton:hover {{
    border-color: {FOREST};
    color: {FOREST};
    background: {FOREST_WASH};
}}
QPushButton#CheckButton {{
    background: {PAPER};
    border: 1px solid {LINE_STRONG};
    border-radius: 11px;
    color: transparent;
    font-size: 10px;
    font-weight: 700;
    padding: 0;
}}
QPushButton#CheckButton:hover {{ border-color: {FOREST}; color: {FOREST}; }}
QPushButton#CheckButton[checked="true"] {{
    background: {FOREST};
    border-color: {FOREST};
    color: #fffdf6;
}}
QPushButton#SeatAction {{
    background: transparent;
    color: {DANGER};
    font-size: 9px;
    padding: 2px;
}}
QPushButton#TableAction {{
    background: {PAPER_SOFT};
    border: 1px solid {LINE};
    border-radius: 6px;
    color: {INK_SOFT};
    font-size: 8px;
    padding: 4px 7px;
}}
QPushButton#TableAction:hover {{
    border-color: {FOREST};
    color: {FOREST};
    background: {FOREST_WASH};
}}
QPushButton#TableDanger {{
    background: transparent;
    border: none;
    color: {MUTED};
    font-size: 11px;
    padding: 2px;
}}
QPushButton#TableDanger:hover {{ color: {DANGER}; }}

QLineEdit, QTextEdit, QComboBox, QDateTimeEdit, QSpinBox {{
    background: #fffefa;
    border: 1px solid {LINE_STRONG};
    border-radius: 9px;
    padding: 9px 11px;
    color: {INK};
    font-size: 11px;
    selection-background-color: {FOREST_WASH};
    selection-color: {INK};
}}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateTimeEdit:focus {{
    border: 1px solid {FOREST};
    background: #ffffff;
}}
QLineEdit#SearchField {{
    background: {PAPER_SOFT};
    border-radius: 16px;
    padding: 8px 12px;
}}
QComboBox::drop-down {{ border: none; width: 18px; }}
QComboBox QAbstractItemView {{
    background: {PAPER};
    border: 1px solid {LINE};
    selection-background-color: {FOREST_WASH};
    selection-color: {FOREST};
    padding: 4px;
}}
QComboBox QAbstractItemView::item {{ padding: 5px 8px; }}
QCheckBox {{ color: {INK_SOFT}; font-size: 11px; spacing: 7px; }}
QCheckBox::indicator {{
    width: 16px; height: 16px;
    border: 1px solid {LINE_STRONG};
    border-radius: 4px;
    background: {PAPER};
}}
QCheckBox::indicator:checked {{
    background: {FOREST};
    border-color: {FOREST};
    image: none;
}}

QCalendarWidget {{
    background: transparent;
    border: none;
}}
QCalendarWidget QWidget#qt_calendar_navigationbar {{
    background: transparent;
    border: none;
    min-height: 34px;
}}
QCalendarWidget QToolButton {{
    background: transparent;
    border: none;
    color: {INK};
    font-family: "{DISPLAY}";
    font-size: 17px;
    font-weight: 600;
    padding: 4px 6px;
    border-radius: 7px;
}}
QCalendarWidget QToolButton:hover {{ background: {PAPER_SOFT}; }}
QCalendarWidget QSpinBox {{
    background: transparent;
    border: none;
    color: {INK};
    font-size: 12px;
}}
QCalendarWidget QAbstractItemView:enabled {{
    background: {PAPER};
    color: {INK_SOFT};
    selection-background-color: {FOREST};
    selection-color: #fffdf6;
    border: none;
    font-size: 10px;
    outline: none;
}}
QCalendarWidget QAbstractItemView:disabled {{ color: {MUTED_LIGHT}; }}
QCalendarWidget QWidget {{ alternate-background-color: {PAPER}; }}
QCalendarWidget QMenu {{ background: {PAPER}; border: 1px solid {LINE}; }}
QCalendarWidget QSpinBox::up-button, QCalendarWidget QSpinBox::down-button {{
    width: 0; height: 0; border: none;
}}

QScrollArea {{ border: none; background: transparent; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QScrollBar:vertical {{
    background: transparent; width: 8px; margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: {LINE_STRONG}; min-height: 24px; border-radius: 4px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ height: 8px; background: transparent; }}
QScrollBar::handle:horizontal {{ background: {LINE_STRONG}; border-radius: 4px; }}

QTableWidget {{
    background: {PAPER};
    border: none;
    border-top: 1px solid {LINE};
    gridline-color: transparent;
    font-size: 10px;
    selection-background-color: {PAPER_SOFT};
    selection-color: {INK};
}}
QTableWidget::item {{
    padding: 8px 7px;
    border-bottom: 1px solid {LINE};
}}
QHeaderView::section {{
    background: {PAPER_SOFT};
    color: {MUTED_LIGHT};
    border: none;
    border-bottom: 1px solid {LINE};
    padding: 7px;
    font-size: 8px;
    font-weight: 700;
    letter-spacing: 0.6px;
}}
QTableCornerButton::section {{ background: {PAPER_SOFT}; border: none; }}

QDialog {{
    background: {PAPER};
}}
QMessageBox {{
    background: {PAPER};
}}
QMessageBox QLabel {{ font-size: 11px; }}
QToolTip {{
    background: {INK};
    color: #fffdf6;
    border: none;
    padding: 5px 7px;
}}
QStatusBar {{
    background: {PAPER};
    border-top: 1px solid {LINE};
    color: {MUTED};
    font-size: 9px;
}}

QFrame#SeatCard {{
    background: {PAPER};
}}
QFrame#SeatCard[primary="true"] {{
    background: #fffaf5;
    border: 1px solid #e3c4b5;
}}
QFrame#SeatCard[open="true"] {{
    background: rgba(255, 253, 248, 140);
    border: 1px dashed {LINE_STRONG};
}}
QFrame#StatCard {{
    background: {PAPER};
    border-radius: 12px;
}}
QFrame#StatCard[accent="today"] {{ border-top: 2px solid {GOLD}; }}
QFrame#StatCard[accent="overdue"] {{ border-top: 2px solid {CLAY}; }}
QFrame#StatCard[accent="open"] {{ border-top: 2px solid {FOREST}; }}
QLabel#StatLabel {{ color: {MUTED}; font-size: 8px; font-weight: 700; letter-spacing: 0.8px; }}
QLabel#StatValue {{ font-family: "{DISPLAY}"; font-size: 26px; font-weight: 500; color: {INK}; }}
QLabel#StatFoot {{ color: {MUTED_LIGHT}; font-size: 8px; }}
QLabel#SeatBadge {{
    border-radius: 8px; padding: 2px 7px; font-size: 7px; font-weight: 700;
    background: {FOREST_WASH}; color: {FOREST};
}}
QLabel#SeatBadge[primary="true"] {{ background: {CLAY_SOFT}; color: #9b3f21; }}
QLabel#SeatBadge[open="true"] {{ background: {PAPER_SOFT}; color: {MUTED}; }}
QLabel#RoleBadge {{
    border-radius: 8px; padding: 2px 6px; font-size: 8px; font-weight: 700;
    background: {PAPER_SOFT}; color: {MUTED};
}}
QLabel#RoleBadge[role="admin"] {{ background: {FOREST}; color: #fffdf6; }}
QLabel#RoleBadge[role="primary"] {{ background: {CLAY}; color: #fffdf6; }}
QLabel#ProtectedLabel {{ color: #9b3f21; font-size: 9px; font-weight: 700; }}
QLabel#SearchIcon {{ color: {MUTED_LIGHT}; font-size: 12px; }}
"""
