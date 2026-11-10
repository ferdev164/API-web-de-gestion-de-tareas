"""Modelos de entrada y salida (Pydantic)."""
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

Role = Literal["estudiante", "docente", "admin"]
TaskStatus = Literal["pendiente", "en_progreso", "completada"]


# ---------- Usuarios ----------
class UserRegister(BaseModel):
    model_config = ConfigDict(extra="forbid")  # rechaza campos como "role"

    nombre: str = Field(min_length=2, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    id: int
    nombre: str
    email: EmailStr
    role: Role


class RoleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Role


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Tareas ----------
class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")  # rechaza owner_id, id, etc.

    title: str = Field(min_length=3, max_length=120)
    description: str = Field(default="", max_length=1000)
    status: TaskStatus = "pendiente"


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = Field(default=None, min_length=3, max_length=120)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: Optional[TaskStatus] = None


class TaskOut(BaseModel):
    id: int
    title: str
    description: str
    status: TaskStatus
    owner_id: int
    created_at: str
    updated_at: str
