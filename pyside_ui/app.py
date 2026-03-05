# pyside_ui/app.py
from __future__ import annotations

import atexit
import os
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from pyside_ui.main_window import MainWindow

_LOCK_FILE: Path | None = None


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


def _single_instance_lock() -> bool:
    """True si esta instancia puede seguir; False si ya hay otra ventana (evita 2 ventanas)."""
    global _LOCK_FILE
    import tempfile
    lock_dir = Path(tempfile.gettempdir())
    lock_path = lock_dir / "HelpDeskManagerApp.PySide6.lock"
    try:
        if lock_path.exists():
            try:
                pid = int(lock_path.read_text().strip())
            except (ValueError, OSError):
                pid = None
            if pid is not None and _process_exists(pid):
                return False
            lock_path.unlink(missing_ok=True)
        lock_path.write_text(str(os.getpid()))
        _LOCK_FILE = lock_path
        atexit.register(lambda: lock_path.unlink(missing_ok=True))
        return True
    except Exception:
        return True


def _process_exists(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def main() -> int:
    if not _single_instance_lock():
        return 0

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
    