# pyside_ui/controllers/ftp_controller.py
from __future__ import annotations

from typing import Callable, Optional

from PySide6 import QtCore, QtWidgets

from pyside_ui.services.ftp_service import FtpService
from pyside_ui.ui.ftp_dialogs import (
    ask_add_client,
    ask_edit_client,
    ask_delete_client,
)

NotifyCb = Callable[[str, str, str, int], None]
StatusCb = Callable[[str], None]


class FtpController(QtCore.QObject):
    """
    Controller FTP (solo CRUD de clientes).
    - Qt: solo para orquestar diálogos.
    - Negocio real: FtpService (Qt-agnóstico).
    - Emite feedback vía callbacks (status_cb/notify_cb).
    """

    def __init__(
        self,
        parent: QtWidgets.QWidget,
        *,
        ftp_service: FtpService,
        status_cb: StatusCb,
        notify_cb: Optional[NotifyCb] = None,
    ) -> None:
        super().__init__(parent)
        self._parent = parent
        self._ftp = ftp_service
        self._status_cb = status_cb
        self._notify_cb = notify_cb

    # -------------------------
    # Helpers
    # -------------------------
    def _notify(self, level: str, title: str, message: str, timeout_ms: int = 3000) -> None:
        if self._notify_cb:
            self._notify_cb(level, title, message, timeout_ms)

    def _status(self, text: str) -> None:
        if self._status_cb:
            self._status_cb(text)

    def _safe_parent(self) -> QtWidgets.QWidget:
        # Preferir la ventana para modal y foco correcto
        try:
            w = self._parent.window()
            return w if isinstance(w, QtWidgets.QWidget) else self._parent
        except Exception:
            return self._parent

    def _get_cfg_path_or_error(self) -> Optional[str]:
        try:
            self._status("Preparando configuración FTP…")
            return self._ftp.ensure_cfg_path()
        except Exception as e:
            self._notify("error", "FTP", f"No se pudo acceder a la configuración FTP.\n\n{e}", 7000)
            self._status("")  # no mostramos "Listo"
            return None

    # -------------------------
    # Acciones del menú
    # -------------------------
    def add_client(self) -> None:
        cfg_path = self._get_cfg_path_or_error()
        if not cfg_path:
            return

        parent = self._safe_parent()
        creds = ask_add_client(parent)
        if not creds:
            self._status("")
            return

        try:
            self._status("Guardando cliente FTP…")
            self._ftp.upsert_client(cfg_path, creds.cliente, creds.user, creds.password)
            # ✅ Toast final (éxito)
            self._notify("success", "FTP", f"Cliente agregado/actualizado: {creds.cliente}", 4000)
        except Exception as e:
            # ✅ Toast final (error)
            self._notify("error", "FTP", f"No se pudo guardar el cliente.\n\n{e}", 7000)
        finally:
            self._status("")

    def edit_client(self) -> None:
        cfg_path = self._get_cfg_path_or_error()
        if not cfg_path:
            return

        parent = self._safe_parent()

        try:
            self._status("Cargando clientes FTP…")
            clientes = self._ftp.list_clients(cfg_path)
        except Exception as e:
            self._notify("error", "FTP", f"No se pudieron listar clientes.\n\n{e}", 7000)
            self._status("")
            return

        creds = ask_edit_client(parent, clientes)
        if not creds:
            self._status("")
            return

        try:
            self._status("Actualizando credenciales…")
            self._ftp.update_client_credentials(cfg_path, creds.cliente, creds.user, creds.password)
            # ✅ Toast final (éxito)
            self._notify("success", "FTP", f"Cliente modificado: {creds.cliente}", 4000)
        except Exception as e:
            # ✅ Toast final (error)
            self._notify("error", "FTP", f"No se pudo modificar el cliente.\n\n{e}", 7000)
        finally:
            self._status("")

    def delete_client(self) -> None:
        cfg_path = self._get_cfg_path_or_error()
        if not cfg_path:
            return

        parent = self._safe_parent()

        try:
            self._status("Cargando clientes FTP…")
            clientes = self._ftp.list_clients(cfg_path)
        except Exception as e:
            self._notify("error", "FTP", f"No se pudieron listar clientes.\n\n{e}", 7000)
            self._status("")
            return

        # ✅ ask_delete_client YA incluye ConfirmDialog (dialog_kit).
        cliente = ask_delete_client(parent, clientes)
        if not cliente:
            self._status("")
            return

        try:
            self._status("Eliminando cliente FTP…")
            self._ftp.delete_client(cfg_path, cliente)
            # ✅ Toast final (éxito)
            self._notify("success", "FTP", f"Cliente eliminado: {cliente}", 4000)
        except Exception as e:
            # ✅ Toast final (error)
            self._notify("error", "FTP", f"No se pudo eliminar el cliente.\n\n{e}", 7000)
        finally:
            self._status("")
