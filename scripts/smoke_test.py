"""Quick smoke test: health endpoints only (no captcha solve)."""

import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
sys.path.insert(0, str(ROOT))

API = os.environ.get("SMOKE_API", "http://127.0.0.1:8080")
HSW = os.environ.get("HSW_SERVER_URL", "http://127.0.0.1:2030")


def main() -> int:
    hsw = requests.get(f"{HSW.rstrip('/')}/health", timeout=5)
    hsw.raise_for_status()
    print("hsw:", hsw.json())

    api = requests.get(f"{API.rstrip('/')}/health", timeout=5)
    api.raise_for_status()
    print("api:", api.json())

    auth = os.environ.get("API_AUTH_TOKEN", "change-me")
    bad = requests.get(f"{API.rstrip('/')}/solve", timeout=5)
    assert bad.status_code == 401, bad.text

    missing = requests.get(
        f"{API.rstrip('/')}/solve",
        headers={"Authorization": auth},
        timeout=5,
    )
    assert missing.status_code == 400, missing.text
    assert missing.json().get("success") is False

    legacy = requests.get(
        f"{API.rstrip('/')}/in.php",
        params={"key": auth, "method": "hcaptcha"},
        timeout=5,
    )
    assert legacy.status_code == 400
    assert legacy.text.startswith("ERROR|")
    print("auth + validation + legacy bridge OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
