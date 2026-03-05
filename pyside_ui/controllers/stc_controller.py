# pyside_ui/controllers/stc_controller.py
from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from PySide6 import QtCore, QtWidgets

from pyside_ui.core.Extraer_ips import generate_ip_ranges
from pyside_ui.core.ip_ranges_txt import _find_ipv4, _net24_key, _range24


StatusCb = Callable[[str], None]
NotifyCb = Callable[[str, str, str, int], None]


class StcController(QtCore.QObject):
    """
    Controller para las operaciones del tab STC.
    - db3 a Direc. IP: selecciona archivos DB3, guarda rangos IP en TXT.
    - txt a Direc. IP: selecciona TXT con IPs, genera rangos /24 y guarda.
    """

    def __init__(
        self,
        parent: Optional[QtWidgets.QWidget] = None,
        *,
        status_cb: Optional[StatusCb] = None,
        notify_cb: Optional[NotifyCb] = None,
    ):
        super().__init__(parent)
        self._parent = parent
        self._status_cb = status_cb
        self._notify_cb = notify_cb

    def _status(self, text: str) -> None:
        if self._status_cb:
            self._status_cb(text)

    def _notify(self, level: str, title: str, message: str, timeout_ms: int = 4000) -> None:
        if self._notify_cb:
            self._notify_cb(level, title, message, timeout_ms)

    def procesar_db3_a_ip(self) -> None:
        """Flujo: seleccionar archivos DB3 → elegir dónde guardar → extraer IPs y guardar rangos /24."""
        self._status("")
        parent = self._parent

        files, _ = QtWidgets.QFileDialog.getOpenFileNames(
            parent,
            "Seleccionar archivos DB3 / SQLite",
            "",
            "Archivos SQLite (*.db3 *.db *.sqlite *.sqlite3);;Todos los archivos (*)",
        )
        if not files:
            self._status("")
            return

        save_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            parent,
            "Guardar rangos de IP",
            str(Path(files[0]).parent) if files else "",
            "Archivo de texto (*.txt);;Todos los archivos (*)",
            "*.txt",
        )
        if not save_path:
            self._status("")
            return

        try:
            self._status("Extrayendo direcciones IP…")
            out_path, count = generate_ip_ranges(
                paths=files,
                save_path=save_path,
                parent=None,
                gui_only=True,
            )
            self._status("")
            if count > 0:
                self._notify(
                    "success",
                    "STC",
                    f"Se generaron {count} rango(s) /24.\n{Path(out_path).name}",
                    5000,
                )
            elif out_path:
                self._notify(
                    "info",
                    "STC",
                    "No se encontraron IPs en los archivos. Se creó archivo vacío.",
                    4000,
                )
            else:
                self._notify("warning", "STC", "No se encontraron archivos SQLite válidos.", 4000)
        except Exception as e:
            self._status("")
            self._notify("error", "STC", f"Error al procesar DB3 → IP:\n\n{e}", 6000)

    def procesar_txt_a_ip(self) -> None:
        """Flujo: seleccionar TXT con IPs → elegir dónde guardar → generar rangos /24."""
        self._status("")
        parent = self._parent

        in_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            parent,
            "Seleccionar TXT con IPs",
            "",
            "Archivos de texto (*.txt);;Todos los archivos (*)",
        )
        if not in_path:
            self._status("")
            return

        out_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            parent,
            "Guardar rangos /24",
            str(Path(in_path).parent),
            "Archivos de texto (*.txt);;Todos los archivos (*)",
            "*.txt",
        )
        if not out_path:
            self._status("")
            return

        try:
            self._status("Generando rangos /24…")
            with open(in_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            ips = _find_ipv4(text)
            nets = sorted({_net24_key(ip) for ip in ips})
            ranges = [_range24(a, b, c) for (a, b, c) in nets]
            content = ",".join(ranges)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(content)
            self._status("")
            if ranges:
                self._notify(
                    "success",
                    "STC",
                    f"Se generaron {len(ranges)} rango(s) /24.\n{Path(out_path).name}",
                    5000,
                )
            else:
                self._notify(
                    "info",
                    "STC",
                    "No se encontraron IPv4 válidas. Se creó archivo vacío.",
                    4000,
                )
        except Exception as e:
            self._status("")
            self._notify("error", "STC", f"Error al procesar TXT → IP:\n\n{e}", 6000)
