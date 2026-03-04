# pyside_ui/ui/ftp_dialogs.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List

from PySide6 import QtWidgets, QtCore

from pyside_ui.ui.dialog_kit import (
    BaseProDialog,
    ConfirmDialog,
    MessageDialog,
    make_card,
    make_button_row,
    warn,
)


@dataclass(frozen=True)
class FtpCreds:
    cliente: str
    user: str
    password: str


class _ClientPickerDialog(BaseProDialog):
    def __init__(self, parent: QtWidgets.QWidget, title: str, subtitle: str, clientes: List[str]):
        super().__init__(parent, title, subtitle, w=560, h=420)
        self._all = list(clientes)
        self._result: Optional[str] = None

        self._search = QtWidgets.QLineEdit()
        self._search.setPlaceholderText("Buscar cliente…")
        self._search.textChanged.connect(self._refill)

        self._list = QtWidgets.QListWidget()
        self._list.itemDoubleClicked.connect(lambda _it: self._accept_current())

        btn_ok, btn_cancel, row = make_button_row(ok_text="Continuar", cancel_text="Cancelar", ok_object_name="Primary")
        btn_cancel.clicked.connect(self.reject)
        btn_ok.clicked.connect(self._accept_current)

        self.root_layout.addWidget(self._search)
        self.root_layout.addWidget(self._list, 1)
        self.root_layout.addLayout(row)

        self._refill()

    def _refill(self):
        q = self._search.text().strip().lower()
        self._list.clear()
        items = self._all if not q else [c for c in self._all if q in c.lower()]
        for c in items:
            self._list.addItem(c)
        if self._list.count() > 0:
            self._list.setCurrentRow(0)

    def _accept_current(self):
        it = self._list.currentItem()
        if not it:
            return
        self._result = it.text().strip()
        self.accept()

    @property
    def result(self) -> Optional[str]:
        return self._result


class _CredsDialog(BaseProDialog):
    def __init__(
        self,
        parent: QtWidgets.QWidget,
        title: str,
        subtitle: str,
        *,
        cliente_readonly: bool = False,
        cliente_initial: str = "",
        user_initial: str = "",
        password_initial: str = "",
    ):
        super().__init__(parent, title, subtitle, w=620)

        card = make_card()
        card_lay = QtWidgets.QVBoxLayout(card)
        card_lay.setContentsMargins(14, 12, 14, 12)
        card_lay.setSpacing(10)

        self._cliente = QtWidgets.QLineEdit(cliente_initial)
        self._user = QtWidgets.QLineEdit(user_initial)
        self._pass = QtWidgets.QLineEdit(password_initial)
        self._pass.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)

        self._cliente.setReadOnly(cliente_readonly)
        if cliente_readonly:
            self._cliente.setToolTip("El nombre del cliente no se puede editar.")

        def row(label: str, widget: QtWidgets.QWidget) -> QtWidgets.QWidget:
            w = QtWidgets.QWidget()
            l = QtWidgets.QHBoxLayout(w)
            l.setContentsMargins(0, 0, 0, 0)
            l.setSpacing(12)
            lbl = QtWidgets.QLabel(label)
            lbl.setMinimumWidth(110)
            l.addWidget(lbl)
            l.addWidget(widget, 1)
            return w

        card_lay.addWidget(row("Cliente", self._cliente))
        card_lay.addWidget(row("Usuario", self._user))
        card_lay.addWidget(row("Password", self._pass))

        btn_ok, btn_cancel, row_btns = make_button_row(ok_text="Aceptar", cancel_text="Cancelar", ok_object_name="Primary")
        btn_cancel.clicked.connect(self.reject)
        btn_ok.clicked.connect(self._on_ok)

        self.root_layout.addWidget(card)
        self.root_layout.addLayout(row_btns)

        self._result: Optional[FtpCreds] = None

    def _on_ok(self):
        cliente = self._cliente.text().strip()
        user = self._user.text().strip()
        password = self._pass.text()

        if not cliente:
            warn(self, "Dato faltante", "El campo 'Cliente' es obligatorio.")
            return
        if not user:
            warn(self, "Dato faltante", "El campo 'Usuario' es obligatorio.")
            return
        if password == "":
            warn(self, "Dato faltante", "El campo 'Password' es obligatorio.")
            return

        self._result = FtpCreds(cliente=cliente, user=user, password=password)
        self.accept()

    @property
    def result(self) -> Optional[FtpCreds]:
        return self._result


# ==========================
# API pública (MISMAS firmas)
# ==========================
def ask_add_client(parent: QtWidgets.QWidget) -> Optional[FtpCreds]:
    dlg = _CredsDialog(
        parent,
        "Agregar cliente FTP",
        "Completá las credenciales del cliente para guardarlas en el JSON.",
        cliente_readonly=False,
    )
    if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
        return dlg.result
    return None


def ask_edit_client(parent: QtWidgets.QWidget, clientes: List[str]) -> Optional[FtpCreds]:
    if not clientes:
        MessageDialog(parent, "Sin clientes", "No hay clientes FTP cargados.").exec()
        return None

    pick = _ClientPickerDialog(
        parent,
        "Modificar cliente FTP",
        "Seleccioná un cliente para editar sus credenciales.",
        clientes,
    )
    if pick.exec() != QtWidgets.QDialog.DialogCode.Accepted or not pick.result:
        return None

    cliente = pick.result
    dlg = _CredsDialog(
        parent,
        "Modificar credenciales FTP",
        "Actualizá usuario y password. El nombre del cliente no se puede editar.",
        cliente_readonly=True,
        cliente_initial=cliente,
    )
    if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
        return dlg.result
    return None


def ask_delete_client(parent: QtWidgets.QWidget, clientes: List[str]) -> Optional[str]:
    if not clientes:
        MessageDialog(parent, "Sin clientes", "No hay clientes FTP cargados.").exec()
        return None

    pick = _ClientPickerDialog(
        parent,
        "Eliminar cliente FTP",
        "Seleccioná un cliente para eliminarlo del JSON.",
        clientes,
    )
    if pick.exec() != QtWidgets.QDialog.DialogCode.Accepted or not pick.result:
        return None

    cliente = pick.result
    confirm = ConfirmDialog(
        parent,
        "Confirmar eliminación",
        f"¿Eliminar el cliente '{cliente}' del JSON?\n\nEsta acción no se puede deshacer.",
        confirm_text="Eliminar",
        cancel_text="Cancelar",
        danger=True,
    )
    if confirm.exec() != QtWidgets.QDialog.DialogCode.Accepted:
        return None

    return cliente
