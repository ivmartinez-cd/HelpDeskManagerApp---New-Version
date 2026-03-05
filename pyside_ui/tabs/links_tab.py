# pyside_ui/tabs/links_tab.py
from __future__ import annotations

import webbrowser

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QHeaderView,
    QHBoxLayout,
    QLineEdit,
    QComboBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QLabel,
)

from pyside_ui.widgets import BaseTabLayout, ModernCheckBox


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
            outline: 0;
        }}
        QTableWidget::item:selected {{
            background: {accent};
            color: #111111;
        }}
        QTableWidget::item:selected:active {{
            background: {accent};
            color: #111111;
        }}
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
    """
    Tab Links: solo define UI. Usa BaseTabLayout para estructura consistente.
    Sin ventanas ni diálogos; solo widgets y layouts.
    """

    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self._theme = theme or {}

        # Contenedor con margen inferior para sombra (igual que antes)
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 36)
        root_layout.setSpacing(0)

        self._base = BaseTabLayout(self)
        root_layout.addWidget(self._base)

        # ─── SECTION 1 — Header: título + toolbar (búsqueda, filtro) ─────────
        self._title_lbl = QLabel("Links")
        self._title_lbl.setObjectName("LinksTabTitle")
        self._title_lbl.setFont(QFont("Segoe UI", 17, QFont.DemiBold))
        self._base.header_layout.addWidget(self._title_lbl)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        self.ed_filter = QLineEdit()
        self.ed_filter.setPlaceholderText("Buscar por nombre o URL…")
        toolbar.addWidget(self.ed_filter, 1)
        self.cmb_group = QComboBox()
        self.cmb_group.addItems(["Todos", "Manuales", "Documentación", "Otros"])
        self.cmb_group.setFixedWidth(130)
        toolbar.addWidget(self.cmb_group, 0)
        self._base.header_layout.addLayout(toolbar)

        # ─── SECTION 2 — Content: tabla (expande) ────────────────────────────
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
        self._base.content_layout.addWidget(self.table, 1)

        # ─── SECTION 3 — Action bar: botones a la derecha (stretch ya en base) ─
        self.btn_open = QPushButton("Abrir")
        self.btn_copy = QPushButton("Copiar URL")
        self.btn_open.clicked.connect(self._open_link)
        self.btn_copy.clicked.connect(self._copy_link)
        self._base.action_bar_layout.addWidget(self.btn_open, 0)
        self._base.action_bar_layout.addWidget(self.btn_copy, 0)

        # ─── SECTION 4 — Footer: izquierda texto, derecha checkbox ───────────
        self.footer_lbl = QLabel("Hecho por: Iván Martínez")
        self._base.footer_layout.addWidget(self.footer_lbl, 0, Qt.AlignLeft)
        self._base.footer_layout.addStretch(1)
        self.chk_startup = ModernCheckBox("Iniciar con Windows")
        self._base.footer_layout.addWidget(self.chk_startup, 0, Qt.AlignRight)

        self.set_theme(self._theme)
        self._seed_demo()

    def _get_status_bus(self):
        win = self.window()
        return getattr(win, "status_bus", None)

    def _get_selected_url(self) -> tuple[str | None, str | None]:
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

    def _seed_demo(self) -> None:
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
        t = self._theme

        self._title_lbl.setStyleSheet(
            f"color: {t.get('text', '#EAEAEA')}; background: transparent; border: none;"
        )

        qss_inputs = _inputs_qss(t)
        self.ed_filter.setStyleSheet(qss_inputs)
        self.cmb_group.setStyleSheet(qss_inputs)

        self.table.setStyleSheet(_table_qss(t))

        btn_qss = _small_btn_qss(t)
        self.btn_open.setStyleSheet(btn_qss)
        self.btn_copy.setStyleSheet(btn_qss)

        muted = t.get("muted", "#B8B8B8")
        self.footer_lbl.setStyleSheet(f"color: {muted}; background: transparent; border: none;")
        self.chk_startup.set_theme(t)
