# pyside_ui/ui/estimador_manual_dialog.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import math
from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets

from pyside_ui.ui.dialog_kit import BaseProDialog, apply_dialog_style, get_theme, warn


# =====================
# Lógica (Qt-agnóstica)
# =====================

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


class EstimadorManualDialog(BaseProDialog):
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None, *, theme: Optional[dict] = None):
        # ✅ parent=None para evitar que se “levante” la ventana de atrás (Windows owner behavior)
        super().__init__(
            parent,
            "Estimación manual de contadores",
            "Cálculo por 30/360 • Proyección y estimación",
            w=860,
        )

        self._theme = theme if theme else get_theme(parent)
        if self._theme:
            apply_dialog_style(self, self._theme)

        # ✅ Always-on-top + no modal (como Tkinter)
        self.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint, True)
        self.setWindowModality(QtCore.Qt.WindowModality.NonModal)
        self.setModal(False)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose, True)

        self._build_inputs_section()
        self.root_layout.addSpacing(6)
        self._build_results_section()
        self.root_layout.addSpacing(10)
        self._build_buttons()

        hoy = QtCore.QDate.currentDate().toString("dd/MM/yyyy")
        self.ed_fecha_fin.setText(hoy)
        self.ed_fecha_est.setText(hoy)

        for w in (self.ed_cont_ini, self.ed_cont_fin, self.ed_fecha_ini, self.ed_fecha_fin, self.ed_fecha_est):
            w.returnPressed.connect(self._on_calcular)

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        super().showEvent(event)
        QtCore.QTimer.singleShot(0, lambda: (self.raise_(), self.activateWindow()))

    def position_near(self, owner: QtWidgets.QWidget) -> None:
        """Posiciona la ventana en una zona cómoda dentro del área visible (sin irse arriba)."""
        try:
            if not owner:
                return

            self.adjustSize()

            # screen/área disponible (sin taskbar)
            screen = None
            try:
                screen = owner.screen()
            except Exception:
                screen = None
            if screen is None:
                try:
                    screen = QtGui.QGuiApplication.screenAt(owner.frameGeometry().center())
                except Exception:
                    screen = None
            if screen is None:
                screen = QtGui.QGuiApplication.primaryScreen()

            avail = screen.availableGeometry() if screen else QtCore.QRect(0, 0, 1920, 1080)

            # centrar respecto al owner, pero bajarlo un poco (más cómodo)
            geo = owner.frameGeometry()
            center = geo.center()

            my_geo = self.frameGeometry()
            my_geo.moveCenter(center)

            target = my_geo.topLeft()
            target.setY(target.y() + 120)  # 👈 bajá la ventana (ajustá si querés)

            # clamp para que siempre quede dentro del área visible
            w = self.width() or my_geo.width()
            h = self.height() or my_geo.height()

            margin = 16
            x = max(avail.left() + margin, min(target.x(), avail.right() - w - margin))
            y = max(avail.top() + margin, min(target.y(), avail.bottom() - h - margin))

            self.move(x, y)
        except Exception:
            pass

    def _group_box(self, title: str) -> QtWidgets.QGroupBox:
        gb = QtWidgets.QGroupBox(title)
        text_color = (self._theme or {}).get("text", "#EAEAEA")
        gb.setStyleSheet(f"""
            QGroupBox {{ color: {text_color}; }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 6px;
                color: {text_color};
            }}
        """)
        lay = QtWidgets.QGridLayout(gb)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setHorizontalSpacing(12)
        lay.setVerticalSpacing(10)
        return gb

    def _build_inputs_section(self) -> None:
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(12)

        gb_ini = self._group_box("Primer contador real")
        lay_ini = gb_ini.layout()  # type: ignore

        self.ed_fecha_ini = QtWidgets.QLineEdit()
        self.ed_fecha_ini.setPlaceholderText("DD/MM/AAAA")
        self.ed_cont_ini = QtWidgets.QLineEdit()
        self.ed_cont_ini.setPlaceholderText("Entero (ej: 12345)")
        self.ed_cont_ini.setValidator(QtGui.QIntValidator(0, 2_147_483_647, self))

        lay_ini.addWidget(QtWidgets.QLabel("Fecha inicial"), 0, 0)
        lay_ini.addWidget(self.ed_fecha_ini, 0, 1)
        lay_ini.addWidget(QtWidgets.QLabel("Contador inicial"), 1, 0)
        lay_ini.addWidget(self.ed_cont_ini, 1, 1)

        gb_fin = self._group_box("Segundo contador real")
        lay_fin = gb_fin.layout()  # type: ignore

        self.ed_fecha_fin = QtWidgets.QLineEdit()
        self.ed_fecha_fin.setPlaceholderText("DD/MM/AAAA")
        self.ed_cont_fin = QtWidgets.QLineEdit()
        self.ed_cont_fin.setPlaceholderText("Entero (ej: 67890)")
        self.ed_cont_fin.setValidator(QtGui.QIntValidator(0, 2_147_483_647, self))

        lay_fin.addWidget(QtWidgets.QLabel("Fecha final"), 0, 0)
        lay_fin.addWidget(self.ed_fecha_fin, 0, 1)
        lay_fin.addWidget(QtWidgets.QLabel("Contador final"), 1, 0)
        lay_fin.addWidget(self.ed_cont_fin, 1, 1)

        gb_est = self._group_box("Estimación")
        lay_est = gb_est.layout()  # type: ignore

        self.ed_fecha_est = QtWidgets.QLineEdit()
        self.ed_fecha_est.setPlaceholderText("DD/MM/AAAA")

        lay_est.addWidget(QtWidgets.QLabel("Fecha estimación"), 0, 0)
        lay_est.addWidget(self.ed_fecha_est, 0, 1)

        row.addWidget(gb_ini, 1)
        row.addWidget(gb_fin, 1)
        row.addWidget(gb_est, 1)

        self.root_layout.addLayout(row)

    def _build_results_section(self) -> None:
        gb = self._group_box("Resultados")
        lay = gb.layout()  # type: ignore

        self.ed_imp_dia = QtWidgets.QLineEdit()
        self.ed_imp_dia.setReadOnly(True)

        self.ed_imp_mes = QtWidgets.QLineEdit()
        self.ed_imp_mes.setReadOnly(True)

        self.ed_dias_est = QtWidgets.QLineEdit()
        self.ed_dias_est.setReadOnly(True)

        self.ed_cont_est = QtWidgets.QLineEdit()
        self.ed_cont_est.setReadOnly(True)

        self.ed_imp_est = QtWidgets.QLineEdit()
        self.ed_imp_est.setReadOnly(True)

        lay.addWidget(QtWidgets.QLabel("Impresiones diarias"), 0, 0)
        lay.addWidget(self.ed_imp_dia, 0, 1)
        lay.addWidget(QtWidgets.QLabel("Contador estimado"), 0, 2)
        lay.addWidget(self.ed_cont_est, 0, 3)

        lay.addWidget(QtWidgets.QLabel("Impresiones mensuales"), 1, 0)
        lay.addWidget(self.ed_imp_mes, 1, 1)
        lay.addWidget(QtWidgets.QLabel("Impresiones estimadas"), 1, 2)
        lay.addWidget(self.ed_imp_est, 1, 3)

        lay.addWidget(QtWidgets.QLabel("Días estimación"), 2, 0)
        lay.addWidget(self.ed_dias_est, 2, 1)

        self.root_layout.addWidget(gb)

    def _build_buttons(self) -> None:
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(10)

        btn_calc = QtWidgets.QPushButton("Calcular")
        btn_calc.setObjectName("Primary")
        btn_calc.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        btn_calc.clicked.connect(self._on_calcular)

        btn_close = QtWidgets.QPushButton("Cerrar")
        btn_close.clicked.connect(self.close)

        row.addStretch(1)
        row.addWidget(btn_calc)
        row.addWidget(btn_close)

        self.root_layout.addLayout(row)

    def _set(self, w: QtWidgets.QLineEdit, s: str) -> None:
        w.setText(s)

    def _on_calcular(self) -> None:
        try:
            ci = int(self.ed_cont_ini.text().strip())
            cf = int(self.ed_cont_fin.text().strip())
        except Exception:
            warn(self, "Datos inválidos", "Contadores inicial/final deben ser enteros.")
            return

        try:
            fi = parse_fecha_ddmmyyyy(self.ed_fecha_ini.text())
            ff = parse_fecha_ddmmyyyy(self.ed_fecha_fin.text())
            fe = parse_fecha_ddmmyyyy(self.ed_fecha_est.text())
        except Exception:
            warn(self, "Datos inválidos", "Fechas deben ser dd/MM/yyyy.")
            return

        ndias = dias_360(fi, ff)
        if ndias <= 0:
            warn(self, "Rango inválido", "El rango de días entre inicial y final debe ser mayor a 0.")
            return

        ndias_est = dias_360(ff, fe)
        impresiones_diarias = round((cf - ci) / ndias, 2)

        self._set(self.ed_imp_dia, f"{impresiones_diarias}")
        self._set(self.ed_dias_est, f"{ndias_est}")

        im = calcular_impresiones_mensuales(impresiones_diarias)
        self._set(self.ed_imp_mes, f"{im}")

        cont_est, imp_est = calcular_resultado_estimacion(cf, impresiones_diarias, ndias_est)
        self._set(self.ed_cont_est, f"{cont_est}")
        self._set(self.ed_imp_est, f"{imp_est}")
