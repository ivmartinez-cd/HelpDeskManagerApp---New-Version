# pyside_ui/widgets/modern_checkbox.py
from __future__ import annotations

from PySide6.QtCore import Qt, QRectF, QSize, Signal, Property, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QFont, QPaintEvent
from PySide6.QtWidgets import QWidget, QSizePolicy


class ModernCheckBox(QWidget):
    toggled = Signal(bool)

    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)
        self._text = text
        self._checked = False
        self._hover = False
        self._pressed = False
        self._theme: dict = {}

        self._box_size = 20
        self._box_radius = 6
        self._gap = 10
        self._pad_v = 6

        self._check_progress = 0
        self._anim = QPropertyAnimation(self, b"checkProgress", self)
        self._anim.setDuration(140)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)

        # IMPORTANTE: que no lo achique el layout
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        self.setMinimumHeight(self._box_size + self._pad_v * 2)

        self._recompute_min_width()

    # -------- Theme / Text --------
    def set_theme(self, theme: dict) -> None:
        self._theme = theme or {}
        self.update()

    def setText(self, text: str) -> None:
        self._text = text
        self._recompute_min_width()
        self.update()

    def _recompute_min_width(self) -> None:
        fm = self.fontMetrics()
        text_w = fm.horizontalAdvance(self._text) if self._text else 0
        w = self._box_size + self._gap + text_w + 24
        self.setMinimumWidth(max(220, w))  # 220 evita cortes típicos en footer

    # -------- Checked API --------
    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, on: bool, emit: bool = False) -> None:
        on = bool(on)
        if on == self._checked:
            return
        self._checked = on
        self._start_anim(on)
        if emit:
            self.toggled.emit(on)
        self.update()

    def toggle(self) -> None:
        self.setChecked(not self._checked, emit=True)

    # -------- Animation property --------
    def _get_checkProgress(self) -> int:
        return int(self._check_progress)

    def _set_checkProgress(self, v: int) -> None:
        self._check_progress = int(v)
        self.update()

    checkProgress = Property(int, _get_checkProgress, _set_checkProgress)

    def _start_anim(self, checked: bool) -> None:
        self._anim.stop()
        self._anim.setStartValue(self._check_progress)
        self._anim.setEndValue(100 if checked else 0)
        self._anim.start()

    # -------- Sizing --------
    def sizeHint(self) -> QSize:
        fm = self.fontMetrics()
        text_w = fm.horizontalAdvance(self._text) if self._text else 0
        w = self._box_size + self._gap + text_w + 24
        h = self._box_size + self._pad_v * 2
        return QSize(max(220, w), h)

    # -------- Events --------
    def enterEvent(self, _e) -> None:
        self._hover = True
        self.update()

    def leaveEvent(self, _e) -> None:
        self._hover = False
        self._pressed = False
        self.update()

    def mousePressEvent(self, e) -> None:
        if e.button() == Qt.LeftButton:
            self._pressed = True
            self.update()

    def mouseReleaseEvent(self, e) -> None:
        if self._pressed and e.button() == Qt.LeftButton:
            self._pressed = False
            if self.rect().contains(e.position().toPoint()):
                self.toggle()
            self.update()

    # -------- Paint --------
    def paintEvent(self, _e: QPaintEvent) -> None:
        t = self._theme or {}

        text_col = QColor(t.get("text", "#EAEAEA"))
        muted = QColor(t.get("muted", "#B8B8B8"))
        border = QColor(t.get("card_border", "#3A3A3A"))
        fill_checked = QColor(t.get("orange", "#FF9A2E"))
        hover_bg = QColor(t.get("btn_hover", "#333333"))

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)

        # Hover/Pressed background (sutil)
        if self._pressed:
            c = QColor(hover_bg); c.setAlpha(130)
            p.setBrush(QBrush(c)); p.setPen(Qt.NoPen)
            p.drawRoundedRect(QRectF(0, 0, self.width(), self.height()), 10, 10)
        elif self._hover:
            c = QColor(hover_bg); c.setAlpha(80)
            p.setBrush(QBrush(c)); p.setPen(Qt.NoPen)
            p.drawRoundedRect(QRectF(0, 0, self.width(), self.height()), 10, 10)

        # Box
        x = 0
        y = (self.height() - self._box_size) / 2
        box = QRectF(x, y, self._box_size, self._box_size)

        pen = QPen(border); pen.setWidth(2)
        p.setPen(pen)

        progress = self._check_progress / 100.0
        if progress > 0:
            c = QColor(fill_checked)
            c.setAlpha(int(255 * min(1.0, 0.35 + progress * 0.65)))
            p.setBrush(QBrush(c))
        else:
            p.setBrush(Qt.NoBrush)

        p.drawRoundedRect(box, self._box_radius, self._box_radius)

        # Checkmark
        if progress > 0:
            check_pen = QPen(QColor("#FFFFFF"))
            check_pen.setWidth(3)
            check_pen.setCapStyle(Qt.RoundCap)
            check_pen.setJoinStyle(Qt.RoundJoin)
            p.setPen(check_pen)

            x1 = box.left() + 5
            y1 = box.top() + 11
            x2 = box.left() + 9
            y2 = box.top() + 15
            x3 = box.left() + 16
            y3 = box.top() + 6

            if progress < 0.5:
                k = progress / 0.5
                xa = x1 + (x2 - x1) * k
                ya = y1 + (y2 - y1) * k
                p.drawLine(int(x1), int(y1), int(xa), int(ya))
            else:
                p.drawLine(int(x1), int(y1), int(x2), int(y2))
                k = (progress - 0.5) / 0.5
                xb = x2 + (x3 - x2) * k
                yb = y2 + (y3 - y2) * k
                p.drawLine(int(x2), int(y2), int(xb), int(yb))

        # Text
        p.setPen(text_col if self.isEnabled() else muted)
        p.setFont(QFont("Segoe UI", 11, QFont.DemiBold))
        tx = self._box_size + self._gap
        p.drawText(QRectF(tx, 0, self.width() - tx, self.height()),
                   Qt.AlignVCenter | Qt.AlignLeft, self._text)

        p.end()
