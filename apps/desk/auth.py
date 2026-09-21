"""Demo auth stub — not production IAM.

Env: DESK_DEMO_USER / DESK_DEMO_PASSWORD (defaults: demo / demurrage).
Cookie desk_session=1 when signed in. Robot API /api/v1 stays open.
"""
from __future__ import annotations

import os
import secrets
from typing import Callable

from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

SESSION_COOKIE = "desk_session"

PUBLIC_EXACT = {"/login", "/docs", "/openapi.json", "/redoc", "/favicon.ico"}
PUBLIC_PREFIXES = ("/static", "/api/v1", "/docs")


def demo_credentials() -> tuple[str, str]:
    user = os.environ.get("DESK_DEMO_USER", "demo").strip() or "demo"
    password = os.environ.get("DESK_DEMO_PASSWORD", "demurrage").strip() or "demurrage"
    return user, password


def check_password(username: str, password: str) -> bool:
    u, p = demo_credentials()
    return secrets.compare_digest(username or "", u) and secrets.compare_digest(password or "", p)


def is_authenticated(request: Request) -> bool:
    return request.cookies.get(SESSION_COOKIE) == "1"


def _is_public(path: str) -> bool:
    if path in PUBLIC_EXACT:
        return True
    return any(path.startswith(p) for p in PUBLIC_PREFIXES)


class DemoAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        if _is_public(request.url.path):
            return await call_next(request)
        if not is_authenticated(request):
            return RedirectResponse(url="/login", status_code=303)
        return await call_next(request)
