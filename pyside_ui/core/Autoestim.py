# Autoestim.py
# Genera 2 CSV:
# 1) import_autoestim_*.csv  -> listo para importar (formato "import")
# 2) formato_14_10_20_*.csv  -> columnas SERIE, FECHA, TIPO(14), CLASE10(10),
#                              CONTADOR (si Mono), CLASE20(20), CONTADOR20 (si Color),
#                              MOTIVO, OBSERVACIONES
#
# Uso:
#   python Autoestim.py

import pandas as pd
from pathlib import Path
from datetime import datetime, date


# =========================
# 1) CARGA
# =========================
def cargar_csv_detalle(ruta_csv: str) -> pd.DataFrame:
    ruta = Path(ruta_csv)
    if not ruta.exists():
        raise FileNotFoundError(f"No existe el archivo: {ruta}")

    # Autodetección de separador (',' o ';') + soporte BOM de Excel
    df = pd.read_csv(
        ruta,
        sep=None,
        engine="python",
        encoding="utf-8-sig",
    )

    # Limpieza de headers por las dudas
    df.columns = df.columns.astype(str).str.strip()
    return df


# =========================
# 2) LIMPIEZA DE COLUMNAS
# =========================
def limpiar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Elimina columnas innecesarias, PERO mantiene 'NombreClase' (Mono/Color).
    """
    columnas_a_eliminar = [
        "Empresa1",
        "Sucursal1",
        "Articulo1",
        "Sector1",
        "BackupDe",
        "CenCosto",
        # "NombreClase",  # <-- NO borrar: se usa para Mono/Color
        "Estado_Maquina",
        "Direccion_IP",
        "Mascara_IP",
    ]
    return df.drop(columns=[c for c in columnas_a_eliminar if c in df.columns])


# =========================
# 3) FILTRO Tipo = Estimado
# =========================
def filtrar_tipo_estimado(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filtra el dataframe dejando solo filas con Tipo = 'Estimado' (case-insensitive).
    """
    if "Tipo" not in df.columns:
        raise KeyError(
            f"No existe la columna 'Tipo'. Columnas disponibles: {df.columns.tolist()}"
        )

    df = df.copy()
    df["Tipo"] = df["Tipo"].astype(str).str.strip()

    return df[df["Tipo"].str.lower() == "estimado"].copy()


# =========================
# 4) NORMALIZACIONES
# =========================
def normalizar_campos(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Serie
    if "Nro_serie" in df.columns:
        df["Nro_serie"] = df["Nro_serie"].astype(str).str.strip().str.upper()

    # NombreClase (Mono/Color)
    if "NombreClase" in df.columns:
        df["NombreClase"] = df["NombreClase"].astype(str).str.strip()

    # Fechas
    for col in ["FechaTomaContadorAnterior1", "FechaTomaContadorActual"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")

    # Números
    for col in ["ImpreContadorAnterior", "ContActual", "Impresiones_Realizadas"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    return df


# =========================
# 5) NUEVA TOMA
# =========================
def agregar_nueva_toma(df: pd.DataFrame, fecha_nueva: str | None = None) -> pd.DataFrame:
    """
    Agrega:
      - FechaTomaContadorNueva
      - Impresiones_Estimadas_Nueva
      - ContadorNuevo
    Regla: si Impresiones_Realizadas = 0, el contador queda igual.
    """
    df = df.copy()

    if fecha_nueva is None:
        fecha_nueva = date.today().strftime("%d/%m/%Y")

    for col in ["ContActual", "Impresiones_Realizadas"]:
        if col not in df.columns:
            raise KeyError(f"Falta la columna requerida: '{col}'")

    df["FechaTomaContadorNueva"] = fecha_nueva
    df["Impresiones_Estimadas_Nueva"] = df["Impresiones_Realizadas"]
    df["ContadorNuevo"] = df["ContActual"] + df["Impresiones_Realizadas"]

    return df


# =========================
# 6) CSV 1: IMPORTACIÓN
# =========================
def preparar_csv_importacion(df: pd.DataFrame) -> pd.DataFrame:
    """
    Arma el CSV de importación general.
    """
    df = df.copy()

    if "Nro_serie" in df.columns and "SERIE" not in df.columns:
        df["SERIE"] = df["Nro_serie"]

    columnas_import = [
        "SERIE",
        "FechaTomaContadorNueva",
        "ContadorNuevo",
        "Impresiones_Estimadas_Nueva",
        "FechaTomaContadorActual",
        "ContActual",
        "Impresiones_Realizadas",
        "Tipo",
        "NombreClase",  # útil para trazabilidad
    ]
    columnas_import = [c for c in columnas_import if c in df.columns]
    df_out = df[columnas_import].copy()

    # Formato de fecha para columnas datetime
    for col in ["FechaTomaContadorActual"]:
        if col in df_out.columns and pd.api.types.is_datetime64_any_dtype(df_out[col]):
            df_out[col] = df_out[col].dt.strftime("%d/%m/%Y")

    return df_out


# =========================
# 7) CSV 2: FORMATO 14 / 10 / 20 con Mono/Color
# =========================
def preparar_csv_formato_14_10_20(
    df: pd.DataFrame,
    fecha_hoy: str | None = None
) -> pd.DataFrame:
    """
    Genera el CSV adicional con columnas:
    SERIE, FECHA, TIPO(14),
    CLASE10(10), CONTADOR,
    CLASE20(20), CONTADOR20,
    MOTIVO, OBSERVACIONES

    Regla:
    - NombreClase == 'Mono'  -> CONTADOR (clase 10)
    - NombreClase == 'Color' -> CONTADOR20 (clase 20)
    """
    if fecha_hoy is None:
        fecha_hoy = date.today().strftime("%d/%m/%Y")

    df = df.copy()

    # Asegurar SERIE
    if "SERIE" not in df.columns:
        if "Nro_serie" in df.columns:
            df["SERIE"] = df["Nro_serie"]
        else:
            raise KeyError("No existe 'SERIE' ni 'Nro_serie' para armar el CSV 2")

    if "ContadorNuevo" not in df.columns:
        raise KeyError("No existe la columna 'ContadorNuevo' para armar el CSV 2")

    if "NombreClase" not in df.columns:
        raise KeyError("No existe la columna 'NombreClase' (Mono/Color) para armar el CSV 2")

    # Normalizamos NombreClase para comparar
    clase = df["NombreClase"].astype(str).str.strip().str.lower()

    # Si Mono => contador en clase10; si Color => contador en clase20
    contador_nuevo = pd.to_numeric(df["ContadorNuevo"], errors="coerce").fillna(0).astype(int)

    contador10 = contador_nuevo.where(clase.eq("mono"), other="")
    contador20 = contador_nuevo.where(clase.eq("color"), other="")

    df2 = pd.DataFrame({
        "SERIE": df["SERIE"].astype(str).str.strip().str.upper(),
        "FECHA": fecha_hoy,
        "TIPO": 14,
        "CLASE10": 10,
        "CONTADOR": contador10,
        "CLASE20": 20,
        "CONTADOR20": contador20,
        "MOTIVO": "",
        "OBSERVACIONES": "",
    })

    return df2


# =========================
# 8) ORQUESTADOR: GENERA 2 CSV
# =========================
def ejecutar_generacion_dos_csv(
    ruta_csv_detalle: str,
    salida_import: str | None = None,
    salida_formato: str | None = None,
    fecha_nueva: str | None = None,
) -> tuple[str, str]:
    df = cargar_csv_detalle(ruta_csv_detalle)
    df = limpiar_columnas(df)
    df = filtrar_tipo_estimado(df)

    if df.empty:
        raise ValueError(
            "No se encontraron registros con Tipo = 'Estimado'. "
            "No se generaron archivos de salida."
        )

    df = normalizar_campos(df)
    df = agregar_nueva_toma(df, fecha_nueva=fecha_nueva)

    df_import = preparar_csv_importacion(df)
    df_formato = preparar_csv_formato_14_10_20(
        df, fecha_hoy=(fecha_nueva or date.today().strftime("%d/%m/%Y"))
    )

    ruta_in = Path(ruta_csv_detalle)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if salida_import is None:
        salida_import = ruta_in.with_name(f"import_autoestim_{stamp}.csv")
    if salida_formato is None:
        salida_formato = ruta_in.with_name(f"formato_14_10_20_{stamp}.csv")

    # Exportamos con coma (ajustar si tu importador necesita ';')
    df_import.to_csv(salida_import, index=False, sep=",", encoding="utf-8")
    df_formato.to_csv(salida_formato, index=False, sep=",", encoding="utf-8")

    return str(salida_import), str(salida_formato)


# =========================
# SOLICITUD DE FECHA A ESTIMAR
# =========================
def pedir_fecha_estimacion() -> str:
    """
    Pide la fecha de estimación por consola en formato dd/mm/aaaa.
    Acepta Enter para usar la fecha de hoy.
    Devuelve string dd/mm/aaaa.
    """
    while True:
        entrada = input("Ingresá la FECHA de estimación (dd/mm/aaaa) [Enter = hoy]: ").strip()

        if entrada == "":
            return date.today().strftime("%d/%m/%Y")

        try:
            datetime.strptime(entrada, "%d/%m/%Y")
            return entrada
        except ValueError:
            print("❌ Formato inválido. Usá dd/mm/aaaa (ej: 14/01/2026).")


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    ruta_csv = "Detalle de contadores por nro de proceso.csv"

    fecha_estimacion = pedir_fecha_estimacion()

    out1, out2 = ejecutar_generacion_dos_csv(
        ruta_csv_detalle=ruta_csv,
        fecha_nueva=fecha_estimacion
    )

    print("✅ CSV 1 (importación) generado en:")
    print(out1)
    print("\n✅ CSV 2 (formato 14/10/20) generado en:")
    print(out2)
