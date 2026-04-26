# pyside_ui/widgets/action_card.py
from __future__ import annotations
from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, Signal

from .effects import apply_shadow


class ActionCard(QtWidgets.QFrame):
    clicked = Signal()

    def __init__(
        self,
        title: str,
        description: str,
        icon_text: str = "⚡",
        parent: Optional[QtWidgets.QWidget] = None
    ):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self._theme: dict = {}
        
        self.setMinimumHeight(85)
        self.setObjectName("ActionCard")
        
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(12)
        
        # Icon Container
        self.icon_lbl = QtWidgets.QLabel(icon_text)
        font_icon = QtGui.QFont("Segoe UI", 20)
        font_icon.setPointSizeF(20)
        self.icon_lbl.setFont(font_icon)
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        self.icon_lbl.setFixedSize(48, 48)
        self.icon_lbl.setObjectName("ActionIcon")
        lay.addWidget(self.icon_lbl)
        
        # Text Container
        text_lay = QtWidgets.QVBoxLayout()
        text_lay.setSpacing(4)
        
        self.title_lbl = QtWidgets.QLabel(title)
        self.title_lbl.setObjectName("ActionTitle")
        font_t = QtGui.QFont("Segoe UI", 15, QtGui.QFont.Weight.Bold)
        font_t.setPointSizeF(11.5)
        self.title_lbl.setFont(font_t)
        
        self.desc_lbl = QtWidgets.QLabel(description)
        self.desc_lbl.setObjectName("ActionDesc")
        self.desc_lbl.setWordWrap(True)
        font_d = QtGui.QFont("Segoe UI", 13)
        font_d.setPointSizeF(9.5)
        self.desc_lbl.setFont(font_d)
        
        text_lay.addWidget(self.title_lbl)
        text_lay.addWidget(self.desc_lbl)
        lay.addLayout(text_lay, 1)
        
        # Arrow icon at the end
        self.arrow_lbl = QtWidgets.QLabel("→")
        self.arrow_lbl.setObjectName("ActionArrow")
        font_a = QtGui.QFont("Segoe UI", 18, QtGui.QFont.Weight.Bold)
        font_a.setPointSizeF(14)
        self.arrow_lbl.setFont(font_a)
        lay.addWidget(self.arrow_lbl)

    def set_theme(self, theme: dict):
        self._theme = theme
        t = self._theme
        
        self.setStyleSheet(f"""
            QFrame#ActionCard {{
                background-color: {t.get('surface', '#1E1E1E')};
                border: 1px solid {t.get('card_border', '#2A2A2A')};
                border-radius: 16px;
            }}
            QFrame#ActionCard:hover {{
                background-color: {t.get('surface_raised', '#252525')};
                border: 1px solid {t.get('orange', '#FF9A2E')};
            }}
            
            QLabel#ActionIcon {{
                background-color: {t.get('app_bg', '#121212')};
                border-radius: 12px;
                font-size: 20px;
                color: {t.get('orange', '#FF9A2E')};
            }}
            
            QLabel#ActionTitle {{
                color: {t.get('text', '#F5F5F5')};
                font-size: 15px;
                font-weight: 700;
                background: transparent;
            }}
            
            QLabel#ActionDesc {{
                color: {t.get('muted', '#9CA3AF')};
                font-size: 13px;
                background: transparent;
            }}
            
            QLabel#ActionArrow {{
                color: {t.get('muted', '#9CA3AF')};
                font-size: 18px;
                font-weight: bold;
                background: transparent;
            }}
        """)
        
        apply_shadow(self, blur=20, y=4, rgba=t.get("shadow_color", (0, 0, 0, 100)))

    def setEnabled(self, enabled: bool) -> None:
        super().setEnabled(enabled)
        if not enabled:
            eff = QtWidgets.QGraphicsOpacityEffect(self)
            eff.setOpacity(0.4)
            self.setGraphicsEffect(eff)
            self.setCursor(Qt.ArrowCursor)
        else:
            apply_shadow(self, blur=20, y=4, rgba=self._theme.get("shadow_color", (0, 0, 0, 100)))
            self.setCursor(Qt.PointingHandCursor)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)

    def enterEvent(self, event: QtGui.QEnterEvent):
        apply_shadow(self, blur=28, y=6, rgba=self._theme.get("shadow_color", (0, 0, 0, 140)))
        super().enterEvent(event)

    def leaveEvent(self, event: QtGui.QEvent):
        apply_shadow(self, blur=20, y=4, rgba=self._theme.get("shadow_color", (0, 0, 0, 100)))
        super().leaveEvent(event)
