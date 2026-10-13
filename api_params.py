"""Parse solver API requests (multiple client conventions)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional

from flask import Request


@dataclass
class SolveRequest:
    site_key: str
    site_url: str
    proxy: Optional[str] = None
    rqdata: Optional[str] = None
    enterprise: bool = False
    invisible: bool = False


def _first(data: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        val = data.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    return ""


def _as_bool(val: Any) -> bool:
    if isinstance(val, bool):
        return val
    if val is None:
        return False
    return str(val).strip().lower() in ("1", "true", "yes", "on")


def normalize_site_url(url: str) -> str:
    url = url.strip()
    if not url:
        return url
    if not url.startswith(("http://", "https://")):
        return f"https://{url}"
    return url


def parse_solve_request(req: Request) -> SolveRequest:
    data: dict[str, Any] = {}
    if req.method == "POST":
        if req.is_json:
            data.update(req.get_json(silent=True) or {})
        else:
            data.update(req.form.to_dict())
    data.update(req.args.to_dict())

    site_key = _first(data, "site_key", "sitekey", "siteKey")
    site_url = normalize_site_url(_first(data, "site_url", "pageurl", "pageUrl", "url"))
    proxy = _first(data, "proxy", "proxy_url") or None
    rqdata = _first(data, "rqdata", "rqData") or None

    return SolveRequest(
        site_key=site_key,
        site_url=site_url,
        proxy=proxy,
        rqdata=rqdata,
        enterprise=_as_bool(data.get("enterprise")),
        invisible=_as_bool(data.get("invisible")),
    )


def build_hcaptcha_data(solve: SolveRequest) -> Optional[dict]:
    extra: dict[str, str] = {}
    if solve.rqdata:
        extra["rqdata"] = solve.rqdata
    return extra or None


def extract_api_key(req: Request, configured_token: str) -> bool:
    """True if request presents the configured API key."""
    header = (
        req.headers.get("Authorization", "").strip()
        or req.headers.get("X-API-Key", "").strip()
    )
    if header.lower().startswith("bearer "):
        header = header[7:].strip()
    if header == configured_token:
        return True
    data = {**req.args.to_dict()}
    if req.is_json:
        data.update(req.get_json(silent=True) or {})
    data.update(req.form.to_dict())
    for key in ("key", "api_key", "apikey", "clientKey", "client_key"):
        if data.get(key) == configured_token:
            return True
    return False
