# pyside_ui/tabs/contadores_tab.py
from __future__ import annotations

from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel

from pyside_ui.widgets import ModernCheckBox, ActionCard
from pyside_ui.controllers.contadores_controller import ContadoresController
from pyside_ui.controllers.ftp_controller import FtpController
from pyside_ui.services.ftp_service import FtpService
from pyside_ui.theme.theme import TAB_MARGINS


class SectionHeader(QWidget):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 5, 0, 2)
        from PySide6.QtGui import QFont
        self.lbl = QLabel(title.upper())
        font = QFont("Segoe UI", 10, QFont.Bold)
        font.setPointSizeF(9.5) # ✅ Blindaje anti-warning
        self.lbl.setFont(font)
        self.lbl.setStyleSheet("color: #9CA3AF; letter-spacing: 1.2px;")
        lay.addWidget(self.lbl)


class ContadoresTab(QWidget):
    def __init__(self, theme: dict, parent=None, status_bus=None):
        super().__init__(parent)
        self._theme = theme or {}
        self._status_bus = status_bus

        # Layout Principal (Sin scroll para evitar ruido visual)
        self.root_lay = QVBoxLayout(self)
        self.root_lay.setContentsMargins(*TAB_MARGINS)
        self.root_lay.setSpacing(18)

        # ---------------------------------------------------------
        # BLOQUE 1: PROCESAMIENTO (ACCION PRINCIPAL)
        # ---------------------------------------------------------
        self.root_lay.addWidget(SectionHeader("Procesamiento de Datos"))
        
        self.btn_db3 = ActionCard(
            "Procesar Base de Datos (DB3)", 
            "Conversión nativa a CSV para el sistema.",
            "📊"
        )
        self.chk_ftp = ModernCheckBox("Descargar automáticamente desde servidor FTP")
        self.chk_ftp.setContentsMargins(10, 0, 0, 0)
        
        self.root_lay.addWidget(self.btn_db3)
        self.root_lay.addWidget(self.chk_ftp)

        # ---------------------------------------------------------
        # BLOQUE 2: PANEL DE CONTROL Y HERRAMIENTAS (GRID 2x2)
        # ---------------------------------------------------------
        self.root_lay.addWidget(SectionHeader("Herramientas de Gestión e IA"))
        
        tools_grid = QtWidgets.QGridLayout()
        tools_grid.setSpacing(14)

        self.btn_en0 = ActionCard("Limpiar a Cero", "Reseteo de contadores.", "🧹")
        self.btn_suma = ActionCard("Suma Fija", "Incrementos masivos.", "➕")
        self.btn_manual = ActionCard("Calculadora", "Proyección interactiva.", "🧮")
        self.btn_auto = ActionCard("Asistente IA", "Estimaciones automáticas.", "🤖")
        
        tools_grid.addWidget(self.btn_en0, 0, 0)
        tools_grid.addWidget(self.btn_suma, 0, 1)
        tools_grid.addWidget(self.btn_manual, 1, 0)
        tools_grid.addWidget(self.btn_auto, 1, 1)
        
        self.root_lay.addLayout(tools_grid)
        self.root_lay.addStretch(1) # ✅ Empuja todo hacia arriba para que no flote

        # -------------------------
        # Services & Controllers
        # -------------------------
        self._ftp_service = FtpService()
        self._controller = ContadoresController(
            parent=self, status_cb=self.set_status,
            ftp_service=self._ftp_service, uncheck_ftp_cb=self._uncheck_ftp,
            notify_cb=self._notify,
        )
        self._ftp_controller = FtpController(
            parent=self, ftp_service=self._ftp_service,
            status_cb=self.set_status, notify_cb=self._notify,
        )
        QtCore.QTimer.singleShot(0, self._expose_ftp_controller_to_window)

        # Wiring
        self.btn_db3.clicked.connect(lambda: self._controller.procesar_db3_a_csv(use_ftp=self.chk_ftp.isChecked()))
        self.btn_en0.clicked.connect(lambda: self._controller.estimacion_en0_contadores_por_proceso())
        self.btn_suma.clicked.connect(lambda: self._controller.estimacion_suma_fija())
        self.btn_manual.clicked.connect(lambda: self._controller.abrir_estimador_manual())
        self.btn_auto.clicked.connect(lambda: self._controller.abrir_autoestimacion())

        self.set_theme(self._theme)
        self.set_status("Listo")

    def _expose_ftp_controller_to_window(self) -> None:
        try:
            w = self.window()
            if w: setattr(w, "ftp_controller", self._ftp_controller)
        except Exception: pass

    def _uncheck_ftp(self) -> None:
        self.chk_ftp.setChecked(False)

    def _notify(self, level: str, title: str, message: str, timeout_ms: int = 3000) -> None:
        if self._status_bus: self._status_bus.notify(level, title, message, timeout_ms)

    def set_status(self, text: str) -> None:
        if self._status_bus: self._status_bus.set_status(text)

    def set_theme(self, theme: dict) -> None:
        self._theme = theme or {}
        for btn in (self.btn_db3, self.btn_en0, self.btn_suma, self.btn_manual, self.btn_auto):
            btn.set_theme(self._theme)
        self.chk_ftp.set_theme(self._theme)

    def set_ftp_available(self, available: bool) -> None:
        self.chk_ftp.setEnabled(available)
        if not available: self.chk_ftp.setChecked(False)
