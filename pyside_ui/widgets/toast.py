from __future__ import annotations

from collections import deque
from PySide6 import QtCore, QtWidgets


class Toast(QtWidgets.QFrame):
    closed = QtCore.Signal()

    def __init__(self, parent, level: str, title: str, message: str, timeout_ms: int = 3000):
        super().__init__(parent, QtCore.Qt.ToolTip)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.ToolTip)

        color = {
            "success": "#2ecc71",
            "warning": "#f1c40f",
            "error": "#e74c3c",
            "info": "#3498db",
        }.get(level, "#3498db")

        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(4)

        lbl_title = QtWidgets.QLabel(title)
        lbl_title.setStyleSheet("font-weight: 600; color: white;")
        lbl_msg = QtWidgets.QLabel(message)
        lbl_msg.setStyleSheet("color: #eee;")
        lbl_msg.setWordWrap(True)

        lay.addWidget(lbl_title)
        lay.addWidget(lbl_msg)

        self.setStyleSheet(
            f"""
            QFrame {{
                background: {color};
                border-radius: 8px;
            }}
            """
        )

        self.adjustSize()
        QtCore.QTimer.singleShot(timeout_ms, self._close)

    def _close(self):
        self.close()

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)


class ToastManager(QtCore.QObject):
    MARGIN = 20
    FIRST_TOAST_EXTRA_MS = 2000  # +2s solo para el primero

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self._parent = parent
        self._queue: deque[tuple] = deque()
        self._current: Toast | None = None

    def show(self, level: str, title: str, message: str, timeout_ms: int = 3000):
        # ✅ PRIORIDAD: resultados finales de FTP (evita desfasaje con los diálogos siguientes)
        # - success/warning/error con título "FTP" se muestran inmediatamente
        # - cortan la cola y cierran el toast actual
        if title.strip().lower() == "ftp" and level in ("success", "warning", "error"):
            self._show_priority(level, title, message, timeout_ms)
            return

        self._queue.append((level, title, message, timeout_ms))
        if self._current is None:
            self._show_next(first=True)

    def _show_priority(self, level: str, title: str, message: str, timeout_ms: int):
        # Limpia cola y fuerza a mostrar YA
        self._queue.clear()

        if self._current is not None:
            try:
                self._current.closed.disconnect(self._on_toast_closed)
            except Exception:
                pass
            try:
                self._current.close()
            except Exception:
                pass
            self._current = None

        self._show_toast(level, title, message, timeout_ms, first=False)

    def _show_next(self, first: bool = False):
        if not self._queue:
            self._current = None
            return

        level, title, message, timeout_ms = self._queue.popleft()
        self._show_toast(level, title, message, timeout_ms, first=first)

    def _show_toast(self, level: str, title: str, message: str, timeout_ms: int, *, first: bool):
        if first:
            timeout_ms += self.FIRST_TOAST_EXTRA_MS

        toast = Toast(self._parent, level, title, message, timeout_ms)
        toast.closed.connect(self._on_toast_closed)

        geo = self._parent.geometry()
        x = geo.x() + geo.width() - toast.width() - self.MARGIN
        y = geo.y() + self.MARGIN
        toast.move(x, y)

        self._current = toast
        toast.show()

    def _on_toast_closed(self):
        self._current = None
        self._show_next(first=False)
