import time
import base64
import secrets
import requests
import jwt

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, PlainTextResponse

import app.config as config

router_entra_id = APIRouter(prefix="/api/auth", tags=["entraid"])

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

def _get_jwks():
    return requests.get(config.JWKS_URL, timeout=10).json()

@router_entra_id.get("/login")
def login(request: Request, next: str | None = "/chat"):
    request.session["next"] = next
    # optional anti-CSRF state
    state = _b64url(secrets.token_bytes(16))
    request.session["oidc_state"] = state

    params = {
        "client_id": config.CLIENT_ID,
        "response_type": "code",
        "redirect_uri": config.REDIRECT_URI,
        "response_mode": "query",
        "scope": "openid profile email",
        "state": state,
        "prompt": "select_account",
    }

    url = requests.Request("GET", config.AUTHORIZE_URL, params=params).prepare().url
    return RedirectResponse(url)

@router_entra_id.get("/callback")
def callback(request: Request, code: str | None = None, state: str | None = None, error: str | None = None):
    if error:
        return PlainTextResponse(f"Entra error: {error}", status_code=400)
    if not code:
        return PlainTextResponse("Missing code", status_code=400)

    expected_state = request.session.get("oidc_state")
    if (expected_state and state != expected_state) or (not expected_state) or (not state):
        return PlainTextResponse("Invalid state", status_code=400)

    token_resp = requests.post(
        config.TOKEN_URL,
        data={
            "client_id": config.CLIENT_ID,
            "grant_type": "authorization_code",
            "code": code,
            "client_secret": config.SECRET_ID,
            "redirect_uri": config.REDIRECT_URI
        },
        timeout=10,
    )
    if token_resp.status_code != 200:
        return PlainTextResponse(f"Token exchange failed: {token_resp.text}", status_code=400)

    tokens = token_resp.json()
    id_token = tokens.get("id_token")
    if not id_token:
        return PlainTextResponse("No id_token returned", status_code=400)

    # Validate id_token signature + standard claims using JWKS
    jwks = _get_jwks()
    unverified_header = jwt.get_unverified_header(id_token)

    key = None
    for k in jwks.get("keys", []):
        if k.get("kid") == unverified_header.get("kid"):
            key = jwt.algorithms.RSAAlgorithm.from_jwk(k)
            break
    if not key:
        return PlainTextResponse("Unable to find signing key", status_code=400)

    issuer = f"https://login.microsoftonline.com/{config.TENANT_ID}/v2.0"

    try:
        claims = jwt.decode(
            id_token,
            key=key,
            algorithms=["RS256"],
            audience=config.CLIENT_ID,
            issuer=issuer,
            options={"require": ["exp", "iat", "iss", "aud"]},
        )
    except Exception as e:
        return PlainTextResponse(f"Invalid id_token: {e}", status_code=400)

    # Enforce tenant (defense-in-depth even though app is single-tenant)
    if claims.get("tid") != config.TENANT_ID:
        return PlainTextResponse("Forbidden: wrong tenant", status_code=403)

    # Create our own app cookie for gate (works for HTTP + WS)
    now = int(time.time())
    app_claims = {
        "tid": claims.get("tid"),
        "oid": claims.get("oid"),
        "name": claims.get("name"),
        "preferred_username": claims.get("preferred_username"),
        "iat": now,
        "exp": now + 60 * 60,  # 1 hour
    }
    app_token = jwt.encode(app_claims, config.SESSION_SECRET, algorithm="HS256")

    next_url = request.session.get("next", "/chat")
    resp = RedirectResponse(url=next_url, status_code=302)
    resp.set_cookie(
        "cl_auth",
        app_token,
        httponly=True,
        samesite="lax",
        secure=False,  # set True when on HTTPS in Azure
        path="/",
    )

    # cleanup one-time session values
    request.session.pop("oidc_state", None)
    request.session.pop("next", None)

    return resp