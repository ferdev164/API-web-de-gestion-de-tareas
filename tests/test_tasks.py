import pytest

from conftest import auth_headers, create_admin, register, set_role


@pytest.fixture
def users(client):
    """Crea dos estudiantes, un docente y un admin; devuelve sus headers."""
    for email in ("a@test.com", "b@test.com", "doc@test.com"):
        register(client, email)
    set_role("doc@test.com", "docente")
    create_admin()
    return {
        "a": auth_headers(client, "a@test.com"),
        "b": auth_headers(client, "b@test.com"),
        "doc": auth_headers(client, "doc@test.com"),
        "admin": auth_headers(client, "admin@test.com"),
    }


def new_task(client, headers, title="Tarea de prueba", **extra):
    return client.post("/tasks", json={"title": title, **extra}, headers=headers)


# ---------- CRUD básico ----------
def test_crear_tarea(client, users):
    r = new_task(client, users["a"], description="Detalle")
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "pendiente"
    assert body["owner_id"] == 1


def test_listar_solo_propias(client, users):
    new_task(client, users["a"], "Tarea de A")
    new_task(client, users["b"], "Tarea de B")
    titles = [t["title"] for t in client.get("/tasks", headers=users["a"]).json()]
    assert titles == ["Tarea de A"]


def test_editar_tarea_propia(client, users):
    tid = new_task(client, users["a"]).json()["id"]
    r = client.put(f"/tasks/{tid}", json={"status": "completada"}, headers=users["a"])
    assert r.status_code == 200
    assert r.json()["status"] == "completada"


def test_eliminar_tarea_propia(client, users):
    tid = new_task(client, users["a"]).json()["id"]
    assert client.delete(f"/tasks/{tid}", headers=users["a"]).status_code == 204
    assert client.get(f"/tasks/{tid}", headers=users["a"]).status_code == 404


# ---------- Autorización (IDOR) ----------
def test_idor_ver_tarea_ajena_403(client, users):
    tid = new_task(client, users["a"]).json()["id"]
    r = client.get(f"/tasks/{tid}", headers=users["b"])
    assert r.status_code == 403
    assert "title" not in r.json()


def test_idor_editar_tarea_ajena_403(client, users):
    tid = new_task(client, users["a"]).json()["id"]
    assert client.put(f"/tasks/{tid}", json={"title": "Hackeado"}, headers=users["b"]).status_code == 403


def test_idor_eliminar_tarea_ajena_403(client, users):
    tid = new_task(client, users["a"]).json()["id"]
    assert client.delete(f"/tasks/{tid}", headers=users["b"]).status_code == 403


def test_no_se_puede_asignar_owner_id(client, users):
    r = new_task(client, users["a"], owner_id=2)
    assert r.status_code == 422


def test_sin_token_401(client):
    assert client.get("/tasks").status_code == 401
    assert client.post("/tasks", json={"title": "abc"}).status_code == 401


# ---------- Roles ----------
def test_docente_ve_todas_pero_no_edita_ajenas(client, users):
    tid = new_task(client, users["a"]).json()["id"]
    assert len(client.get("/tasks", headers=users["doc"]).json()) == 1
    assert client.get(f"/tasks/{tid}", headers=users["doc"]).status_code == 200
    assert client.put(f"/tasks/{tid}", json={"title": "Cambio"}, headers=users["doc"]).status_code == 403


def test_admin_edita_y_elimina_ajenas(client, users):
    tid = new_task(client, users["a"]).json()["id"]
    assert client.put(f"/tasks/{tid}", json={"title": "Revisada"}, headers=users["admin"]).status_code == 200
    assert client.delete(f"/tasks/{tid}", headers=users["admin"]).status_code == 204


def test_solo_admin_lista_usuarios(client, users):
    assert client.get("/users", headers=users["a"]).status_code == 403
    assert client.get("/users", headers=users["admin"]).status_code == 200


def test_admin_cambia_rol(client, users):
    r = client.patch("/users/2/role", json={"role": "docente"}, headers=users["admin"])
    assert r.status_code == 200 and r.json()["role"] == "docente"


def test_estudiante_no_puede_cambiar_roles(client, users):
    assert client.patch("/users/1/role", json={"role": "admin"}, headers=users["a"]).status_code == 403


# ---------- Validación ----------
@pytest.mark.parametrize("payload", [
    {"title": ""},
    {"title": "ab"},
    {"title": "x" * 121},
    {"title": "Válido", "description": "x" * 1001},
    {"title": "Válido", "status": "terminada"},
])
def test_validacion_rechaza_datos_invalidos(client, users, payload):
    assert client.post("/tasks", json=payload, headers=users["a"]).status_code == 422


def test_acepta_unicode(client, users):
    r = new_task(client, users["a"], "Revisar ñandú 📚")
    assert r.status_code == 201
    assert r.json()["title"] == "Revisar ñandú 📚"
