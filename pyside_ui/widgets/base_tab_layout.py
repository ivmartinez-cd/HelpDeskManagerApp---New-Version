# pyside_ui/widgets/base_tab_layout.py
"""
BaseTabLayout — Contenedor reutilizable para tabs con estructura consistente.

Estructura:
  MainVBoxLayout
    Header (título + barra de herramientas opcional)
    Content (área principal, expande)
    ActionBar (botones alineados a la derecha)
    Footer (texto, checkboxes, etc.)

Los tabs añaden widgets/layouts a los slots expuestos; no se usa posicionamiento absoluto.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)


# Valores recomendados para consistencia visual
OUTER_MARGIN = 20
SECTION_SPACING = 16
INTERNAL_SPACING = 8


class BaseTabLayout(QWidget):
    """
    Contenedor con cuatro secciones: header, content, action_bar, footer.
    Expone los layouts para que el tab los rellene.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self._main = QVBoxLayout(self)
        self._main.setContentsMargins(OUTER_MARGIN, OUTER_MARGIN, OUTER_MARGIN, OUTER_MARGIN)
        self._main.setSpacing(SECTION_SPACING)

        # ─── 1. Header (título + toolbar opcional) ─────────────────────────
        self._header_widget = QWidget()
        self.header_layout = QVBoxLayout(self._header_widget)
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        self.header_layout.setSpacing(INTERNAL_SPACING)
        self._main.addWidget(self._header_widget, 0)

        # ─── 2. Content (expande) ───────────────────────────────────────────
        self._content_widget = QWidget()
        self.content_layout = QVBoxLayout(self._content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(INTERNAL_SPACING)
        self._main.addWidget(self._content_widget, 1)

        # ─── 3. Action bar (stretch a la izquierda → botones a la derecha) ──
        self._action_bar_widget = QWidget()
        self.action_bar_layout = QHBoxLayout(self._action_bar_widget)
        self.action_bar_layout.setContentsMargins(0, 0, 0, 0)
        self.action_bar_layout.setSpacing(INTERNAL_SPACING)
        self.action_bar_layout.addStretch(1)
        self._main.addWidget(self._action_bar_widget, 0)

        # ─── 4. Footer ─────────────────────────────────────────────────────
        self._footer_widget = QWidget()
        self.footer_layout = QHBoxLayout(self._footer_widget)
        self.footer_layout.setContentsMargins(0, 0, 0, 0)
        self.footer_layout.setSpacing(INTERNAL_SPACING)
        self._main.addWidget(self._footer_widget, 0)
