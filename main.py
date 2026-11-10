"""API de gestión de tareas – Proyecto base (Guía de Práctica 04, ISW).

Ejecutar:
    python -m uvicorn main:app --reload --port 8000
Documentación interactiva:
    http://127.0.0.1:8000/docs
"""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from database import ensure_admin, init_db
from routers import auth, tasks, users
from security import hash_password


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    admin_email, admin_password = os.getenv("ADMIN_EMAIL"), os.getenv("ADMIN_PASSWORD")
    if admin_email and admin_password:
        ensure_admin(admin_email, admin_password, hash_password)
    yield


app = FastAPI(
    title="API de Gestión de Tareas",
    description="Proyecto base – Guía 04: Ingeniería de software seguro",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(users.router)


STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def frontend():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health", tags=["Estado"])
def health():
    return {"status": "ok"}
