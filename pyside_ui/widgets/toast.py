from __future__ import annotations

from collections import deque
from typing import Optional

from PySide6 import QtCore, QtWidgets


def _toast_level_colors() -> dict:
    """Colores por nivel cuando no hay theme (comportamiento actual)."""
    return {
        "success": "#2ecc71",
        "warning": "#f1c40f",
        "error": "#e74c3c",
        "info": "#3498db",
    }


class Toast(QtWidgets.QFrame):
    closed = QtCore.Signal()

    def __init__(
        self,
        parent: QtWidgets.QWidget,
        level: str,
        title: str,
        message: str,
        timeout_ms: int = 3000,
        theme: Optional[dict] = None,
    ):
        super().__init__(parent, QtCore.Qt.ToolTip)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.ToolTip)

        level_colors = _toast_level_colors()
        color = level_colors.get(level, level_colors["info"])

        if theme:
            title_color = theme.get("text", "#FFFFFF")
            msg_color = theme.get("muted", "#EEEEEE")
        else:
            title_color = "#FFFFFF"
            msg_color = "#EEEEEE"

        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(4)

        lbl_title = QtWidgets.QLabel(title)
        lbl_title.setStyleSheet(f"font-weight: 600; color: {title_color};")
        lbl_msg = QtWidgets.QLabel(message)
        lbl_msg.setStyleSheet(f"color: {msg_color};")
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

    def _close(self) -> None:
        self.close()

    def closeEvent(self, event: QtCore.QEvent) -> None:
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

    def _get_theme(self) -> Optional[dict]:
        """Obtiene el tema de la ventana si está disponible."""
        try:
            w = self._parent.window()
            t = getattr(w, "theme", None)
            return t if isinstance(t, dict) else None
        except Exception:
            return None

    def show(self, level: str, title: str, message: str, timeout_ms: int = 3000) -> None:
        # ✅ PRIORIDAD: resultados finales de FTP (evita desfasaje con los diálogos siguientes)
        # - success/warning/error con título "FTP" se muestran inmediatamente
        # - cortan la cola y cierran el toast actual
        if title.strip().lower() == "ftp" and level in ("success", "warning", "error"):
            self._show_priority(level, title, message, timeout_ms)
            return

        self._queue.append((level, title, message, timeout_ms))
        if self._current is None:
            self._show_next(first=True)

    def _show_priority(self, level: str, title: str, message: str, timeout_ms: int) -> None:
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

    def _show_next(self, first: bool = False) -> None:
        if not self._queue:
            self._current = None
            return

        level, title, message, timeout_ms = self._queue.popleft()
        self._show_toast(level, title, message, timeout_ms, first=first)

    def _show_toast(self, level: str, title: str, message: str, timeout_ms: int, *, first: bool) -> None:
        if first:
            timeout_ms += self.FIRST_TOAST_EXTRA_MS

        theme = self._get_theme()
        toast = Toast(self._parent, level, title, message, timeout_ms, theme=theme)
        toast.closed.connect(self._on_toast_closed)

        geo = self._parent.geometry()
        x = geo.x() + geo.width() - toast.width() - self.MARGIN
        y = geo.y() + self.MARGIN
        toast.move(x, y)

        self._current = toast
        toast.show()

    def _on_toast_closed(self) -> None:
        self._current = None
        self._show_next(first=False)
