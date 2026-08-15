import sys
import json
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime, timedelta
from PySide6.QtCore import Qt, QTimer, QPoint, QSize
from PySide6.QtGui import QPixmap, QIcon, QPainter, QColor, QFont
from PySide6 import QtSvg
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QSlider, QSystemTrayIcon, QMenu, QSizePolicy
)
from PySide6.QtGui import QAction
from backend.timer import TaskState
from backend.task_runner import TaskRunner
from frontend.popup import Popup, SmoothScrollArea
from backend.sound import SoundManager
from backend.blocker import Blocker


ACCENT = "#FFB300"
ACCENT_HOVER = "#FF8C00"
BG_MAIN = "#050505"
BG_COLUMN = "#0d0d0d"
BG_HEADER_CARD = "#141414"
BG_CARD = "#111111"
BORDER = "#1a1a1a"
BORDER_HEADER = "#1f1f1f"
TEXT_PRIMARY = "#e0e0e0"
TEXT_SECONDARY = "#888888"
TEXT_MUTED = "#444444"
GRAY = "#888888"
GREEN = "#2ed573"
RED = "#ff4757"
BREAK_COLOR = "#4FC3F7"

TOOLBAR_Y_OFFSET = 60
SOUND_BAR_Y_OFFSET = -185
SOUND_BAR_PLACEHOLDER_HEIGHT = 1
FOCUS_COLUMN_Y_OFFSET = 57
LOGO_X_OFFSET = 70
LOGO_Y_OFFSET = 15

SFX_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "sfx")
AMBIENCE_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "ambience")

from paths import resource_path, get_asset_path

ICONS_DIR = get_asset_path("assets", "icons")


def icon_path(filename):
    """كيرجع المسار الكامل لملف svg داخل assets/icons/"""
    return os.path.join(ICONS_DIR, filename)


ICON_EDIT = icon_path("edit.svg")
ICON_MENU = icon_path("menu.svg")
ICON_CLOSE = icon_path("close.svg")
ICON_CHECK = icon_path("check.svg")
ICON_TRASH = icon_path("trash.svg")
ICON_VOLUME = icon_path("volume.svg")
ICON_VOLUME_MUTE = icon_path("volume-mute.svg")
ICON_PLAY = icon_path("play.svg")
ICON_PAUSE = icon_path("pause.svg")
ICON_STATUS_TODO = icon_path("status-todo.svg")
ICON_STATUS_INPROGRESS = icon_path("status-inprogress.svg")
ICON_STATUS_DONE = icon_path("status-done.svg")
ICON_STATUS_REFUSED = icon_path("status-refused.svg")
ICON_RAIN = icon_path("rain.svg")
ICON_FOREST = icon_path("forest.svg")
ICON_WIND = icon_path("wind.svg")
ICON_WAVE = icon_path("wave.svg")
ICON_APP = icon_path("app.ico")
TRAY_ICON = get_asset_path("assets", "icons", "app_tray.ico")
NOTIFY_ICON = get_asset_path("assets", "icons", "app_notify.png")


def set_icon(button, path, size=18):
    """كيحط أيقونة svg فزر (QPushButton) بدل ما يحط ايموجي كنص"""
    button.setText("")
    button.setIcon(QIcon(path))
    button.setIconSize(QSize(size, size))


def _resolve_logo_path():
    candidates = [
        get_asset_path("assets", "FocusFlowBanner.png"),
        get_asset_path("FocusFlowBanner.png"),
        resource_path("assets", "FocusFlowBanner.png"),
        resource_path("FocusFlowBanner.png"),
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return get_asset_path("FocusFlowBanner.png")


LOGO_PATH = _resolve_logo_path()


def state_color(state):
    return {
        TaskState.WAITING: TEXT_SECONDARY,
        TaskState.IN_PROGRESS: ACCENT,
        TaskState.BREAK: BREAK_COLOR,
        TaskState.PENDING_VALIDATION: ACCENT,
        TaskState.COMPLETED: GREEN,
        TaskState.REFUSED: RED,
    }.get(state, TEXT_PRIMARY)


COLUMN_GRADIENTS = {
    "todo": """
        QFrame {
            background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                stop:0 #1a1a1a,
                stop:0.4 #2a2a2a,
                stop:1 #888888);
            border: 1px solid #333333;
            border-radius: 14px;
        }
        QFrame:hover {
            border: 1px solid #555555;
        }
    """,
    "inprogress": """
        QFrame {
            background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                stop:0 #f5f5f5,
                stop:0.3 #e0c060,
                stop:1 #FFB300);
            border: 1px solid #FFB300;
            border-radius: 14px;
        }
        QFrame:hover {
            border: 1px solid #FFE600;
        }
    """,
    "break": """
        QFrame {
            background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                stop:0 #e8e8e8,
                stop:0.4 #a0c8e8,
                stop:1 #4FC3F7);
            border: 1px solid #4FC3F7;
            border-radius: 14px;
        }
        QFrame:hover {
            border: 1px solid #7FD6F9;
        }
    """,
    "done": """
        QFrame {
            background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                stop:0 #e8e8e8,
                stop:0.4 #c8e8d8,
                stop:1 #2ed573);
            border: 1px solid #2ed573;
            border-radius: 14px;
        }
        QFrame:hover {
            border: 1px solid #4ef593;
        }
    """,
    "refused": """
        QFrame {
            background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                stop:0 #e8e8e8,
                stop:0.4 #e8c8c8,
                stop:1 #ff4757);
            border: 1px solid #ff4757;
            border-radius: 14px;
        }
        QFrame:hover {
            border: 1px solid #ff6b7a;
        }
    """,
}


class MarqueeLabel(QLabel):
    """QLabel كيدير scroll تلقائي (من اليمين للشمال) للنص غير إلا كان طويل
    ماكايدخلش فـ العرض ديالو. إلا كان قصير، كيبان عادي وثابت فـ الوسط."""

    def __init__(self, text="", parent=None, text_color="#000000", speed=45, gap=45):
        super().__init__(parent)
        self._full_text = text
        self._text_color = text_color
        self._speed = speed   # بيكسل / ثانية
        self._gap = gap       # المسافة بين كل تكرار للنص
        self._offset = 0.0
        self._text_width = 0
        self._scrolling = False
        self._last_tick = None

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._timer = QTimer(self)
        self._timer.setInterval(30)
        self._timer.timeout.connect(self._advance)
        self.setText(text)

    def setText(self, text):
        self._full_text = text
        super().setText(text)
        self._offset = 0.0
        self._update_scroll_state()

    def minimumSizeHint(self):
        return QSize(0, super().sizeHint().height())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_scroll_state()

    def _update_scroll_state(self):
        fm = self.fontMetrics()
        self._text_width = fm.horizontalAdvance(self._full_text)
        needs_scroll = self.width() > 0 and self._text_width > self.width()

        if needs_scroll and not self._scrolling:
            self._scrolling = True
            self._offset = 0.0
            self._last_tick = None
            self._timer.start()
        elif not needs_scroll and self._scrolling:
            self._scrolling = False
            self._timer.stop()
            self._offset = 0.0
        self.update()

    def _advance(self):
        import time as _time
        now = _time.monotonic()
        if self._last_tick is None:
            self._last_tick = now
        dt = now - self._last_tick
        self._last_tick = now

        loop_length = self._text_width + self._gap
        if loop_length <= 0:
            return
        self._offset = (self._offset + self._speed * dt) % loop_length
        self.update()

    def paintEvent(self, event):
        if not self._scrolling:
            super().paintEvent(event)
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setFont(self.font())
        painter.setPen(QColor(self._text_color))

        fm = painter.fontMetrics()
        y = (self.height() + fm.ascent() - fm.descent()) // 2
        loop_length = self._text_width + self._gap

        x = -int(self._offset)
        while x < self.width():
            painter.drawText(x, y, self._full_text)
            x += loop_length

        painter.end()


class TaskCard(QFrame):
    def __init__(self, runner, on_stop, on_complete, on_refuse, on_edit, on_view, column_type="todo", parent=None):
        super().__init__(parent)
        self.runner = runner
        self.on_stop = on_stop
        self.on_complete = on_complete
        self.on_refuse = on_refuse
        self.on_edit = on_edit
        self.on_view = on_view
        self.column_type = column_type
        self.setFixedHeight(76)
        self.setStyleSheet(COLUMN_GRADIENTS.get(column_type, COLUMN_GRADIENTS["todo"]))
        self._build_ui()

    def _build_ui(self):
        main = QHBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        left_frame = QFrame()
        left_frame.setFixedWidth(58)
        left_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(12, 12, 12, 0.78);
                border: none;
                border-top-left-radius: 14px;
                border-bottom-left-radius: 14px;
                border-top-right-radius: 14px;
                border-bottom-right-radius: 14px;
            }
        """)
        left_col = QVBoxLayout(left_frame)
        left_col.setSpacing(3)
        left_col.setContentsMargins(0, 3, 0, 0)
        left_col.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        if self.column_type == "todo":
            self.edit_btn = QPushButton()
            self.edit_btn.setFixedSize(35, 35)
            self.edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 179, 0, 0.18);
                    border: 1.2px solid rgba(255, 179, 0, 0.45);
                    border-radius: 17px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 179, 0, 0.40);
                    border: 1.2px solid #FFB300;
                }
            """)
            set_icon(self.edit_btn, ICON_EDIT, 20)
            self.edit_btn.clicked.connect(lambda: self.on_edit(self.runner))
            left_col.addWidget(self.edit_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        else:
            self.view_btn = QPushButton()
            self.view_btn.setFixedSize(35, 35)
            self.view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.view_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.10);
                    border: 1.2px solid rgba(255, 255, 255, 0.18);
                    border-radius: 17px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.22);
                    border: 1.2px solid rgba(255, 255, 255, 0.35);
                }
            """)
            set_icon(self.view_btn, ICON_MENU, 20)
            self.view_btn.clicked.connect(lambda: self.on_view(self.runner))
            left_col.addWidget(self.view_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        left_col.addSpacing(3)
        sep_dot = QFrame()
        sep_dot.setFixedHeight(1)
        sep_dot.setFixedWidth(50)
        sep_dot.setStyleSheet("background-color: rgba(255, 255, 255, 0.15); border: none;")
        left_col.addSpacing(3)
        left_col.addWidget(sep_dot, alignment=Qt.AlignmentFlag.AlignHCenter)
        left_col.addSpacing(2)

        dot = QLabel("●")
        p = str(self.runner.priority_instance)
        dot_colors = {"High": "#ff6b6b", "Medium": "#FFB300", "Low": "#2ed573"}
        dot.setStyleSheet(f"color: {dot_colors.get(p, '#FFB300')}; font-size: 20px; background: transparent; border: none;")
        dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_col.addWidget(dot, alignment=Qt.AlignmentFlag.AlignHCenter)

        left_col.addStretch()
        main.addWidget(left_frame)

        content = QHBoxLayout()
        content.setContentsMargins(14, 12, 16, 12)
        content.setSpacing(14)

        center = QVBoxLayout()
        center.setSpacing(0)
        center.setContentsMargins(0, 6, 0, 0)
        center.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.name_lbl = MarqueeLabel(self.runner.name_instance.name, text_color="#000000")
        self.name_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.name_lbl.setStyleSheet("background: transparent; border: none; color: #000000;")
        self.name_lbl.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        center.addWidget(self.name_lbl)
        center.addSpacing(10)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: rgba(0, 0, 0, 0.3); border: none;")
        center.addWidget(sep)
        center.addSpacing(8)

        self.time_lbl = QLabel("--:--")
        self.time_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_lbl.setStyleSheet(
            "color: #000000; font-family: 'Consolas', monospace; font-size: 13px; font-weight: 600; background: transparent; border: none;"
        )
        center.addWidget(self.time_lbl)

        content.addLayout(center, stretch=1)

        right_col = QVBoxLayout()
        right_col.setSpacing(8)
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.stop_btn = QPushButton()
        self.stop_btn.setFixedSize(28, 28)
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 0, 0, 0.25);
                border: 1px solid rgba(0, 0, 0, 0.4);
                border-radius: 14px;
            }
            QPushButton:hover {
                background-color: rgba(231, 76, 60, 0.8);
                border: 1px solid #E74C3C;
            }
        """)
        set_icon(self.stop_btn, ICON_CLOSE, 13)
        self.stop_btn.clicked.connect(lambda: self.on_stop(self.runner))
        right_col.addWidget(self.stop_btn)

        self.done_btn = QPushButton()
        self.done_btn.setFixedSize(35, 35)
        self.done_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.done_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(46, 213, 115, 0.2);
                border: 1px solid rgba(46, 213, 115, 0.5);
                border-radius: 14px;
            }
            QPushButton:hover {
                background-color: #2ed573;
                border: 1px solid #2ed573;
            }
        """)
        set_icon(self.done_btn, ICON_CHECK, 15)
        self.done_btn.clicked.connect(lambda: self.on_complete(self.runner))
        self.done_btn.hide()
        right_col.addWidget(self.done_btn)

        self.refuse_btn = QPushButton()
        self.refuse_btn.setFixedSize(35, 35)
        self.refuse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refuse_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 71, 87, 0.2);
                border: 1px solid rgba(255, 71, 87, 0.5);
                border-radius: 14px;
            }
            QPushButton:hover {
                background-color: #ff4757;
                border: 1px solid #ff4757;
            }
        """)
        set_icon(self.refuse_btn, ICON_CLOSE, 15)
        self.refuse_btn.clicked.connect(lambda: self.on_refuse(self.runner))
        self.refuse_btn.hide()
        right_col.addWidget(self.refuse_btn)

        content.addLayout(right_col)
        main.addLayout(content, stretch=1)

    def refresh(self):
        state = self.runner.time_instance.state

        if state == TaskState.BREAK:
            self.setStyleSheet(COLUMN_GRADIENTS["break"])
        else:
            self.setStyleSheet(COLUMN_GRADIENTS.get(self.column_type, COLUMN_GRADIENTS["todo"]))

        if state == TaskState.COMPLETED:
            self.time_lbl.setText("Done")
            self.stop_btn.hide()
            self.done_btn.hide()
            self.refuse_btn.hide()
        elif state == TaskState.REFUSED:
            self.time_lbl.setText("Refused")
            self.stop_btn.hide()
            self.done_btn.hide()
            self.refuse_btn.hide()
        elif state == TaskState.PENDING_VALIDATION:
            self.time_lbl.setText("00:00")
            self.stop_btn.hide()
            self.done_btn.show()
            self.refuse_btn.show()
        elif state == TaskState.WAITING:
            diff = int((self.runner.time_instance.start_datetime - datetime.now()).total_seconds())
            if diff > 0:
                h = diff // 3600
                m = (diff % 3600) // 60
                self.time_lbl.setText(f"-{h:02d}:{m:02d}")
            else:
                self.time_lbl.setText("00:00")
            self.stop_btn.show()
            self.done_btn.hide()
            self.refuse_btn.hide()
        elif state == TaskState.IN_PROGRESS:
            rem = self.runner.time_instance.remaining_seconds
            m = rem // 60
            s = rem % 60
            self.time_lbl.setText(f"{m:02d}:{s:02d}")
            self.stop_btn.show()
            self.done_btn.hide()
            self.refuse_btn.hide()
        elif state == TaskState.BREAK:
            elapsed = self.runner.time_instance.break_elapsed_seconds
            m = elapsed // 60
            s = elapsed % 60
            self.time_lbl.setText(f"{m:02d}:{s:02d}")
            self.stop_btn.show()
            self.done_btn.hide()
            self.refuse_btn.hide()


class KanbanColumn(QFrame):
    def __init__(self, title, subtitle, accent_color, status_icon="●", column_type="todo", parent=None):
        super().__init__(parent)
        self.title = title
        self.subtitle = subtitle
        self.accent_color = accent_color
        self.status_icon = status_icon
        self.column_type = column_type
        self.cards = {}
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_COLUMN};
                border: 1px solid {BORDER};
                border-radius: 20px;
            }}
        """)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QFrame()
        header.setFixedHeight(76)
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                    stop:0 #080808,
                    stop:0.5 #111111,
                    stop:1 #1a1508);
                border: 1px solid #2a2210;
                border-radius: 16px;
            }}
        """)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(14, 10, 14, 10)
        header_layout.setSpacing(6)

        row1 = QHBoxLayout()
        row1.setSpacing(8)

        menu_icon = QLabel()
        menu_icon.setPixmap(QIcon(ICON_MENU).pixmap(14, 14))
        menu_icon.setStyleSheet("background: transparent; border: none;")

        title_lbl = QLabel(self.title)
        title_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; font-family: 'Segoe UI'; font-size: 16px; font-weight: 600; background: transparent; border: none;")

        row1.addWidget(menu_icon)
        row1.addWidget(title_lbl)
        row1.addStretch()
        header_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(6)

        status_lbl = QLabel()
        if str(self.status_icon).lower().endswith(".svg"):
            status_lbl.setPixmap(QIcon(self.status_icon).pixmap(12, 12))
            status_lbl.setStyleSheet("background: transparent; border: none;")
        else:
            status_lbl.setText(self.status_icon)
            status_lbl.setStyleSheet(f"color: {self.accent_color}; font-size: 11px; background: transparent; border: none;")

        sub_lbl = QLabel(self.subtitle.upper())
        sub_lbl.setStyleSheet(f"color: {self.accent_color}; font-family: 'Segoe UI'; font-size: 10px; font-weight: bold; letter-spacing: 1px; background: transparent; border: none;")

        row2.addWidget(status_lbl)
        row2.addWidget(sub_lbl)
        row2.addStretch()
        header_layout.addLayout(row2)

        layout.addWidget(header)

        self.cards_container = QFrame()
        self.cards_container.setStyleSheet("background: transparent; border: none;")
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(10)
        self.cards_layout.addStretch()

        scroll = SmoothScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:vertical {{ background: transparent; width: 3px; border-radius: 1px; }}
            QScrollBar::handle:vertical {{ background: #222222; min-height: 20px; border-radius: 1px; }}
        """)
        scroll.setWidget(self.cards_container)
        layout.addWidget(scroll)

    def add_card(self, runner, on_stop, on_complete, on_refuse, on_edit, on_view):
        card = TaskCard(runner, on_stop, on_complete, on_refuse, on_edit, on_view, column_type=self.column_type)
        self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)
        self.cards[runner] = card

    def remove_card(self, runner):
        if runner in self.cards:
            card = self.cards.pop(runner)
            card.deleteLater()

    def get_card(self, runner):
        return self.cards.get(runner)

    def sort_cards(self, key_func):
        ordered = sorted(self.cards.keys(), key=key_func)
        for runner in ordered:
            self.cards_layout.removeWidget(self.cards[runner])
        for runner in ordered:
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, self.cards[runner])


class FocusPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(400)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_COLUMN};
                border: 1px solid {BORDER};
                border-radius: 24px;
            }}
        """)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 28, 24, 28)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        layout.addSpacing(25)

        tabs = QHBoxLayout()
        tabs.setSpacing(6)
        tabs.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.tab_focus = QLabel("FOCUS")
        self.tab_break = QLabel("BREAK")

        for lbl, active in [(self.tab_focus, True), (self.tab_break, False)]:
            if active:
                lbl.setStyleSheet(f"""
                    QLabel {{
                        color: #000000;
                        background-color: {ACCENT};
                        border-radius: 10px;
                        padding: 7px 18px;
                        font-family: 'Segoe UI';
                        font-size: 11px;
                        font-weight: bold;
                    }}
                """)
            else:
                lbl.setStyleSheet(f"""
                    QLabel {{
                        color: {TEXT_SECONDARY};
                        background-color: #0f0f0f;
                        border-radius: 10px;
                        padding: 7px 18px;
                        font-family: 'Segoe UI';
                        font-size: 11px;
                        font-weight: bold;
                    }}
                """)
            tabs.addWidget(lbl)

        layout.addLayout(tabs)

        circle_container = QFrame()
        circle_container.setFixedSize(260, 260)
        circle_container.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border: 3px solid {BORDER};
                border-radius: 130px;
            }}
        """)

        inner_ring = QFrame(circle_container)
        inner_ring.setFixedSize(240, 240)
        inner_ring.move(10, 10)
        inner_ring.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border: 2px solid {ACCENT};
                border-radius: 120px;
            }}
        """)

        circle_layout = QVBoxLayout(circle_container)
        circle_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        circle_layout.setSpacing(4)

        self.big_time = QLabel("__ : __")
        self.big_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.big_time.setStyleSheet(f"color: {TEXT_PRIMARY}; font-family: 'Segoe UI'; font-size: 48px; font-weight: 300; background: transparent; border: none;")

        state_row = QHBoxLayout()
        state_row.setSpacing(6)
        state_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.state_icon_lbl = QLabel()
        self.state_icon_lbl.setStyleSheet("background: transparent; border: none;")
        self.state_icon_lbl.hide()

        self.focus_label = QLabel("READY")
        self.focus_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.focus_label.setStyleSheet(f"color: {ACCENT}; font-family: 'Segoe UI'; font-size: 20px; font-weight: bold; letter-spacing: 4px; background: transparent; border: none;")

        state_row.addWidget(self.state_icon_lbl)
        state_row.addWidget(self.focus_label)

        circle_layout.addWidget(self.big_time)
        circle_layout.addSpacing(15)
        circle_layout.addLayout(state_row)

        layout.addWidget(circle_container, alignment=Qt.AlignmentFlag.AlignHCenter)

        controls = QHBoxLayout()
        controls.setSpacing(20)
        controls.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.play_btn = QPushButton()
        self.play_btn.setFixedSize(60, 60)
        self.play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT};
                border: none;
                border-radius: 28px;
            }}
            QPushButton:hover {{
                background-color: {ACCENT_HOVER};
            }}
        """)
        set_icon(self.play_btn, ICON_PLAY, 26)

        controls.addWidget(self.play_btn)
        layout.addLayout(controls)

        progress = QHBoxLayout()
        progress.setSpacing(6)
        progress.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bars = []
        for i in range(2):
            bar = QFrame()
            bar.setFixedSize(28, 4)
            bar.setStyleSheet(f"background-color: {BORDER}; border-radius: 2px;")
            progress.addWidget(bar)
            self.progress_bars.append(bar)
        layout.addLayout(progress)

        layout.addStretch()

    def update_focus(self, runner):
        if runner is None:
            self.big_time.setText("__ : __")
            self.focus_label.setText("READY")
            self.state_icon_lbl.hide()
            self._set_focus_mode(True)
            set_icon(self.play_btn, ICON_PLAY, 26)
            return

        state = runner.time_instance.state

        if state == TaskState.WAITING:
            diff = int((runner.time_instance.start_datetime - datetime.now()).total_seconds())
            if diff > 0:
                h = diff // 3600
                m = (diff % 3600) // 60
                s = diff % 60
                self.big_time.setText(f"{h:02d}:{m:02d}:{s:02d}")
            else:
                self.big_time.setText("00:00:00")
            self.focus_label.setText("WAITING")
            self.state_icon_lbl.hide()
            self._set_focus_mode(True)
            set_icon(self.play_btn, ICON_PLAY, 26)
        elif state == TaskState.IN_PROGRESS:
            rem = runner.time_instance.remaining_seconds
            m = rem // 60
            s = rem % 60
            self.big_time.setText(f"{m:02d}:{s:02d}")
            self.focus_label.setText("FOCUS")
            self.state_icon_lbl.hide()
            self._set_focus_mode(True)
            set_icon(self.play_btn, ICON_PAUSE, 26)
        elif state == TaskState.BREAK:
            elapsed = runner.time_instance.break_elapsed_seconds
            m = elapsed // 60
            s = elapsed % 60
            self.big_time.setText(f"{m:02d}:{s:02d}")
            self.focus_label.setText("BREAK")
            self.state_icon_lbl.hide()
            self._set_focus_mode(False)
            set_icon(self.play_btn, ICON_PLAY, 26)
        else:
            self.big_time.setText("00:00")
            self.focus_label.setText("DONE")
            self.state_icon_lbl.setPixmap(QIcon(ICON_STATUS_DONE).pixmap(16, 16))
            self.state_icon_lbl.show()
            self._set_focus_mode(True)
            set_icon(self.play_btn, ICON_PLAY, 26)

    def _set_focus_mode(self, is_focus):
        if is_focus:
            self.tab_focus.setStyleSheet(f"""
                QLabel {{
                    color: #000000;
                    background-color: {ACCENT};
                    border-radius: 10px;
                    padding: 7px 18px;
                    font-family: 'Segoe UI';
                    font-size: 11px;
                    font-weight: bold;
                }}
            """)
            self.tab_break.setStyleSheet(f"""
                QLabel {{
                    color: {TEXT_SECONDARY};
                    background-color: #0f0f0f;
                    border-radius: 10px;
                    padding: 7px 18px;
                    font-family: 'Segoe UI';
                    font-size: 11px;
                    font-weight: bold;
                }}
            """)
        else:
            self.tab_focus.setStyleSheet(f"""
                QLabel {{
                    color: {TEXT_SECONDARY};
                    background-color: #0f0f0f;
                    border-radius: 10px;
                    padding: 7px 18px;
                    font-family: 'Segoe UI';
                    font-size: 11px;
                    font-weight: bold;
                }}
            """)
            self.tab_break.setStyleSheet(f"""
                QLabel {{
                    color: #000000;
                    background-color: {ACCENT};
                    border-radius: 10px;
                    padding: 7px 18px;
                    font-family: 'Segoe UI';
                    font-size: 11px;
                    font-weight: bold;
                }}
            """)

        self.progress_bars[0].setStyleSheet(f"background-color: {ACCENT if is_focus else BORDER}; border-radius: 2px;")
        self.progress_bars[1].setStyleSheet(f"background-color: {ACCENT if not is_focus else BORDER}; border-radius: 2px;")


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FocusFlow")
        self.setWindowIcon(QIcon(ICON_APP))
        self.resize(1280, 850)
        self.setStyleSheet(f"background-color: {BG_MAIN};")

        self.glow_logo = QFrame(self)
        self.glow_logo.setStyleSheet("""
            QFrame {
                background: qradialgradient(cx:0.12, cy:0.12, radius:0.75,
                    stop:0 rgba(255, 179, 0, 50),
                    stop:0.35 rgba(255, 140, 0, 22),
                    stop:0.65 rgba(255, 100, 0, 8),
                    stop:1 rgba(5, 5, 5, 0));
                border: none;
            }
        """)
        self.glow_logo.lower()

        self.glow_br = QFrame(self)
        self.glow_br.setStyleSheet("""
            QFrame {
                background: qradialgradient(cx:1.05, cy:1.05, radius:1.8,
                    stop:0 rgba(255, 179, 0, 48),
                    stop:0.18 rgba(255, 150, 30, 14),
                    stop:0.40 rgba(255, 130, 20, 4),
                    stop:0.70 rgba(255, 110, 10, 1),
                    stop:1 rgba(5, 5, 5, 0));
                border: none;
            }
        """)
        self.glow_br.lower()

        self.active_runners = []
        self.task_widgets = {}
        self.current_popup = None
        self.focused_runner = None
        self.blocker = Blocker()
        self._timer_done_played = set()

        self._init_sound()
        self._build_ui()

        QTimer.singleShot(0, self._reposition_sound_bar)
        QTimer.singleShot(0, self._reposition_logo)

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(TRAY_ICON))
        self.tray_icon.setToolTip("FocusFlow")

        tray_menu = QMenu(self)
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)

        hide_action = QAction("Hide", self)
        hide_action.triggered.connect(self.hide)
        tray_menu.addAction(hide_action)

        tray_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self._tray_exit)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._refresh_all)
        self.refresh_timer.start(1000)

    def _init_sound(self):
        self.sound = SoundManager(self)
        self._sound_buttons = {}

        ambience_map = {
            "deep_rain": "rain.ogg",
            "forest": "forest.ogg",
            "brown_noise": "brown.ogg",
            "ocean": "ocean.ogg",
        }
        for key, filename in ambience_map.items():
            path = os.path.join(AMBIENCE_DIR, filename)
            self.sound.register_ambience(key, path)

        sfx_map = {
            "add_task": "add.ogg",
            "timer_done": "done.ogg",
            "cancel": "cancel.ogg",
            "refuse": "refuse.ogg",
        }
        for key, filename in sfx_map.items():
            path = os.path.join(SFX_DIR, filename)
            self.sound.preload_effect(key, path)

        self.sound.ambience_active.connect(self._on_ambience_active)
        self.sound.effect_error.connect(self._on_sound_error)
        self.sound.error_occurred.connect(self._on_sound_error)
        self.sound.global_mute_changed.connect(self._on_mute_changed)
        self.sound.global_volume_changed.connect(self._on_volume_changed)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 4, 40, 28)
        main_layout.setSpacing(8)

        logo_row = QHBoxLayout()
        logo_row.setSpacing(0)

        self.logo_lbl = QLabel()
        self.logo_lbl.setFixedSize(360, 100)
        pixmap = QPixmap(LOGO_PATH)
        if not pixmap.isNull():
            self.logo_lbl.setPixmap(pixmap.scaled(340, 95, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.logo_lbl.setStyleSheet("background: transparent; border: none;")
        else:
            self.logo_lbl.setText("FocusFlow")
            self.logo_lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            self.logo_lbl.setStyleSheet(f"color: {ACCENT}; font-size: 26px; font-weight: bold; background: transparent; border: none;")

        self.logo_placeholder = QFrame()
        self.logo_placeholder.setFixedSize(360, 100)
        self.logo_placeholder.setStyleSheet("background: transparent; border: none;")
        logo_row.addWidget(self.logo_placeholder)
        logo_row.addStretch()
        main_layout.addLayout(logo_row)

        self.logo_lbl.setParent(self)
        self.logo_lbl.raise_()

        content = QHBoxLayout()
        content.setSpacing(28)
        content.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.focus_panel = FocusPanel()
        focus_panel_wrapper = QVBoxLayout()
        focus_panel_wrapper.setContentsMargins(0, FOCUS_COLUMN_Y_OFFSET, 0, 0)
        focus_panel_wrapper.addWidget(self.focus_panel)
        content.addLayout(focus_panel_wrapper)

        right_side = QVBoxLayout()
        right_side.setSpacing(16)
        right_side.setAlignment(Qt.AlignmentFlag.AlignTop)
        right_side.setContentsMargins(0, TOOLBAR_Y_OFFSET, 0, 0)

        self.toolbar = QFrame()
        self.toolbar.setFixedHeight(64)
        self.toolbar.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_COLUMN};
                border: 1px solid {BORDER};
                border-radius: 30px;
            }}
        """)
        tb_layout = QHBoxLayout(self.toolbar)
        tb_layout.setContentsMargins(20, 0, 20, 0)
        tb_layout.setSpacing(16)

        add_task_btn = QPushButton("+  Add Task")
        add_task_btn.setFixedHeight(40)
        add_task_btn.setMinimumWidth(200)
        add_task_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_task_btn.setStyleSheet(f"""
            QPushButton {{
                color: {ACCENT};
                background-color: transparent;
                font-size: 15px;
                font-weight: bold;
                border: 1px dashed {TEXT_MUTED};
                border-radius: 10px;
            }}
            QPushButton:hover {{
                border: 1px solid {ACCENT};
                background-color: #1a1508;
            }}
        """)
        add_task_btn.clicked.connect(self.show_popup)
        tb_layout.addWidget(add_task_btn, stretch=1)

        tb_layout.addStretch()

        self.stats_lbl = QLabel("0 / 0 COMPLETED")
        self.stats_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-family: 'Segoe UI'; font-size: 12px; font-weight: 600; letter-spacing: 0.5px; background: transparent; border: none;")
        tb_layout.addWidget(self.stats_lbl)
        tb_layout.addSpacing(20)

        clear_btn = QPushButton("  CLEAR BOARD")
        clear_btn.setIcon(QIcon(ICON_TRASH))
        clear_btn.setIconSize(QSize(14, 14))
        clear_btn.setFixedHeight(40)
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                color: {TEXT_SECONDARY};
                background-color: {BG_MAIN};
                font-family: 'Segoe UI';
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 0.5px;
                border: 1px solid {BORDER};
                border-radius: 10px;
                padding: 0 16px;
            }}
            QPushButton:hover {{
                color: #ff4757;
                border-color: #ff4757;
                background-color: #1a0a0a;
            }}
        """)
        clear_btn.clicked.connect(self._clear_board)
        tb_layout.addWidget(clear_btn)

        right_side.addWidget(self.toolbar)

        sound_bar = QFrame()
        sound_bar.setFixedHeight(70)
        sound_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_COLUMN};
                border: 1px solid {BORDER};
                border-radius: 35px;
            }}
        """)
        sound_layout = QHBoxLayout(sound_bar)
        sound_layout.setContentsMargins(16, 10, 16, 10)
        sound_layout.setSpacing(12)
        sound_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.vol_btn = QPushButton()
        self.vol_btn.setFixedSize(44, 44)
        self.vol_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.vol_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BG_HEADER_CARD};
                border: 1px solid {BORDER};
                border-radius: 22px;
            }}
            QPushButton:hover {{
                border-color: {ACCENT};
            }}
        """)
        set_icon(self.vol_btn, ICON_VOLUME, 20)
        self.vol_btn.clicked.connect(self._toggle_mute)
        sound_layout.addWidget(self.vol_btn)

        self.vol_slider = QSlider(Qt.Orientation.Horizontal)
        self.vol_slider.setFixedWidth(140)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(int(self.sound.get_master_volume() * 100))
        self.vol_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{ height: 6px; background: transparent; border-radius: 3px; }}
            QSlider::sub-page:horizontal {{ background: {ACCENT}; border-radius: 3px; }}
            QSlider::add-page:horizontal {{ background: transparent; border-radius: 3px; }}
            QSlider::handle:horizontal {{ width: 18px; height: 18px; margin: -6px 0; background: {TEXT_PRIMARY}; border-radius: 9px; }}
        """)
        self.vol_slider.valueChanged.connect(self._on_slider_changed)
        sound_layout.addWidget(self.vol_slider)

        sep = QFrame()
        sep.setFixedSize(1, 36)
        sep.setStyleSheet(f"background-color: {BORDER};")
        sound_layout.addWidget(sep)

        ambience_data = [
            (ICON_RAIN, "DEEP RAIN", "deep_rain"),
            (ICON_FOREST, "FOREST", "forest"),
            (ICON_WIND, "BROWN NOISE", "brown_noise"),
            (ICON_WAVE, "OCEAN", "ocean"),
        ]
        for icon, text, key in ambience_data:
            btn = QPushButton()
            btn.setFixedSize(44, 44)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("ambience_key", key)
            set_icon(btn, icon, 20)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {BG_HEADER_CARD};
                    border: 1px solid {BORDER};
                    border-radius: 22px;
                }}
                QPushButton:hover {{
                    border-color: {ACCENT};
                }}
            """)
            btn.setToolTip(text)
            btn.clicked.connect(lambda checked=False, k=key: self._on_ambience_clicked(k))
            sound_layout.addWidget(btn)
            self._sound_buttons[key] = btn

        sound_wrapper = QHBoxLayout()
        sound_wrapper.setSpacing(0)
        sound_wrapper.setContentsMargins(0, 0, 0, 0)
        sound_wrapper.addStretch()
        self.sound_bar_placeholder = QFrame()
        self.sound_bar_placeholder.setFixedSize(sound_bar.sizeHint().width(), SOUND_BAR_PLACEHOLDER_HEIGHT)
        self.sound_bar_placeholder.setStyleSheet("background: transparent; border: none;")
        sound_wrapper.addWidget(self.sound_bar_placeholder)
        right_side.addLayout(sound_wrapper)

        sound_bar.setParent(self)
        self.sound_bar = sound_bar
        self.sound_bar.raise_()

        col_headers = QHBoxLayout()
        col_headers.setSpacing(16)

        todo_frame = QFrame()
        todo_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_COLUMN};
                border: 1px solid {BORDER};
                border-radius: 10px;
            }}
        """)
        h1 = QHBoxLayout(todo_frame)
        h1.setContentsMargins(12, 8, 12, 8)
        h1.setSpacing(4)
        lbl1 = QLabel("TO DO")
        lbl1.setStyleSheet(f"color: {TEXT_SECONDARY}; font-family: 'Segoe UI'; font-size: 12px; font-weight: 600; letter-spacing: 1.5px; background: transparent; border: none;")
        dot1 = QLabel("●")
        dot1.setStyleSheet(f"color: {GRAY}; font-size: 15px; background: transparent; border: none;")
        self.todo_badge = QLabel("0")
        self.todo_badge.setFixedSize(36, 26)
        self.todo_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.todo_badge.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_SECONDARY};
                background-color: {BG_HEADER_CARD};
                border: 1px solid {BORDER};
                border-radius: 6px;
                font-family: 'Segoe UI';
                font-size: 13px;
                font-weight: bold;
            }}
        """)
        h1.addWidget(lbl1)
        h1.addWidget(dot1)
        h1.addStretch()
        h1.addWidget(self.todo_badge)
        col_headers.addWidget(todo_frame, stretch=1)

        inprog_frame = QFrame()
        inprog_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_COLUMN};
                border: 1px solid {BORDER};
                border-radius: 10px;
            }}
        """)
        h2 = QHBoxLayout(inprog_frame)
        h2.setContentsMargins(12, 8, 12, 8)
        h2.setSpacing(4)
        lbl2 = QLabel("IN PROGRESS")
        lbl2.setStyleSheet(f"color: {TEXT_SECONDARY}; font-family: 'Segoe UI'; font-size: 12px; font-weight: 600; letter-spacing: 1.5px; background: transparent; border: none;")
        dot2 = QLabel("●")
        dot2.setStyleSheet(f"color: {ACCENT}; font-size: 15px; background: transparent; border: none;")
        self.inprog_badge = QLabel("0")
        self.inprog_badge.setFixedSize(36, 26)
        self.inprog_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.inprog_badge.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_SECONDARY};
                background-color: {BG_HEADER_CARD};
                border: 1px solid {BORDER};
                border-radius: 6px;
                font-family: 'Segoe UI';
                font-size: 13px;
                font-weight: bold;
            }}
        """)
        h2.addWidget(lbl2)
        h2.addWidget(dot2)
        h2.addStretch()
        h2.addWidget(self.inprog_badge)
        col_headers.addWidget(inprog_frame, stretch=1)

        h3 = QHBoxLayout()
        h3.setSpacing(12)
        h3.addStretch()

        done_frame = QFrame()
        done_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_COLUMN};
                border: 1px solid {BORDER};
                border-radius: 10px;
            }}
        """)
        done_layout = QHBoxLayout(done_frame)
        done_layout.setContentsMargins(12, 8, 12, 8)
        done_layout.setSpacing(4)

        lbl3 = QLabel("DONE")
        lbl3.setStyleSheet(f"color: {TEXT_SECONDARY}; font-family: 'Segoe UI'; font-size: 12px; font-weight: 600; letter-spacing: 1.5px; background: transparent; border: none;")
        dot3 = QLabel("●")
        dot3.setStyleSheet(f"color: {GREEN}; font-size: 15px; background: transparent; border: none;")
        self.done_badge = QLabel("0")
        self.done_badge.setFixedSize(36, 26)
        self.done_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.done_badge.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_SECONDARY};
                background-color: {BG_HEADER_CARD};
                border: 1px solid {BORDER};
                border-radius: 6px;
                font-family: 'Segoe UI';
                font-size: 13px;
                font-weight: bold;
            }}
        """)
        done_layout.addWidget(lbl3)
        done_layout.addWidget(dot3)
        done_layout.addStretch()
        done_layout.addWidget(self.done_badge)
        h3.addWidget(done_frame)

        refused_frame = QFrame()
        refused_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_COLUMN};
                border: 1px solid {BORDER};
                border-radius: 10px;
            }}
        """)
        refused_layout = QHBoxLayout(refused_frame)
        refused_layout.setContentsMargins(12, 8, 12, 8)
        refused_layout.setSpacing(4)

        lbl4 = QLabel("REFUSED")
        lbl4.setStyleSheet(f"color: {TEXT_SECONDARY}; font-family: 'Segoe UI'; font-size: 12px; font-weight: 600; letter-spacing: 1.5px; background: transparent; border: none;")
        dot4 = QLabel("●")
        dot4.setStyleSheet(f"color: {RED}; font-size: 15px; background: transparent; border: none;")
        self.refused_badge = QLabel("0")
        self.refused_badge.setFixedSize(36, 26)
        self.refused_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.refused_badge.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_SECONDARY};
                background-color: {BG_HEADER_CARD};
                border: 1px solid {BORDER};
                border-radius: 6px;
                font-family: 'Segoe UI';
                font-size: 13px;
                font-weight: bold;
            }}
        """)
        refused_layout.addWidget(lbl4)
        refused_layout.addWidget(dot4)
        refused_layout.addStretch()
        refused_layout.addWidget(self.refused_badge)
        h3.addWidget(refused_frame)

        h3.addStretch()

        col_headers.addLayout(h3, stretch=1)
        right_side.addLayout(col_headers)

        columns_row = QHBoxLayout()
        columns_row.setSpacing(16)

        self.todo_col = KanbanColumn("TO DO", "TO DO", GRAY, "○", column_type="todo")
        columns_row.addWidget(self.todo_col, stretch=1)

        self.inprogress_col = KanbanColumn("In Progress", "IN PROGRESS", ACCENT, ICON_STATUS_INPROGRESS, column_type="inprogress")
        columns_row.addWidget(self.inprogress_col, stretch=1)

        done_refused_container = QVBoxLayout()
        done_refused_container.setSpacing(12)
        done_refused_container.setContentsMargins(0, 0, 0, 0)

        self.done_col = KanbanColumn("Done", "DONE", GREEN, ICON_STATUS_DONE, column_type="done")
        self.refused_col = KanbanColumn("Refused", "REFUSED", RED, ICON_STATUS_REFUSED, column_type="refused")

        done_refused_container.addWidget(self.done_col, stretch=1)
        done_refused_container.addWidget(self.refused_col, stretch=1)

        done_refused_widget = QFrame()
        done_refused_widget.setLayout(done_refused_container)
        done_refused_widget.setStyleSheet("background: transparent; border: none;")
        columns_row.addWidget(done_refused_widget, stretch=1)

        right_side.addLayout(columns_row, stretch=1)
        content.addLayout(right_side, stretch=1)
        main_layout.addLayout(content, stretch=1)

        self.focus_panel.play_btn.clicked.connect(self._toggle_focus_break)

    def _toggle_focus_break(self):
        if self.focused_runner is None:
            return

        state = self.focused_runner.time_instance.state

        if state == TaskState.WAITING:
            self.focused_runner.time_instance.start_now()
        elif state == TaskState.IN_PROGRESS:
            self.focused_runner.time_instance.go_to_break()
        elif state == TaskState.BREAK:
            self.focused_runner.time_instance.resume_focus()

        self.focus_panel.update_focus(self.focused_runner)
        self._refresh_all()

    def _on_ambience_clicked(self, key):
        if self.sound.active_ambience() == key:
            self.sound.stop_ambience()
        else:
            self.sound.play_ambience(key)

    def _on_ambience_active(self, name, active):
        for k, btn in self._sound_buttons.items():
            if k == name and active:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        color: {BG_MAIN};
                        background-color: {ACCENT};
                        font-size: 20px;
                        border: 1px solid {ACCENT};
                        border-radius: 22px;
                    }}
                    QPushButton:hover {{
                        background-color: {ACCENT_HOVER};
                        border-color: {ACCENT_HOVER};
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        color: {TEXT_SECONDARY};
                        background-color: {BG_HEADER_CARD};
                        font-size: 20px;
                        border: 1px solid {BORDER};
                        border-radius: 22px;
                    }}
                    QPushButton:hover {{
                        color: {TEXT_PRIMARY};
                        border-color: {ACCENT};
                    }}
                """)

    def _on_slider_changed(self, value):
        self.sound.set_master_volume(value / 100.0)

    def _toggle_mute(self):
        self.sound.toggle_mute()

    def _on_mute_changed(self, muted):
        icons = {True: ICON_VOLUME_MUTE, False: ICON_VOLUME}
        set_icon(self.vol_btn, icons.get(muted, ICON_VOLUME), 20)
        if muted:
            self.vol_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {BG_HEADER_CARD};
                    border: 1px solid {RED};
                    border-radius: 22px;
                }}
                QPushButton:hover {{
                    border-color: #ff6b6b;
                }}
            """)
        else:
            self.vol_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {BG_HEADER_CARD};
                    border: 1px solid {BORDER};
                    border-radius: 22px;
                }}
                QPushButton:hover {{
                    border-color: {ACCENT};
                }}
            """)

    def _on_volume_changed(self, vol):
        self.vol_slider.blockSignals(True)
        self.vol_slider.setValue(int(vol * 100))
        self.vol_slider.blockSignals(False)

    def _on_sound_error(self, msg):
        pass

    def show_popup(self):
        self.current_popup = Popup(
            self,
            on_save_callback=self.handle_task_saved,
            existing_tasks=self._get_existing_task_windows()
        )

    def _get_existing_task_windows(self, exclude_runner=None):
        windows = []
        for r in self.active_runners:
            if r is exclude_runner:
                continue
            if r.time_instance.state in (TaskState.COMPLETED, TaskState.REFUSED):
                continue
            start = r.time_instance.start_datetime
            end = start + timedelta(seconds=r.time_instance.duration_total_seconds)
            windows.append((start, end, r.name_instance.name))
        return windows

    def handle_task_saved(self, name_obj, time_obj, priority_obj, sites_list):
        self.sound.play_effect("add_task")
        runner = TaskRunner(name_obj, time_obj, priority_obj, sites_list, sound_manager=self.sound)
        runner.description = self.current_popup.desc_text.toPlainText().strip() if self.current_popup else ""
        runner.sites = sites_list
        runner.start()
        self.active_runners.append(runner)

        if runner.time_instance.state == TaskState.WAITING:
            self.todo_col.add_card(runner, self._stop_task, self._complete_task, self._refuse_task, self._edit_task, self._view_task)
        elif runner.time_instance.state in (TaskState.IN_PROGRESS, TaskState.BREAK):
            self.inprogress_col.add_card(runner, self._stop_task, self._complete_task, self._refuse_task, self._edit_task, self._view_task)
        elif runner.time_instance.state == TaskState.REFUSED:
            self.refused_col.add_card(runner, self._stop_task, self._complete_task, self._refuse_task, self._edit_task, self._view_task)
        else:
            self.done_col.add_card(runner, self._stop_task, self._complete_task, self._refuse_task, self._edit_task, self._view_task)

        self._update_stats()
        self._update_badges()
        self._pick_focus_task()

    def _edit_task(self, runner):
        task_data = {
            "name": runner.name_instance.name,
            "description": getattr(runner, 'description', ''),
            "start_hour": runner.time_instance.start_hour,
            "start_min": runner.time_instance.start_minute,
            "dur_hour": runner.time_instance.duration_hours,
            "dur_min": runner.time_instance.duration_minutes,
            "sites": getattr(runner, 'sites', []),
            "priority": str(runner.priority_instance)
        }
        self.current_popup = Popup(
            self,
            on_save_callback=self.handle_task_saved,
            start_rect=None,
            edit_mode=True,
            task_data=task_data,
            on_edit_callback=lambda data: self._on_task_edited(runner, data),
            existing_tasks=self._get_existing_task_windows(exclude_runner=runner)
        )

    def _view_task(self, runner):
        task_data = {
            "name": runner.name_instance.name,
            "description": getattr(runner, 'description', ''),
            "start_hour": runner.time_instance.start_hour,
            "start_min": runner.time_instance.start_minute,
            "dur_hour": runner.time_instance.duration_hours,
            "dur_min": runner.time_instance.duration_minutes,
            "sites": getattr(runner, 'sites', []),
            "priority": str(runner.priority_instance)
        }
        self.current_popup = Popup(
            self,
            on_save_callback=None,
            start_rect=None,
            edit_mode=False,
            task_data=task_data,
            read_only=True
        )

    def _on_task_edited(self, runner, new_data):
        from backend.name import Name
        from backend.timer import Time
        from backend.priority import Priority

        old_name = runner.name_instance.name

        runner.stop()
        for col in [self.todo_col, self.inprogress_col, self.done_col, self.refused_col]:
            if runner in col.cards:
                col.remove_card(runner)
        if runner in self.active_runners:
            self.active_runners.remove(runner)

        name_obj = Name(new_data["name"])
        time_obj = Time(
            new_data["start_hour"], new_data["start_min"], 0,
            new_data["dur_hour"], new_data["dur_min"], 0
        )
        priority_obj = Priority(new_data["priority"])
        sites_list = new_data["sites"]

        new_runner = TaskRunner(name_obj, time_obj, priority_obj, sites_list, sound_manager=self.sound)
        new_runner.description = new_data.get("description", "")
        new_runner.start()
        self.active_runners.append(new_runner)

        if new_runner.time_instance.state == TaskState.WAITING:
            self.todo_col.add_card(new_runner, self._stop_task, self._complete_task, self._refuse_task, self._edit_task, self._view_task)
        elif new_runner.time_instance.state in (TaskState.IN_PROGRESS, TaskState.BREAK):
            self.inprogress_col.add_card(new_runner, self._stop_task, self._complete_task, self._refuse_task, self._edit_task, self._view_task)
        elif new_runner.time_instance.state == TaskState.REFUSED:
            self.refused_col.add_card(new_runner, self._stop_task, self._complete_task, self._refuse_task, self._edit_task, self._view_task)
        else:
            self.done_col.add_card(new_runner, self._stop_task, self._complete_task, self._refuse_task, self._edit_task, self._view_task)

        self._delete_task_from_json(old_name)
        self._save_task_to_json(new_data)

        self._update_stats()
        self._update_badges()
        self._pick_focus_task()
        self._refresh_all()

    def _save_task_to_json(self, task_data):
        try:
            tasks = []
            if os.path.exists("tasks.json"):
                with open("tasks.json", "r", encoding="utf-8") as f:
                    tasks = json.load(f)
            tasks.append(task_data)
            with open("tasks.json", "w", encoding="utf-8") as f:
                json.dump(tasks, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error saving task: {e}")

    def _stop_task(self, runner):
        self.sound.play_effect("cancel")
        self._delete_task_from_json(runner.name_instance.name)
        self._timer_done_played.discard(runner)
        runner.stop()

        for col in [self.todo_col, self.inprogress_col, self.done_col, self.refused_col]:
            if runner in col.cards:
                col.remove_card(runner)

        if runner in self.active_runners:
            self.active_runners.remove(runner)
        if runner in self.task_widgets:
            del self.task_widgets[runner]

        if self.focused_runner == runner:
            self.focused_runner = None
            self._pick_focus_task()

        self._update_stats()
        self._update_badges()

    def _complete_task(self, runner):
        self.sound.play_effect("done")
        self._timer_done_played.discard(runner)
        runner.time_instance.mark_completed()
        self._refresh_all()

    def _refuse_task(self, runner):
        self.sound.play_effect("refuse")
        self._timer_done_played.discard(runner)
        runner.time_instance.cancel_or_refuse_task()
        self._refresh_all()

    def _clear_board(self):
        for runner in list(self.active_runners):
            self._delete_task_from_json(runner.name_instance.name)
            runner.stop()
        self.active_runners.clear()
        self.task_widgets.clear()
        self.focused_runner = None
        for col in [self.todo_col, self.inprogress_col, self.done_col, self.refused_col]:
            for runner in list(col.cards.keys()):
                col.remove_card(runner)
        self._update_stats()
        self._update_badges()
        self.focus_panel.update_focus(None)

    def _update_stats(self):
        total = len(self.active_runners)
        done = sum(1 for r in self.active_runners if r.time_instance.state in (TaskState.COMPLETED, TaskState.REFUSED))
        self.stats_lbl.setText(f"{done} / {total} COMPLETED")

    def _update_badges(self):
        if hasattr(self, 'todo_badge'):
            self.todo_badge.setText(str(len(self.todo_col.cards)))
        if hasattr(self, 'inprog_badge'):
            self.inprog_badge.setText(str(len(self.inprogress_col.cards)))
        if hasattr(self, 'done_badge'):
            self.done_badge.setText(str(len(self.done_col.cards)))
        if hasattr(self, 'refused_badge'):
            self.refused_badge.setText(str(len(self.refused_col.cards)))

    def _pick_focus_task(self):
        for runner in self.active_runners:
            if runner.time_instance.state in (TaskState.IN_PROGRESS, TaskState.BREAK):
                self.focused_runner = runner
                return
        for runner in self.active_runners:
            if runner.time_instance.state == TaskState.WAITING:
                self.focused_runner = runner
                return
        self.focused_runner = None

    def _refresh_all(self):
        for runner in list(self.active_runners):
            state = runner.time_instance.state
            if state == TaskState.IN_PROGRESS:
                runner.time_instance.tick_focus()
            elif state == TaskState.BREAK:
                runner.time_instance.tick_break()
            elif state == TaskState.WAITING:
                runner.time_instance.update_status()

        for runner in list(self.active_runners):
            state = runner.time_instance.state

            if state == TaskState.PENDING_VALIDATION and runner not in self._timer_done_played:
                self.sound.play_effect("timer_done")
                self._timer_done_played.add(runner)

            current_col = None
            for col in [self.todo_col, self.inprogress_col, self.done_col, self.refused_col]:
                if runner in col.cards:
                    current_col = col
                    break

            if state == TaskState.WAITING:
                target_col = self.todo_col
            elif state in (TaskState.IN_PROGRESS, TaskState.BREAK, TaskState.PENDING_VALIDATION):
                target_col = self.inprogress_col
            elif state == TaskState.REFUSED:
                target_col = self.refused_col
            else:
                target_col = self.done_col

            if current_col != target_col and current_col is not None:
                current_col.remove_card(runner)
                target_col.add_card(runner, self._stop_task, self._complete_task, self._refuse_task, self._edit_task, self._view_task)

            card = target_col.get_card(runner) if target_col else None
            if card:
                card.refresh()

        self.todo_col.sort_cards(lambda r: r.time_instance.start_datetime)
        self.inprogress_col.sort_cards(lambda r: r.time_instance.remaining_seconds)

        self._pick_focus_task()
        self.focus_panel.update_focus(self.focused_runner)
        self._update_stats()
        self._update_badges()

    def _delete_task_from_json(self, task_name):
        try:
            if os.path.exists("tasks.json"):
                with open("tasks.json", "r", encoding="utf-8") as f:
                    tasks = json.load(f)
                tasks = [t for t in tasks if t.get("name") != task_name]
                with open("tasks.json", "w", encoding="utf-8") as f:
                    json.dump(tasks, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

    def _clear_tasks_json(self):
        try:
            with open("tasks.json", "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=4)
        except Exception:
            pass

    def _reposition_sound_bar(self):
        if hasattr(self, 'sound_bar') and hasattr(self, 'sound_bar_placeholder'):
            pos = self.sound_bar_placeholder.pos()
            self.sound_bar.setGeometry(pos.x(), pos.y() + SOUND_BAR_Y_OFFSET, self.sound_bar_placeholder.width(), 95)
            self.sound_bar.raise_()

    def _reposition_logo(self):
        if hasattr(self, 'logo_lbl') and hasattr(self, 'logo_placeholder'):
            pos = self.logo_placeholder.pos()
            self.logo_lbl.setGeometry(pos.x() + LOGO_X_OFFSET, pos.y() + LOGO_Y_OFFSET, self.logo_placeholder.width(), self.logo_placeholder.height())
            self.logo_lbl.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'glow_logo'):
            self.glow_logo.setGeometry(0, 0, self.width(), self.height())
        if hasattr(self, 'glow_br'):
            self.glow_br.setGeometry(0, 0, self.width(), self.height())
        self._reposition_sound_bar()
        self._reposition_logo()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.raise_()
                self.activateWindow()

    def _tray_exit(self):
        self._force_close = True
        self.close()

    def closeEvent(self, event):
        if not getattr(self, '_force_close', False):
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "FocusFlow",
                "Running in background. Click tray icon to restore.",
                QIcon(NOTIFY_ICON),
                2000
            )
            return

        self.refresh_timer.stop()
        self.sound.save()
        for runner in self.active_runners:
            runner.stop()
        self.blocker.unblock_sites()
        self._clear_tasks_json()
        self.tray_icon.hide()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
