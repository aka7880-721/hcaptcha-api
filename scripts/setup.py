#!/usr/bin/env python3
"""Cross-platform one-time project setup."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIN_PYTHON = (3, 10)
MIN_NODE_MAJOR = 18


def _run(cmd: list[str], *, cwd: Path | None = None, shell: bool = False) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.check_call(cmd, cwd=cwd or ROOT, shell=shell)


def _npm_install(cwd: Path) -> None:
    npm = shutil.which("npm")
    if not npm:
        raise SystemExit("Node.js/npm not found. Install from https://nodejs.org/ (18+).")
    if sys.platform == "win32":
        _run(["npm", "install"], cwd=cwd, shell=True)
    else:
        _run([npm, "install"], cwd=cwd)


def _check_python() -> None:
    if sys.version_info < MIN_PYTHON:
        ver = ".".join(map(str, MIN_PYTHON))
        raise SystemExit(f"Python {ver}+ required (found {sys.version.split()[0]})")


def _check_node() -> None:
    if not shutil.which("node"):
        raise SystemExit("Node.js not found. Install from https://nodejs.org/ (18+).")
    out = subprocess.check_output(["node", "-v"], text=True).strip()
    major = int(out.lstrip("v").split(".")[0])
    if major < MIN_NODE_MAJOR:
        raise SystemExit(f"Node.js {MIN_NODE_MAJOR}+ required (found {out})")


def _ensure_env() -> None:
    env_path = ROOT / ".env"
    example = ROOT / ".env.example"
    if env_path.exists():
        print(".env already exists")
        return
    if not example.exists():
        raise SystemExit(".env.example missing")
    shutil.copy(example, env_path)
    print("Created .env from .env.example")


def _preflight() -> None:
    sys.path.insert(0, str(ROOT / "solver"))
    from hsolver import Solver  # noqa: F401

    print("  hsolver import: OK")
    print("  Browser: Puppeteer bundled Chromium (optional: BROWSER_EXECUTABLE in .env)")


def main() -> int:
    _check_python()
    _check_node()
    print("[1/4] Python packages")
    _run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("[2/4] Node packages (solver/)")
    _npm_install(ROOT / "solver")
    print("[3/4] Environment")
    _ensure_env()
    print("[4/4] Preflight")
    try:
        _preflight()
    except Exception as exc:
        print(f"  WARN: {exc}")
    print("\nSetup complete. Start with: python scripts/start.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
