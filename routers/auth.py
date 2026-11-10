"""Registro, inicio de sesión y perfil."""
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from database import get_db
from schemas import Token, UserOut, UserRegister
from security import (
    DUMMY_HASH,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: UserRegister, db=Depends(get_db)):
    # Todo usuario nuevo es "estudiante"; solo un admin puede cambiar roles.
    try:
        cur = db.execute(
            "INSERT INTO users (nombre, email, password_hash, role) VALUES (?, ?, ?, 'estudiante')",
            (data.nombre.strip(), data.email.lower(), hash_password(data.password)),
        )
        db.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No se pudo completar el registro")
    return {"id": cur.lastrowid, "nombre": data.nombre.strip(),
            "email": data.email.lower(), "role": "estudiante"}


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    """En el campo `username` va el correo."""
    row = db.execute(
        "SELECT id, password_hash FROM users WHERE email = ?", (form.username.lower(),)
    ).fetchone()

    # Se verifica siempre un hash para no revelar si el correo existe.
    ok = verify_password(row["password_hash"] if row else DUMMY_HASH, form.password)
    if not row or not ok:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": create_access_token(row["id"]), "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
def me(user: dict = Depends(get_current_user)):
    return user
