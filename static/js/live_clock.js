(function () {
    function updateClock() {
        const now = new Date();
        const options = {
            weekday: 'short',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        };

        const dateString = now.toLocaleTimeString('uk-UA', options);
        const clockElement = document.getElementById('live-clock');

        if (clockElement) {
            clockElement.textContent = dateString;
        }
    }

    document.addEventListener('DOMContentLoaded', function () {
        updateClock();
        setInterval(updateClock, 1000);
    });
})();
