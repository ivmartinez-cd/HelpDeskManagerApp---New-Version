# pyside_ui/ui/title_bar.py
from __future__ import annotations
from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QToolButton, QMenu, QSizePolicy
from PySide6.QtGui import QFont

class ProTitleBar(QWidget):
    """
    Barra de título personalizada y modular.
    Maneja el arrastre de ventana, el menú de app y los controles de ventana.
    """
    menu_requested = Signal()

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self._parent = parent
        self.setFixedHeight(40)
        self._drag_pos = QPoint()

        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 0, 10, 0)
        lay.setSpacing(8)

        # ☰ Botón Menú
        self._btn_menu = QToolButton(self)
        font_btn = QFont("Segoe UI", 10)
        font_btn.setPointSizeF(10)
        self._btn_menu.setFont(font_btn)
        self._btn_menu.setObjectName("ProWinBtn")
        self._btn_menu.setText("☰")
        self._btn_menu.setFixedSize(42, 38)
        self._btn_menu.setToolTip("Menú de Aplicación")
        self._btn_menu.clicked.connect(self.menu_requested.emit)
        lay.addWidget(self._btn_menu, 0, Qt.AlignVCenter)

        # Título de Ventana (Muestra el título de la ventana principal)
        self._title = QLabel(parent.windowTitle(), self)
        self._title.setObjectName("ProMainTitle")
        font_title = QFont("Segoe UI", 10, QFont.Bold)
        font_title.setPointSizeF(10)
        self._title.setFont(font_title)
        lay.addWidget(self._title, 0, Qt.AlignVCenter)

        lay.addStretch(1)

        # Botones de Control (Minimizar / Cerrar)
        self._btn_min = QToolButton(self)
        font_ctrl = QFont("Segoe UI", 10)
        font_ctrl.setPointSizeF(10)
        self._btn_min.setFont(font_ctrl)
        self._btn_min.setObjectName("ProWinBtn")
        self._btn_min.setText("—")
        self._btn_min.setFixedSize(45, 40)
        self._btn_min.clicked.connect(parent.showMinimized)
        lay.addWidget(self._btn_min)

        self._btn_close = QToolButton(self)
        self._btn_close.setFont(font_ctrl)
        self._btn_close.setObjectName("ProWinBtnClose")
        self._btn_close.setText("✕")
        self._btn_close.setFixedSize(45, 40)
        self._btn_close.clicked.connect(parent.close)
        lay.addWidget(self._btn_close)

    def set_title(self, title: str):
        self._title.setText(title)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self._parent.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self._parent.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def apply_theme(self, t: dict):
        # El estilo real vive en el QSS global de MainWindow, 
        # pero aquí podemos ajustar propiedades específicas si fuera necesario.
        pass
