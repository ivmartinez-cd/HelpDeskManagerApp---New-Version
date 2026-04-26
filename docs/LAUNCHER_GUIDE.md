# 🚀 Guía del Sistema de Smart Launcher y Actualizaciones (v2.0.6)

Esta guía explica cómo funciona el sistema de distribución de **HelpDesk Manager 2026** diseñado para entornos de red con NAS.

## 📂 Componentes del Sistema

1.  **`HelpDeskLauncher.exe`**: El ejecutable estable que entregas al usuario. Se encuentra en `dist/HelpDeskLauncher`.
2.  **`_internal/`**: Carpeta que acompaña al EXE y contiene el motor de Python y las librerías (`PySide6`, `pandas`, etc.).
3.  **`deploy.py`**: Herramienta del administrador para publicar nuevas versiones. Incrementa la versión (ej: `2.0.5 -> 2.0.6`).
4.  **`AppData/Local/HelpDeskManagerApp`**: Carpeta oculta en el PC del usuario donde se descarga el código actualizado del NAS.

---

## 🛠️ Cómo funciona la Auto-Actualización

El sistema separa el **Motor** (el EXE) de la **Lógica** (los archivos .py). Esto permite actualizar la app sin tener que reenviar el archivo `.exe` a los usuarios.

1.  El usuario abre `HelpDeskLauncher.exe`.
2.  El lanzador mira en el **NAS** si hay una versión superior en `version.json`.
3.  Si la hay, descarga solo los archivos modificados a `%LOCALAPPDATA%/HelpDeskManagerApp`.
4.  El lanzador arranca la app usando ese código actualizado.

---

## 🚀 Cómo Desplegar una Nueva Versión (Tu flujo de trabajo)

Cuando hayas hecho cambios en el código (en la carpeta `pyside_ui/`):

1.  Abre una terminal en la carpeta del proyecto.
2.  Ejecuta: `python deploy.py`.
3.  El script hará lo siguiente:
    *   Incrementará la versión (ej: de `2.0.6` a `2.0.7`).
    *   Subirá el código al NAS.
    *   **¡Listo!** La próxima vez que un usuario abra su lanzador, verá el aviso de actualización.

---

## 📦 Cuándo reconstruir el Lanzador (EXE)

Solo necesitas ejecutar `python build_launcher.py` si:
- Instalas una **nueva librería** de Python que la app no usaba antes.
- Quieres cambiar el **Icono** del archivo `.exe`.
- Quieres cambiar el nombre del ejecutable.

Para cambios en la interfaz o lógica, **SOLO necesitas usar `deploy.py`**.

---

## ⚠️ Solución de Problemas y Logs

Si algo falla, revisa estos archivos en `%LOCALAPPDATA%/HelpDeskManagerApp`:
- **`launcher_debug.log`**: Registro de lo que hizo el lanzador.
- **`crash_launcher.txt`**: Error fatal si el lanzador no puede ni siquiera arrancar.
- **`crash_app.txt`**: Error fatal dentro de la aplicación principal.

---
*Documentación actualizada para HelpDesk Manager v2.0.6*
