# app/main.py
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from chainlit.utils import mount_chainlit
from app.middleware.auth_middleware import AuthGate
from app.crud.sessions import router_crud
from app.entraid.entraid import router_entra_id
from app.config import TENANT_ID, SESSION_SECRET, PUBLIC_PATHS, setup_telemetry

app = FastAPI(title="FastAPI + Chainlit")

setup_telemetry()

app.include_router(router_crud)
app.include_router(router_entra_id)

# Chainlit served under /chat
mount_chainlit(
    app=app, 
    target="cl_app/app.py", 
    path="/"
)

# Session middleware
app.add_middleware(
    SessionMiddleware, 
    secret_key=SESSION_SECRET, 
    same_site="lax", 
    https_only=False
)

# Auth middleware
app.add_middleware(
    AuthGate,
    tenant_id=TENANT_ID,
    public_paths=PUBLIC_PATHS,
    jwt_secret=SESSION_SECRET,
)

# Health check endpoint
@app.get("/healthz")
def healthz():
    return {"status": "ok"}