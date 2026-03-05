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
        self.v.setContentsMargins(20, 18, 20, 18)
        self.v.setSpacing(0)

        # ---- Título ----
        top = QHBoxLayout()
        top.setSpacing(10)
        self.title_lbl = QLabel(title)
        self.title_lbl.setFont(QFont("Segoe UI", 17, QFont.DemiBold))
        top.addWidget(self.title_lbl, 1)
        self.v.addLayout(top)
        self.v.addSpacing(6)

        # ---- Divider (1px, theme card_border) ----
        self.title_rule = QFrame()
        self.title_rule.setObjectName("title_rule")
        self.title_rule.setFixedHeight(1)
        self.v.addWidget(self.title_rule)
        self.v.addSpacing(10)

        # ---- Content grid (spacing 12px, stretch 1) ----
        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(12)
        self.grid.setVerticalSpacing(12)
        self.v.addLayout(self.grid, 1)

    def set_theme(self, theme: dict):
        self._theme = theme or {}
        apply_shadow(
            self,
            blur=24,
            y=4,
            rgba=self._theme.get("shadow_color", (0, 0, 0, 80)),
        )

        self.setStyleSheet(f"""
            QFrame#card {{
                background: {self._theme.get("card_bg", "#2b2b2b")};
                border: 1px solid {self._theme.get("card_border", "#3a3a3a")};
                border-radius: 22px;
            }}
        """)

        # Título
        self.title_lbl.setStyleSheet(f"""
            color: {self._theme.get("text", "#ffffff")};
            background: transparent;
            border: 0;
            padding: 0;
        """)

        # Divider: 1px, theme card_border
        border = self._theme.get("card_border", "#3a3a3a")
        self.title_rule.setStyleSheet(f"""
            QFrame#title_rule {{
                background: {border};
                border: 0;
            }}
        """)
