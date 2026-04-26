import os
from datetime import datetime
from typing import Optional

import pandas as pd


def _validar_fecha_dmy(fecha: str) -> None:
    """Valida formato DD/MM/YYYY; lanza ValueError si no cumple."""
    try:
        datetime.strptime(fecha, "%d/%m/%Y")
    except ValueError:
        raise ValueError("fecha_nueva debe tener formato DD/MM/YYYY")


def filtrar_falta_contador_csv(
    archivo_csv_entrada: str,
    fecha_nueva: str,
    nombre_cliente: str,
    carpeta_salida: Optional[str] = None,
    delimiter_entrada: str = ",",
) -> str:
    """
    Filtra filas con Tipo == 'FALTA CONTADOR', normaliza columnas y exporta CSV.
    - fecha_nueva: string DD/MM/YYYY (se escribe en la columna FECHA)
    - nombre_cliente: se usa para armar el nombre del archivo de salida
    - carpeta_salida: si no se indica, usa la carpeta del CSV de entrada
    - delimiter_entrada: separador del CSV de entrada (por defecto coma)

    Devuelve: ruta completa del archivo CSV generado.
    """
    # Validaciones básicas
    if not os.path.isfile(archivo_csv_entrada):
        raise FileNotFoundError(f"No existe el archivo: {archivo_csv_entrada}")
    if not nombre_cliente:
        raise ValueError("nombre_cliente es obligatorio")
    if not fecha_nueva:
        raise ValueError("fecha_nueva es obligatoria")
    _validar_fecha_dmy(fecha_nueva)

    # Leer CSV
    try:
        datos = pd.read_csv(archivo_csv_entrada, delimiter=delimiter_entrada)
    except Exception as exc:
        raise ValueError(f"No se pudo leer el CSV de entrada: {exc}") from exc

    # Chequeo de columna clave
    if "Tipo" not in datos.columns:
        raise KeyError("La columna 'Tipo' no existe en el CSV de entrada.")

    # Filtrar 'FALTA CONTADOR' (Mono / Color incluidos)
    datos = datos[
        datos["Tipo"].isin([
            "FALTA CONTADOR",
            "FALTA CONTADOR Mono",
            "FALTA CONTADOR Color",
        ])
    ].copy()

    if datos.empty:
        raise ValueError("No se encontraron filas con Tipo == 'FALTA CONTADOR'.")

    # Columnas a eliminar si existen
    cols_drop = [
        "Empresa1", "Sucursal1", "Articulo1", "Sector1", "FechaTomaContadorActual",
        "ContActual", "Impresiones_Realizadas", "BackupDe", "CenCosto",
    ]
    datos.drop(columns=[c for c in cols_drop if c in datos.columns], inplace=True, errors="ignore")

    # Renombres si existen esas columnas originales
    rename_map = {
        "Nro_serie": "SERIE",
        "FechaTomaContadorAnterior1": "FECHA",
        "ImpreContadorAnterior": "CONTADOR",
    }
    to_rename = {k: v for k, v in rename_map.items() if k in datos.columns}
    if to_rename:
        datos.rename(columns=to_rename, inplace=True)

    # Asegurar columnas destino y asignar valores
    if "SERIE" not in datos.columns:
        raise KeyError("No se encontró la columna 'SERIE' ni 'Nro_serie' para renombrar.")
    if "CONTADOR" not in datos.columns:
        raise KeyError("No se encontró la columna 'CONTADOR' ni 'ImpreContadorAnterior' para renombrar.")

    datos["FECHA"] = fecha_nueva  # DD/MM/YYYY
    if "TIPO" not in datos.columns:
        datos["TIPO"] = ""
    if "CLASE" not in datos.columns:
        datos["CLASE"] = ""

    # Mapear CLASE desde NombreClase si existe (Color -> 20, resto -> 10)
    if "NombreClase" in datos.columns:
        datos.loc[datos["NombreClase"] == "Color", "CLASE"] = "20"
        datos.loc[datos["NombreClase"] != "Color", "CLASE"] = "10"

    # Forzar TIPO = 14 como en tu lógica original
    datos["TIPO"] = "14"

    # Inicializar columnas
    datos["CLASE_10"] = ""
    datos["CONTADOR_10"] = 0
    datos["CLASE_20"] = ""
    datos["CONTADOR_20"] = 0

    # Asignar según clase
    es_color = datos["CLASE"] == "20"

    # Color → CLASE_20
    datos.loc[es_color, "CLASE_20"] = "20"
    datos.loc[es_color, "CONTADOR_20"] = datos.loc[es_color, "CONTADOR"]

    # Mono → CLASE_10
    datos.loc[~es_color, "CLASE_10"] = "10"
    datos.loc[~es_color, "CONTADOR_10"] = datos.loc[~es_color, "CONTADOR"]

    # Limpiar columnas que ya no necesitamos
    for c in ("Tipo", "NombreClase", "CLASE", "CONTADOR"):
        if c in datos.columns:
            datos.drop(columns=c, inplace=True, errors="ignore")

    # Agregar columnas vacías requeridas al final
    datos["MOTIVO"] = ""
    datos["OBSERVACION"] = ""

    # Definir el orden y subconjunto exacto de columnas
    columnas_finales = [
        "SERIE",
        "FECHA",
        "TIPO",
        "CLASE_10",
        "CONTADOR_10",
        "CLASE_20",
        "CONTADOR_20",
        "MOTIVO",
        "OBSERVACION",
    ]

    # Asegurar que existan todas las columnas requeridas
    for col in columnas_finales:
        if col not in datos.columns:
            datos[col] = ""

    datos = datos[columnas_finales]

    # Consolidar una sola fila por SERIE
    datos = (
        datos
        .groupby(["SERIE", "FECHA", "TIPO"], as_index=False)
        .agg({
            "CLASE_10": "first",
            "CONTADOR_10": "max",
            "CLASE_20": "first",
            "CONTADOR_20": "max",
            "MOTIVO": "first",
            "OBSERVACION": "first",
        })
    )

    # --- FIX: si SOLO existe clase 20, moverla a la primera columna ---
    # Condición: tiene CLASE_20=20 y no tiene CLASE_10 (vacía) y contador_10 es 0 o NaN
    cl10_vacia = (datos["CLASE_10"].astype(str).str.strip() == "") | (datos["CLASE_10"].isna())
    c10_cero = datos["CONTADOR_10"].isna() | (datos["CONTADOR_10"] == 0)

    solo_color = (datos["CLASE_20"].astype(str).str.strip() == "20") & cl10_vacia & c10_cero

    # Shift a la izquierda
    datos.loc[solo_color, "CLASE_10"] = "20"
    datos.loc[solo_color, "CONTADOR_10"] = datos.loc[solo_color, "CONTADOR_20"]
    datos.loc[solo_color, "CLASE_20"] = ""
    datos.loc[solo_color, "CONTADOR_20"] = 0
    # --- FIN FIX ---

    # Salida
    carpeta_base = carpeta_salida or os.path.dirname(archivo_csv_entrada)
    nombre_carpeta = os.path.basename(carpeta_base) or os.path.basename(os.path.dirname(archivo_csv_entrada))
    nombre_archivo = f"{nombre_cliente}_{nombre_carpeta}_CSVen0.csv"
    ruta_salida = os.path.join(carpeta_base, nombre_archivo)

    # Exportar (UTF-8 sin BOM, CRLF)
    datos.to_csv(ruta_salida, sep=";", index=False, encoding="utf-8", lineterminator="\r\n")

    return ruta_salida
