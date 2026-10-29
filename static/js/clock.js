/* Live analog + digital clock. The clock is presentation-only; it is not
   stored in the database and does not affect task deadlines. */
(function () {
    "use strict";

    var timeEl = document.getElementById("clock-time");
    var secondsEl = document.getElementById("clock-seconds");
    var periodEl = document.getElementById("clock-period");
    var dateEl = document.getElementById("clock-date");
    var zoneEl = document.getElementById("clock-zone");
    var hourHand = document.getElementById("clock-hour-hand");
    var minuteHand = document.getElementById("clock-minute-hand");
    var secondHand = document.getElementById("clock-second-hand");

    if (!timeEl || !hourHand) return;

    var dateFormatter = new Intl.DateTimeFormat(undefined, {
        weekday: "long",
        month: "long",
        day: "numeric",
        year: "numeric"
    });

    var zone = "";
    try {
        zone = new Intl.DateTimeFormat().resolvedOptions().timeZone || "";
    } catch (error) {
        zone = "";
    }
    if (zoneEl) {
        zoneEl.textContent = zone ? zone.replace(/_/g, " ") : "Your local timezone";
    }

    function pad(value) {
        return String(value).padStart(2, "0");
    }

    function tick() {
        var now = new Date();
        var hours = now.getHours();
        var minutes = now.getMinutes();
        var seconds = now.getSeconds();
        var period = hours >= 12 ? "PM" : "AM";
        var displayHour = hours % 12 || 12;

        timeEl.textContent = displayHour + ":" + pad(minutes);
        if (secondsEl) secondsEl.textContent = pad(seconds);
        if (periodEl) periodEl.textContent = period;
        if (dateEl) dateEl.textContent = dateFormatter.format(now);

        var secondAngle = seconds * 6;
        var minuteAngle = (minutes + seconds / 60) * 6;
        var hourAngle = ((hours % 12) + minutes / 60 + seconds / 3600) * 30;

        hourHand.style.transform = "rotate(" + hourAngle + "deg)";
        minuteHand.style.transform = "rotate(" + minuteAngle + "deg)";
        if (secondHand) {
            secondHand.style.transform = "rotate(" + secondAngle + "deg)";
        }
    }

    tick();
    window.setInterval(tick, 1000);
})();
