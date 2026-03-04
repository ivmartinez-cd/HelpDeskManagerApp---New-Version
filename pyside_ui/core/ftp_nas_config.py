# ftp_nas_config.py
from __future__ import annotations

import os
import json
from typing import Any, Dict

NAS_APP_DIR = r"\\nas1\nsi\Programas\HelpDeskManagerApp"
NAS_CONFIG_DIR = os.path.join(NAS_APP_DIR, "config")
NAS_FTP_CONFIG = os.path.join(NAS_CONFIG_DIR, "ftp_clientes.json")

FTP_DEFAULTS = {
    "host": "www.cdsisa.com.ar",
    "path": "/",
    "pattern": "PrinterMonitorClient.db3.*",
}


def write_json_atomic(path: str, data: Dict[str, Any]) -> None:
    tmp = path + ".tmp"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def ensure_nas_ftp_config() -> str:
    os.makedirs(NAS_CONFIG_DIR, exist_ok=True)
    if not os.path.isfile(NAS_FTP_CONFIG):
        write_json_atomic(NAS_FTP_CONFIG, {})
    return NAS_FTP_CONFIG


def read_raw_cfg(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, dict):
            return raw
        return {}
    except Exception:
        return {}


def upsert_client_minimal(path: str, cliente: str, user: str, password: str) -> None:
    """
    Inserta/actualiza cliente con estructura existente:
    {
      "Dos Anclas": {"host":..., "user":..., "password":..., "path":..., "pattern":...}
    }
    """
    raw = read_raw_cfg(path)
    raw[cliente] = {
        "host": FTP_DEFAULTS["host"],
        "user": user,
        "password": password,
        "path": FTP_DEFAULTS["path"],
        "pattern": FTP_DEFAULTS["pattern"],
    }
    write_json_atomic(path, raw)
