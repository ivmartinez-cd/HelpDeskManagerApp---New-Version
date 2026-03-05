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
        self.v.setContentsMargins(22, 20, 22, 20)
        self.v.setSpacing(12)

        # ---- Header (solo título) ----
        top = QHBoxLayout()
        top.setSpacing(10)

        self.title_lbl = QLabel(title)
        self.title_lbl.setFont(QFont("Segoe UI", 17, QFont.DemiBold))
        top.addWidget(self.title_lbl, 1)

        self.v.addLayout(top)

        # ---- Subrayado moderno ----
        self.title_rule = QFrame()
        self.title_rule.setObjectName("title_rule")
        self.title_rule.setFixedHeight(2)
        self.v.addWidget(self.title_rule)

        # ---- Content grid (stretch 1: ocupa el espacio restante de la card) ----
        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(16)
        self.grid.setVerticalSpacing(14)
        self.v.addLayout(self.grid, 1)

    def set_theme(self, theme: dict):
        self._theme = theme or {}
        apply_shadow(
            self,
            blur=36,
            y=10,
            rgba=self._theme.get("shadow_color", (0, 0, 0, 120)),
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

        # Underline (fade soft)
        accent = self._theme.get("orange", "#FF9A2E")
        border = self._theme.get("card_border", "#3a3a3a")
        bg = self._theme.get("card_bg", "#2b2b2b")

        self.title_rule.setStyleSheet(f"""
            QFrame#title_rule {{
                border-radius: 2px;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {bg},
                    stop:0.08 {border},
                    stop:0.22 {accent},
                    stop:0.78 {accent},
                    stop:0.92 {border},
                    stop:1 {bg}
                );
            }}
        """)
