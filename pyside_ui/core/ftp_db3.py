# core/ftp_db3.py
from __future__ import annotations

import os
import json
import tempfile
import fnmatch
import sqlite3
from datetime import datetime
from ftplib import FTP
from pathlib import Path
from typing import Dict, Optional, Callable, Tuple, List, Any


def load_ftp_config(config_path: str) -> Dict[str, Dict[str, str]]:
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("El JSON de FTP debe ser un objeto (dict) con clientes como keys.")

    normalized: Dict[str, Dict[str, str]] = {}
    for k, v in data.items():
        if not isinstance(v, dict):
            continue
        normalized[str(k).strip().upper()] = {str(kk): str(vv) for kk, vv in v.items()}
    return normalized


def _list_remote_files(
    ftp: FTP,
    pattern: str,
    *,
    status_cb: Optional[Callable[[str], None]] = None,
) -> List[str]:
    if status_cb:
        status_cb("Buscando archivo…")

    files = ftp.nlst()
    candidatos = [f for f in files if fnmatch.fnmatch(f.lower(), pattern.lower())]
    if not candidatos:
        if status_cb:
            status_cb("No hay archivos disponibles")
        raise FileNotFoundError(f"No encontré archivos con patrón '{pattern}' en el directorio FTP actual.")

    candidatos.sort()
    return candidatos


def _pick_remote_file(
    ftp: FTP,
    pattern: str,
    *,
    status_cb: Optional[Callable[[str], None]] = None,
) -> str:
    return _list_remote_files(ftp, pattern, status_cb=status_cb)[-1]


def download_db3_from_ftp(
    cliente: str,
    *,
    cfg_map: Dict[str, Dict[str, str]],
    dest_path: Optional[str] = None,
    timeout: int = 8,
    status_cb: Optional[Callable[[str], None]] = None,
) -> Tuple[str, str]:
    key = (cliente or "").strip().upper()
    cfg = cfg_map.get(key)
    if not cfg:
        raise ValueError(f"Cliente '{cliente}' no configurado en el JSON.")

    host = cfg["host"]
    user = cfg["user"]
    password = cfg["password"]
    path = cfg.get("path", "/")
    pattern = cfg.get("pattern", "*.db3")

    if not dest_path:
        fd, dest_path = tempfile.mkstemp(suffix=".db3")
        os.close(fd)

    ftp = FTP(host, timeout=timeout)
    try:
        if status_cb:
            status_cb(f"Conectando a FTP: {host} ...")

        ftp.login(user, password)
        ftp.cwd(path)

        remoto = _pick_remote_file(ftp, pattern, status_cb=status_cb)

        if status_cb:
            status_cb(f"Descargando: {key} → {remoto}")

        with open(dest_path, "wb") as f:
            ftp.retrbinary(f"RETR {remoto}", f.write)

        if status_cb:
            status_cb("Descarga completa")

        return dest_path, remoto

    finally:
        # IMPORTANTE: quit() puede colgarse esperando respuesta del server.
        # close() corta el socket sin handshake -> el worker termina siempre.
        try:
            ftp.close()
        except Exception:
            pass


def _merge_db3_files(
    local_files: List[str],
    merged_path: str,
    *,
    status_cb: Optional[Callable[[str], None]] = None,
) -> str:
    """
    Une múltiples SQLite DB3 en uno solo SIN usar ATTACH DATABASE.
    Evita 'database src is already in use' y el límite de attach.

    Estrategia:
    - Copia schema desde el DB base (último archivo).
    - Copia filas tabla por tabla.
    - Si hay PK INTEGER simple, inserta sin esa PK.
    - Los originales NO se borran.
    """
    if not local_files:
        raise ValueError("No hay archivos para fusionar.")
    if len(local_files) == 1:
        return local_files[0]

    base_db = local_files[-1]
    os.makedirs(os.path.dirname(merged_path), exist_ok=True)

    if status_cb:
        status_cb(f"Fusionando {len(local_files)} DB3 en: {os.path.basename(merged_path)}")

    base_con = sqlite3.connect(base_db)
    base_con.row_factory = sqlite3.Row
    try:
        schema_rows = base_con.execute(
            """
            SELECT type, name, sql
            FROM sqlite_master
            WHERE sql IS NOT NULL
              AND name NOT LIKE 'sqlite_%'
            ORDER BY
              CASE type
                WHEN 'table' THEN 1
                WHEN 'view' THEN 2
                WHEN 'index' THEN 3
                WHEN 'trigger' THEN 4
                ELSE 99
              END,
              name
            """
        ).fetchall()
    finally:
        base_con.close()

    merged_con = sqlite3.connect(merged_path)
    merged_con.row_factory = sqlite3.Row

    try:
        merged_con.execute("PRAGMA foreign_keys=OFF;")
        merged_con.execute("BEGIN;")
        for r in schema_rows:
            sql = (r["sql"] or "").strip()
            if sql:
                merged_con.execute(sql)
        merged_con.execute("COMMIT;")
    except Exception:
        merged_con.rollback()
        merged_con.close()
        raise

    tables = merged_con.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table'
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    ).fetchall()
    table_names = [t["name"] for t in tables]

    def get_table_columns_and_pk(con, table: str):
        info = con.execute(f'PRAGMA table_info("{table}");').fetchall()
        cols = [row["name"] for row in info]
        pk_cols = [row for row in info if int(row["pk"] or 0) == 1]
        if len(pk_cols) == 1:
            pk = pk_cols[0]["name"]
            is_int_pk = str(pk_cols[0]["type"] or "").upper() == "INTEGER"
            return cols, pk, is_int_pk
        return cols, None, False

    try:
        merged_con.execute("PRAGMA foreign_keys=OFF;")
        merged_con.execute("BEGIN;")

        total = len(local_files)

        for idx, src in enumerate(local_files, start=1):
            if status_cb:
                status_cb(f"Importando ({idx}/{total}): {os.path.basename(src)}")

            src_con = sqlite3.connect(src)
            src_con.row_factory = sqlite3.Row

            try:
                for table in table_names:
                    exists = src_con.execute(
                        """
                        SELECT 1
                        FROM sqlite_master
                        WHERE type='table' AND name=?
                        """,
                        (table,),
                    ).fetchone()
                    if not exists:
                        continue

                    cols, pk, is_int_pk = get_table_columns_and_pk(merged_con, table)

                    if pk and is_int_pk and pk in cols:
                        cols_wo_pk = [c for c in cols if c != pk]
                        if not cols_wo_pk:
                            continue
                        col_list = ", ".join([f'"{c}"' for c in cols_wo_pk])
                        rows = src_con.execute(f'SELECT {col_list} FROM "{table}";').fetchall()
                        for row in rows:
                            merged_con.execute(
                                f'INSERT INTO "{table}" ({col_list}) VALUES ({",".join(["?"]*len(row))});',
                                tuple(row),
                            )
                    else:
                        col_list = ", ".join([f'"{c}"' for c in cols])
                        rows = src_con.execute(f'SELECT {col_list} FROM "{table}";').fetchall()
                        for row in rows:
                            merged_con.execute(
                                f'INSERT OR IGNORE INTO "{table}" ({col_list}) VALUES ({",".join(["?"]*len(row))});',
                                tuple(row),
                            )
            finally:
                src_con.close()

        merged_con.execute("COMMIT;")

        if status_cb:
            status_cb("Fusión finalizada.")

        return merged_path

    except Exception:
        merged_con.rollback()
        raise

    finally:
        merged_con.close()


def download_db3_many_from_ftp(
    cliente: str,
    *,
    cfg_map: Dict[str, Dict[str, str]],
    dest_dir: str,
    timeout: int = 8,
    status_cb: Optional[Callable[[str], None]] = None,
) -> Tuple[List[str], List[str]]:
    """
    Descarga TODOS los archivos remotos que matchean pattern.
    Si se descargan >1, genera un DB3 merged con timestamp (sin borrar originales)
    y devuelve solo ese merged como lista de 1 elemento.

    Devuelve: (lista_paths_locales, lista_nombres_remotos)
    """
    key = (cliente or "").strip().upper()
    cfg = cfg_map.get(key)
    if not cfg:
        raise ValueError(f"Cliente '{cliente}' no configurado en el JSON.")

    host = cfg["host"]
    user = cfg["user"]
    password = cfg["password"]
    path = cfg.get("path", "/")
    pattern = cfg.get("pattern", "*.db3")

    os.makedirs(dest_dir, exist_ok=True)

    ftp = FTP(host, timeout=timeout)
    try:
        if status_cb:
            status_cb(f"Conectando a FTP: {host} ...")

        ftp.login(user, password)
        ftp.cwd(path)

        remotos = _list_remote_files(ftp, pattern, status_cb=status_cb)

        locales: List[str] = []
        total = len(remotos)

        for i, remoto in enumerate(remotos, start=1):
            local_path = os.path.join(dest_dir, os.path.basename(remoto))

            if status_cb:
                status_cb(f"Descargando ({i}/{total}): {key} → {remoto}")

            with open(local_path, "wb") as f:
                ftp.retrbinary(f"RETR {remoto}", f.write)

            locales.append(local_path)

        if len(locales) > 1:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            merged_name = f"MERGED_{key}_{stamp}.db3"
            merged_path = os.path.join(dest_dir, merged_name)

            merged_path = _merge_db3_files(locales, merged_path, status_cb=status_cb)

            if status_cb:
                status_cb("Descarga completa")

            return [merged_path], remotos

        if status_cb:
            status_cb("Descarga completa")

        return locales, remotos

    finally:
        try:
            ftp.close()
        except Exception:
            pass


def safe_remove(path: str) -> None:
    try:
        os.remove(path)
    except Exception:
        pass


REQUIRED_FIELDS = ("host", "user", "password", "path", "pattern")


def load_ftp_config_raw(config_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Lee el JSON de FTP preservando NOMBRES originales de clientes (keys),
    sin normalizarlas a UPPER().
    Ideal para UI de Agregar/Modificar.
    """
    if not Path(config_path).exists():
        return {}

    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("El JSON de FTP debe ser un objeto (dict) con clientes como keys.")

    out: Dict[str, Dict[str, Any]] = {}
    for k, v in data.items():
        if isinstance(k, str) and isinstance(v, dict):
            out[k] = dict(v)
    return out


def _atomic_write_json(path: str, data: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(p)


def save_ftp_config_raw(config_path: str, data: Dict[str, Dict[str, Any]]) -> None:
    if not isinstance(data, dict):
        raise ValueError("data debe ser dict.")
    _atomic_write_json(config_path, data)


def validate_ftp_client_cfg(cfg: Dict[str, Any]) -> None:
    if not isinstance(cfg, dict):
        raise ValueError("La configuración del cliente debe ser un objeto (dict).")

    missing = [k for k in REQUIRED_FIELDS if not cfg.get(k)]
    if missing:
        raise ValueError(f"Faltan campos requeridos: {', '.join(missing)}")

    if not isinstance(cfg["host"], str) or not cfg["host"].strip():
        raise ValueError("host inválido.")
    if not isinstance(cfg["user"], str) or not cfg["user"].strip():
        raise ValueError("user inválido.")
    if not isinstance(cfg["password"], str):
        raise ValueError("password inválido.")
    if not isinstance(cfg["path"], str) or not cfg["path"].startswith("/"):
        raise ValueError("path inválido (debe comenzar con '/').")
    if not isinstance(cfg["pattern"], str) or not cfg["pattern"].strip():
        raise ValueError("pattern inválido.")


def add_ftp_client_to_json(config_path: str, client_name: str, cfg: Dict[str, Any]) -> None:
    name = (client_name or "").strip()
    if not name:
        raise ValueError("Nombre de cliente vacío.")

    data = load_ftp_config_raw(config_path)

    if name in data:
        raise ValueError(f"El cliente '{name}' ya existe.")

    validate_ftp_client_cfg(cfg)

    data[name] = {
        "host": str(cfg["host"]).strip(),
        "user": str(cfg["user"]).strip(),
        "password": str(cfg["password"]),
        "path": str(cfg["path"]).strip(),
        "pattern": str(cfg["pattern"]).strip(),
    }

    save_ftp_config_raw(config_path, data)


def update_ftp_client_in_json(config_path: str, client_name: str, cfg: Dict[str, Any]) -> None:
    name = (client_name or "").strip()
    if not name:
        raise ValueError("Nombre de cliente vacío.")

    data = load_ftp_config_raw(config_path)

    if name not in data:
        raise ValueError(f"El cliente '{name}' no existe.")

    validate_ftp_client_cfg(cfg)

    data[name] = {
        "host": str(cfg["host"]).strip(),
        "user": str(cfg["user"]).strip(),
        "password": str(cfg["password"]),
        "path": str(cfg["path"]).strip(),
        "pattern": str(cfg["pattern"]).strip(),
    }

    save_ftp_config_raw(config_path, data)


def list_ftp_clients_from_json(config_path: str) -> List[str]:
    return sorted(load_ftp_config_raw(config_path).keys())
