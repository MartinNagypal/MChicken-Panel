const dashboardButton = document.getElementById("dashboardButton");
const consoleButton = document.getElementById("consoleButton");
const backupsButton = document.getElementById("backupsButton");
const settingsButton = document.getElementById("settingsButton");
const consoleExpandButton = document.getElementById("consoleExpandButton");

dashboardButton.addEventListener("click", () => {
    window.location.href = "index.html";
});

consoleButton.addEventListener("click", () => {
    window.location.href = "console.html";
});

backupsButton.addEventListener("click", () => {
    window.location.href = "backups.html";
});

settingsButton.addEventListener("click", () => {
    window.location.href = "settings.html";
});

consoleExpandButton.addEventListener("click", () => {
    if (window.location.href.includes("console.html")) {
        window.location.href = "index.html";
    } else {
        window.location.href = "console.html";
    }
});