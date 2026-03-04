# pyside_ui/services/ftp_service.py
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable, Dict, Any, Optional, Tuple, List

# Reutilizamos la lógica EXISTENTE del repo Tkinter (negocio, sin UI)
from pyside_ui.core.ftp_db3 import (
    load_ftp_config,
    load_ftp_config_raw,
    save_ftp_config_raw,
    list_ftp_clients_from_json,
    download_db3_from_ftp,
    download_db3_many_from_ftp,
    safe_remove,
)
from pyside_ui.core.ftp_nas_config import ensure_nas_ftp_config, upsert_client_minimal

StatusCb = Callable[[str], None]


@dataclass(frozen=True)
class DownloadResult:
    local_path: str
    remote_name: str


class FtpService:
    """
    Service de FTP (Qt-agnóstico). La UI (PySide6) solo llama a esto y decide cómo mostrar errores.

    - Mantiene compatibilidad con la estructura actual del JSON en NAS:
      {
        "Dos Anclas": {"host":..., "user":..., "password":..., "path":..., "pattern":...}
      }
    """

    def load_cfg(self) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        Devuelve (cfg_map, cfg_path).
        Si no hay config, devuelve ({}, None) o ({}, <path>) según disponibilidad.
        """
        try:
            cfg_path = ensure_nas_ftp_config()
            if cfg_path and os.path.isfile(cfg_path):
                return load_ftp_config(cfg_path), cfg_path
            return {}, cfg_path
        except Exception:
            # Mismo comportamiento del servicio Tkinter: no rompe UI
            return {}, None

    def ensure_cfg_path(self) -> str:
        """
        Garantiza que exista el archivo en NAS y devuelve la ruta.
        Lanza excepción si algo sale mal de forma explícita.
        """
        cfg_path = ensure_nas_ftp_config()
        if not cfg_path:
            raise RuntimeError("No se pudo determinar la ruta del config FTP en NAS.")
        return cfg_path

    def list_clients(self, cfg_path: str) -> List[str]:
        return list_ftp_clients_from_json(cfg_path)

    def upsert_client(self, cfg_path: str, cliente: str, user: str, password: str) -> None:
        """
        Agrega o actualiza cliente (comportamiento existente).
        """
        upsert_client_minimal(cfg_path, cliente, user, password)

    def update_client_credentials(self, cfg_path: str, cliente: str, user: str, password: str) -> None:
        """
        MODIFICAR estrictamente: solo cambia user/password si el cliente ya existe.
        No crea clientes nuevos.
        """
        data = load_ftp_config_raw(cfg_path)
        if cliente not in data:
            raise ValueError(f"El cliente '{cliente}' no existe.")

        # Preservar el resto de campos (host/path/pattern)
        data[cliente]["user"] = user
        data[cliente]["password"] = password
        save_ftp_config_raw(cfg_path, data)

    def delete_client(self, cfg_path: str, cliente: str) -> None:
        """
        Elimina un cliente existente del JSON.
        Lanza error si no existe.
        """
        data = load_ftp_config_raw(cfg_path)
        if cliente not in data:
            raise ValueError(f"El cliente '{cliente}' no existe.")
        del data[cliente]
        save_ftp_config_raw(cfg_path, data)

    # -------------------------
    # Descargas (con estados y excepciones tipo Tkinter)
    # -------------------------
    def download_latest_db3(
        self,
        cfg_map: Dict[str, Any],
        cliente: str,
        dest_dir: str,
        status_cb: Optional[StatusCb] = None,
    ) -> DownloadResult:
        """
        Descarga 1 DB3 (el último). Garantiza:
        - Status inicial y final
        - Si no hay remoto, levanta FileNotFoundError (igual Tkinter)
        """
        os.makedirs(dest_dir, exist_ok=True)
        local_path = os.path.join(dest_dir, f"{cliente}.db3")

        def say(msg: str) -> None:
            if status_cb:
                status_cb(msg)

        try:
            say("Conectando…")
            # El core puede emitir más estados, pero no dependemos de eso.
            local_path_out, remote_name = download_db3_from_ftp(
                cliente,
                cfg_map=cfg_map,
                dest_path=local_path,
                status_cb=status_cb,
            )

            # Igual que Tkinter: si no hay nada para bajar, se considera “no hay archivos”
            if not remote_name:
                raise FileNotFoundError("No hay archivos disponibles para descargar.")

            say("Descarga completa")
            return DownloadResult(local_path=local_path_out, remote_name=remote_name)

        except FileNotFoundError:
            say("No hay archivos disponibles")
            raise
        except Exception as e:
            say(f"Error FTP: {e}")
            raise

    def download_many_db3(
        self,
        cfg_map: Dict[str, Any],
        cliente: str,
        dest_dir: str,
        status_cb: Optional[StatusCb] = None,
    ) -> DownloadResult:
        """
        Descarga múltiples DB3 y devuelve el último (o el merged).
        Garantiza status final y error tipo Tkinter.
        """
        os.makedirs(dest_dir, exist_ok=True)

        def say(msg: str) -> None:
            if status_cb:
                status_cb(msg)

        try:
            say("Conectando…")
            locales, remotos = download_db3_many_from_ftp(
                cliente,
                cfg_map=cfg_map,
                dest_dir=dest_dir,
                status_cb=status_cb,
            )

            if not locales:
                raise FileNotFoundError("No hay archivos disponibles para descargar.")

            local_path = locales[-1]
            remote_name = remotos[-1] if remotos else ""
            if not remote_name:
                # si core no reportó nombres, igual lo tratamos como “sin archivos”
                raise FileNotFoundError("No hay archivos disponibles para descargar.")

            say("Descarga completa")
            return DownloadResult(local_path=local_path, remote_name=remote_name)

        except FileNotFoundError:
            say("No hay archivos disponibles")
            raise
        except Exception as e:
            say(f"Error FTP: {e}")
            raise
