# app/main.py
from fastapi import FastAPI
from chainlit.utils import mount_chainlit  # ← from chainlit.utils, not cl_app

app = FastAPI(title="FastAPI + Chainlit 2.9.3")

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

# IMPORTANT: target is the path to your Chainlit file
mount_chainlit(
    app=app,
    target="cl_app/app.py",
    path="/chat",  # Chainlit will be served under /chat
)
