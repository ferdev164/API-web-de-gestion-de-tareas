# API de Gestión de Tareas – Proyecto base (Guía 04, ISW)

API web en **FastAPI + SQLite** con registro e inicio de sesión, CRUD de tareas y roles
(estudiante, docente, administrador).

## Instalación (Windows / PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Ejecutar

```powershell
python -m uvicorn main:app --reload --port 8000
```

- Documentación interactiva: http://127.0.0.1:8000/docs
- Para probar endpoints protegidos en `/docs`: botón **Authorize** → en *username* va el correo.

Crear un administrador:

```powershell
python create_admin.py
```

Opcional: definir una clave fija para los tokens (si no, se genera una al iniciar
y las sesiones se pierden al reiniciar):

```powershell
$env:SECRET_KEY = "una-clave-larga-y-aleatoria-de-32+caracteres"
```

## Pruebas

```powershell
python -m pytest -v
```

## Estructura

```
main.py            App FastAPI y registro de routers
database.py        Conexión SQLite y esquema (users, tasks)
security.py        Hash Argon2id, JWT con expiración, control de roles
schemas.py         Validación de entrada/salida (Pydantic)
routers/auth.py    /auth/register, /auth/login, /auth/me
routers/tasks.py   CRUD /tasks con control por propiedad y rol
routers/users.py   /users (solo admin): listar y cambiar rol
create_admin.py    Script para crear/promover un admin
tests/             Pruebas automatizadas (pytest)
```

## Endpoints

| Método | Ruta | Descripción | Acceso |
|---|---|---|---|
| POST | `/auth/register` | Registro (siempre como estudiante) | Público |
| POST | `/auth/login` | Devuelve token JWT (30 min) | Público |
| GET | `/auth/me` | Datos del usuario actual | Autenticado |
| GET | `/tasks` | Listar tareas | Propias; docente/admin: todas |
| POST | `/tasks` | Crear tarea (dueño = usuario actual) | Autenticado |
| GET | `/tasks/{id}` | Ver tarea | Dueño, docente, admin |
| PUT | `/tasks/{id}` | Editar tarea | Dueño, admin |
| DELETE | `/tasks/{id}` | Eliminar tarea | Dueño, admin |
| GET | `/users` | Listar usuarios | Admin |
| PATCH | `/users/{id}/role` | Cambiar rol | Admin |

## Modelo de datos

- **users**: id, nombre, email (único), password_hash, role, created_at
- **tasks**: id, title, description, status (`pendiente`, `en_progreso`, `completada`),
  owner_id → users.id, created_at, updated_at

## Controles de seguridad ya incluidos

- Contraseñas con Argon2id (nunca en texto plano).
- Tokens JWT firmados, con expiración; el rol se lee de la BD, no del token.
- Mensaje de login genérico (no revela si el correo existe).
- Registro siempre como `estudiante`; se rechazan campos extra como `role` u `owner_id`.
- Verificación de propiedad en servidor → HTTP 403 ante acceso a tareas ajenas (IDOR).
- Consultas SQL parametrizadas en todos los endpoints.
- Validación: título 3–120, descripción ≤ 1000, estado en lista permitida.

## Pendiente para las siguientes actividades de la guía

- 1.2: límite de intentos/bloqueo progresivo, logout y revocación de sesión,
  recuperación de contraseña con token de un solo uso.
- 3.1 y 4.1: versión insegura de `POST /tasks` y de búsqueda para comparar antes/después,
  registro de eventos de validación fallida.
- Actividad 3/4: `app_vulnerable.py` y `app_segura.py` (caso SportReserve).
