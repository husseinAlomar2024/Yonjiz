/* Admin directory search. Destructive forms are confirmed by app.js. */
(function () {
    "use strict";

    var input = document.getElementById("admin-user-search");
    var rows = Array.prototype.slice.call(document.querySelectorAll("#admin-user-rows tr"));
    var emptyMessage = document.getElementById("admin-empty-search");

    if (!input || !rows.length) return;

    function filterRows() {
        var query = input.value.trim().toLowerCase();
        var visible = 0;

        rows.forEach(function (row) {
            var haystack = row.getAttribute("data-search") || "";
            var show = !query || haystack.indexOf(query) !== -1;
            row.hidden = !show;
            if (show) visible += 1;
        });

        if (emptyMessage) emptyMessage.hidden = visible > 0;
    }

    input.addEventListener("input", filterRows);
})();
