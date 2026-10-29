document.addEventListener("DOMContentLoaded", () => {
    const todoForm = document.getElementById("add-todo-form");
    const todoList = document.getElementById("todo-list");
    const emptyState = document.getElementById("empty-state");

    // --- 1. LIVE CLOCK (12h Format) ---
    function updateClock() {
        const now = new Date();
        const timeEl = document.getElementById("clock-time");
        const dateEl = document.getElementById("clock-date");
        
        if (timeEl && dateEl) {
            timeEl.textContent = now.toLocaleTimeString('en-US', { hour12: true });
            dateEl.textContent = now.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });
        }
    }
    setInterval(updateClock, 1000);
    updateClock(); // Run immediately

    // Format ISO string to 12h Time
    function formatTime(isoString) {
        if (!isoString) return "";
        const date = new Date(isoString);
        return date.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit', hour12: true });
    }

    // --- 2. ADD TODO ---
    todoForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const titleInput = document.getElementById("todo-title");
        const descInput = document.getElementById("todo-desc");
        const prioritySelect = document.getElementById("todo-priority");
        const deadlineInput = document.getElementById("todo-deadline");
        
        const newTodo = {
            title: titleInput.value,
            description: descInput.value,
            priority: parseInt(prioritySelect.value),
            complete: false,
            deadline: deadlineInput.value ? new Date(deadlineInput.value).toISOString() : null
        };

        try {
            const response = await fetch("/todos/todo", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(newTodo),
                credentials: "include"
            });

            if (response.ok) {
                const savedTodo = await response.json();
                addTodoToDOM(savedTodo);
                todoForm.reset();
                emptyState.classList.add("hidden");
            } else {
                const errorData = await response.json();
                showToast("Error: " + errorData.detail[0].msg);
            }
        } catch (error) {
            console.error("Error adding todo:", error);
        }
    });

    // --- 3. TOGGLE COMPLETE & CALCULATE DURATION ---
    todoList.addEventListener("change", async (e) => {
        if (e.target.classList.contains("toggle-todo")) {
            const checkbox = e.target;
            const li = checkbox.closest(".todo-item");
            const todoId = li.dataset.id;
            const isComplete = checkbox.checked;

            const title = li.dataset.title;
            const description = li.dataset.description;
            const priority = parseInt(li.dataset.priority);
            const created = li.dataset.created;
            const deadline = li.dataset.deadline ? li.dataset.deadline : null;

            li.classList.toggle("completed", isComplete);

            // Calculate Duration if completed
            const durationEl = li.querySelector(".duration-time");
            if (isComplete && created) {
                const createdDate = new Date(created);
                const now = new Date();
                const diffMs = now - createdDate;
                const diffMins = Math.floor(diffMs / 60000);
                const diffHours = Math.floor(diffMins / 60);
                const diffDays = Math.floor(diffHours / 24);

                let durationText = "Finished in: ";
                if (diffDays > 0) durationText += `${diffDays}d `;
                if (diffHours % 24 > 0) durationText += `${diffHours % 24}h `;
                durationText += `${diffMins % 60}m`;
                
                durationEl.textContent = durationText;
                durationEl.style.display = "inline";
                durationEl.style.color = "#10b981"; // Green for success
                durationEl.style.fontWeight = "bold";
            } else {
                durationEl.style.display = "none";
            }

            try {
                await fetch(`/todos/todo/${todoId}`, {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ 
                        title: title, 
                        description: description, 
                        priority: priority, 
                        complete: isComplete,
                        deadline: deadline
                    }),
                    credentials: "include"
                });
            } catch (error) {
                console.error("Error updating todo:", error);
                checkbox.checked = !isComplete; 
                li.classList.toggle("completed", !isComplete);
            }
        }
    });

    // --- 4. DELETE TODO ---
    todoList.addEventListener("click", async (e) => {
        if (e.target.classList.contains("delete-btn")) {
            const li = e.target.closest(".todo-item");
            const todoId = li.dataset.id;

            li.classList.add("deleting");

            try {
                await fetch(`/todos/todo/${todoId}`, { 
                    method: "DELETE",
                    credentials: "include"
                });
                
                setTimeout(() => {
                    li.remove();
                    if (todoList.children.length === 0) {
                        emptyState.classList.remove("hidden");
                    }
                }, 300);
            } catch (error) {
                console.error("Error deleting todo:", error);
                li.classList.remove("deleting"); 
            }
        }
    });

    // --- 5. HELPER TO ADD DOM ---
    function addTodoToDOM(todo) {
        const li = document.createElement("li");
        li.className = "todo-item";
        li.dataset.id = todo.id;
        li.dataset.title = todo.title;
        li.dataset.description = todo.description;
        li.dataset.priority = todo.priority;
        li.dataset.complete = todo.complete;
        li.dataset.created = todo.created_at;
        li.dataset.deadline = todo.deadline || '';
        
        let priorityText = todo.priority;
        if(todo.priority === 1) priorityText = "Very Low";
        if(todo.priority === 2) priorityText = "Low";
        if(todo.priority === 3) priorityText = "Medium";
        if(todo.priority === 4) priorityText = "High";
        if(todo.priority === 5) priorityText = "Critical";

        const createdStr = formatTime(todo.created_at);
        const deadlineStr = todo.deadline ? formatTime(todo.deadline) : '';

        li.innerHTML = `
            <label class="checkbox-container">
                <input type="checkbox" class="toggle-todo">
                <span class="checkmark"></span>
            </label>
            <div class="todo-content">
                <div class="todo-main">
                    <span class="todo-title">${todo.title}</span>
                    <span class="priority-tag priority-${todo.priority}">${priorityText}</span>
                </div>
                <div class="todo-meta">
                    <span class="created-time">Created: ${createdStr}</span>
                    ${deadlineStr ? `<span class="deadline-time">Deadline: ${deadlineStr}</span>` : ''}
                    <span class="duration-time" style="display: none;"></span>
                </div>
            </div>
            <button class="delete-btn" title="Delete task">&times;</button>
        `;
        
        todoList.prepend(li);
    }
});

// Custom Toast
function showToast(message) {
    const toast = document.createElement("div");
    toast.className = "toast";
    toast.innerText = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.classList.add("show"), 100);
    setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => toast.remove(), 400);
    }, 3000);
}