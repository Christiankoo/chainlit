# app/auth_middleware.py
from typing import Iterable, Optional, Set

import jwt
from starlette.responses import RedirectResponse


class AuthGate:
    def __init__(
        self,
        app,
        tenant_id: str,
        public_paths: Optional[Iterable[str]] = None,
        auth_cookie_name: str = "cl_auth",
        jwt_secret: str = "",
    ):
        self.app = app
        self.tenant_id = tenant_id
        self.public_paths: Set[str] = set(public_paths or [])
        self.auth_cookie_name = auth_cookie_name
        self.jwt_secret = jwt_secret

        if not self.jwt_secret:
            raise RuntimeError("AuthGate requires jwt_secret (set SESSION_SECRET).")

    def _is_public(self, path: str) -> bool:
        if path in self.public_paths:
            return True

        return any(
            path.startswith(p.rstrip("/") + "/")
            for p in self.public_paths
        )

    def _cookie_header(self, scope) -> str:
        headers = dict(scope.get("headers") or [])
        return headers.get(b"cookie", b"").decode("utf-8", errors="ignore")

    def _extract_cookie(self, cookie_header: str, name: str) -> Optional[str]:
        # very small cookie parser
        parts = [p.strip() for p in cookie_header.split(";") if "=" in p]

        for p in parts:
            k, v = p.split("=", 1)
            if k.strip() == name:
                return v.strip()

        return None

    def _verify_auth_cookie(self, token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=["HS256"],
                options={"require": ["exp"]},
            )

            # enforce tenant
            if payload.get("tid") != self.tenant_id:
                return None

            return payload

        except Exception:
            return None

    async def __call__(self, scope, receive, send):
        scope_type = scope["type"]
        path = scope.get("path", "")

        if scope_type not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        if self._is_public(path):
            await self.app(scope, receive, send)
            return

        cookie_header = self._cookie_header(scope)
        raw = self._extract_cookie(cookie_header, self.auth_cookie_name)
        path = scope.get("path", "/")
        qs = scope.get("query_string", b"").decode()
        next_url = f"{path}?{qs}" if qs else path

        if not raw:
            if scope_type == "http":
                resp = RedirectResponse(f"/login?next={next_url}")
                await resp(scope, receive, send)
                return

            await send({"type": "websocket.close", "code": 4401})
            return

        claims = self._verify_auth_cookie(raw)

        if not claims:
            if scope_type == "http":
                resp = RedirectResponse(f"/login?next={next_url}")
                await resp(scope, receive, send)
                return

            await send({"type": "websocket.close", "code": 4401})
            return

        await self.app(scope, receive, send)
