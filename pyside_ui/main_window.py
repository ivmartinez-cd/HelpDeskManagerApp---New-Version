from __future__ import annotations

from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QStackedWidget, QToolButton, QSizeGrip
)
from PySide6 import QtWidgets

from pyside_ui.services.status_bus import StatusBus

from .theme import THEME
from .widgets import ThemeIconButton, SegmentedTabs, ModernCheckBox

from pyside_ui.tabs.contadores_tab import ContadoresTab
from pyside_ui.tabs.stc_tab import STCTab
from pyside_ui.tabs.links_tab import LinksTab

from .ui.menubar import build_menubar, apply_menubar_theme

from pyside_ui.widgets.toast import ToastManager


class _ProTitleBar(QWidget):
    """
    Titlebar custom tipo dialog_kit:
    - draggable (mueve la ventana)
    - botones minimizar / cerrar
    """
    def __init__(self, parent: "MainWindow"):
        super().__init__(parent)
        self._mw = parent
        self._drag_pos: QPoint | None = None
        self.setObjectName("ProMainTitleBar")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 8, 8, 8)
        lay.setSpacing(10)

        # icono + titulo
        self._icon = QLabel()
        self._icon.setFixedSize(16, 16)
        self._icon.setScaledContents(True)

        self._title = QLabel(parent.windowTitle())
        self._title.setObjectName("ProMainTitle")
        self._title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        if not parent.windowTitle():
            self._title.setVisible(False)

        lay.addWidget(self._icon, 0, Qt.AlignVCenter)
        lay.addWidget(self._title, 0, Qt.AlignVCenter)
        lay.addStretch(1)

        self._btn_min = QToolButton()
        self._btn_min.setObjectName("ProWinBtn")
        self._btn_min.setText("–")
        self._btn_min.clicked.connect(parent.showMinimized)

        self._btn_close = QToolButton()
        self._btn_close.setObjectName("ProWinBtnClose")
        self._btn_close.setText("✕")
        self._btn_close.clicked.connect(parent.close)

        lay.addWidget(self._btn_min, 0, Qt.AlignVCenter)
        lay.addWidget(self._btn_close, 0, Qt.AlignVCenter)

    def set_title(self, text: str):
        self._title.setText(text)

    def set_icon(self, icon: QIcon | None):
        if not icon or icon.isNull():
            self._icon.setVisible(False)
            return
        pm = icon.pixmap(16, 16)
        self._icon.setPixmap(pm)
        self._icon.setVisible(True)

    # Drag window
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self._mw.frameGeometry().topLeft()
            e.accept()
            return
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._drag_pos is not None and (e.buttons() & Qt.LeftButton):
            self._mw.move(e.globalPosition().toPoint() - self._drag_pos)
            e.accept()
            return
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        self._drag_pos = None
        super().mouseReleaseEvent(e)

    def mouseDoubleClickEvent(self, e):
        # opcional: maximizar/restaurar en doble click
        # lo dejo desactivado para no cambiar UX (podés activarlo si querés)
        super().mouseDoubleClickEvent(e)


class MainWindow(QMainWindow):
    def __init__(self, app_icon: QIcon | None = None):
        super().__init__()

        # ✅ Frameless: elimina la barra nativa
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)

        self._app_icon = app_icon if (app_icon and not app_icon.isNull()) else None
        if self._app_icon:
            self.setWindowIcon(self._app_icon)

        self.theme_name = "dark"
        self.theme = THEME[self.theme_name]

        self.setWindowTitle("")
        self.setMinimumSize(960, 640)
        self.resize(1100, 720)
        self.setMaximumSize(1400, 900)

        # Bus global
        self.status_bus = StatusBus()

        self.toast_mgr = ToastManager(self)
        self.status_bus.notify_requested.connect(self.toast_mgr.show)

        # Menú (queda dentro del client area)
        build_menubar(self, self._noop)

        root = QWidget()
        self.setCentralWidget(root)
        self.root = root

        self.v = QVBoxLayout(root)
        self.v.setContentsMargins(0, 0, 0, 0)
        self.v.setSpacing(0)

        # ✅ Titlebar custom
        self.titlebar = _ProTitleBar(self)
        self.titlebar.set_icon(self._app_icon)
        self.v.addWidget(self.titlebar, 0)

        # Contenedor interno (margen superior reducido para anclar el header; horizontales sin cambio)
        self.inner = QWidget()
        self.inner_lay = QVBoxLayout(self.inner)
        self.inner_lay.setContentsMargins(28, 12, 28, 22)
        self.inner_lay.setSpacing(14)

        # Header: [ Icono + Título/Subtítulo ]  stretch  [ Theme Toggle ]
        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        # Bloque izquierdo: icono opcional + título y subtítulo
        left_outer = QHBoxLayout()
        left_outer.setSpacing(10)

        self.header_icon = QLabel()
        self.header_icon.setFixedSize(24, 24)
        self.header_icon.setScaledContents(True)
        if self._app_icon and not self._app_icon.isNull():
            self.header_icon.setPixmap(self._app_icon.pixmap(24, 24))
            self.header_icon.setVisible(True)
        else:
            self.header_icon.setVisible(False)
        left_outer.addWidget(self.header_icon, 0, Qt.AlignVCenter)

        left = QVBoxLayout()
        left.setSpacing(5)

        self.h1 = QLabel("HelpDeskManagerApp")
        self.h1.setFont(QFont("Segoe UI", 20, QFont.Bold))
        left.addWidget(self.h1)

        self.h2 = QLabel("Gestión de mesa de ayuda • Operaciones")
        self.h2.setFont(QFont("Segoe UI", 11))
        left.addWidget(self.h2)

        left_outer.addLayout(left, 1)
        header_row.addLayout(left_outer, 0)

        header_row.addStretch(1)

        self.theme_btn = ThemeIconButton()
        self.theme_btn.toggled.connect(self.on_toggle_theme)
        header_row.addWidget(self.theme_btn, 0, Qt.AlignRight | Qt.AlignVCenter)

        self.inner_lay.addLayout(header_row)

        # Tabs (navegación), alineados a la izquierda con el contenido de la card
        tabs_row = QHBoxLayout()
        self.tabs = SegmentedTabs(["Contadores", "STC", "Links"])
        self.tabs.changed.connect(self.on_tab_changed)
        tabs_row.addWidget(self.tabs, 0, Qt.AlignLeft)
        tabs_row.addStretch(1)
        self.inner_lay.addLayout(tabs_row)

        # Stack (contenido / card)
        self.stack = QStackedWidget()
        self.inner_lay.addWidget(self.stack, 1)

        self._build_tab_contadores()
        self._build_tab_stc()
        self._build_tab_links()

        # Footer
        footer = QHBoxLayout()
        footer.setContentsMargins(0, 0, 0, 0)

        self.footer_lbl = QLabel("Hecho por: Iván Martínez")
        self.footer_lbl.setFont(QFont("Segoe UI", 11))
        footer.addWidget(self.footer_lbl, 1, Qt.AlignLeft)

        # 🔕 Estado global: oculto por defecto (y NO mostramos "Listo")
        self.global_status_lbl = QLabel("")
        self.global_status_lbl.setFont(QFont("Segoe UI", 10))
        self.global_status_lbl.setVisible(False)
        footer.addWidget(self.global_status_lbl, 0, Qt.AlignRight)

        self.chk_startup = ModernCheckBox("Iniciar con Windows")
        footer.addWidget(self.chk_startup, 0, Qt.AlignRight)

        # ✅ QSizeGrip para resize en frameless
        self._grip = QSizeGrip(self)
        self._grip.setFixedSize(18, 18)

        footer_wrap = QWidget()
        footer_wrap.setLayout(footer)

        footer_row = QHBoxLayout()
        footer_row.setContentsMargins(0, 0, 0, 0)
        footer_row.addWidget(footer_wrap, 1)
        footer_row.addWidget(self._grip, 0, Qt.AlignRight | Qt.AlignBottom)

        self.inner_lay.addLayout(footer_row)

        # Añadir el contenedor interno al layout principal (titlebar + inner)
        self.v.addWidget(self.inner, 1)

        # Conectar bus → label
        self.status_bus.status_changed.connect(self._set_global_status)

        self.apply_theme()

    def _set_global_status(self, text: str) -> None:
        text = (text or "").strip()
        if not text or text.lower() == "listo":
            self.global_status_lbl.setVisible(False)
            self.global_status_lbl.setText("")
            return
        self.global_status_lbl.setText(text)
        self.global_status_lbl.setVisible(True)

    def _noop(self) -> None:
        return

    # Tabs
    def _build_tab_contadores(self):
        self.contadores_tab = ContadoresTab(self.theme, status_bus=self.status_bus)
        self.stack.addWidget(self.contadores_tab)

        # ✅ Wiring determinístico: el menú FTP resuelve win.ftp_controller
        # No instanciamos controllers acá; solo exponemos el que ya creó el Tab.
        self.ftp_controller = getattr(self.contadores_tab, "_ftp_controller", None)

    def _build_tab_stc(self):
        self.stc_tab = STCTab(self.theme, status_bus=self.status_bus)
        self.stack.addWidget(self.stc_tab)

    def _build_tab_links(self):
        self.links_tab = LinksTab(self.theme)
        self.stack.addWidget(self.links_tab)

    # Theme
    def apply_theme(self):
        self.theme = THEME[self.theme_name]
        t = self.theme

        # fondo general
        self.root.setStyleSheet(f"background: {t['app_bg']};")
        self.setStyleSheet(f"QMainWindow {{ background: {t['app_bg']}; }}")

        # titlebar custom + botones
        self.titlebar.setStyleSheet(f"""
            QWidget#ProMainTitleBar {{
                background: {t.get('card_bg', t['app_bg'])};
                border-bottom: 1px solid {t.get('card_border', t.get('border', '#3A3A3A'))};
            }}
            QLabel#ProMainTitle {{
                color: {t.get('text', '#EAEAEA')};
            }}
            QToolButton#ProWinBtn {{
                background: transparent;
                border: 1px solid {t.get('card_border', t.get('border', '#3A3A3A'))};
                border-radius: 10px;
                padding: 4px 10px;
                color: {t.get('text', '#EAEAEA')};
            }}
            QToolButton#ProWinBtn:hover {{
                background: {t.get('btn_hover', t.get('panel_bg2', '#333333'))};
                border: 1px solid {t.get('orange', '#ff9a2e')};
            }}
            QToolButton#ProWinBtnClose {{
                background: transparent;
                border: 1px solid {t.get('card_border', t.get('border', '#3A3A3A'))};
                border-radius: 10px;
                padding: 4px 10px;
                color: {t.get('text', '#EAEAEA')};
            }}
            QToolButton#ProWinBtnClose:hover {{
                background: {t.get('btn_hover', t.get('panel_bg2', '#333333'))};
                border: 1px solid {t.get('orange', '#ff9a2e')};
            }}
        """)

        self.h1.setStyleSheet(f"color: {t['orange']};")
        self.h2.setStyleSheet(f"color: {t.get('muted', t.get('blue', '#888888'))};")
        self.footer_lbl.setStyleSheet(f"color: {t['muted']};")
        self.global_status_lbl.setStyleSheet(f"color: {t['muted']};")

        self.tabs.set_theme(t)

        if hasattr(self, "contadores_tab"):
            self.contadores_tab.set_theme(t)
        if hasattr(self, "stc_tab"):
            self.stc_tab.set_theme(t)
        if hasattr(self, "links_tab"):
            self.links_tab.set_theme(t)

        self.chk_startup.set_theme(t)

        self.theme_btn.set_theme(t)
        self.theme_btn.set_light(self.theme_name == "light", emit=False)

        apply_menubar_theme(self, t)
        mb = self.menuBar()
        mb.setStyleSheet(
            "QMenuBar { background: %(bg)s; color: %(fg)s; }"
            "QMenuBar::item { background: transparent; padding: 4px 10px; }"
            "QMenuBar::item:selected { background: %(hover)s; }"
            "QMenu { background: %(bg2)s; color: %(fg)s; border: 1px solid %(border)s; }"
            "QMenu::item:selected { background: %(hover)s; }"
            % {
                "bg": t["app_bg"],
                "bg2": t.get("panel_bg", t["app_bg"]),
                "fg": t.get("text", "#EAEAEA"),
                "hover": t.get("panel_bg2", t.get("panel_bg", t["app_bg"])),
                "border": t.get("border", "#3A3A3A"),
            }
        )

    # Events
    def on_toggle_theme(self, is_light: bool):
        self.theme_name = "light" if is_light else "dark"
        self.apply_theme()

    def on_tab_changed(self, idx: int):
        self.stack.setCurrentIndex(idx)
