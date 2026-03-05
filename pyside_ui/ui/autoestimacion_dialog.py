# pyside_ui/ui/autoestimacion_dialog.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from datetime import datetime

from PySide6 import QtWidgets, QtCore, QtGui

from pyside_ui.ui.dialog_kit import BaseProDialog, apply_dialog_style, get_theme, warn
from pyside_ui.widgets.folder_picker_row import FolderPickerRow


@dataclass(frozen=True)
class AutoestimacionParams:
    archivo_csv: str
    fecha_nueva: str


class AutoestimacionDialog(BaseProDialog):
    def __init__(
        self,
        parent: QtWidgets.QWidget,
        *,
        default_csv: str | None = None,
        default_fecha: str | None = None,
        theme: Optional[dict] = None,
    ):
        super().__init__(
            parent,
            "Autoestimación",
            "Seleccioná el CSV de detalle y la fecha para generar los archivos.",
            w=720,
        )

        theme_to_apply = theme if theme else get_theme(parent)
        apply_dialog_style(self, theme_to_apply)

        self._result: Optional[AutoestimacionParams] = None

        form = QtWidgets.QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)

        # CSV entrada
        self.csv_picker = FolderPickerRow(
            self,
            placeholder="Seleccioná el CSV de detalle…",
            initial_value=default_csv or "",
            theme=theme_to_apply,
            mode="file",
            file_filter="CSV (*.csv);;Todos (*.*)",
            dialog_title="Elegir CSV de detalle",
        )
        form.addRow("CSV detalle:", self.csv_picker)

        # -------------------------
        # Fecha
        # -------------------------
        self.ed_fecha = QtWidgets.QLineEdit()
        self.ed_fecha.setPlaceholderText("DD/MM/AAAA")
        self.ed_fecha.setClearButtonEnabled(True)

        if default_fecha:
            self.ed_fecha.setText(default_fecha)
        else:
            self.ed_fecha.setText(
                QtCore.QDate.currentDate().toString("dd/MM/yyyy")
            )

        form.addRow("Fecha estimación:", self.ed_fecha)

        self.root_layout.addLayout(form)

        # -------------------------
        # Botones
        # -------------------------
        btn_ok = QtWidgets.QPushButton("Generar")
        btn_cancel = QtWidgets.QPushButton("Cancelar")
        btn_ok.setObjectName("Primary")

        btn_ok.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        btn_cancel.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))

        btn_ok.clicked.connect(self._on_ok)
        btn_cancel.clicked.connect(self.reject)

        row_btns = QtWidgets.QHBoxLayout()
        row_btns.addStretch(1)
        row_btns.addWidget(btn_cancel)
        row_btns.addWidget(btn_ok)

        self.root_layout.addSpacing(6)
        self.root_layout.addLayout(row_btns)

    # ======================================================
    # Internos
    # ======================================================

    def _valid_date_ddmmyyyy(self, s: str) -> bool:
        if not s:
            return False
        try:
            dt = QtCore.QDate.fromString(s, "dd/MM/yyyy")
            return dt.isValid()
        except Exception:
            return False

    def _on_ok(self) -> None:
        csv_path = self.csv_picker.get_path()
        fecha = self.ed_fecha.text().strip()

        if not csv_path:
            warn(self, "Dato faltante", "Tenés que seleccionar el CSV de detalle.")
            return

        if not fecha:
            warn(self, "Dato faltante", "El campo 'Fecha estimación' es obligatorio.")
            return

        if not self._valid_date_ddmmyyyy(fecha):
            warn(
                self,
                "Fecha inválida",
                "La fecha debe tener formato DD/MM/AAAA (ej: 09/02/2026).",
            )
            return

        self._result = AutoestimacionParams(
            archivo_csv=csv_path,
            fecha_nueva=fecha,
        )

        self.accept()

    def get_data(self) -> tuple[str, str]:
        if not self._result:
            return "", ""
        return self._result.archivo_csv, self._result.fecha_nueva
