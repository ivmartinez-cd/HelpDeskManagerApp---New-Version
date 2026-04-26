# Propuesta Técnica: Agente de Inteligencia y Análisis Local (AI-AL)

Este documento resume la estrategia para implementar capacidades de análisis inteligente en la aplicación HelpDesk Manager, optimizada para hardware de oficina estándar y sin dependencia de servicios en la nube o sobrecarga de recursos compartidos (NAS).

## 1. Visión y Objetivos
Transformar los datos históricos de contadores en información accionable para el equipo de Help Desk, permitiendo:
*   **Detección temprana de anomalías** (IPs cambiadas, falta de reportes).
*   **Mantenimiento predictivo** basado en tendencias de uso.
*   **Validación de insumos** (cruzar consumo real vs. pedidos registrados).
*   **Impacto cero en el usuario:** El operador no debe sentir lentitud en su PC (i5 9000 / 8GB RAM).

---

## 2. Estrategia de Hardware y Rendimiento
Dado que las terminales no son estaciones de trabajo de alta gama, se descarta el uso de Modelos de Lenguaje Grandes (LLMs) locales pesados en favor de **Machine Learning Liviano**:

*   **Motor de Análisis:** Uso de librerías estadísticas (`pandas`) y aprendizaje automático clásico (`scikit-learn`).
*   **Prioridad de Proceso:** Ejecución en hilos secundarios (`QThread`) con prioridad `Idle` o `LowestPriority`. 
*   **Consumo Estimado:** 
    *   **RAM:** < 50MB adicionales.
    *   **CPU:** Picos breves (< 1s) durante la descarga de nuevos datos.

---

## 3. Sistema de Caché Local Inteligente
Para evitar leer cientos de archivos del NAS cada vez, se implementará un sistema de caché persistente en la PC del operador.

### Estructura de Archivos
Ubicación: `pyside_ui/data/cache/`
Formato: `NOMBRE_DEL_CLIENTE.json`

### Contenido del Caché (Perfil de Comportamiento)
```json
{
  "cliente_id": "BANCO_Z",
  "ultimo_procesado": "2024-04-26 09:00",
  "perfil_uso": {
    "promedio_mensual": 12500,
    "desvio_estandar": 1200,
    "ip_habitual": "192.168.1.45"
  },
  "historico_resumido": [
    {"mes": "2024-01", "contador": 150000},
    {"mes": "2024-02", "contador": 162000}
  ],
  "alertas_pendientes": [
    "Cambio de IP detectado el 2024-04-20"
  ],
  "archivos_procesados": [
    "contador_20240425.ftp",
    "contador_20240426.ftp"
  ]
}
```

---

## 4. Casos de Uso Inteligentes

### A. Detector de "Impresora Fantasma" (Anomalía de Reporte)
Si el tiempo transcurrido desde el último reporte supera el promedio histórico del cliente en un margen crítico, el sistema marca a la impresora como "Posiblemente Desconectada".

### B. Gatillo de Auditoría para Estimaciones Prolongadas
En lugar de un análisis complejo, la app actuará como un monitor de integridad de la base de datos:
*   **Detección de "Estimación Estancada":** El sistema identifica impresoras que han sido "estimadas" por la aplicación durante **6 meses o más** sin recibir un reporte de contador real.
*   **Acción de la App (Sugerencia de Validación):** La app mostrará una sugerencia directa al operador:
    > 📋 **Validación Necesaria:** "Este equipo lleva 6 meses de estimación continua sin reportes reales. Por favor, verifique si el cliente realizó pedidos de insumos en este periodo para validar si se debe seguir estimando o si el equipo debe pasarse a 0 (fuera de servicio)."
*   **Objetivo:** Ayudar al operador a decidir el destino de los equipos "zombis" en la base de datos, basándose en su conocimiento de los pedidos manuales.
*   **Sin Sobrecarga:** No requiere conexiones externas ni procesos pesados; es un simple contador de tiempo desde el último dato real.

### C. Alerta de Cambio de Red
Si una impresora reporta desde una IP fuera de su rango habitual o máscara de red, se notifica para actualizar la gestión de activos o verificar si el equipo fue movido de sector.

---

## 5. Interfaz de Usuario y Notificaciones
Para que el sistema sea útil sin ser molesto, las sugerencias se presentarán de forma no intrusiva:

1.  **Indicadores de Estado (Semáforo):** En la lista de clientes/impresoras, un icono inteligente mostrará si hay una sugerencia pendiente.
2.  **Tarjetas de Sugerencia (Smart Cards):** Al seleccionar una impresora, aparecerá una tarjeta discreta con la recomendación de la IA.
3.  **Toasts Informativos:** Solo para anomalías críticas (ej: cambio de IP o caída de reporte prolongada).

---

## 6. Flujo de Trabajo (Pipeline)
1.  **Descarga FTP:** El sistema baja el archivo nuevo al NAS (como hasta ahora).
2.  **Trigger de Análisis:** La app detecta el nuevo archivo y lo lee localmente.
3.  **Actualización Delta:** Solo se procesa el archivo nuevo y se suma al `CLIENTE.json` local.
4.  **Inferencia:** El "Agente" compara el nuevo dato contra el perfil del caché.
5.  **Feedback:** Se actualiza el icono de estado en la UI de la aplicación.

---

## 6. Ventajas de este Enfoque
1.  **Privacidad:** Los perfiles de comportamiento no salen de la terminal del operador.
2.  **Escalabilidad:** No satura el NAS porque no requiere que el servidor procese nada; el trabajo se reparte entre las terminales de los operadores de forma pasiva.
3.  **Orden:** Al estar nombrado por cliente, el mantenimiento y depuración del sistema es intuitivo.
