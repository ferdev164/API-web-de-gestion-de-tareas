import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_connection  # noqa: E402
from main import app  # noqa: E402
from security import hash_password  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Cada prueba usa una base de datos nueva y temporal.
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    with TestClient(app) as c:
        yield c


def register(client, email, password="Clave12345", nombre="Usuario"):
    return client.post("/auth/register", json={"nombre": nombre, "email": email, "password": password})


def login(client, email, password="Clave12345"):
    r = client.post("/auth/login", data={"username": email, "password": password})
    return r


def auth_headers(client, email, password="Clave12345"):
    token = login(client, email, password).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def set_role(email, role):
    conn = get_connection()
    conn.execute("UPDATE users SET role = ? WHERE email = ?", (role, email))
    conn.commit()
    conn.close()


def create_admin(email="admin@test.com", password="Clave12345"):
    conn = get_connection()
    conn.execute(
        "INSERT INTO users (nombre, email, password_hash, role) VALUES (?, ?, ?, 'admin')",
        ("Admin", email, hash_password(password)),
    )
    conn.commit()
    conn.close()
