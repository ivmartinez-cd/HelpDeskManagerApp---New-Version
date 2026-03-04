import os
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List

import numpy as np
import pandas as pd

# Modelos especiales que fuerzan CLASE=20 cuando counterclass_id=40
MODELOS_ESPECIALES = {
    "C4010ND", "CLX_6260_Series", "CLX_9201", "HP_PageWide_Color_MFP_E58650", "X4300LX", "CLP_680_Series",
    "FD_E8_48_50_20_50_61_67_65_57_69_64_65_20_50_72_6F_20_34_35_32_64_77_20_50_72_69_6E_74_65_72",
    "FD_E8_48_50_20_43_6F_6C_6F_72_20_4C_61_73_65_72_4A_65_74_20_4D_46_50_20_4D_35_37_37",
    "Samsung_CLP_680_Series", "CLP_670_Series", "P774ADM05",
    "FD_E8_48_50_20_50_61_67_65_57_69_64_65_20_4D_46_50_20_50_35_37_37_35_30",
    "FD_E8_48_50_20_43_6F_6C_6F_72_20_4C_61_73_65_72_4A_65_74_20_4D_36_35_31",
    "FD_E8_48_50_20_43_6F_6C_6F_72_20_4C_61_73_65_72_4A_65_74_20_4D_36_35_32",
    "FD_E8_48_50_20_4C_61_73_65_72_4A_65_74_20_4D_35_30_36",
    "FD_E8_48_50_20_4C_61_73_65_72_4A_65_74_20_4D_36_30_35",
    "FD_E8_48_50_20_4C_61_73_65_72_4A_65_74_20_4D_36_30_38",
    "HP_PageWide_MFP_P57750", "HP_Color_LaserJet_MFP_M577"
}

# -------------------- utilidades base --------------------

def validar_fecha_ddmmyyyy(fecha: str) -> bool:
    """True si la fecha tiene formato DD/MM/YYYY."""
    try:
        datetime.strptime(fecha, "%d/%m/%Y")
        return True
    except ValueError:
        return False

def _fecha_param(fecha_maxima_str: str) -> str:
    """Convierte 'DD/MM/YYYY' a 'YYYY-MM-DD 00:00:00' + 1 día (límite exclusivo)."""
    dt = datetime.strptime(fecha_maxima_str, "%d/%m/%Y") + timedelta(days=1)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def conectar_db(filename: str) -> sqlite3.Connection:
    """Devuelve una conexión sqlite3; el caller maneja excepciones."""
    return sqlite3.connect(filename)

def verificar_estructura(conn: sqlite3.Connection) -> bool:
    """Chequea columnas esperadas en tabla 'counters'."""
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(counters)")
    cols = {row[1] for row in cur.fetchall()}
    requeridas = {"serialnumber", "readdate", "readvalue", "model", "counterclass_id"}
    return requeridas.issubset(cols)

def ejecutar_consulta(conn: sqlite3.Connection, fecha_maxima: Optional[str]) -> pd.DataFrame:
    """
    Lee counters (clases 40/10/20). Si fecha_maxima (DD/MM/YYYY) se provee, aplica readdate < fecha+1d.
    """
    base_query = (
        "SELECT serialnumber, readdate, readvalue, model, counterclass_id "
        "FROM counters WHERE counterclass_id IN (40,10,20)"
    )
    if fecha_maxima:
        if not validar_fecha_ddmmyyyy(fecha_maxima):
            raise ValueError("fecha_maxima debe tener formato DD/MM/YYYY")
        query = base_query + " AND readdate < ?"
        # parse_dates convierte 'readdate' a datetime ya desde SQL
        return pd.read_sql(query, conn, params=(_fecha_param(fecha_maxima),), parse_dates=["readdate"])
    return pd.read_sql(base_query, conn, parse_dates=["readdate"])

# -------------------- flujo principal DB -> CSV --------------------

def procesar_db_a_csv(
    archivos_db: List[str],
    fecha_maxima: Optional[str],
    nombre_base_salida: str,
    carpeta_salida: Optional[str] = None,
) -> str:
    """
    Une lecturas desde múltiples DB SQLite, aplica reglas TIPO/CLASE y exporta
    CSV en formato ANCHO (columnas para 10 y 20): 
      SERIE, FECHA, TIPO, CLASE_10, CONTADOR_10, CLASE_20, CONTADOR_20, MOTIVO, OBSERVACION
    (UTF-8 sin BOM, CRLF).
    """
    if not archivos_db:
        raise ValueError("Se requiere al menos un archivo de base de datos.")
    if fecha_maxima and not validar_fecha_ddmmyyyy(fecha_maxima):
        raise ValueError("fecha_maxima inválida; use DD/MM/YYYY.")
    if not nombre_base_salida:
        raise ValueError("nombre_base_salida no puede ser vacío.")

    # Leer y unir
    dfs: List[pd.DataFrame] = []
    for path in archivos_db:
        with conectar_db(path) as conn:
            if not verificar_estructura(conn):
                raise RuntimeError(f"Estructura inesperada en DB: {path}")
            df = ejecutar_consulta(conn, fecha_maxima)
            if df is None or df.empty:
                continue
            dfs.append(df)

    if not dfs:
        raise RuntimeError("No se obtuvieron datos de las bases proporcionadas.")

    df = pd.concat(dfs, ignore_index=True)

    # ----- Transformaciones base -----
    # TIPO: 40 -> 15; otros -> 7
    df.insert(df.columns.get_loc("readvalue"), "TIPO", np.where(df["counterclass_id"].eq(40), 15, 7))

    # CLASE (40 + modelo especial -> 20; 40 -> 10; resto mantiene)
    df["CLASE"] = np.where(
        df["counterclass_id"].eq(40) & df["model"].isin(MODELOS_ESPECIALES),
        "20",
        np.where(df["counterclass_id"].eq(40), "10", df["counterclass_id"].astype(str)),
    )

    # Renombrar a finales
    df = df.rename(columns={
        "serialnumber": "SERIE",
        "readdate":     "FECHA",
        "model":        "MODELO",
        "readvalue":    "CONTADOR",
    })

    # Ordenar por fecha (más reciente primero) y formatear
    df["FECHA"] = pd.to_datetime(df["FECHA"], errors="coerce")
    df = df.sort_values("FECHA", ascending=False)
    df["FECHA"] = df["FECHA"].dt.strftime("%d/%m/%Y")

    # Quedarnos con columnas de trabajo
    df = df[["SERIE", "FECHA", "TIPO", "CLASE", "CONTADOR"]]

    # Deduplicar por SERIE+CLASE (conserva la más reciente por el sort previo)
    df = df.drop_duplicates(subset=["SERIE", "CLASE"], keep="first")

    # ---------- Formato ANCHO (dos columnas para 10 y 20) ----------
    # Lado "10": incluye CLASE 10 y también CLASE 20 con TIPO 15 (herencia de total=40→20)
    df10 = df[(df["CLASE"] == "10") | ((df["CLASE"] == "20") & (df["TIPO"] == 15))].copy()
    df10 = df10.rename(columns={"CLASE": "CLASE_10", "CONTADOR": "CONTADOR_10"})

    # Lado "20": todas las CLASE 20
    df20 = df[df["CLASE"] == "20"].copy()
    df20 = df20.rename(columns={"CLASE": "CLASE_20", "CONTADOR": "CONTADOR_20"})

    # Merge por SERIE + FECHA + TIPO
    merged = pd.merge(
        df10[["SERIE", "FECHA", "TIPO", "CLASE_10", "CONTADOR_10"]],
        df20[["SERIE", "FECHA", "TIPO", "CLASE_20", "CONTADOR_20"]],
        on=("SERIE", "FECHA", "TIPO"),
        how="outer"
    )

    # ================== BLOQUE: mover "solo 20" a primera columna ==================
    merged["CONTADOR_10"] = merged["CONTADOR_10"].fillna(0)
    merged["CONTADOR_20"] = merged["CONTADOR_20"].fillna(0)

    mask_only20 = (merged["CONTADOR_10"].eq(0)) & (merged["CONTADOR_20"].gt(0))

    merged.loc[mask_only20, ["CLASE_10", "CONTADOR_10"]] = merged.loc[mask_only20, ["CLASE_20", "CONTADOR_20"]].values
    merged.loc[mask_only20, ["CLASE_20", "CONTADOR_20"]] = ["", 0]

    merged["CONTADOR_10"] = merged["CONTADOR_10"].fillna(0).astype(int)
    merged["CONTADOR_20"] = merged["CONTADOR_20"].fillna(0).astype(int)
    merged["CLASE_10"] = merged["CLASE_10"].fillna("").astype(str)
    merged["CLASE_20"] = merged["CLASE_20"].fillna("").astype(str)
    # ==================================================================

    # ----- Exportación -----
    base_folder = carpeta_salida or os.path.dirname(archivos_db[0]) or os.getcwd()
    os.makedirs(base_folder, exist_ok=True)
    nombre_archivo = f"{nombre_base_salida}_{os.path.basename(base_folder) or 'root'}_AutoCSV.csv"
    file_path = os.path.join(base_folder, nombre_archivo)

    # Ordenar por SERIE/FECHA/TIPO
    out = merged.sort_values(["SERIE", "FECHA", "TIPO"]).copy()

    # Agregar columnas vacías requeridas
    out["MOTIVO"] = ""
    out["OBSERVACION"] = ""

    # Elegir el orden de columnas final (sin renombrar las existentes)
    out = out[[
        "SERIE", "FECHA", "TIPO",
        "CLASE_10", "CONTADOR_10",
        "CLASE_20", "CONTADOR_20",
        "MOTIVO", "OBSERVACION"
    ]]

    # Exportar (UTF-8 sin BOM, CRLF)
    out.to_csv(file_path, sep=";", index=False, encoding="utf-8", lineterminator="\r\n")

    return file_path
