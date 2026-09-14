const consoleExpandButton = document.getElementById("consoleExpandButton");
const terminal = document.getElementById('consoleTerminalOutput');
const consoleInputSendButton = document.getElementById('consoleInputSendButton');

const errorWords = [
    "Error",
    "ERROR",
    "error",
    "java.lang.Exception",
    "Exception"
]

const warningWords = [
    "Warning",
    "WARNING",
    "warning",
    "WARN",
    "Warn",
    "warn",
    "at"
]

const debugWords = [
    "TRACE",
    "Trace",
    "trace",
    "DEBUG",
    "Debug",
    "debug",
    "NOTICE",
    "Notice",
    "notice",
    "COMMAND",
    "Command",
    "commands",
    "INFO",
    "Info",
    "info"
]

const secondaryWords = [
    "...",
    "Caused by",
    "Suppressed:",
    "Exception in thread",
    "Stack trace"
]

const successWords = [
    "SUCCESS",
    "SUCCEEDED",
    "SUCCESSFUL",
    "COMPLETED",
    "COMPLETE",
    "READY",
    "AVAILABLE",
    "ONLINE",
    "CONNECTED",
    "ACCEPTED",
    "APPROVED",
    "ENABLED",
    "STARTED",
    "STARTING",
    "LOADED",
    "INITIALIZED",
    "REGISTERED",
    "CREATED",
    "SAVED",
    "BACKUP COMPLETE",
    "BACKUP SUCCESSFUL",
    "RELOADED",
    "RELOADING",
    "RESOLVED",
    "FOUND",
    "VALID",
    "PASSED",
    "PASS",
    "OK",
    "DONE",
    "SUCCESSFULLY",
    "MADE",
    "Made",
    "made",

    "FOR HELP, TYPE \"HELP\"",
    "STARTING MINECRAFT SERVER",
    "LOADING PROPERTIES",
    "PREPARING SPAWN AREA",
    "TIME ELAPSED",
    "SERVER STARTED",
    "LISTENING ON"
];

consoleExpandButton.addEventListener("click", () => {
    if (window.location.href.includes("console.html")) {
        window.location.href = "index.html";
    } else {
        window.location.href = "console.html";
    }
});

consoleInputSendButton.addEventListener("click", async () => {
    await sendConsoleInput();
});

async function sendConsoleInput() {
    const inputField = document.getElementById('consoleInputField');
    const command = inputField.value;
    response = await fetch("http://127.0.0.1:8000/server/sendCommand", {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ command })
    });
    const result = await response.json()
    if(response.ok){
        const terminal = document.getElementById('consoleContent');
        const response = result.response
        line = document.createElement('div');
        line.textContent = response;
        checkLineStatus(response, line);
        terminal.appendChild(line);
        terminal.scrollTop = terminal.scrollHeight;
        inputField.value = '';
    }
    else{
        await showInfoScreen(result.detail, false);
    }
}

const socket = new WebSocket('ws://127.0.0.1:8000/server/logs');
socket.onopen = () => {
    console.log('WebSocket connection established');
}

socket.onmessage = (event) => {
    const console = document.getElementById('consoleContent');
    const line = document.createElement('div');
    line.textContent = event.data;
    checkLineStatus(event.data, line);
    if(event.data.includes("RCON") || event.data.includes("Rcon") || event.data.includes("rcon")){
        pass;
    }
    console.appendChild(line);
    console.scrollTop = console.scrollHeight;
}

socket.onclose = () => {
    console.log("WebSocket disconnected");
};

socket.onerror = (error) => {
    console.error("WebSocket error:", error);
};

function checkLineStatus(lineString, lineObject) {
    if (errorWords.some(word => lineString.includes(word))) {
        lineObject.style.color = 'var(--status-danger)';
    }
    else if (warningWords.some(word => lineString.includes(word))) {
        lineObject.style.color = 'var(--status-warning)';
    }
    else if (debugWords.some(word => lineString.includes(word))) {
        lineObject.style.color = 'var(--status-info)';
    }
    else if (successWords.some(word => lineString.includes(word))) {
        lineObject.style.color = 'var(--status-success)';
    }
    else if (secondaryWords.some(word => lineString.includes(word))) {
        lineObject.style.color = 'var(--text-color-secondary)';
    }
    else {
        lineObject.style.color = 'var(--text-color)';
    }
}