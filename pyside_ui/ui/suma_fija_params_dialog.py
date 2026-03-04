# pyside_ui/ui/suma_fija_params_dialog.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List

from PySide6 import QtWidgets, QtCore, QtGui

from pyside_ui.ui.dialog_kit import BaseProDialog, apply_dialog_style, warn


@dataclass(frozen=True)
class SumaFijaParams:
    archivos_xls: List[str]
    carpeta_salida: str
    fecha: str
    hojas_a_sumar: int


class SumaFijaParamsDialog(BaseProDialog):
    def __init__(
        self,
        parent: QtWidgets.QWidget,
        *,
        default_files: Optional[List[str]] = None,
        default_out_dir: str | None = None,
        default_fecha: str | None = None,
        default_hojas: int = 0,
        theme: Optional[dict] = None,
    ):
        super().__init__(
            parent,
            "Estimación – Suma fija",
            "Seleccioná los Excel SIGES y definí los parámetros para generar los CSV.",
            w=760,
        )

        if theme:
            apply_dialog_style(self, theme)

        self._result: Optional[SumaFijaParams] = None

        form = QtWidgets.QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)

        # -------- Archivos (multi) --------
        self.ed_files = QtWidgets.QLineEdit()
        self.ed_files.setReadOnly(True)
        self.ed_files.setPlaceholderText("Seleccioná uno o más archivos Excel (.xls/.xlsx)…")
        self._files: List[str] = list(default_files or [])
        self._refresh_files_text()

        btn_pick_files = QtWidgets.QPushButton("Elegir…")
        btn_pick_files.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        btn_pick_files.clicked.connect(self._pick_files)

        row_files = QtWidgets.QHBoxLayout()
        row_files.setContentsMargins(0, 0, 0, 0)
        row_files.setSpacing(8)
        row_files.addWidget(self.ed_files, 1)
        row_files.addWidget(btn_pick_files, 0)

        wrap_files = QtWidgets.QWidget()
        wrap_files.setObjectName("RowWrapTransparent")
        wrap_files.setLayout(row_files)
        wrap_files.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground, True)
        wrap_files.setStyleSheet("QWidget#RowWrapTransparent { background: transparent; }")

        form.addRow("Excel SIGES:", wrap_files)

        # -------- Carpeta salida --------
        self.ed_out = QtWidgets.QLineEdit()
        self.ed_out.setPlaceholderText("Carpeta destino (obligatoria)")
        self.ed_out.setClearButtonEnabled(True)
        if default_out_dir:
            self.ed_out.setText(default_out_dir)

        btn_pick_out = QtWidgets.QPushButton("Elegir…")
        btn_pick_out.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        btn_pick_out.clicked.connect(self._pick_out_dir)

        row_out = QtWidgets.QHBoxLayout()
        row_out.setContentsMargins(0, 0, 0, 0)
        row_out.setSpacing(8)
        row_out.addWidget(self.ed_out, 1)
        row_out.addWidget(btn_pick_out, 0)

        wrap_out = QtWidgets.QWidget()
        wrap_out.setObjectName("RowWrapTransparent")
        wrap_out.setLayout(row_out)
        wrap_out.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground, True)
        wrap_out.setStyleSheet("QWidget#RowWrapTransparent { background: transparent; }")

        form.addRow("Carpeta salida:", wrap_out)

        # -------- Fecha --------
        self.ed_fecha = QtWidgets.QLineEdit()
        self.ed_fecha.setPlaceholderText("DD/MM/AAAA (obligatorio)")
        self.ed_fecha.setClearButtonEnabled(True)
        if default_fecha:
            self.ed_fecha.setText(default_fecha)
        else:
            self.ed_fecha.setText(QtCore.QDate.currentDate().toString("dd/MM/yyyy"))
        form.addRow("Fecha:", self.ed_fecha)

        # -------- Hojas a sumar --------
        self.sp_hojas = QtWidgets.QSpinBox()
        self.sp_hojas.setRange(0, 10_000_000)
        self.sp_hojas.setValue(int(default_hojas or 0))
        self.sp_hojas.setSingleStep(100)
        self.sp_hojas.setMaximumWidth(220)
        form.addRow("Hojas a sumar:", self.sp_hojas)

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

    def _refresh_files_text(self) -> None:
        if not self._files:
            self.ed_files.setText("")
            return
        if len(self._files) == 1:
            self.ed_files.setText(self._files[0])
        else:
            self.ed_files.setText(f"{len(self._files)} archivos seleccionados")

    def _pick_files(self) -> None:
        start_dir = ""
        if self._files:
            try:
                import os
                start_dir = os.path.dirname(self._files[0])
            except Exception:
                start_dir = ""

        files, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            "Seleccionar archivo(s) Excel",
            start_dir,
            "Excel (*.xls *.xlsx);;Todos (*.*)",
        )
        if files:
            self._files = list(files)
            self._refresh_files_text()
            # sugerir carpeta salida si está vacía
            if not self.ed_out.text().strip():
                try:
                    import os
                    self.ed_out.setText(os.path.dirname(files[0]))
                except Exception:
                    pass

    def _pick_out_dir(self) -> None:
        start = self.ed_out.text().strip() or ""
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Elegir carpeta de salida", start)
        if folder:
            self.ed_out.setText(folder)

    def _valid_date_ddmmyyyy(self, s: str) -> bool:
        if not s:
            return False
        dt = QtCore.QDate.fromString(s, "dd/MM/yyyy")
        return dt.isValid()

    def _on_ok(self) -> None:
        out_dir = self.ed_out.text().strip()
        fecha = self.ed_fecha.text().strip()
        hojas = int(self.sp_hojas.value())

        if not self._files:
            warn(self, "Dato faltante", "Tenés que seleccionar al menos un archivo Excel.")
            return

        if not out_dir:
            warn(self, "Dato faltante", "Tenés que seleccionar la carpeta de salida.")
            return

        if not fecha:
            warn(self, "Dato faltante", "El campo 'Fecha' es obligatorio.")
            return

        if not self._valid_date_ddmmyyyy(fecha):
            warn(self, "Fecha inválida", "La fecha debe tener formato DD/MM/AAAA (ej: 09/02/2026).")
            return

        self._result = SumaFijaParams(
            archivos_xls=list(self._files),
            carpeta_salida=out_dir,
            fecha=fecha,
            hojas_a_sumar=hojas,
        )
        self.accept()

    def get_result(self) -> Optional[SumaFijaParams]:
        return self._result


def ask_suma_fija_params(
    parent: QtWidgets.QWidget,
    *,
    default_files: Optional[List[str]] = None,
    default_out_dir: str | None = None,
    default_fecha: str | None = None,
    default_hojas: int = 0,
    theme: Optional[dict] = None,
) -> Optional[SumaFijaParams]:
    dlg = SumaFijaParamsDialog(
        parent,
        default_files=default_files,
        default_out_dir=default_out_dir,
        default_fecha=default_fecha,
        default_hojas=default_hojas,
        theme=theme,
    )
    if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
        return dlg.get_result()
    return None
