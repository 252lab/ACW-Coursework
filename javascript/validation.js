const form = document.getElementById("routeForm");
const errorBox = document.getElementById("error-message");
const errorText = document.getElementById("error-text");

form.addEventListener("submit", function (event) {
    const startTime = document.getElementById("startTime").value;
    const endTime = document.getElementById("endTime").value;

    //hide any previous error
    errorBox.style.display = "none";

    //both times cannot be entered
    if (startTime && endTime) {
        event.preventDefault();
        errorText.textContent ="Please enter either a start time or an end time, not both.";
        errorBox.style.display = "block";
    }
});