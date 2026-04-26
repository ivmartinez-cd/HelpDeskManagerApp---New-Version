# tests/test_ui.py
import pytest
from PySide6 import QtCore
from pyside_ui.main_window import MainWindow

def test_main_window_setup(qtbot):
    """Verifica que la ventana principal se cree y configure correctamente."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    
    # Esperamos un momento a que Qt procese eventos
    qtbot.wait(100)
    
    # El título debería contener "HelpDesk Manager"
    assert "HelpDesk Manager" in window.windowTitle()
    
    # El StackedWidget debería tener 3 pestañas
    assert window.stack.count() == 3
    
    # Verificar que el controlador de contadores existe
    assert window.contadores_tab._controller is not None
