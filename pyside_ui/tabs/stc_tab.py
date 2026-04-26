# pyside_ui/tabs/stc_tab.py
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from pyside_ui.controllers.stc_controller import StcController
from pyside_ui.widgets import ActionCard
from .contadores_tab import SectionHeader
from pyside_ui.theme.theme import TAB_MARGINS


class STCTab(QWidget):
    def __init__(self, theme: dict, parent=None, status_bus=None):
        super().__init__(parent)
        self._theme = theme or {}
        self._status_bus = status_bus

        # Layout Dashboard 2026
        self.root_lay = QVBoxLayout(self)
        self.root_lay.setContentsMargins(*TAB_MARGINS)
        self.root_lay.setSpacing(18)

        # ---------------------------------------------------------
        # SECCIÓN 1: CONVERSIÓN DE DATOS STC
        # ---------------------------------------------------------
        self.root_lay.addWidget(SectionHeader("Utilidades de Red y STC"))
        
        self.btn_db3_ip = ActionCard(
            "Extraer IPs desde DB3", 
            "Convierte bases de datos SQLite (.db3) a listado de Direcciones IP.",
            "📡"
        )
        self.btn_txt_ip = ActionCard(
            "Extraer IPs desde TXT", 
            "Procesa archivos de texto plano para identificar y extraer Direcciones IP.",
            "📄"
        )

        self.root_lay.addWidget(self.btn_db3_ip)
        self.root_lay.addWidget(self.btn_txt_ip)
        
        self.root_lay.addStretch(1) # ✅ Todo arriba, sin scroll

        # Controller
        self._stc_controller = StcController(
            parent=self,
            status_cb=self._status_cb,
            notify_cb=self._notify_cb,
        )
        
        # Wiring
        self.btn_db3_ip.clicked.connect(self._stc_controller.procesar_db3_a_ip)
        self.btn_txt_ip.clicked.connect(self._stc_controller.procesar_txt_a_ip)

        self.set_theme(self._theme)

    def _status_cb(self, text: str) -> None:
        if self._status_bus: self._status_bus.set_status(text)

    def _notify_cb(self, level: str, title: str, message: str, timeout_ms: int = 3000) -> None:
        if self._status_bus: self._status_bus.notify(level, title, message, timeout_ms)

    def set_theme(self, theme: dict) -> None:
        self._theme = theme or {}
        self.btn_db3_ip.set_theme(self._theme)
        self.btn_txt_ip.set_theme(self._theme)
