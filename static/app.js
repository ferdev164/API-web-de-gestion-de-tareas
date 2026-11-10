// Frontend de la API de gestión de tareas.
// Todo el contenido del usuario se inserta con textContent (nunca innerHTML) para evitar XSS.

const STATUS_LABEL = { pendiente: "Pendiente", en_progreso: "En progreso", completada: "Completada" };
const ROLE_LABEL = { estudiante: "Estudiante", docente: "Docente", admin: "Administrador" };

let token = sessionStorage.getItem("token");
let currentUser = null;
let tasks = [];
let editingId = null;

const $ = (sel) => document.querySelector(sel);

// ---------- Utilidades ----------
function toast(msg, isError = false) {
  const el = $("#toast");
  el.textContent = msg;
  el.className = isError ? "error" : "";
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => el.classList.add("hidden"), 3000);
}

function errorMessage(data, fallback) {
  if (!data || !data.detail) return fallback;
  if (typeof data.detail === "string") return data.detail;
  if (Array.isArray(data.detail)) {
    return data.detail.map((d) => `${(d.loc || []).slice(-1)[0]}: ${d.msg}`).join(" · ");
  }
  return fallback;
}

async function api(path, { method = "GET", body, form } = {}) {
  const headers = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  let payload;
  if (form) {
    payload = new URLSearchParams(form);
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  const res = await fetch(path, { method, headers, body: payload });
  if (res.status === 401 && token) {
    logout();
    throw new Error("Tu sesión expiró. Inicia sesión de nuevo.");
  }
  const data = res.status === 204 ? null : await res.json().catch(() => null);
  if (!res.ok) throw new Error(errorMessage(data, `Error ${res.status}`));
  return data;
}

function el(tag, props = {}, children = []) {
  const node = document.createElement(tag);
  Object.entries(props).forEach(([k, v]) => {
    if (k === "text") node.textContent = v;
    else if (k === "class") node.className = v;
    else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v);
  });
  children.forEach((c) => c && node.appendChild(c));
  return node;
}

// ---------- Autenticación ----------
document.querySelectorAll(".tab").forEach((tab) =>
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    const isLogin = tab.dataset.tab === "login";
    $("#login-form").classList.toggle("hidden", !isLogin);
    $("#register-form").classList.toggle("hidden", isLogin);
  })
);

$("#login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const f = new FormData(e.target);
  try {
    const data = await api("/auth/login", {
      method: "POST",
      form: { username: f.get("email"), password: f.get("password") },
    });
    token = data.access_token;
    sessionStorage.setItem("token", token);
    e.target.reset();
    await startApp();
  } catch (err) {
    toast(err.message, true);
  }
});

$("#register-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const f = new FormData(e.target);
  try {
    await api("/auth/register", {
      method: "POST",
      body: { nombre: f.get("nombre"), email: f.get("email"), password: f.get("password") },
    });
    toast("Cuenta creada. Ahora inicia sesión.");
    e.target.reset();
    document.querySelector('.tab[data-tab="login"]').click();
  } catch (err) {
    toast(err.message, true);
  }
});

function logout() {
  token = null;
  currentUser = null;
  sessionStorage.removeItem("token");
  $("#app-view").classList.add("hidden");
  $("#user-info").classList.add("hidden");
  $("#auth-view").classList.remove("hidden");
}
$("#btn-logout").addEventListener("click", logout);

// ---------- Tareas ----------
function canEdit(task) {
  return currentUser && (task.owner_id === currentUser.id || currentUser.role === "admin");
}

function renderTasks() {
  const filter = $("#filter-status").value;
  const list = $("#task-list");
  list.replaceChildren();
  const visible = tasks.filter((t) => !filter || t.status === filter);
  $("#empty-msg").classList.toggle("hidden", visible.length > 0);

  visible.forEach((t) => {
    const actions = el("div");
    if (canEdit(t)) {
      actions.append(
        el("button", { class: "link", text: "Editar", onclick: () => openEdit(t) }),
        el("button", { class: "danger", text: "Eliminar", onclick: () => deleteTask(t) })
      );
    }
    const owner = t.owner_id === currentUser.id ? "Tú" : `Usuario #${t.owner_id}`;
    list.appendChild(
      el("li", { class: "task", "data-status": t.status }, [
        el("div", { class: "task-head" }, [
          el("span", { class: "task-title", text: t.title }),
          el("span", { class: `badge ${t.status}`, text: STATUS_LABEL[t.status] }),
        ]),
        t.description ? el("div", { class: "task-desc", text: t.description }) : null,
        el("div", { class: "task-meta" }, [
          el("span", { text: `${owner} · ${t.updated_at}` }),
          actions,
        ]),
      ])
    );
  });
}

async function loadTasks() {
  try {
    tasks = await api("/tasks");
    renderTasks();
  } catch (err) {
    toast(err.message, true);
  }
}

$("#filter-status").addEventListener("change", renderTasks);

$("#task-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const f = new FormData(e.target);
  try {
    await api("/tasks", {
      method: "POST",
      body: { title: f.get("title"), description: f.get("description"), status: f.get("status") },
    });
    e.target.reset();
    toast("Tarea creada");
    loadTasks();
  } catch (err) {
    toast(err.message, true);
  }
});

async function deleteTask(task) {
  if (!confirm(`¿Eliminar la tarea "${task.title}"?`)) return;
  try {
    await api(`/tasks/${task.id}`, { method: "DELETE" });
    toast("Tarea eliminada");
    loadTasks();
  } catch (err) {
    toast(err.message, true);
  }
}

function openEdit(task) {
  editingId = task.id;
  const form = $("#edit-form");
  form.elements.title.value = task.title;
  form.elements.description.value = task.description;
  form.elements.status.value = task.status;
  $("#edit-dialog").showModal();
}

$("#edit-cancel").addEventListener("click", () => $("#edit-dialog").close());

$("#edit-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  try {
    await api(`/tasks/${editingId}`, {
      method: "PUT",
      body: { title: form.elements.title.value, description: form.elements.description.value, status: form.elements.status.value },
    });
    $("#edit-dialog").close();
    toast("Tarea actualizada");
    loadTasks();
  } catch (err) {
    toast(err.message, true);
  }
});

// ---------- Administración ----------
async function loadUsers() {
  try {
    const users = await api("/users");
    const tbody = $("#user-table");
    tbody.replaceChildren();
    users.forEach((u) => {
      const select = el("select");
      Object.entries(ROLE_LABEL).forEach(([value, label]) => {
        const opt = el("option", { value, text: label });
        if (u.role === value) opt.selected = true;
        select.appendChild(opt);
      });
      if (u.id === currentUser.id) select.disabled = true;
      select.addEventListener("change", async () => {
        try {
          await api(`/users/${u.id}/role`, { method: "PATCH", body: { role: select.value } });
          toast(`Rol de ${u.nombre} actualizado`);
        } catch (err) {
          toast(err.message, true);
          select.value = u.role;
        }
      });
      tbody.appendChild(
        el("tr", {}, [
          el("td", { text: String(u.id) }),
          el("td", { text: u.nombre }),
          el("td", { text: u.email }),
          el("td", {}, [select]),
        ])
      );
    });
  } catch (err) {
    toast(err.message, true);
  }
}

// ---------- Inicio ----------
async function startApp() {
  try {
    currentUser = await api("/auth/me");
  } catch {
    logout();
    return;
  }
  $("#auth-view").classList.add("hidden");
  $("#app-view").classList.remove("hidden");
  $("#user-info").classList.remove("hidden");
  $("#user-label").textContent = `${currentUser.nombre} (${ROLE_LABEL[currentUser.role]})`;
  $("#tasks-title").textContent = currentUser.role === "estudiante" ? "Mis tareas" : "Todas las tareas";

  const isAdmin = currentUser.role === "admin";
  $("#admin-panel").classList.toggle("hidden", !isAdmin);
  await loadTasks();
  if (isAdmin) loadUsers();
}

if (token) startApp();
