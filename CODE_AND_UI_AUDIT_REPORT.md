# Informe de auditoría de código y UI — HelpDeskManagerApp (PySide6)

**Fecha:** 4 de marzo de 2025  
**Alcance:** Análisis completo del repositorio sin modificación de código.  
**Referencias:** ARCHITECTURE_AUDIT_REPORT.md, ARCHITECTURE_RULES.md.

---

## 1. Resumen ejecutivo

La aplicación mantiene una arquitectura MVC-like clara: la UI delega en controladores, los controladores orquestan y llaman a core/servicios, y el feedback se canaliza por `status_cb`/`notify_cb`. La migración a PySide6 está avanzada en Contadores y FTP; los tabs STC y Links siguen sin controlador y con funcionalidad limitada.

**Estado general:** Aceptable para producción en el flujo Contadores + FTP, con deuda técnica y algunos riesgos acotados.

**Hallazgos principales:**
- No se detectan violaciones graves de arquitectura en la UI activa (tabs/diálogos que llaman a controladores).
- Hay lógica de negocio dentro de un diálogo (Estimador manual) y un posible KeyError en Card con tema vacío.
- STC y Links carecen de controlador; los botones de Links no están conectados.
- Varios módulos core siguen usando Tkinter (filedialog/messagebox) en APIs no usadas por PySide6.
- El punto de entrada no propaga el código de salida de la aplicación.

---

## 2. Problemas críticos (deben corregirse)

### 2.1 Posible KeyError en Card cuando el tema está vacío

**Archivo:** `pyside_ui/widgets/card.py`  
**Líneas:** 55-58, 63-64, 72-73  

En `set_theme(self, theme: dict)` se hace `self._theme = theme or {}` pero luego se usan `self._theme["card_bg"]`, `self._theme["card_border"]` y `self._theme['text']` sin `.get()`. Si por error se llama con `theme={}` o un dict sin esas claves, se lanza **KeyError**.

**Impacto:** Bajo en la práctica (MainWindow siempre pasa THEME[theme_name]), pero el widget no es defensivo.

**Recomendación:** Usar `self._theme.get("card_bg", "<fallback>")` y análogos, o validar que el tema tenga las claves mínimas.

---

### 2.2 Conexión duplicada en EstimadorManualDialog

**Archivo:** `pyside_ui/ui/estimador_manual_dialog.py`  
**Líneas:** 227 y 231  

`btn_calc.clicked.connect(self._on_calcular)` se ejecuta dos veces. Cada clic en "Calcular" dispararía `_on_calcular` dos veces.

**Impacto:** Medio: doble ejecución del cálculo y posible parpadeo o comportamiento confuso.

**Recomendación:** Eliminar una de las dos líneas.

---

### 2.3 Código de salida no propagado en el entrypoint

**Archivo:** `run_pyside_ui.py`  

Se llama a `main()` pero no se usa su valor de retorno (`app.exec()`). El proceso termina siempre con código 0 aunque la aplicación cierre con error.

**Recomendación:** Usar `sys.exit(main())` o `raise SystemExit(main())` para propagar el código de salida.

---

## 3. Problemas de lógica

### 3.1 Flujo FTP: delay fijo antes de abrir diálogo DB3→CSV

**Archivo:** `pyside_ui/controllers/contadores_controller.py`  
**Líneas:** 302-306  

Tras la descarga FTP exitosa se muestra un toast y se programa `_run_db3_to_csv_flow` con `QTimer.singleShot(3500, ...)`. El diálogo de parámetros DB3→CSV se abre 3,5 segundos después. Si el usuario cierra el toast antes, puede no entender por qué aparece el diálogo más tarde.

**Recomendación:** Reducir el delay o abrir el flujo DB3→CSV de forma inmediata (o con un delay mucho menor) y mantener el toast solo informativo.

---

### 3.2 ContadoresController: procesar_db3_a_csv(False) no devuelve el resultado del flujo

**Archivo:** `pyside_ui/controllers/contadores_controller.py`  
**Líneas:** 121-136  

`procesar_db3_a_csv(use_ftp=False)` llama a `_run_db3_to_csv_flow(...)` pero no retorna su valor; solo hace `return True` después. `_run_db3_to_csv_flow` puede devolver `False` (usuario cancela o error). En ese caso el controller igual retorna `True`.

**Impacto:** Bajo: la UI no depende del retorno, pero la semántica es incorrecta.

**Recomendación:** Hacer `return self._run_db3_to_csv_flow(...)` y mantener `return True` solo cuando el flujo sea exitoso.

---

### 3.3 FtpClientPickerDialog: tema solo aplicado cuando se pasa explícitamente

**Archivo:** `pyside_ui/ui/ftp_client_picker.py`  
**Líneas:** 30-32  

Si el controller no pasa `theme`, solo se aplica el estilo que BaseProDialog obtiene de `get_theme(parent)` en su propio `__init__`. No se llama a `apply_dialog_style` en el FtpClientPickerDialog. En la práctica el controller siempre pasa theme, pero si en el futuro se abre sin theme y con parent que no tenga ventana con `theme`, el diálogo podría verse sin tematizar.

**Recomendación:** Alinear con otros diálogos: si no hay theme, llamar a `apply_dialog_style(self, get_theme(parent))` para no depender solo del padre.

---

### 3.4 CsvEn0ParamsDialog: sin default para “Nombre cliente”

El controller guarda `_last_en0_cliente` pero no lo pasa al diálogo. El diálogo no tiene parámetro `default_nombre_cliente`, por lo que el campo “Nombre cliente” no se prellena con el último valor.

**Recomendación:** Añadir `default_nombre_cliente` al diálogo y que el controller lo pase para mejorar la UX.

---

## 4. UI / UX

### 4.1 LinksTab: botones “Abrir” y “Copiar URL” sin conectar

**Archivo:** `pyside_ui/tabs/links_tab.py`  

Los botones no tienen `clicked.connect(...)`. No hacen nada. La tabla se rellena con datos demo en `_seed_demo()`.

**Recomendación:** Conectar a un controller (o a slots del tab que deleguen en un controller) para abrir URL en el navegador y copiar URL al portapapeles, con feedback vía status_cb/notify_cb.

---

### 4.2 STCTab: botones sin wiring

**Archivo:** `pyside_ui/tabs/stc_tab.py`  

“db3 a Direc. IP” y “txt a Direc. IP” no están conectados a ninguna acción. La funcionalidad de `Extraer_ips` e `ip_ranges_txt` no está expuesta en la UI.

**Recomendación:** Introducir un STCController (o ampliar un controller existente) que use QFileDialog y llame a la lógica headless de core, y conectar los botones a ese controller.

---

### 4.3 EstimadorManualDialog: estilos hardcodeados en _group_box

**Archivo:** `pyside_ui/ui/estimador_manual_dialog.py`  
**Líneas:** 133-143  

`_group_box` aplica colores fijos (`rgba(255,255,255,0.92)`). No usa el dict de tema. En tema claro el contraste puede ser malo.

**Recomendación:** Recibir el tema en el diálogo y usar `theme.get("text", ...)` (y muted/orange si aplica) para QGroupBox y títulos.

---

### 4.4 Toast: colores fijos

**Archivo:** `pyside_ui/widgets/toast.py`  
**Líneas:** 15-21, 26-30  

Los colores de nivel (success, warning, error, info) y el texto (“white”, “#eee”) están hardcodeados. No respetan el tema de la aplicación.

**Recomendación:** Pasar el tema al Toast (o al ToastManager) y derivar colores de nivel y texto desde el tema para mantener coherencia con el resto de la UI.

---

### 4.5 Inconsistencia en contenedores de “file picker” en diálogos

- **db3_csv_params_dialog:** Contenedor “Carpeta salida” con estilo desde tema (FolderPickerWrap con panel_bg, border, border-radius).
- **csven0_params_dialog, suma_fija_params_dialog, autoestimacion_dialog:** Usan `RowWrapTransparent` con `background: transparent`.

En temas con fondo no uniforme, los wrappers transparentes pueden verse distintos al de DB3. No es un bug grave pero rompe la consistencia visual.

**Recomendación:** Unificar: o bien todos usan contenedor estilizado (como DB3) o todos transparente, y documentar el criterio en ARCHITECTURE_RULES o en el dialog_kit.

---

### 4.6 Changelog y “Iniciar con Windows” sin implementar

**Archivo:** `pyside_ui/ui/menubar.py` — Changelog llama a `on_noop`.  
**Archivo:** `pyside_ui/main_window.py` — Checkbox “Iniciar con Windows” no tiene lógica ni persistencia.

**Recomendación:** Si son placeholders, dejarlo documentado; si son requeridos, implementar (Changelog: diálogo o enlace; Iniciar con Windows: persistencia y registro en el SO si aplica).

---

## 5. Riesgos de rendimiento

### 5.1 Operaciones de archivo en el hilo de UI

Todas las llamadas a core (procesar_db_a_csv, filtrar_falta_contador_csv, convertir_xls_a_csv_arcos_headless, ejecutar_generacion_dos_csv, download_many_db3) se ejecutan en el hilo de la UI. Con archivos grandes o muchas filas, la ventana puede bloquearse.

**Recomendación:** Para operaciones largas, mover el trabajo a QThread (o threading) y usar señales para actualizar estado y notificaciones. Mantener el contrato status_cb/notify_cb desde el hilo de UI vía señales.

---

### 5.2 Descarga FTP en el hilo de UI

**Archivo:** `pyside_ui/controllers/contadores_controller.py` — `_ftp_step_download` llama a `_ftp.download_many_db3()` de forma síncrona. La descarga bloquea la UI.

**Recomendación:** Ejecutar la descarga en un worker (QThread o ThreadPool) y notificar fin/error por señal para actualizar toasts y siguiente paso desde el main thread.

---

## 6. Cumplimiento de arquitectura

### 6.1 Respeto de ARCHITECTURE_RULES.md

- **UI → Controller → Core:** Respetado en ContadoresTab y en el menú FTP. STC y Links no tienen controller.
- **Sin core desde UI:** Tabs y diálogos no importan ni llaman a core; solo ContadoresTab instancia servicios/controladores.
- **status_cb / notify_cb:** ContadoresController y FtpController reciben y usan correctamente los callbacks; el tab los implementa delegando en StatusBus.
- **Diálogos BaseProDialog:** Todos los diálogos modales de params/pickers heredan de BaseProDialog y usan dialog_kit.
- **Sin QMessageBox para resultados:** No se usa QMessageBox para éxito/error de operaciones; se usa notify_cb. En diálogos se usa `warn()` para validación.

### 6.2 Violación: lógica de negocio en UI

**Archivo:** `pyside_ui/ui/estimador_manual_dialog.py`  

Las funciones `dias_360`, `parse_fecha_ddmmyyyy`, `calcular_impresiones_mensuales`, `calcular_resultado_estimacion` son lógica de dominio y viven en el mismo módulo que el diálogo. Según ARCHITECTURE_RULES, esa lógica debería estar en core y el diálogo solo presentar y delegar.

**Recomendación:** Mover esas funciones a un módulo `pyside_ui/core/estimador_manual.py` (o similar) y que el diálogo solo las importe y muestre resultados.

### 6.3 Core con Tkinter

Módulos que aún usan Tk en parte de su API (no en la ruta usada por PySide6):

- **core/Clientes_suma.py:** `convertir_xls_a_csv_arcos()` usa filedialog, simpledialog, messagebox. La app usa solo `convertir_xls_a_csv_arcos_headless`.
- **core/ip_ranges_txt.py:** `generate_ip_ranges_txt()` usa filedialog y messagebox.
- **core/Extraer_ips.py:** `select_files_gui()` crea un Tk() temporal y filedialog.
- **core/Estimador_manual.py:** Ventana Tk y messagebox (la app PySide6 usa el diálogo en ui/).
- **core/links_tab.py:** LinksTab Tkinter; no referenciado por la app PySide6.

No hay violación en la ruta que usa la app (siempre se usan APIs headless o el controller no llama a las funciones con Tk). Sí hay deuda de migración y riesgo si alguien llama esas APIs con Tk desde otro entrypoint.

---

## 7. Calidad de código

### 7.1 Duplicación

- **Patrón “file picker row”:** Varios diálogos (db3_csv_params, csven0_params, suma_fija_params, autoestimacion_dialog) repiten la estructura: QLineEdit + QPushButton “Elegir…” en un layout horizontal, a veces con wrapper. El estilo del wrapper no es uniforme (estilizado vs transparent).
- **Obtención de tema en controladores:** `_get_theme()` en ContadoresController repite la lógica de obtener theme desde la ventana; FtpController no tiene _get_theme pero los diálogos FTP reciben theme desde el controller que sí lo tiene. Aceptable, pero se podría extraer un helper compartido.

### 7.2 Naming y ubicación

- **core/links_tab.py:** Es la implementación Tk de la pestaña Links; el nombre sugiere “lógica de links” pero en realidad es UI Tk. Puede inducir a error. Mejor nombre sería `links_tab_tk.py` o moverlo a un paquete legacy.
- **ask_db3_csv_params:** La función helper no recibe `default_nombre_base` en la posición que el controller usa (keyword-only); está alineado con el controller tras la corrección del contrato. Sin problemas.

### 7.3 Código muerto / legacy

- **platform/win_titlebar.py:** `set_titlebar_dark` no está referenciado por la aplicación. Código muerto desde el punto de vista del flujo actual.
- **core/links_tab.py (Tk):** No referenciado por la app PySide6. Solo tendría sentido para una app Tk legacy o scripts.

### 7.4 Manejo de excepciones

- Los controladores capturan excepciones genéricas, limpian estado con `_status_cb("")` y notifican con `_notify("error", ...)`. Patrón correcto.
- **ContadoresController._get_theme()** y **FtpController._safe_parent()** usan `try/except Exception: return {} / return self._parent`. Evitan fallos pero ocultan errores. Aceptable para resiliencia; opcionalmente loguear en desarrollo.

---

## 8. Refactors sugeridos (seguros)

1. **Card.set_theme:** Usar `.get()` con fallbacks para `card_bg`, `card_border`, `text` (y el resto que use directo) para evitar KeyError con tema incompleto.
2. **EstimadorManualDialog:** Quitar la segunda conexión `btn_calc.clicked.connect(self._on_calcular)`.
3. **run_pyside_ui.py:** Propagar código de salida con `sys.exit(main())` o `raise SystemExit(main())`.
4. **ContadoresController.procesar_db3_a_csv:** Devolver el resultado de `_run_db3_to_csv_flow` en lugar de siempre `True`.
5. **Estimador manual – extracción de lógica:** Mover `dias_360`, `parse_fecha_ddmmyyyy`, `calcular_impresiones_mensuales`, `calcular_resultado_estimacion` a `core/estimador_manual.py` y que el diálogo solo las llame.
6. **FtpClientPickerDialog:** Cuando `theme` es None, llamar a `apply_dialog_style(self, get_theme(parent))` para no depender solo del estilo del padre.

---

## 9. Mejoras de UI sugeridas

1. **Unificar estilo de file/folder picker:** Decidir un único patrón (contenedor estilizado como DB3 o transparente) y aplicarlo en csven0, suma_fija y autoestimacion para coherencia visual.
2. **EstimadorManualDialog:** Aplicar tema a QGroupBox y etiquetas (colores desde theme) y eliminar hardcodes.
3. **Toast:** Hacer que los colores de nivel y texto dependan del tema (inyección de tema en ToastManager/Toast).
4. **CsvEn0ParamsDialog:** Añadir `default_nombre_cliente` y que el controller pase `_last_en0_cliente`.
5. **LinksTab:** Conectar “Abrir” y “Copiar URL” a un controller o a slots que deleguen, con feedback por status_cb/notify_cb.
6. **STCTab:** Añadir controller que use QFileDialog y APIs headless de Extraer_ips/ip_ranges_txt y conectar los dos botones.
7. **Changelog / Iniciar con Windows:** Documentar como placeholder o implementar según requisitos.

---

## 10. Componentes reutilizables sugeridos

1. **FolderPickerRow (o FilePickerRow):** Widget compuesto: QLineEdit (stretch) + QPushButton “Elegir…”, con opción de estilo “themed container” o “transparent”, usando theme. Reutilizable en db3_csv_params, csven0_params, suma_fija_params, autoestimacion_dialog.
2. **FormParamsDialog base:** Clase intermedia entre BaseProDialog y los diálogos de parámetros (form + botones Aceptar/Cancelar + aplicación de tema + validación con warn). Reduciría duplicación en los diálogos de params.
3. **ClientPickerDialog genérico:** FtpClientPickerDialog y _ClientPickerDialog en ftp_dialogs comparten patrón (búsqueda + lista + aceptar/cancelar). Podría extraerse un “ListPickerDialog” con título, subtítulo, lista de ítems, filtro por texto y resultado seleccionado.
4. **Theme-aware Toast:** Componente Toast que reciba theme y aplique colores por nivel desde el tema, reutilizable en cualquier ventana que use StatusBus.

---

**Fin del informe.** Este documento debe usarse para priorizar correcciones y mejoras sin modificar código hasta que se aprueben los cambios.
