# scratch/detect_windows.py
import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# Importamos tu app
from pyside_ui.app import main

def analyze_windows():
    app = QApplication.instance()
    if not app:
        with open("log_ventanas.txt", "w", encoding="utf-8") as f:
            f.write("No se encontró instancia de QApplication.\n")
        return

    windows = app.topLevelWidgets()
    with open("log_ventanas.txt", "w", encoding="utf-8") as f:
        f.write(f"--- DIAGNÓSTICO DE VENTANAS ({len(windows)} detectadas) ---\n")
        for i, w in enumerate(windows):
            f.write(f"Ventana #{i}:\n")
            f.write(f"  - Clase: {w.__class__.__name__}\n")
            f.write(f"  - Título: '{w.windowTitle()}'\n")
            f.write(f"  - Visible: {w.isVisible()}\n")
            f.write(f"  - Geometría: {w.geometry()}\n")
            f.write(f"  - Flags: {w.windowFlags()}\n")
            f.write("-" * 40 + "\n")
    
    print("\n[OK] Diagnóstico guardado en log_ventanas.txt")

if __name__ == "__main__":
    # Inyectamos el timer en la cola de eventos antes de que empiece el loop
    QTimer.singleShot(4000, analyze_windows)
    
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        with open("log_ventanas.txt", "a", encoding="utf-8") as f:
            f.write(f"Error en main: {e}\n")
        sys.exit(1)
