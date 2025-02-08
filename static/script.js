// Flash message fade out
document.addEventListener("DOMContentLoaded", function () {
    setTimeout(() => {
        let flashMessages = document.querySelectorAll(".flash-message");
        flashMessages.forEach(msg => {
            msg.style.opacity = "0";
            setTimeout(() => msg.remove(), 1000);
        });
    }, 3000);
});

// Select Time of Day function
function selectTimeOfDay(value) {
    document.getElementById('collection-time-of-day').value = value;
    const dayButton = document.getElementById('day-button');
    const nightButton = document.getElementById('night-button');

    if (value === 1) {
        dayButton.classList.add('active');
        nightButton.classList.remove('active');
    } else {
        nightButton.classList.add('active');
        dayButton.classList.remove('active');
    }
}
