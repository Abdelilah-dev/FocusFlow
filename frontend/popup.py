import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import json
from datetime import timedelta
from PySide6.QtCore import Qt, QVariantAnimation, QEasingCurve, QRect, QSize
from PySide6.QtGui import QIntValidator, QPixmap, QColor
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QFrame, QGraphicsDropShadowEffect, QSizePolicy,
    QLayout, QScrollArea
)
from backend.name import Name
from backend.timer import Time
from backend.priority import Priority
from backend.sites import Sites
from paths import resource_path, get_asset_path, app_data_path

TASKS_FILE = app_data_path("tasks.json")


def _resolve_logo_path():
    candidates = [
        get_asset_path("assets", "FocusFlow.png"),
        get_asset_path("FocusFlow.png"),
        resource_path("assets", "FocusFlow.png"),
        resource_path("FocusFlow.png"),
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return get_asset_path("FocusFlow.png")


LOGO_PATH = _resolve_logo_path()


def load_tasks():
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_task_to_json(task_data):
    tasks = load_tasks()
    tasks.append(task_data)
    try:
        with open(TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error saving task: {e}")


def update_task_in_json(old_name, new_data):
    try:
        if os.path.exists(TASKS_FILE):
            with open(TASKS_FILE, "r", encoding="utf-8") as f:
                tasks = json.load(f)
            for i, task in enumerate(tasks):
                if task.get("name") == old_name:
                    tasks[i] = new_data
                    break
            with open(TASKS_FILE, "w", encoding="utf-8") as f:
                json.dump(tasks, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error updating task: {e}")


class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, hSpacing=8, vSpacing=8):
        super().__init__(parent)
        self._item_list = []
        self.setContentsMargins(margin, margin, margin, margin)
        self.m_h_space = hSpacing
        self.m_v_space = vSpacing

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self._item_list.append(item)

    def horizontalSpacing(self):
        return self.m_h_space

    def verticalSpacing(self):
        return self.m_v_space

    def count(self):
        return len(self._item_list)

    def itemAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def _do_layout(self, rect, test_only):
        left, top, right, bottom = self.getContentsMargins()
        effective_rect = rect.adjusted(left, top, -right, -bottom)
        x = effective_rect.x()
        y = effective_rect.y()
        line_height = 0

        for item in self._item_list:
            space_x = self.m_h_space
            space_y = self.m_v_space
            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > effective_rect.right() and line_height > 0:
                x = effective_rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(x, y, item.sizeHint().width(), item.sizeHint().height()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y() + bottom


class SmoothScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(220)
        self.anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.anim.valueChanged.connect(self._set_scroll_value)
        self.target_value = 0

    def wheelEvent(self, event):
        scrollbar = self.verticalScrollBar()
        delta = event.angleDelta().y()

        if self.anim.state() == QVariantAnimation.State.Running:
            current = self.target_value
        else:
            current = scrollbar.value()

        self.target_value = current - int(delta * 0.4)
        self.target_value = max(scrollbar.minimum(), min(scrollbar.maximum(), self.target_value))

        self.anim.stop()
        self.anim.setStartValue(scrollbar.value())
        self.anim.setEndValue(self.target_value)
        self.anim.start()
        event.accept()

    def _set_scroll_value(self, value):
        self.verticalScrollBar().setValue(int(value))


class AnimatedLineEdit(QLineEdit):
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        if placeholder:
            self.setPlaceholderText(placeholder)
        self.focus_progress = 0.0
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(250)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.valueChanged.connect(self._on_anim_value_changed)
        self.returnPressed.connect(self.clearFocus)
        self.update_style()

    def focusInEvent(self, event):
        self.anim.stop()
        self.anim.setStartValue(self.focus_progress)
        self.anim.setEndValue(1.0)
        self.anim.start()
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self.anim.stop()
        self.anim.setStartValue(self.focus_progress)
        self.anim.setEndValue(0.0)
        self.anim.start()
        super().focusOutEvent(event)

    def _on_anim_value_changed(self, val):
        self.focus_progress = val
        self.update_style()

    def update_style(self):
        r = int(18 + (8 - 18) * self.focus_progress)
        g = int(18 + (8 - 18) * self.focus_progress)
        b = int(18 + (8 - 18) * self.focus_progress)

        br = int(51 + (255 - 51) * self.focus_progress)
        bg = int(51 + (215 - 51) * self.focus_progress)
        bb = int(51 + (0 - 51) * self.focus_progress)

        border_width = 1.0 + 0.6 * self.focus_progress

        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: rgb({r}, {g}, {b});
                border: {border_width}px solid rgb({br}, {bg}, {bb});
                border-radius: 18px;
                color: #FFFFFF;
                padding: 6px 16px;
                font-family: 'FreeSerif', 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
                font-size: 14px;
                font-weight: 600;
                selection-background-color: #FFB300;
                selection-color: #000000;
            }}
        """)


class AnimatedTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.focus_progress = 0.0
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(250)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.valueChanged.connect(self._on_anim_value_changed)

        self.scroll_anim = QVariantAnimation(self)
        self.scroll_anim.setDuration(220)
        self.scroll_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.scroll_anim.valueChanged.connect(self._set_scroll_value)
        self.target_value = 0

        self.update_style()

    def focusInEvent(self, event):
        self.anim.stop()
        self.anim.setStartValue(self.focus_progress)
        self.anim.setEndValue(1.0)
        self.anim.start()
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self.anim.stop()
        self.anim.setStartValue(self.focus_progress)
        self.anim.setEndValue(0.0)
        self.anim.start()
        super().focusOutEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                super().keyPressEvent(event)
            else:
                self.clearFocus()
        else:
            super().keyPressEvent(event)

    def wheelEvent(self, event):
        scrollbar = self.verticalScrollBar()
        delta = event.angleDelta().y()

        if self.scroll_anim.state() == QVariantAnimation.State.Running:
            current = self.target_value
        else:
            current = scrollbar.value()

        self.target_value = current - int(delta * 0.4)
        self.target_value = max(scrollbar.minimum(), min(scrollbar.maximum(), self.target_value))

        self.scroll_anim.stop()
        self.scroll_anim.setStartValue(scrollbar.value())
        self.scroll_anim.setEndValue(self.target_value)
        self.scroll_anim.start()
        event.accept()

    def _set_scroll_value(self, value):
        self.verticalScrollBar().setValue(int(value))

    def _on_anim_value_changed(self, val):
        self.focus_progress = val
        self.update_style()

    def update_style(self):
        r = int(18 + (8 - 18) * self.focus_progress)
        g = int(18 + (8 - 18) * self.focus_progress)
        b = int(18 + (8 - 18) * self.focus_progress)

        br = int(51 + (255 - 51) * self.focus_progress)
        bg = int(51 + (215 - 51) * self.focus_progress)
        bb = int(51 + (0 - 51) * self.focus_progress)

        border_width = 1.0 + 0.6 * self.focus_progress

        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: rgb({r}, {g}, {b});
                border: {border_width}px solid rgb({br}, {bg}, {bb});
                border-radius: 18px;
                color: #FFFFFF;
                padding: 10px;
                font-family: 'FreeSerif', 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
                font-size: 14px;
                font-weight: 600;
                selection-background-color: #FFB300;
                selection-color: #000000;
            }}
            QTextEdit QScrollBar:vertical {{
                background: #0a0a0a;
                width: 8px;
                margin: 4px 2px;
                border-radius: 4px;
            }}
            QTextEdit QScrollBar::handle:vertical {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #777777, stop:1 #444444);
                min-height: 25px;
                border-radius: 4px;
                border: none;
            }}
            QTextEdit QScrollBar::handle:vertical:hover {{
                background: #999999;
            }}
            QTextEdit QScrollBar::add-line:vertical, QTextEdit QScrollBar::sub-line:vertical {{
                height: 0px;
                background: none;
            }}
            QTextEdit QScrollBar::add-page:vertical, QTextEdit QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)


class AnimatedSpinbox(QFrame):
    def __init__(self, min_val=0, max_val=59, initial_val=0, unit="", right_margin=2, parent=None):
        super().__init__(parent)
        self.min_val = min_val
        self.max_val = max_val
        self.value = max(min_val, min(max_val, initial_val))
        self.unit = unit
        self.hover_progress = 0.0

        self.setFixedSize(96, 42)

        self.anim = QVariantAnimation(self)
        self.anim.setDuration(250)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.valueChanged.connect(self._on_anim_value_changed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, right_margin, 0)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.input_field = QLineEdit(f"{self.value:02d}")
        self.input_field.setFixedWidth(32)
        self.input_field.setFixedHeight(34)
        self.input_field.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        self.input_field.setMaxLength(2)
        self.input_field.returnPressed.connect(self.input_field.clearFocus)
        self.input_field.setStyleSheet("""
            QLineEdit {
                color: #FFB300;
                font-family: 'FreeSerif', 'Noto Serif', 'Georgia', 'Times New Roman', serif;
                font-weight: bold;
                font-size: 16px;
                border: none;
                background: transparent;
                selection-background-color: #FFB300;
                selection-color: #000000;
                padding: 0px;
            }
        """)

        validator = QIntValidator(self.min_val, self.max_val, self)
        self.input_field.setValidator(validator)
        self.input_field.textChanged.connect(self._on_text_changed)
        self.input_field.editingFinished.connect(self._on_editing_finished)

        self.unit_label = QLabel(self.unit)
        self.unit_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.unit_label.setStyleSheet("color: #FFB300; font-family: 'FreeSerif', 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif; font-weight: bold; font-size: 12px; border: none; background: transparent; padding-top: 0px; padding-bottom: 7px;")

        btn_widget = QWidget()
        btn_widget.setFixedWidth(28)
        btn_widget.setFixedHeight(42)
        btn_widget.setStyleSheet("background: transparent; border: none;")

        btn_layout = QVBoxLayout(btn_widget)
        btn_layout.setContentsMargins(0, 2, 2, 2)
        btn_layout.setSpacing(0)

        up_btn = QPushButton("▲")
        up_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        up_btn.setFixedHeight(18)
        up_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #FFB300;
                border: none;
                border-radius: 9px;
                font-size: 9px;
                font-weight: bold;
            }
            QPushButton:hover { 
                background-color: rgba(255, 179, 0, 0.28); 
                color: #FFFFFF; 
            }
            QPushButton:pressed {
                background-color: rgba(255, 179, 0, 0.5);
            }
        """)
        up_btn.clicked.connect(self.increment)

        down_btn = QPushButton("▼")
        down_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        down_btn.setFixedHeight(18)
        down_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #FFB300;
                border: none;
                border-radius: 9px;
                font-size: 9px;
                font-weight: bold;
            }
            QPushButton:hover { 
                background-color: rgba(255, 179, 0, 0.28); 
                color: #FFFFFF; 
            }
            QPushButton:pressed {
                background-color: rgba(255, 179, 0, 0.5);
            }
        """)
        down_btn.clicked.connect(self.decrement)

        btn_layout.addWidget(up_btn)
        btn_layout.addWidget(down_btn)

        layout.addWidget(self.input_field, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.unit_label, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addStretch()
        layout.addWidget(btn_widget, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.update_style()

    def enterEvent(self, event):
        self.anim.stop()
        self.anim.setStartValue(self.hover_progress)
        self.anim.setEndValue(1.0)
        self.anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.anim.stop()
        self.anim.setStartValue(self.hover_progress)
        self.anim.setEndValue(0.0)
        self.anim.start()
        super().leaveEvent(event)

    def _on_anim_value_changed(self, val):
        self.hover_progress = val
        self.update_style()

    def update_style(self):
        r = int(15 + (26 - 15) * self.hover_progress)
        g = int(15 + (26 - 15) * self.hover_progress)
        b = int(15 + (26 - 15) * self.hover_progress)

        br = int(51 + (255 - 51) * self.hover_progress)
        bg = int(51 + (215 - 51) * self.hover_progress)
        bb = int(51 + (0 - 51) * self.hover_progress)

        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgb({r}, {g}, {b});
                border: 1.4px solid rgb({br}, {bg}, {bb});
                border-radius: 21px;
            }}
        """)

    def trigger_pulse_animation(self):
        self.pulse_anim = QVariantAnimation(self)
        self.pulse_anim.setDuration(220)
        self.pulse_anim.setStartValue(1.0)
        self.pulse_anim.setEndValue(0.0)
        self.pulse_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.pulse_anim.valueChanged.connect(self._on_pulse_anim_value)
        self.pulse_anim.start()

    def _on_pulse_anim_value(self, val):
        r = int(255)
        g = int(179 + (76 * val))
        b = int(255 * val)
        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                color: rgb({r}, {g}, {b});
                font-family: 'FreeSerif', 'Noto Serif', 'Georgia', 'Times New Roman', serif;
                font-weight: bold;
                font-size: 16px;
                border: none;
                background: transparent;
                selection-background-color: #FFB300;
                selection-color: #000000;
                padding: 0px;
            }}
        """)

    def _on_text_changed(self, text):
        text = text.strip()
        if text.isdigit():
            val = int(text)
            if val > self.max_val:
                self.value = self.max_val
                self.update_text()
            else:
                self.value = val

    def _on_editing_finished(self):
        text = self.input_field.text().strip()
        if not text.isdigit():
            self.value = self.min_val
        else:
            self.value = max(self.min_val, min(self.max_val, int(text)))
        self.update_text()

    def update_text(self):
        self.input_field.blockSignals(True)
        self.input_field.setText(f"{self.value:02d}")
        self.input_field.blockSignals(False)
        self.trigger_pulse_animation()

    def increment(self):
        self.value = self.value + 1 if self.value < self.max_val else self.min_val
        self.update_text()

    def decrement(self):
        self.value = self.value - 1 if self.value > self.min_val else self.max_val
        self.update_text()

    def get_value(self) -> int:
        self._on_editing_finished()
        return self.value

    def set_value(self, val: int):
        self.value = max(self.min_val, min(self.max_val, val))
        self.update_text()


class AnimatedCloseButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__("✕", parent)
        self.setFixedSize(34, 34)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.hover_progress = 0.0

        self.anim = QVariantAnimation(self)
        self.anim.setDuration(200)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.valueChanged.connect(self._on_anim_value)

        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(12)
        self.shadow.setColor(QColor(255, 179, 0, 0))
        self.shadow.setOffset(0, 2)
        self.setGraphicsEffect(self.shadow)

        self.update_style()

    def enterEvent(self, event):
        self.anim.stop()
        self.anim.setStartValue(self.hover_progress)
        self.anim.setEndValue(1.0)
        self.anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.anim.stop()
        self.anim.setStartValue(self.hover_progress)
        self.anim.setEndValue(0.0)
        self.anim.start()
        super().leaveEvent(event)

    def _on_anim_value(self, val):
        self.hover_progress = val
        self.shadow.setBlurRadius(int(12 + 8 * val))
        self.shadow.setColor(QColor(255, 179, 0, int(180 * val)))
        self.update_style()

    def update_style(self):
        r = int(20 + (255 - 20) * self.hover_progress)
        g = int(20 + (179 - 20) * self.hover_progress)
        b = int(20 + (0 - 20) * self.hover_progress)

        text_r = int(136 + (0 - 136) * self.hover_progress)
        text_g = int(136 + (0 - 136) * self.hover_progress)
        text_b = int(136 + (0 - 136) * self.hover_progress)

        border_r = int(51 + (255 - 51) * self.hover_progress)
        border_g = int(51 + (215 - 51) * self.hover_progress)
        border_b = int(51 + (0 - 51) * self.hover_progress)

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: rgb({int(31 - 11 * self.hover_progress)}, {int(31 - 11 * self.hover_progress)}, {int(31 - 11 * self.hover_progress)});
                color: rgb({text_r}, {text_g}, {text_b});
                font-family: 'FreeSerif', 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
                font-size: 14px;
                font-weight: bold;
                border: {1.0 + 0.6 * self.hover_progress}px solid rgb({border_r}, {border_g}, {border_b});
                border-radius: 17px;
            }}
            QPushButton:pressed {{
                background-color: #D4A017;
            }}
        """)


class AnimatedAddButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.hover_progress = 0.0
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(200)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.valueChanged.connect(self._on_anim_value)
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(15)
        self.shadow.setColor(QColor(255, 140, 0, 150))
        self.shadow.setOffset(0, 4)
        self.setGraphicsEffect(self.shadow)
        self.update_style()

    def enterEvent(self, event):
        self.anim.stop()
        self.anim.setStartValue(self.hover_progress)
        self.anim.setEndValue(1.0)
        self.anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.anim.stop()
        self.anim.setStartValue(self.hover_progress)
        self.anim.setEndValue(0.0)
        self.anim.start()
        super().leaveEvent(event)

    def _on_anim_value(self, val):
        self.hover_progress = val
        self.shadow.setBlurRadius(int(15 + 15 * val))
        self.shadow.setColor(QColor(255, 179, 0, int(150 + 105 * val)))
        self.shadow.setOffset(0, int(4 + 3 * val))
        self.update_style()

    def update_style(self):
        border_px = 1.0 + 0.8 * self.hover_progress
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFE600, stop:1 #FF8C00); 
                color: #000000; 
                font-family: 'FreeSerif', 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
                font-size: 13px; font-weight: bold;
                border: {border_px}px solid #FFFFFF; 
                border-radius: 19px;
            }}
            QPushButton:pressed {{
                background-color: #D4A017;
            }}
        """)


class AnimatedSubmitButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.hover_progress = 0.0
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(200)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.valueChanged.connect(self._on_anim_value)

        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(15)
        self.shadow.setColor(QColor(255, 140, 0, 150))
        self.shadow.setOffset(0, 4)
        self.setGraphicsEffect(self.shadow)
        self.update_style()

    def enterEvent(self, event):
        self.anim.stop()
        self.anim.setStartValue(self.hover_progress)
        self.anim.setEndValue(1.0)
        self.anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.anim.stop()
        self.anim.setStartValue(self.hover_progress)
        self.anim.setEndValue(0.0)
        self.anim.start()
        super().leaveEvent(event)

    def _on_anim_value(self, val):
        self.hover_progress = val
        self.shadow.setBlurRadius(int(15 + 15 * val))
        self.shadow.setColor(QColor(255, 179, 0, int(150 + 105 * val)))
        self.shadow.setOffset(0, int(4 + 3 * val))
        self.update_style()

    def update_style(self):
        border_px = 1.0 + 0.8 * self.hover_progress
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFE600, stop:1 #FF8C00); 
                color: #000000; 
                font-family: 'FreeSerif', 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
                font-size: 14px; font-weight: bold;
                border: {border_px}px solid #FFFFFF; 
                border-radius: 21px;
            }}
            QPushButton:pressed {{
                background-color: #D4A017;
            }}
        """)


class AnimatedPriorityButton(QPushButton):
    def __init__(self, text, base_color_hex, parent=None):
        super().__init__(text, parent)
        self.text_str = text
        self.base_color = QColor(base_color_hex)
        self.is_selected = False
        self.is_hovered = False
        self.setFixedHeight(38)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.progress = 0.0
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(250)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.valueChanged.connect(self._on_animation_value_changed)

        self.update_stylesheet()

    def set_selected(self, selected):
        if self.is_selected != selected:
            self.is_selected = selected
            self.update_stylesheet()
            self.run_animation()

    def enterEvent(self, event):
        self.is_hovered = True
        self.run_animation()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovered = False
        self.run_animation()
        super().leaveEvent(event)

    def run_animation(self):
        self.anim.stop()
        start_val = self.progress
        target_val = 1.0 if (self.is_selected or self.is_hovered) else 0.0
        if start_val == target_val:
            self.update_stylesheet()
            return
        self.anim.setStartValue(start_val)
        self.anim.setEndValue(target_val)
        self.anim.start()

    def _on_animation_value_changed(self, value):
        self.progress = value
        self.update_stylesheet()

    def update_stylesheet(self):
        if self.is_selected:
            if self.text_str == "High":
                bg_color = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ff6b6b, stop:1 #e74c3c)"
            elif self.text_str == "Medium":
                bg_color = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFE600, stop:1 #FF8C00)"
            else:
                bg_color = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2ed573, stop:1 #0a6e41)"
            border_color = "#FFFFFF"
            text_color = "#000000"
            border_width = "1.8px"
        else:
            r = int(18 + (self.base_color.red() - 18) * (0.6 * self.progress))
            g = int(18 + (self.base_color.green() - 18) * (0.6 * self.progress))
            b = int(18 + (self.base_color.blue() - 18) * (0.6 * self.progress))
            bg_color = f"rgb({r}, {g}, {b})"

            bc_r = int(51 + (self.base_color.red() - 51) * self.progress)
            bc_g = int(51 + (self.base_color.green() - 51) * self.progress)
            bc_b = int(51 + (self.base_color.blue() - 51) * self.progress)
            border_color = f"rgb({bc_r}, {bc_g}, {bc_b})"
            text_color = self.base_color.name()
            border_width = f"{1.2 + 0.6 * self.progress}px"

        self.setStyleSheet(f"""
            QPushButton {{
                border-radius: 19px;
                font-family: 'FreeSerif', 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
                font-weight: bold;
                font-size: 13px;
                background-color: {bg_color};
                color: {text_color};
                border: {border_width} solid {border_color};
            }}
        """)


class AnimatedChip(QFrame):
    def __init__(self, site_name, on_delete_callback, container_widget, parent=None):
        super().__init__(parent)
        self.site_name = site_name
        self.on_delete_callback = on_delete_callback
        self.container_widget = container_widget

        self.setFixedHeight(38)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.target_width = len(site_name) * 8 + 55
        self.setFixedWidth(0)

        self.setStyleSheet("""
            QFrame {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFE600, stop:1 #FF8C00);
                border-radius: 19px;
                border: 1px solid #FFFFFF;
            }
            QLabel { 
                color: #000000; 
                font-family: 'FreeSerif', 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif; 
                font-size: 13px; 
                font-weight: bold;
                background: transparent;
                border: none;
            }
        """)

        c_layout = QHBoxLayout(self)
        c_layout.setContentsMargins(14, 2, 6, 2)
        c_layout.setSpacing(8)

        s_lbl = QLabel(site_name)

        del_btn = QPushButton("✕")
        del_btn.setFixedSize(26, 26)
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 11px;
                border: none;
                border-radius: 13px;
            }
            QPushButton:hover {
                background-color: #FF0000;
            }
        """)
        del_btn.clicked.connect(self.animate_out_and_delete)

        c_layout.addWidget(s_lbl)
        c_layout.addWidget(del_btn)

    def showEvent(self, event):
        super().showEvent(event)
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(250)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.setStartValue(0)
        self.anim.setEndValue(self.target_width)
        self.anim.valueChanged.connect(self._on_width_anim)
        self.anim.start()

    def _on_width_anim(self, val):
        self.setFixedWidth(val)
        if self.container_widget:
            self.container_widget.updateGeometry()

    def animate_out_and_delete(self):
        self.setEnabled(False)
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(180)
        self.anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self.anim.setStartValue(self.width())
        self.anim.setEndValue(0)
        self.anim.valueChanged.connect(self._on_width_anim)
        self.anim.finished.connect(lambda: self.on_delete_callback(self))
        self.anim.start()


class Popup(QWidget):
    def __init__(self, parent, on_save_callback, start_rect=None, edit_mode=False, task_data=None, on_edit_callback=None, read_only=False, existing_tasks=None, existing_names=None, retry_mode=False):
        super().__init__(parent)
        self.on_save_callback = on_save_callback
        self.on_edit_callback = on_edit_callback
        self.edit_mode = edit_mode
        self.retry_mode = retry_mode
        self.read_only = read_only
        self.task_data = task_data or {}
        self.old_name = task_data.get("name", "") if edit_mode else ""
        self.blocked_sites_list = []
        self.selected_priority = "Medium"
        self.sites_helper = Sites()
        self.existing_tasks = existing_tasks or []
        self.existing_names = existing_names or set()

        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setGeometry(0, 0, parent.width(), parent.height())
        self.setStyleSheet("background-color: rgba(0, 0, 0, 0.0);")

        final_w, final_h = 570, 690
        final_x = (parent.width() - final_w) // 2
        final_y = (parent.height() - final_h) // 2
        self.final_rect = QRect(final_x, final_y, final_w, final_h)

        if start_rect:
            self.start_rect = start_rect
        else:
            self.start_rect = QRect(final_x + final_w // 2, final_y + final_h // 2, 0, 0)

        self.card = QFrame(self)
        self.card.setGeometry(self.start_rect)
        self.card.setStyleSheet("""
            QFrame {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #333333, 
                    stop:0.02 #161616, 
                    stop:0.5 #050505, 
                    stop:1 #000000
                );
                border: 1.5px solid #444444;
                border-radius: 42px;
            }
            QLabel {
                border: none;
                background: transparent;
                font-family: 'FreeSerif', 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
            }
        """)

        card_shadow = QGraphicsDropShadowEffect(self.card)
        card_shadow.setBlurRadius(40)
        card_shadow.setColor(QColor(255, 179, 0, 45))
        card_shadow.setOffset(0, 10)
        self.card.setGraphicsEffect(card_shadow)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(28, 20, 28, 20)
        card_layout.setSpacing(8)

        self._build_header(card_layout)
        self._build_task_name(card_layout)
        self._build_description(card_layout)
        self._build_time_card_section(card_layout)
        self._build_sites_section(card_layout)
        self._build_priority_section(card_layout)
        self._build_submit_button(card_layout)

        # Fill data if edit mode
        if self.task_data:
            self._fill_edit_data()

        if self.read_only:
            self._set_read_only()

        parent.installEventFilter(self)
        self.show()
        self.raise_()

        self.anim = QVariantAnimation(self)
        self.anim.setDuration(220)
        self.anim.setEasingCurve(QEasingCurve.Type.OutBack)
        self.anim.valueChanged.connect(self._on_anim_value_changed)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.start()

    def _fill_edit_data(self):
        td = self.task_data
        self.name_entry.setText(td.get("name", ""))
        self.desc_text.setPlainText(td.get("description", ""))
        self.start_hour.set_value(td.get("start_hour", 0))
        self.start_min.set_value(td.get("start_min", 0))
        self.dur_hour.set_value(td.get("dur_hour", 0))
        self.dur_min.set_value(td.get("dur_min", 25))
        self.set_priority(td.get("priority", "Medium"))

        sites = td.get("sites", [])
        for site in sites:
            if site and site not in self.blocked_sites_list:
                if not self.blocked_sites_list:
                    self.sites_layout.removeWidget(self.empty_sites_lbl)
                    self.empty_sites_lbl.hide()
                self.blocked_sites_list.append(site)
                chip = AnimatedChip(site, self.remove_site_chip, self.sites_container)
                self.sites_layout.addWidget(chip)
        self.sites_container.updateGeometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.setGeometry(0, 0, self.parent().width(), self.parent().height())

        final_w, final_h = 570, 690
        final_x = (self.parent().width() - final_w) // 2
        final_y = (self.parent().height() - final_h) // 2
        self.final_rect = QRect(final_x, final_y, final_w, final_h)

        if hasattr(self, 'card') and not (getattr(self, 'anim', None) and self.anim.state() == QVariantAnimation.State.Running) and \
           not (getattr(self, 'close_anim', None) and self.close_anim.state() == QVariantAnimation.State.Running):
            self.card.setGeometry(self.final_rect)

    def _on_anim_value_changed(self, val):
        self.setStyleSheet(f"background-color: rgba(0, 0, 0, {val * 0.35});")
        x = int(self.start_rect.x() + (self.final_rect.x() - self.start_rect.x()) * val)
        y = int(self.start_rect.y() + (self.final_rect.y() - self.start_rect.y()) * val)
        w = int(self.start_rect.width() + (self.final_rect.width() - self.start_rect.width()) * val)
        h = int(self.start_rect.height() + (self.final_rect.height() - self.start_rect.height()) * val)
        self.card.setGeometry(x, y, w, h)

    def closeEvent(self, event):
        self.parent().removeEventFilter(self)
        super().closeEvent(event)

    def close(self):
        self.close_anim = QVariantAnimation(self)
        self.close_anim.setDuration(180)
        self.close_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self.close_anim.valueChanged.connect(self._on_close_anim_value)
        self.close_anim.setStartValue(1.0)
        self.close_anim.setEndValue(0.0)
        self.close_anim.finished.connect(super().close)
        self.close_anim.start()

    def _on_close_anim_value(self, val):
        self.setStyleSheet(f"background-color: rgba(0, 0, 0, {val * 0.35});")
        x = int(self.start_rect.x() + (self.final_rect.x() - self.start_rect.x()) * val)
        y = int(self.start_rect.y() + (self.final_rect.y() - self.start_rect.y()) * val)
        w = int(self.start_rect.width() + (self.final_rect.width() - self.start_rect.width()) * val)
        h = int(self.start_rect.height() + (self.final_rect.height() - self.start_rect.height()) * val)
        self.card.setGeometry(x, y, w, h)

    def eventFilter(self, obj, event):
        if obj == self.parent() and event.type() == event.Type.Resize:
            self.setGeometry(0, 0, self.parent().width(), self.parent().height())
        return super().eventFilter(obj, event)

    def _set_read_only(self):
        self.name_entry.setEnabled(False)
        self.name_entry.setStyleSheet(self.name_entry.styleSheet().replace("color: #FFFFFF;", "color: #888888;"))
        self.desc_text.setEnabled(False)
        self.start_hour.setEnabled(False)
        self.start_min.setEnabled(False)
        self.dur_hour.setEnabled(False)
        self.dur_min.setEnabled(False)
        self.site_entry.setEnabled(False)
        self.btn_high.setEnabled(False)
        self.btn_med.setEnabled(False)
        self.btn_low.setEnabled(False)
        # Disable add button for sites
        for i in range(self.sites_layout.count()):
            item = self.sites_layout.itemAt(i)
            if item and item.widget():
                w = item.widget()
                if isinstance(w, AnimatedChip):
                    # Hide delete buttons on chips in read-only mode
                    for child in w.findChildren(QPushButton):
                        child.hide()

    def _build_header(self, layout):
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)

        logo_label = QLabel()
        pixmap = QPixmap(LOGO_PATH)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                170, 56, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            logo_label.setPixmap(scaled_pixmap)
        else:
            logo_label.setText("FocusFlow")
            logo_label.setStyleSheet("""
                QLabel {
                    color: #FFB300;
                    font-family: 'FreeSerif', 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
                    font-size: 18px;
                    font-weight: bold;
                    background: transparent;
                    border: none;
                }
            """)

        close_btn = AnimatedCloseButton()
        close_btn.clicked.connect(self.close)

        header.addWidget(logo_label, alignment=Qt.AlignmentFlag.AlignVCenter)
        header.addStretch()
        header.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

        layout.addLayout(header)

    def _build_task_name(self, layout):
        lbl = QLabel("📌 Task Name")
        lbl.setStyleSheet("color: #CCCCCC; font-size: 13px; font-weight: bold;")

        self.name_entry = AnimatedLineEdit("What are you working on?")
        self.name_entry.setFixedHeight(38)

        layout.addWidget(lbl)
        layout.addWidget(self.name_entry)

    def _build_description(self, layout):
        lbl = QLabel("📝 Description")
        lbl.setStyleSheet("color: #CCCCCC; font-size: 13px; font-weight: bold;")

        self.desc_text = AnimatedTextEdit()
        self.desc_text.setFixedHeight(60)

        layout.addWidget(lbl)
        layout.addWidget(self.desc_text)

    def _build_time_card_section(self, layout):
        time_main_layout = QHBoxLayout()
        time_main_layout.setContentsMargins(0, 0, 0, 0)
        time_main_layout.setSpacing(10)

        start_card = QFrame()
        start_card.setStyleSheet("""
            QFrame {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0e0e0e, stop:1 #060606);
                border: 1px solid #222222;
                border-radius: 18px;
            }
        """)
        sc_layout = QVBoxLayout(start_card)
        sc_layout.setContentsMargins(12, 10, 12, 10)
        sc_layout.setSpacing(6)

        lbl1 = QLabel("⏱️ Start Time")
        lbl1.setStyleSheet("color: #CCCCCC; font-size: 12px; font-weight: bold; background: transparent; border: none;")

        h1 = QHBoxLayout()
        h1.setSpacing(4)
        h1.setContentsMargins(0, 0, 0, 0)
        self.start_hour = AnimatedSpinbox(0, 23, 0, unit="h", right_margin=2)
        colon1 = QLabel(":")
        colon1.setStyleSheet("color: #FFB300; font-family: 'FreeSerif', 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif; font-weight: bold; font-size: 16px; background: transparent; border: none;")
        colon1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.start_min = AnimatedSpinbox(0, 59, 0, unit="min", right_margin=6)

        h1.addWidget(self.start_hour)
        h1.addWidget(colon1)
        h1.addWidget(self.start_min)

        sc_layout.addWidget(lbl1)
        sc_layout.addLayout(h1)

        dur_card = QFrame()
        dur_card.setStyleSheet("""
            QFrame {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0e0e0e, stop:1 #060606);
                border: 1px solid #222222;
                border-radius: 18px;
            }
        """)
        dc_layout = QVBoxLayout(dur_card)
        dc_layout.setContentsMargins(12, 10, 12, 10)
        dc_layout.setSpacing(6)

        lbl2 = QLabel("⏳ Duration")
        lbl2.setStyleSheet("color: #CCCCCC; font-size: 12px; font-weight: bold; background: transparent; border: none;")

        h2 = QHBoxLayout()
        h2.setSpacing(4)
        h2.setContentsMargins(0, 0, 0, 0)
        self.dur_hour = AnimatedSpinbox(0, 23, 0, unit="h", right_margin=2)
        colon2 = QLabel(":")
        colon2.setStyleSheet("color: #FFB300; font-family: 'FreeSerif', 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif; font-weight: bold; font-size: 16px; background: transparent; border: none;")
        colon2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dur_min = AnimatedSpinbox(0, 59, 25, unit="min", right_margin=6)

        h2.addWidget(self.dur_hour)
        h2.addWidget(colon2)
        h2.addWidget(self.dur_min)

        dc_layout.addWidget(lbl2)
        dc_layout.addLayout(h2)

        time_main_layout.addWidget(start_card)
        time_main_layout.addWidget(dur_card)

        layout.addLayout(time_main_layout)

        self.time_error_lbl = QLabel("")
        self.time_error_lbl.setWordWrap(True)
        self.time_error_lbl.setStyleSheet(
            "color: #FF5555; font-size: 12px; font-weight: bold; background: transparent; border: none;"
        )
        self.time_error_lbl.hide()
        layout.addWidget(self.time_error_lbl)

    def _build_sites_section(self, layout):
        lbl = QLabel("🛡️ Blocked Websites")
        lbl.setStyleSheet("color: #CCCCCC; font-size: 13px; font-weight: bold;")

        input_layout = QHBoxLayout()
        self.site_entry = AnimatedLineEdit("e.g. youtube.com")
        self.site_entry.setFixedHeight(38)

        add_btn = AnimatedAddButton("Add")
        add_btn.setFixedSize(68, 38)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self.add_site_item)

        input_layout.addWidget(self.site_entry)
        input_layout.addWidget(add_btn)

        self.scroll_area = SmoothScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMaximumHeight(90)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: 1px solid #222222;
                border-radius: 18px;
            }
            QScrollBar:vertical {
                background: #0a0a0a;
                width: 8px;
                margin: 4px 2px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #777777, stop:1 #444444);
                min-height: 25px;
                border-radius: 4px;
                border: none;
            }
            QScrollBar::handle:vertical:hover {
                background: #999999;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        self.sites_container = QFrame()
        self.sites_container.setStyleSheet("""
            QFrame {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0a0a0a, stop:1 #000000);
                border: none;
                border-radius: 18px;
            }
        """)
        self.sites_layout = FlowLayout(self.sites_container, margin=8, hSpacing=8, vSpacing=8)

        self.empty_sites_lbl = QLabel("No websites blocked yet")
        self.empty_sites_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_sites_lbl.setStyleSheet("color: #555555; font-size: 12px; font-style: italic; background: transparent; border: none;")
        self.sites_layout.addWidget(self.empty_sites_lbl)

        self.scroll_area.setWidget(self.sites_container)

        layout.addWidget(lbl)
        layout.addLayout(input_layout)
        layout.addWidget(self.scroll_area)

    def add_site_item(self):
        raw_site = self.site_entry.text().strip()
        site = self.sites_helper.clean_url(raw_site)
        if site and site not in self.blocked_sites_list:
            if not self.blocked_sites_list:
                self.sites_layout.removeWidget(self.empty_sites_lbl)
                self.empty_sites_lbl.hide()
            self.blocked_sites_list.append(site)
            self.site_entry.clear()
            chip = AnimatedChip(site, self.remove_site_chip, self.sites_container)
            self.sites_layout.addWidget(chip)
            self.sites_container.updateGeometry()

    def remove_site_chip(self, chip_widget):
        if chip_widget.site_name in self.blocked_sites_list:
            self.blocked_sites_list.remove(chip_widget.site_name)
        self.sites_layout.removeWidget(chip_widget)
        chip_widget.deleteLater()
        if not self.blocked_sites_list:
            self.sites_layout.addWidget(self.empty_sites_lbl)
            self.empty_sites_lbl.show()
        self.sites_container.updateGeometry()

    def _build_priority_section(self, layout):
        lbl = QLabel("⚡ Priority")
        lbl.setStyleSheet("color: #CCCCCC; font-size: 13px; font-weight: bold;")

        p_layout = QHBoxLayout()
        self.btn_high = AnimatedPriorityButton("High", "#FF5555", self)
        self.btn_med = AnimatedPriorityButton("Medium", "#FFB300", self)
        self.btn_low = AnimatedPriorityButton("Low", "#2ECC71", self)

        self.btn_high.clicked.connect(lambda: self.set_priority("High"))
        self.btn_med.clicked.connect(lambda: self.set_priority("Medium"))
        self.btn_low.clicked.connect(lambda: self.set_priority("Low"))

        p_layout.addWidget(self.btn_high)
        p_layout.addWidget(self.btn_med)
        p_layout.addWidget(self.btn_low)

        layout.addWidget(lbl)
        layout.addLayout(p_layout)
        self.set_priority("Medium")

    def set_priority(self, p):
        self.selected_priority = p
        self.btn_high.set_selected(p == "High")
        self.btn_med.set_selected(p == "Medium")
        self.btn_low.set_selected(p == "Low")

    def _build_submit_button(self, layout):
        if self.read_only:
            btn_text = "👁 View Only"
        elif self.edit_mode:
            btn_text = "💾 Save Changes"
        elif self.retry_mode:
            btn_text = "🔄 Retry Task"
        else:
            btn_text = "+ Add Task"
        save_btn = AnimatedSubmitButton(btn_text)
        save_btn.setFixedHeight(42)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if self.read_only:
            save_btn.setEnabled(False)
            save_btn.setStyleSheet(save_btn.styleSheet().replace(
                "background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFE600, stop:1 #FF8C00);",
                "background-color: #333333;"
            ).replace("color: #000000;", "color: #888888;"))
        else:
            save_btn.clicked.connect(self.save)
        layout.addWidget(save_btn)

    def _check_time_overlap(self, time_obj):
        new_start = time_obj.start_datetime
        new_end = new_start + timedelta(seconds=time_obj.duration_total_seconds)
        conflicts = []
        for start, end, name in self.existing_tasks:
            if new_start < end and start < new_end:
                conflicts.append((name, start, end))
        return conflicts

    def save(self):
        self.time_error_lbl.hide()
        self.time_error_lbl.setText("")

        time_obj = Time(
            self.start_hour.get_value(),
            self.start_min.get_value(),
            0,
            self.dur_hour.get_value(),
            self.dur_min.get_value(),
            0
        )

        conflicts = self._check_time_overlap(time_obj)
        if conflicts:
            conflict_text = ", ".join(
                f"\"{name}\" ({start.strftime('%H:%M')}–{end.strftime('%H:%M')})"
                for name, start, end in conflicts
            )
            self.time_error_lbl.setText(f"⏰ Conflicts with {conflict_text} — pick another slot")
            self.time_error_lbl.show()
            return

        typed_name = self.name_entry.text().strip()
        if not typed_name:
            n = 1
            while f"Task {n}" in self.existing_names:
                n += 1
            typed_name = f"Task {n}"

        name_obj = Name(typed_name)

        priority_obj = Priority(self.selected_priority)

        data = {
            "name": name_obj.name,
            "description": self.desc_text.toPlainText().strip(),
            "start_hour": time_obj.start_hour,
            "start_min": time_obj.start_minute,
            "dur_hour": time_obj.duration_hours,
            "dur_min": time_obj.duration_minutes,
            "sites": self.blocked_sites_list,
            "priority": priority_obj.priority
        }

        if self.edit_mode and self.on_edit_callback:
            self.on_edit_callback(data)
        else:
            self.on_save_callback(name_obj, time_obj, priority_obj, self.blocked_sites_list)
        self.close()