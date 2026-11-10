"""CRUD de tareas con control de acceso por propiedad y rol.

Reglas:
- estudiante: solo ve, edita y elimina sus propias tareas.
- docente:    ve todas las tareas; solo edita y elimina las suyas.
- admin:      ve, edita y elimina cualquier tarea.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from database import get_db
from schemas import TaskCreate, TaskOut, TaskUpdate
from security import get_current_user

router = APIRouter(prefix="/tasks", tags=["Tareas"])

READ_ALL_ROLES = ("docente", "admin")
WRITE_ALL_ROLES = ("admin",)


def _get_task_or_404(db, task_id: int) -> dict:
    row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tarea no encontrada")
    return dict(row)


def _check_access(task: dict, user: dict, privileged_roles: tuple) -> None:
    if task["owner_id"] != user["id"] and user["role"] not in privileged_roles:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No tiene acceso a esta tarea")


@router.get("", response_model=list[TaskOut])
def list_tasks(
    owner_id: Optional[int] = Query(default=None, description="Solo docente/admin"),
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    if user["role"] in READ_ALL_ROLES:
        if owner_id is None:
            rows = db.execute("SELECT * FROM tasks ORDER BY id").fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM tasks WHERE owner_id = ? ORDER BY id", (owner_id,)
            ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM tasks WHERE owner_id = ? ORDER BY id", (user["id"],)
        ).fetchall()
    return [dict(r) for r in rows]


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(data: TaskCreate, user: dict = Depends(get_current_user), db=Depends(get_db)):
    # El dueño siempre es el usuario autenticado, nunca un valor del cliente.
    cur = db.execute(
        "INSERT INTO tasks (title, description, status, owner_id) VALUES (?, ?, ?, ?)",
        (data.title.strip(), data.description, data.status, user["id"]),
    )
    db.commit()
    return _get_task_or_404(db, cur.lastrowid)


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int, user: dict = Depends(get_current_user), db=Depends(get_db)):
    task = _get_task_or_404(db, task_id)
    _check_access(task, user, READ_ALL_ROLES)
    return task


@router.put("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int, data: TaskUpdate, user: dict = Depends(get_current_user), db=Depends(get_db)
):
    task = _get_task_or_404(db, task_id)
    _check_access(task, user, WRITE_ALL_ROLES)

    changes = data.model_dump(exclude_unset=True, exclude_none=True)
    if "title" in changes:
        changes["title"] = changes["title"].strip()
    if not changes:
        return task

    # Nombres de columna fijos (lista blanca); los valores van parametrizados.
    allowed = ("title", "description", "status")
    sets = ", ".join(f"{col} = ?" for col in allowed if col in changes)
    values = [changes[col] for col in allowed if col in changes]
    db.execute(
        f"UPDATE tasks SET {sets}, updated_at = datetime('now') WHERE id = ?",
        (*values, task_id),
    )
    db.commit()
    return _get_task_or_404(db, task_id)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, user: dict = Depends(get_current_user), db=Depends(get_db)):
    task = _get_task_or_404(db, task_id)
    _check_access(task, user, WRITE_ALL_ROLES)
    db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
