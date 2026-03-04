import os
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox

# Links por defecto: (Nombre, URL, Categoria)
LINKS_DEFAULT = [
    ("Manual App Mobile", "https://cdst-ar.github.io/ST/appmobile.html", "App mobile"),
    ("Instructivos contadores/ST", "https://sites.google.com/canaldirecto.com.ar/instructivocontadores/inicio", "Contadores/ST"),
    ("Manuales Impresoras", "https://drive.google.com/drive/folders/0B31B34smQTFBdlQ3U2dLTnFTT2s?resourcekey=0-kmulvtewKYti_qx0P1AQFw", "ST"),
    ("Envios Credifin", "https://docs.google.com/spreadsheets/d/16EGCq4WMBjlkBELUk0y1XKnRGD-XW4BJUxNQQz0lrGg/edit?pli=1&gid=192972919#gid=192972919", "Logistica"),
    # podés sumar más acá:
    # ("Portal CDST", "https://cdst-ar.github.io/", "STC"),
    # ("Guia SIGES", "https://tusitio/guia-siges", "SIGES"),
    # ("Intranet", "https://intranet/", "General"),
]

class LinksTab(ttk.Frame):
    """
    Pestaña reutilizable de Links con:
      - filtro por texto
      - filtro por categoria
      - doble click o Enter para abrir
      - boton copiar URL
    No guarda cambios: los links se pasan por parametro o usa LINKS_DEFAULT.
    """

    def __init__(self, parent, *,
                 default_links=None,
                 pad_in=8,
                 status_var: tk.StringVar | None = None):
        super().__init__(parent, padding=(4, 8))
        self.pad_in = pad_in
        self.status_var = status_var
        self._all_links = list(default_links or LINKS_DEFAULT)

        self._build_ui()
        self._refresh()

    # ---------- UI ----------
    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Filtros arriba
        top = ttk.Frame(self)
        top.grid(row=0, column=0, sticky="ew", padx=self.pad_in, pady=(self.pad_in, 0))
        top.columnconfigure(1, weight=1)

        ttk.Label(top, text="Filtrar").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.var_filter = tk.StringVar()
        ent = ttk.Entry(top, textvariable=self.var_filter)
        ent.grid(row=0, column=1, sticky="ew")

        cats = sorted({c for _, _, c in self._all_links})
        self.var_category = tk.StringVar(value="Todos")
        self.cbo_cat = ttk.Combobox(top,
                                    values=["Todos"] + cats,
                                    textvariable=self.var_category,
                                    state="readonly",
                                    width=12)
        self.cbo_cat.grid(row=0, column=2, sticky="w", padx=(6, 0))

        # Tabla
        cols = ("name", "url", "cat")
        self.tv = ttk.Treeview(self, columns=cols, show="headings", selectmode="browse")
        self.tv.heading("name", text="Nombre")
        self.tv.heading("url",  text="URL")
        self.tv.heading("cat",  text="Categoria")
        self.tv.column("name", width=200, anchor="w")
        self.tv.column("url",  width=240, anchor="w")
        self.tv.column("cat",  width=100, anchor="w")
        self.tv.grid(row=1, column=0, sticky="nsew", padx=self.pad_in, pady=(6, 6))

        # Scrollbar
        vs = ttk.Scrollbar(self, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=vs.set)
        vs.grid(row=1, column=1, sticky="ns", pady=(6, 6))

        # Botonera
        btnbar = ttk.Frame(self)
        btnbar.grid(row=2, column=0, sticky="w", padx=self.pad_in, pady=(0, self.pad_in))
        ttk.Button(btnbar, text="Abrir", command=self._open_selected).pack(side="left", padx=(0, 6))
        ttk.Button(btnbar, text="Copiar URL", command=self._copy_selected).pack(side="left")

        # Eventos
        self.var_filter.trace_add("write", lambda *_: self._refresh())
        self.cbo_cat.bind("<<ComboboxSelected>>", lambda e: self._refresh())
        self.tv.bind("<Double-1>", lambda e: self._open_selected())
        self.tv.bind("<Return>",  lambda e: self._open_selected())

    # ---------- lógica ----------
    def _refresh(self):
        f = (self.var_filter.get() or "").lower().strip()
        cat = self.var_category.get()
        self.tv.delete(*self.tv.get_children())
        for name, url, category in self._all_links:
            if cat != "Todos" and category != cat:
                continue
            if f and (f not in name.lower() and f not in url.lower() and f not in category.lower()):
                continue
            self.tv.insert("", "end", values=(name, url, category))

    def _selected(self):
        sel = self.tv.selection()
        if not sel:
            return None, None
        name, url, _ = self.tv.item(sel[0], "values")
        return name, url

    def _open_selected(self):
        name, url = self._selected()
        if not url:
            return
        try:
            webbrowser.open_new_tab(url)
            if self.status_var is not None:
                self.status_var.set(f"Abrir: {name}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el link:\n{url}\n\n{e}", parent=self)

    def _copy_selected(self):
        name, url = self._selected()
        if not url:
            return
        try:
            # buscamos una ventana raiz para clipboard (Treeview no tiene)
            root = self.winfo_toplevel()
            root.clipboard_clear()
            root.clipboard_append(url)
            if self.status_var is not None:
                self.status_var.set("URL copiada al portapapeles")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo copiar la URL:\n{url}\n\n{e}", parent=self)
