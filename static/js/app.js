/* Shared page behaviour: confirmation dialogs and a small toast system. */
(function () {
    "use strict";

    document.querySelectorAll("form[data-confirm]").forEach(function (form) {
        form.addEventListener("submit", function (event) {
            var message = form.getAttribute("data-confirm") || "Are you sure?";
            if (!window.confirm(message)) {
                event.preventDefault();
            }
        });
    });

    var region = document.getElementById("toast-region");

    window.showToast = function (message, kind) {
        if (!region) return;

        while (region.children.length >= 3) {
            region.removeChild(region.firstElementChild);
        }

        var toast = document.createElement("div");
        toast.className = "toast" + (kind === "error" ? " is-error" : "");

        var icon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        icon.setAttribute("class", "icon");
        icon.setAttribute("aria-hidden", "true");
        var use = document.createElementNS("http://www.w3.org/2000/svg", "use");
        use.setAttribute("href", kind === "error" ? "#icon-alert" : "#icon-check");
        icon.appendChild(use);

        var text = document.createElement("span");
        text.textContent = message;

        toast.appendChild(icon);
        toast.appendChild(text);
        region.appendChild(toast);

        requestAnimationFrame(function () {
            toast.classList.add("is-visible");
        });

        window.setTimeout(function () {
            toast.classList.remove("is-visible");
            window.setTimeout(function () {
                toast.remove();
            }, 260);
        }, 3600);
    };
})();
