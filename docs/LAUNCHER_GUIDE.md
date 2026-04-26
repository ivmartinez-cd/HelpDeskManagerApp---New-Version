# Guia del Sistema de Launcher y Actualizaciones (2026)

Esta guia describe el launcher actual de **HelpDesk Manager 2026** para entornos con NAS, cache local y tolerancia a modo offline.

## Componentes del sistema

1. **`HelpDeskLauncher.exe`**: ejecutable estable que entregas al usuario. Vive en `dist/HelpDeskLauncher`.
2. **`_internal/`**: runtime empaquetado por PyInstaller.
3. **`launcher.py`**: implementacion real del launcher.
4. **`HelpDeskLauncher.py`**: entrypoint fino para PyInstaller.
5. **`deploy.py`**: publica nuevas versiones en el NAS.
6. **`%LOCALAPPDATA%/HelpDeskManagerApp`**: cache local con la version descargada.

## Como funciona la autoactualizacion

El sistema separa el runtime del codigo actualizable. Esto permite publicar cambios frecuentes sin redistribuir el `.exe` en cada iteracion.

1. El usuario abre `HelpDeskLauncher.exe`.
2. El launcher verifica `version.json` en el NAS.
3. Si encuentra una version mas nueva, sincroniza `NAS/app -> %LOCALAPPDATA%/HelpDeskManagerApp` usando `robocopy`.
4. Si el NAS no responde, abre la copia local.
5. Si no existe una copia local valida, el build puede arrancar la version embebida de `pyside_ui`.

## Como desplegar una nueva version

1. Abre una terminal en la carpeta del proyecto.
2. Ejecuta `python deploy.py`.
3. El script incrementa `version.json`, publica el codigo en el NAS y luego copia el `version.json` raiz como disparador de actualizacion.

## Cuando reconstruir el launcher

Ejecuta `python build_launcher.py` cuando:

- agregues nuevas dependencias del runtime
- cambies icono o branding del `.exe`
- modifiques el propio launcher

Para cambios solo en la UI o logica de `pyside_ui`, normalmente alcanza con `deploy.py`.

## Logs y diagnostico

Si algo falla, revisa estos archivos en `%LOCALAPPDATA%/HelpDeskManagerApp`:

- `launcher_debug.log`: decisiones del launcher, sync y arranque.
- `crash_launcher.txt`: fallo fatal en bootstrap.
- `crash_app.txt`: fallo fatal dentro de la app principal.

Este launcher prioriza arranque confiable, trazabilidad y recuperacion offline.
