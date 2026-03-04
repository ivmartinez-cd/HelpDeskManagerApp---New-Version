# pyside_ui/app.py
from __future__ import annotations

import sys
import os
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from pyside_ui.main_window import MainWindow


def _set_windows_appusermodelid(app_id: str) -> None:
    """Ayuda a que Windows muestre el ícono correcto en la taskbar (especialmente en debug)."""
    if os.name != "nt":
        return
    try:
        import ctypes  # type: ignore
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        # no rompemos nada si falla
        pass


def _load_app_icon() -> QIcon:
    assets_dir = Path(__file__).resolve().parent / "assets"
    icon_path = assets_dir / "ico.png"
    if not icon_path.is_file():
        # Dejamos un icono vacío si no está; evita crash.
        return QIcon()
    return QIcon(str(icon_path))


def main() -> int:
    # Para que el icono se vea bien en taskbar (Windows)
    _set_windows_appusermodelid("HelpDeskManagerApp.PySide6.Prototype")

    app = QApplication(sys.argv)

    icon = _load_app_icon()
    if not icon.isNull():
        app.setWindowIcon(icon)

    win = MainWindow(app_icon=icon)
    win.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
    