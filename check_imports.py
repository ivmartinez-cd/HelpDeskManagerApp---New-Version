from __future__ import annotations
import re
from pathlib import Path

BAD_ALWAYS = [
    re.compile(r'^\s*from\s+tabs\s+import\s+', re.M),
    re.compile(r'^\s*from\s+widgets\s+import\s+', re.M),
]

BAD_IN_TABS_ONLY = [
    re.compile(r'^\s*from\s+\.widgets\s+import\s+', re.M),
]


root = Path.cwd()
py_files = list(root.rglob("*.py"))

bad_hits = []
for p in py_files:
    if any(part in {"__pycache__", ".venv", "venv", "env", ".git"} for part in p.parts):
        continue

    text = p.read_text(encoding="utf-8", errors="replace")

    # reglas globales
    for pat in BAD_ALWAYS:
        if pat.search(text):
            bad_hits.append((str(p), pat.pattern))

    # reglas solo para tabs/*
    if "tabs" in p.parts:
        for pat in BAD_IN_TABS_ONLY:
            if pat.search(text):
                bad_hits.append((str(p), pat.pattern))


if not bad_hits:
    print("[OK] No se detectaron imports problemáticos.")
else:
    print("[WARN] Imports problemáticos encontrados:")
    for f, pat in bad_hits:
        print(" -", f, "matches", pat)
    raise SystemExit(1)
