import os
import numpy as np
import pandas as pd
from datetime import datetime


def _validar_fecha_ddmmyyyy(fecha_usuario: str) -> str:
    if not fecha_usuario:
        raise ValueError("No se ingresó ninguna fecha.")
    try:
        return datetime.strptime(fecha_usuario, "%d/%m/%Y").strftime("%d/%m/%Y")
    except ValueError:
        raise ValueError("La fecha ingresada no tiene el formato correcto (DD/MM/AAAA).")


def _procesar_un_excel_a_df(archivo_xls: str, fecha_actual: str, hojas_a_sumar: int) -> pd.DataFrame:
    # leer excel
    try:
        datos = pd.read_excel(archivo_xls)
    except Exception as e:
        raise RuntimeError(f"No se pudo leer:\n{archivo_xls}\n\n{e}")

    # renombrar serie (si existe)
    if "Nro Serie" in datos.columns and "SERIE" not in datos.columns:
        datos.rename(columns={"Nro Serie": "SERIE"}, inplace=True)

    # columnas a eliminar (si no están, no falla)
    columnas_a_eliminar = [
        "Empresa", "Centro Costo", "CMeses", "Conts", "Bonif", "Renta",
        "Diferencia", "Clase", "Modelo", "Sector", "Direccion IP",
        "Toma Anterior", "Toma Actual", "Cdor Anterior", "Tipo", "Tipo.1"
    ]
    datos.drop(columns=columnas_a_eliminar, errors="ignore", inplace=True)

    # defensivo: chequear columnas usadas en el calculo
    faltantes = [c for c in ["Estado", "Cdor Actual"] if c not in datos.columns]
    if faltantes:
        raise ValueError(
            f"Faltan columnas requeridas en {os.path.basename(archivo_xls)}:\n{', '.join(faltantes)}"
        )

    # agregar columnas
    datos["FECHA"] = fecha_actual
    datos["TIPO"] = "14"
    datos["CLASE"] = "10"
    datos["CONTADOR"] = ""

    # regla de CONTADOR
    datos["CONTADOR"] = np.where(
        (datos["Estado"] == "Desaparecida") | (datos["Estado"] == "Backup Fijo"),
        datos["Cdor Actual"],
        np.where(
            datos["Cdor Actual"] == 1,
            datos["Cdor Actual"],
            np.where(
                (datos["Estado"] == "Activa en Cliente") & (datos["Cdor Actual"] != 1),
                datos["Cdor Actual"] + int(hojas_a_sumar),
                ""
            )
        )
    )

    # reordenar cerca de SERIE si existe
    if "SERIE" in datos.columns:
        indice_serie = datos.columns.get_loc("SERIE")
        columnas = datos.columns.tolist()
        for c in ["FECHA", "TIPO", "CLASE", "CONTADOR"]:
            columnas.remove(c)
        columnas[indice_serie + 1:indice_serie + 1] = ["FECHA", "TIPO", "CLASE", "CONTADOR"]
        datos = datos[columnas]

    return datos


def convertir_xls_a_csv_arcos_headless(
    archivos_xls: list[str],
    carpeta_salida: str,
    fecha_usuario: str,
    hojas_a_sumar: int,
) -> list[str]:
    """
    ✅ Función NUEVA para PySide (sin UI Tkinter).
    - No abre dialogs.
    - No muestra messagebox.
    - Reutiliza la misma lógica de transformación.
    Retorna: lista de rutas CSV generadas.
    Lanza excepciones con detalle en caso de error.
    """
    if not archivos_xls:
        raise ValueError("No se seleccionaron archivos XLS/XLSX.")

    if not carpeta_salida:
        # por seguridad, si no se pasa, usar carpeta del primero
        carpeta_salida = os.path.dirname(str(archivos_xls[0]))

    fecha_actual = _validar_fecha_ddmmyyyy(fecha_usuario)

    if hojas_a_sumar is None:
        hojas_a_sumar = 0

    os.makedirs(carpeta_salida, exist_ok=True)

    rutas_salida: list[str] = []

    for archivo_xls in archivos_xls:
        df = _procesar_un_excel_a_df(str(archivo_xls), fecha_actual, int(hojas_a_sumar))

        base = os.path.splitext(os.path.basename(str(archivo_xls)))[0]
        archivo_csv = os.path.join(carpeta_salida, f"{base}_AutoCSV.csv")

        try:
            df.to_csv(archivo_csv, index=False, sep=";")
        except Exception as e:
            raise RuntimeError(f"No se pudo guardar:\n{archivo_csv}\n\n{e}")

        rutas_salida.append(archivo_csv)

    return rutas_salida


def convertir_xls_a_csv_arcos(archivos_xls=None, carpeta_salida=None, parent=None):
    from tkinter import filedialog, simpledialog, messagebox
    """
    Convierte uno o varios XLS/XLSX al formato CSV requerido.
    Si no se proveen parametros, abre dialogos para pedirlos.
    Retorna: (ok:boolean, rutas_csv:list[str])
    """
    # --- seleccionar archivo(s) si no vinieron ---
    if not archivos_xls:
        archivos_xls = filedialog.askopenfilenames(
            title="Selecciona archivo(s) XLS/XLSX",
            filetypes=[("Archivos Excel", "*.xls *.xlsx")],
            parent=parent
        )
        if not archivos_xls:
            return (False, [])

    # normalizar a lista
    if isinstance(archivos_xls, (str, os.PathLike)):
        archivos_xls = [str(archivos_xls)]
    else:
        archivos_xls = [str(p) for p in archivos_xls]

    # --- carpeta de salida ---
    if not carpeta_salida:
        carpeta_salida = filedialog.askdirectory(
            title="Selecciona carpeta de destino",
            parent=parent
        )
        if not carpeta_salida:
            # por defecto, la del primer archivo
            carpeta_salida = os.path.dirname(archivos_xls[0])

    # --- fecha ---
    fecha_usuario = simpledialog.askstring(
        "Entrada de Fecha",
        "Ingrese la fecha (DD/MM/AAAA):",
        parent=parent
    )
    if not fecha_usuario:
        messagebox.showwarning("Advertencia", "No se ingresó ninguna fecha.", parent=parent)
        return (False, [])
    try:
        fecha_actual = datetime.strptime(fecha_usuario, "%d/%m/%Y").strftime("%d/%m/%Y")
    except ValueError:
        messagebox.showerror("Error", "La fecha ingresada no tiene el formato correcto (DD/MM/AAAA).", parent=parent)
        return (False, [])

    # --- hojas a sumar ---
    hojas_a_sumar = simpledialog.askinteger(
        "Copias a sumar",
        "Ingrese la cantidad de hojas que desea sumar a los equipos a estimar:",
        parent=parent
    )
    if hojas_a_sumar is None:
        messagebox.showwarning("Advertencia", "No se ingresó ninguna cantidad. Se tomará 0.", parent=parent)
        hojas_a_sumar = 0

    rutas_salida = []

    for archivo_xls in archivos_xls:
        # leer excel
        try:
            datos = pd.read_excel(archivo_xls)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer:\n{archivo_xls}\n\n{e}", parent=parent)
            return (False, [])

        # renombrar serie (si existe)
        if "Nro Serie" in datos.columns and "SERIE" not in datos.columns:
            datos.rename(columns={"Nro Serie": "SERIE"}, inplace=True)

        # columnas a eliminar (si no están, no falla)
        columnas_a_eliminar = [
            "Empresa","Centro Costo","CMeses","Conts","Bonif","Renta",
            "Diferencia","Clase","Modelo","Sector","Direccion IP",
            "Toma Anterior","Toma Actual","Cdor Anterior","Tipo","Tipo.1"
        ]
        datos.drop(columns=columnas_a_eliminar, errors="ignore", inplace=True)

        # defensivo: chequear columnas usadas en el calculo
        faltantes = [c for c in ["Estado", "Cdor Actual"] if c not in datos.columns]
        if faltantes:
            messagebox.showerror(
                "Error",
                f"Faltan columnas requeridas en {os.path.basename(archivo_xls)}:\n{', '.join(faltantes)}",
                parent=parent
            )
            return (False, [])

        # agregar columnas
        datos["FECHA"] = fecha_actual
        datos["TIPO"] = "14"
        datos["CLASE"] = "10"
        datos["CONTADOR"] = ""

        # regla de CONTADOR
        datos["CONTADOR"] = np.where(
            (datos["Estado"] == "Desaparecida") | (datos["Estado"] == "Backup Fijo"),
            datos["Cdor Actual"],
            np.where(
                datos["Cdor Actual"] == 1,
                datos["Cdor Actual"],
                np.where(
                    (datos["Estado"] == "Activa en Cliente") & (datos["Cdor Actual"] != 1),
                    datos["Cdor Actual"] + int(hojas_a_sumar),
                    ""
                )
            )
        )

        # reordenar cerca de SERIE si existe
        if "SERIE" in datos.columns:
            indice_serie = datos.columns.get_loc("SERIE")
            columnas = datos.columns.tolist()
            for c in ["FECHA","TIPO","CLASE","CONTADOR"]:
                columnas.remove(c)
            columnas[indice_serie+1:indice_serie+1] = ["FECHA","TIPO","CLASE","CONTADOR"]
            datos = datos[columnas]

        # guardar CSV
        base = os.path.splitext(os.path.basename(archivo_xls))[0]
        sugerido = os.path.join(carpeta_salida, f"{base}_AutoCSV.csv")
        archivo_csv = filedialog.asksaveasfilename(
            title="Guardar CSV",
            initialfile=os.path.basename(sugerido),
            defaultextension=".csv",
            filetypes=[("Archivos CSV", "*.csv")],
            parent=parent
        )
        if not archivo_csv:
            # si cancela guardar para este archivo, cancelar toda la operación
            return (False, [])

        try:
            datos.to_csv(archivo_csv, index=False, sep=";")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar:\n{archivo_csv}\n\n{e}", parent=parent)
            return (False, [])
        rutas_salida.append(archivo_csv)

    messagebox.showinfo("Éxito", f"Archivo(s) CSV guardado(s):\n" + "\n".join(rutas_salida), parent=parent)
    return (True, rutas_salida)
