from __future__ import annotations

from PySide6 import QtCore


class StatusBus(QtCore.QObject):
    """
    Canal único de mensajes de estado y notificaciones.
    Paso 1: solo status (texto).
    Paso 2: toasts (notify) usando la señal notify_requested.
    """
    status_changed = QtCore.Signal(str)
    notify_requested = QtCore.Signal(str, str, str, int)  # level, title, message, timeout_ms

    def set_status(self, text: str) -> None:
        self.status_changed.emit(text)

    def notify(self, level: str, title: str, message: str, timeout_ms: int = 3000) -> None:
        self.notify_requested.emit(level, title, message, timeout_ms)
