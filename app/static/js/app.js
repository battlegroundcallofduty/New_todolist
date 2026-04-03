// Todo App - Frontend Logic

const API_TODOS = "/api/todos";
const API_CATS  = "/api/categories";

// ── DOM refs ──────────────────────────────────────────────────
const todoForm         = document.getElementById("todo-form");
const todoInput        = document.getElementById("todo-input");
const dueDateInput     = document.getElementById("due-date-input");
const categoryFormSel  = document.getElementById("category-select-form");
const todoList         = document.getElementById("todo-list");
const emptyState       = document.getElementById("empty-state");
const errorState       = document.getElementById("error-state");
const listContainer    = document.getElementById("todo-list-container");
const categoryList     = document.getElementById("category-list");     // 사이드바 ul
const sidebarAddBtn    = document.getElementById("sidebar-add-btn");
const sidebarAddForm   = document.getElementById("sidebar-add-form");
const categoryInput    = document.getElementById("category-input");
const categoryMobSel   = document.getElementById("category-select-mobile");
const themeToggle      = document.getElementById("theme-toggle");
const themeIcon        = document.getElementById("theme-icon");

let todos      = [];
let categories = [];
let activeCategory = "all";  // "all" | category id (number)

// ── 다크모드 ──────────────────────────────────────────────────

function applyTheme(dark) {
  document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
  themeIcon.textContent = dark ? "\u2602" : "\u2600";  // ☂ / ☀
}

function initTheme() {
  const saved = localStorage.getItem("theme");
  const dark = saved === "dark";
  applyTheme(dark);
}

themeToggle.addEventListener("click", () => {
  const isDark = document.documentElement.getAttribute("data-theme") === "dark";
  const next = !isDark;
  applyTheme(next);
  localStorage.setItem("theme", next ? "dark" : "light");
});

// ── API helpers ───────────────────────────────────────────────

async function apiFetch(url, options = {}) {
  const res = await fetch(url, options);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  if (res.status === 204) return null;
  return res.json();
}

// ── Category API ──────────────────────────────────────────────

async function fetchCategories() {
  categories = await apiFetch(API_CATS + "/");
  renderSidebar();
  renderCategorySelects();
}

async function addCategory(name) {
  const cat = await apiFetch(API_CATS + "/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  categories.push(cat);
  renderSidebar();
  renderCategorySelects();
}

async function deleteCategory(id) {
  await apiFetch(`${API_CATS}/${id}`, { method: "DELETE" });
  categories = categories.filter((c) => c.id !== id);
  if (activeCategory === id) activeCategory = "all";
  renderSidebar();
  renderCategorySelects();
  renderTodos();
}

// ── Todo API ──────────────────────────────────────────────────

async function fetchTodos() {
  listContainer.classList.add("loading");
  errorState.hidden = true;
  try {
    todos = await apiFetch(API_TODOS + "/");
    renderTodos();
  } catch {
    errorState.hidden = false;
    emptyState.hidden = true;
  } finally {
    listContainer.classList.remove("loading");
  }
}

async function addTodo(title, dueDate, categoryId) {
  const body = { title };
  if (dueDate)      body.due_date    = dueDate;
  if (categoryId)   body.category_id = categoryId;
  const todo = await apiFetch(API_TODOS + "/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  todos.push(todo);
  renderTodos();
}

async function toggleTodo(id, completed) {
  const updated = await apiFetch(`${API_TODOS}/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ completed }),
  });
  todos = todos.map((t) => (t.id === id ? updated : t));
}

async function deleteTodo(id) {
  await apiFetch(`${API_TODOS}/${id}`, { method: "DELETE" });
  todos = todos.filter((t) => t.id !== id);
}

async function updateTodoTitle(id, title) {
  const updated = await apiFetch(`${API_TODOS}/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  todos = todos.map((t) => (t.id === id ? updated : t));
  return updated;
}

// ── Rendering: Sidebar ────────────────────────────────────────

function renderSidebar() {
  // 기존 카테고리 항목만 제거 (전체 항목은 유지)
  const items = categoryList.querySelectorAll(".category-item[data-id]");
  items.forEach((el) => {
    if (el.dataset.id !== "all") el.remove();
  });

  // 전체 항목 active 상태 갱신
  const allItem = categoryList.querySelector('[data-id="all"]');
  allItem.classList.toggle("active", activeCategory === "all");

  categories.forEach((cat) => {
    const li = document.createElement("li");
    li.className = "category-item" + (activeCategory === cat.id ? " active" : "");
    li.dataset.id = cat.id;

    const nameSpan = document.createElement("span");
    nameSpan.className = "category-name";
    nameSpan.textContent = cat.name;

    const delBtn = document.createElement("button");
    delBtn.className = "category-delete-btn";
    delBtn.setAttribute("aria-label", "카테고리 삭제");
    delBtn.textContent = "×";
    delBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      deleteCategory(cat.id);
    });

    li.appendChild(nameSpan);
    li.appendChild(delBtn);
    li.addEventListener("click", () => setActiveCategory(cat.id));
    categoryList.appendChild(li);
  });

  // 전체 항목 클릭 이벤트 (중복 방지: 매번 새로 등록하지 않고 이미 있으면 skip)
  if (!allItem._listenerAdded) {
    allItem.addEventListener("click", () => setActiveCategory("all"));
    allItem._listenerAdded = true;
  }
}

function renderCategorySelects() {
  // 폼 내 select + 모바일 select 동기화
  [categoryFormSel, categoryMobSel].forEach((sel) => {
    const currentVal = sel.value;
    // 기존 동적 옵션 제거
    Array.from(sel.options).forEach((opt) => {
      if (opt.dataset.dynamic) opt.remove();
    });
    categories.forEach((cat) => {
      const opt = document.createElement("option");
      opt.value = cat.id;
      opt.textContent = cat.name;
      opt.dataset.dynamic = "1";
      sel.appendChild(opt);
    });
    sel.value = currentVal;
  });
}

function setActiveCategory(id) {
  activeCategory = id;
  renderSidebar();
  // 모바일 드롭다운 동기화
  categoryMobSel.value = id === "all" ? "all" : id;
  renderTodos();
}

// ── Rendering: Todos ──────────────────────────────────────────

function getFilteredTodos() {
  if (activeCategory === "all") return todos;
  return todos.filter((t) => t.category_id === activeCategory);
}

function formatDueDate(dateStr) {
  if (!dateStr) return null;
  // dateStr: "YYYY-MM-DD"
  const [y, m, d] = dateStr.split("-").map(Number);
  return `${m}/${d}`;
}

function isDueDateOverdue(dateStr) {
  if (!dateStr) return false;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const due = new Date(dateStr + "T00:00:00");
  return due < today;
}

function renderTodos() {
  todoList.innerHTML = "";
  const visible = getFilteredTodos();

  if (visible.length === 0) {
    emptyState.hidden = false;
  } else {
    emptyState.hidden = true;
    visible.forEach((todo) => {
      todoList.appendChild(createTodoElement(todo));
    });
  }
}

function getCategoryName(catId) {
  if (!catId) return null;
  const cat = categories.find((c) => c.id === catId);
  return cat ? cat.name : null;
}

function createTodoElement(todo) {
  const li = document.createElement("li");
  li.className = "todo-item" + (todo.completed ? " completed" : "");
  li.dataset.id = todo.id;

  // 체크박스
  const checkbox = document.createElement("div");
  checkbox.className = "todo-checkbox";
  const mark = document.createElement("span");
  mark.className = "todo-checkbox-mark";
  mark.innerHTML = "&#10003;";
  checkbox.appendChild(mark);
  checkbox.addEventListener("click", () => handleToggle(li, todo));

  // 바디 (타이틀 + 메타)
  const body = document.createElement("div");
  body.className = "todo-body";

  const titleSpan = document.createElement("span");
  titleSpan.className = "todo-title";
  titleSpan.textContent = todo.title;
  if (!todo.completed) {
    titleSpan.addEventListener("dblclick", () => startEditing(li, todo));
  }

  body.appendChild(titleSpan);

  // 메타 (마감일 + 카테고리)
  const hasDue = !!todo.due_date;
  const catName = getCategoryName(todo.category_id);
  if (hasDue || catName) {
    const meta = document.createElement("div");
    meta.className = "todo-meta";

    if (hasDue) {
      const dateSpan = document.createElement("span");
      dateSpan.className = "todo-due-date" + (isDueDateOverdue(todo.due_date) && !todo.completed ? " overdue" : "");
      dateSpan.textContent = formatDueDate(todo.due_date);
      meta.appendChild(dateSpan);
    }

    if (catName) {
      const badge = document.createElement("span");
      badge.className = "todo-category-badge";
      badge.textContent = catName;
      meta.appendChild(badge);
    }

    body.appendChild(meta);
  }

  // 삭제 버튼
  const deleteBtn = document.createElement("button");
  deleteBtn.className = "todo-delete";
  deleteBtn.setAttribute("aria-label", "삭제");
  deleteBtn.textContent = "×";
  deleteBtn.addEventListener("click", () => handleDelete(li, todo.id));

  li.appendChild(checkbox);
  li.appendChild(body);
  li.appendChild(deleteBtn);

  return li;
}

// ── Interactions ──────────────────────────────────────────────

function handleToggle(li, todo) {
  const newCompleted = !todo.completed;
  // Optimistic update
  todo.completed = newCompleted;
  li.classList.toggle("completed", newCompleted);

  toggleTodo(todo.id, newCompleted)
    .then(() => {
      // 완료 상태 변경 후 목록 재렌더 (완료항목 하단 이동)
      renderTodos();
    })
    .catch(() => {
      // Rollback
      todo.completed = !newCompleted;
      li.classList.toggle("completed", !newCompleted);
    });
}

function handleDelete(li, id) {
  li.style.maxHeight = li.scrollHeight + "px";
  requestAnimationFrame(() => {
    li.classList.add("removing");
  });

  li.addEventListener(
    "transitionend",
    () => {
      deleteTodo(id)
        .then(() => {
          li.remove();
          if (getFilteredTodos().length === 0) emptyState.hidden = false;
        })
        .catch(() => {
          li.classList.remove("removing");
          li.style.maxHeight = "";
        });
    },
    { once: true }
  );
}

function startEditing(li, todo) {
  const body = li.querySelector(".todo-body");
  const titleSpan = li.querySelector(".todo-title");
  const originalTitle = todo.title;
  let saved = false;

  const input = document.createElement("input");
  input.className = "todo-edit-input";
  input.value = originalTitle;

  body.replaceChild(input, titleSpan);
  input.focus();
  input.select();

  async function save() {
    if (saved) return;
    saved = true;

    const newTitle = input.value.trim();
    if (!newTitle || newTitle === originalTitle) {
      body.replaceChild(titleSpan, input);
      return;
    }

    try {
      const updated = await updateTodoTitle(todo.id, newTitle);
      todo.title = updated.title;
      titleSpan.textContent = updated.title;
    } catch {
      titleSpan.textContent = originalTitle;
    }
    body.replaceChild(titleSpan, input);
  }

  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") save();
    if (e.key === "Escape") {
      saved = true;
      body.replaceChild(titleSpan, input);
    }
  });

  input.addEventListener("blur", save);
}

// ── 사이드바 카테고리 추가 폼 ────────────────────────────────

sidebarAddBtn.addEventListener("click", () => {
  const hidden = sidebarAddForm.hidden;
  sidebarAddForm.hidden = !hidden;
  if (!hidden) return;
  categoryInput.value = "";
  categoryInput.focus();
});

sidebarAddForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const name = categoryInput.value.trim();
  if (!name) return;
  try {
    await addCategory(name);
    categoryInput.value = "";
    sidebarAddForm.hidden = true;
  } catch {
    // silently ignore
  }
});

categoryInput.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    sidebarAddForm.hidden = true;
  }
});

// 모바일 드롭다운 변경 → 필터 적용
categoryMobSel.addEventListener("change", (e) => {
  const val = e.target.value;
  setActiveCategory(val === "all" ? "all" : Number(val));
});

// ── 할일 추가 폼 ─────────────────────────────────────────────

todoForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const title = todoInput.value.trim();

  if (!title) {
    todoInput.classList.remove("shake");
    void todoInput.offsetWidth;
    todoInput.classList.add("shake");
    todoInput.addEventListener(
      "animationend",
      () => todoInput.classList.remove("shake"),
      { once: true }
    );
    return;
  }

  const dueDate   = dueDateInput.value || null;
  const catIdRaw  = categoryFormSel.value;
  const categoryId = catIdRaw ? Number(catIdRaw) : null;

  try {
    await addTodo(title, dueDate, categoryId);
    todoInput.value    = "";
    dueDateInput.value = "";
    categoryFormSel.value = "";
    todoInput.focus();
  } catch {
    // silently ignore — server-side validation handles 422
  }
});

// ── Init ──────────────────────────────────────────────────────

initTheme();
fetchCategories().then(() => fetchTodos());
