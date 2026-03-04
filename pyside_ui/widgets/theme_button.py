# pyside_ui/widgets/theme_button.py
from __future__ import annotations

from PySide6.QtCore import Qt, QRectF, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QPaintEvent
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainterPath



class ThemeIconButton(QWidget):
    """
    Botón circular sol/luna (icon-only).
    - Muestra SOL si el tema actual es claro
    - Muestra LUNA si el tema actual es oscuro
    - Click: emite toggled(bool) donde True=light, False=dark (nuevo estado)
    """
    toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(44, 44)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)

        self._theme: dict = {}
        self._is_light = False
        self._hover = False
        self._pressed = False

    def set_theme(self, theme: dict):
        self._theme = theme or {}
        self.update()

    def set_light(self, on: bool, emit: bool = False):
        on = bool(on)
        if on == self._is_light:
            return
        self._is_light = on
        if emit:
            self.toggled.emit(on)
        self.update()

    def enterEvent(self, _e):
        self._hover = True
        self.update()

    def leaveEvent(self, _e):
        self._hover = False
        self._pressed = False
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._pressed = True
            self.update()

    def mouseReleaseEvent(self, e):
        if self._pressed and e.button() == Qt.LeftButton:
            self._pressed = False
            if self.rect().contains(e.position().toPoint()):
                # togglear al estado opuesto
                self.set_light(not self._is_light, emit=True)
            self.update()

    def paintEvent(self, _e: QPaintEvent):
        t = self._theme or {}

        border = QColor(t.get("card_border", "#3A3A3A"))
        bg = QColor(t.get("pill_bg", "#2D2D2D"))  # fondo del botón
        orange = QColor(t.get("orange", "#FF9A2E"))
        text = QColor(t.get("text", "#EAEAEA"))
        muted = QColor(t.get("muted", "#B8B8B8"))

        # Estados hover/pressed (muy sutil)
        if self._pressed:
            c = QColor(bg)
            c = c.darker(115)
            bg_state = c
        elif self._hover:
            c = QColor(bg)
            c = c.lighter(112)
            bg_state = c
        else:
            bg_state = bg

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)

        # Círculo base
        r = QRectF(3, 3, self.width() - 6, self.height() - 6)
        p.setBrush(QBrush(bg_state))
        p.setPen(QPen(border, 1))
        p.drawEllipse(r)

        # Icono
        icon_rect = QRectF(12, 12, self.width() - 24, self.height() - 24)

        if self._is_light:
            # SOL (cuando está en modo claro)
            p.setPen(QPen(orange, 2))
            self._draw_sun(p, icon_rect)
        else:
            # LUNA (cuando está en modo oscuro)
            p.setPen(QPen(text, 2))
            self._draw_moon(p, icon_rect)



        p.end()

    def _draw_sun(self, p: QPainter, r: QRectF):
        cx, cy = r.center().x(), r.center().y()
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QRectF(cx - 5, cy - 5, 10, 10))

        import math
        for i in range(8):
            a = i * (2 * math.pi / 8)
            x1 = cx + 7 * math.cos(a)
            y1 = cy + 7 * math.sin(a)
            x2 = cx + 11 * math.cos(a)
            y2 = cy + 11 * math.sin(a)
            p.drawLine(int(x1), int(y1), int(x2), int(y2))

    def _draw_moon(self, p: QPainter, r: QRectF):
        """
        Luna real (crescent) usando QPainterPath.
        Geométricamente correcta, sin hacks.
        """
        cx, cy = r.center().x(), r.center().y()

        outer = QPainterPath()
        outer.addEllipse(QRectF(cx - 6.5, cy - 6.5, 13, 13))

        inner = QPainterPath()
        inner.addEllipse(QRectF(cx - 2.5, cy - 6.5, 13, 13))

        crescent = outer.subtracted(inner)

        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor("#FFFFFF")))
        p.drawPath(crescent)
