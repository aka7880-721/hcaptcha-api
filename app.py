import asyncio
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request

from api_params import build_hcaptcha_data, extract_api_key, parse_solve_request
from api_responses import error_payload, success_payload

_ROOT = Path(__file__).resolve().parent
load_dotenv(_ROOT / ".env")

sys.path.insert(0, str(_ROOT / "solver"))

from hsolver import Solver  # noqa: E402

app = Flask(__name__)

API_AUTH_TOKEN = os.environ.get("API_AUTH_TOKEN", "change-me")
HSW_SERVER_URL = os.environ.get("HSW_SERVER_URL", "http://127.0.0.1:2030")


def _nocaptcha_configured() -> bool:
    return bool(
        os.environ.get("NOCAPTCHA_UID", "").strip()
        and os.environ.get("NOCAPTCHA_APIKEY", "").strip()
    )


def _hsw_reachable() -> bool:
    try:
        import requests

        r = requests.get(f"{HSW_SERVER_URL.rstrip('/')}/health", timeout=3)
        return r.ok
    except Exception:
        return False


def _preflight_errors():
    if not _hsw_reachable():
        return error_payload(
            "HSW proof server unreachable. Start with: python scripts/start.py",
            code="HSW_UNAVAILABLE",
        ), 503
    if not _nocaptcha_configured():
        return error_payload(
            "Configure NOCAPTCHA_UID and NOCAPTCHA_APIKEY for image challenges",
            code="CLASSIFIER_NOT_CONFIGURED",
        ), 503
    return None


def _run_solve(solve_req):
    started = time.time()
    extra = build_hcaptcha_data(solve_req)
    try:
        token = asyncio.run(
            Solver(
                solve_req.proxy,
                solve_req.site_key,
                solve_req.site_url,
                hcaptcha_data=extra,
            ).solve_captcha()
        )
    except Exception as exc:
        elapsed = time.time() - started
        return jsonify(
            error_payload(str(exc), code="SOLVE_EXCEPTION", elapsed_sec=elapsed)
        ), 502

    elapsed = time.time() - started
    if not token:
        return jsonify(
            error_payload("Challenge could not be solved", code="SOLVE_FAILED", elapsed_sec=elapsed)
        ), 502
    return jsonify(success_payload(token, elapsed))


@app.route("/")
def index():
    return jsonify(
        {
            "service": "hcaptcha-solver-api",
            "description": "Self-hosted hCaptcha token solver for automation, scraping, and testing",
            "token_field": "Use hCaptchaResponse / generated_pass_UUID in your form or API call",
            "token_ttl_seconds": 120,
            "endpoints": {
                "health": "GET /health",
                "solve": "GET|POST /solve",
                "solve_v1": "POST /api/v1/hcaptcha/solve",
                "legacy_2captcha": "GET /in.php?key=&method=hcaptcha&sitekey=&pageurl=",
            },
            "parameters": {
                "site_key": "hCaptcha sitekey (aliases: sitekey)",
                "site_url": "Page URL where widget loads (aliases: pageurl, url)",
                "proxy": "Optional http://user:pass@host:port",
                "rqdata": "Enterprise rqdata when required by target site",
            },
            "auth": "Authorization header, X-API-Key, or query key=/clientKey=",
        }
    )


@app.route("/health")
def health():
    return jsonify(
        {
            "ok": True,
            "hsw_server": HSW_SERVER_URL,
            "hsw_reachable": _hsw_reachable(),
            "nocaptcha_configured": _nocaptcha_configured(),
        }
    )


@app.route("/solve", methods=["GET", "POST"])
@app.route("/api/v1/hcaptcha/solve", methods=["POST"])
def solve():
    if not extract_api_key(request, API_AUTH_TOKEN):
        return jsonify(error_payload("Invalid or missing API key", code="UNAUTHORIZED")), 401

    solve_req = parse_solve_request(request)
    if not solve_req.site_key or not solve_req.site_url:
        return jsonify(
            error_payload("site_key and site_url (or sitekey/pageurl) are required", code="INVALID_PARAMS")
        ), 400

    err = _preflight_errors()
    if err:
        return jsonify(err[0]), err[1]

    return _run_solve(solve_req)


@app.route("/in.php", methods=["GET", "POST"])
def legacy_2captcha():
    """Minimal 2Captcha-style bridge: OK|<token> or ERROR|<message>."""
    def plain(text: str, status: int = 200) -> Response:
        return Response(text, status=status, mimetype="text/plain; charset=utf-8")

    if not extract_api_key(request, API_AUTH_TOKEN):
        return plain("ERROR|UNAUTHORIZED", 401)

    method = (request.values.get("method") or "").strip().lower()
    if method and method not in ("hcaptcha", "hcaptchaproxy"):
        return plain("ERROR|UNSUPPORTED_METHOD", 400)

    solve_req = parse_solve_request(request)
    if not solve_req.site_key or not solve_req.site_url:
        return plain("ERROR|MISSING_SITEKEY_OR_PAGEURL", 400)

    err = _preflight_errors()
    if err:
        return plain(f"ERROR|{err[0]['errorCode']}", err[1])

    extra = build_hcaptcha_data(solve_req)
    try:
        token = asyncio.run(
            Solver(
                solve_req.proxy,
                solve_req.site_key,
                solve_req.site_url,
                hcaptcha_data=extra,
            ).solve_captcha()
        )
    except Exception as exc:
        return plain(f"ERROR|{exc}", 502)

    if not token:
        return plain("ERROR|SOLVE_FAILED", 502)
    return plain(f"OK|{token}")


if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8080"))
    app.run(host=host, port=port)
