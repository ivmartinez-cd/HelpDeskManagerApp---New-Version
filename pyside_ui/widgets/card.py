# pyside_ui/widgets/card.py
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QHBoxLayout, QGridLayout

from .effects import apply_shadow


class Card(QFrame):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._theme: dict = {}

        self.setObjectName("card")
        self.setMinimumHeight(360)

        self.v = QVBoxLayout(self)
        self.v.setContentsMargins(24, 20, 24, 20)
        self.v.setSpacing(0)

        # ---- Título ----
        top = QHBoxLayout()
        top.setSpacing(10)
        self.title_lbl = QLabel(title)
        font_title = QFont("Segoe UI Variable Display", 17, QFont.DemiBold)
        font_title.setPointSizeF(17)
        self.title_lbl.setFont(font_title)
        top.addWidget(self.title_lbl, 1)
        self.v.addLayout(top)
        self.v.addSpacing(10)

        # ---- Divider ----
        self.title_rule = QFrame(self)
        self.title_rule.setObjectName("title_rule")
        self.title_rule.setFixedHeight(1)
        self.v.addWidget(self.title_rule)
        self.v.addSpacing(16)

        # ---- Content grid (spacing 24px) ----
        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(24)
        self.grid.setVerticalSpacing(24)
        self.v.addLayout(self.grid, 1)

    def set_theme(self, theme: dict):
        self._theme = theme or {}
        apply_shadow(
            self,
            blur=32,
            y=8,
            rgba=self._theme.get("shadow_color", (0, 0, 0, 150)),
        )

        self.setStyleSheet(f"""
            QFrame#card {{
                background: {self._theme.get("card_bg", "#1A1A1A")};
                border: 1px solid {self._theme.get("card_border", "#2A2A2A")};
                border-radius: 24px;
            }}
        """)

        self.title_lbl.setStyleSheet(f"""
            color: {self._theme.get("text", "#F5F5F5")};
            background: transparent;
            font-weight: 700;
            padding-left: 4px;
        """)

        self.title_rule.setStyleSheet(f"""
            QFrame#title_rule {{
                background: {self._theme.get("card_border", "#2A2A2A")};
                border: 0;
                margin: 0 4px;
            }}
        """)
