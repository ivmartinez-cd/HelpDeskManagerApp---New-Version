# pyside_ui/ui/dialog_kit.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from PySide6 import QtWidgets
from PySide6.QtCore import Qt, QPoint


@dataclass(frozen=True)
class DialogTheme:
    app_bg: str = "#1E1E1E"
    panel_bg: str = "#2A2A2A"
    panel_bg2: str = "#303030"
    text: str = "#EAEAEA"
    muted: str = "#A0A0A0"
    orange: str = "#F59E0B"
    border: str = "#3A3A3A"


def get_theme(parent: QtWidgets.QWidget) -> Dict[str, str]:
    try:
        w = parent.window()
        t = getattr(w, "theme", None)
        return t if isinstance(t, dict) else {}
    except Exception:
        return {}


def resolve_theme(theme: dict) -> DialogTheme:
    """
    Keys reales esperadas:
      - app_bg, text, muted, orange
      - card_bg, card_border
      - btn_bg, btn_hover
    """
    card_bg = theme.get("card_bg", DialogTheme.panel_bg)
    btn_bg = theme.get("btn_bg", card_bg)

    return DialogTheme(
        app_bg=theme.get("app_bg", DialogTheme.app_bg),
        panel_bg=btn_bg,
        panel_bg2=theme.get("btn_hover", DialogTheme.panel_bg2),
        text=theme.get("text", DialogTheme.text),
        muted=theme.get("muted", DialogTheme.muted),
        orange=theme.get("orange", DialogTheme.orange),
        border=theme.get("card_border", theme.get("border", DialogTheme.border)),
    )


def apply_dialog_style(widget: QtWidgets.QWidget, theme: dict) -> None:
    t = resolve_theme(theme)
    widget.setStyleSheet(
        f"""
        QDialog {{
            background: transparent;
            color: {t.text};
        }}

        /* ✅ Labels: SIEMPRE con color (evita que vuelvan a negro) */
        QLabel {{
            background: transparent;
            color: {t.text};
        }}
        QLabel#Subtitle {{
            color: {t.muted};
            font-size: 12px;
        }}

        QLineEdit, QComboBox {{
            background: {t.panel_bg};
            border: 1px solid {t.border};
            border-radius: 10px;
            padding: 8px 10px;
            color: {t.text};
        }}
        QLineEdit:focus, QComboBox:focus {{
            border: 1px solid {t.orange};
        }}

        QListWidget {{
            background: {t.panel_bg};
            border: 1px solid {t.border};
            border-radius: 12px;
            padding: 6px;
        }}
        QListWidget::item {{
            padding: 8px 10px;
            border-radius: 10px;
            color: {t.text};
        }}
        QListWidget::item:hover {{
            background: {t.panel_bg2};
        }}
        QListWidget::item:selected {{
            background: {t.panel_bg2};
            color: {t.text};
        }}

        QPushButton {{
            background: {t.panel_bg};
            border: 1px solid {t.border};
            border-radius: 12px;
            padding: 8px 14px;
            color: {t.text};
        }}
        QPushButton:hover {{
            background: {t.panel_bg2};
        }}
        QPushButton#Primary {{
            background: {t.orange};
            border: 1px solid {t.orange};
            color: #111111;
            font-weight: 700;
        }}
        QPushButton#Danger {{
            background: {t.panel_bg2};
            border: 1px solid {t.orange};
            color: {t.text};
            font-weight: 700;
        }}

        QFrame#Card {{
            background: {theme.get("card_bg", "#2A2A2A")};
            border: 1px solid {t.border};
            border-radius: 16px;
        }}

        QWidget#ProTitleBar {{
            background: {theme.get("card_bg", "#2A2A2A")};
            border-bottom: 1px solid {t.border};
        }}
        QLabel#ProTitle {{
            background: transparent;
            color: {t.text};
            font-weight: 700;
        }}
        QToolButton#ProClose {{
            background: transparent;
            border: 1px solid {t.border};
            border-radius: 10px;
            padding: 6px 10px;
            color: {t.text};
        }}
        QToolButton#ProClose:hover {{
            background: {t.panel_bg2};
            border: 1px solid {t.orange};
        }}
        """
    )


def make_subtitle(subtitle: str) -> QtWidgets.QLabel:
    sub_lbl = QtWidgets.QLabel(subtitle)
    sub_lbl.setObjectName("Subtitle")
    sub_lbl.setWordWrap(True)
    return sub_lbl


def make_card() -> QtWidgets.QFrame:
    card = QtWidgets.QFrame()
    card.setObjectName("Card")
    return card


def make_button_row(
    *,
    ok_text: str,
    cancel_text: str = "Cancelar",
    ok_object_name: str = "Primary",
) -> tuple[QtWidgets.QPushButton, QtWidgets.QPushButton, QtWidgets.QHBoxLayout]:
    btn_cancel = QtWidgets.QPushButton(cancel_text)
    btn_ok = QtWidgets.QPushButton(ok_text)
    btn_ok.setObjectName(ok_object_name)

    row = QtWidgets.QHBoxLayout()
    row.addStretch(1)
    row.addWidget(btn_cancel)
    row.addWidget(btn_ok)
    return btn_ok, btn_cancel, row


class BaseProDialog(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget, title: str, subtitle: str, *, w: int = 560, h: int = 0):
        super().__init__(parent)
        self.setModal(True)
        self.setMinimumWidth(w)
        if h:
            self.setMinimumHeight(h)

        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self._theme_dict = get_theme(parent)
        apply_dialog_style(self, self._theme_dict)

        self._drag_pos: QPoint | None = None
        self._drag_enabled = False

        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._shell = make_card()
        outer.addWidget(self._shell)

        shell_lay = QtWidgets.QVBoxLayout(self._shell)
        shell_lay.setContentsMargins(16, 0, 16, 16)
        shell_lay.setSpacing(12)

        tb = QtWidgets.QWidget()
        tb.setObjectName("ProTitleBar")
        tb_lay = QtWidgets.QHBoxLayout(tb)
        tb_lay.setContentsMargins(16, 12, 12, 12)
        tb_lay.setSpacing(10)

        self._title_lbl = QtWidgets.QLabel(title)
        self._title_lbl.setObjectName("ProTitle")

        btn_close = QtWidgets.QToolButton()
        btn_close.setObjectName("ProClose")
        btn_close.setText("✕")
        btn_close.clicked.connect(self.reject)

        tb_lay.addWidget(self._title_lbl, 1)
        tb_lay.addWidget(btn_close, 0, Qt.AlignRight)
        shell_lay.addWidget(tb)

        self._root = QtWidgets.QVBoxLayout()
        self._root.setContentsMargins(0, 12, 0, 0)
        self._root.setSpacing(12)

        if subtitle:
            self._root.addWidget(make_subtitle(subtitle))

        shell_lay.addLayout(self._root)
        self.setWindowTitle(title)

    @property
    def root_layout(self) -> QtWidgets.QVBoxLayout:
        return self._root

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            if e.position().y() <= 52:
                self._drag_enabled = True
                self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
                e.accept()
                return
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._drag_enabled and self._drag_pos is not None and (e.buttons() & Qt.LeftButton):
            self.move(e.globalPosition().toPoint() - self._drag_pos)
            e.accept()
            return
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        self._drag_enabled = False
        self._drag_pos = None
        super().mouseReleaseEvent(e)


class MessageDialog(BaseProDialog):
    def __init__(self, parent: QtWidgets.QWidget, title: str, message: str, ok_text: str = "Aceptar"):
        super().__init__(parent, title, message, w=520)

        btn_ok, _btn_cancel, row = make_button_row(ok_text=ok_text, cancel_text="", ok_object_name="Primary")
        row.itemAt(1).widget().setVisible(False)  # type: ignore
        btn_ok.clicked.connect(self.accept)
        self.root_layout.addLayout(row)


class ConfirmDialog(BaseProDialog):
    def __init__(
        self,
        parent: QtWidgets.QWidget,
        title: str,
        message: str,
        confirm_text: str = "Confirmar",
        cancel_text: str = "Cancelar",
        *,
        danger: bool = False,
    ):
        super().__init__(parent, title, message, w=560)

        ok_name = "Danger" if danger else "Primary"
        btn_ok, btn_cancel, row = make_button_row(ok_text=confirm_text, cancel_text=cancel_text, ok_object_name=ok_name)
        btn_cancel.clicked.connect(self.reject)
        btn_ok.clicked.connect(self.accept)
        self.root_layout.addLayout(row)


def warn(parent: QtWidgets.QWidget, title: str, message: str) -> None:
    MessageDialog(parent, title, message).exec()
