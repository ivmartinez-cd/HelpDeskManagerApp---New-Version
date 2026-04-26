# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the App

```bash
# Direct launch (development)
python run_pyside_ui.py

# Smart launcher with auto-update via NAS
python launcher.py

# Windows end-user executable (after build)
dist/HelpDeskLauncher/HelpDeskLauncher.exe
```

## Build & Deploy Commands

```bash
# 1. Build the launcher EXE (only needed if adding new libraries or changing icons)
python build_launcher.py

# 2. Deploy a new version to NAS (semantic versioning v2.0.x)
python deploy.py
```

## Testing

```bash
# Run all tests
pytest

# Run a single test file
pytest tests/test_logic.py
```

Tests live in `tests/`. `pytest.ini` sets `qt_api = pyside6`.

## Dependencies

Core runtime dependency is **PySide6**. Additional packages: `pandas`, `numpy`, `openpyxl`, `Pillow`, `scapy`, `geopy`, `requests`.

## Architecture

The app is a PySide6 desktop tool with a **Smart Launcher** architecture:

```
HelpDeskLauncher.exe           ← Stable bootloader (onedir mode)
_internal/                     ← Bundled Python environment & libraries
pyside_ui/                     ← Dynamic app code (synced to AppData/Local)
  app.py                       ← Main entry point, single-instance lock
  main_window.py               ← MainWindow (frameless, titlebar, tab switcher)
  tabs/, controllers/, core/   ← Logic layers
version.json                   ← Semantic version marker (e.g., "2.0.6")
```

### Key patterns

- **NAS Sync**: `deploy.py` pushes code to NAS. `launcher.py` pulls from NAS to `%LOCALAPPDATA%/HelpDeskManagerApp`.
- **Dynamic Loading**: Launcher injects AppData into `sys.path` and loads `pyside_ui.app` at runtime.
- **Signal/Slot**: `StatusBus` broadcasts status updates across the app.
- **Theming**: `theme/theme.py` exports `DARK_THEME` and `LIGHT_THEME`.

See `docs/LAUNCHER_GUIDE.md` for the full deployment workflow.
