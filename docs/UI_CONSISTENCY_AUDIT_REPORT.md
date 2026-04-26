# Informe de auditoría de consistencia UI — HelpDeskManagerApp (PySide6)

**Fecha:** 4 de marzo de 2025  
**Alcance:** Análisis de consistencia visual, layout, tema y usabilidad en módulos UI.  
**Referencias:** ARCHITECTURE_RULES.md, ARCHITECTURE_AUDIT_REPORT.md, CODE_AND_UI_AUDIT_REPORT.md.

---

## 1. Resumen ejecutivo

La aplicación tiene una base coherente: todos los diálogos heredan de BaseProDialog, los tres tabs usan el mismo Card y el tema se aplica en la mayoría de los componentes. Persisten **inconsistencias localizadas** que conviene unificar para mejorar la percepción de calidad y la mantenibilidad:

- **File/folder picker:** Un diálogo (DB3→CSV) usa contenedor estilizado con tema; el resto usa wrapper transparente y otro spacing, lo que genera diferencias visuales.
- **Botones:** Varias familias (big button 62px, small 36px, segment 34px, diálogos 8px padding) con border-radius distintos (10, 12, 14, 16, 18).
- **Tema:** Toast y EstimadorManualDialog usan colores fijos; el Toast no se adapta al tema claro/oscuro.
- **Layout:** Márgenes y spacing están alineados en formularios (14/10) y en BaseProDialog, pero el spacing del picker row varía (0 vs 8) y no hay constantes compartidas documentadas.

El informe propone un **conjunto mínimo de estándares UI** y mejoras seguras sin refactor arquitectónico, para usar como hoja de ruta en futuras iteraciones.

---

## 2. Inconsistencias UI detectadas

### 2.1 File / folder picker

| Ubicación | Contenedor | Estilo | Spacing fila |
|-----------|------------|--------|--------------|
| db3_csv_params_dialog | FolderPickerWrap | panel_bg, border, border-radius 10px; QLineEdit transparente | 0 |
| csven0_params_dialog | RowWrapTransparent | background: transparent | 8 |
| suma_fija_params_dialog | RowWrapTransparent | background: transparent | 8 |
| autoestimacion_dialog | RowWrapTransparent | background: transparent | 8 |

**Problema:** DB3 se ve como un único bloque con borde; el resto deja ver el fondo del diálogo entre el QLineEdit y el botón "Elegir…". En temas con contraste, el resultado visual no es el mismo.

### 2.2 Border-radius y padding de botones

| Componente | border-radius | padding | min-height |
|------------|---------------|---------|------------|
| controls.make_big_button (tabs) | 18px | 10px 12px | 62px |
| dialog_kit QPushButton | 12px | 8px 14px | — |
| dialog_kit QPushButton#Primary | 12px | 8px 14px | — |
| LinksTab _small_btn_qss | 14px | 8px 14px | 36px |
| SegmentedTabs botones | 16px | 6px 14px | 34px |
| BaseProDialog ProClose (QToolButton) | 10px | 6px 10px | — |

No hay una escala única (p. ej. small / medium / large) documentada; cada módulo elige valores cercanos pero distintos.

### 2.3 Inputs (QLineEdit / QComboBox)

| Origen | border-radius | padding |
|--------|----------------|---------|
| dialog_kit apply_dialog_style | 10px | 8px 10px |
| LinksTab _inputs_qss | 14px | 8px 12px |
| Card (no define inputs) | — | — |

En tabs (Links) los inputs son más redondeados y con padding distinto a los de los diálogos.

### 2.4 Colores y tema

- **Toast (widgets/toast.py):** Colores de nivel (`#2ecc71`, `#f1c40f`, `#e74c3c`, `#3498db`) y texto (`white`, `#eee`) fijos. No usa `theme`; en tema claro los toasts siguen siendo muy contrastados y ajenos a la paleta.
- **EstimadorManualDialog _group_box:** `rgba(255,255,255,0.92)` fijo para título y borde. En tema claro el texto blanco sobre fondo claro pierde legibilidad.
- **LinksTab tabla:** `card_bg` con fallback `#202020`; en theme.py el `card_bg` es `#2A2A2A`. La tabla queda algo más oscura que el resto de cards en dark.

### 2.5 Diálogos: aplicación de tema

- **db3_csv_params_dialog:** Siempre aplica tema: `theme_to_apply = theme or get_theme(parent)` y luego `apply_dialog_style(self, theme_to_apply)` + estilo extra para FolderPickerWrap.
- **csven0_params_dialog, suma_fija_params_dialog, autoestimacion_dialog:** Solo llaman `apply_dialog_style(self, theme)` cuando `if theme:`. Si el controller no pasa theme, dependen del estilo aplicado en BaseProDialog (get_theme(parent) en __init__). Comportamiento correcto pero distinto al de db3 en cuanto a código.

### 2.6 Botones de acción en diálogos

- **db3_csv_params_dialog:** "Aceptar" / "Cancelar"; btn_ok ObjectName "Primary", btn_cancel "Secondary".
- **autoestimacion_dialog:** "Generar" / "Cancelar"; solo btn_ok "Primary"; no se asigna ObjectName a Cancelar.
- **ftp_dialogs / ftp_client_picker:** "Continuar" / "Cancelar" o "Aceptar" / "Cancelar".

Texto y roles son coherentes por contexto, pero falta una convención explícita (por ejemplo: siempre Primary para la acción principal y mismo ObjectName para cancelar).

---

## 3. Problemas de layout

### 3.1 Márgenes y spacing

- **MainWindow inner:** 28, 22, 28, 22; spacing 18.
- **Card:** 22, 20, 22, 20; spacing 12; grid 16 (H), 14 (V).
- **BaseProDialog shell:** 16, 0, 16, 16; spacing 12; _root 0, 12, 0, 0; spacing 12.
- **FormLayout en diálogos:** margins 0,0,0,0; horizontalSpacing 14; verticalSpacing 10 (uniforme en db3, csven0, suma_fija, autoestim).
- **TitleBar MainWindow:** 12, 8, 8, 8; spacing 10.
- **BaseProDialog ProTitleBar:** 16, 12, 12, 12; spacing 10.

Los valores son razonables pero están dispersos; no hay constantes compartidas (p. ej. `SPACING_FORM`, `MARGIN_DIALOG`) ni documento que los agrupe.

### 3.2 Fila de botones en diálogos

- **db3_csv_params_dialog:** `row_btns.addStretch(1)` → cancel → ok; `self.root_layout.addSpacing(6)` antes de `addLayout(row_btns)`.
- **csven0_params_dialog, suma_fija_params_dialog:** Mismo patrón (stretch, cancel, ok); no siempre el mismo addSpacing antes.
- **autoestimacion_dialog:** Botones "Generar" y "Cancelar"; orden y layout similares.

La alineación (derecha, cancelar + aceptar) es consistente; el spacing previo a la fila de botones no está unificado en código.

### 3.3 Tabs: estructura del contenido

- **ContadoresTab:** Card + grid 4 filas (botones + checkbox). Sin spacing adicional entre card y contenido; el grid del Card define todo.
- **STCTab:** Card + grid 2 filas, botones a ancho completo. Misma idea que Contadores pero con menos elementos.
- **LinksTab:** Card + grid: fila 0 = HBox (filtro + combo), fila 1 = tabla, fila 2 = HBox (botones). Los botones "Abrir" y "Copiar URL" no usan make_big_button; usan _small_btn_qss (36px). Densidad y tipo de controles distintos a Contadores/STC.

Los tres usan el mismo Card y layout general (vertical, un Card), pero la densidad y el tipo de acciones (big buttons vs small + tabla) difieren por naturaleza del tab; solo se sugiere unificar criterios de spacing interno del Card cuando haya botonera (p. ej. siempre mismo gap antes de la última fila).

---

## 4. Violaciones de tema

### 4.1 Toast

- Colores de nivel y texto no leen del `theme`; no hay variante “light” para toasts.
- **Recomendación:** Pasar `theme` (o paleta derivada) al Toast/ToastManager y mapear success/warning/error/info a colores del tema (o a una extensión del theme, p. ej. `toast_success`, `toast_error`).

### 4.2 EstimadorManualDialog

- `_group_box` usa `rgba(255,255,255,0.92)` para color de texto y título del QGroupBox.
- **Recomendación:** Recibir `theme` en el diálogo y usar `theme.get("text", "#EAEAEA")` (y muted si aplica) para QGroupBox y títulos, de modo que en tema claro se vea correctamente.

### 4.3 LinksTab

- Tabla: fallback `card_bg` "#202020" mientras theme usa card_bg "#2A2A2A". Opcional unificar el fallback con theme (p. ej. mismo valor que card_bg del theme por defecto).

### 4.4 Resto

- Card, SegmentedTabs, controls, dialog_kit y MainWindow aplican theme con .get() o resolve_theme; no se detectan más violaciones graves.

---

## 5. Mejoras de UX

### 5.1 Mensajes y feedback

- Unificar tono de toasts (ej. “Listo” vs “URL copiada” vs “CSV generado: …”) en estilo breve y consistente.
- En diálogos de parámetros, si un campo es obligatorio, indicarlo en placeholder o label (ej. “(obligatorio)”) de forma uniforme.

### 5.2 Agrupación de acciones

- Contadores: muchas acciones en un solo card; está claro pero denso. Opcional agrupar en secciones con títulos (p. ej. “Exportación”, “Estimaciones”) si se añaden más acciones.
- STC: solo dos acciones; actual layout es suficiente.

### 5.3 Etiquetas de botones

- “Aceptar” / “Cancelar” vs “Generar” / “Cancelar”: aceptable por contexto. Documentar en estándares que la acción principal lleve ObjectName "Primary" y que “Cancelar” sea siempre la secundaria.

### 5.4 Legibilidad

- Espaciado entre filas de formulario (10px) y entre secciones (12px en BaseProDialog) es adecuado. No se proponen cambios de tamaño de fuente sin requisitos de accesibilidad; solo unificar que los títulos de sección usen el mismo criterio (Card 17 DemiBold, ProTitle 700).

---

## 6. Widgets reutilizables sugeridos

### 6.1 FilePickerRow / FolderPickerRow

- **Problema:** Cuatro implementaciones distintas del patrón “QLineEdit + QPushButton ‘Elegir…’” (una con contenedor estilizado, tres con transparent).
- **Propuesta:** Un solo widget (o dos variantes: file vs folder) que reciba theme, placeholder, valor inicial, y callback al pulsar “Elegir…”. Opciones: contenedor estilizado (como DB3) por defecto, o flag `styled_container=True/False`. Ubicación sugerida: `pyside_ui/widgets/` o helper en `dialog_kit`. Así se unifica spacing (p. ej. 8), border-radius y uso de tema.

### 6.2 FormButtonRow

- **Problema:** Cada diálogo monta a mano la fila “Cancelar” + “Aceptar” (o “Generar”) con stretch y a veces spacing.
- **Propuesta:** Reutilizar o extender `make_button_row` de dialog_kit para una fila estándar de diálogo (stretch + cancel + ok, con ObjectNames y spacing fijo). No obliga a cambiar la API actual de make_button_row; puede ser una función adicional `make_dialog_button_row(...)` que devuelva el layout ya con addStretch(1).

### 6.3 SmallActionButton (opcional)

- **Problema:** LinksTab define _small_btn_qss (36px, radius 14) localmente; si otros tabs necesitan botones “secundarios” pequeños, se repetiría el patrón.
- **Propuesta:** Función en `widgets/controls.py` tipo `make_small_button(text, theme)` que devuelva un QPushButton con el mismo estilo que Links, para reutilizar en cualquier tab o barra de herramientas.

### 6.4 Tabla temática (opcional)

- **Problema:** LinksTab tiene _table_qss con muchos detalles (header, selection, hover). Si en el futuro STC u otro tab muestran tablas, se duplicaría estilo.
- **Propuesta:** Helper `apply_table_theme(table_widget, theme)` o widget `ThemedTable` que aplique el mismo QSS desde theme, para mantener tablas consistentes.

---

## 7. Estándares UI propuestos

### 7.1 Espaciado

- **Estándar sugerido (documentar en diseño o en código):**
  - Formularios: horizontalSpacing 14, verticalSpacing 10.
  - Contenido de diálogo (root_layout): spacing 12; márgenes shell 16,0,16,16.
  - Card: márgenes 22,20,22,20; spacing 12; grid 16 (H), 14 (V).
  - MainWindow inner: márgenes 28,22,28,22; spacing 18.
  - Fila “picker” (LineEdit + botón): spacing 8 entre controles; contenedor con mismo fondo que inputs (panel_bg) y border-radius 10 para igualar a QLineEdit de dialog_kit.

### 7.2 Botones

- **Primaria (acción principal):** ObjectName "Primary"; estilo dialog_kit (orange, radius 12, padding 8 14).
- **Secundaria (cancelar/cerrar):** Mismo padding y radius que el resto de QPushButton del diálogo (12, 8 14).
- **Big action (tabs):** make_big_button: height 62, radius 18, padding 10 12.
- **Small action (toolbar / Links):** min-height 36, radius 14, padding 8 14; usar tema (btn_bg, btn_hover, card_border, text).

### 7.3 Inputs

- **En diálogos:** Los definidos por apply_dialog_style: radius 10, padding 8 10.
- **En tabs (Links):** radius 14, padding 8 12, min-height 36. Si se desea convergencia, valorar alinear radius (p. ej. 10 o 12) y padding con diálogos en una futura iteración.

### 7.4 Cards

- Un solo componente Card; márgenes y grid según 7.1. Título: Segoe UI 17 DemiBold; color desde theme["text"]. No definir inputs dentro de Card; los tabs que tengan inputs (Links) los estilizan aparte con theme.

### 7.5 Diálogos

- Siempre BaseProDialog; siempre aplicar tema (explícito o get_theme(parent)) y apply_dialog_style. Filas de file/folder picker: mismo patrón visual (contenedor estilizado recomendado para igualar a los demás campos). Botones: stretch + cancel + ok; spacing 6 u 8 antes de la fila de botones de forma uniforme.

---

## 8. Correcciones UI seguras (roadmap)

Sin refactor de arquitectura ni de APIs públicas:

1. **Unificar estilo del file/folder picker:** Decidir un único criterio (contenedor estilizado como DB3 vs transparente). Si se elige estilizado: en csven0, suma_fija y autoestimacion_dialog reutilizar el mismo patrón que db3 (FolderPickerWrap + resolve_theme + panel_bg/border radius 10) o introducir un widget compartido FolderPickerRow que reciba theme.
2. **Toast y tema:** Añadir parámetro opcional theme a Toast/ToastManager; si viene theme, usar colores derivados (p. ej. success = verde suave del theme o nuevo key toast_success); si no, mantener colores actuales para no romper comportamiento.
3. **EstimadorManualDialog _group_box:** Sustituir colores fijos por theme.get("text") (y muted si hace falta) en el QSS del QGroupBox para que respete tema claro/oscuro.
4. **LinksTab tabla:** Usar theme.get("card_bg", "#2A2A2A") (o el mismo fallback que el resto de cards) para evitar #202020 más oscuro que el theme.
5. **Constantes de layout (opcional):** Definir en theme o en un módulo `ui_constants.py` valores como FORM_SPACING_H, FORM_SPACING_V, DIALOG_SHELL_MARGINS, CARD_GRID_SPACING y usarlos en nuevos código o, de forma gradual, en los módulos que se toquen.
6. **ObjectName en botón Cancelar:** Asignar ObjectName "Secondary" (o el que se estandarice) al botón cancelar en autoestimacion_dialog (y revisar otros) para que el QSS de dialog_kit se aplique igual en todos los diálogos si en el futuro se define estilo para Secondary.
7. **Documentar estándares:** Añadir una sección “UI Standards” o “Design system” en ARCHITECTURE_RULES.md o en un doc DESIGN_SYSTEM.md con: spacing (7.1), botones (7.2), inputs (7.3), cards (7.4), diálogos (7.5), y criterio para file/folder picker, para que futuros cambios respeten la misma base.

---

**Fin del informe.** Este documento sirve como hoja de ruta para alcanzar una UI más consistente sin modificar la arquitectura ni los contratos existentes.
