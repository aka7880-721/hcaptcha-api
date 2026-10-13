"""Standard solver API response shapes."""

from __future__ import annotations

from typing import Any

TOKEN_TTL_SECONDS = 120


def success_payload(token: str, elapsed_sec: float) -> dict[str, Any]:
    t = round(elapsed_sec, 3)
    return {
        "success": True,
        "status": "ready",
        "token": token,
        "generated_pass_UUID": token,
        "hCaptchaResponse": token,
        "key": token,
        "solve_time": t,
        "time": t,
        "expires_in_seconds": TOKEN_TTL_SECONDS,
    }


def error_payload(
    message: str,
    *,
    code: str = "ERROR",
    elapsed_sec: float | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "success": False,
        "status": "error",
        "error": message,
        "errorCode": code,
    }
    if elapsed_sec is not None:
        body["time"] = round(elapsed_sec, 3)
    return body
