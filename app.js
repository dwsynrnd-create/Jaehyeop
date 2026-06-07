// 할 일 관리 - 의존성 없는 순수 JavaScript
// 데이터는 브라우저 localStorage에 저장되어 새로고침해도 유지됩니다.

(function () {
  "use strict";

  const STORAGE_KEY = "jaehyeop.todos";

  /** @type {{ id: string, text: string, done: boolean }[]} */
  let todos = load();
  let filter = "all"; // all | active | done

  // DOM 참조
  const form = document.getElementById("todo-form");
  const input = document.getElementById("todo-input");
  const list = document.getElementById("todo-list");
  const emptyState = document.getElementById("empty-state");
  const counter = document.getElementById("counter");
  const clearDoneBtn = document.getElementById("clear-done");
  const filterButtons = document.querySelectorAll(".filters__btn");

  // ---- 저장/불러오기 ----
  function load() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch (e) {
      return [];
    }
  }

  function save() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(todos));
  }

  // ---- 동작 ----
  function addTodo(text) {
    const trimmed = text.trim();
    if (!trimmed) return;
    todos.unshift({
      id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
      text: trimmed,
      done: false,
    });
    save();
    render();
  }

  function toggleTodo(id) {
    const todo = todos.find((t) => t.id === id);
    if (todo) {
      todo.done = !todo.done;
      save();
      render();
    }
  }

  function deleteTodo(id) {
    todos = todos.filter((t) => t.id !== id);
    save();
    render();
  }

  function clearDone() {
    todos = todos.filter((t) => !t.done);
    save();
    render();
  }

  function getVisibleTodos() {
    if (filter === "active") return todos.filter((t) => !t.done);
    if (filter === "done") return todos.filter((t) => t.done);
    return todos;
  }

  // ---- 렌더링 ----
  function render() {
    const visible = getVisibleTodos();
    list.innerHTML = "";

    visible.forEach((todo) => {
      const li = document.createElement("li");
      li.className = "todo-item" + (todo.done ? " is-done" : "");

      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.className = "todo-item__checkbox";
      checkbox.checked = todo.done;
      checkbox.addEventListener("change", () => toggleTodo(todo.id));

      const span = document.createElement("span");
      span.className = "todo-item__text";
      span.textContent = todo.text;

      const delBtn = document.createElement("button");
      delBtn.className = "todo-item__delete";
      delBtn.type = "button";
      delBtn.setAttribute("aria-label", "삭제");
      delBtn.textContent = "×";
      delBtn.addEventListener("click", () => deleteTodo(todo.id));

      li.append(checkbox, span, delBtn);
      list.appendChild(li);
    });

    // 빈 상태 표시
    emptyState.hidden = visible.length > 0;

    // 카운터 갱신
    const remaining = todos.filter((t) => !t.done).length;
    counter.textContent = remaining + "개 진행 중";
  }

  // ---- 이벤트 바인딩 ----
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    addTodo(input.value);
    input.value = "";
    input.focus();
  });

  clearDoneBtn.addEventListener("click", clearDone);

  filterButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      filter = btn.dataset.filter;
      filterButtons.forEach((b) => b.classList.toggle("is-active", b === btn));
      render();
    });
  });

  // 첫 렌더링
  render();
})();
