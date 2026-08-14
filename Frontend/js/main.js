const dashboardButton = document.getElementById("dashboardButton");
const backupsButton = document.getElementById("backupsButton");
const settingsButton = document.getElementById("settingsButton");

dashboardButton.addEventListener("click", () => {
    window.location.href = "index.html";
});

backupsButton.addEventListener("click", () => {
    window.location.href = "backups.html";
});

settingsButton.addEventListener("click", () => {
    window.location.href = "settings.html";
});