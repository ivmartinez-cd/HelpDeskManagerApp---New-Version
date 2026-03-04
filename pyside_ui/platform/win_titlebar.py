# pyside_ui/platform/win_titlebar.py
from __future__ import annotations

import sys
import ctypes
from ctypes import wintypes


def set_titlebar_dark(hwnd: int, enable_dark: bool) -> bool:
    """
    Activa/Desactiva Immersive Dark Mode en la barra de título nativa (Windows 10/11).

    En algunos builds, DwmSetWindowAttribute NO repinta el non-client area hasta que hay cambio de foco.
    Para forzar refresh inmediato hacemos:
      - DwmSetWindowAttribute (attr 20 y 19)
      - DwmFlush (si existe)
      - SetWindowPos(SWP_FRAMECHANGED)
      - RedrawWindow(RDW_FRAME|RDW_INVALIDATE|RDW_UPDATENOW)
      - SendMessage: WM_NCACTIVATE / WM_NCPAINT / WM_THEMECHANGED / WM_DWMCOMPOSITIONCHANGED
    """
    if sys.platform != "win32":
        return False

    try:
        dwmapi = ctypes.WinDLL("dwmapi")
        user32 = ctypes.WinDLL("user32")
    except Exception:
        return False

    DWMWA_USE_IMMERSIVE_DARK_MODE_19 = 19
    DWMWA_USE_IMMERSIVE_DARK_MODE_20 = 20

    target = 1 if enable_dark else 0
    value = ctypes.c_int(target)

    def _try(attr: int) -> bool:
        res = dwmapi.DwmSetWindowAttribute(
            wintypes.HWND(hwnd),
            ctypes.c_int(attr),
            ctypes.byref(value),
            ctypes.sizeof(value),
        )
        return res == 0

    ok = _try(DWMWA_USE_IMMERSIVE_DARK_MODE_20) or _try(DWMWA_USE_IMMERSIVE_DARK_MODE_19)

    # DwmFlush (no siempre existe)
    try:
        dwmapi.DwmFlush()
    except Exception:
        pass

    # Forzar recálculo y repaint del frame (non-client)
    try:
        SWP_NOSIZE = 0x0001
        SWP_NOMOVE = 0x0002
        SWP_NOZORDER = 0x0004
        SWP_NOACTIVATE = 0x0010
        SWP_FRAMECHANGED = 0x0020

        user32.SetWindowPos.argtypes = [
            wintypes.HWND, wintypes.HWND,
            wintypes.INT, wintypes.INT, wintypes.INT, wintypes.INT,
            wintypes.UINT
        ]
        user32.SetWindowPos.restype = wintypes.BOOL

        user32.SetWindowPos(
            wintypes.HWND(hwnd),
            wintypes.HWND(0),
            0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED
        )

        RDW_INVALIDATE = 0x0001
        RDW_UPDATENOW = 0x0100
        RDW_FRAME = 0x0400

        user32.RedrawWindow.argtypes = [
            wintypes.HWND,
            wintypes.LPCRECT,
            wintypes.HRGN,
            wintypes.UINT
        ]
        user32.RedrawWindow.restype = wintypes.BOOL

        user32.RedrawWindow(
            wintypes.HWND(hwnd),
            None,
            None,
            RDW_FRAME | RDW_INVALIDATE | RDW_UPDATENOW
        )

        # Mensajes non-client: fuerzan a Windows a “tomar” el cambio inmediato
        user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        user32.SendMessageW.restype = wintypes.LRESULT

        WM_NCPAINT = 0x0085
        WM_NCACTIVATE = 0x0086
        WM_THEMECHANGED = 0x031A
        WM_DWMCOMPOSITIONCHANGED = 0x031E

        user32.SendMessageW(wintypes.HWND(hwnd), WM_THEMECHANGED, 0, 0)
        user32.SendMessageW(wintypes.HWND(hwnd), WM_DWMCOMPOSITIONCHANGED, 0, 0)
        user32.SendMessageW(wintypes.HWND(hwnd), WM_NCACTIVATE, 1, 0)
        user32.SendMessageW(wintypes.HWND(hwnd), WM_NCPAINT, 0, 0)

    except Exception:
        # Si falla el forcing, igual devolvemos si el set del atributo funcionó
        pass

    return ok
