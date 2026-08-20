const dashboardButton = document.getElementById("dashboardButton");
const consoleButton = document.getElementById("consoleButton");
const backupsButton = document.getElementById("backupsButton");
const settingsButton = document.getElementById("settingsButton");
const consoleExpandButton = document.getElementById("consoleExpandButton");
const terminal = document.getElementById('consoleTerminalOutput');

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


const socket = new WebSocket('ws://127.0.0.1:8000/server/logs');
socket.onopen = () => {
    console.log('WebSocket connection established');
}

socket.onmessage = (event) => {
    const console = document.getElementById('consoleContent');
    const line = document.createElement('div');
    line.textContent = event.data;

    console.appendChild(line);
    console.scrollTop = terminal.scrollHeight;
}

socket.onclose = () => {
    console.log("WebSocket disconnected");
};

socket.onerror = (error) => {
    console.error("WebSocket error:", error);
};