from __future__ import annotations

import json
import logging
import multiprocessing
import os
import re
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QProcess, QTimer, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPixmap


APP_NAME = "HelpDesk Manager"
APP_FOLDER_NAME = "HelpDeskManagerApp"
LOG_FILE_NAME = "launcher_debug.log"
CRASH_FILE_NAME = "crash_launcher.txt"
NAS_DEFAULT_PATH = "J:/HelpDesk_Test_Server"
MINIMUM_SPLASH_MS = 4000
WINDOWS_APP_ID = "HelpDeskManagerApp.Launcher"
EXCLUDED_TREE_NAMES = {
    ".git",
    "build",
    "dist",
    "__pycache__",
    ".pytest_cache",
    "tests",
    "docs",
    ".claude",
}

FILE_ACTION_PREFIXES = (
    "New File",
    "Newer",
    "Older",
    "Changed",
    "Tweaked",
    "*EXTRA File",
)
DIR_ACTION_PREFIXES = (
    "New Dir",
    "*EXTRA Dir",
)
PROGRESS_PATTERN = re.compile(r"(?<!\d)(\d{1,3})(?:\.\d+)?%(?!\d)")


@dataclass(frozen=True)
class LauncherPaths:
    local_root: Path
    nas_root: Path
    local_version_file: Path
    nas_version_file: Path
    local_log_file: Path
    local_crash_file: Path
    source_entrypoint: Path


@dataclass(frozen=True)
class VersionInfo:
    raw: str

    @property
    def normalized(self) -> tuple[int, ...]:
        token = self.raw.strip().lower().lstrip("v")
        parts: list[int] = []
        for piece in token.split("."):
            if piece.isdigit():
                parts.append(int(piece))
            else:
                return tuple()
        return tuple(parts)

    def is_newer_than(self, other: "VersionInfo") -> bool:
        if self.normalized and other.normalized:
            width = max(len(self.normalized), len(other.normalized))
            left = self.normalized + (0,) * (width - len(self.normalized))
            right = other.normalized + (0,) * (width - len(other.normalized))
            return left > right
        return self.raw != other.raw


@dataclass(frozen=True)
class UpdateDecision:
    local_version: VersionInfo
    remote_version: VersionInfo | None
    update_required: bool
    online: bool
    first_install: bool
    message: str


@dataclass
class SyncStats:
    files_total: int = 0
    files_processed: int = 0
    dirs_total: int = 0
    dirs_processed: int = 0
    current_file: str = ""


def build_paths() -> LauncherPaths:
    local_app_data = Path(os.environ.get("LOCALAPPDATA", os.environ.get("APPDATA", ".")))
    local_root = local_app_data / APP_FOLDER_NAME
    nas_root = Path(os.environ.get("HELPDESK_NAS_PATH", NAS_DEFAULT_PATH))
    return LauncherPaths(
        local_root=local_root,
        nas_root=nas_root,
        local_version_file=local_root / "version.json",
        nas_version_file=nas_root / "version.json",
        local_log_file=local_root / LOG_FILE_NAME,
        local_crash_file=local_root / CRASH_FILE_NAME,
        source_entrypoint=Path(__file__).resolve(),
    )


def ensure_local_root(paths: LauncherPaths) -> None:
    paths.local_root.mkdir(parents=True, exist_ok=True)


def configure_logging(paths: LauncherPaths) -> None:
    ensure_local_root(paths)
    logging.basicConfig(
        filename=paths.local_log_file,
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        force=True,
    )


def load_version(path: Path, fallback: str = "0.0.0") -> VersionInfo:
    if not path.exists():
        return VersionInfo(fallback)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return VersionInfo(fallback)
    return VersionInfo(str(payload.get("version", fallback)))


def decide_update(paths: LauncherPaths) -> UpdateDecision:
    local_version = load_version(paths.local_version_file)
    first_install = not paths.local_version_file.exists()
    if not paths.nas_version_file.exists():
        return UpdateDecision(
            local_version=local_version,
            remote_version=None,
            update_required=False,
            online=False,
            first_install=first_install,
            message=f"Servidor no accesible. Abriendo copia local ({local_version.raw}).",
        )

    remote_version = load_version(paths.nas_version_file)
    if remote_version.is_newer_than(local_version):
        return UpdateDecision(
            local_version=local_version,
            remote_version=remote_version,
            update_required=True,
            online=True,
            first_install=first_install,
            message=f"Hay una nueva version disponible: {remote_version.raw}.",
        )

    return UpdateDecision(
        local_version=local_version,
        remote_version=remote_version,
        update_required=False,
        online=True,
        first_install=first_install,
        message=f"La instalacion local ya esta al dia ({local_version.raw}).",
    )


def local_app_ready(paths: LauncherPaths) -> bool:
    required = [
        paths.local_version_file,
        paths.local_root / "pyside_ui" / "app.py",
        paths.local_root / "pyside_ui" / "main_window.py",
        paths.local_root / "pyside_ui" / "assets" / "ico.png",
    ]
    return all(path.exists() for path in required)


def count_source_files(source: Path) -> int:
    if not source.exists():
        return 0
    total = 0
    for root, dirnames, filenames in os.walk(source):
        dirnames[:] = [name for name in dirnames if name not in EXCLUDED_TREE_NAMES]
        total += sum(1 for filename in filenames if filename not in EXCLUDED_TREE_NAMES)
    return total


def build_child_command(paths: LauncherPaths) -> list[str]:
    if getattr(sys, "frozen", False):
        return [sys.executable, "--run-app"]
    return [sys.executable, str(paths.source_entrypoint), "--run-app"]


def prepare_sys_path(paths: LauncherPaths) -> None:
    local_root = str(paths.local_root)
    if local_root not in sys.path:
        sys.path.insert(0, local_root)


def run_main_app(paths: LauncherPaths) -> int:
    prepare_sys_path(paths)
    try:
        import importlib

        module = importlib.import_module("pyside_ui.app")
        main_func = getattr(module, "main")
        return int(main_func())
    except Exception as exc:
        ensure_local_root(paths)
        err_msg = traceback.format_exc()
        paths.local_crash_file.write_text(err_msg, encoding="utf-8")
        logging.critical("Error fatal al iniciar la app: %s\n%s", exc, err_msg)

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
        QtWidgets.QMessageBox.critical(
            None,
            f"Error al iniciar {APP_NAME}",
            f"No se pudo iniciar la aplicacion.\n\nError: {exc}\n\nRevisa crash_launcher.txt para mas detalles.",
        )
        return 1


def load_launcher_icon() -> QPixmap:
    icon_path = Path(__file__).resolve().parent / "pyside_ui" / "assets" / "ico.png"
    if icon_path.exists():
        return QPixmap(str(icon_path))
    return QPixmap()


def load_launcher_qicon() -> QIcon:
    icon_path = Path(__file__).resolve().parent / "pyside_ui" / "assets" / "ico.png"
    if icon_path.exists():
        return QIcon(str(icon_path))
    return QIcon()


def set_windows_appusermodelid(app_id: str) -> None:
    if os.name != "nt":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        logging.exception("No se pudo configurar AppUserModelID")


def build_robocopy_args(source: Path, destination: Path, list_only: bool = False) -> list[str]:
    args = [
        str(source),
        str(destination),
        "/MIR",
        "/MT:8",
        "/R:3",
        "/W:3",
        "/ETA",
        "/TEE",
        "/BYTES",
        "/XJ",
        "/XD",
        ".git",
        "build",
        "dist",
        "__pycache__",
        ".pytest_cache",
        "tests",
        "docs",
        ".claude",
    ]
    if list_only:
        return ["robocopy", *args, "/L", "/NJH", "/NJS"]
    return ["robocopy", *args, "/NJH"]


def strip_robocopy_prefix(line: str, prefixes: tuple[str, ...]) -> str:
    for prefix in prefixes:
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return line.strip()


def parse_robocopy_line(stats: SyncStats, line: str, list_only: bool) -> tuple[str | None, str | None, int | None]:
    raw = line.strip()
    if not raw:
        return None, None, None

    if raw.startswith(FILE_ACTION_PREFIXES):
        stats.current_file = strip_robocopy_prefix(raw, FILE_ACTION_PREFIXES)
        if list_only:
            stats.files_total += 1
        else:
            stats.files_processed += 1
        return "file", stats.current_file, None

    if raw.startswith(DIR_ACTION_PREFIXES):
        folder = strip_robocopy_prefix(raw, DIR_ACTION_PREFIXES)
        if list_only:
            stats.dirs_total += 1
        else:
            stats.dirs_processed += 1
        return "dir", folder, None

    match = PROGRESS_PATTERN.search(raw)
    if match:
        return "progress", stats.current_file or "Copiando archivos...", int(match.group(1))

    if raw.lower().startswith("files :"):
        return "summary", raw, None
    if raw.lower().startswith("dirs :"):
        return "summary", raw, None
    if raw.lower().startswith("bytes :"):
        return "summary", raw, None
    return "info", raw, None


class LauncherWindow(QtWidgets.QWidget):
    def __init__(self, paths: LauncherPaths):
        super().__init__()
        self.paths = paths
        self._fade = QPropertyAnimation(self, b"windowOpacity")
        self._elapsed = QtCore.QElapsedTimer()
        self._child_started = False
        self._sync_process: QProcess | None = None
        self._sync_stats = SyncStats()
        self._sync_buffer = ""
        self._pending_version = ""
        self._pending_child_cmd: list[str] | None = None

        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(580, 400)
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(load_launcher_qicon())

        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(14, 14, 14, 14)

        self.card = QtWidgets.QFrame()
        self.card.setObjectName("card")
        self.card.setStyleSheet(
            """
            #card {
                background: #121212;
                border: 1px solid #2a2a2a;
                border-radius: 22px;
            }
            QFrame#heroSurface {
                background: #121212;
                border: none;
            }
            QFrame#miniCard {
                background: #1e1e1e;
                border: 1px solid #2a2a2a;
                border-radius: 18px;
            }
            QLabel#runtime {
                color: #6cb6ff;
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 1px;
            }
            QLabel#heroTitle {
                color: #ff9a2e;
                font-size: 28px;
                font-weight: 800;
            }
            QLabel#heroSubtitle {
                color: #9ca3af;
                font-size: 10px;
                font-weight: 500;
                letter-spacing: 2px;
            }
            QLabel#sectionTitle {
                color: #6cb6ff;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 1px;
            }
            QLabel#cardTitle {
                color: #f5f5f5;
                font-size: 14px;
                font-weight: 700;
            }
            QLabel#cardBody, QLabel#status {
                color: #9ca3af;
                font-size: 13px;
            }
            QLabel#logLine {
                color: #f5f5f5;
                font-size: 12px;
                font-weight: 700;
            }
            QLabel#footnote {
                color: #7b8591;
                font-size: 11px;
            }
            QProgressBar {
                background: #252525;
                border: none;
                border-radius: 6px;
                min-height: 8px;
            }
            QProgressBar::chunk {
                border-radius: 6px;
                background: #ff9a2e;
            }
            """
        )
        outer.addWidget(self.card)

        layout = QtWidgets.QVBoxLayout(self.card)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        runtime = QtWidgets.QLabel("2026 LAUNCHER RUNTIME")
        runtime.setObjectName("runtime")
        layout.addWidget(runtime)

        hero = QtWidgets.QFrame()
        hero.setObjectName("heroSurface")
        hero_layout = QtWidgets.QHBoxLayout(hero)
        hero_layout.setContentsMargins(0, 4, 0, 0)
        hero_layout.setSpacing(18)

        icon_label = QtWidgets.QLabel()
        icon_label.setFixedSize(48, 48)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_pixmap = load_launcher_icon()
        if not icon_pixmap.isNull():
            icon_label.setPixmap(icon_pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            icon_label.setText("HD")
            icon_label.setStyleSheet("color: #ff9a2e; font-size: 22px; font-weight: 800;")
        hero_layout.addWidget(icon_label, 0, Qt.AlignTop)

        hero_text = QtWidgets.QVBoxLayout()
        hero_text.setSpacing(4)

        title = QtWidgets.QLabel("HELPDESK MANAGER")
        title.setObjectName("heroTitle")
        title_font = QFont("Outfit", 28, QFont.Weight.Bold)
        title_font.setPointSizeF(28)
        title.setFont(title_font)
        hero_text.addWidget(title)

        subtitle = QtWidgets.QLabel("PLATAFORMA DE GESTION • OPERACIONES")
        subtitle.setObjectName("heroSubtitle")
        subtitle_font = QFont("Segoe UI", 9)
        subtitle_font.setPointSizeF(8.5)
        subtitle.setFont(subtitle_font)
        hero_text.addWidget(subtitle)
        hero_text.addStretch(1)

        hero_layout.addLayout(hero_text, 1)
        layout.addWidget(hero)

        section = QtWidgets.QLabel("INICIALIZACION DEL SISTEMA")
        section.setObjectName("sectionTitle")
        layout.addWidget(section)

        mini_card = QtWidgets.QFrame()
        mini_card.setObjectName("miniCard")
        mini_layout = QtWidgets.QVBoxLayout(mini_card)
        mini_layout.setContentsMargins(20, 18, 20, 18)
        mini_layout.setSpacing(12)

        self.card_title = QtWidgets.QLabel("Preparando lanzamiento")
        self.card_title.setObjectName("cardTitle")
        mini_layout.addWidget(self.card_title)

        self.card_body = QtWidgets.QLabel("Verificacion de version, sincronizacion NAS y arranque protegido.")
        self.card_body.setObjectName("cardBody")
        self.card_body.setWordWrap(True)
        self.card_body.setMinimumHeight(44)
        self.card_body.setMaximumHeight(44)
        self.card_body.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        mini_layout.addWidget(self.card_body)

        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(8)
        self.progress.setTextVisible(False)
        mini_layout.addWidget(self.progress)

        self.log_label = QtWidgets.QLabel("Esperando verificacion inicial...")
        self.log_label.setObjectName("logLine")
        self.log_label.setWordWrap(True)
        self.log_label.setMinimumHeight(36)
        self.log_label.setMaximumHeight(36)
        self.log_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        mini_layout.addWidget(self.log_label)

        self.status_label = QtWidgets.QLabel("Preparando entorno local...")
        self.status_label.setObjectName("status")
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(38)
        self.status_label.setMaximumHeight(38)
        self.status_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        mini_layout.addWidget(self.status_label)

        layout.addWidget(mini_card)

        self.detail_label = QtWidgets.QLabel(self.compact_path(str(self.paths.local_root)))
        self.detail_label.setObjectName("footnote")
        self.detail_label.setWordWrap(True)
        layout.addWidget(self.detail_label)

        shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 12)
        shadow.setColor(QColor(0, 0, 0, 180))
        self.card.setGraphicsEffect(shadow)

        self.setWindowOpacity(0.0)
        self._fade.setDuration(280)
        self._fade.setEasingCurve(QEasingCurve.OutCubic)
        self._fade.setStartValue(0.0)
        self._fade.setEndValue(1.0)
        self._elapsed.start()

        QTimer.singleShot(0, self._fade.start)
        QTimer.singleShot(120, self.begin)

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        super().showEvent(event)
        self.raise_()
        self.activateWindow()

    @staticmethod
    def compact_path(value: str, max_len: int = 58) -> str:
        if len(value) <= max_len:
            return value
        keep = max_len - 3
        left = keep // 2
        right = keep - left
        return f"{value[:left]}...{value[-right:]}"

    def set_step(self, progress: int, text: str, detail: str | None = None) -> None:
        if self.progress.minimum() == 0 and self.progress.maximum() == 0:
            self.progress.setRange(0, 100)
        self.progress.setValue(max(0, min(100, progress)))
        self.log_label.setText(text)
        if detail is not None:
            self.status_label.setText(detail)
        QtWidgets.QApplication.processEvents()

    def set_busy_state(self, title: str, body: str, text: str, detail: str) -> None:
        self.card_title.setText(title)
        self.card_body.setText(body)
        self.log_label.setText(text)
        self.status_label.setText(detail)
        self.progress.setRange(0, 0)
        QtWidgets.QApplication.processEvents()

    def begin(self) -> None:
        logging.info("Launcher started. frozen=%s", getattr(sys, "frozen", False))
        self.set_step(12, "Verificando version local y conectividad con el NAS...", "Comprobando cache local y servidor de actualizaciones.")

        try:
            decision = decide_update(self.paths)
            logging.info(
                "Update decision | online=%s | local=%s | remote=%s | update_required=%s | first_install=%s",
                decision.online,
                decision.local_version.raw,
                decision.remote_version.raw if decision.remote_version else "n/a",
                decision.update_required,
                decision.first_install,
            )
        except Exception as exc:
            logging.exception("No se pudo evaluar el estado de actualizacion")
            self.finish_and_launch(f"Fallo la verificacion de version. Se abre la copia local. ({exc})")
            return

        if decision.update_required:
            self._pending_version = decision.remote_version.raw if decision.remote_version else "n/a"
            if decision.first_install:
                self.card_title.setText("Descargando primera instalacion")
                self.card_body.setText("No existe una copia local todavia. Vamos a copiar todos los archivos iniciales desde el NAS.")
                self.set_step(20, f"Preparando descarga inicial de la version {self._pending_version}...", "Conectando con el NAS y preparando la copia inicial.")
            else:
                self.card_title.setText("Actualizando instalacion local")
                self.card_body.setText("Se copiaran solo los cambios necesarios antes de abrir el sistema.")
                self.set_step(20, f"Preparando actualizacion a la version {self._pending_version}...", "Conectando con el NAS y preparando la sincronizacion.")
            self.start_robocopy_copy()
            return

        self.finish_and_launch(decision.message)

    def start_robocopy_copy(self) -> None:
        self._sync_stats = SyncStats()
        self._sync_buffer = ""
        self.progress.setRange(0, 100)
        self.progress.setValue(25)
        source = self.paths.nas_root / "app"
        self._sync_stats.files_total = max(1, count_source_files(source))
        self.status_label.setText(f"Descargando version {self._pending_version}...")
        self.log_label.setText(f"Preparando copia de {self._sync_stats.files_total} archivos con robocopy...")
        self.start_robocopy_process()

    def start_robocopy_process(self) -> None:
        ensure_local_root(self.paths)
        source = self.paths.nas_root / "app"
        if not source.exists():
            self.on_sync_failed("La carpeta de actualizacion del NAS no existe.")
            return

        if self._sync_process is not None:
            self._sync_process.deleteLater()

        self._sync_buffer = ""
        process = QProcess(self)
        process.setProgram("robocopy")
        process.setArguments(build_robocopy_args(source, self.paths.local_root, list_only=False)[1:])
        process.setProcessChannelMode(QProcess.MergedChannels)
        process.readyReadStandardOutput.connect(self.on_robocopy_output)
        process.finished.connect(self.on_robocopy_finished)
        process.errorOccurred.connect(self.on_robocopy_error)
        self._sync_process = process
        logging.info("Starting robocopy copy args=%s", process.arguments())
        process.start()

    def on_robocopy_output(self) -> None:
        if self._sync_process is None:
            return
        chunk = bytes(self._sync_process.readAllStandardOutput()).decode("utf-8", errors="ignore")
        if not chunk:
            return
        logging.info("robocopy chunk: %s", chunk.strip())
        self._sync_buffer += chunk.replace("\r", "\n")
        while "\n" in self._sync_buffer:
            line, self._sync_buffer = self._sync_buffer.split("\n", 1)
            self.handle_robocopy_line(line.strip())

    def handle_robocopy_line(self, line: str) -> None:
        if not line:
            return
        event, payload, percent = parse_robocopy_line(self._sync_stats, line, list_only=False)

        if event == "file":
            total = max(self._sync_stats.files_total, self._sync_stats.files_processed, 1)
            self._sync_stats.files_total = total
            ratio = self._sync_stats.files_processed / total
            progress = 30 + int(ratio * 60)
            filename = Path(payload or "").name or payload or "archivo"
            self.set_step(progress, f"Copiando archivos ({self._sync_stats.files_processed}/{total})...", f"Archivo actual: {filename}")
            return

        if event == "dir":
            folder = payload or "carpeta"
            self.status_label.setText(f"Chequeando carpeta: {folder}")
            return

        if event == "progress":
            total = max(self._sync_stats.files_total, self._sync_stats.files_processed, 1)
            self._sync_stats.files_total = total
            completed_files = max(0, self._sync_stats.files_processed - 1)
            ratio = (completed_files + ((percent or 0) / 100.0)) / total
            progress = 30 + int(ratio * 60)
            label = Path(payload or "").name or payload or "Copiando archivos..."
            self.progress.setValue(max(0, min(100, progress)))
            self.status_label.setText(f"Archivo actual: {label}")
            return

        if event in {"info", "summary"}:
            self.status_label.setText(payload or line)

    def on_robocopy_finished(self, exit_code: int, _exit_status: QtCore.QProcess.ExitStatus) -> None:
        process = self._sync_process
        self._sync_process = None
        if self._sync_buffer.strip():
            self.handle_robocopy_line(self._sync_buffer.strip())
            self._sync_buffer = ""

        logging.info("robocopy finished | exit_code=%s", exit_code)
        if process is not None:
            process.deleteLater()

        if exit_code >= 8:
            self.on_sync_failed(f"Robocopy fallo con codigo {exit_code}.")
            return

        if not local_app_ready(self.paths):
            self.on_sync_failed("La descarga termino, pero faltan archivos base en la copia local.")
            return

        self.card_title.setText("Sincronizacion completada")
        self.card_body.setText("Los archivos locales quedaron listos para abrir la aplicacion.")
        copied = self._sync_stats.files_processed
        total = self._sync_stats.files_total
        if copied <= 0:
            self.finish_and_launch(f"Sincronizacion completada. Instalacion base verificada sobre {total} archivos.")
            return
        self.finish_and_launch(f"Sincronizacion completada. Archivos procesados: {copied} de {total}.")

    def on_robocopy_error(self, error: QProcess.ProcessError) -> None:
        self.on_sync_failed(f"No se pudo ejecutar robocopy ({error}).")

    def on_sync_failed(self, detail: str) -> None:
        logging.warning("Sync failed: %s", detail)
        self.card_title.setText("Sincronizacion no disponible")
        self.card_body.setText("No se pudo completar la descarga. Vamos a revisar si existe una copia local utilizable.")
        self.log_label.setText("No se pudo completar la sincronizacion.")
        self.status_label.setText(detail)
        if local_app_ready(self.paths):
            self.finish_and_launch(f"{detail} Se intentara abrir la copia local.")
            return
        self.finish_and_launch(f"{detail} Se abrira la version integrada del launcher.")

    def finish_and_launch(self, text: str) -> None:
        self.set_step(100, text, self.log_label.text())
        remaining_ms = max(0, MINIMUM_SPLASH_MS - self._elapsed.elapsed())
        QTimer.singleShot(remaining_ms, self.begin_fade_and_launch)

    def begin_fade_and_launch(self) -> None:
        if self._child_started:
            return
        self._child_started = True
        self._pending_child_cmd = build_child_command(self.paths)
        self._fade.finished.connect(self.start_child_after_fade)
        self._fade.setDirection(QPropertyAnimation.Backward)
        self._fade.start()

    def start_child_after_fade(self) -> None:
        if not self._pending_child_cmd:
            QtWidgets.QApplication.quit()
            return

        cmd = self._pending_child_cmd
        workdir = str(self.paths.local_root if self.paths.local_root.exists() else Path.cwd())
        logging.info("Launching child process after fade: %s | cwd=%s", cmd, workdir)
        ok = QProcess.startDetached(cmd[0], cmd[1:], workdir)
        if not ok:
            logging.error("No se pudo iniciar la aplicacion principal con startDetached")
            QtWidgets.QMessageBox.critical(
                self,
                f"Error al iniciar {APP_NAME}",
                "No se pudo iniciar la aplicacion principal despues de la sincronizacion.",
            )
        QtWidgets.QApplication.quit()


def show_launcher(paths: LauncherPaths) -> int:
    set_windows_appusermodelid(WINDOWS_APP_ID)
    app = QtWidgets.QApplication(sys.argv)
    font = QFont("Segoe UI Variable Text", 10)
    font.setPointSizeF(10)
    app.setFont(font)
    app.setApplicationDisplayName(APP_NAME)
    icon = load_launcher_qicon()
    if not icon.isNull():
        app.setWindowIcon(icon)

    win = LauncherWindow(paths)
    screen = app.primaryScreen()
    if screen is not None:
        geometry = screen.availableGeometry()
        win.move(geometry.center() - win.rect().center())
    win.show()
    return app.exec()


def main() -> int:
    multiprocessing.freeze_support()
    paths = build_paths()
    configure_logging(paths)

    if "--run-app" in sys.argv:
        return run_main_app(paths)

    try:
        return show_launcher(paths)
    except Exception:
        ensure_local_root(paths)
        err_msg = traceback.format_exc()
        paths.local_crash_file.write_text(err_msg, encoding="utf-8")
        logging.critical("Error fatal en el launcher\n%s", err_msg)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
