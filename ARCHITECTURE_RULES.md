# Reglas de Arquitectura — HelpDeskManagerApp (PySide6)

**Documento:** Contrato arquitectónico del proyecto.  
**Objetivo:** Evitar regresiones arquitectónicas durante el desarrollo futuro.  
**Referencia:** Basado en `ARCHITECTURE_AUDIT_REPORT.md`.

Toda modificación de código debe respetar estas reglas. Las excepciones deben documentarse y aprobarse explícitamente.

---

## 1. Principios arquitectónicos del proyecto

1. **Separación estricta de capas:** La UI no contiene lógica de negocio. Los controladores orquestan. El core contiene la lógica de negocio reutilizable.

2. **Flujo unidireccional:** UI → Controller → Core (o Service). La UI nunca invoca core ni servicios directamente. El feedback al usuario se hace siempre mediante callbacks inyectados (`status_cb`, `notify_cb`).

3. **Un solo canal de notificaciones:** Los mensajes al usuario (estado en barra, toasts) pasan por el **StatusBus** y el sistema de toasts. No se usan `QMessageBox` ni equivalentes Tkinter para resultados de operaciones; solo se permite `dialog_kit.warn()` para validaciones en diálogos.

4. **Diálogos unificados:** Todos los diálogos modales o de parámetros heredan de **BaseProDialog** (dialog_kit), usan el tema de la aplicación y siguen el mismo patrón visual (barra de título draggable, botones consistentes).

5. **Cambios incrementales y reversibles:** No se realizan refactors estructurales ni cambios de contratos API sin autorización explícita. Las reglas del proyecto (no refactor estructural, no modificar contratos API, no cambiar nombres de modelos/schemas/tablas sin confirmación) se aplican.

6. **Core sin dependencia de UI:** Los módulos en `pyside_ui/core/` no deben importar PySide6 ni Tkinter para su API principal. La obtención de rutas, opciones o confirmaciones desde el usuario es responsabilidad del controller (que usa QFileDialog, diálogos de `ui/`, etc.) y pasa datos ya resueltos al core.

---

## 2. Responsabilidades por capa

### 2.1 UI (tabs, widgets, ventana principal)

- **Permitido:**
  - Presentar datos y controles.
  - Conectar señales de widgets (clicked, changed, etc.) a métodos del controller.
  - Recibir y aplicar tema (dict THEME).
  - Exponer callbacks que el controller usará para feedback (`status_cb`, `notify_cb`), típicamente delegando en el StatusBus.
  - Usar únicamente componentes de `pyside_ui/widgets/` y de `pyside_ui/ui/` (dialog_kit, diálogos de parámetros).

- **Prohibido:**
  - Contener lógica de negocio (cálculos, reglas de dominio, validaciones de negocio).
  - Llamar a módulos de `pyside_ui/core/` o a servicios.
  - Usar `QMessageBox` para resultados de operaciones.
  - Abrir diálogos que no provengan de dialog_kit o de los diálogos definidos en `ui/` (params, pickers).

### 2.2 Controllers (`pyside_ui/controllers/`)

- **Permitido:**
  - Recibir eventos desde la UI (por conexión de señales a métodos del controller).
  - Abrir diálogos de parámetros o pickers (de `ui/`) y leer resultados.
  - Llamar a servicios (`pyside_ui/services/`) y a funciones de core (`pyside_ui/core/`).
  - Usar `status_cb` y `notify_cb` para informar progreso y resultado.
  - Usar `QFileDialog`, `QColorDialog`, etc., cuando sea necesario para elegir archivos o opciones que luego se pasan al core.
  - Mantener estado de “últimos valores” (rutas, opciones) para prellenar diálogos.
  - Obtener tema desde la ventana (p. ej. `parent.window().theme`) para pasarlo a los diálogos.

- **Prohibido:**
  - Contener lógica de negocio pesada (cálculos de dominio, transformaciones de datos); debe delegarse en core.
  - Acceder directamente a widgets internos del tab más allá del parent necesario para diálogos modales.
  - Mostrar mensajes con `QMessageBox`; usar siempre `notify_cb` o, en diálogos, `dialog_kit.warn()`.

### 2.3 Core (`pyside_ui/core/`)

- **Permitido:**
  - Lógica de negocio pura: transformaciones, validaciones de dominio, acceso a datos (archivos, SQLite, FTP a nivel de protocolo), generación de archivos.
  - APIs “headless”: funciones que reciben rutas, opciones y parámetros ya resueltos y devuelven resultados o lanzan excepciones.
  - Documentar claramente qué funciones son para uso desde PySide6 (sin UI) y cuáles son legacy (con Tk/file dialogs).

- **Prohibido:**
  - Importar PySide6 o crear ventanas/diálogos en la API principal usada por la aplicación PySide6.
  - Para código nuevo o refactorizado: usar `tkinter.filedialog`, `tkinter.messagebox` o cualquier UI; el caller (controller) debe resolver rutas y opciones y pasarlas al core.

### 2.4 Services (`pyside_ui/services/`)

- **Permitido:**
  - Abstraer infraestructura (FTP, bus de estado, futuros servicios de red o almacenamiento).
  - Delegar en módulos de core para la lógica que ya vive ahí (p. ej. FtpService → core.ftp_db3, core.ftp_nas_config).
  - Exponer APIs que reciban callbacks opcionales (p. ej. `status_cb`) para progreso.

- **Prohibido:**
  - Contener lógica de negocio de dominio que pertenezca a core.
  - Mostrar diálogos o mensajes al usuario; eso es responsabilidad del controller usando `status_cb`/`notify_cb`.

---

## 3. Patrones prohibidos

### 3.1 Lógica de negocio dentro de la UI

- **Prohibido:** Cálculos de dominio, reglas de validación de negocio, transformaciones de datos, llamadas a core o servicios dentro de tabs, diálogos o widgets.
- **Correcto:** La UI solo presenta, captura entrada y delega en el controller. Toda decisión de negocio y toda llamada a core/servicios ocurre en el controller.

### 3.2 Uso de QMessageBox (y equivalentes)

- **Prohibido:** `QMessageBox.information`, `QMessageBox.warning`, `QMessageBox.critical`, `QMessageBox.question` para informar resultado de operaciones iniciadas desde la aplicación (éxito, error, aviso).
- **Correcto:** Usar `notify_cb(level, title, message, timeout_ms)` para toasts (éxito, error, info, warning). Para confirmaciones destructivas o críticas, usar `dialog_kit.ConfirmDialog`. Para avisos breves dentro de un diálogo (p. ej. validación de campos), usar `dialog_kit.warn(parent, title, message)`.

### 3.3 Acceso directo al core desde la UI

- **Prohibido:** Que un tab, widget o diálogo importe y llame directamente a funciones de `pyside_ui.core.*` o a servicios para ejecutar operaciones de negocio.
- **Correcto:** La UI conecta señales a un controller; el controller llama al core (o al servicio) y luego usa `status_cb`/`notify_cb` para actualizar al usuario.

### 3.4 Diálogos que no usen dialog_kit

- **Prohibido:** Crear diálogos modales que no hereden de `BaseProDialog` o que no usen los estilos y helpers de `dialog_kit` (make_card, make_button_row, warn, apply_dialog_style).
- **Correcto:** Todos los diálogos de parámetros, confirmación o mensaje usan `BaseProDialog` y, cuando corresponda, `MessageDialog`, `ConfirmDialog` o `warn()`.

---

## 4. Reglas de comunicación (callbacks y diálogos)

### 4.1 status_cb

- **Definición:** Callback inyectado en el controller con firma `(text: str) -> None`.
- **Uso:** El controller lo invoca para actualizar el texto de la barra de estado global (o para limpiarlo con `""`). El tab (o la ventana) implementa `status_cb` delegando en `StatusBus.set_status(text)`.
- **Reglas:**
  - Solo el controller (o código que actúe como orquestador) debe llamar a `status_cb`. La UI no debe invocar lógica de negocio que a su vez use `status_cb`; el flujo debe ser UI → controller → core → controller → `status_cb`/`notify_cb`.
  - Limpiar el estado al finalizar la operación (por ejemplo `status_cb("")`) para no dejar mensajes obsoletos.

### 4.2 notify_cb

- **Definición:** Callback inyectado en el controller con firma `(level: str, title: str, message: str, timeout_ms: int = 3000) -> None`.
- **Uso:** El controller lo invoca para mostrar toasts (éxito, error, aviso, info). El tab implementa `notify_cb` delegando en `StatusBus.notify(level, title, message, timeout_ms)`.
- **Reglas:**
  - Solo el controller (o orquestador) debe llamar a `notify_cb` para resultados de operaciones. No usar QMessageBox como sustituto.
  - Niveles esperados: `"success"`, `"error"`, `"warning"`, `"info"`.

### 4.3 Uso de dialog_kit

- **BaseProDialog:** Base de todos los diálogos modales: frameless, barra de título draggable, estilos vía `apply_dialog_style(widget, theme)`.
- **MessageDialog / ConfirmDialog:** Para mensajes y confirmaciones sin lógica de formulario.
- **warn(parent, title, message):** Para validaciones dentro de un diálogo (campos obligatorios, formato incorrecto). No usar QMessageBox para eso.
- **Tema:** Los diálogos deben recibir el tema desde el controller (p. ej. `get_theme(parent)` o `theme` explícito) y llamar a `apply_dialog_style(self, theme)` para consistencia visual.

---

## 5. Reglas para crear nuevas pestañas (tabs)

1. **Ubicación:** El módulo del tab debe vivir en `pyside_ui/tabs/` y ser un `QWidget` que se añade al `QStackedWidget` desde `main_window.py`.

2. **Sin lógica de negocio:** El tab solo construye la UI (layout, botones, campos, tabla) y conecta señales a un controller. No debe importar `pyside_ui.core.*` ni servicios para ejecutar operaciones.

3. **Controller obligatorio para operaciones:** Si el tab tiene acciones que afectan datos o ejecutan flujos de negocio, debe existir un controller que reciba los callbacks (`status_cb`, `notify_cb`) y que sea instanciado por el tab (o inyectado). Las señales de los botones/controles se conectan a métodos de ese controller.

4. **Callbacks inyectados:** Si el tab debe mostrar estado o toasts, recibe `status_bus` (o callbacks equivalentes) y los pasa al controller. El tab puede implementar `set_status`/`_notify` que deleguen en el StatusBus y pasar esas funciones al controller como `status_cb` y `notify_cb`.

5. **Tema:** El tab debe implementar `set_theme(theme: dict)` y aplicar el tema a sus widgets (Card, botones, etc.) para que `MainWindow.apply_theme()` pueda actualizar la apariencia.

6. **Registro en MainWindow:** Añadir el nuevo tab al stack y a la lista de SegmentedTabs en `main_window.py`, y aplicar tema al tab en `apply_theme`.

---

## 6. Reglas para crear controladores

1. **Ubicación:** Los controladores viven en `pyside_ui/controllers/`. Heredan de `QObject` si necesitan señales o ciclo de vida Qt; en cualquier caso, reciben un `parent` (widget) para poder obtener la ventana y el tema.

2. **Inyección de dependencias:** El controller recibe por constructor:
   - Al menos un `parent` (widget de la UI que lo usa).
   - `status_cb: Callable[[str], None]` para barra de estado.
   - `notify_cb: Callable[[str, str, str, int], None]` para toasts (opcional pero recomendado para operaciones con resultado).
   - Servicios o dependencias que necesite (p. ej. `FtpService`).

3. **Sin lógica de negocio pesada:** La orquestación (qué diálogo abrir, en qué orden llamar al core, cómo notificar) pertenece al controller. La lógica de dominio (cálculos, transformaciones, reglas) pertenece al core; el controller solo prepara parámetros y maneja excepciones.

4. **Diálogos y tema:** El controller debe obtener el tema (p. ej. desde `parent.window().theme`) y pasarlo a los diálogos de parámetros/pickers para que se apliquen estilos correctos.

5. **Manejo de errores:** En caso de excepción desde core o servicio, el controller debe limpiar el estado (`status_cb("")`) y notificar con `notify_cb("error", title, str(e), timeout)` (o similar). No debe dejar ventanas o estado inconsistente.

6. **Exposición al menú (si aplica):** Si la ventana principal debe invocar acciones del controller (p. ej. menú FTP), el tab que posee el controller debe exponerlo en la ventana (p. ej. `setattr(win, "ftp_controller", self._ftp_controller)`) de forma documentada y estable (por ejemplo en un timer de inicialización).

---

## 7. Reglas para diálogos

1. **Heredar de BaseProDialog:** Todos los diálogos modales de la aplicación deben heredar de `pyside_ui.ui.dialog_kit.BaseProDialog` y usar `self.root_layout` para el contenido.

2. **Estilos:** Llamar a `apply_dialog_style(self, theme)` en el constructor, usando el tema obtenido de `get_theme(parent)` o el `theme` pasado por el controller. No dejar diálogos sin tema aplicado.

3. **Validación en diálogo:** Si se validan campos (obligatorios, formato), usar `dialog_kit.warn(self, title, message)` para mostrar el error. No usar `QMessageBox`.

4. **Resultado:** Exponer el resultado vía propiedad (p. ej. `result`) o método (p. ej. `get_result()`). La API pública del diálogo (función `ask_*` si existe) debe aceptar los mismos parámetros que el controller va a pasar (defaults, theme) para evitar desalineación de contratos.

5. **Diálogos no modales (excepcionales):** Si se requiere una ventana no modal (p. ej. estimador manual always-on-top), seguir usando BaseProDialog como base y documentar que no se usa como modal; la lógica de negocio que se muestre en pantalla debe residir en core o en el controller, no solo en el diálogo.

---

## 8. Reglas para interactuar con módulos core

1. **Solo el controller (o servicios) llama al core:** La UI (tabs, diálogos, widgets) no importa ni invoca funciones de `pyside_ui.core.*` para ejecutar operaciones. El controller obtiene rutas y opciones (p. ej. vía QFileDialog o diálogos de params) y llama al core con esos datos.

2. **Preferir API headless:** Al usar un módulo core, usar la variante que no abre ventanas ni messageboxes (p. ej. `convertir_xls_a_csv_arcos_headless` en lugar de `convertir_xls_a_csv_arcos`). Si no existe, el controller debe obtener todos los parámetros (rutas, fechas, etc.) mediante la UI (diálogos PySide6) y pasar esos valores a una función del core que no dependa de Tk ni de PySide6.

3. **Excepciones:** El core puede lanzar excepciones (ValueError, FileNotFoundError, RuntimeError, etc.). El controller debe capturarlas, limpiar el estado y notificar al usuario con `notify_cb("error", ...)`.

4. **No extender core con UI:** Al añadir funcionalidad nueva en core, no introducir dependencias de PySide6 ni Tkinter en la API principal. Si se necesita elegir archivos o mostrar mensajes, eso se resuelve en el controller y se pasa al core.

---

## 9. Reglas de migración de módulos Tkinter

1. **No eliminar código legacy sin criterio:** Los módulos en `core/` que aún usan Tkinter (filedialog, messagebox, ttk) pueden coexistir con la aplicación PySide6 siempre que la ruta usada por PySide6 sea headless (sin UI). No borrar la API legacy sin definir migración o deprecación explícita.

2. **Nuevas funcionalidades en core:** Para funcionalidad nueva o refactors en core, no usar Tkinter. El controller debe usar QFileDialog (o diálogos de `ui/`) y pasar rutas/opciones al core.

3. **Migrar llamadas desde PySide6:** Cualquier flujo que desde la app PySide6 necesite una operación que hoy está en un módulo core con Tk debe:
   - Usar una API headless del core (parámetros ya resueltos), y
   - Hacer que el controller resuelva esos parámetros con UI PySide6 (diálogos, QFileDialog).

4. **Crear API headless si no existe:** Si un módulo core solo expone una función que usa filedialog/messagebox, añadir una nueva función (o parámetros opcionales) que reciba rutas/opciones como argumentos y no abra UI. La app PySide6 usará solo esa API; la función con Tk puede quedar como legacy/deprecada.

5. **No añadir Tk a módulos ya headless:** En módulos que ya tienen API headless (p. ej. Db3ToCsv, CsvEn0, Autoestim, Clientes_suma headless), no reintroducir dependencias de Tkinter ni PySide6 en esa API.

---

## Resumen de cumplimiento

- **UI:** Solo presentación y delegación; sin core, sin servicios, sin QMessageBox.
- **Controllers:** Orquestación, diálogos, llamadas a core/servicios, `status_cb`/`notify_cb`.
- **Core:** Lógica de negocio; API headless para uso desde PySide6; sin UI en la API principal.
- **Services:** Abstracción de infraestructura; sin lógica de dominio; sin diálogos.
- **Diálogos:** Siempre BaseProDialog y dialog_kit; tema aplicado; validaciones con `warn()`.
- **Migración:** Preferir API headless; no añadir Tk a rutas usadas por PySide6; extender contratos de diálogos de forma explícita y alineada con el controller.

Este documento es el contrato arquitectónico del proyecto. Cualquier desviación debe quedar documentada y aprobada.
