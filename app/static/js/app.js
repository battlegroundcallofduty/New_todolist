// Todo App - Frontend Logic

const API_URL = "/api/todos";

const todoForm = document.getElementById("todo-form");
const todoInput = document.getElementById("todo-input");
const todoList = document.getElementById("todo-list");
const emptyState = document.getElementById("empty-state");
const errorState = document.getElementById("error-state");
const listContainer = document.getElementById("todo-list-container");

let todos = [];

// ─── API helpers ──────────────────────────────────────────────

async function fetchTodos() {
  listContainer.classList.add("loading");
  errorState.hidden = true;
  try {
    const res = await fetch(API_URL + "/");
    if (!res.ok) throw new Error("서버 오류");
    todos = await res.json();
    renderTodos();
  } catch {
    errorState.hidden = false;
    emptyState.hidden = true;
  } finally {
    listContainer.classList.remove("loading");
  }
}

async function addTodo(title) {
  const res = await fetch(API_URL + "/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error("추가 실패");
  const todo = await res.json();
  todos.push(todo);
  renderTodos();
}

async function toggleTodo(id, completed) {
  const res = await fetch(`${API_URL}/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ completed }),
  });
  if (!res.ok) throw new Error("토글 실패");
  const updated = await res.json();
  todos = todos.map((t) => (t.id === id ? updated : t));
}

async function deleteTodo(id) {
  const res = await fetch(`${API_URL}/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("삭제 실패");
  todos = todos.filter((t) => t.id !== id);
}

async function updateTodoTitle(id, title) {
  const res = await fetch(`${API_URL}/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error("수정 실패");
  const updated = await res.json();
  todos = todos.map((t) => (t.id === id ? updated : t));
  return updated;
}

// ─── Rendering ────────────────────────────────────────────────

function renderTodos() {
  todoList.innerHTML = "";
  if (todos.length === 0) {
    emptyState.hidden = false;
  } else {
    emptyState.hidden = true;
    todos.forEach((todo) => {
      todoList.appendChild(createTodoElement(todo));
    });
  }
}

function createTodoElement(todo) {
  const li = document.createElement("li");
  li.className = "todo-item" + (todo.completed ? " completed" : "");
  li.dataset.id = todo.id;

  // Checkbox
  const checkbox = document.createElement("div");
  checkbox.className = "todo-checkbox";

  const mark = document.createElement("span");
  mark.className = "todo-checkbox-mark";
  mark.innerHTML = "&#10003;";
  checkbox.appendChild(mark);

  checkbox.addEventListener("click", () => handleToggle(li, todo));

  // Title
  const titleSpan = document.createElement("span");
  titleSpan.className = "todo-title";
  titleSpan.textContent = todo.title;

  if (!todo.completed) {
    titleSpan.addEventListener("dblclick", () => startEditing(li, todo));
  }

  // Delete button
  const deleteBtn = document.createElement("button");
  deleteBtn.className = "todo-delete";
  deleteBtn.setAttribute("aria-label", "삭제");
  deleteBtn.textContent = "×";
  deleteBtn.addEventListener("click", () => handleDelete(li, todo.id));

  li.appendChild(checkbox);
  li.appendChild(titleSpan);
  li.appendChild(deleteBtn);

  return li;
}

// ─── Interactions ─────────────────────────────────────────────

function handleToggle(li, todo) {
  const newCompleted = !todo.completed;
  // Optimistic update
  todo.completed = newCompleted;
  li.classList.toggle("completed", newCompleted);

  toggleTodo(todo.id, newCompleted).catch(() => {
    // Rollback
    todo.completed = !newCompleted;
    li.classList.toggle("completed", !newCompleted);
  });
}

function handleDelete(li, id) {
  // Set explicit max-height before animating
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
          if (todos.length === 0) emptyState.hidden = false;
        })
        .catch(() => {
          // Rollback: restore item
          li.classList.remove("removing");
          li.style.maxHeight = "";
          todos.push({ id });
        });
    },
    { once: true }
  );
}

function startEditing(li, todo) {
  const titleSpan = li.querySelector(".todo-title");
  const originalTitle = todo.title;
  let saved = false;

  const input = document.createElement("input");
  input.className = "todo-edit-input";
  input.value = originalTitle;

  li.replaceChild(input, titleSpan);
  input.focus();
  input.select();

  async function save() {
    if (saved) return;
    saved = true;

    const newTitle = input.value.trim();
    if (!newTitle || newTitle === originalTitle) {
      // Restore original title without server call
      li.replaceChild(titleSpan, input);
      return;
    }

    try {
      const updated = await updateTodoTitle(todo.id, newTitle);
      todo.title = updated.title;
      titleSpan.textContent = updated.title;
    } catch {
      // Rollback
      titleSpan.textContent = originalTitle;
    }
    li.replaceChild(titleSpan, input);
  }

  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") save();
    if (e.key === "Escape") {
      saved = true;
      li.replaceChild(titleSpan, input);
    }
  });

  input.addEventListener("blur", save);
}

// ─── Form submit ──────────────────────────────────────────────

todoForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const title = todoInput.value.trim();

  if (!title) {
    todoInput.classList.remove("shake");
    // Force reflow to restart animation
    void todoInput.offsetWidth;
    todoInput.classList.add("shake");
    todoInput.addEventListener(
      "animationend",
      () => todoInput.classList.remove("shake"),
      { once: true }
    );
    return;
  }

  try {
    await addTodo(title);
    todoInput.value = "";
    todoInput.focus();
  } catch {
    // silently ignore — server-side validation handles 422
  }
});

// ─── Init ─────────────────────────────────────────────────────

fetchTodos();
