# pyside_ui/ui/csven0_params_dialog.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from PySide6 import QtWidgets, QtCore, QtGui

from pyside_ui.ui.dialog_kit import BaseProDialog, apply_dialog_style, warn


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

        # Si el controller pasa theme explícito, lo aplicamos (override del que toma del parent.window())
        if theme:
            apply_dialog_style(self, theme)

        self._result: Optional[CsvEn0Params] = None

        form = QtWidgets.QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)

        # CSV entrada + picker
        self.ed_csv = QtWidgets.QLineEdit()
        self.ed_csv.setPlaceholderText("Seleccioná el CSV de entrada…")
        self.ed_csv.setClearButtonEnabled(True)
        if default_in_path:
            self.ed_csv.setText(default_in_path)

        btn_pick_csv = QtWidgets.QPushButton("Elegir…")
        btn_pick_csv.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        btn_pick_csv.clicked.connect(self._pick_csv)

        row_csv = QtWidgets.QHBoxLayout()
        row_csv.setContentsMargins(0, 0, 0, 0)
        row_csv.setSpacing(8)  # ✅ evita “seams” visuales
        row_csv.addWidget(self.ed_csv, 1)
        row_csv.addWidget(btn_pick_csv, 0)

        wrap_csv = QtWidgets.QWidget()
        wrap_csv.setObjectName("RowWrapTransparent")
        wrap_csv.setLayout(row_csv)
        # ✅ FIX: el wrapper debe ser transparente para que no “aparezca negro”
        wrap_csv.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground, True)
        wrap_csv.setStyleSheet("QWidget#RowWrapTransparent { background: transparent; }")

        form.addRow("CSV entrada:", wrap_csv)

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

        # Carpeta salida + picker
        self.ed_carpeta = QtWidgets.QLineEdit()
        self.ed_carpeta.setPlaceholderText("Carpeta destino (opcional, por defecto junto al CSV)")
        self.ed_carpeta.setClearButtonEnabled(True)
        if default_out_dir:
            self.ed_carpeta.setText(default_out_dir)

        btn_pick_out = QtWidgets.QPushButton("Elegir…")
        btn_pick_out.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        btn_pick_out.clicked.connect(self._pick_out_dir)

        row_out = QtWidgets.QHBoxLayout()
        row_out.setContentsMargins(0, 0, 0, 0)
        row_out.setSpacing(8)  # ✅ evita “seams” visuales
        row_out.addWidget(self.ed_carpeta, 1)
        row_out.addWidget(btn_pick_out, 0)

        wrap_out = QtWidgets.QWidget()
        wrap_out.setObjectName("RowWrapTransparent")
        wrap_out.setLayout(row_out)
        # ✅ FIX: transparente también
        wrap_out.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground, True)
        wrap_out.setStyleSheet("QWidget#RowWrapTransparent { background: transparent; }")

        form.addRow("Carpeta salida:", wrap_out)

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

    def _pick_csv(self) -> None:
        start = self.ed_csv.text().strip() or ""
        path, _filter = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Elegir CSV de entrada",
            start,
            "CSV (*.csv);;Todos (*.*)",
        )
        if path:
            self.ed_csv.setText(path)
            if not self.ed_carpeta.text().strip():
                try:
                    import os

                    self.ed_carpeta.setText(os.path.dirname(path))
                except Exception:
                    pass

    def _pick_out_dir(self) -> None:
        start = self.ed_carpeta.text().strip() or ""
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Elegir carpeta de salida", start)
        if folder:
            self.ed_carpeta.setText(folder)

    def _valid_date_ddmmyyyy(self, s: str) -> bool:
        if not s:
            return False
        try:
            dt = QtCore.QDate.fromString(s, "dd/MM/yyyy")
            return dt.isValid()
        except Exception:
            return False

    def _on_ok(self) -> None:
        csv_in = self.ed_csv.text().strip()
        fecha = self.ed_fecha.text().strip()
        cliente = self.ed_cliente.text().strip()
        carpeta = self.ed_carpeta.text().strip()
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
