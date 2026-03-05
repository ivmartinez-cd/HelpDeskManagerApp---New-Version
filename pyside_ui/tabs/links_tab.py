# pyside_ui/tabs/links_tab.py
from __future__ import annotations

import webbrowser

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHeaderView,
    QHBoxLayout,
    QLineEdit,
    QComboBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pyside_ui.widgets import Card


def _small_btn_qss(theme: dict) -> str:
    bg = theme.get("btn_bg", "#2B2B2B")
    hover = theme.get("btn_hover", "#333333")
    text = theme.get("text", "#FFFFFF")
    border = theme.get("card_border", "#3A3A3A")
    return f"""
        QPushButton {{
            background: {bg};
            color: {text};
            border: 1px solid {border};
            border-radius: 14px;
            padding: 8px 14px;
            min-height: 36px;
        }}
        QPushButton:hover {{
            background: {hover};
        }}
        QPushButton:pressed {{
            background: {hover};
        }}
        QPushButton:disabled {{
            opacity: 0.55;
        }}
    """


def _inputs_qss(theme: dict) -> str:
    bg = theme.get("btn_bg", "#2B2B2B")
    hover = theme.get("btn_hover", "#333333")
    text = theme.get("text", "#FFFFFF")
    border = theme.get("card_border", "#3A3A3A")
    accent = theme.get("orange", "#FF9A2E")

    return f"""
        QLineEdit {{
            background: {bg};
            color: {text};
            border: 1px solid {border};
            border-radius: 14px;
            padding: 8px 12px;
            min-height: 36px;
            selection-background-color: {accent};
        }}
        QLineEdit:focus {{
            border: 1px solid {accent};
        }}

        QComboBox {{
            background: {bg};
            color: {text};
            border: 1px solid {border};
            border-radius: 14px;
            padding: 8px 12px;
            min-height: 36px;
        }}
        QComboBox:hover {{
            background: {hover};
        }}
        QComboBox::drop-down {{
            border: 0;
            width: 28px;
        }}
        QComboBox QAbstractItemView {{
            background: {bg};
            color: {text};
            border: 1px solid {border};
            selection-background-color: {accent};
        }}
    """


def _table_qss(theme: dict) -> str:
    bg = theme.get("card_bg", "#2A2A2A")
    text = theme.get("text", "#FFFFFF")
    border = theme.get("card_border", "#3A3A3A")
    hover = theme.get("btn_hover", "#333333")
    accent = theme.get("orange", "#FF9A2E")
    muted = theme.get("muted", "#B0B0B0")

    return f"""
        QTableWidget {{
            background: {bg};
            color: {text};
            border: 1px solid {border};
            border-radius: 14px;
            gridline-color: {border};
            padding: 4px;

            /* Evita el contorno de foco "viejo" */
            outline: 0;
        }}

        /* Selección prolija y consistente por celda (y como estás en SelectRows, se ve fila completa) */
        QTableWidget::item:selected {{
            background: {accent};
            color: #111111;
        }}
        QTableWidget::item:selected:active {{
            background: {accent};
            color: #111111;
        }}

        /* Quita el focus-rect que genera ese "pill" raro */
        QTableWidget::item:focus {{
            outline: none;
        }}
              
        QHeaderView::section {{
            background: transparent;
            color: {muted};
            border: 0;
            border-bottom: 1px solid {border};
            padding: 8px 10px;
            font-weight: 600;
        }}

        QTableWidget::item {{
            padding: 8px 10px;
            border: 0;
        }}

        QTableWidget::item:hover {{
            background: {hover};
        }}

        QTableCornerButton::section {{
            background: transparent;
            border: 0;
        }}
    """


class LinksTab(QWidget):
    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self._theme = theme or {}

        lay = QVBoxLayout(self)
        # Margen inferior para que la sombra del Card no se recorte (blur 24, offset 4)
        lay.setContentsMargins(0, 0, 0, 36)
        lay.setSpacing(0)

        self.card = Card("Links")
        lay.addWidget(self.card, 1)  # stretch 1: la card ocupa todo el alto disponible

        # --- Fila búsqueda + filtro (sin etiqueta "Filtrar") ---
        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)

        self.ed_filter = QLineEdit()
        self.ed_filter.setPlaceholderText("Buscar por nombre o URL…")
        filter_row.addWidget(self.ed_filter, 1)

        self.cmb_group = QComboBox()
        self.cmb_group.addItems(["Todos", "Manuales", "Documentación", "Otros"])
        self.cmb_group.setFixedWidth(130)
        filter_row.addWidget(self.cmb_group, 0)

        self.card.grid.addLayout(filter_row, 0, 0, 1, 2)

        # --- Tabla ---
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Nombre", "URL"])
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)

        # Scroll area para que la tabla no desborde la card: contenido dentro del borde
        self.table_scroll = QScrollArea()
        self.table_scroll.setWidget(self.table)
        self.table_scroll.setWidgetResizable(True)
        self.table_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.table_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table_scroll.setMinimumHeight(200)

        self.card.grid.addWidget(self.table_scroll, 1, 0, 1, 2)
        self.card.grid.setRowStretch(1, 1)

        # --- Botonera: alineada a la derecha, 12px sobre la fila, 8px entre botones ---
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.setContentsMargins(0, 12, 0, 0)
        btn_row.addStretch(1)
        self.btn_open = QPushButton("Abrir")
        self.btn_copy = QPushButton("Copiar URL")
        btn_row.addWidget(self.btn_open, 0)
        btn_row.addWidget(self.btn_copy, 0)

        self.btn_open.clicked.connect(self._open_link)
        self.btn_copy.clicked.connect(self._copy_link)

        self.card.grid.addLayout(btn_row, 2, 0, 1, 2)

        # Estilos
        self.set_theme(self._theme)

        # Demo visual (solo UI)
        self._seed_demo()

    def _get_status_bus(self):
        """Obtiene el StatusBus de la ventana si está disponible (p. ej. MainWindow)."""
        win = self.window()
        return getattr(win, "status_bus", None)

    def _get_selected_url(self) -> tuple[str | None, str | None]:
        """Devuelve (nombre, url) de la fila seleccionada, o (None, None) si no hay selección."""
        row = self.table.currentRow()
        if row < 0:
            return None, None
        name_item = self.table.item(row, 0)
        url_item = self.table.item(row, 1)
        if url_item is None:
            return None, None
        name = name_item.text().strip() if name_item else ""
        url = url_item.text().strip() if url_item else ""
        return name or None, url or None

    def _open_link(self) -> None:
        name, url = self._get_selected_url()
        if not url:
            status_bus = self._get_status_bus()
            if status_bus:
                status_bus.notify("warning", "Links", "Seleccione un link primero.", 4000)
            return
        try:
            webbrowser.open(url)
            status_bus = self._get_status_bus()
            if status_bus:
                status_bus.set_status(f"Abrir: {name or url}")
                status_bus.notify("success", "Links", "URL abierta en el navegador.", 3000)
        except Exception as e:
            status_bus = self._get_status_bus()
            if status_bus:
                status_bus.set_status("")
                status_bus.notify("error", "Links", f"No se pudo abrir la URL:\n{e}", 5000)

    def _copy_link(self) -> None:
        name, url = self._get_selected_url()
        if not url:
            status_bus = self._get_status_bus()
            if status_bus:
                status_bus.notify("warning", "Links", "Seleccione un link primero.", 4000)
            return
        try:
            clipboard = QApplication.clipboard()
            clipboard.setText(url)
            status_bus = self._get_status_bus()
            if status_bus:
                status_bus.set_status("URL copiada al portapapeles")
                status_bus.notify("success", "Links", "URL copiada.", 3000)
        except Exception as e:
            status_bus = self._get_status_bus()
            if status_bus:
                status_bus.set_status("")
                status_bus.notify("error", "Links", f"No se pudo copiar:\n{e}", 5000)

    def _seed_demo(self):
        demo = [
            ("Manual App Mobile", "https://cdst-ar.github.io/ST/appmobile"),
            ("Instructivos contadores/ST", "https://sites.google.com/…/calendarict"),
            ("Manuales Impresoras", "https://drive.google.com/drive/folders/…"),
            ("Envios Credifin", "https://docs.google.com/spreadsheets/…"),
        ]
        self.table.setRowCount(len(demo))
        for r, (name, url) in enumerate(demo):
            self.table.setItem(r, 0, QTableWidgetItem(name))
            self.table.setItem(r, 1, QTableWidgetItem(url))

    def set_theme(self, theme: dict) -> None:
        self._theme = theme or {}
        self.card.set_theme(self._theme)

        qss_inputs = _inputs_qss(self._theme)
        self.ed_filter.setStyleSheet(qss_inputs)
        self.cmb_group.setStyleSheet(qss_inputs)

        self.table.setStyleSheet(_table_qss(self._theme))

        # Scroll area transparente para integrarse con la card
        bg = self._theme.get("card_bg", "#2A2A2A")
        self.table_scroll.setStyleSheet(f"""
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:vertical {{ background: {bg}; border-radius: 6px; width: 10px; margin: 0; }}
            QScrollBar::handle:vertical {{ background: #555; border-radius: 5px; min-height: 24px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        btn_qss = _small_btn_qss(self._theme)
        self.btn_open.setStyleSheet(btn_qss)
        self.btn_copy.setStyleSheet(btn_qss)
