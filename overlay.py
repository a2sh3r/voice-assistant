from __future__ import annotations

from PyQt5.QtCore import Qt, QPoint, QRectF, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QPainterPath
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

_MAX_MESSAGES = 20

_STYLE_WINDOW = """
    QWidget#overlay_root {
        background: transparent;
    }
"""


_COLOR_USER = "#e0e0e0"
_COLOR_ASSISTANT = "#7ec8e3"
_COLOR_LABEL_USER = "#aaaaaa"
_COLOR_LABEL_ASSISTANT = "#5aabcb"


class _MessageWidget(QWidget):
    """Single chat bubble displayed in the overlay."""

    def __init__(self, role: str, text: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(1)

        is_user = role == "user"
        label_text = "Ты" if is_user else "Бот"
        label_color = _COLOR_LABEL_USER if is_user else _COLOR_LABEL_ASSISTANT
        text_color = _COLOR_USER if is_user else _COLOR_ASSISTANT

        role_label = QLabel(label_text)
        role_label.setStyleSheet(
            f"color: {label_color}; font-size: 10px; font-weight: bold; background: transparent;"
        )

        text_label = QLabel(text)
        text_label.setWordWrap(True)
        text_label.setStyleSheet(
            f"color: {text_color}; font-size: 13px; background: transparent;"
        )
        text_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        layout.addWidget(role_label)
        layout.addWidget(text_label)


class _ScrollContent(QWidget):
    """Inner widget that holds all message widgets."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 6, 0, 6)
        self._layout.setSpacing(6)
        self._layout.addStretch()
        self.setStyleSheet("background: transparent;")

    def add_message(self, role: str, text: str) -> None:
        widget = _MessageWidget(role, text)
        self._layout.addWidget(widget)

    def clear_messages(self) -> None:
        while self._layout.count() > 1:
            item = self._layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()


class _RoundedContainer(QWidget):
    """Painted rounded-corner semi-transparent background."""

    def paintEvent(self, _event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect().adjusted(0, 0, -1, -1)), 12, 12)
        painter.fillPath(path, QColor(20, 20, 20, 185))


_FLAGS_LOCKED = (
    Qt.FramelessWindowHint
    | Qt.WindowStaysOnTopHint
    | Qt.WindowTransparentForInput
    | Qt.Window
)
_FLAGS_UNLOCKED = Qt.Window


class OverlayWindow(QWidget):
    """
    Semi-transparent, always-on-top overlay that displays conversation history.

    Two modes:
      - Locked (default): click-through, stays on top, no interaction.
      - Unlocked: draggable by mouse. Toggle with toggle_lock().

    Thread-safe: all public methods emit Qt signals dispatched on the GUI thread.
    """

    _sig_push = pyqtSignal(str, str)
    _sig_clear = pyqtSignal()
    _sig_toggle_visible = pyqtSignal()
    _sig_toggle_lock = pyqtSignal()
    _sig_loading = pyqtSignal(bool)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Voice Assistant Overlay")
        self.setObjectName("overlay_root")
        self._locked = True
        self._drag_pos: QPoint | None = None

        self.setWindowFlags(_FLAGS_LOCKED)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setStyleSheet(_STYLE_WINDOW)

        self._build_ui()
        self._position_window()

        self._sig_push.connect(self._on_push)
        self._sig_clear.connect(self._on_clear)
        self._sig_toggle_visible.connect(self._on_toggle_visible)
        self._sig_toggle_lock.connect(self._on_toggle_lock)
        self._sig_loading.connect(self._on_loading)

        self._spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self._spinner_idx = 0
        self._spinner_timer = QTimer(self)
        self._spinner_timer.timeout.connect(self._tick_spinner)

    def push_message(self, role: str, text: str) -> None:
        self._sig_push.emit(role, text)

    def clear(self) -> None:
        self._sig_clear.emit()

    def toggle_visibility(self) -> None:
        self._sig_toggle_visible.emit()

    def toggle_lock(self) -> None:
        self._sig_toggle_lock.emit()

    def set_loading(self, active: bool) -> None:
        self._sig_loading.emit(active)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if not self._locked and event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event) -> None:  # type: ignore[override]
        if not self._locked and self._drag_pos and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[override]
        self._drag_pos = None

    def _on_push(self, role: str, text: str) -> None:
        self._content.add_message(role, text)
        self._trim_messages()
        self._scroll.verticalScrollBar().setValue(
            self._scroll.verticalScrollBar().maximum()
        )

    def _on_clear(self) -> None:
        self._content.clear_messages()

    def _on_toggle_visible(self) -> None:
        if self.isVisible():
            self.hide()
        else:
            self.show()

    def _on_loading(self, active: bool) -> None:
        if active:
            self._spinner_idx = 0
            self._spinner_label.setText(f"{self._spinner_frames[0]}  думаю...")
            self._spinner_label.setVisible(True)
            self._spinner_timer.start(80)
        else:
            self._spinner_timer.stop()
            self._spinner_label.setVisible(False)

    def _tick_spinner(self) -> None:
        self._spinner_idx = (self._spinner_idx + 1) % len(self._spinner_frames)
        self._spinner_label.setText(f"{self._spinner_frames[self._spinner_idx]}  думаю...")

    def _on_toggle_lock(self) -> None:
        self._locked = not self._locked
        flags = _FLAGS_LOCKED if self._locked else _FLAGS_UNLOCKED
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_ShowWithoutActivating, self._locked)
        self.show()
        status = "заблокирован/click-through" if self._locked else "обычное окно (можно скейлить/тайлить)"
        print(f"Оверлей {status}")

    def _build_ui(self) -> None:
        self.resize(420, 340)
        self.setMinimumSize(280, 120)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._container = _RoundedContainer(self)
        container_layout = QVBoxLayout(self._container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
            "QScrollBar:vertical { width: 4px; background: transparent; }"
            "QScrollBar::handle:vertical { background: rgba(255,255,255,60); border-radius: 2px; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
        )

        self._content = _ScrollContent()
        self._scroll.setWidget(self._content)

        self._spinner_label = QLabel("")
        self._spinner_label.setAlignment(Qt.AlignCenter)
        self._spinner_label.setStyleSheet(
            "color: #7ec8e3; font-size: 15px; background: transparent; padding: 4px 0;"
        )
        self._spinner_label.setVisible(False)

        container_layout.addWidget(self._scroll)
        container_layout.addWidget(self._spinner_label)
        outer.addWidget(self._container)

    def _position_window(self) -> None:
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.right() - self.width() - 20, screen.bottom() - self.height() - 40)

    def _trim_messages(self) -> None:
        layout = self._content._layout
        msg_count = layout.count() - 1
        while msg_count > _MAX_MESSAGES:
            item = layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()
            msg_count -= 1
