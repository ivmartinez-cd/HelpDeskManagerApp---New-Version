# pyside_ui/core/estimador_manual.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
import math

def dias_360(fecha_inicial: datetime, fecha_final: datetime) -> int:
    di, mi, yi = fecha_inicial.day, fecha_inicial.month, fecha_inicial.year
    df, mf, yf = fecha_final.day, fecha_final.month, fecha_final.year
    if di == 31:
        di = 30
    if df == 31 and di >= 30:
        df = 30
    return (yf - yi) * 360 + (mf - mi) * 30 + (df - di)


def parse_fecha_ddmmyyyy(s: str) -> datetime:
    return datetime.strptime(s.strip(), "%d/%m/%Y")


def calcular_impresiones_mensuales(impresiones_diarias: float) -> float:
    return round(impresiones_diarias * 30, 2)


def calcular_resultado_estimacion(contador_final: int, impresiones_diarias: float, dias_estimacion: int):
    if contador_final < 0:
        raise ValueError(f"contador_final no puede ser negativo: {contador_final}")
    if impresiones_diarias < 0:
        raise ValueError(f"impresiones_diarias no puede ser negativa: {impresiones_diarias}")
    if dias_estimacion < 0:
        raise ValueError(f"dias_estimacion no puede ser negativo: {dias_estimacion}")
    if impresiones_diarias == 0 or dias_estimacion == 0:
        return contador_final, 0
    contador_estimado = math.ceil(contador_final + (impresiones_diarias * dias_estimacion))
    impresiones_estimadas = math.ceil(impresiones_diarias * dias_estimacion)
    return contador_estimado, impresiones_estimadas


@dataclass(frozen=True)
class EstimadorManualResult:
    contador_estimado: int
    impresiones_estimadas: int
    impresiones_diarias: float
    impresiones_mensuales: float
    dias_estimacion: int
