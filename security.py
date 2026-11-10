"""Hash de contraseñas, tokens JWT y control de roles."""
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from database import get_db

# En producción SECRET_KEY debe venir de una variable de entorno.
# Si no existe se genera una aleatoria (los tokens se invalidan al reiniciar).
SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "30"))

ROLES = ("estudiante", "docente", "admin")

_hasher = PasswordHasher()  # Argon2id
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ---------- Contraseñas ----------
def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


# Hash ficticio para gastar el mismo tiempo cuando el correo no existe
# (evita distinguir usuarios existentes por tiempo de respuesta).
DUMMY_HASH = hash_password("contraseña-ficticia")


# ---------- Tokens ----------
def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_MINUTES),
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


_credentials_error = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Credenciales inválidas o sesión expirada",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db)) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise _credentials_error

    # El rol se lee de la base de datos, no del token.
    row = db.execute(
        "SELECT id, nombre, email, role FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    if row is None:
        raise _credentials_error
    return dict(row)


def require_roles(*allowed: str):
    """Dependencia que exige uno de los roles indicados (HTTP 403 si no)."""

    def checker(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "No tiene permisos para esta acción")
        return user

    return checker
