#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
audit_repo.py
Auditoría estática (no ejecuta la app, no modifica nada).
Genera un reporte Markdown (y opcional JSON) para limpiar/ordenar el repo de forma profesional.

Uso (Windows):
  py audit_repo.py --root "C:\Users\imartinez\Desktop\Scripts\new UI" --out audit_report.md

Uso (repo actual):
  py audit_repo.py --out audit_report.md

Opcional:
  py audit_repo.py --out audit_report.md --json audit_report.json --include-core 0
"""


from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set


# -------------------------
# Config / patterns
# -------------------------

DEFAULT_EXCLUDE_DIRS = {
    ".git", ".hg", ".svn", "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    ".venv", "venv", "env", "node_modules", "dist", "build", "out", "_context_repo",
}

DEFAULT_EXCLUDE_EXTS = {
    ".pyc", ".pyo", ".pyd", ".dll", ".so", ".dylib", ".exe",
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico",
    ".pdf", ".zip", ".7z", ".rar",
    ".db3", ".sqlite", ".bin",
}

# Heurísticas de "cosas a revisar"
RE_TODO = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b", re.IGNORECASE)
RE_PRINT = re.compile(r"^\s*print\(", re.MULTILINE)
RE_BARE_EXCEPT = re.compile(r"^\s*except\s*:\s*$", re.MULTILINE)
RE_EXCEPT_EXCEPTION = re.compile(r"^\s*except\s+Exception\s*(as\s+\w+)?\s*:\s*$", re.MULTILINE)
RE_PASS = re.compile(r"^\s*pass\s*$", re.MULTILINE)

# Cosas específicas de tu migración / UX definida
RE_QMESSAGEBOX = re.compile(r"\bQMessageBox\b")
RE_QPROGRESS = re.compile(r"\bQProgress(Dialog)?\b")
RE_LOGGING = re.compile(r"\blogging\.(debug|info|warning|error|exception)\b|\blogging\.getLogger\b")
RE_DEBUG_WORDS = re.compile(r"\b(debug|dbg|temp|tmp|wip)\b", re.IGNORECASE)

# Imports "core/" no se toca, pero sí queremos auditar referencias
CORE_DIR_NAME = "core"


# -------------------------
# Utils
# -------------------------

def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        try:
            return path.read_text(encoding=sys.getdefaultencoding(), errors="replace")
        except Exception:
            return ""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    try:
        return sha256_bytes(path.read_bytes())
    except Exception:
        return ""


def is_excluded_path(path: Path, exclude_dirs: Set[str]) -> bool:
    parts = {p.name for p in path.parents}
    return any(d in parts for d in exclude_dirs)


def human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def stable_rel(root: Path, p: Path) -> str:
    try:
        return str(p.relative_to(root)).replace("\\", "/")
    except Exception:
        return str(p).replace("\\", "/")


# -------------------------
# AST parsing for .py
# -------------------------

@dataclass
class PyMeta:
    classes: int = 0
    functions: int = 0
    imports: int = 0
    import_modules: List[str] = None
    has_main_guard: bool = False
    top_level_code_lines: int = 0  # heuristic

    def __post_init__(self):
        if self.import_modules is None:
            self.import_modules = []


def parse_py_meta(text: str) -> PyMeta:
    meta = PyMeta()
    try:
        tree = ast.parse(text)
    except Exception:
        return meta

    class_counter = 0
    func_counter = 0
    import_counter = 0
    mods: List[str] = []
    has_main = False

    # Heurística: contar sentencias top-level "no definiciones / imports"
    top_level_statements = 0

    for node in tree.body:
        if isinstance(node, (ast.ClassDef,)):
            class_counter += 1
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_counter += 1
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            import_counter += 1
            if isinstance(node, ast.Import):
                for a in node.names:
                    mods.append(a.name)
            else:
                # from X import Y
                mod = node.module or ""
                mods.append(mod)
        else:
            # top level "otras cosas"
            top_level_statements += 1

        # detectar if __name__ == "__main__":
        if isinstance(node, ast.If):
            try:
                if (
                    isinstance(node.test, ast.Compare)
                    and isinstance(node.test.left, ast.Name)
                    and node.test.left.id == "__name__"
                ):
                    has_main = True
            except Exception:
                pass

    meta.classes = class_counter
    meta.functions = func_counter
    meta.imports = import_counter
    meta.import_modules = sorted(set(m for m in mods if m))
    meta.has_main_guard = has_main
    meta.top_level_code_lines = top_level_statements
    return meta


# -------------------------
# Duplicate detection
# -------------------------

def tokenize_for_simhash(s: str) -> List[str]:
    # Normaliza para near-duplicate (sin spacing / comments simples)
    s = re.sub(r"#.*", "", s)
    s = re.sub(r'""".*?"""', "", s, flags=re.S)
    s = re.sub(r"'''.*?'''", "", s, flags=re.S)
    s = re.sub(r"\s+", " ", s).strip().lower()
    # tokens alfanuméricos + símbolos relevantes
    return re.findall(r"[a-z_]\w+|\d+|==|!=|<=|>=|->|:=|[{}()\[\].,:;=+\-*/%<>]", s)


def simhash(tokens: List[str], bits: int = 64) -> int:
    # Implementación simple de simhash
    v = [0] * bits
    for t in tokens:
        h = int(hashlib.md5(t.encode("utf-8", errors="ignore")).hexdigest(), 16)
        for i in range(bits):
            bit = (h >> i) & 1
            v[i] += 1 if bit else -1
    out = 0
    for i in range(bits):
        if v[i] >= 0:
            out |= (1 << i)
    return out


def hamming(a: int, b: int) -> int:
    return (a ^ b).bit_count()


# -------------------------
# Repo scan
# -------------------------

@dataclass
class FileStat:
    path: str
    ext: str
    size: int
    lines: int
    sha256: str
    todo_hits: int
    print_hits: int
    bare_except_hits: int
    except_exception_hits: int
    pass_hits: int
    qmessagebox_hits: int
    qprogress_hits: int
    logging_hits: int
    debug_word_hits: int
    py_meta: Optional[PyMeta] = None


@dataclass
class AuditReport:
    root: str
    scanned_files: int
    skipped_files: int
    total_size: int
    file_stats: List[FileStat]
    duplicates_exact: Dict[str, List[str]]  # sha -> [paths]
    duplicates_near: List[Dict[str, object]]  # groups
    orphan_candidates: List[str]
    hot_spots: List[Dict[str, object]]
    notes: List[str]


def iter_files(root: Path, exclude_dirs: Set[str], exclude_exts: Set[str]) -> List[Path]:
    out: List[Path] = []
    for p in root.rglob("*"):
        if p.is_dir():
            continue
        if is_excluded_path(p, exclude_dirs):
            continue
        if p.suffix.lower() in exclude_exts:
            continue
        out.append(p)
    return out


def build_tree(root: Path, paths: List[Path], max_depth: int = 6) -> str:
    # Árbol simple basado en paths incluidos
    rels = sorted({stable_rel(root, p) for p in paths})
    tree: Dict[str, dict] = {}
    for r in rels:
        parts = r.split("/")
        cur = tree
        for i, part in enumerate(parts[:max_depth]):
            cur = cur.setdefault(part, {})
    # Render
    def render(node: dict, prefix: str = "") -> List[str]:
        lines: List[str] = []
        keys = sorted(node.keys())
        for idx, k in enumerate(keys):
            last = idx == len(keys) - 1
            branch = "└── " if last else "├── "
            lines.append(prefix + branch + k)
            child = node[k]
            if child:
                ext_prefix = "    " if last else "│   "
                lines.extend(render(child, prefix + ext_prefix))
        return lines
    return "\n".join(render(tree))


def collect_import_references(py_files: List[Tuple[Path, str]]) -> Set[str]:
    """
    Junta referencias a módulos/archivos propios para detectar "archivos huérfanos".
    Heurística:
    - imports: from pyside_ui.x import y, import pyside_ui.x
    - strings: "pyside_ui/..." o "core/..."
    """
    refs: Set[str] = set()

    for path, text in py_files:
        # imports "pyside_ui.something"
        for m in re.findall(r"\bimport\s+(pyside_ui(?:\.[\w_]+)*)", text):
            refs.add(m)
        for m in re.findall(r"\bfrom\s+(pyside_ui(?:\.[\w_]+)*)\s+import\b", text):
            refs.add(m)

        # strings con rutas
        for m in re.findall(r"(pyside_ui/[A-Za-z0-9_./-]+)", text):
            refs.add(m.split(".")[0])
        for m in re.findall(r"(core/[A-Za-z0-9_./-]+)", text):
            refs.add(m.split(".")[0])

        # también por nombre de archivo importado
        # (no perfecto, pero ayuda)
        for m in re.findall(r"['\"]([^'\"]+\.py)['\"]", text):
            refs.add(m.replace("\\", "/"))

    return refs


def find_orphan_candidates(root: Path, files: List[Path], refs: Set[str]) -> List[str]:
    """
    Archivos candidatos a estar "no usados":
    - .py dentro de pyside_ui/ que no parece estar referenciado por imports/rutas
    """
    cands: List[str] = []
    for p in files:
        rel = stable_rel(root, p)
        if not rel.endswith(".py"):
            continue
        if rel.startswith(f"{CORE_DIR_NAME}/"):
            continue
        if not rel.startswith("pyside_ui/"):
            continue

        mod = rel[:-3].replace("/", ".")  # pyside_ui.ui.x
        if (mod not in refs) and (rel not in refs):
            # muy probable: no importado directamente
            cands.append(rel)

    return sorted(cands)


def hot_spots(stats: List[FileStat], top_n: int = 15) -> List[Dict[str, object]]:
    """
    Ranking de archivos "calientes" por combinación de:
    - tamaño (líneas)
    - señales de deuda (TODO/print/except)
    """
    scored = []
    for fs in stats:
        if fs.ext != ".py":
            continue
        debt = fs.todo_hits + fs.print_hits + fs.bare_except_hits + fs.except_exception_hits + fs.pass_hits
        debt += fs.qmessagebox_hits + fs.qprogress_hits
        score = fs.lines * 0.02 + debt * 8
        scored.append((score, debt, fs.lines, fs.path))
    scored.sort(reverse=True)
    out = []
    for score, debt, lines, path in scored[:top_n]:
        out.append({"path": path, "lines": lines, "debt_signals": debt, "score": round(score, 2)})
    return out


def compute_exact_duplicates(stats: List[FileStat]) -> Dict[str, List[str]]:
    buckets: Dict[str, List[str]] = {}
    for fs in stats:
        if not fs.sha256:
            continue
        buckets.setdefault(fs.sha256, []).append(fs.path)
    return {h: ps for h, ps in buckets.items() if len(ps) > 1}


def compute_near_duplicates(root: Path, stats: List[FileStat], files_by_path: Dict[str, Path]) -> List[Dict[str, object]]:
    """
    Near-duplicate simple:
    - solo .py
    - simhash del archivo completo (rápido)
    - agrupa si distancia Hamming <= 6
    """
    entries: List[Tuple[str, int]] = []
    for fs in stats:
        if fs.ext != ".py":
            continue
        p = files_by_path.get(fs.path)
        if not p:
            continue
        text = read_text(p)
        tokens = tokenize_for_simhash(text)
        if len(tokens) < 60:
            continue
        h = simhash(tokens)
        entries.append((fs.path, h))

    groups: List[Dict[str, object]] = []
    used: Set[str] = set()
    for i in range(len(entries)):
        p1, h1 = entries[i]
        if p1 in used:
            continue
        group = [p1]
        for j in range(i + 1, len(entries)):
            p2, h2 = entries[j]
            if p2 in used:
                continue
            if hamming(h1, h2) <= 6:
                group.append(p2)
        if len(group) >= 2:
            for p in group:
                used.add(p)
            groups.append({"paths": sorted(group), "kind": "near-duplicate(simhash<=6)"})

    # ordenar por tamaño del grupo desc
    groups.sort(key=lambda g: len(g["paths"]), reverse=True)
    return groups


def scan(root: Path, include_core: bool, exclude_dirs: Set[str], exclude_exts: Set[str]) -> AuditReport:
    all_files = iter_files(root, exclude_dirs, exclude_exts)
    if not include_core:
        all_files = [p for p in all_files if not stable_rel(root, p).startswith(f"{CORE_DIR_NAME}/")]

    total_size = sum(p.stat().st_size for p in all_files if p.exists())

    file_stats: List[FileStat] = []
    skipped = 0

    py_texts: List[Tuple[Path, str]] = []
    files_by_path: Dict[str, Path] = {}

    for p in all_files:
        rel = stable_rel(root, p)
        files_by_path[rel] = p

        try:
            size = p.stat().st_size
        except Exception:
            skipped += 1
            continue

        text = ""
        lines = 0
        sha = sha256_file(p)

        if p.suffix.lower() in {".py", ".md", ".txt", ".json", ".ini", ".toml", ".yml", ".yaml"}:
            text = read_text(p)
            lines = text.count("\n") + (1 if text else 0)
        else:
            # binario/otros: no analizamos texto
            text = ""

        todo_hits = len(RE_TODO.findall(text)) if text else 0
        print_hits = len(RE_PRINT.findall(text)) if text else 0
        bare_except_hits = len(RE_BARE_EXCEPT.findall(text)) if text else 0
        except_exception_hits = len(RE_EXCEPT_EXCEPTION.findall(text)) if text else 0
        pass_hits = len(RE_PASS.findall(text)) if text else 0

        qmessagebox_hits = len(RE_QMESSAGEBOX.findall(text)) if text else 0
        qprogress_hits = len(RE_QPROGRESS.findall(text)) if text else 0
        logging_hits = len(RE_LOGGING.findall(text)) if text else 0
        debug_word_hits = len(RE_DEBUG_WORDS.findall(text)) if text else 0

        py_meta = None
        if p.suffix.lower() == ".py" and text:
            py_meta = parse_py_meta(text)
            py_texts.append((p, text))

        file_stats.append(FileStat(
            path=rel,
            ext=p.suffix.lower(),
            size=size,
            lines=lines,
            sha256=sha,
            todo_hits=todo_hits,
            print_hits=print_hits,
            bare_except_hits=bare_except_hits,
            except_exception_hits=except_exception_hits,
            pass_hits=pass_hits,
            qmessagebox_hits=qmessagebox_hits,
            qprogress_hits=qprogress_hits,
            logging_hits=logging_hits,
            debug_word_hits=debug_word_hits,
            py_meta=py_meta,
        ))

    refs = collect_import_references(py_texts)
    orphans = find_orphan_candidates(root, all_files, refs)

    exact_dups = compute_exact_duplicates(file_stats)
    near_dups = compute_near_duplicates(root, file_stats, files_by_path)

    notes: List[str] = []
    notes.append("Este reporte es heurístico: confirmá antes de borrar/limpiar.")
    notes.append("Regla recomendada: cambiar 1 cosa por vez y con rollback fácil.")

    return AuditReport(
        root=str(root),
        scanned_files=len(file_stats),
        skipped_files=skipped,
        total_size=total_size,
        file_stats=file_stats,
        duplicates_exact=exact_dups,
        duplicates_near=near_dups,
        orphan_candidates=orphans,
        hot_spots=hot_spots(file_stats),
        notes=notes,
    )


# -------------------------
# Report rendering
# -------------------------

def render_markdown(rep: AuditReport, tree_str: str) -> str:
    stats = rep.file_stats

    # Helpers
    def top_by(key_fn, n=15, only_py=False):
        items = [s for s in stats if (not only_py or s.ext == ".py")]
        items.sort(key=key_fn, reverse=True)
        return items[:n]

    top_big = top_by(lambda s: (s.lines, s.size), n=20, only_py=True)
    top_todo = top_by(lambda s: s.todo_hits, n=20, only_py=True)
    top_print = top_by(lambda s: s.print_hits, n=20, only_py=True)

    # QMessageBox/QProgress presence
    qmsg = [s for s in stats if s.qmessagebox_hits > 0]
    qprog = [s for s in stats if s.qprogress_hits > 0]

    # Render
    out: List[str] = []
    out.append("# Auditoría del repo — Reporte\n")
    out.append(f"- Root: `{rep.root}`")
    out.append(f"- Archivos analizados: **{rep.scanned_files}** (skipped: {rep.skipped_files})")
    out.append(f"- Tamaño total: **{human_size(rep.total_size)}**\n")

    out.append("## Árbol (parcial)\n")
    out.append("```")
    out.append(tree_str)
    out.append("```\n")

    out.append("## Hot spots (prioridad para revisar)\n")
    out.append("| Archivo | Líneas | Señales deuda | Score |")
    out.append("|---|---:|---:|---:|")
    for h in rep.hot_spots:
        out.append(f"| `{h['path']}` | {h['lines']} | {h['debt_signals']} | {h['score']} |")
    out.append("")

    out.append("## Archivos más grandes (.py)\n")
    out.append("| Archivo | Líneas | Tamaño | Clases | Funciones | Imports |")
    out.append("|---|---:|---:|---:|---:|---:|")
    for s in top_big:
        pm = s.py_meta or PyMeta()
        out.append(f"| `{s.path}` | {s.lines} | {human_size(s.size)} | {pm.classes} | {pm.functions} | {pm.imports} |")
    out.append("")

    out.append("## Señales (TODO/FIXME)\n")
    out.append("| Archivo | Hits |")
    out.append("|---|---:|")
    for s in top_todo:
        if s.todo_hits <= 0:
            break
        out.append(f"| `{s.path}` | {s.todo_hits} |")
    out.append("")

    out.append("## Señales (print)\n")
    out.append("| Archivo | Hits |")
    out.append("|---|---:|")
    for s in top_print:
        if s.print_hits <= 0:
            break
        out.append(f"| `{s.path}` | {s.print_hits} |")
    out.append("")

    out.append("## Señales de riesgo (except/pass)\n")
    out.append("| Archivo | bare except | except Exception | pass |")
    out.append("|---|---:|---:|---:|")
    risky = [s for s in stats if s.ext == ".py" and (s.bare_except_hits or s.except_exception_hits or s.pass_hits)]
    risky.sort(key=lambda s: (s.bare_except_hits + s.except_exception_hits + s.pass_hits), reverse=True)
    for s in risky[:25]:
        out.append(f"| `{s.path}` | {s.bare_except_hits} | {s.except_exception_hits} | {s.pass_hits} |")
    out.append("")

    out.append("## Chequeos UX PySide (cosas que se ‘cuelan’)\n")
    if qmsg:
        out.append("### QMessageBox encontrado (revisar: debería estar en dialog_kit si aplica)\n")
        out.append("| Archivo | Hits |")
        out.append("|---|---:|")
        for s in sorted(qmsg, key=lambda x: x.qmessagebox_hits, reverse=True)[:30]:
            out.append(f"| `{s.path}` | {s.qmessagebox_hits} |")
        out.append("")
    else:
        out.append("- ✅ No se detectó `QMessageBox` en los archivos analizados.\n")

    if qprog:
        out.append("### QProgressDialog/QProgress encontrado (revisar: UX decidió NO usar)\n")
        out.append("| Archivo | Hits |")
        out.append("|---|---:|")
        for s in sorted(qprog, key=lambda x: x.qprogress_hits, reverse=True)[:30]:
            out.append(f"| `{s.path}` | {s.qprogress_hits} |")
        out.append("")
    else:
        out.append("- ✅ No se detectó `QProgress*` en los archivos analizados.\n")

    out.append("## Duplicación exacta (sha256 igual)\n")
    if rep.duplicates_exact:
        for h, paths in rep.duplicates_exact.items():
            out.append(f"- **{h[:12]}…**")
            for p in sorted(paths):
                out.append(f"  - `{p}`")
        out.append("")
    else:
        out.append("- ✅ No se detectaron duplicados exactos.\n")

    out.append("## Duplicación aproximada (near-duplicate)\n")
    if rep.duplicates_near:
        for g in rep.duplicates_near[:20]:
            out.append(f"- {g['kind']}")
            for p in g["paths"]:
                out.append(f"  - `{p}`")
        out.append("")
    else:
        out.append("- ✅ No se detectaron near-duplicates fuertes (heurística simhash).\n")

    out.append("## Candidatos a ‘orphan’ (posible código no referenciado)\n")
    if rep.orphan_candidates:
        out.append("> Heurístico: puede ser falso positivo (plugins/dynamic imports). Confirmar antes de borrar.\n")
        for p in rep.orphan_candidates[:120]:
            out.append(f"- `{p}`")
        if len(rep.orphan_candidates) > 120:
            out.append(f"- … +{len(rep.orphan_candidates) - 120} más")
        out.append("")
    else:
        out.append("- ✅ No se detectaron orphans claros.\n")

    out.append("## Notas\n")
    for n in rep.notes:
        out.append(f"- {n}")
    out.append("")

    return "\n".join(out)


# -------------------------
# CLI
# -------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="Root del repo")
    ap.add_argument("--out", default="audit_report.md", help="Salida Markdown")
    ap.add_argument("--json", default="", help="Salida JSON opcional")
    ap.add_argument("--include-core", type=int, default=1, help="1=auditar core/ (solo lectura), 0=excluir")
    ap.add_argument("--max-depth", type=int, default=6, help="Profundidad árbol")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"[ERROR] Root no existe: {root}")
        return 2

    rep = scan(
        root=root,
        include_core=bool(args.include_core),
        exclude_dirs=set(DEFAULT_EXCLUDE_DIRS),
        exclude_exts=set(DEFAULT_EXCLUDE_EXTS),
    )

    files = [Path(root / fs.path) for fs in rep.file_stats if fs.path]
    tree_str = build_tree(root, files, max_depth=args.max_depth)

    md = render_markdown(rep, tree_str)
    out_path = Path(args.out).resolve()
    out_path.write_text(md, encoding="utf-8", errors="replace")
    print(f"[OK] Markdown: {out_path}")

    if args.json:
        json_path = Path(args.json).resolve()
        payload = {
            **asdict(rep),
            "file_stats": [
                {
                    **{k: v for k, v in asdict(fs).items() if k != "py_meta"},
                    "py_meta": asdict(fs.py_meta) if fs.py_meta else None,
                }
                for fs in rep.file_stats
            ],
        }
        json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[OK] JSON: {json_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#python audit_repo.py --out audit_report.md --json audit_report.json
