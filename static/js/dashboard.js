/* Workspace behaviour: filtering, sorting, the task dialog and JSON CRUD. */
(function () {
    "use strict";

    var list = document.getElementById("task-list");
    var workspace = document.querySelector(".workspace");
    if (!list || !workspace) return;

    var dialog = document.getElementById("task-dialog");
    var form = document.getElementById("task-form");
    var taskIdInput = document.getElementById("task-id");
    var titleInput = document.getElementById("task-title");
    var descriptionInput = document.getElementById("task-description");
    var submitButton = document.getElementById("task-submit");
    var dialogKicker = document.getElementById("task-dialog-kicker");
    var dialogTitle = document.getElementById("task-dialog-title");
    var formError = document.getElementById("task-form-error");
    var deadlineToggle = document.getElementById("has-deadline");
    var deadlineInput = document.getElementById("task-deadline");
    var deadlineWrap = document.getElementById("deadline-input-wrap");
    var template = document.getElementById("task-card-template");

    var searchInput = document.getElementById("task-search");
    var sortSelect = document.getElementById("task-sort");
    var filterTabs = Array.prototype.slice.call(document.querySelectorAll(".filter-tab"));
    var statTotal = document.getElementById("stat-total");
    var statOpen = document.getElementById("stat-open");
    var statToday = document.getElementById("stat-today");
    var statOverdue = document.getElementById("stat-overdue");
    var taskCount = document.getElementById("task-count");
    var filterSummary = document.getElementById("filter-summary");
    var emptyState = document.getElementById("empty-state");
    var noResults = document.getElementById("no-results");
    var dateFilterBar = document.getElementById("date-filter-bar");
    var dateFilterLabel = document.getElementById("date-filter-label");
    var progressRing = document.getElementById("progress-ring");
    var progressValue = document.getElementById("progress-value");
    var progressTitle = document.getElementById("progress-title");
    var progressDetail = document.getElementById("progress-detail");

    var statusFilter = "all";
    var selectedDateKey = null;
    var editingCard = null;

    var priorityNames = { 1: "Very low", 2: "Low", 3: "Medium", 4: "High", 5: "Critical" };
    var priorityKeys = { 1: "very-low", 2: "low", 3: "medium", 4: "high", 5: "critical" };

    var fullDateFormatter = new Intl.DateTimeFormat(undefined, {
        weekday: "long",
        month: "long",
        day: "numeric",
        year: "numeric"
    });
    var weekdayTimeFormatter = new Intl.DateTimeFormat(undefined, {
        weekday: "short",
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit"
    });
    var monthDayFormatter = new Intl.DateTimeFormat(undefined, {
        month: "short",
        day: "numeric"
    });
    var monthDayYearFormatter = new Intl.DateTimeFormat(undefined, {
        month: "short",
        day: "numeric",
        year: "numeric"
    });

    function cards() {
        return Array.prototype.slice.call(list.querySelectorAll(".task-card"));
    }

    function dateKey(date) {
        return date.getFullYear() + "-" +
            String(date.getMonth() + 1).padStart(2, "0") + "-" +
            String(date.getDate()).padStart(2, "0");
    }

    function sameLocalDay(a, b) {
        return a.getFullYear() === b.getFullYear() &&
            a.getMonth() === b.getMonth() &&
            a.getDate() === b.getDate();
    }

    function parseDate(value) {
        if (!value) return null;
        var parsed = new Date(value);
        return Number.isNaN(parsed.getTime()) ? null : parsed;
    }

    function cardDeadline(card) {
        return parseDate(card.getAttribute("data-deadline"));
    }

    function cardCreated(card) {
        return parseDate(card.getAttribute("data-created-at")) || new Date(0);
    }

    function isComplete(card) {
        return card.getAttribute("data-complete") === "true";
    }

    function isOverdue(card) {
        var deadline = cardDeadline(card);
        return Boolean(deadline) && !isComplete(card) && deadline < new Date();
    }

    function formatDeadline(deadline) {
        if (!deadline) return "No deadline";

        var now = new Date();
        var tomorrow = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);
        var time = deadline.toLocaleTimeString(undefined, {
            hour: "numeric",
            minute: "2-digit"
        });

        if (sameLocalDay(deadline, now)) return "Today, " + time;
        if (sameLocalDay(deadline, tomorrow)) return "Tomorrow, " + time;

        var day = deadline.getFullYear() === now.getFullYear()
            ? monthDayFormatter.format(deadline)
            : monthDayYearFormatter.format(deadline);
        return day + ", " + time;
    }

    function deadlineState(deadline, complete) {
        if (!deadline) return null;
        if (complete) return { text: "Done", className: "is-done" };

        var now = new Date();
        if (deadline < now) return { text: "Overdue", className: "is-overdue" };
        if (sameLocalDay(deadline, now)) return { text: "Due today", className: "is-today" };

        var hours = (deadline - now) / 3600000;
        if (hours <= 72) return { text: "Due soon", className: "is-soon" };
        return null;
    }

    function updateCardMeta(card) {
        var deadline = cardDeadline(card);
        var complete = isComplete(card);
        var label = card.querySelector(".js-deadline-label");
        var stateElement = card.querySelector("[data-deadline-state]");
        var toggle = card.querySelector('[data-action="toggle"]');
        var createdLabel = card.querySelector(".js-created-label");
        var created = parseDate(card.getAttribute("data-created-at"));
        var title = card.getAttribute("data-title") || "task";

        card.classList.toggle("is-complete", complete);

        if (label) {
            label.textContent = formatDeadline(deadline);
            label.classList.toggle("meta-muted", !deadline);
            label.title = deadline ? fullDateFormatter.format(deadline) : "This task has no deadline";
        }

        if (stateElement) {
            var state = deadlineState(deadline, complete);
            stateElement.className = "deadline-state";
            if (state) {
                stateElement.textContent = state.text;
                stateElement.classList.add("is-visible", state.className);
            } else {
                stateElement.textContent = "";
            }
        }

        if (toggle) {
            toggle.setAttribute("aria-pressed", complete ? "true" : "false");
            toggle.setAttribute(
                "aria-label",
                (complete ? "Mark as not done: " : "Mark as done: ") + title
            );
        }

        if (createdLabel && created) {
            var today = new Date();
            if (sameLocalDay(created, today)) {
                createdLabel.textContent = "Added today";
            } else if (created.getFullYear() === today.getFullYear()) {
                createdLabel.textContent = "Added " + monthDayFormatter.format(created);
            } else {
                createdLabel.textContent = "Added " + monthDayYearFormatter.format(created);
            }
            createdLabel.title = fullDateFormatter.format(created);
        }
    }

    function updateStats() {
        var all = cards();
        var complete = all.filter(isComplete).length;
        var open = all.length - complete;
        var now = new Date();
        var dueToday = all.filter(function (card) {
            var deadline = cardDeadline(card);
            return deadline && !isComplete(card) && sameLocalDay(deadline, now);
        }).length;
        var overdue = all.filter(isOverdue).length;
        var percentage = all.length ? Math.round((complete / all.length) * 100) : 0;

        statTotal.textContent = String(all.length);
        statOpen.textContent = String(open);
        statToday.textContent = String(dueToday);
        statOverdue.textContent = String(overdue);

        progressValue.textContent = percentage + "%";
        if (progressRing) {
            progressRing.style.setProperty("--progress", String(percentage));
            progressRing.setAttribute(
                "aria-label",
                percentage + "% of tasks completed"
            );
        }

        if (!all.length) {
            progressTitle.textContent = "A fresh start";
            progressDetail.textContent = "Add a task to begin.";
        } else if (percentage === 100) {
            progressTitle.textContent = "Everything, done.";
            progressDetail.textContent = "A clean sweep. Make some room.";
        } else if (percentage >= 60) {
            progressTitle.textContent = "Well under way";
            progressDetail.textContent = complete + " of " + all.length + " tasks complete.";
        } else if (percentage > 0) {
            progressTitle.textContent = "Finding a rhythm";
            progressDetail.textContent = complete + " of " + all.length + " tasks complete.";
        } else {
            progressTitle.textContent = "Ready when you are";
            progressDetail.textContent = all.length + " task" + (all.length === 1 ? "" : "s") + " waiting.";
        }
    }

    function matchesSearch(card, query) {
        if (!query) return true;
        return (card.getAttribute("data-search") || "").indexOf(query) !== -1;
    }

    function applyFilters() {
        var query = (searchInput.value || "").trim().toLowerCase();
        var all = cards();
        var now = new Date();
        var visible = 0;

        all.forEach(function (card) {
            var show = true;
            var deadline = cardDeadline(card);

            if (statusFilter === "open" && isComplete(card)) show = false;
            if (statusFilter === "complete" && !isComplete(card)) show = false;
            if (statusFilter === "overdue" && !isOverdue(card)) show = false;
            if (selectedDateKey) {
                show = show && Boolean(deadline) && dateKey(deadline) === selectedDateKey;
            }
            if (!matchesSearch(card, query)) show = false;

            card.hidden = !show;
            if (show) visible += 1;
        });

        if (taskCount) taskCount.textContent = String(visible);

        if (filterSummary) {
            if (!all.length) {
                filterSummary.textContent = "No tasks yet";
            } else if (visible === all.length) {
                filterSummary.textContent = all.length + (all.length === 1 ? " task" : " tasks");
            } else {
                filterSummary.textContent = visible + " of " + all.length + " shown";
            }
        }

        if (emptyState) emptyState.hidden = all.length > 0;
        if (noResults) noResults.hidden = all.length === 0 || visible > 0;

        if (dateFilterBar) {
            dateFilterBar.hidden = !selectedDateKey;
        }
        if (selectedDateKey && dateFilterLabel) {
            var parts = selectedDateKey.split("-").map(Number);
            dateFilterLabel.textContent = new Intl.DateTimeFormat(undefined, {
                weekday: "long",
                month: "long",
                day: "numeric"
            }).format(new Date(parts[0], parts[1] - 1, parts[2]));
        }

        updateStats();
    }

    function numeric(card, name) {
        return parseInt(card.getAttribute(name) || "0", 10) || 0;
    }

    function compareCards(a, b, mode) {
        var aComplete = isComplete(a);
        var bComplete = isComplete(b);
        var aDeadline = cardDeadline(a);
        var bDeadline = cardDeadline(b);

        if (aComplete !== bComplete) return aComplete ? 1 : -1;

        if (mode === "deadline") {
            if (aDeadline && bDeadline) {
                if (aDeadline.getTime() !== bDeadline.getTime()) {
                    return aDeadline - bDeadline;
                }
            } else if (aDeadline) {
                return -1;
            } else if (bDeadline) {
                return 1;
            }
            return numeric(b, "data-priority") - numeric(a, "data-priority");
        }

        if (mode === "priority") {
            var priorityDifference = numeric(b, "data-priority") - numeric(a, "data-priority");
            if (priorityDifference !== 0) return priorityDifference;
            return cardCreated(b) - cardCreated(a);
        }

        if (mode === "newest") {
            return cardCreated(b) - cardCreated(a);
        }

        /* Smart order: deadlines first, then priority, then recency. */
        if (aDeadline && bDeadline) {
            if (aDeadline.getTime() !== bDeadline.getTime()) {
                return aDeadline - bDeadline;
            }
        } else if (aDeadline) {
            return -1;
        } else if (bDeadline) {
            return 1;
        }

        var smartPriority = numeric(b, "data-priority") - numeric(a, "data-priority");
        if (smartPriority !== 0) return smartPriority;
        return cardCreated(b) - cardCreated(a);
    }

    function sortTasks() {
        var mode = sortSelect.value;
        var sorted = cards().sort(function (a, b) {
            return compareCards(a, b, mode);
        });
        sorted.forEach(function (card) {
            list.appendChild(card);
        });
    }

    function notifyTodosChanged() {
        document.dispatchEvent(new CustomEvent("daymark:todos-changed"));
    }

    function buildCard(todo) {
        var fragment = template.content.cloneNode(true);
        var card = fragment.querySelector(".task-card");

        card.setAttribute("data-todo-id", String(todo.id));
        card.setAttribute("data-title", todo.title);
        card.setAttribute("data-description", todo.description || "");
        card.setAttribute("data-priority", String(todo.priority));
        card.setAttribute("data-complete", todo.complete ? "true" : "false");
        card.setAttribute("data-created-at", todo.created_at || "");
        card.setAttribute("data-deadline", todo.deadline || "");
        card.setAttribute("data-completed-at", todo.completed_at || "");
        card.setAttribute(
            "data-search",
            (todo.title + " " + (todo.description || "")).toLowerCase()
        );

        card.querySelector(".task-title").textContent = todo.title;

        var description = card.querySelector(".task-description");
        if (todo.description) {
            description.textContent = todo.description;
        } else {
            description.remove();
        }

        var priority = card.querySelector(".priority-pill");
        priority.classList.add("priority-" + (priorityKeys[todo.priority] || "medium"));
        priority.textContent = priorityNames[todo.priority] || "Priority " + todo.priority;

        var editButton = card.querySelector('[data-action="edit"]');
        var deleteButton = card.querySelector('[data-action="delete"]');
        editButton.setAttribute("aria-label", "Edit task: " + todo.title);
        deleteButton.setAttribute("aria-label", "Delete task: " + todo.title);

        updateCardMeta(card);
        return card;
    }

    function showFormError(message) {
        formError.textContent = message;
        formError.hidden = !message;
    }

    function syncDeadlineInput() {
        var enabled = deadlineToggle.checked;
        deadlineInput.disabled = !enabled;
        deadlineWrap.classList.toggle("is-disabled", !enabled);

        if (!enabled) {
            deadlineInput.value = "";
        } else if (!deadlineInput.value) {
            var now = new Date();
            var defaultDate = new Date(now.getTime() + 60 * 60 * 1000);
            defaultDate.setMinutes(Math.ceil(defaultDate.getMinutes() / 5) * 5, 0, 0);
            deadlineInput.value = localInputValue(defaultDate);
        }
    }

    function localInputValue(date) {
        return date.getFullYear() + "-" +
            String(date.getMonth() + 1).padStart(2, "0") + "-" +
            String(date.getDate()).padStart(2, "0") + "T" +
            String(date.getHours()).padStart(2, "0") + ":" +
            String(date.getMinutes()).padStart(2, "0");
    }

    function setPriority(value) {
        var radio = form.querySelector('input[name="priority"][value="' + value + '"]');
        if (radio) radio.checked = true;
    }

    function openDialog(mode, card) {
        form.reset();
        showFormError("");
        editingCard = null;
        taskIdInput.value = "";

        if (mode === "edit" && card) {
            editingCard = card;
            taskIdInput.value = card.getAttribute("data-todo-id");
            titleInput.value = card.getAttribute("data-title") || "";
            descriptionInput.value = card.getAttribute("data-description") || "";
            setPriority(parseInt(card.getAttribute("data-priority") || "3", 10));
            dialogKicker.textContent = "A gentle edit";
            dialogTitle.textContent = "Edit task";
            submitButton.textContent = "Save changes";

            var deadline = cardDeadline(card);
            deadlineToggle.checked = Boolean(deadline);
            deadlineInput.value = deadline ? localInputValue(deadline) : "";
        } else {
            dialogKicker.textContent = "A new intention";
            dialogTitle.textContent = "Add a task";
            submitButton.textContent = "Add task";
            setPriority(3);
            deadlineToggle.checked = false;
            deadlineInput.value = "";
        }

        syncDeadlineInput();
        dialog.showModal();
        window.setTimeout(function () {
            titleInput.focus();
            titleInput.select();
        }, 30);
    }

    function closeDialog() {
        if (dialog.open) dialog.close();
    }

    function extractError(payload) {
        if (!payload) return "Something went wrong. Please try again.";
        if (typeof payload.detail === "string") return payload.detail;
        if (Array.isArray(payload.detail)) {
            return payload.detail.map(function (item) {
                return item.msg || "Invalid value";
            }).join(" ");
        }
        return payload.message || "Something went wrong. Please try again.";
    }

    async function apiRequest(url, options) {
        var requestOptions = options || {};
        requestOptions.credentials = "same-origin";
        requestOptions.headers = Object.assign(
            { "Accept": "application/json" },
            requestOptions.headers || {}
        );

        var response = await fetch(url, requestOptions);

        if (response.status === 401) {
            window.location.href = "/auth/login-page?next=/todos";
            throw new Error("Your session has expired.");
        }

        if (response.status === 204) return null;

        var payload = null;
        try {
            payload = await response.json();
        } catch (error) {
            payload = null;
        }

        if (!response.ok) {
            throw new Error(extractError(payload));
        }

        return payload;
    }

    form.addEventListener("submit", async function (event) {
        event.preventDefault();
        showFormError("");

        var title = titleInput.value.trim();
        if (!title) {
            showFormError("Give this task a title.");
            titleInput.focus();
            return;
        }

        var hasDeadline = deadlineToggle.checked;
        if (hasDeadline && !deadlineInput.value) {
            showFormError("Choose a deadline, or turn the deadline switch off.");
            deadlineInput.focus();
            return;
        }

        var complete = editingCard ? isComplete(editingCard) : false;
        var payload = {
            title: title,
            description: descriptionInput.value.trim(),
            priority: parseInt((form.querySelector('input[name="priority"]:checked') || {}).value || "3", 10),
            complete: complete,
            deadline: hasDeadline ? new Date(deadlineInput.value).toISOString() : null
        };

        var editingId = taskIdInput.value;
        var oldLabel = submitButton.textContent;
        submitButton.disabled = true;
        submitButton.textContent = "Saving…";
        form.setAttribute("aria-busy", "true");

        try {
            if (editingId) {
                var updated = await apiRequest("/api/todos/" + editingId, {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                var replacement = buildCard(updated);
                if (editingCard && editingCard.isConnected) {
                    editingCard.replaceWith(replacement);
                } else {
                    list.appendChild(replacement);
                }
                closeDialog();
                window.showToast("Task updated.");
            } else {
                var created = await apiRequest("/api/todos", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                list.appendChild(buildCard(created));
                closeDialog();
                window.showToast(payload.deadline ? "Task added with a deadline." : "Task added.");
            }

            sortTasks();
            applyFilters();
            notifyTodosChanged();
        } catch (error) {
            showFormError(error.message || "Could not save this task.");
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = oldLabel;
            form.removeAttribute("aria-busy");
        }
    });

    async function toggleComplete(card) {
        var button = card.querySelector('[data-action="toggle"]');
        var nextState = !isComplete(card);
        button.disabled = true;

        try {
            var updated = await apiRequest(
                "/api/todos/" + card.getAttribute("data-todo-id") + "/complete",
                {
                    method: "PATCH",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ complete: nextState })
                }
            );

            card.setAttribute("data-complete", updated.complete ? "true" : "false");
            card.setAttribute("data-completed-at", updated.completed_at || "");
            updateCardMeta(card);
            sortTasks();
            applyFilters();
            notifyTodosChanged();
            window.showToast(updated.complete ? "Nice — one task done." : "Task moved back to open.");
        } catch (error) {
            window.showToast(error.message || "Could not update that task.", "error");
        } finally {
            button.disabled = false;
        }
    }

    async function removeTask(card) {
        var title = card.getAttribute("data-title") || "this task";
        if (!window.confirm('Delete "' + title + '"? This cannot be undone.')) return;

        try {
            await apiRequest("/api/todos/" + card.getAttribute("data-todo-id"), {
                method: "DELETE"
            });
            card.classList.add("is-removing");
            window.setTimeout(function () {
                card.remove();
                applyFilters();
                notifyTodosChanged();
            }, 180);
            window.showToast("Task deleted.");
        } catch (error) {
            window.showToast(error.message || "Could not delete that task.", "error");
        }
    }

    list.addEventListener("click", function (event) {
        var actionButton = event.target.closest("[data-action]");
        if (!actionButton) return;

        var card = actionButton.closest(".task-card");
        if (!card) return;

        var action = actionButton.getAttribute("data-action");
        if (action === "toggle") toggleComplete(card);
        if (action === "edit") openDialog("edit", card);
        if (action === "delete") removeTask(card);
    });

    document.getElementById("open-task-dialog").addEventListener("click", function () {
        openDialog("add");
    });

    var emptyAdd = document.getElementById("empty-add");
    if (emptyAdd) {
        emptyAdd.addEventListener("click", function () {
            openDialog("add");
        });
    }

    dialog.querySelectorAll("[data-close-dialog]").forEach(function (button) {
        button.addEventListener("click", closeDialog);
    });

    dialog.addEventListener("click", function (event) {
        if (event.target === dialog) closeDialog();
    });

    deadlineToggle.addEventListener("change", syncDeadlineInput);

    filterTabs.forEach(function (tab) {
        tab.addEventListener("click", function () {
            statusFilter = tab.getAttribute("data-filter");
            filterTabs.forEach(function (otherTab) {
                otherTab.classList.toggle("is-active", otherTab === tab);
            });
            applyFilters();
        });
    });

    searchInput.addEventListener("input", applyFilters);

    sortSelect.addEventListener("change", function () {
        sortTasks();
        applyFilters();
    });

    var dateFilterClear = document.getElementById("date-filter-clear");
    if (dateFilterClear) {
        dateFilterClear.addEventListener("click", function () {
            document.dispatchEvent(new CustomEvent("daymark:calendar-clear-request"));
        });
    }

    document.addEventListener("daymark:date-selected", function (event) {
        selectedDateKey = event.detail.key;
        applyFilters();
    });

    document.addEventListener("daymark:date-cleared", function () {
        selectedDateKey = null;
        applyFilters();
    });

    var resetView = document.getElementById("reset-view");
    if (resetView) {
        resetView.addEventListener("click", function () {
            searchInput.value = "";
            statusFilter = "all";
            filterTabs.forEach(function (tab) {
                tab.classList.toggle("is-active", tab.getAttribute("data-filter") === "all");
            });
            document.dispatchEvent(new CustomEvent("daymark:calendar-clear-request"));
            applyFilters();
        });
    }

    function setWorkspaceDate() {
        var now = new Date();
        var dateElement = document.getElementById("workspace-date");
        var greetingElement = document.getElementById("greeting");
        var hour = now.getHours();

        if (dateElement) dateElement.textContent = fullDateFormatter.format(now);
        if (greetingElement) {
            if (hour < 12) greetingElement.textContent = "Good morning";
            else if (hour < 18) greetingElement.textContent = "Good afternoon";
            else greetingElement.textContent = "Good evening";
        }
    }

    setWorkspaceDate();
    cards().forEach(updateCardMeta);
    sortTasks();
    applyFilters();
    notifyTodosChanged();
})();
