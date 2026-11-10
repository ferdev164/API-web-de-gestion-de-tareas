from datetime import datetime, timedelta, timezone

import jwt

from conftest import auth_headers, login, register
from database import get_connection
from security import ALGORITHM, SECRET_KEY


def test_registro_exitoso_crea_estudiante(client):
    r = register(client, "ana@test.com")
    assert r.status_code == 201
    assert r.json()["role"] == "estudiante"
    assert "password" not in r.json()


def test_registro_rechaza_role_inyectado(client):
    r = client.post("/auth/register", json={
        "nombre": "Eva", "email": "eva@test.com", "password": "Clave12345", "role": "admin"})
    assert r.status_code == 422


def test_registro_correo_duplicado(client):
    register(client, "ana@test.com")
    assert register(client, "ana@test.com").status_code == 400


def test_registro_password_corta(client):
    assert register(client, "ana@test.com", password="123").status_code == 422


def test_password_guardada_con_argon2(client):
    register(client, "ana@test.com")
    conn = get_connection()
    h = conn.execute("SELECT password_hash FROM users WHERE email='ana@test.com'").fetchone()[0]
    conn.close()
    assert h.startswith("$argon2id$")
    assert "Clave12345" not in h


def test_login_exitoso(client):
    register(client, "ana@test.com")
    r = login(client, "ana@test.com")
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"


def test_login_mensaje_generico(client):
    register(client, "ana@test.com")
    r1 = login(client, "ana@test.com", "incorrecta")
    r2 = login(client, "noexiste@test.com", "incorrecta")
    assert r1.status_code == r2.status_code == 401
    assert r1.json()["detail"] == r2.json()["detail"]


def test_me_sin_token(client):
    assert client.get("/auth/me").status_code == 401


def test_me_con_token(client):
    register(client, "ana@test.com")
    r = client.get("/auth/me", headers=auth_headers(client, "ana@test.com"))
    assert r.status_code == 200
    assert r.json()["email"] == "ana@test.com"


def test_token_expirado(client):
    register(client, "ana@test.com")
    expired = jwt.encode(
        {"sub": "1", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        SECRET_KEY, algorithm=ALGORITHM)
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert r.status_code == 401


def test_token_falsificado(client):
    register(client, "ana@test.com")
    fake = jwt.encode({"sub": "1"}, "otra-clave-secreta-de-al-menos-32-bytes!!", algorithm=ALGORITHM)
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {fake}"})
    assert r.status_code == 401
