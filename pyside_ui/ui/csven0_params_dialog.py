# pyside_ui/ui/csven0_params_dialog.py
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from PySide6 import QtWidgets, QtCore, QtGui

from pyside_ui.ui.dialog_kit import BaseProDialog, apply_dialog_style, get_theme, warn
from pyside_ui.widgets.folder_picker_row import FolderPickerRow


@dataclass(frozen=True)
class CsvEn0Params:
    archivo_csv_entrada: str
    fecha_nueva: str
    nombre_cliente: str
    carpeta_salida: Optional[str]
    delimiter_entrada: str


class CsvEn0ParamsDialog(BaseProDialog):
    def __init__(
        self,
        parent: QtWidgets.QWidget,
        *,
        default_in_path: str | None = None,
        default_out_dir: str | None = None,
        theme: Optional[dict] = None,
    ):
        super().__init__(
            parent,
            "Estimación en 0 – Contadores por Proceso",
            "Seleccioná el CSV de entrada y definí los parámetros de salida.",
            w=720,
        )

        theme_to_apply = theme if theme else get_theme(parent)
        apply_dialog_style(self, theme_to_apply)

        self._result: Optional[CsvEn0Params] = None

        form = QtWidgets.QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)

        # CSV entrada
        self.csv_picker = FolderPickerRow(
            self,
            placeholder="Seleccioná el CSV de entrada…",
            initial_value=default_in_path or "",
            theme=theme_to_apply,
            mode="file",
            file_filter="CSV (*.csv);;Todos (*.*)",
            dialog_title="Elegir CSV de entrada",
        )
        form.addRow("CSV entrada:", self.csv_picker)

        # Fecha nueva
        self.ed_fecha = QtWidgets.QLineEdit()
        self.ed_fecha.setPlaceholderText("DD/MM/AAAA (obligatorio)")
        self.ed_fecha.setClearButtonEnabled(True)
        self.ed_fecha.setText(QtCore.QDate.currentDate().toString("dd/MM/yyyy"))
        form.addRow("Fecha nueva:", self.ed_fecha)

        # Nombre cliente
        self.ed_cliente = QtWidgets.QLineEdit()
        self.ed_cliente.setPlaceholderText("Ej: Citrusvil")
        self.ed_cliente.setClearButtonEnabled(True)
        form.addRow("Nombre cliente:", self.ed_cliente)

        # Carpeta salida
        self.folder_picker = FolderPickerRow(
            self,
            placeholder="Carpeta destino (opcional, por defecto junto al CSV)",
            initial_value=default_out_dir or "",
            theme=theme_to_apply,
            mode="folder",
            dialog_title="Elegir carpeta de salida",
        )
        self.csv_picker.path_changed.connect(self._on_csv_path_changed)
        form.addRow("Carpeta salida:", self.folder_picker)

        # Delimiter
        self.ed_delim = QtWidgets.QLineEdit()
        self.ed_delim.setPlaceholderText("Ej: ,  (por defecto coma)")
        self.ed_delim.setClearButtonEnabled(True)
        self.ed_delim.setText(",")
        self.ed_delim.setMaximumWidth(120)
        form.addRow("Delimitador:", self.ed_delim)

        self.root_layout.addLayout(form)

        # Buttons
        btn_ok = QtWidgets.QPushButton("Aceptar")
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

    def _on_csv_path_changed(self, path: str) -> None:
        if path and not self.folder_picker.get_path():
            try:
                self.folder_picker.set_path(os.path.dirname(path))
            except Exception:
                pass

    def _valid_date_ddmmyyyy(self, s: str) -> bool:
        if not s:
            return False
        try:
            dt = QtCore.QDate.fromString(s, "dd/MM/yyyy")
            return dt.isValid()
        except Exception:
            return False

    def _on_ok(self) -> None:
        csv_in = self.csv_picker.get_path()
        fecha = self.ed_fecha.text().strip()
        cliente = self.ed_cliente.text().strip()
        carpeta = self.folder_picker.get_path()
        delim = self.ed_delim.text().strip() or ","

        if not csv_in:
            warn(self, "Dato faltante", "Tenés que seleccionar el CSV de entrada.")
            return

        if not fecha:
            warn(self, "Dato faltante", "El campo 'Fecha nueva' es obligatorio.")
            return

        if not self._valid_date_ddmmyyyy(fecha):
            warn(self, "Fecha inválida", "La fecha debe tener formato DD/MM/AAAA (ej: 09/02/2026).")
            return

        if not cliente:
            warn(self, "Dato faltante", "El campo 'Nombre cliente' es obligatorio.")
            return

        self._result = CsvEn0Params(
            archivo_csv_entrada=csv_in,
            fecha_nueva=fecha,
            nombre_cliente=cliente,
            carpeta_salida=carpeta or None,
            delimiter_entrada=delim,
        )
        self.accept()

    def get_result(self) -> Optional[CsvEn0Params]:
        return self._result


def ask_csven0_params(
    parent: QtWidgets.QWidget,
    *,
    default_in_path: str | None = None,
    default_out_dir: str | None = None,
    theme: Optional[dict] = None,
) -> Optional[CsvEn0Params]:
    dlg = CsvEn0ParamsDialog(
        parent,
        default_in_path=default_in_path,
        default_out_dir=default_out_dir,
        theme=theme,
    )
    if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
        return dlg.get_result()
    return None
