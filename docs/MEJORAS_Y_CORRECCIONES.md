# Mejoras y Correcciones — HelpDesk Manager App

> Estado: cada ítem se tacha al completarse.  
> Prioridades: 🔴 Urgente · 🟠 Alta · 🟡 Media · 🟢 Baja

---

## 🐛 Bugs Críticos

- [x] ~~🔴 **[app.py:46-56]** Race condition en el lock de instancia única — entre el check y la escritura del archivo pueden abrirse dos ventanas simultáneas. Usar `portalocker` o apertura atómica.~~ ✅ Reemplazado por `os.O_CREAT|O_EXCL` (creación atómica).
- [x] ~~🟠 **[ftp_dialogs.py:122-138]** Validación de contraseña no llama `.strip()` — contraseñas con solo espacios pasan el check vacío.~~ ✅ Cambiado a `if not self._pass.text().strip()`.
- [x] ~~🟠 **[csv_en0.py:42]** `pd.read_csv()` sin try-except — CSV malformado crashea la app sin mensaje amigable.~~ ✅ Envuelto en try-except con ValueError descriptivo.
- [x] ~~🟠 **[db3_to_csv.py:99-102]** `pd.concat()` con lista vacía lanza excepción confusa si ninguna DB tiene datos. Agregar guard antes del concat.~~ ✅ Ya estaba resuelto en el código (`if not dfs: raise RuntimeError(...)`).
- [x] ~~🟡 **[ip_ranges_txt.py:8-13]** `ipaddress.IPv4Interface()` no maneja CIDR inválido (ej. `/99`) — el rango se saltea silenciosamente sin log.~~ ✅ Ahora loguea con `warnings.warn` incluyendo lista de IPs ignoradas.
- [x] ~~🟡 **[db3_to_csv.py:91]** No verifica si los archivos `.db3` existen antes de intentar la conexión SQLite.~~ ✅ Agrega `FileNotFoundError` explícito antes de `conectar_db`.
- [x] ~~🟡 **[Estimador_manual.py:26]** Sin validación de límites en contadores — valores negativos o enormes producen estimaciones sin sentido.~~ ✅ Valida negativos y retorna early si `impresiones_diarias == 0` o `dias_estimacion == 0`.

---

## 🎨 Inconsistencias de UI / Tema

- [x] ~~🟠 **[toast.py:100]** Color `"#1E1E1E"` hardcodeado — no respeta el tema claro.~~ ✅ Usa `theme.get("surface")` y `theme.get("card_border")`.
- [x] ~~🟠 **[dialog_kit.py:150]** Color `"#E81123"` hardcodeado — debería venir de `theme.py`.~~ ✅ Agregado `"danger"` a ambos temas; `apply_dialog_style` lo consume via `theme.get("danger")`.
- [x] ~~🟠 **[modern_checkbox.py:166]** Color `"#FFFFFF"` hardcodeado.~~ ✅ Revisado — intencional: el checkmark es blanco sobre fondo naranja, correcto en ambos temas.
- [x] ~~🟡 **[estimador_manual_dialog.py:89]** Offset de posicionamiento `120` px hardcodeado — en pantallas 4K el diálogo aparece mal posicionado. Escalar por DPI.~~ ✅ Offset escalado con `screen.logicalDotsPerInch() / 96.0`.
- [x] ~~🟡 **Fuentes inconsistentes** — `setPointSizeF` usa 9.5, 10.5, 11.5 dispersos en múltiples archivos. Centralizar como constantes en `theme.py`.~~ ✅ Constantes `FONT_SMALL`, `FONT_BASE`, `FONT_LARGE`, `FONT_ICON` agregadas a `theme.py`.
- [x] ~~🟡 **Márgenes de layout hardcodeados** — `setContentsMargins(24, 10, 24, 20)` repetido en los tres tabs. Definir constante `TAB_MARGINS`.~~ ✅ `TAB_MARGINS` en `theme.py`; los tres tabs usan `*TAB_MARGINS`.
- [x] ~~🟡 **[action_card.py:121-126]** `enterEvent`/`leaveEvent` declarados pero no implementan nada — el hover de las cards no funciona.~~ ✅ Hover eleva sombra (`blur 20→28, y 4→6`); leaveEvent la restaura.
- [x] ~~🟢 **[links_tab.py:32]** Placeholder con emoji `"🔍 Filtrar recursos..."` mientras el resto de la app usa texto plano. Estandarizar.~~ ✅ Emoji removido.
- [x] ~~🟢 **[action_card.py]** Sin override de `setEnabled()` — botones deshabilitados no dan feedback visual.~~ ✅ Override implementado: opacity 0.4 + cursor Arrow cuando disabled; sombra + cursor Hand cuando enabled.

---

## 🔁 Código Duplicado / Refactors

- [ ] 🟠 **Validación de fecha repetida 3 veces** — `_valid_date_ddmmyyyy()` está copiada en `autoestimacion_dialog.py`, `csven0_params_dialog.py` y `db3_csv_params_dialog.py`. Mover a `pyside_ui/core/validation.py`.
- [ ] 🟡 **Patrón shadow + tema repetido** — `card.py`, `action_card.py`, `segmented_tabs.py`, `modern_checkbox.py` repiten la misma lógica. Considerar `BaseThemedWidget`.
- [ ] 🟡 **[contadores_controller.py:49-61]** Variables con nombres crípticos (`_last_suma_hojas`, `_last_en0_csv_in`). Renombrar a nombres descriptivos completos.
- [ ] 🟢 **Mensajes de error inconsistentes** entre `csv_en0.py` y `db3_to_csv.py`. Estandarizar formato.

---

## ⚠️ Manejo de Errores Faltante

- [ ] 🟠 **[dialog_kit.py:22-28]** `get_theme()` silencia todas las excepciones sin loguear — fallos de tema pasan desapercibidos.
- [ ] 🟡 **[contadores_tab.py:113 / stc_tab.py:57]** `set_status()` / `notify()` ignoran silenciosamente `StatusBus` None — agregar warning log.
- [ ] 🟡 **[Clientes_suma.py:2-3]** `import numpy / pandas` sin try-except — si faltan dependencias el error es críptico.
- [ ] 🟡 **[autoestimacion_dialog.py:110-128]** Solo verifica existencia del CSV, no valida su estructura. Agregar `pd.read_csv(path, nrows=1)` en validación.

---

## 🔒 Seguridad

- [ ] 🟠 **[db3_to_csv.py:169]** Nombre de archivo de salida construido con input del usuario sin sanitizar — posible path traversal. Aplicar `re.sub(r'[^\w\-]', '', nombre)`.
- [ ] 🟡 **[app.py:74]** App User Model ID hardcodeado con versión fija `"Prototype"` — debería leer `version.json` para evitar íconos duplicados en la barra de tareas al actualizar.

---

## 🚀 Funcionalidad Incompleta

- [ ] 🟠 **[links_tab.py:178-188]** Datos de links hardcodeados — no se persisten entre sesiones. Implementar `pyside_ui/core/links_storage.py` con guardado JSON.
- [ ] 🟡 **[contadores_controller.py]** Operaciones FTP sin timeout — si la red cuelga, la UI se congela indefinidamente.
- [ ] 🟡 **[stc_controller.py / contadores_controller.py]** CSVs grandes cargados completos en memoria sin chunking — archivos de +50 MB congela la UI. Usar `chunksize` en `pd.read_csv()`.
- [ ] 🟡 **[toast.py:158-174]** Al recibir mensaje FTP se limpia toda la cola de notificaciones — notificaciones de otras fuentes se pierden. Reemplazar con priority queue.
- [ ] 🟢 **[menubar.py:26]** Solo `Ctrl+Q` definido como shortcut. Agregar `F5` (refrescar), `Ctrl+S` (guardar config), etc.

---

## 📋 Configuración y Entorno

- [ ] 🟡 **[version.json:3]** Timestamp `"last_update": "1777170444.475353"` inválido (corresponde a año 1956). Corregir con timestamp actual.
- [ ] 🟢 **Sin `requirements.txt`** — las dependencias no están documentadas formalmente. Generar con `pip freeze > requirements.txt` o usar `pyproject.toml`.
- [ ] 🟢 **Sin soporte `.env`** — rutas del servidor FTP y NAS bakeadas en el código. Considerar `python-dotenv`.

---

## 🧪 Tests

- [ ] 🟡 **Cobertura mínima** — 34 archivos fuente, solo 4 tests. Agregar tests para controllers y dialogs (objetivo 80%+).
- [ ] 🟡 **Sin tests de integración** — no hay test que verifique el flujo DB → CSV → Diálogo → Exportación completo.
- [ ] 🟢 **[estimador_manual_dialog.py:38]** `WA_DeleteOnClose` con parent `None` puede dejar ventanas sin liberar en memoria. Verificar con test de ciclo de vida.

---

## 🧹 Limpieza Menor

- [ ] 🟢 **[ftp_dialogs.py:7]** `QtCore` importado pero no usado.
- [ ] 🟢 **Sin sistema de logging estructurado** — errores van a stdout/stderr. Implementar `logging` con rotación de archivo.
- [ ] 🟢 **[main_window.py:35]** Comentario temporal con emoji `# 🚩 Temporalmente...` — convertir a formato estándar `# TODO:` con descripción clara.

## 🚀 Sistema de Lanzamiento (Smart Launcher)

- [x] 🔴 **Lanzador Estático** — El launcher anterior era un `.exe` único que no se podía actualizar. ✅ Implementado sistema `onedir` con motor estable y núcleo dinámico.
- [x] 🟠 **Sincronización NAS** — Los usuarios tenían que copiar carpetas a mano. ✅ Implementado `deploy.py` (NAS) y `launcher.py` (Pull automático).
- [x] 🟠 **Iconos rotos en EXE** — El launcher no mostraba el icono de la empresa. ✅ Corregido con rutas absolutas en el build.
- [x] 🟡 **Versionado numérico simple** — Usar `1, 2, 3` es confuso para el usuario. ✅ Implementado versionado semántico `2.0.x` visible en la ventana principal.
- [x] 🟡 **Dependencias faltantes en runtime** — El launcher fallaba si el usuario no tenía pandas/numpy. ✅ Blindado con `hiddenimports` en el bundle del motor.
- [x] 🟡 **Limpieza de rutas** — Logs y archivos de crash ensuciaban la carpeta del EXE. ✅ Redirigidos a `%LOCALAPPDATA%/HelpDeskManagerApp`.

---

---

> Última actualización: 2026-04-26 · Total: **44 ítems** (7 bugs · 9 UI · 6 Launcher · 4 duplicados · 4 errores · 2 seguridad · 5 funcionalidad · 3 config · 3 tests · 3 limpieza)  
> Completados hasta ahora: **22/44** ✅ (7 bugs + 9 UI + 6 Launcher) — siguiente sección: 🔁 Código Duplicado / Refactors
