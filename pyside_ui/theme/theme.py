# pyside_ui/theme/theme.py
THEME = {
    "dark": {
        "app_bg": "#121212",        # Más profundo
        "header_bg": "#121212",
        "text": "#F5F5F5",          # Casi blanco
        "muted": "#9CA3AF",         # Gris azulado moderno
        "orange": "#FF9A2E",
        "orange_glow": "rgba(255, 154, 46, 40)",
        "blue": "#6CB6FF",
        "danger": "#E81123",        # Rojo de acción destructiva / cierre

        "surface": "#1E1E1E",       # Base para cards
        "surface_raised": "#252525", # Hover para cards
        "card_bg": "#1A1A1A",
        "card_border": "#2A2A2A",
        "btn_bg": "#2A2A2A",
        "btn_hover": "#333333",

        "seg_bg": "#1A1A1A",
        "seg_unselected": "transparent",
        "seg_hover": "#252525",
        "seg_selected": "#FF9A2E",
        "seg_text": "#9CA3AF",
        "seg_text_selected": "#FFFFFF",

        "pill_bg": "#262626",
        "pill_text": "#F5F5F5",

        "shadow_color": (0, 0, 0, 180),
        "glass_bg": "rgba(30, 30, 30, 160)", # Para efectos de vidrio
    },
    "light": {
        "app_bg": "#F9FAFB",
        "header_bg": "#F9FAFB",
        "text": "#111827",
        "muted": "#6B7280",
        "orange": "#F97316",
        "orange_glow": "rgba(249, 115, 22, 30)",
        "blue": "#2563EB",
        "danger": "#DC2626",        # Rojo de acción destructiva / cierre (modo claro)

        "surface": "#FFFFFF",
        "surface_raised": "#F3F4F6",
        "card_bg": "#FFFFFF",
        "card_border": "#E5E7EB",
        "btn_bg": "#F3F4F6",
        "btn_hover": "#E5E7EB",

        "seg_bg": "#F3F4F6",
        "seg_unselected": "transparent",
        "seg_hover": "#E5E7EB",
        "seg_selected": "#FFFFFF",
        "seg_text": "#6B7280",
        "seg_text_selected": "#111827",

        "pill_bg": "#E5E7EB",
        "pill_text": "#111827",

        "shadow_color": (150, 150, 150, 60),
        "glass_bg": "rgba(255, 255, 255, 180)",
    },
}

# ---------------------------------------------------------------------------
# Constantes de tipografía (puntos). Usar en lugar de valores dispersos.
# ---------------------------------------------------------------------------
FONT_SMALL: float = 9.5    # descripciones, captions
FONT_BASE: float = 10.5    # cuerpo de texto, checkboxes, toasts
FONT_LARGE: float = 11.5   # títulos de card, headers de sección
FONT_ICON: float = 20.0    # labels de ícono

# ---------------------------------------------------------------------------
# Márgenes estándar de tabs (left, top, right, bottom)
# ---------------------------------------------------------------------------
TAB_MARGINS: tuple[int, int, int, int] = (24, 10, 24, 20)
