    # pyside_ui/widgets/segmented_tabs.py
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout, QSizePolicy

from .effects import apply_shadow


class SegmentedTabs(QWidget):
    changed = Signal(int)

    def __init__(self, labels: list[str], parent=None):
        super().__init__(parent)
        self._theme: dict = {}
        self._buttons: list[QPushButton] = []
        self._active = 0

        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(6)

        for i, lab in enumerate(labels):
            b = QPushButton(lab)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, idx=i: self.set_active(idx))
            b.setMinimumHeight(34)
            b.setMinimumWidth(110 if i == 0 else 90)
            b.setFont(QFont("Segoe UI", 11, QFont.DemiBold))
            self._buttons.append(b)
            lay.addWidget(b)

        self.setObjectName("segRoot")

    def set_theme(self, theme: dict):
        self._theme = theme or {}
        apply_shadow(self, blur=24, y=6, rgba=self._theme.get("shadow_color", (0, 0, 0, 120)))
        self._apply_styles()

    def set_active(self, idx: int):
        if idx == self._active:
            return
        self._active = idx
        self._apply_styles()
        self.changed.emit(idx)

    def _apply_styles(self):
        t = self._theme or {}
        self.setStyleSheet(f"""
            QWidget#segRoot {{
                background: {t.get("seg_bg", "#2A2A2A")};
                border: 1px solid {t.get("card_border", "#3A3A3A")};
                border-radius: 18px;
            }}
        """)

        for i, b in enumerate(self._buttons):
            if i == self._active:
                b.setStyleSheet(f"""
                    QPushButton {{
                        background: {t.get("seg_selected", "#FF9A2E")};
                        color: {t.get("seg_text_selected", "#FFFFFF")};
                        border: none;
                        border-radius: 16px;
                        padding: 6px 14px;
                        font: 600 11pt "Segoe UI";
                    }}
                """)
            else:
                b.setStyleSheet(f"""
                    QPushButton {{
                        background: {t.get("seg_unselected", "#2A2A2A")};
                        color: {t.get("seg_text", "#EAEAEA")};
                        border: none;
                        border-radius: 16px;
                        padding: 6px 14px;
                        font: 600 11pt "Segoe UI";
                    }}
                    QPushButton:hover {{
                        background: {t.get("seg_hover", "#333333")};
                    }}
                """)
