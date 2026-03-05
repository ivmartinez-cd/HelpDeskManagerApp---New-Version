# pyside_ui/tabs/stc_tab.py
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout

from pyside_ui.controllers.stc_controller import StcController
from pyside_ui.widgets import Card
from pyside_ui.widgets import make_big_button, update_big_button


class STCTab(QWidget):
    def __init__(self, theme: dict, parent=None, status_bus=None):
        super().__init__(parent)
        self._theme = theme or {}
        self._status_bus = status_bus

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self.card = Card("Herramientas STC")
        lay.addWidget(self.card, 0, Qt.AlignTop)

        self.btn_db3_ip = make_big_button("db3 a Direc. IP", self._theme)
        self.btn_txt_ip = make_big_button("txt a Direc. IP", self._theme)

        self.card.grid.addWidget(self.btn_db3_ip, 0, 0, 1, 2)
        self.card.grid.addWidget(self.btn_txt_ip, 1, 0, 1, 2)

        self._stc_controller = StcController(
            parent=self,
            status_cb=self._status_cb,
            notify_cb=self._notify_cb,
        )
        self.btn_db3_ip.clicked.connect(self._stc_controller.procesar_db3_a_ip)
        self.btn_txt_ip.clicked.connect(self._stc_controller.procesar_txt_a_ip)

        self.set_theme(self._theme)

    def _status_cb(self, text: str) -> None:
        if self._status_bus is not None:
            self._status_bus.set_status(text)

    def _notify_cb(self, level: str, title: str, message: str, timeout_ms: int = 3000) -> None:
        if self._status_bus is not None:
            self._status_bus.notify(level, title, message, timeout_ms)

    def set_theme(self, theme: dict) -> None:
        self._theme = theme or {}
        self.card.set_theme(self._theme)
        update_big_button(self.btn_db3_ip, self._theme)
        update_big_button(self.btn_txt_ip, self._theme)
