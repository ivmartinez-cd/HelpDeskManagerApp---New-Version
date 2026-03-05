# pyside_ui/widgets/folder_picker_row.py
from __future__ import annotations

from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets


class FolderPickerRow(QtWidgets.QWidget):
    """
    Widget reutilizable: QLineEdit (stretch) + QPushButton "Elegir…".
    Soporta modo archivo (getOpenFileName) o carpeta (getExistingDirectory).
    Contenedor estilizado con tema (panel_bg, card_border, radius 10).
    """

    path_changed = QtCore.Signal(str)

    def __init__(
        self,
        parent: Optional[QtWidgets.QWidget] = None,
        *,
        placeholder: str = "",
        initial_value: str = "",
        theme: Optional[dict] = None,
        mode: str = "folder",
        file_filter: Optional[str] = None,
        dialog_title: Optional[str] = None,
    ):
        super().__init__(parent)
        self._mode = "folder" if mode != "file" else "file"
        self._file_filter = file_filter or "Todos los archivos (*)"
        self._dialog_title = dialog_title or ("Elegir carpeta" if self._mode == "folder" else "Elegir archivo")

        self.setObjectName("FolderPickerWrap")
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._line_edit = QtWidgets.QLineEdit()
        self._line_edit.setPlaceholderText(placeholder)
        self._line_edit.setClearButtonEnabled(True)
        if initial_value:
            self._line_edit.setText(initial_value)

        btn = QtWidgets.QPushButton("Elegir…")
        btn.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        btn.clicked.connect(self._on_pick)

        lay.addWidget(self._line_edit, 1)
        lay.addWidget(btn, 0)

        self._theme = theme or {}
        self._apply_theme()

    def _apply_theme(self) -> None:
        panel_bg = self._theme.get("btn_bg", self._theme.get("card_bg", "#2A2A2A"))
        border = self._theme.get("card_border", self._theme.get("border", "#3A3A3A"))
        self.setStyleSheet(
            f"""
            QWidget#FolderPickerWrap {{
                background: {panel_bg};
                border: 1px solid {border};
                border-radius: 10px;
            }}
            QWidget#FolderPickerWrap QLineEdit {{
                background: transparent;
                border: none;
            }}
            """
        )

    def set_theme(self, theme: Optional[dict]) -> None:
        self._theme = theme or {}
        self._apply_theme()

    def _on_pick(self) -> None:
        start = self._line_edit.text().strip() or ""
        if self._mode == "folder":
            path = QtWidgets.QFileDialog.getExistingDirectory(self, self._dialog_title, start)
        else:
            path, _ = QtWidgets.QFileDialog.getOpenFileName(
                self,
                self._dialog_title,
                start,
                self._file_filter,
            )
        if path:
            self._line_edit.setText(path)
            self.path_changed.emit(path)

    def get_path(self) -> str:
        return self._line_edit.text().strip()

    def set_path(self, path: str) -> None:
        self._line_edit.setText(path or "")

    @property
    def line_edit(self) -> QtWidgets.QLineEdit:
        return self._line_edit
