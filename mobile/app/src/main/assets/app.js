/**
 * YONJIZ mobile — offline SPA.
 * Persistence goes through the native YonjizStore bridge (or localStorage when
 * previewing in a desktop browser). There is no fetch(), no server, no network.
 */
(function () {
    "use strict";

    const $ = (selector) => document.querySelector(selector);
    const $$ = (selector) => Array.from(document.querySelectorAll(selector));
    const STORAGE_KEY = "yonjiz-mobile-v1";
    const PRIORITIES = { 1: "VERY LOW", 2: "LOW", 3: "MEDIUM", 4: "HIGH", 5: "CRITICAL" };
    const nativeStore = window.YonjizStore || null;

    let state = { version: 1, tasks: [] };
    let currentView = "tasks";
    let activeFilter = "all";
    let selectedDateKey = null;
    let calendarCursor = new Date();
    let editingId = null;
    let toastTimer = null;

    const monthFmt = new Intl.DateTimeFormat(undefined, { month: "long", year: "numeric" });
    const weekdayFmt = new Intl.DateTimeFormat(undefined, { weekday: "long", month: "long", day: "numeric" });
    const shortFmt = new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" });

    function loadState() {
        let raw = "{}";
        try {
            raw = nativeStore ? nativeStore.load() : (localStorage.getItem(STORAGE_KEY) || "{}");
        } catch (err) {
            raw = "{}";
        }
        try {
            const parsed = JSON.parse(raw);
            if (parsed && Array.isArray(parsed.tasks)) {
                state.tasks = parsed.tasks.filter(isValidTask);
            }
        } catch (err) {
            state.tasks = [];
        }
    }

    function isValidTask(task) {
        return task && (typeof task.id === "number" || typeof task.id === "string") && typeof task.title === "string";
    }

    function saveState() {
        const raw = JSON.stringify(state);
        try {
            if (nativeStore) nativeStore.save(raw);
            else localStorage.setItem(STORAGE_KEY, raw);
        } catch (err) {
            toast("Could not save on this device.");
        }
    }

    function nextId() {
        return state.tasks.reduce((max, task) => Math.max(max, Number(task.id) || 0), 0) + 1;
    }

    function esc(value) {
        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    function localDateKey(date) {
        return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
    }

    function parseDeadline(raw) {
        if (!raw) return null;
        const date = new Date(raw);
        return Number.isNaN(date.getTime()) ? null : date;
    }

    function deadlineForTask(task) {
        return parseDeadline(task.deadline);
    }

    function sameDay(a, b) {
        return a && b && a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
    }

    function isOverdue(task) {
        const deadline = deadlineForTask(task);
        return Boolean(deadline) && !task.complete && deadline < new Date();
    }

    function timeText(date) {
        return date.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
    }

    function deadlineText(date) {
        const now = new Date();
        const tomorrow = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);
        if (sameDay(date, now)) return `Today, ${timeText(date)}`;
        if (sameDay(date, tomorrow)) return `Tomorrow, ${timeText(date)}`;
        return `${shortFmt.format(date)}, ${timeText(date)}`;
    }

    function deadlineState(task) {
        if (!task.deadline) return null;
        const date = deadlineForTask(task);
        if (!date) return null;
        if (task.complete) return "done";
        if (isOverdue(task)) return "overdue";
        if (sameDay(date, new Date())) return "today";
        if (date - new Date() <= 72 * 3600 * 1000) return "soon";
        return null;
    }

    function saveAndRender() {
        saveState();
        renderAll();
    }

    function renderAll() {
        renderStats();
        renderTasks();
        renderCalendar();
        renderDayTasks();
        $("#taskWipeCount").textContent = String(state.tasks.length);
    }

    function renderStats() {
        const now = new Date();
        const total = state.tasks.length;
        const complete = state.tasks.filter((task) => task.complete).length;
        const dueToday = state.tasks.filter((task) => !task.complete && deadlineForTask(task) && sameDay(deadlineForTask(task), now)).length;
        const overdue = state.tasks.filter(isOverdue).length;
        $("#statTotal").textContent = total;
        $("#statOpen").textContent = total - complete;
        $("#statToday").textContent = dueToday;
        $("#statOverdue").textContent = overdue;
        $("#taskCount").textContent = total;
    }

    function taskSearch(task) {
        return `${task.title} ${task.description || ""}`.toLowerCase();
    }

    function visibleTasks(list) {
        const query = $("#searchInput").value.trim().toLowerCase();
        const now = new Date();
        return (list || state.tasks)
            .filter((task) => {
                if (query && !taskSearch(task).includes(query)) return false;
                if (activeFilter === "open" && task.complete) return false;
                if (activeFilter === "complete" && !task.complete) return false;
                if (activeFilter === "overdue" && !isOverdue(task)) return false;
                if (selectedDateKey) {
                    const deadline = deadlineForTask(task);
                    if (!deadline || localDateKey(deadline) !== selectedDateKey) return false;
                }
                return true;
            })
            .sort((a, b) => {
                if (a.complete !== b.complete) return a.complete ? 1 : -1;
                const ad = deadlineForTask(a);
                const bd = deadlineForTask(b);
                if (ad && bd && ad - bd !== 0) return ad - bd;
                if (ad && !bd) return -1;
                if (!ad && bd) return 1;
                if (a.priority !== b.priority) return b.priority - a.priority;
                return String(b.createdAt).localeCompare(String(a.createdAt));
            });
    }

    function taskCard(task) {
        const stateName = deadlineState(task);
        const deadline = deadlineForTask(task);
        const meta = deadline
            ? `<span>◷ ${esc(deadlineText(deadline))}</span>${stateName ? `<span class="due-badge ${stateName}">${stateName.toUpperCase()}</span>` : ""}`
            : `<span>No deadline</span>`;
        return `
        <article class="task-card ${task.complete ? "is-complete" : ""}" data-id="${esc(task.id)}">
            <button class="task-check ${task.complete ? "is-checked" : ""}" data-action="toggle" type="button"
                aria-label="${task.complete ? "Mark not done" : "Mark done"}" aria-pressed="${task.complete}">✓</button>
            <div class="task-body">
                <div class="task-top">
                    <span class="task-title">${esc(task.title)}</span>
                    <span class="priority" data-p="${Number(task.priority) || 3}">${PRIORITIES[task.priority] || "MEDIUM"}</span>
                </div>
                ${task.description ? `<p class="task-desc">${esc(task.description)}</p>` : ""}
                <div class="task-meta">${meta}</div>
            </div>
            <div class="task-actions">
                <button class="mini-btn" data-action="edit" type="button" aria-label="Edit task">✎</button>
                <button class="mini-btn" data-action="delete" type="button" aria-label="Delete task">×</button>
            </div>
        </article>`;
    }

    function renderTasks() {
        const list = visibleTasks();
        const empty = $("#emptyState");
        const listElement = $("#taskList");
        if (!list.length) {
            listElement.innerHTML = "";
            empty.hidden = false;
            if (!state.tasks.length) {
                $("#emptyTitle").textContent = "A clear page.";
                $("#emptyCopy").textContent = "Add the first thing you want to make room for. A deadline is optional.";
                $("#emptyAdd").hidden = false;
            } else {
                $("#emptyTitle").textContent = "Nothing matches that view.";
                $("#emptyCopy").textContent = "Try another filter or clear the selected date.";
                $("#emptyAdd").hidden = true;
            }
        } else {
            empty.hidden = true;
            listElement.innerHTML = list.map(taskCard).join("");
        }
        const dateChip = $("#dateChip");
        if (selectedDateKey) {
            const date = new Date(`${selectedDateKey}T12:00:00`);
            $("#dateChipText").textContent = `Showing ${weekdayFmt.format(date)}`;
            dateChip.hidden = false;
        } else {
            dateChip.hidden = true;
        }
    }

    function renderCalendar() {
        const year = calendarCursor.getFullYear();
        const month = calendarCursor.getMonth();
        const first = new Date(year, month, 1);
        const start = new Date(year, month, 1 - first.getDay());
        const todayKey = localDateKey(new Date());
        $("#monthLabel").textContent = monthFmt.format(calendarCursor);
        const deadlineDays = new Map();
        state.tasks.forEach((task) => {
            const date = deadlineForTask(task);
            if (!date) return;
            const key = localDateKey(date);
            const previous = deadlineDays.get(key) || { count: 0, overdue: false, complete: true };
            previous.count += 1;
            previous.overdue = previous.overdue || isOverdue(task);
            previous.complete = previous.complete && task.complete;
            deadlineDays.set(key, previous);
        });
        let html = "";
        for (let i = 0; i < 42; i += 1) {
            const date = new Date(start.getFullYear(), start.getMonth(), start.getDate() + i);
            const key = localDateKey(date);
            const info = deadlineDays.get(key);
            const classes = ["day"];
            if (date.getMonth() !== month) classes.push("outside");
            if (date.getDay() === 0 || date.getDay() === 6) classes.push("weekend");
            if (key === todayKey) classes.push("today");
            if (key === selectedDateKey) classes.push("selected");
            if (info) {
                classes.push("has-deadline");
                if (info.overdue) classes.push("has-overdue");
                else if (info.complete) classes.push("has-complete");
            }
            const aria = info ? `${weekdayFmt.format(date)}, ${info.count} deadline${info.count === 1 ? "" : "s"}` : weekdayFmt.format(date);
            html += `<button class="${classes.join(" ")}" data-date="${key}" type="button" aria-label="${esc(aria)}">${date.getDate()}</button>`;
        }
        $("#calendarGrid").innerHTML = html;
    }

    function tasksForDay(key) {
        return state.tasks
            .filter((task) => {
                const date = deadlineForTask(task);
                return date && localDateKey(date) === key;
            })
            .sort((a, b) => (deadlineForTask(a) - deadlineForTask(b)) || (a.complete ? 1 : -1));
    }

    function renderDayTasks() {
        const key = selectedDateKey || localDateKey(new Date());
        const date = new Date(`${key}T12:00:00`);
        const tasks = tasksForDay(key);
        $("#dayTitle").textContent = selectedDateKey ? weekdayFmt.format(date) : "Today";
        $("#dayCount").textContent = String(tasks.length);
        $("#dayTaskList").innerHTML = tasks.length
            ? tasks.map(taskCard).join("")
            : `<p class="footnote" style="text-align:left;margin:8px 2px;">No tasks with a deadline on this day.</p>`;
        $("#clearDay").textContent = selectedDateKey ? "All tasks" : "";
        $("#clearDay").style.visibility = selectedDateKey ? "visible" : "hidden";
    }

    function selectDate(key) {
        selectedDateKey = key;
        const parts = key.split("-").map(Number);
        calendarCursor = new Date(parts[0], parts[1] - 1, 1);
        renderTasks();
        renderCalendar();
        renderDayTasks();
    }

    function clearDate() {
        selectedDateKey = null;
        renderTasks();
        renderCalendar();
        renderDayTasks();
    }

    function switchView(view) {
        currentView = view;
        $$(".view").forEach((element) => element.classList.toggle("is-active", element.id === `${view}View`));
        $$(".tab[data-view]").forEach((tab) => tab.classList.toggle("is-active", tab.dataset.view === view));
        if (view === "tasks") renderStats();
        if (view === "calendar") {
            renderCalendar();
            renderDayTasks();
        }
        window.scrollTo({ top: 0, behavior: "smooth" });
    }

    function toast(message) {
        const element = $("#toast");
        element.textContent = message;
        element.classList.add("show");
        clearTimeout(toastTimer);
        toastTimer = setTimeout(() => element.classList.remove("show"), 2400);
        if (navigator.vibrate) navigator.vibrate(8);
    }

    function toggleTask(id) {
        const task = state.tasks.find((item) => String(item.id) === String(id));
        if (!task) return;
        task.complete = !task.complete;
        task.completedAt = task.complete ? new Date().toISOString() : null;
        saveAndRender();
        toast(task.complete ? "Task completed." : "Task moved back to open.");
    }

    function deleteTask(id) {
        const task = state.tasks.find((item) => String(item.id) === String(id));
        if (!task) return;
        if (!confirm(`Delete “${task.title}”?`)) return;
        state.tasks = state.tasks.filter((item) => String(item.id) !== String(id));
        saveAndRender();
        toast("Task deleted.");
    }

    function formatInputValue(date) {
        return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}T${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
    }

    function syncDeadlineInput() {
        const enabled = $("#hasDeadline").checked;
        $("#taskDeadline").disabled = !enabled;
        $("#deadlineField").classList.toggle("is-disabled", !enabled);
        if (!enabled) {
            $("#taskDeadline").value = "";
        } else if (!$("#taskDeadline").value) {
            const tomorrow = new Date();
            tomorrow.setDate(tomorrow.getDate() + 1);
            tomorrow.setHours(17, 0, 0, 0);
            $("#taskDeadline").value = formatInputValue(tomorrow);
        }
    }

    function openDialog(task) {
        editingId = task ? task.id : null;
        $("#taskForm").reset();
        $("#formError").hidden = true;
        $("#dialogEyebrow").textContent = task ? "A GENTLE EDIT" : "A NEW INTENTION";
        $("#dialogTitle").textContent = task ? "Edit task" : "Add a task";
        $("#saveTask").textContent = task ? "Save changes" : "Add task";
        $("#taskTitle").value = task ? task.title : "";
        $("#taskDescription").value = task ? task.description : "";
        const priority = task ? Number(task.priority) || 3 : 3;
        const radio = $(`input[name="priority"][value="${priority}"]`);
        if (radio) radio.checked = true;
        const deadline = task ? deadlineForTask(task) : null;
        $("#hasDeadline").checked = Boolean(deadline);
        $("#taskDeadline").value = deadline ? formatInputValue(deadline) : "";
        syncDeadlineInput();
        $("#taskDialog").showModal();
        setTimeout(() => $("#taskTitle").focus(), 40);
    }

    function closeDialog() {
        if ($("#taskDialog").open) $("#taskDialog").close();
    }

    function showFormError(message) {
        $("#formError").textContent = message;
        $("#formError").hidden = false;
    }

    function submitTask(event) {
        event.preventDefault();
        const title = $("#taskTitle").value.trim();
        if (!title) {
            showFormError("Give this task a title.");
            return;
        }
        const hasDeadline = $("#hasDeadline").checked;
        if (hasDeadline && !$("#taskDeadline").value) {
            showFormError("Choose a deadline, or turn the deadline off.");
            return;
        }
        const payload = {
            title,
            description: $("#taskDescription").value.trim(),
            priority: Number(document.querySelector('input[name="priority"]:checked').value),
            deadline: hasDeadline ? new Date($("#taskDeadline").value).toISOString() : null,
        };
        if (editingId !== null) {
            const task = state.tasks.find((item) => String(item.id) === String(editingId));
            if (task) Object.assign(task, payload);
            toast("Task updated.");
        } else {
            state.tasks.push({
                id: nextId(),
                ...payload,
                complete: false,
                createdAt: new Date().toISOString(),
                completedAt: null,
            });
            toast("Task added.");
        }
        saveState();
        closeDialog();
        renderAll();
    }

    function renderClock() {
        const now = new Date();
        const hour = now.getHours();
        let displayHour = hour % 12 || 12;
        $("#clockTime").textContent = `${displayHour}:${String(now.getMinutes()).padStart(2, "0")}`;
        $("#clockSeconds").textContent = String(now.getSeconds()).padStart(2, "0");
        $("#clockPeriod").textContent = hour >= 12 ? "PM" : "AM";
        $("#clockDate").textContent = weekdayFmt.format(now);
        $("#hourHand").setAttribute("transform", `rotate(${(hour % 12 + now.getMinutes() / 60) * 30} 50 50)`);
        $("#minuteHand").setAttribute("transform", `rotate(${(now.getMinutes() + now.getSeconds() / 60) * 6} 50 50)`);
        $("#secondHand").setAttribute("transform", `rotate(${now.getSeconds() * 6} 50 50)`);
        const greeting = hour < 12 ? "Good morning." : hour < 18 ? "Good afternoon." : "Good evening.";
        $("#greeting").textContent = greeting;
        $("#todayLabel").textContent = weekdayFmt.format(now).toUpperCase();
    }

    function buildClockTicks() {
        const group = $("#clockTicks");
        const ns = "http://www.w3.org/2000/svg";
        for (let i = 0; i < 12; i += 1) {
            const line = document.createElementNS(ns, "line");
            const angle = (i * 30 * Math.PI) / 180;
            const outer = 44;
            const inner = i % 3 === 0 ? 37 : 40;
            line.setAttribute("x1", String(50 + Math.sin(angle) * inner));
            line.setAttribute("y1", String(50 - Math.cos(angle) * inner));
            line.setAttribute("x2", String(50 + Math.sin(angle) * outer));
            line.setAttribute("y2", String(50 - Math.cos(angle) * outer));
            group.appendChild(line);
        }
    }

    function bindEvents() {
        $$(".tab[data-view]").forEach((tab) => tab.addEventListener("click", () => switchView(tab.dataset.view)));
        $(".tab-add").addEventListener("click", () => openDialog(null));
        $("#openAdd").addEventListener("click", () => openDialog(null));
        $("#emptyAdd").addEventListener("click", () => openDialog(null));

        $("#searchInput").addEventListener("input", renderTasks);
        $$(".filter").forEach((button) => {
            button.addEventListener("click", () => {
                activeFilter = button.dataset.filter;
                $$(".filter").forEach((item) => item.classList.toggle("is-active", item === button));
                renderTasks();
            });
        });

        document.addEventListener("click", (event) => {
            const action = event.target.closest("[data-action]");
            if (action && action.dataset.action === "add") {
                openDialog(null);
                return;
            }
            const control = event.target.closest("[data-action]");
            if (!control) return;
            const card = control.closest(".task-card");
            if (!card) return;
            const id = card.dataset.id;
            if (control.dataset.action === "toggle") toggleTask(id);
            if (control.dataset.action === "edit") {
                const task = state.tasks.find((item) => String(item.id) === String(id));
                if (task) openDialog(task);
            }
            if (control.dataset.action === "delete") deleteTask(id);
        });

        $("#clearDate").addEventListener("click", clearDate);
        $("#clearDay").addEventListener("click", clearDate);
        $("#todayButton").addEventListener("click", () => {
            const today = new Date();
            calendarCursor = new Date(today.getFullYear(), today.getMonth(), 1);
            selectDate(localDateKey(today));
        });
        $("#prevMonth").addEventListener("click", () => {
            calendarCursor = new Date(calendarCursor.getFullYear(), calendarCursor.getMonth() - 1, 1);
            renderCalendar();
        });
        $("#nextMonth").addEventListener("click", () => {
            calendarCursor = new Date(calendarCursor.getFullYear(), calendarCursor.getMonth() + 1, 1);
            renderCalendar();
        });
        $("#calendarGrid").addEventListener("click", (event) => {
            const day = event.target.closest(".day");
            if (day) selectDate(day.dataset.date);
        });

        $("#closeDialog").addEventListener("click", closeDialog);
        $("#cancelDialog").addEventListener("click", closeDialog);
        $("#taskDialog").addEventListener("click", (event) => {
            if (event.target === $("#taskDialog")) closeDialog();
        });
        $("#hasDeadline").addEventListener("change", syncDeadlineInput);
        $("#taskForm").addEventListener("submit", submitTask);

        $("#clearCompleted").addEventListener("click", () => {
            const completed = state.tasks.filter((task) => task.complete);
            if (!completed.length) {
                toast("No completed tasks.");
                return;
            }
            if (!confirm(`Clear ${completed.length} completed task${completed.length === 1 ? "" : "s"}?`)) return;
            state.tasks = state.tasks.filter((task) => !task.complete);
            saveAndRender();
            toast("Completed tasks cleared.");
        });
        $("#wipeData").addEventListener("click", () => {
            if (!state.tasks.length) {
                toast("There is nothing to delete.");
                return;
            }
            if (!confirm("Delete every task on this phone? This cannot be undone.")) return;
            state.tasks = [];
            saveAndRender();
            selectedDateKey = null;
            toast("All local data deleted.");
        });
    }

    window.mobileBack = function () {
        if ($("#taskDialog").open) {
            closeDialog();
            return true;
        }
        if (currentView !== "tasks") {
            switchView("tasks");
            return true;
        }
        return false;
    };

    buildClockTicks();
    loadState();
    bindEvents();
    renderClock();
    setInterval(renderClock, 1000);
    renderAll();
    document.addEventListener("visibilitychange", () => {
        if (!document.hidden) renderClock();
    });
})();
