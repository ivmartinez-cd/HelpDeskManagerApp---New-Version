from __future__ import annotations
import sys

from PySide6.QtCore import Qt, QPoint, QTimer
from pathlib import Path
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QStackedWidget, QToolButton, QSizeGrip,
    QMenu,
)
from PySide6 import QtWidgets, QtGui

from pyside_ui.services.status_bus import StatusBus
from pyside_ui.ui.title_bar import ProTitleBar

from .theme import THEME
from .widgets import ThemeIconButton, SegmentedTabs, ModernCheckBox

from pyside_ui.tabs.contadores_tab import ContadoresTab
from pyside_ui.tabs.stc_tab import STCTab
from pyside_ui.tabs.links_tab import LinksTab

from .ui.menubar import build_menubar, apply_menubar_theme

from pyside_ui.widgets.toast import ToastManager


class MainWindow(QMainWindow):
    def __init__(self, app_icon: QIcon | None = None):
        super().__init__()

        # Cargar versión
        self.version = "v0.0.0"
        try:
            import json
            import os
            # Intentar encontrar version.json en la raíz o en AppData
            v_paths = [
                Path("version.json"),
                Path(sys.executable).parent / "version.json",
                Path(os.environ.get('LOCALAPPDATA', os.environ.get('APPDATA', '.'))) / "HelpDeskManagerApp" / "version.json"
            ]
            for vp in v_paths:
                if vp.exists():
                    with open(vp, "r") as f:
                        v_data = json.load(f)
                        self.version = f"v{v_data.get('version', '0.0.0')}"
                    break
        except:
            pass

        # ✅ Frameless: elimina la barra nativa y evita sombras raras en algunos sistemas
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint | Qt.WindowSystemMenuHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)

        # 🚩 Temporalmente desactivamos setWindowIcon por si es la causa de la ventana fantasma
        # self._app_icon = app_icon if (app_icon and not app_icon.isNull()) else None
        # if self._app_icon:
        #     self.setWindowIcon(self._app_icon)
        self._app_icon = app_icon

        self.theme_name = "dark"
        self.theme = THEME[self.theme_name]

        self.setWindowTitle(f"HelpDesk Manager - {self.version}")
        self.setMinimumSize(960, 640)
        self.resize(1100, 720)
        self.setMaximumSize(1400, 900)

        # Bus global
        self.status_bus = StatusBus()

        self.toast_mgr = ToastManager(self)
        # 🚩 Retrasamos la conexión de notificaciones para evitar disparos al inicio
        QTimer.singleShot(1500, lambda: self.status_bus.notify_requested.connect(self.toast_mgr.show))

        # Menú: se construye solo al primer clic en ☰ para evitar ventana nativa del menubar al inicio.
        self._menubar_built = False
        self.menuBar().setVisible(False)  # ✅ Aseguramos que esté oculta

        root = QWidget(self)
        self.setCentralWidget(root)
        self.root = root

        self.v = QVBoxLayout(root)
        self.v.setContentsMargins(0, 0, 0, 0)
        self.v.setSpacing(0)

        # ✅ Titlebar custom
        # ✅ Barra de título modular
        self.title_bar = ProTitleBar(self)
        self.title_bar.menu_requested.connect(self._show_app_menu)
        self.v.addWidget(self.title_bar, 0)

        # Contenedor interno (margen superior reducido para acercar header a la barra; horizontales sin cambio)
        self.inner = QWidget(root)
        self.inner_lay = QVBoxLayout(self.inner)
        self.inner_lay.setContentsMargins(28, 20, 28, 22)  # ✅ Más margen superior (antes 8)
        self.inner_lay.setSpacing(14)

        # Header: [ Icono + Título/Subtítulo ]  stretch  [ Theme Toggle ]
        header_row = QHBoxLayout()
        header_row.setSpacing(16)

        left_outer = QHBoxLayout()
        left_outer.setContentsMargins(10, 0, 0, 0)
        left_outer.setSpacing(18)

        self.header_icon = QLabel(self)
        self.header_icon.setFixedSize(48, 48) # ✅ Tamaño con presencia
        self.header_icon.setScaledContents(True)
        
        # Intentamos cargar tu icono diseñado
        assets_dir = Path(__file__).resolve().parent / "assets"
        icon_path = assets_dir / "ico.png"
        
        if icon_path.exists():
            self.header_icon.setPixmap(QtGui.QPixmap(str(icon_path)))
        else:
            # Fallback por si acaso
            self.header_icon.setText("📁")
            self.header_icon.setStyleSheet("font-size: 32px;")
            
        left_outer.addWidget(self.header_icon, 0, Qt.AlignVCenter)

        left = QVBoxLayout()
        left.setSpacing(5)
        t = self.theme # ✅ Definimos 't' para que las siguientes líneas funcionen

        self.header_title = QLabel("HELPDESK MANAGER")
        self.header_title.setObjectName("HeaderTitle")
        font_h = QFont("Outfit", 28, QFont.Weight.Bold)
        font_h.setPointSizeF(26) # ✅ Blindaje Header
        self.header_title.setFont(font_h)
        self.header_title.setStyleSheet(f"color: {t['orange']}; background: transparent;")
        
        # Efecto Glow (Sombra blanca sutil)
        glow = QtWidgets.QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(15)
        glow.setOffset(0, 0)
        glow.setColor(QtGui.QColor(255, 154, 46, 120)) 
        self.header_title.setGraphicsEffect(glow)
        
        left.addWidget(self.header_title)

        self.header_subtitle = QLabel("PLATAFORMA DE GESTIÓN • OPERACIONES")
        self.header_subtitle.setObjectName("HeaderSubtitle")
        font_sub = QFont("Inter", 9, QFont.Weight.Normal)
        font_sub.setPointSizeF(8.5) # ✅ Blindaje Subtítulo
        self.header_subtitle.setFont(font_sub)
        self.header_subtitle.setContentsMargins(2, 0, 0, 0)
        # ✅ Estética Small-Caps con espaciado para un look gerencial
        self.header_subtitle.setStyleSheet(f"color: {t['muted']}; letter-spacing: 2px;")
        left.addWidget(self.header_subtitle)

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

        self.footer_lbl = QLabel("Hecho por: Iván Martínez", self)
        font_footer = QFont("Segoe UI", 11)
        font_footer.setPointSizeF(11)
        self.footer_lbl.setFont(font_footer)
        footer.addWidget(self.footer_lbl, 1, Qt.AlignLeft)

        # 🔕 Estado global: oculto por defecto (y NO mostramos "Listo")
        self.global_status_lbl = QLabel("", self)
        font_status = QFont("Segoe UI", 10)
        font_status.setPointSizeF(10)
        self.global_status_lbl.setFont(font_status)
        self.global_status_lbl.setVisible(False)
        footer.addWidget(self.global_status_lbl, 0, Qt.AlignRight)

        self.chk_startup = ModernCheckBox("Iniciar con Windows")
        footer.addWidget(self.chk_startup, 0, Qt.AlignRight)

        # ✅ QSizeGrip para resize en frameless
        self._grip = QSizeGrip(self)
        self._grip.setFixedSize(18, 18)

        footer_wrap = QWidget(self.inner)
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
    def _show_app_menu(self):
        """Muestra el menú completo (Archivo, FTP, Ayuda) bajo el botón de hamburguesa."""
        from .ui.menubar import build_menubar
        
        # Si no se ha construido el menubar interno (que usamos como base), lo hacemos
        if not hasattr(self, "_internal_menubar"):
            self._internal_menubar = QtWidgets.QMenuBar(self)
            build_menubar(self, lambda: None) # Usamos el build original
            self._internal_menubar.setVisible(False)

        m = QMenu(self)
        m.setWindowFlags(m.windowFlags() | Qt.NoDropShadowWindowHint | Qt.FramelessWindowHint)
        m.setAttribute(Qt.WA_TranslucentBackground)
        
        t = self.theme
        m.setStyleSheet(f"""
            QMenu {{
                background: #1A1A1A;
                color: {t['text']};
                border: 1px solid #333333;
                border-radius: 12px;
                padding: 8px 4px;
            }}
            QMenu::item {{
                padding: 10px 32px;
                border-radius: 6px;
                margin: 2px 4px;
                font-weight: 600;
            }}
            QMenu::item:selected {{
                background: #2D2D2D;
                color: {t['orange']};
            }}
            QMenu::separator {{
                height: 1px;
                background: #333333;
                margin: 4px 10px;
            }}
        """)

        # Copiamos las acciones del MenuBar real al Popup moderno
        mb = self.menuBar()
        if mb:
            for act in mb.actions():
                if act.menu():
                    m.addMenu(act.menu())
                else:
                    m.addAction(act)
        
        # Posicionar el menú debajo del botón del menú en la barra de título
        btn = self.title_bar._btn_menu
        btn_pos = btn.mapToGlobal(QPoint(0, btn.height() + 5))
        m.exec(btn_pos)

    def apply_theme(self):
        self.theme = THEME[self.theme_name]
        t = self.theme

        # fondo general
        self.root.setStyleSheet(f"background: {t['app_bg']};")
        self.setStyleSheet(f"""
            QMainWindow {{ background: {t['app_bg']}; }}
            QMenu {{
                background-color: {t.get('card_bg', '#2A2A2A')};
                color: {t['text']} !important;
                border: 1px solid {t.get('card_border', '#3A3A3A')};
                padding: 5px;
                border-radius: 8px;
            }}
            QMenu::item {{
                padding: 8px 28px;
                color: {t['text']} !important;
                background-color: transparent;
                border-radius: 4px;
                margin: 2px;
            }}
            QMenu::item:selected {{
                background-color: {t.get('panel_bg2', '#333333')};
                color: {t['orange']} !important;
            }}
            QMenu::separator {{
                height: 1px;
                background: {t.get('card_border', '#3A3A3A')};
                margin: 5px 10px;
            }}
        """)

        # titlebar custom + botones
        self.title_bar.setStyleSheet(f"""
            QWidget#ProMainTitleBar {{
                background: {t['app_bg']};
                border-bottom: 1px solid {t['card_border']};
            }}
            QLabel#ProMainTitle {{
                color: {t['text']};
                font-weight: 800;
            }}
            QToolButton#ProWinBtn {{
                background: transparent;
                border: none;
                border-radius: 10px;
                padding: 6px 14px;
                color: {t['muted']};
                font-weight: bold;
                font-size: 14px;
            }}
            QToolButton#ProWinBtn:hover {{
                background: {t['surface_raised']};
                color: {t['orange']};
            }}
            QToolButton#ProWinBtnClose {{
                background: transparent;
                border: none;
                border-radius: 10px;
                padding: 6px 14px;
                color: {t['muted']};
            }}
            QToolButton#ProWinBtnClose:hover {{
                background: #E81123;
                color: white;
            }}
        """)

        self.header_title.setStyleSheet(f"color: {t['orange']}; background: transparent;")
        self.header_subtitle.setStyleSheet(f"color: {t['muted']}; letter-spacing: 2px;")
        self.footer_lbl.setStyleSheet(f"color: {t['muted']}; font-size: 10px; letter-spacing: 0.5px;")
        self.global_status_lbl.setStyleSheet(f"color: {t['orange']}; font-weight: 800; text-transform: uppercase; font-size: 10px;")

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

        if getattr(self, "_menubar_built", False):
            apply_menubar_theme(self, t)
            mb = self.menuBar()
            mb.setStyleSheet(
                "QMenuBar { background: %(bg)s; color: %(fg)s; }"
                "QMenuBar::item { background: transparent; padding: 4px 10px; color: %(fg)s; }"
                "QMenuBar::item:selected { background: %(hover)s; color: %(orange)s; }"
                % {
                    "bg": t["app_bg"],
                    "fg": t["text"],
                    "hover": t["surface_raised"],
                    "orange": t["orange"],
                }
            )
            mb.hide()  # ✅ Volvemos a ocultar tras aplicar estilo por si Qt la hizo visible

    # Events
    def on_toggle_theme(self, is_light: bool):
        self.theme_name = "light" if is_light else "dark"
        self.apply_theme()

    def on_tab_changed(self, idx: int):
        self.stack.setCurrentIndex(idx)
