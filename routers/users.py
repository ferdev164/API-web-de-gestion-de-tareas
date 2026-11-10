"""Administración de usuarios (solo admin)."""
from fastapi import APIRouter, Depends, HTTPException, status

from database import get_db
from schemas import RoleUpdate, UserOut
from security import require_roles

router = APIRouter(prefix="/users", tags=["Usuarios (admin)"])


@router.get("", response_model=list[UserOut])
def list_users(_admin: dict = Depends(require_roles("admin")), db=Depends(get_db)):
    rows = db.execute("SELECT id, nombre, email, role FROM users ORDER BY id").fetchall()
    return [dict(r) for r in rows]


@router.patch("/{user_id}/role", response_model=UserOut)
def change_role(
    user_id: int,
    data: RoleUpdate,
    admin: dict = Depends(require_roles("admin")),
    db=Depends(get_db),
):
    if user_id == admin["id"]:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No puede cambiar su propio rol")
    cur = db.execute("UPDATE users SET role = ? WHERE id = ?", (data.role, user_id))
    db.commit()
    if cur.rowcount == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
    row = db.execute("SELECT id, nombre, email, role FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row)
