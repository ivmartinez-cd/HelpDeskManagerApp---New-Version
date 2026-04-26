# ip_ranges_txt.py
import os, re, ipaddress

def _find_ipv4(text: str):
    # capta 1.2.3.4, 1.2.3.4/xx, 1.2.3.4:puerto
    cand = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}(?:/\d{1,2})?\b', text)
    out = []
    skipped = []
    for c in cand:
        try:
            ip = ipaddress.IPv4Interface(c).ip if "/" in c else ipaddress.IPv4Address(c)
            out.append(ip)
        except Exception:
            skipped.append(c)
    if skipped:
        import warnings
        warnings.warn(f"Se ignoraron {len(skipped)} IPs/CIDRs inválidos: {skipped[:10]}", stacklevel=2)
    return out

def _net24_key(ip):
    a,b,c,_ = str(ip).split(".")
    return int(a), int(b), int(c)

def _range24(a,b,c):
    return f"{a}.{b}.{c}.1-{a}.{b}.{c}.254"

def generate_ip_ranges_txt(parent=None):
    from tkinter import filedialog, messagebox
    """
    Lee un TXT con IPs, genera rangos /24 (deduplicados y ordenados)
    y los guarda en un TXT (una sola linea separada por comas).
    Retorna (ruta_salida, cantidad_rangos).
    """
    in_path = filedialog.askopenfilename(
        title="Seleccionar TXT con IPs",
        filetypes=[("Archivos de texto", "*.txt")],
        parent=parent
    )
    if not in_path:
        return (None, 0)

    try:
        with open(in_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo leer:\n{in_path}\n\n{e}", parent=parent)
        return (None, 0)

    ips = _find_ipv4(text)
    nets = sorted({ _net24_key(ip) for ip in ips })
    ranges = [ _range24(a,b,c) for (a,b,c) in nets ]

    out_path = filedialog.asksaveasfilename(
        title="Guardar rangos /24",
        initialfile="rangos_ip.txt",
        defaultextension=".txt",
        filetypes=[("Archivos de texto", "*.txt")],
        initialdir=os.path.dirname(in_path),
        parent=parent
    )
    if not out_path:
        return (None, 0)

    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(",".join(ranges))  # cambia a "\n".join(ranges) si los queres uno por linea
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo escribir:\n{out_path}\n\n{e}", parent=parent)
        return (None, 0)

    if ranges:
        messagebox.showinfo("Listo", f"Se generaron {len(ranges)} rango(s) /24.\n{out_path}", parent=parent)
    else:
        messagebox.showinfo("Listo", f"No se encontraron IPv4 validas.\nSe creo archivo vacio:\n{out_path}", parent=parent)

    return (out_path, len(ranges))
