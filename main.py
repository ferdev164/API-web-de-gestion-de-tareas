"""API de gestión de tareas – Proyecto base (Guía de Práctica 04, ISW).

Ejecutar:
    python -m uvicorn main:app --reload --port 8000
Documentación interactiva:
    http://127.0.0.1:8000/docs
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from database import init_db
from routers import auth, tasks, users


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
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


@app.get("/", tags=["Estado"])
def root():
    return {"mensaje": "API de gestión de tareas funcionando", "docs": "/docs"}
