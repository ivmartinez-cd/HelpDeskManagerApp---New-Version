# Informe de Auditoría Arquitectónica — HelpDeskManagerApp (PySide6)

**Fecha:** 4 de marzo de 2025  
**Alcance:** Análisis completo del repositorio sin modificación de código.  
**Objetivo:** Documentar la arquitectura actual, el estado de la migración Tkinter → PySide6 y las recomendaciones para un ingeniero senior que se incorpore al proyecto.

---

## 1. Estructura del Proyecto

### Árbol de directorios relevante

```
HelpDeskManagerApp---New-Version/
├── run_pyside_ui.py          # Punto de entrada de la aplicación PySide6
├── audit_repo.py             # Script de auditoría (fuera del runtime)
├── check_imports.py           # Utilidad de verificación de imports
├── collect_repo_context.py   # Utilidad de contexto del repo
├── _context_repo/            # Artefactos generados (all_py.txt, tree.txt, etc.)
│
└── pyside_ui/
    ├── app.py                # QApplication, MainWindow, ícono
    ├── main_window.py        # Ventana principal frameless, tabs, StatusBus, ToastManager
    ├── theme/
    │   ├── __init__.py       # Reexporta THEME
    │   └── theme.py          # Diccionario THEME (dark/light)
    │
    ├── controllers/
    │   ├── contadores_controller.py   # Orquestación: DB3→CSV, En0, Suma fija, Manual, Autoestim, FTP flow
    │   └── ftp_controller.py         # CRUD clientes FTP (agregar/editar/eliminar)
    │
    ├── services/
    │   ├── status_bus.py      # Canal único: status_changed + notify_requested (toasts)
    │   └── ftp_service.py    # Capa sobre core FTP (load_cfg, list_clients, download_*)
    │
    ├── ui/
    │   ├── dialog_kit.py      # BaseProDialog, MessageDialog, ConfirmDialog, warn(), estilos
    │   ├── menubar.py         # Archivo | FTP | Ayuda
    │   ├── ftp_dialogs.py     # ask_add_client, ask_edit_client, ask_delete_client
    │   ├── ftp_client_picker.py  # Diálogo para elegir cliente FTP
    │   ├── db3_csv_params_dialog.py
    │   ├── csven0_params_dialog.py
    │   ├── suma_fija_params_dialog.py
    │   ├── autoestimacion_dialog.py
    │   └── estimador_manual_dialog.py
    │
    ├── tabs/
    │   ├── contadores_tab.py  # Tab Contadores: botones + checkbox FTP, Controllers
    │   ├── stc_tab.py         # Tab STC: botones sin wiring
    │   └── links_tab.py      # Tab Links: filtro, tabla, Abrir/Copiar (demo)
    │
    ├── widgets/
    │   ├── __init__.py       # ThemeIconButton, SegmentedTabs, Card, ModernCheckBox, make_big_button
    │   ├── card.py
    │   ├── controls.py       # make_big_button, update_big_button
    │   ├── effects.py
    │   ├── modern_checkbox.py
    │   ├── segmented_tabs.py
    │   ├── theme_button.py
    │   └── toast.py          # Toast + ToastManager
    │
    ├── platform/
    │   └── win_titlebar.py   # set_titlebar_dark (DWM dark mode) — no referenciado desde la app
    │
    └── core/                  # Lógica de negocio (sin UI o con UI legacy)
        ├── Db3ToCsv.py        # procesar_db_a_csv (SQLite → CSV ancho)
        ├── CsvEn0.py          # filtrar_falta_contador_csv
        ├── Clientes_suma.py  # convertir_xls_a_csv_arcos_headless + legacy con Tk
        ├── Autoestim.py       # ejecutar_generacion_dos_csv (autoestimación)
        ├── ftp_db3.py         # FTP: load_ftp_config, download_db3_*, list_ftp_clients_from_json
        ├── ftp_nas_config.py  # NAS paths, ensure_nas_ftp_config, upsert_client_minimal
        ├── Extraer_ips.py     # Extracción IP desde SQLite (select_files_gui con Tk)
        ├── ip_ranges_txt.py   # generate_ip_ranges_txt (filedialog/messagebox Tk)
        ├── links_tab.py       # Legacy: LinksTab Tkinter (ttk.Frame, LINKS_DEFAULT)
        └── Estimador_manual.py # Lógica 30/360 + ventana Tk (messagebox); lógica reutilizada en PySide6
```

### Explicación de carpetas principales

| Carpeta | Rol |
|--------|-----|
| **pyside_ui/** | Raíz del código de la aplicación PySide6. Contiene UI, controladores, servicios y referencias a core. |
| **controllers/** | Orquestación: reciben eventos de la UI, llaman a core y a diálogos, usan `status_cb`/`notify_cb`. No contienen lógica de negocio pesada. |
| **services/** | Abstracción sobre infra (FTP, bus de estado). FtpService delega en `core.ftp_db3` y `core.ftp_nas_config`. |
| **ui/** | Diálogos y menú. Todos los diálogos que se usan desde controllers heredan de `BaseProDialog` (dialog_kit). |
| **tabs/** | Pestañas del QStackedWidget: Contadores (con controllers), STC (sin wiring), Links (demo estático). |
| **widgets/** | Componentes reutilizables (Card, botones, tabs, checkbox, toast). Sin lógica de negocio. |
| **theme/** | Paleta dark/light (THEME) usada por main_window y por diálogos vía `get_theme(parent)`. |
| **platform/** | Código específico de plataforma (p. ej. Windows DWM). No está integrado en el flujo actual. |
| **core/** | Lógica de negocio: DB↔CSV, FTP, IP, estimaciones. Algunos módulos aún usan Tkinter para GUI o file dialogs. |

---

## 2. Visión general de la arquitectura

### Patrón utilizado

- **MVC-like desacoplado**: la UI solo presenta y delega; los controladores orquestan; el core contiene reglas de negocio.
- **Comunicación**:
  - **UI → Controller:** señales de botones/menú conectadas a métodos del controller.
  - **Controller → Core:** llamadas directas a funciones en `pyside_ui.core.*`.
  - **Controller → UI (feedback):** `status_cb` (texto en barra de estado) y `notify_cb` (toasts). Los callbacks los proporciona la capa UI (tab o ventana) y se inyectan en el controller.

### Flujo entre capas

1. **MainWindow** crea un **StatusBus** y un **ToastManager**; el bus emite `status_changed` y `notify_requested`.
2. **ContadoresTab** recibe `status_bus`, crea **ContadoresController** y **FtpController** inyectando `status_cb` (→ `status_bus.set_status`) y `notify_cb` (→ `status_bus.notify`).
3. Los botones del tab están conectados a métodos del controller (p. ej. `procesar_db3_a_csv`, `abrir_estimador_manual`).
4. El controller abre diálogos (params, picker FTP, etc.), llama a core y al finalizar usa `_notify`/`_status_cb` para actualizar estado y toasts.
5. El **menú FTP** usa `win.ftp_controller` (expuesto por ContadoresTab en `_expose_ftp_controller_to_window` vía `QTimer.singleShot(0, ...)`).

### Reglas arquitectónicas respetadas en el diseño

- UI sin lógica de negocio: tabs y diálogos solo muestran y delegan.
- Controllers como orquestadores: deciden qué diálogo abrir, qué función de core llamar y cómo notificar.
- Core con lógica reutilizable; en varios módulos existe una variante “headless” o pura para uso desde PySide6.
- Notificaciones vía `notify_cb` (toasts), no QMessageBox; avisos modales con `dialog_kit.warn()` o `ConfirmDialog`.
- Diálogos basados en **BaseProDialog** (dialog_kit) con título, barra de arrastre y estilos unificados.

---

## 3. Estado de la migración

### Migrados a PySide6

- **Punto de entrada:** `run_pyside_ui.py` → `pyside_ui.app.main()`.
- **Ventana principal:** `main_window.py` (frameless, titlebar propio, SegmentedTabs, stack de tabs).
- **Tabs:** `ContadoresTab`, `STCTab`, `LinksTab` (versiones en `pyside_ui/tabs/`).
- **Contadores:** flujo completo vía ContadoresController: DB3→CSV, En0, Suma fija, Estimador manual, Autoestimación, descarga FTP + DB3→CSV.
- **FTP:** menú y CRUD de clientes vía FtpController y FtpService; diálogos en `ftp_dialogs.py` y `ftp_client_picker.py`.
- **Diálogos de parámetros:** DB3→CSV, CsvEn0, Suma fija, Autoestimación, Estimador manual (todos BaseProDialog).
- **Servicios/UI compartida:** StatusBus, ToastManager, dialog_kit, theme, widgets (Card, botones, tabs, checkbox).

### Todavía en Tkinter o con dependencias Tk

- **core/links_tab.py:** `LinksTab` como `ttk.Frame`, Treeview, messagebox, webbrowser. **No es usado por la app PySide6** (la app usa `tabs/links_tab.py`).
- **core/Estimador_manual.py:** ventana y estilos Tk + `messagebox` para validación; la **lógica** (días 30/360, cálculos) se reutiliza en `ui/estimador_manual_dialog.py` (PySide6).
- **core/Clientes_suma.py:** `convertir_xls_a_csv_arcos()` usa `filedialog`, `simpledialog`, `messagebox`. La app PySide6 solo usa `convertir_xls_a_csv_arcos_headless()`.
- **core/Extraer_ips.py:** `select_files_gui()` crea un `tk.Tk()` temporal y usa `filedialog`; el resto es lógica pura.
- **core/ip_ranges_txt.py:** `generate_ip_ranges_txt()` usa `filedialog` y `messagebox` (Tk).

### Zonas híbridas

- **Core:** varios módulos tienen dos “modos”: una API headless/sin UI usada por PySide6 y otra con Tk (file dialogs/messagebox) para uso legacy o script.
- **Tab STC:** UI PySide6 (botones “db3 a Direc. IP” y “txt a Direc. IP”) pero **sin wiring**: no hay controller ni llamadas a `Extraer_ips` ni `ip_ranges_txt`.
- **Tab Links:** datos demo en código; botones Abrir/Copiar no conectados a lógica (sin controller ni uso de `core.links_tab`).

---

## 4. Controladores

### ContadoresController (`controllers/contadores_controller.py`)

- **Responsabilidades:**
  - Procesar DB3 → CSV (archivos locales o vía flujo FTP).
  - Estimación en 0 (CsvEn0): parámetros vía diálogo, luego `CsvEn0.filtrar_falta_contador_csv`.
  - Suma fija: parámetros vía diálogo, luego `Clientes_suma.convertir_xls_a_csv_arcos_headless`.
  - Abrir ventana del Estimador manual (siempre encima, no modal).
  - Autoestimación: diálogo de parámetros y `Autoestim.ejecutar_generacion_dos_csv`.
  - Flujo FTP: cargar config, elegir cliente (FtpClientPickerDialog), carpeta destino, descarga con FtpService y luego DB3→CSV.
- **Usado por:** `ContadoresTab` (botones Procesar DB3→CSV, En0, Suma fija, Estimador manual, Autoestimación; checkbox FTP).
- **Callbacks:** `status_cb`, `notify_cb`, `uncheck_ftp_cb`; obtiene tema vía `_get_theme()` desde la ventana.

### FtpController (`controllers/ftp_controller.py`)

- **Responsabilidades:** Agregar, editar y eliminar clientes FTP. Usa FtpService para persistencia y diálogos de `ui/ftp_dialogs` y `ui/ftp_client_picker`.
- **Usado por:** menú “FTP” de la barra de menú (MainWindow). El controller se expone como `win.ftp_controller` desde ContadoresTab.
- **Callbacks:** `status_cb`, `notify_cb`.

### Resumen

- No existe un controller dedicado para la pestaña STC ni para Links; la lógica de STC (Extraer_ips, ip_ranges_txt) y la de Links (abrir/copiar, filtros) seguiría en core y se conectaría desde nuevos controllers o desde los tabs con un controller mínimo.

---

## 5. Módulos de UI

### Tabs (contenido del QStackedWidget)

| Módulo | Descripción |
|--------|-------------|
| **ContadoresTab** | Card con botones de operaciones y checkbox “Descargar DB3 desde FTP”. Crea y conecta ContadoresController y FtpController. |
| **STCTab** | Card con dos botones (“db3 a Direc. IP”, “txt a Direc. IP”). Sin señales conectadas. |
| **LinksTab** | Card con filtro, QComboBox “Todos”, QTableWidget (Nombre/URL), botones Abrir y Copiar. Datos demo en `_seed_demo()`; sin controller. |

### Diálogos (todos heredan de BaseProDialog en dialog_kit)

| Módulo | Uso |
|--------|-----|
| **ftp_dialogs** | ask_add_client, ask_edit_client, ask_delete_client (FtpCreds / selección de cliente). |
| **ftp_client_picker** | FtpClientPickerDialog para elegir cliente FTP (lista + búsqueda). |
| **db3_csv_params_dialog** | Parámetros DB3→CSV (fecha, nombre base, carpeta). |
| **csven0_params_dialog** | Parámetros Estimación en 0 (CSV entrada, fecha, cliente, carpeta, delimitador). |
| **suma_fija_params_dialog** | Parámetros Suma fija (archivos XLS, carpeta, fecha, hojas). |
| **autoestimacion_dialog** | CSV detalle y fecha para autoestimación. |
| **estimador_manual_dialog** | Ventana no modal, always-on-top: entradas y resultados de estimación manual (lógica 30/360 en el mismo archivo). |

### Widgets reutilizables

| Widget | Descripción |
|--------|-------------|
| **Card** | Contenedor con título y grid para botones/contenido. |
| **SegmentedTabs** | Pestañas segmentadas (Contadores / STC / Links). |
| **ThemeIconButton** | Botón de tema claro/oscuro (toggled). |
| **ModernCheckBox** | Checkbox estilizado. |
| **make_big_button / update_big_button** | Botones grandes de acciones en cards. |
| **Toast / ToastManager** | Notificaciones tipo toast; ToastManager conectado a `StatusBus.notify_requested`. |

### Sistema de layout y diálogos

- **dialog_kit:** BaseProDialog (frameless, draggable, ProTitleBar), MessageDialog, ConfirmDialog, `warn()`, `apply_dialog_style()`, `resolve_theme()`, helpers (make_subtitle, make_card, make_button_row).
- **theme:** THEME dark/light aplicado en main_window y en diálogos vía `get_theme(parent)` o theme explícito pasado por el controller.

---

## 6. Módulos Core (lógica de negocio)

| Módulo | Propósito |
|--------|-----------|
| **Db3ToCsv** | Lectura de SQLite (counters), reglas TIPO/CLASE, export a CSV ancho (SERIE, FECHA, TIPO, CLASE_10/20, etc.). |
| **CsvEn0** | Filtrado de filas “FALTA CONTADOR” en CSV y generación de nuevo CSV con fecha y nombre cliente. |
| **Clientes_suma** | Lectura de Excel, transformación a formato CSV (suma fija). API headless usada por PySide6; versión con Tk para legacy. |
| **Autoestim** | Carga CSV detalle, filtros y transformaciones, generación de dos CSV (import_autoestim y formato 14/10/20). |
| **ftp_db3** | Conexión FTP, listado/descarga de DB3, merge opcional; uso de `ftplib.FTP`. |
| **ftp_nas_config** | Rutas NAS (HelpDeskManagerApp, ftp_clientes.json), lectura/escritura JSON, upsert de cliente. |
| **Extraer_ips** | Detección de archivos SQLite, extracción de IP desde tabla counters, deduplicación /24, salida en texto. Incluye `select_files_gui` con Tk. |
| **ip_ranges_txt** | Lectura de TXT con IPs, generación de rangos /24 en una línea; usa filedialog/messagebox Tk. |
| **Estimador_manual** | Cálculos 30/360 y proyección; ventana Tk con messagebox. La lógica se reutiliza en estimador_manual_dialog (PySide6). |
| **links_tab** (core) | Implementación Tk de la pestaña Links (Treeview, LINKS_DEFAULT). No referenciada por la app PySide6. |

---

## 7. Sistemas externos e integraciones

- **FTP:** `ftplib.FTP` en `core.ftp_db3`; configuración en JSON en NAS (`ftp_nas_config.NAS_FTP_CONFIG`). FtpService y FtpController encapsulan el uso.
- **Archivos / NAS:** rutas en `\\\\nas1\\nsi\\Programas\\HelpDeskManagerApp` y subcarpeta `config`; lectura/escritura de JSON y de archivos locales.
- **CSV:** pandas y/o escritura manual; encoding UTF-8, separadores configurables (coma/punto y coma).
- **Excel:** `pandas.read_excel` en Clientes_suma y en Autoestim.
- **SQLite:** `sqlite3` en Db3ToCsv, Extraer_ips y ftp_db3 (validación de DB).
- **Red:** solo FTP; no hay otros clientes HTTP/APIs documentados en el análisis.
- **OCR:** no detectado en el repositorio.
- **Portapapeles / Navegador:** el tab Links (Tk) usa `webbrowser` y clipboard; la versión PySide6 del tab no tiene aún la lógica de abrir/copiar conectada.

---

## 8. Ejemplo de flujo de eventos

**Caso: usuario hace clic en “Procesar DB3 → CSV” con “Descargar DB3 desde FTP” marcado.**

1. **UI:** `ContadoresTab.btn_db3.clicked` emite.
2. **Tab:** La lambda llama a `self._controller.procesar_db3_a_csv(use_ftp=True)`.
3. **Controller:** `procesar_db3_a_csv(True)` llama a `_run_ftp_flow_steps()`.
4. **Controller:** Carga config con `_ftp.load_cfg()` (FtpService) → core `load_ftp_config` / `ensure_nas_ftp_config`.
5. **Controller:** Lista clientes con `_ftp.list_clients(cfg_path)`.
6. **Controller:** Abre `FtpClientPickerDialog` (dialog_kit); usuario elige cliente y acepta.
7. **Controller:** Pide carpeta con `QFileDialog.getExistingDirectory`, luego `_notify("info", "FTP", "Conectando…")` y programa con `QTimer.singleShot` el paso asíncrono.
8. **Controller:** En el paso diferido llama a `_ftp.download_many_db3()` (FtpService) → core `download_db3_many_from_ftp`; al terminar llama a `_run_db3_to_csv_flow([local_path], ...)`.
9. **Controller:** Abre `ask_db3_csv_params(...)` con valores por defecto; usuario confirma.
10. **Controller:** Llama a `procesar_db_a_csv` (core Db3ToCsv) con los parámetros.
11. **Controller:** `_status_cb("")` y `_notify("success", "Contadores", "CSV generado correctamente.", 4000)`.
12. **UI:** `status_cb` está conectado a `StatusBus.set_status` → el label de estado se actualiza (o se oculta si está vacío).
13. **UI:** `notify_cb` está conectado a `StatusBus.notify` → `notify_requested.emit` → ToastManager muestra el toast de éxito.

En todo el flujo, la UI solo reacciona a callbacks/signals; el controller no conoce widgets concretos más allá del parent para diálogos.

---

## 9. Deuda técnica y riesgos

### Lógica en UI

- **Estimador manual:** `estimador_manual_dialog.py` contiene tanto la lógica de cálculo (días 30/360, proyección) como la UI. Sería preferible mover las funciones puras a un módulo core y dejar el diálogo solo como presentación.
- **LinksTab (tabs):** `_seed_demo()` y estilos están en el tab; cuando se conecte la funcionalidad, conviene que la fuente de datos y la lógica de filtrado/abrir/copiar estén en core o en un controller.

### Acoplamiento y contratos

- **FtpController en MainWindow:** El menú FTP depende de que ContadoresTab haya asignado `win.ftp_controller` en un timer. Cualquier cambio en el orden de creación de tabs o en la pestaña por defecto podría dejar el menú sin controller.
- **Contrato ask_db3_csv_params:** El controller llama a `ask_db3_csv_params(parent, default_fecha=..., default_nombre_base=..., default_carpeta=..., theme=...)`, pero la función y `Db3CsvParamsDialog` actuales solo aceptan `parent` y `default_out_dir`. Es un **error de contrato**: en tiempo de ejecución se produciría `TypeError` por argumentos inesperados, a menos que exista otra versión del diálogo o que se use `**kwargs`. Debe alinearse la firma del diálogo con la del controller (aceptar y usar los defaults y el theme).

### Restos de Tkinter

- **Core con Tk:** `core/links_tab.py`, `core/Estimador_manual.py` (ventana + messagebox), `core/Clientes_suma.py` (convertir_xls_a_csv_arcos con dialogs), `core/Extraer_ips.py` (select_files_gui), `core/ip_ranges_txt.py` (filedialog/messagebox). Para una migración completa, las rutas que usa PySide6 deberían usar solo APIs headless o recibir rutas/opciones desde la UI PySide6 (p. ej. QFileDialog en controller).
- **Dependencia implícita:** Si en el futuro se ejecuta algún script que importe `core.ip_ranges_txt` o `core.Clientes_suma` y llame a las funciones con UI Tk, seguirá existiendo dependencia de Tkinter.

### Riesgos concretos

- **STC sin wiring:** Los botones del tab STC no hacen nada; la funcionalidad de Extraer_ips e ip_ranges_txt no está expuesta en la app.
- **Links sin datos reales:** El tab Links no usa `core.links_tab.LINKS_DEFAULT` ni persistencia; Abrir/Copiar no están conectados.
- **platform/win_titlebar:** No está integrado; si se quisiera barra de título nativa oscura en Windows, habría que conectar `set_titlebar_dark` con el HWND de la ventana.
- **apply_dialog_style(self)** en `Db3CsvParamsDialog`: Se llama sin pasar `theme`; en otros diálogos se usa `apply_dialog_style(self, theme)`. Inconsistencia y posible tema incorrecto si el padre no tiene `theme`.

---

## 10. Recomendaciones para completar la migración

1. **Unificar contrato de parámetros DB3→CSV:** Extender `ask_db3_csv_params` y `Db3CsvParamsDialog` para aceptar `default_fecha`, `default_nombre_base`, `default_carpeta` y `theme`, y prellenar los campos y estilos. Eliminar el riesgo de TypeError y mejorar UX con valores por defecto.
2. **Extraer lógica del Estimador manual:** Mover `dias_360`, `calcular_resultado_estimacion`, etc. a un módulo `core/estimador_manual.py` (o similar) y que el diálogo PySide6 solo llame a esas funciones y muestre resultados.
3. **Conectar tab STC:** Crear un `STCController` (o ampliar un controller existente) que reciba rutas/opciones desde diálogos PySide6 (QFileDialog) y llame a `Extraer_ips` e `ip_ranges_txt` con APIs que no usen Tk (o añadir wrappers headless que reciban rutas). Conectar los botones del tab a ese controller.
4. **Conectar tab Links:** Definir fuente de datos (archivo, LINKS_DEFAULT, o config) y lógica de filtrado/abrir/copiar en core o en un LinksController; conectar botones y filtros del tab a esa lógica usando `status_cb`/`notify_cb` y sin messagebox.
5. **Reducir Tk en core:** Para cada módulo core que aún use Tk:
   - Mantener o crear API que reciba rutas/opciones (headless).
   - Reemplazar llamadas desde la app PySide6 por flujos que usen QFileDialog/QMessageBox equivalentes en controller/dialog_kit.
   - Opcional: marcar como deprecadas las funciones que usan Tk y migrar scripts que las usen.
6. **Diálogos y tema:** Pasar siempre `theme` a `apply_dialog_style` en todos los diálogos que lo soporten y unificar la obtención del tema (p. ej. siempre desde parent o siempre por parámetro).
7. **Documentar dependencias:** Añadir `requirements.txt` o `pyproject.toml` con PySide6 y pandas (y otras dependencias detectadas) para facilitar onboarding y entornos reproducibles.

---

## Safe Next Steps

Tareas sugeridas para los próximos pasos, con bajo riesgo y sin refactors estructurales grandes:

1. **Corregir contrato DB3→CSV:** En `db3_csv_params_dialog.py`, ampliar la firma de `ask_db3_csv_params` y del constructor de `Db3CsvParamsDialog` para aceptar `default_fecha`, `default_nombre_base`, `default_carpeta` y `theme`; prellenar los campos y llamar a `apply_dialog_style(self, theme)` cuando se pase theme. Verificar que el flujo “Procesar DB3 → CSV” (local y vía FTP) funcione correctamente.
2. **Wiring mínimo del tab STC:** Sin cambiar nombres de módulos ni APIs de core, crear un controller mínimo (o métodos en un controller existente) que:
   - Para “db3 a Direc. IP”: abra QFileDialog para elegir archivo(s), llame a la API headless de Extraer_ips (si existe) o a la que devuelva rutas sin abrir Tk, y muestre resultado vía `notify_cb`/`status_cb`.
   - Para “txt a Direc. IP”: abra QFileDialog para el TXT de entrada y para guardar salida, llame a la lógica de `ip_ranges_txt` con esas rutas (o añadir una función headless que reciba rutas y no use filedialog/messagebox).
3. **Tab Links – Abrir y Copiar:** En `tabs/links_tab.py`, conectar los botones Abrir y Copiar a lógica que use la fila seleccionada de la tabla: abrir URL con `webbrowser.open` y copiar URL al portapapeles (QApplication.clipboard). Mostrar feedback con `status_cb` o `notify_cb`. Mantener datos demo hasta que se defina fuente de datos real.
4. **Extraer lógica del Estimador manual:** Crear `core/estimador_manual.py` con las funciones puras (días 30/360, cálculos) y hacer que `ui/estimador_manual_dialog.py` las importe y solo maneje UI y validación con `warn()`.
5. **Requirements:** Añadir `requirements.txt` (o dependencias en `pyproject.toml`) con `PySide6` y `pandas` (y `openpyxl` si se usa para Excel), y documentar en README cómo crear el entorno e iniciar la app con `run_pyside_ui.py`.

Con esto se avanza en migración, se corrige un bug de contrato y se mantienen cambios incrementales y reversibles, sin tocar nombres de modelos ni contratos de API existentes más allá de la extensión acordada del diálogo DB3→CSV.
