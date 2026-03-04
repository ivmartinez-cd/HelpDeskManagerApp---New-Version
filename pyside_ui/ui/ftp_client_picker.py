# pyside_ui/ui/ftp_client_picker.py
from __future__ import annotations

from typing import Optional

from PySide6 import QtWidgets

from pyside_ui.ui.dialog_kit import BaseProDialog, make_button_row, apply_dialog_style


class FtpClientPickerDialog(BaseProDialog):
    """
    Diálogo PRO para elegir cliente FTP (base: dialog_kit).
    - Soporta dark/light vía theme dict (MainWindow.theme) o theme explícito.
    - Incluye buscador + lista.
    - Enter = Continuar, Esc = Cancelar.
    - Mantiene API usada por ContadoresController: selected_client.
    """

    def __init__(self, parent: QtWidgets.QWidget, clients: list[str], theme: Optional[dict] = None):
        super().__init__(
            parent,
            "Cliente FTP",
            "Elegí el cliente para descargar el archivo DB3.",
            w=560,
            h=420,
        )

        # Si el controller pasa theme explícito, lo aplicamos (override del que toma del parent.window())
        if theme:
            apply_dialog_style(self, theme)

        self._all_clients = list(clients)
        self._selected: Optional[str] = None

        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText("Buscar cliente…")
        self.search.setClearButtonEnabled(True)

        self.list = QtWidgets.QListWidget()
        self.list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.list.setMinimumHeight(240)

        self.btn_ok, self.btn_cancel, row = make_button_row(
            ok_text="Continuar",
            cancel_text="Cancelar",
            ok_object_name="Primary",
        )
        self.btn_ok.setDefault(True)
        self.btn_ok.setEnabled(False)

        # Wiring
        self.search.textChanged.connect(self._apply_filter)
        self.list.itemSelectionChanged.connect(self._sync_ok_state)
        self.list.itemDoubleClicked.connect(lambda _it: self._accept_if_selected())
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_ok.clicked.connect(self._accept_if_selected)

        # Layout
        self.root_layout.addWidget(self.search)
        self.root_layout.addWidget(self.list, 1)
        self.root_layout.addLayout(row)

        # Fill inicial
        self._apply_filter("")

    @property
    def selected_client(self) -> Optional[str]:
        return self._selected

    def _sync_ok_state(self) -> None:
        self.btn_ok.setEnabled(self.list.currentItem() is not None)

    def _accept_if_selected(self) -> None:
        it = self.list.currentItem()
        if not it:
            return
        self._selected = it.text().strip()
        if self._selected:
            self.accept()

    def _apply_filter(self, text: str) -> None:
        q = (text or "").strip().lower()
        self.list.clear()

        if not q:
            items = self._all_clients
        else:
            items = [c for c in self._all_clients if q in c.lower()]

        self.list.addItems(items)

        if self.list.count() > 0:
            self.list.setCurrentRow(0)

        self._sync_ok_state()
