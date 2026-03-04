# pyside_ui/widgets/controls.py
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QPushButton


def make_big_button(text: str, theme: dict) -> QPushButton:
    b = QPushButton(text)
    b.setCursor(Qt.PointingHandCursor)
    b.setMinimumHeight(62)
    b.setFont(QFont("Segoe UI", 12, QFont.DemiBold))
    b.setStyleSheet(_big_btn_qss(theme))
    return b


def update_big_button(btn: QPushButton, theme: dict) -> None:
    btn.setStyleSheet(_big_btn_qss(theme))


def _big_btn_qss(theme: dict) -> str:
    return f"""
        QPushButton {{
            background: {theme["btn_bg"]};
            color: {theme["text"]};
            border: 1px solid {theme["card_border"]};
            border-radius: 18px;
            padding: 10px 12px;
        }}
        QPushButton:hover {{
            background: {theme["btn_hover"]};
        }}
        QPushButton:pressed {{
            background: {theme["btn_hover"]};
        }}
    """
