"""Build dashboard/dist if missing or source is newer."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DASHBOARD_DIR = PROJECT_ROOT / "dashboard"
DIST_DIR = DASHBOARD_DIR / "dist"


def _newest_mtime(paths: list[Path]) -> float:
    best = 0.0
    for p in paths:
        if p.is_file():
            best = max(best, p.stat().st_mtime)
        elif p.is_dir():
            for f in p.rglob("*"):
                if f.is_file():
                    best = max(best, f.stat().st_mtime)
    return best


def ensure_dashboard_built(*, force: bool = False) -> bool:
    """Return True if dist exists after this call."""
    pkg = DASHBOARD_DIR / "package.json"
    if not pkg.is_file():
        print("dashboard/package.json not found, skip build")
        return DIST_DIR.is_dir()

    dist_index = DIST_DIR / "index.html"
    src_dir = DASHBOARD_DIR / "src"
    need = force or not dist_index.is_file()
    if not need and src_dir.is_dir():
        src_mtime = _newest_mtime([src_dir])
        dist_mtime = dist_index.stat().st_mtime if dist_index.is_file() else 0
        need = src_mtime > dist_mtime

    if not need:
        return True

    npm = shutil.which("npm")
    if not npm:
        print("npm not found; build manually: cd dashboard && npm run build")
        return dist_index.is_file()

    node_modules = DASHBOARD_DIR / "node_modules"
    if not node_modules.is_dir():
        print("Installing dashboard dependencies…")
        subprocess.run([npm, "install"], cwd=DASHBOARD_DIR, check=False)

    print("Building dashboard (npm run build)…")
    r = subprocess.run([npm, "run", "build"], cwd=DASHBOARD_DIR, check=False)
    if r.returncode != 0:
        print("Dashboard build failed; fix errors in dashboard/ and retry")
        return dist_index.is_file()
    print("Dashboard build OK")
    return dist_index.is_file()
