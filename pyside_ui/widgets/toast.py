# pyside_ui/widgets/toast.py
from __future__ import annotations

from collections import deque
from typing import Optional

from PySide6 import QtCore, QtWidgets, QtGui


def _toast_level_data() -> dict:
    """Configuración de iconos y colores por nivel."""
    return {
        "success": {"color": "#2ecc71", "icon": "✔️"},
        "warning": {"color": "#f1c40f", "icon": "⚠️"},
        "error": {"color": "#e74c3c", "icon": "❌"},
        "info": {"color": "#3498db", "icon": "ℹ️"},
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
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.WindowType.ToolTip | QtCore.Qt.WindowType.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        # 🎨 Datos de nivel
        level_info = _toast_level_data().get(level, _toast_level_data()["info"])
        accent_color = level_info["color"]
        icon_text = level_info["icon"]
        
        # Estructura Principal
        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # El contenedor con estilo
        self.container = QtWidgets.QFrame()
        self.container.setObjectName("ToastContainer")
        self.container.setFixedWidth(340)
        
        # Sombra
        shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QtGui.QColor(0, 0, 0, 120))
        shadow.setOffset(0, 4)
        self.container.setGraphicsEffect(shadow)
        
        container_lay = QtWidgets.QHBoxLayout(self.container)
        container_lay.setContentsMargins(0, 0, 16, 0)
        container_lay.setSpacing(12)
        
        # 1. Barra de color lateral
        self.accent_bar = QtWidgets.QFrame()
        self.accent_bar.setFixedWidth(6)
        self.accent_bar.setStyleSheet(f"background: {accent_color}; border-top-left-radius: 12px; border-bottom-left-radius: 12px;")
        container_lay.addWidget(self.accent_bar)
        
        # 2. Icono
        self.icon_lbl = QtWidgets.QLabel(icon_text)
        self.icon_lbl.setStyleSheet("font-size: 20px; background: transparent;")
        container_lay.addWidget(self.icon_lbl)
        
        # 3. Textos
        text_lay = QtWidgets.QVBoxLayout()
        text_lay.setContentsMargins(0, 12, 0, 12)
        text_lay.setSpacing(2)
        
        title_color = (theme or {}).get("text", "#FFFFFF")
        msg_color = (theme or {}).get("muted", "#B0B0B0")
        
        self.lbl_title = QtWidgets.QLabel(title.upper())
        font_t = QtGui.QFont("Segoe UI", 11, QtGui.QFont.Weight.Bold)
        font_t.setPointSizeF(10.5) # ✅ Blindaje anti-warning
        self.lbl_title.setFont(font_t)
        self.lbl_title.setStyleSheet(f"color: {title_color}; letter-spacing: 1px; background: transparent;")
        
        self.lbl_msg = QtWidgets.QLabel(message)
        self.lbl_msg.setWordWrap(True)
        font_m = QtGui.QFont("Segoe UI", 10)
        font_m.setPointSizeF(10) # ✅ Blindaje anti-warning
        self.lbl_msg.setFont(font_m)
        self.lbl_msg.setStyleSheet(f"color: {msg_color}; background: transparent;")
        
        text_lay.addWidget(self.lbl_title)
        text_lay.addWidget(self.lbl_msg)
        container_lay.addLayout(text_lay, 1)
        
        # Estilo del contenedor — usa colores del tema activo
        bg_color = (theme or {}).get("surface", "#1E1E1E")
        border_color = (theme or {}).get("card_border", "#333333")
        self.container.setStyleSheet(f"""
            QFrame#ToastContainer {{
                background: {bg_color};
                border: 1px solid {border_color};
                border-radius: 12px;
            }}
        """)
        
        self.main_layout.addWidget(self.container)
        
        # Animación de entrada
        self.setWindowOpacity(0)
        self.anim = QtCore.QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(300)
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
        
        self.adjustSize()
        QtCore.QTimer.singleShot(timeout_ms, self._fade_out)

    def show(self) -> None:
        super().show()
        self.anim.start()

    def _fade_out(self) -> None:
        self.anim.setDirection(QtCore.QPropertyAnimation.Direction.Backward)
        self.anim.finished.connect(self._close)
        self.anim.start()

    def _close(self) -> None:
        self.close()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.closed.emit()
        super().closeEvent(event)


class ToastManager(QtCore.QObject):
    MARGIN = 24

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self._parent = parent
        self._queue: deque[tuple] = deque()
        self._current: Toast | None = None

    def _get_theme(self) -> Optional[dict]:
        try:
            w = self._parent.window()
            t = getattr(w, "theme", None)
            return t if isinstance(t, dict) else None
        except Exception:
            return None

    def show(self, level: str, title: str, message: str, timeout_ms: int = 3000) -> None:
        # Prioridad FTP
        if title.strip().lower() == "ftp" and level in ("success", "warning", "error"):
            self._show_priority(level, title, message, timeout_ms)
            return

        self._queue.append((level, title, message, timeout_ms))
        if self._current is None:
            self._show_next()

    def _show_priority(self, level: str, title: str, message: str, timeout_ms: int) -> None:
        self._queue.clear()
        if self._current is not None:
            try: self._current.closed.disconnect(self._show_next)
            except Exception: pass
            self._current.close()
            self._current = None
        self._show_toast(level, title, message, timeout_ms)

    def _show_next(self) -> None:
        if not self._queue:
            self._current = None
            return
        level, title, message, timeout_ms = self._queue.popleft()
        self._show_toast(level, title, message, timeout_ms)

    def _show_toast(self, level: str, title: str, message: str, timeout_ms: int) -> None:
        theme = self._get_theme()
        toast = Toast(self._parent, level, title, message, timeout_ms, theme=theme)
        toast.closed.connect(self._show_next)

        win = self._parent.window()
        if win:
            geo = win.geometry()
            # Posición: Inferior Derecha (estilo moderno)
            tx = geo.right() - toast.width() - self.MARGIN
            ty = geo.bottom() - toast.height() - self.MARGIN
            toast.move(tx, ty)
        
        self._current = toast
        toast.show()
