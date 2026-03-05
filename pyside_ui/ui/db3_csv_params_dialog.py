from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from PySide6 import QtWidgets, QtCore, QtGui

from pyside_ui.ui.dialog_kit import (
    BaseProDialog,
    apply_dialog_style,
    get_theme,
    warn,
)
from pyside_ui.widgets.folder_picker_row import FolderPickerRow


@dataclass(frozen=True)
class Db3CsvParams:
    fecha_maxima: Optional[str]
    nombre_base_salida: str
    carpeta_salida: Optional[str]


class Db3CsvParamsDialog(BaseProDialog):
    def __init__(
        self,
        parent: QtWidgets.QWidget,
        default_out_dir: str | None = None,
        *,
        default_fecha: str | None = None,
        default_nombre_base: str | None = None,
        default_carpeta: str | None = None,
        theme: Optional[dict] = None,
    ):
        super().__init__(parent, "Parámetros DB3 → CSV", "Configuración de salida", w=640)

        self._result: Optional[Db3CsvParams] = None
        theme_to_apply = theme if theme else get_theme(parent)

        form = QtWidgets.QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)

        self.ed_fecha = QtWidgets.QLineEdit()
        self.ed_fecha.setPlaceholderText("DD/MM/AAAA (opcional)")
        self.ed_fecha.setClearButtonEnabled(True)
        if default_fecha:
            self.ed_fecha.setText(default_fecha)

        self.ed_nombre = QtWidgets.QLineEdit()
        self.ed_nombre.setPlaceholderText("Ej: Citrusvil (sin _AutoCSV ni período)")
        self.ed_nombre.setClearButtonEnabled(True)
        if default_nombre_base:
            self.ed_nombre.setText(default_nombre_base)

        carpeta_prefill = default_carpeta or default_out_dir or ""
        self.folder_picker = FolderPickerRow(
            self,
            placeholder="Carpeta destino (opcional)",
            initial_value=carpeta_prefill,
            theme=theme_to_apply,
            mode="folder",
            dialog_title="Elegir carpeta de salida",
        )

        form.addRow("Fecha máxima:", self.ed_fecha)
        form.addRow("Nombre base:", self.ed_nombre)
        form.addRow("Carpeta salida:", self.folder_picker)

        self.root_layout.addLayout(form)

        btn_ok = QtWidgets.QPushButton("Aceptar")
        btn_cancel = QtWidgets.QPushButton("Cancelar")
        btn_ok.setObjectName("Primary")
        btn_cancel.setObjectName("Secondary")
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

        apply_dialog_style(self, theme_to_apply)
        self.folder_picker.set_theme(theme_to_apply)

    def _valid_date(self, s: str) -> bool:
        if not s:
            return True
        try:
            dt = QtCore.QDate.fromString(s, "dd/MM/yyyy")
            return dt.isValid()
        except Exception:
            return False

    def _on_ok(self) -> None:
        fecha = self.ed_fecha.text().strip()
        nombre = self.ed_nombre.text().strip()
        carpeta = self.folder_picker.get_path()

        if nombre == "":
            warn(self, "Dato faltante", "El campo 'Nombre base' es obligatorio.")
            return

        if fecha:
            if not self._valid_date(fecha):
                warn(
                    self,
                    "Fecha inválida",
                    "La 'Fecha máxima' debe tener formato DD/MM/AAAA (ej: 09/02/2026) o quedar vacía.",
                )
                return

        self._result = Db3CsvParams(
            fecha_maxima=fecha or None,
            nombre_base_salida=nombre,
            carpeta_salida=carpeta or None,
        )
        self.accept()

    def get_result(self) -> Optional[Db3CsvParams]:
        return self._result


def ask_db3_csv_params(
    parent: QtWidgets.QWidget,
    default_out_dir: str | None = None,
    *,
    default_fecha: str | None = None,
    default_nombre_base: str | None = None,
    default_carpeta: str | None = None,
    theme: Optional[dict] = None,
) -> Optional[Db3CsvParams]:
    dlg = Db3CsvParamsDialog(
        parent,
        default_out_dir=default_out_dir,
        default_fecha=default_fecha,
        default_nombre_base=default_nombre_base,
        default_carpeta=default_carpeta,
        theme=theme,
    )
    if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
        return dlg.get_result()
    return None
