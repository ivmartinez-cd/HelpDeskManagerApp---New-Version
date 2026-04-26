from __future__ import annotations

import argparse
import fnmatch
import hashlib
import os
import re
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

EXCLUDE_DIRS = {
    ".git", ".venv", "venv", "env",
    "__pycache__", ".mypy_cache", ".pytest_cache",
    ".idea", ".vscode",
    "dist", "build", ".ruff_cache",
}

# extensiones a excluir siempre
EXCLUDE_SUFFIX = {".pyc", ".pyo", ".pyd", ".dll", ".exe"}

# tipos “texto” que sí queremos empaquetar (repo snapshot)
INCLUDE_TEXT_SUFFIX = {
    ".py", ".txt", ".md", ".json", ".toml", ".yml", ".yaml", ".ini", ".cfg",
    ".qss", ".css", ".csv", ".tsv", ".xml",
}

# si NO es texto y supera tamaño, lo saltamos (por defecto 2MB)
MAX_NON_TEXT_BYTES_DEFAULT = 2_000_000

# patrones simples para redacción (opcional)
SECRET_PATTERNS = [
    # JSON style: "password": "..."
    (re.compile(r'("password"\s*:\s*)"(.*?)"', re.IGNORECASE), r'\1"***REDACTED***"'),
    (re.compile(r'("pass(word)?"\s*:\s*)"(.*?)"', re.IGNORECASE), r'\1"***REDACTED***"'),
    (re.compile(r'("token"\s*:\s*)"(.*?)"', re.IGNORECASE), r'\1"***REDACTED***"'),
    (re.compile(r'("api[_-]?key"\s*:\s*)"(.*?)"', re.IGNORECASE), r'\1"***REDACTED***"'),

    # INI/env style: PASSWORD=...
    (re.compile(r'^(password|pass|token|api[_-]?key)\s*=\s*(.+)$',
                re.IGNORECASE | re.MULTILINE),
     r'\1=***REDACTED***'),

    # URLs con basic auth: https://user:pass@host/...
    (re.compile(r'(https?://)([^:@/\s]+):([^@/\s]+)@', re.IGNORECASE), r"\1***:***@"),
]


def should_skip_dir(name: str) -> bool:
    return name in EXCLUDE_DIRS


def is_text_file(p: Path) -> bool:
    return p.suffix.lower() in INCLUDE_TEXT_SUFFIX


def should_skip_file(p: Path, max_non_text_bytes: int) -> bool:
    suf = p.suffix.lower()
    if suf in EXCLUDE_SUFFIX:
        return True
    try:
        size = p.stat().st_size
    except FileNotFoundError:
        return True

    # evita binarios grandes
    if (not is_text_file(p)) and size > max_non_text_bytes:
        return True

    return False


def redact_text(text: str) -> str:
    for pat, repl in SECRET_PATTERNS:
        text = pat.sub(repl, text)
    return text


def run_cmd(cmd: list[str]) -> str:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, check=False)
        s = (p.stdout or "") + (("\n" + p.stderr) if p.stderr else "")
        return s.strip() + "\n"
    except Exception as e:
        return f"[ERROR] {cmd}: {e}\n"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass(frozen=True)
class FileEntry:
    path: Path
    rel: str
    size: int
    mtime: float
    sha256: str


def iter_files(
    root: Path,
    include_globs: list[str] | None,
    only_dirs: list[str] | None,
    max_non_text_bytes: int,
) -> list[Path]:
    """
    - include_globs: patrones tipo *.py, pyside_ui/**/*.py, etc. Si None => todo.
    - only_dirs: lista de subdirectorios a incluir (ej: pyside_ui core). Si None => todo.
    """
    root = root.resolve()
    out: list[Path] = []

    only_dir_paths: list[Path] | None = None
    if only_dirs:
        only_dir_paths = [(root / d).resolve() for d in only_dirs]

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]
        dp = Path(dirpath)

        # si usamos only_dirs, saltar árboles fuera
        if only_dir_paths is not None:
            dp_res = dp.resolve()
            if not any(str(dp_res).startswith(str(od)) for od in only_dir_paths):
                continue

        for fn in filenames:
            p = dp / fn
            try:
                if should_skip_file(p, max_non_text_bytes=max_non_text_bytes):
                    continue
            except Exception:
                continue

            rel = str(p.resolve().relative_to(root)).replace("\\", "/")

            # aplicar include_globs si existen
            if include_globs:
                ok = any(fnmatch.fnmatch(rel, g) for g in include_globs)
                if not ok:
                    continue

            out.append(p)

    return sorted(out, key=lambda x: str(x).lower())


def make_tree(root: Path, files: list[Path]) -> str:
    root = root.resolve()
    lines: list[str] = [f"{root.name}/"]

    # armar “tree” a partir del set de archivos incluidos
    # para que el árbol refleje lo empaquetado realmente
    dirs: set[str] = set()
    for p in files:
        rel = p.resolve().relative_to(root)
        parts = rel.parts
        for i in range(1, len(parts)):
            dirs.add("/".join(parts[:i]) + "/")

    items = sorted(list(dirs) + [str(p.resolve().relative_to(root)).replace("\\", "/") for p in files])

    # imprimir tree simple estilo “paths”
    for it in items:
        if it.endswith("/"):
            lines.append(f"DIR  {it}")
        else:
            try:
                size = (root / it).stat().st_size
            except Exception:
                size = 0
            lines.append(f"FILE {it} ({size} bytes)")

    return "\n".join(lines) + "\n"


def build_manifest(root: Path, files: list[Path]) -> list[FileEntry]:
    root = root.resolve()
    entries: list[FileEntry] = []
    for p in files:
        try:
            st = p.stat()
        except FileNotFoundError:
            continue
        rel = str(p.resolve().relative_to(root)).replace("\\", "/")
        try:
            digest = sha256_file(p)
        except Exception:
            digest = "ERROR"
        entries.append(FileEntry(path=p, rel=rel, size=st.st_size, mtime=st.st_mtime, sha256=digest))
    return entries


def write_manifest(out_path: Path, entries: list[FileEntry]) -> None:
    # formato TSV fácil de diff/grep
    # rel \t size \t mtime_iso \t sha256
    with out_path.open("w", encoding="utf-8") as f:
        f.write("# rel\tsize\tmtime_iso\tsha256\n")
        for e in entries:
            mtime_iso = datetime.fromtimestamp(e.mtime).isoformat(timespec="seconds")
            f.write(f"{e.rel}\t{e.size}\t{mtime_iso}\t{e.sha256}\n")


def concat_py_files(root: Path, files: list[Path], out_txt: Path, redact: bool) -> None:
    root = root.resolve()
    with out_txt.open("w", encoding="utf-8") as out:
        out.write(f"# Repo: {root}\n")
        out.write(f"# Generated: {datetime.now().isoformat(timespec='seconds')}\n\n")
        for p in files:
            if p.suffix.lower() != ".py":
                continue
            rel = p.resolve().relative_to(root)
            out.write("\n" + "=" * 90 + "\n")
            out.write("# FILE: " + str(rel).replace("\\", "/") + "\n")
            out.write("=" * 90 + "\n")
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                out.write(f"# [ERROR reading file: {e}]\n")
                continue
            if redact:
                text = redact_text(text)
            out.write(text)
            if not text.endswith("\n"):
                out.write("\n")


def zip_selected_files(
    root: Path,
    files: list[Path],
    zip_path: Path,
    redact: bool,
) -> None:
    """
    Zip “snapshot” del repo con los archivos seleccionados.
    Si redact=True, solo aplica a archivos de texto; binarios (si entraran) se copian tal cual.
    """
    root = root.resolve()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in files:
            rel = str(p.resolve().relative_to(root)).replace("\\", "/")
            if redact and is_text_file(p):
                try:
                    text = p.read_text(encoding="utf-8", errors="replace")
                    text = redact_text(text)
                    z.writestr(rel, text)
                    continue
                except Exception:
                    # fallback: meter el archivo tal cual
                    pass
            try:
                z.write(p, rel)
            except FileNotFoundError:
                continue


def zip_dir(src: Path, zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in src.rglob("*"):
            if p.is_file():
                z.write(p, p.relative_to(src))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--include-py", action="store_true", help="Concatena todos los .py en all_py.txt")
    ap.add_argument("--pip-freeze", action="store_true", help="Guarda pip freeze")
    ap.add_argument("--git", action="store_true", help="Guarda branch/commit/status si hay git (opcional)")
    ap.add_argument("--redact", action="store_true", help="Redacta secretos simples en textos (all_py y zips)")
    ap.add_argument("--out", default="_context_repo", help="Carpeta de salida")
    ap.add_argument("--max-non-text-bytes", type=int, default=MAX_NON_TEXT_BYTES_DEFAULT,
                    help="Tamaño máximo permitido para archivos no-texto")
    ap.add_argument("--only-dirs", nargs="*", default=None,
                    help="Incluir solo estos subdirectorios (ej: pyside_ui core)")
    ap.add_argument("--include-glob", nargs="*", default=None,
                    help="Patrones glob de paths relativos (ej: 'pyside_ui/**/*.py' 'core/**/*.py')")
    ap.add_argument("--snapshot", action="store_true",
                    help="Genera snapshot_repo.zip con los archivos seleccionados (recomendado)")
    args = ap.parse_args()

    root = Path.cwd()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # seleccionar archivos a incluir
    files = iter_files(
        root=root,
        include_globs=args.include_glob,
        only_dirs=args.only_dirs,
        max_non_text_bytes=args.max_non_text_bytes,
    )

    # tree “real” de lo incluido
    (out_dir / "tree.txt").write_text(make_tree(root, files), encoding="utf-8")

    # “fingerprint” sin git: manifest con sha256/mtime
    manifest = build_manifest(root, files)
    write_manifest(out_dir / "manifest.tsv", manifest)

    # archivos “clave” si existen
    for name in ("requirements.txt", "pyproject.toml", "poetry.lock", "Pipfile", "Pipfile.lock", "README.md"):
        p = root / name
        if p.exists() and p.is_file():
            try:
                (out_dir / name).write_bytes(p.read_bytes())
            except Exception:
                pass

    # python info
    (out_dir / "python.txt").write_text(
        f"python_exe={sys.executable}\npython_version={sys.version}\nplatform={sys.platform}\n",
        encoding="utf-8",
    )

    # pip freeze
    if args.pip_freeze:
        (out_dir / "pip_freeze.txt").write_text(
            run_cmd([sys.executable, "-m", "pip", "freeze"]),
            encoding="utf-8",
        )

    # git info (si existe, opcional)
    if args.git:
        (out_dir / "git_branch.txt").write_text(run_cmd(["git", "branch", "--show-current"]), encoding="utf-8")
        (out_dir / "git_head.txt").write_text(run_cmd(["git", "rev-parse", "HEAD"]), encoding="utf-8")
        (out_dir / "git_status.txt").write_text(run_cmd(["git", "status"]), encoding="utf-8")

    if args.include_py:
        concat_py_files(root, files, out_dir / "all_py.txt", redact=args.redact)

    # zip del contexto
    ctx_zip = Path(f"{out_dir.name}.zip")
    if ctx_zip.exists():
        ctx_zip.unlink()
    zip_dir(out_dir, ctx_zip)

    # zip snapshot del repo (lo que realmente necesito para trabajar bien)
    if args.snapshot:
        snap_zip = Path("snapshot_repo.zip")
        if snap_zip.exists():
            snap_zip.unlink()
        zip_selected_files(root, files, snap_zip, redact=args.redact)
        print(f"[OK] snapshot -> {snap_zip}")

    print(f"[OK] {out_dir}/")
    print(f"[OK] {ctx_zip}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# Ejemplos:
# python collect_repo_context.py --snapshot --pip-freeze --redact --only-dirs pyside_ui core
# python collect_repo_context.py --snapshot --include-py --pip-freeze --redact --only-dirs pyside_ui core
