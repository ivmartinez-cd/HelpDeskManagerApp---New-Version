from __future__ import annotations

from PySide6 import QtCore
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout

from pyside_ui.widgets import Card, ModernCheckBox
from pyside_ui.widgets import make_big_button, update_big_button

from pyside_ui.controllers.contadores_controller import ContadoresController
from pyside_ui.controllers.ftp_controller import FtpController
from pyside_ui.services.ftp_service import FtpService


class ContadoresTab(QWidget):
    def __init__(self, theme: dict, parent=None, status_bus=None):
        super().__init__(parent)
        self._theme = theme or {}
        self._status_bus = status_bus

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self.card = Card("Operaciones de Contadores")
        lay.addWidget(self.card, 0, Qt.AlignTop)

        # -------------------------
        # Botones
        # -------------------------
        self.btn_db3 = make_big_button("Procesar\nDB3 → CSV", self._theme)
        self.btn_en0 = make_big_button("Estimación en 0\nContadores por Proceso", self._theme)
        self.btn_suma = make_big_button("Estimación\nsuma fija", self._theme)
        self.btn_manual = make_big_button("Abrir\nEstimador Manual", self._theme)
        self.btn_auto = make_big_button("Autoestimación", self._theme)

        self.chk_ftp = ModernCheckBox("Descargar DB3 desde FTP")

        self.card.grid.addWidget(self.btn_db3, 0, 0)
        self.card.grid.addWidget(self.btn_en0, 0, 1)
        self.card.grid.addWidget(self.chk_ftp, 1, 0, 1, 2)
        self.card.grid.addWidget(self.btn_suma, 2, 0)
        self.card.grid.addWidget(self.btn_manual, 2, 1)
        self.card.grid.addWidget(self.btn_auto, 3, 0, 1, 2)

        # -------------------------
        # Services
        # -------------------------
        self._ftp_service = FtpService()

        # -------------------------
        # Controllers
        # -------------------------
        self._controller = ContadoresController(
            parent=self,
            status_cb=self.set_status,
            ftp_service=self._ftp_service,
            uncheck_ftp_cb=self._uncheck_ftp,
            notify_cb=self._notify,
        )

        self._ftp_controller = FtpController(
            parent=self,
            ftp_service=self._ftp_service,
            status_cb=self.set_status,
            notify_cb=self._notify,
        )

        QtCore.QTimer.singleShot(0, self._expose_ftp_controller_to_window)

        # -------------------------
        # Wiring
        # -------------------------
        self.btn_db3.clicked.connect(
            lambda: self._controller.procesar_db3_a_csv(use_ftp=self.chk_ftp.isChecked())
        )

        self.btn_en0.clicked.connect(
            lambda: self._controller.estimacion_en0_contadores_por_proceso()
        )

        self.btn_suma.clicked.connect(
            lambda: self._controller.estimacion_suma_fija()
        )

        # ✅ NUEVO: Estimador manual
        self.btn_manual.clicked.connect(
            lambda: self._controller.abrir_estimador_manual()
        )

        self.btn_auto.clicked.connect(
            lambda: self._controller.abrir_autoestimacion()
        )


        self.set_theme(self._theme)
        self.set_status("Listo")

    def _expose_ftp_controller_to_window(self) -> None:
        try:
            w = self.window()
            if w is not None:
                setattr(w, "ftp_controller", self._ftp_controller)
        except Exception:
            pass

    def _uncheck_ftp(self) -> None:
        self.chk_ftp.setChecked(False)

    def _notify(self, level: str, title: str, message: str, timeout_ms: int = 3000) -> None:
        if self._status_bus is not None:
            self._status_bus.notify(level, title, message, timeout_ms)

    def set_status(self, text: str) -> None:
        if self._status_bus is not None:
            self._status_bus.set_status(text)

    def set_theme(self, theme: dict) -> None:
        self._theme = theme or {}
        self.card.set_theme(self._theme)

        for btn in (self.btn_db3, self.btn_en0, self.btn_suma, self.btn_manual, self.btn_auto):
            update_big_button(btn, self._theme)

        self.chk_ftp.set_theme(self._theme)

    def set_ftp_available(self, available: bool) -> None:
        self.chk_ftp.setEnabled(available)
        if not available:
            self.chk_ftp.setChecked(False)
