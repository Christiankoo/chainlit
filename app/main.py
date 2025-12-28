# app/main.py
import os
import time
import base64
import secrets
import requests
import jwt
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, PlainTextResponse
from starlette.middleware.sessions import SessionMiddleware

from chainlit.utils import mount_chainlit
from app.auth_middleware import AuthGate

TENANT_ID = os.environ.get("AZURE_TENANT_ID")
CLIENT_ID = os.environ.get("AZURE_CLIENT_ID")
REDIRECT_URI = os.environ.get("AZURE_REDIRECT_URI")
SECRET_ID = os.environ.get("AZURE_SECRET_ID")
SESSION_SECRET= "change-me-to-a-long-random-string"

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0"
AUTHORIZE_URL = f"{AUTHORITY}/authorize"
TOKEN_URL = f"{AUTHORITY}/token"
JWKS_URL = f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys"
PUBLIC_PATHS = {
    "/healthz",
    "/login",
    "/auth/callback",
}

app = FastAPI(title="FastAPI + Chainlit")

app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET, same_site="lax", https_only=False)

app.add_middleware(
    AuthGate,
    tenant_id=TENANT_ID,
    public_paths=PUBLIC_PATHS,
    jwt_secret=SESSION_SECRET,
)

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

@app.get("/login")
def login(request: Request, next: str | None = "/chat"):
    request.session["next"] = next
    # optional anti-CSRF state
    state = _b64url(secrets.token_bytes(16))
    request.session["oidc_state"] = state

    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "response_mode": "query",
        "scope": "openid profile email",
        "state": state
    }

    url = requests.Request("GET", AUTHORIZE_URL, params=params).prepare().url
    return RedirectResponse(url)

def _get_jwks():
    return requests.get(JWKS_URL, timeout=10).json()

@app.get("/auth/callback")
def callback(request: Request, code: str | None = None, state: str | None = None, error: str | None = None):
    if error:
        return PlainTextResponse(f"Entra error: {error}", status_code=400)
    if not code:
        return PlainTextResponse("Missing code", status_code=400)

    expected_state = request.session.get("oidc_state")
    if expected_state and state != expected_state:
        return PlainTextResponse("Invalid state", status_code=400)

    token_resp = requests.post(
        TOKEN_URL,
        data={
            "client_id": CLIENT_ID,
            "grant_type": "authorization_code",
            "code": code,
            "client_secret": SECRET_ID,
            "redirect_uri": REDIRECT_URI
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

    issuer = f"https://login.microsoftonline.com/{TENANT_ID}/v2.0"

    try:
        claims = jwt.decode(
            id_token,
            key=key,
            algorithms=["RS256"],
            audience=CLIENT_ID,
            issuer=issuer,
            options={"require": ["exp", "iat", "iss", "aud"]},
        )
    except Exception as e:
        return PlainTextResponse(f"Invalid id_token: {e}", status_code=400)

    # Enforce tenant (defense-in-depth even though app is single-tenant)
    if claims.get("tid") != TENANT_ID:
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
    app_token = jwt.encode(app_claims, SESSION_SECRET, algorithm="HS256")

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

# Chainlit served under /chat
mount_chainlit(app=app, target="cl_app/app.py", path="/chat")