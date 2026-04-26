# build_launcher.py
import subprocess
import sys
import shutil
import os
from pathlib import Path

def build():
    print("=== Iniciando construcción del Lanzador (HelpDeskLauncher) ===")
    
    # 1. Verificar PyInstaller
    try:
        import PyInstaller
        print(f"PyInstaller detectado (v{PyInstaller.__version__})")
    except ImportError:
        print("ERROR: PyInstaller no está instalado. Ejecuta 'pip install pyinstaller'")
        return

    # 2. Rutas
    spec_file = "HelpDeskLauncher.spec"
    dist_dir = Path("dist")
    build_dir = Path("build")
    
    if not os.path.exists(spec_file):
        print(f"ERROR: No se encuentra el archivo {spec_file}")
        return

    # 3. Limpiar construcciones anteriores para evitar conflictos
    print("Limpiando carpetas temporales...")
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    if build_dir.exists():
        shutil.rmtree(build_dir)

    # 4. Ejecutar PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        spec_file
    ]
    
    print(f"Ejecutando: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        print("\n=== CONSTRUCCIÓN COMPLETADA CON ÉXITO ===")
        print(f"El lanzador se encuentra en: {dist_dir / 'HelpDeskLauncher'}")
        
        # Sugerencia opcional: copiar a la raíz si el usuario lo prefiere
        # shutil.copytree(dist_dir / "HelpDeskLauncher", Path("HelpDeskLauncher"), dirs_exist_ok=True)
        
    except subprocess.CalledProcessError as e:
        print(f"\nERROR durante la construcción: {e}")

if __name__ == "__main__":
    build()
