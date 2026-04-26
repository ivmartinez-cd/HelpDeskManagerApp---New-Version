# pyside_ui/tabs/links_tab.py
from __future__ import annotations
import webbrowser
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QHeaderView, QHBoxLayout, QLineEdit, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
)
from .contadores_tab import SectionHeader
from ..widgets.effects import apply_shadow
from ..theme.theme import TAB_MARGINS

class LinksTab(QWidget):
    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self._theme = theme or {}

        # Layout Principal
        main = QVBoxLayout(self)
        main.setContentsMargins(*TAB_MARGINS)
        main.setSpacing(18)

        # 1. Cabecera
        main.addWidget(SectionHeader("Directorio de Enlaces y Documentación"))

        # 2. Fila de Búsqueda (Con sombra)
        self.search_container = QWidget()
        search_lay = QHBoxLayout(self.search_container)
        search_lay.setContentsMargins(2, 2, 2, 2)
        search_lay.setSpacing(12)

        self.ed_filter = QLineEdit()
        self.ed_filter.setPlaceholderText("Filtrar recursos por nombre o dirección URL…")
        search_lay.addWidget(self.ed_filter, 1)
        
        self.cmb_group = QComboBox()
        self.cmb_group.addItems(["Todos los Grupos", "Manuales", "Documentación", "Otros"])
        self.cmb_group.setFixedWidth(180)
        search_lay.addWidget(self.cmb_group, 0)
        
        main.addWidget(self.search_container)

        # 3. Tabla de Recursos
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["NOMBRE DEL RECURSO", "DIRECCIÓN URL"])
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        
        main.addWidget(self.table, 1)

        # 4. Botonera Inferior
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        btn_row.addStretch(1)
        
        self.btn_copy = QPushButton("Copiar URL")
        self.btn_open = QPushButton("Abrir Recurso")
        self.btn_open.setFixedWidth(150)
        
        btn_row.addWidget(self.btn_copy)
        btn_row.addWidget(self.btn_open)
        main.addLayout(btn_row)

        # Conexiones
        self.btn_open.clicked.connect(self._open_link)
        self.btn_copy.clicked.connect(self._copy_link)
        self.ed_filter.textChanged.connect(self._on_filter)

        self.set_theme(self._theme)
        self._seed_demo()

    def set_theme(self, theme: dict) -> None:
        self._theme = theme or {}
        t = self._theme
        
        # Sombra sutil al buscador
        apply_shadow(self.search_container, blur=15, y=2, rgba=(0,0,0,80))

        # Estilo de inputs
        input_css = f"""
            QLineEdit, QComboBox {{
                background: {t['app_bg']};
                color: {t['text']};
                border: 1px solid {t['card_border']};
                border-radius: 12px;
                padding: 10px 14px;
                font-size: 13px;
            }}
            QLineEdit:focus {{ border: 1px solid {t['orange']}; }}
        """
        self.ed_filter.setStyleSheet(input_css)
        self.cmb_group.setStyleSheet(input_css)

        # Estilo de Tabla Premium
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {t['card_bg']};
                color: {t['text']};
                border: 1px solid {t['card_border']};
                border-radius: 16px;
                gridline-color: transparent;
                outline: 0;
            }}
            QHeaderView::section {{
                background: transparent;
                color: {t['muted']};
                border: 0;
                border-bottom: 1px solid {t['card_border']};
                padding: 12px;
                font-weight: 800;
                font-size: 10px;
                text-transform: uppercase;
            }}
            QTableWidget::item {{
                padding: 14px;
                border-bottom: 1px solid {t['app_bg']};
            }}
            QTableWidget::item:selected {{
                background: {t['surface_raised']};
                color: {t['orange']};
                font-weight: bold;
            }}
        """)

        # Botones
        btn_css = f"""
            QPushButton {{
                background: {t['surface_raised']};
                color: {t['text']};
                border: 1px solid {t['card_border']};
                border-radius: 14px;
                padding: 10px 24px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: {t['orange']};
                color: #000000;
            }}
        """
        self.btn_open.setStyleSheet(btn_css)
        self.btn_copy.setStyleSheet(btn_css)

    def _on_filter(self):
        txt = self.ed_filter.text().lower()
        for i in range(self.table.rowCount()):
            name = self.table.item(i, 0).text().lower()
            url = self.table.item(i, 1).text().lower()
            self.table.setRowHidden(i, txt not in name and txt not in url)

    def _get_selected_url(self) -> tuple[str | None, str | None]:
        row = self.table.currentRow()
        if row < 0: return None, None
        return self.table.item(row, 0).text(), self.table.item(row, 1).text()

    def _open_link(self) -> None:
        name, url = self._get_selected_url()
        if not url: return
        webbrowser.open(url)
        sb = self._get_status_bus()
        if sb: sb.notify("success", "Navegador", f"Abriendo: {name}", 2000)

    def _copy_link(self) -> None:
        _, url = self._get_selected_url()
        if not url: return
        QApplication.clipboard().setText(url)
        sb = self._get_status_bus()
        if sb: sb.notify("success", "Portapapeles", "URL copiada correctamente", 2000)

    def _get_status_bus(self):
        return getattr(self.window(), "status_bus", None)

    def _seed_demo(self) -> None:
        demo = [
            ("Manual App Mobile", "https://cdst-ar.github.io/ST/appmobile"),
            ("Instructivos Contadores/ST", "https://sites.google.com/view/calendarict"),
            ("Manuales Impresoras", "https://drive.google.com/drive/folders/backup"),
            ("Envíos Logística", "https://docs.google.com/spreadsheets/logs"),
        ]
        self.table.setRowCount(len(demo))
        for r, (name, url) in enumerate(demo):
            self.table.setItem(r, 0, QTableWidgetItem(name))
            self.table.setItem(r, 1, QTableWidgetItem(url))
