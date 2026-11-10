"""Conexión a SQLite y creación del esquema."""
import os
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre        TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    role          TEXT    NOT NULL DEFAULT 'estudiante'
                  CHECK (role IN ('estudiante', 'docente', 'admin')),
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL,
    description TEXT    NOT NULL DEFAULT '',
    status      TEXT    NOT NULL DEFAULT 'pendiente'
                CHECK (status IN ('pendiente', 'en_progreso', 'completada')),
    owner_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""


def db_path() -> str:
    # Se lee en cada llamada para que las pruebas puedan usar otra base de datos.
    return os.getenv("DB_PATH", "tareas.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def get_db():
    """Dependencia de FastAPI: una conexión por solicitud."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()
