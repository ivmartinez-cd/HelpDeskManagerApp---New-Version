# pyside_ui/tabs/stc_tab.py
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout

from pyside_ui.widgets import Card
from pyside_ui.widgets import make_big_button, update_big_button


class STCTab(QWidget):
    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self._theme = theme or {}

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self.card = Card("Herramientas STC")
        lay.addWidget(self.card, 0, Qt.AlignTop)

        # Botones (UI pura, sin lógica)
        self.btn_db3_ip = make_big_button("db3 a Direc. IP", self._theme)
        self.btn_txt_ip = make_big_button("txt a Direc. IP", self._theme)

        # Grid del Card
        self.card.grid.addWidget(self.btn_db3_ip, 0, 0, 1, 2)
        self.card.grid.addWidget(self.btn_txt_ip, 1, 0, 1, 2)

        self.set_theme(self._theme)

    def set_theme(self, theme: dict) -> None:
        self._theme = theme or {}
        self.card.set_theme(self._theme)
        update_big_button(self.btn_db3_ip, self._theme)
        update_big_button(self.btn_txt_ip, self._theme)
