# deploy.py
import json
import shutil
import os
import subprocess
from pathlib import Path

# =============================================================================
# CONFIGURACIÓN DEL NAS (Debe coincidir con launcher.py)
# =============================================================================
NAS_PATH = Path("J:/HelpDesk_Test_Server")
# =============================================================================

def increment_version(v_str):
    """ Incrementa el último número de una versión tipo '2.0.1' o '2' """
    parts = str(v_str).split('.')
    try:
        parts[-1] = str(int(parts[-1]) + 1)
        return '.'.join(parts)
    except:
        return str(v_str) + ".1"

def deploy():
    local_dir = Path(__file__).parent
    local_version_file = local_dir / "version.json"
    
    print("Iniciando despliegue de HelpDesk Manager 2026...")

    # 1. Leer y actualizar versión local
    try:
        with open(local_version_file, "r") as f:
            data = json.load(f)
        
        old_v = data.get("version", "0")
        data["version"] = increment_version(old_v)
        data["last_update"] = str(Path().stat().st_mtime) # o fecha actual
        
        with open(local_version_file, "w") as f:
            json.dump(data, f, indent=4)
        
        print(f"Versión incrementada: v{old_v} -> v{data['version']}")
    except Exception as e:
        print(f"Error actualizando version.json: {e}")
        return

    # 2. Preparar NAS
    if not NAS_PATH.parent.exists():
        print(f"ERROR: El NAS ({NAS_PATH}) no parece estar accesible.")
        return

    nas_app_dir = NAS_PATH / "app"
    nas_version_file = NAS_PATH / "version.json"

    try:
        if not NAS_PATH.exists():
            print(f"Creando directorio raíz en NAS: {NAS_PATH}")
            NAS_PATH.mkdir(parents=True)
        if not nas_app_dir.exists():
            nas_app_dir.mkdir(parents=True)

        print(f"Sincronizando archivos con el NAS (usando Robocopy)...")
        
        # Usamos robocopy para un despliegue más profesional y rápido
        # /MIR: Mirroring (borra en destino si no existe en origen)
        # /XF: Excluir archivos
        # /XD: Excluir directorios
        cmd = [
            "robocopy", str(local_dir), str(nas_app_dir),
            "/MIR", "/MT:8", "/R:5", "/W:5",
            "/XF", "deploy.py", "launcher_debug.log", "crash_app.txt", "log_ventanas.txt",
            "/XD", "__pycache__", ".git", ".pytest_cache", "tests", "docs", ".gemini", "build", "dist", "HelpDeskLauncher"
        ]
        
        # Robocopy exit codes < 8 are considered success in this context
        result = subprocess.run(cmd, shell=True)
        
        if result.returncode >= 8:
            print(f"ERROR: Robocopy falló con código {result.returncode}")
            return

        # 3. Subir el version.json al NAS (el disparador para los clientes)
        # Lo hacemos al final para asegurar que la app esté completa antes de avisar
        shutil.copy2(local_version_file, nas_version_file)
        
        print(f"\n¡DESPLIEGUE EXITOSO!")
        print(f"La versión {data['version']} ya está disponible para todos los usuarios.")
        
    except Exception as e:
        print(f"Error crítico durante el despliegue: {e}")

if __name__ == "__main__":
    deploy()
