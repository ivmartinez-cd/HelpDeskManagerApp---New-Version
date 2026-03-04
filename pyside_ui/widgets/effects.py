# pyside_ui/widgets/effects.py
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QWidget


def apply_shadow(widget: QWidget, blur: int, y: int, rgba: tuple[int, int, int, int]) -> None:
    eff = QGraphicsDropShadowEffect(widget)
    eff.setBlurRadius(blur)
    eff.setOffset(0, y)
    eff.setColor(QColor(*rgba))
    widget.setGraphicsEffect(eff)
