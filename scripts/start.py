#!/usr/bin/env python3
"""Cross-platform: start hsw server + Flask API."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

HSW_PORT = os.environ.get("HSW_PORT", "2030")
API_PORT = os.environ.get("PORT", "8080")
HSW_URL = os.environ.get("HSW_SERVER_URL", f"http://127.0.0.1:{HSW_PORT}").rstrip("/")


def _wait_hsw(timeout_sec: float = 60.0) -> None:
    deadline = time.time() + timeout_sec
    url = f"{HSW_URL}/health"
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3) as resp:
                if resp.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.5)
    raise RuntimeError(f"hsw server did not become ready at {url}")


def main() -> int:
    node = "node"
    solver_dir = ROOT / "solver"
    if not (solver_dir / "node_modules").is_dir():
        print("Run setup first: python scripts/setup.py", file=sys.stderr)
        return 1

    env = os.environ.copy()
    print(f"[+] Starting hsw on port {HSW_PORT} ...")
    popen_kw: dict = {"cwd": solver_dir, "env": env}
    if sys.platform == "win32":
        popen_kw["shell"] = True
        hsw = subprocess.Popen(f'node "{solver_dir / "browser.js"}"', **popen_kw)
    else:
        hsw = subprocess.Popen([node, "browser.js"], **popen_kw)

    def stop_hsw(*_args) -> None:
        if hsw.poll() is None:
            hsw.terminate()
            try:
                hsw.wait(timeout=10)
            except subprocess.TimeoutExpired:
                hsw.kill()

    if sys.platform != "win32":
        signal.signal(signal.SIGTERM, stop_hsw)
    signal.signal(signal.SIGINT, stop_hsw)

    try:
        _wait_hsw()
        print(f"[+] hsw ready at {HSW_URL}")
        print(f"[+] Starting API on http://127.0.0.1:{API_PORT} (Ctrl+C to stop)")
        api = subprocess.run([sys.executable, str(ROOT / "app.py")], env=env)
        return api.returncode or 0
    except Exception as exc:
        print(f"[!] {exc}", file=sys.stderr)
        return 1
    finally:
        stop_hsw()


if __name__ == "__main__":
    raise SystemExit(main())
