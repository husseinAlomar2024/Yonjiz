/* Deadline calendar. Deadlines come from the rendered .task-card elements,
   so the calendar has no separate data source to keep in sync. */
(function () {
    "use strict";

    var calendar = document.getElementById("deadline-calendar");
    var grid = document.getElementById("calendar-grid");
    var monthTitle = document.getElementById("calendar-title");
    var previousButton = document.getElementById("calendar-prev");
    var nextButton = document.getElementById("calendar-next");
    var todayButton = document.getElementById("calendar-today");
    var clearButton = document.getElementById("clear-date-filter");
    var collapseToggle = document.getElementById("calendar-toggle");
    var collapseLabel = document.getElementById("calendar-toggle-label");

    if (!calendar || !grid || !monthTitle) return;

    var today = new Date();
    var viewDate = new Date(today.getFullYear(), today.getMonth(), 1);
    var selectedKey = null;

    var monthFormatter = new Intl.DateTimeFormat(undefined, {
        month: "long",
        year: "numeric"
    });
    var dayFormatter = new Intl.DateTimeFormat(undefined, {
        weekday: "long",
        month: "long",
        day: "numeric"
    });
    var selectedFormatter = new Intl.DateTimeFormat(undefined, {
        weekday: "short",
        month: "short",
        day: "numeric"
    });

    function dateKey(date) {
        return date.getFullYear() + "-" +
            String(date.getMonth() + 1).padStart(2, "0") + "-" +
            String(date.getDate()).padStart(2, "0");
    }

    function startOfDay(date) {
        return new Date(date.getFullYear(), date.getMonth(), date.getDate());
    }

    function deadlineMap() {
        var map = {};
        var now = new Date();

        document.querySelectorAll(".task-card[data-deadline]").forEach(function (card) {
            var raw = card.getAttribute("data-deadline");
            if (!raw) return;

            var deadline = new Date(raw);
            if (Number.isNaN(deadline.getTime())) return;

            var key = dateKey(deadline);
            if (!map[key]) {
                map[key] = { count: 0, open: 0, overdue: 0 };
            }

            map[key].count += 1;
            if (card.getAttribute("data-complete") !== "true") {
                map[key].open += 1;
                if (deadline < now) map[key].overdue += 1;
            }
        });

        return map;
    }

    function dispatchSelected(key, date) {
        document.dispatchEvent(new CustomEvent("daymark:date-selected", {
            detail: {
                key: key,
                label: selectedFormatter.format(date)
            }
        }));
    }

    function setCollapsed(collapsed) {
        calendar.classList.toggle("is-collapsed", collapsed);
        if (collapseToggle) {
            collapseToggle.setAttribute("aria-expanded", collapsed ? "false" : "true");
        }
        if (collapseLabel) {
            collapseLabel.textContent = collapsed ? "Show calendar" : "Hide calendar";
        }
    }

    function render() {
        var year = viewDate.getFullYear();
        var month = viewDate.getMonth();
        var firstOfMonth = new Date(year, month, 1);
        var startOffset = firstOfMonth.getDay();
        var startDate = new Date(year, month, 1 - startOffset);
        var deadlines = deadlineMap();
        var todayKey = dateKey(today);

        monthTitle.textContent = monthFormatter.format(viewDate);
        grid.innerHTML = "";

        var fragment = document.createDocumentFragment();

        for (var index = 0; index < 42; index += 1) {
            var date = new Date(
                startDate.getFullYear(),
                startDate.getMonth(),
                startDate.getDate() + index
            );
            var key = dateKey(date);
            var info = deadlines[key];
            var button = document.createElement("button");

            button.type = "button";
            button.className = "calendar-day";
            button.dataset.date = key;
            button.setAttribute("role", "gridcell");

            if (date.getMonth() !== month) button.classList.add("is-outside");
            if (date.getDay() === 0 || date.getDay() === 6) {
                button.classList.add("is-weekend");
            }
            if (key === todayKey) button.classList.add("is-today");
            if (key === selectedKey) {
                button.classList.add("is-selected");
                button.setAttribute("aria-selected", "true");
            } else {
                button.setAttribute("aria-selected", "false");
            }

            if (info) {
                button.classList.add("has-deadline");
                if (info.overdue > 0) button.classList.add("has-overdue");
                if (info.open === 0) button.classList.add("has-completed");
            }

            button.textContent = String(date.getDate());
            button.setAttribute(
                "aria-label",
                dayFormatter.format(date) +
                (info ? " — " + info.count + " deadline" + (info.count === 1 ? "" : "s") : "")
            );

            fragment.appendChild(button);
        }

        grid.appendChild(fragment);

        if (clearButton) {
            clearButton.hidden = selectedKey === null;
        }
    }

    function selectDate(key, date, syncMonth) {
        selectedKey = key;
        if (syncMonth) {
            viewDate = new Date(date.getFullYear(), date.getMonth(), 1);
        }
        render();
        dispatchSelected(key, date);
    }

    function clearSelection(dispatch) {
        selectedKey = null;
        render();
        if (dispatch !== false) {
            document.dispatchEvent(new CustomEvent("daymark:date-cleared"));
        }
    }

    grid.addEventListener("click", function (event) {
        var button = event.target.closest(".calendar-day");
        if (!button) return;

        var parts = button.dataset.date.split("-").map(Number);
        var date = new Date(parts[0], parts[1] - 1, parts[2]);
        selectDate(button.dataset.date, date, button.classList.contains("is-outside"));
    });

    previousButton.addEventListener("click", function () {
        viewDate = new Date(viewDate.getFullYear(), viewDate.getMonth() - 1, 1);
        render();
    });

    nextButton.addEventListener("click", function () {
        viewDate = new Date(viewDate.getFullYear(), viewDate.getMonth() + 1, 1);
        render();
    });

    todayButton.addEventListener("click", function () {
        today = new Date();
        viewDate = new Date(today.getFullYear(), today.getMonth(), 1);
        selectDate(dateKey(today), today, true);
    });

    if (clearButton) {
        clearButton.addEventListener("click", function () {
            clearSelection(true);
        });
    }

    if (collapseToggle) {
        collapseToggle.addEventListener("click", function () {
            setCollapsed(!calendar.classList.contains("is-collapsed"));
        });

        if (window.matchMedia("(max-width: 760px)").matches) {
            setCollapsed(true);
        }
    }

    document.addEventListener("daymark:calendar-clear-request", function () {
        clearSelection(true);
    });

    document.addEventListener("daymark:todos-changed", function () {
        render();
    });

    render();

    window.DaymarkCalendar = {
        clear: function () {
            clearSelection(true);
        }
    };
})();
