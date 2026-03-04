# pyside_ui/ui/menubar.py
from __future__ import annotations

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenuBar


def build_menubar(win, on_noop) -> None:
    """
    Menú superior: Archivo | FTP | Ayuda.

    Regla pedida:
    - NO mostrar toasts al tocar el menú.
    - Los únicos toasts deben salir por confirmación (éxito/error) desde el controller.
    """
    mb: QMenuBar = win.menuBar()

    # Archivo
    m_archivo = mb.addMenu("Archivo")
    act_salir = QAction("Salir (Ctrl+Q)", win)
    act_salir.setShortcut("Ctrl+Q")
    act_salir.triggered.connect(win.close)
    m_archivo.addAction(act_salir)

    # FTP
    m_ftp = mb.addMenu("FTP")

    def _get_ctrl():
        return getattr(win, "ftp_controller", None)

    def _call(method_name: str):
        ctrl = _get_ctrl()
        if ctrl is None:
            on_noop()
            return

        fn = getattr(ctrl, method_name, None)
        if not callable(fn):
            on_noop()
            return

        fn()

    act_add = QAction("Agregar cliente FTP...", win)
    act_add.triggered.connect(lambda: _call("add_client"))
    m_ftp.addAction(act_add)

    act_edit = QAction("Modificar cliente FTP...", win)
    act_edit.triggered.connect(lambda: _call("edit_client"))
    m_ftp.addAction(act_edit)

    m_ftp.addSeparator()

    act_del = QAction("Eliminar cliente FTP...", win)
    act_del.triggered.connect(lambda: _call("delete_client"))
    m_ftp.addAction(act_del)

    # Ayuda
    m_ayuda = mb.addMenu("Ayuda")
    act_changelog = QAction("Changelog", win)
    act_changelog.triggered.connect(on_noop)
    m_ayuda.addAction(act_changelog)


def apply_menubar_theme(menubar: QMenuBar, theme: dict) -> None:
    # Mantener compatibilidad (tema lo aplica MainWindow)
    return
