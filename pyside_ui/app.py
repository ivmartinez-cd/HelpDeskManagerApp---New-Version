# pyside_ui/app.py
from __future__ import annotations

import atexit
import os
import sys
from pathlib import Path

from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from pyside_ui.main_window import MainWindow

LOCAL_ROOT = Path(os.environ.get('LOCALAPPDATA', os.environ.get('APPDATA', '.'))) / "HelpDeskManagerApp"

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
    """True si esta instancia puede seguir; False si ya hay otra ventana (evita 2 ventanas).

    Usa O_CREAT|O_EXCL para creación atómica del lock — elimina la race condition
    TOCTOU del patrón check-then-write anterior.
    """
    global _LOCK_FILE
    import tempfile
    lock_dir = Path(tempfile.gettempdir())
    lock_path = lock_dir / "HelpDeskManagerApp.PySide6.lock"
    try:
        try:
            # Creación atómica: falla con FileExistsError si otro proceso se adelantó.
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
        except FileExistsError:
            # El archivo ya existe — verificar si el proceso dueño sigue vivo.
            try:
                pid = int(lock_path.read_text().strip())
            except (ValueError, OSError):
                pid = None
            if pid is not None and _process_exists(pid):
                return False
            # Lock obsoleto: eliminar y reclamar atómicamente.
            lock_path.unlink(missing_ok=True)
            try:
                fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
            except FileExistsError:
                # Otro proceso lo reclamó en el instante entre unlink y open.
                return False
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
    
    # ✅ Blindaje Global Anti-Warning 2026
    from PySide6.QtGui import QFont
    global_font = QFont("Segoe UI Variable Text", 10)
    global_font.setPointSizeF(10)
    app.setFont(global_font)

    icon = _load_app_icon()
    if not icon.isNull():
        app.setWindowIcon(icon)

    try:
        win = MainWindow(app_icon=icon)
        win.show()

        def diag_win():
            try:
                from PySide6.QtWidgets import QApplication
                windows = QApplication.topLevelWidgets()
                log_file = LOCAL_ROOT / "log_ventanas.txt"
                with open(log_file, "w", encoding="utf-8") as f:
                    f.write(f"--- DIAGNOSTICO --- {len(windows)} ventanas\n")
                    for i, w in enumerate(windows):
                        f.write(f"W#{i}: {w.__class__.__name__} | Title: {w.windowTitle()} | Vis: {w.isVisible()} | Geo: {w.geometry()}\n")
                        if w.__class__.__name__ == "MainWindow":
                            f.write("  Children of MainWindow:\n")
                            for c in w.findChildren(QtWidgets.QWidget):
                                if c.isVisible():
                                    f.write(f"  - {c.__class__.__name__} | Obj: {c.objectName()} | Geo: {c.geometry()}\n")
            except: pass

        from PySide6.QtCore import QTimer
        QTimer.singleShot(3000, diag_win)

        return app.exec()
    except Exception as e:
        import traceback
        crash_file = LOCAL_ROOT / "crash_app.txt"
        with open(crash_file, "w", encoding="utf-8") as f:
            f.write(f"ERROR CRÍTICO EN LA APP:\n{str(e)}\n\n")
            f.write(traceback.format_exc())
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
    