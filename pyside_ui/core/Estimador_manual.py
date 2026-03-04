import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import math

# ===================== Tema / Estilos (replica del Main) =====================

ORANGE = "#FF7F00"
BLUE   = "#1E90FF"
BG     = "#FFFFFF"
TEXT   = "#333333"

PAD_IN  = 8
PAD_OUT = 8

def install_theme(root: tk.Misc):
    root.configure(bg=BG)
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    # Base
    style.configure("TFrame", background=BG)
    style.configure("TLabel", background=BG, foreground=TEXT)

    # Labels específicos
    style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"), foreground=ORANGE, background=BG)
    style.configure("Sub.TLabel", foreground=BLUE, background=BG)

    # Tarjetas (Labelframe)
    style.configure("Card.TLabelframe", background=BG, relief="groove", borderwidth=1)
    style.configure("Card.TLabelframe.Label", font=("Segoe UI", 10, "bold"), foreground=TEXT, background=BG)

    # Botones grandes
    style.configure("Big.TButton", font=("Segoe UI", 10), padding=(10, 8), background=BG, foreground=TEXT)
    style.map("Big.TButton",
              background=[("active", ORANGE)],
              foreground=[("active", "white")])

    # Notebook por si lo extendés
    style.configure("TNotebook", background=BG, borderwidth=0)
    style.configure("TNotebook.Tab", padding=(10, 5), background=BG)
    style.map("TNotebook.Tab",
              background=[("selected", ORANGE)],
              foreground=[("selected", "white")])

# ===================== Lógica =====================

def dias_360(fecha_inicial: datetime, fecha_final: datetime) -> int:
    """Convención 30/360 simple."""
    di, mi, yi = fecha_inicial.day, fecha_inicial.month, fecha_inicial.year
    df, mf, yf = fecha_final.day,   fecha_final.month,   fecha_final.year
    if di == 31:
        di = 30
    if df == 31 and di >= 30:
        df = 30
    return (yf - yi) * 360 + (mf - mi) * 30 + (df - di)

def parse_fecha_ddmmyyyy(s: str) -> datetime:
    return datetime.strptime(s.strip(), "%d/%m/%Y")

def set_entry_value(entry: ttk.Entry, value: str, readonly=True):
    entry.config(state="normal")
    entry.delete(0, tk.END)
    entry.insert(0, value)
    entry.config(state="readonly" if readonly else "normal")

def calcular_impresiones_mensuales(impresiones_diarias: float) -> float:
    # 30 días estándar para proyección mensual
    return round(impresiones_diarias * 30, 2)

def calcular_resultado_estimacion(contador_final: int, impresiones_diarias: float, dias_estimacion: int):
    delta = impresiones_diarias * dias_estimacion

    if dias_estimacion >= 0:
        contador_estimado = math.ceil(contador_final + delta)
        impresiones_estimadas = math.ceil(delta)
    else:
        contador_estimado = math.floor(contador_final + delta)
        impresiones_estimadas = math.floor(delta)

    return contador_estimado, impresiones_estimadas

# ===================== UI =====================

def _calcular(
    e_ci: ttk.Entry, e_cf: ttk.Entry,
    e_fi: ttk.Entry, e_ff: ttk.Entry, e_fe: ttk.Entry,
    e_id: ttk.Entry, e_dias: ttk.Entry, e_im: ttk.Entry,
    e_ce: ttk.Entry, e_ie: ttk.Entry,
):
    try:
        contador_inicial = int(e_ci.get().strip())
        contador_final   = int(e_cf.get().strip())
    except ValueError:
        messagebox.showerror("Datos inválidos", "Los contadores deben ser números enteros.")
        return

    try:
        fi = parse_fecha_ddmmyyyy(e_fi.get())
        ff = parse_fecha_ddmmyyyy(e_ff.get())
        fe = parse_fecha_ddmmyyyy(e_fe.get())
    except ValueError:
        messagebox.showerror("Fecha inválida", "Usá el formato DD/MM/YYYY en todas las fechas.")
        return

    # Validaciones temporales
    if ff < fi:
        messagebox.showerror("Rango inválido", "La fecha final no puede ser anterior a la inicial.")
        return
    

    ndias = dias_360(fi, ff)
    if ndias <= 0:
        messagebox.showerror("Rango inválido", "El rango de días entre inicial y final debe ser mayor a 0.")
        return

    ndias_est = dias_360(ff, fe)
    impresiones_diarias = round((contador_final - contador_inicial) / ndias, 2)

    # Salidas
    set_entry_value(e_id,   f"{impresiones_diarias}")
    set_entry_value(e_dias, f"{ndias_est}")

    im = calcular_impresiones_mensuales(impresiones_diarias)
    set_entry_value(e_im, f"{im}")

    cont_est, imp_est = calcular_resultado_estimacion(contador_final, impresiones_diarias, ndias_est)
    set_entry_value(e_ce, f"{cont_est}")
    set_entry_value(e_ie, f"{imp_est}")

def crear_interfaz():
    root = tk.Tk()
    root.title("Estimación manual de contadores")
    install_theme(root)

    # Header
    header = ttk.Frame(root)
    header.pack(fill="x", padx=PAD_IN, pady=(PAD_IN, 0))
    ttk.Label(header, text="Estimación manual de contadores", style="Header.TLabel").pack(anchor="w")
    ttk.Label(header, text="Cálculo por 30/360 • Proyección y estimación", style="Sub.TLabel").pack(anchor="w", pady=(2, PAD_OUT))

    # --- Primer contador real ---
    card_ini = ttk.Labelframe(root, text="Primer contador real", style="Card.TLabelframe")
    card_ini.pack(fill="x", padx=PAD_IN, pady=PAD_IN)
    for i in range(2): card_ini.columnconfigure(i, weight=1)

    ttk.Label(card_ini, text="Fecha (DD/MM/YYYY):").grid(row=0, column=0, sticky="w", padx=6, pady=4)
    e_fecha_ini = ttk.Entry(card_ini)
    e_fecha_ini.grid(row=0, column=1, sticky="ew", padx=6, pady=4)

    ttk.Label(card_ini, text="Contador:").grid(row=1, column=0, sticky="w", padx=6, pady=4)
    e_cont_ini = ttk.Entry(card_ini)
    e_cont_ini.grid(row=1, column=1, sticky="ew", padx=6, pady=4)

    # --- Último contador real ---
    card_fin = ttk.Labelframe(root, text="Último contador real", style="Card.TLabelframe")
    card_fin.pack(fill="x", padx=PAD_IN, pady=PAD_IN)
    for i in range(2): card_fin.columnconfigure(i, weight=1)

    ttk.Label(card_fin, text="Fecha (DD/MM/YYYY):").grid(row=0, column=0, sticky="w", padx=6, pady=4)
    e_fecha_fin = ttk.Entry(card_fin)
    e_fecha_fin.grid(row=0, column=1, sticky="ew", padx=6, pady=4)

    ttk.Label(card_fin, text="Contador:").grid(row=1, column=0, sticky="w", padx=6, pady=4)
    e_cont_fin = ttk.Entry(card_fin)
    e_cont_fin.grid(row=1, column=1, sticky="ew", padx=6, pady=4)

    # --- Fecha de proceso / estimación ---
    card_est = ttk.Labelframe(root, text="Fecha de proceso", style="Card.TLabelframe")
    card_est.pack(fill="x", padx=PAD_IN, pady=PAD_IN)
    for i in range(2): card_est.columnconfigure(i, weight=1)

    ttk.Label(card_est, text="Fecha (DD/MM/YYYY):").grid(row=0, column=0, sticky="w", padx=6, pady=4)
    e_fecha_est = ttk.Entry(card_est)
    e_fecha_est.grid(row=0, column=1, sticky="ew", padx=6, pady=4)

    ttk.Label(card_est, text="Días estimación:").grid(row=1, column=0, sticky="w", padx=6, pady=4)
    e_dias_est = ttk.Entry(card_est, state="readonly")
    e_dias_est.grid(row=1, column=1, sticky="ew", padx=6, pady=4)

    # --- Resultados ---
    card_out = ttk.Labelframe(root, text="Resultados", style="Card.TLabelframe")
    card_out.pack(fill="x", padx=PAD_IN, pady=PAD_IN)
    for i in range(2): card_out.columnconfigure(i, weight=1)

    ttk.Label(card_out, text="Impresiones diarias:").grid(row=0, column=0, sticky="w", padx=6, pady=4)
    e_imp_dia = ttk.Entry(card_out, state="readonly")
    e_imp_dia.grid(row=0, column=1, sticky="ew", padx=6, pady=4)

    ttk.Label(card_out, text="Impresiones mensuales:").grid(row=1, column=0, sticky="w", padx=6, pady=4)
    e_imp_mes = ttk.Entry(card_out, state="readonly")
    e_imp_mes.grid(row=1, column=1, sticky="ew", padx=6, pady=4)

    ttk.Label(card_out, text="Contador estimado:").grid(row=2, column=0, sticky="w", padx=6, pady=4)
    e_cont_est = ttk.Entry(card_out, state="readonly")
    e_cont_est.grid(row=2, column=1, sticky="ew", padx=6, pady=4)

    ttk.Label(card_out, text="Impresiones estimadas:").grid(row=3, column=0, sticky="w", padx=6, pady=4)
    e_imp_est = ttk.Entry(card_out, state="readonly")
    e_imp_est.grid(row=3, column=1, sticky="ew", padx=6, pady=4)

    # --- Botón ---
    ttk.Button(
        root, text="Calcular", style="Big.TButton",
        command=lambda: _calcular(
            e_cont_ini, e_cont_fin,
            e_fecha_ini, e_fecha_fin, e_fecha_est,
            e_imp_dia, e_dias_est, e_imp_mes,
            e_cont_est, e_imp_est
        )
    ).pack(fill="x", padx=PAD_IN, pady=(0, PAD_OUT))

    # Prefills: hoy en fechas final y estimación
    hoy = datetime.now().strftime("%d/%m/%Y")
    set_entry_value(e_fecha_fin, hoy, readonly=False)
    set_entry_value(e_fecha_est, hoy, readonly=False)

    # Acceso rápido con Enter en cualquier entry
    for w in (e_cont_ini, e_cont_fin, e_fecha_ini, e_fecha_fin, e_fecha_est):
        w.bind("<Return>", lambda _e: _calcular(
            e_cont_ini, e_cont_fin,
            e_fecha_ini, e_fecha_fin, e_fecha_est,
            e_imp_dia, e_dias_est, e_imp_mes,
            e_cont_est, e_imp_est
        ))

    root.lift()
    root.attributes("-topmost", True)
    def _reassert_topmost(_=None):
        try:
            root.attributes("-topmost", True)
        except tk.TclError:
            pass

        for ev in ("<FocusIn>", "<FocusOut>", "<Map>", "<Unmap>", "<Visibility>"):
            root.bind(ev, _reassert_topmost)
    root.mainloop()

if __name__ == "__main__":
    crear_interfaz = crear_interfaz  # alias por si lo importás desde otro módulo
    crear_interfaz()
