"""Crea (o promueve) un usuario administrador desde la consola.

Uso:
    python create_admin.py
"""
import getpass

from database import get_connection, init_db
from security import hash_password


def main() -> None:
    init_db()
    nombre = input("Nombre: ").strip()
    email = input("Correo: ").strip().lower()
    password = getpass.getpass("Contraseña (mín. 8 caracteres): ")
    if len(password) < 8:
        print("La contraseña debe tener al menos 8 caracteres.")
        return

    conn = get_connection()
    try:
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            conn.execute("UPDATE users SET role = 'admin' WHERE id = ?", (existing["id"],))
            print(f"Usuario {email} promovido a admin.")
        else:
            conn.execute(
                "INSERT INTO users (nombre, email, password_hash, role) VALUES (?, ?, ?, 'admin')",
                (nombre, email, hash_password(password)),
            )
            print(f"Administrador {email} creado.")
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
