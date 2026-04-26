# launcher.py
from __future__ import annotations
import sys
import json
import os
import shutil
import subprocess
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QSize
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar, QGraphicsDropShadowEffect
from PySide6.QtGui import QColor, QFont, QPixmap, QIcon
import logging
import multiprocessing

# Definir ruta local de datos (AppData/Local)
LOCAL_APP_DATA = Path(os.environ.get('LOCALAPPDATA', os.environ.get('APPDATA', '.')))
LOCAL_ROOT = LOCAL_APP_DATA / "HelpDeskManagerApp"

# Asegurar que el directorio local existe antes de loguear
if not LOCAL_ROOT.exists():
    try:
        LOCAL_ROOT.mkdir(parents=True, exist_ok=True)
    except:
        pass

# Configuración de log de emergencia para el lanzador
logging.basicConfig(
    filename=str(LOCAL_ROOT / "launcher_debug.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

NAS_PATH = Path("J:/HelpDesk_Test_Server") # Ejemplo: Disco mapeado o UNC //servidor/nas1/...
# =============================================================================

def resource_path(relative_path):
    """ Obtiene la ruta absoluta de los recursos, compatible con PyInstaller EXE """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def is_newer(remote_v, local_v) -> bool:
    """ Compara versiones en formato string (ej: '2.0.1') o int """
    try:
        r_parts = [int(p) for p in str(remote_v).split('.')]
        l_parts = [int(p) for p in str(local_v).split('.')]
        # Rellenar con ceros si tienen longitudes distintas (ej: '2' vs '2.0.1')
        max_len = max(len(r_parts), len(l_parts))
        r_parts.extend([0] * (max_len - len(r_parts)))
        l_parts.extend([0] * (max_len - len(l_parts)))
        return r_parts > l_parts
    except:
        # Fallback a comparación de strings si algo falla
        return str(remote_v) > str(local_v)

class SmartLauncher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(450, 320)

        # UI Layout
        self.container = QWidget(self)
        self.container.setFixedSize(450, 320)
        self.container.setStyleSheet("""
            QWidget {
                background: #1A1A1A;
                border: 2px solid #333333;
                border-radius: 24px;
            }
        """)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(50)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 200))
        self.container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(24)

        # Icono / Logo con Glow Naranja
        self.logo = QLabel()
        icon_path = resource_path("pyside_ui/assets/ico.png")
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo.setPixmap(pix)
        else:
            self.logo.setText("HDM")
            self.logo.setStyleSheet("font-size: 32px; font-weight: 900; color: #FF9A2E; background: transparent; border: none;")
        self.logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.logo)

        # Título
        self.title = QLabel("HelpDesk Manager")
        font_t = QFont("Outfit", 20, QFont.Weight.Bold)
        font_t.setPointSizeF(20)
        self.title.setFont(font_t)
        self.title.setStyleSheet("color: #FFFFFF; background: transparent; border: none;")
        self.title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title)

        # Estado con mejor visibilidad
        self.status = QLabel("Sincronizando...")
        font_s = QFont("Inter", 10)
        font_s.setPointSizeF(10)
        self.status.setFont(font_s)
        self.status.setStyleSheet("color: #FF9A2E; background: transparent; border: none;")
        self.status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status)

        # Barra de Progreso más visible
        self.progress = QProgressBar()
        self.progress.setFixedHeight(6)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                background: #2D2D2D;
                border: none;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF9A2E, stop:1 #FF6B00);
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress)
        self.progress.setRange(0, 0)

        # Animación de entrada
        self.setWindowOpacity(0)
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(600)
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.start()

        # Iniciar lógica con delay para evitar race conditions
        QTimer.singleShot(1500, self.check_updates)

    def check_updates(self):
        # Asegurar que el directorio local de la app existe
        if not LOCAL_ROOT.exists():
            try:
                LOCAL_ROOT.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logging.error(f"No se pudo crear LOCAL_ROOT: {e}")

        local_version_file = LOCAL_ROOT / "version.json"
        remote_version_file = NAS_PATH / "version.json"

        # 1. ¿Existe el NAS?
        if not NAS_PATH.exists():
            self.launch_app("Servidor no accesible. Iniciando versión local...")
            return

        # 2. Leer versión local
        try:
            with open(local_version_file, "r") as f:
                local_data = json.load(f)
        except:
            local_data = {"version": 0}

        # 3. Leer versión remota
        try:
            with open(remote_version_file, "r") as f:
                remote_data = json.load(f)
        except:
            self.launch_app("Error al leer servidor. Iniciando local...")
            return

        # 4. Comparar usando el helper
        if is_newer(remote_data.get("version", "0"), local_data.get("version", "0")):
            self.status.setText(f"Nueva versión encontrada (v{remote_data['version']}). Actualizando...")
            self.progress.setRange(0, 100)
            QTimer.singleShot(500, lambda: self.perform_update(remote_data))
        else:
            self.launch_app("Sistema actualizado. Iniciando...")

    def perform_update(self, remote_data):
        try:
            remote_app_dir = NAS_PATH / "app"
            local_app_dir = LOCAL_ROOT
            
            # Comando robocopy para sincronizar
            # Excluimos version.json (lo actualizamos al final) y los archivos de sistema/lanzador
            cmd = [
                "robocopy", str(remote_app_dir), str(local_app_dir),
                "/E", "/Z", "/R:5", "/W:5", "/MT:8",
                "/XF", "version.json", "launcher.py", "deploy.py", "HelpDeskLauncher.exe", "icon.ico", "version_info.txt"
            ]
            
            # Ejecutar robocopy
            # Robocopy exit codes: 0-7 are success/no-change, 8+ are errors
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            logging.info(f"Robocopy exit code: {result.returncode}")
            
            if result.returncode >= 8:
                logging.error(f"Robocopy failed: {result.stderr}")
                raise RuntimeError(f"Error de sincronización (Code {result.returncode})")
            
            # Actualizar version.json local (esto es lo que detiene el bucle)
            local_version_file = LOCAL_ROOT / "version.json"
            with open(local_version_file, "w") as f:
                json.dump(remote_data, f, indent=4)
            
            self.progress.setValue(100)
            self.launch_app("Actualización completada.")
        except Exception as e:
            self.launch_app(f"Error en actualización: {e}")

    def launch_app(self, msg):
        self.status.setText(msg)
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        QTimer.singleShot(800, self.start_main_process)

    def start_main_process(self):
        # Ejecutar la app principal usando el mismo ejecutable con el flag --main-app
        # Esto evita el bucle y usa el entorno ya cargado del EXE
        try:
            logging.info("Iniciando aplicación principal con flag --main-app")
            subprocess.Popen([sys.executable, "--main-app"])
        except Exception as e:
            logging.error(f"No se pudo iniciar la aplicación principal: {e}")
            # Fallback a script si no estamos congelados
            if not getattr(sys, 'frozen', False):
                main_script = Path(__file__).parent / "run_pyside_ui.py"
                subprocess.Popen([sys.executable, str(main_script)])
        
        # Animación de salida y cierre
        self.anim.setDirection(QPropertyAnimation.Backward)
        self.anim.finished.connect(QApplication.quit)
        self.anim.start()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    
    # BLINDAJE ANTI-BUCLE: Si se pide iniciar la app, saltamos el lanzador
    if "--main-app" in sys.argv:
        logging.info("Modo --main-app detectado. Saltando lanzador e iniciando App.")
        
        # Asegurar que el directorio LOCAL_ROOT está en sys.path para cargar pyside_ui externo
        if getattr(sys, 'frozen', False):
            if str(LOCAL_ROOT) not in sys.path:
                sys.path.insert(0, str(LOCAL_ROOT))
        
        try:
            import importlib
            module = importlib.import_module("pyside_ui.app")
            main = getattr(module, "main")
            sys.exit(main())
        except Exception as e:
            logging.critical(f"Error fatal al iniciar la app desde el lanzador: {e}")
            crash_file = LOCAL_ROOT / "crash_launcher.txt"
            with open(crash_file, "w") as f:
                import traceback
                f.write(traceback.format_exc())
            sys.exit(1)

    app = QApplication(sys.argv)
    
    # Blindaje de fuente para el launcher
    font = QFont("Segoe UI", 10)
    font.setPointSizeF(10)
    app.setFont(font)
    
    try:
        launcher = SmartLauncher()
        # Centrar en pantalla
        screen = app.primaryScreen().geometry()
        launcher.move(screen.center() - launcher.rect().center())
        launcher.show()
        sys.exit(app.exec())
    except Exception as e:
        logging.critical(f"Error en la UI del lanzador: {e}")
        sys.exit(1)
