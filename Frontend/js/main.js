const dashboardButton = document.getElementById("dashboardButton");
const consoleButton = document.getElementById("consoleButton");
const backupsButton = document.getElementById("backupsButton");
const settingsButton = document.getElementById("settingsButton");
const logoutButton = document.getElementById("logoutButton");

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

const isSmallScreen = window.innerWidth < 1200 || window.innerHeight < 800;

if(isSmallScreen){
    window.location.href = "/mobile";
}

async function checkAuthStatus(){
    try{
        result = await fetch("/verifySession", {
            method: "GET",
            credentials: "include",
            headers: {
                "Content-Type": "application/json"
            }
        });
        const data = await result.json();
        console.log(data);
        if(!result.ok){
            window.location.href = "/auth";
        }
        else{
            await fetchUsername();
        }
    }
    catch (error) {
        window.location.href = "/auth";
        console.error("Error checking authentication status:", error);
    }
}

async function checkAuthContinuerly(){
    while(true){
        await checkAuthStatus();
        await sleep(10000);
    }
}

checkAuthContinuerly();


dashboardButton.addEventListener("click", () => {
    window.location.href = "/dashboard";
});

consoleButton.addEventListener("click", () => {
    window.location.href = "/console";
});

backupsButton.addEventListener("click", () => {
    window.location.href = "/backups";
});

settingsButton.addEventListener("click", () => {
    window.location.href = "/settings";
});

document.addEventListener("keydown", async (event) => {
    if (event.key === "Enter") {
        await sendConsoleInput();
    }
});

logoutButton.addEventListener("click", async () => {
    result = await fetch("/logout", {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json"
        }
    });
    if(result.ok){
        window.location.href = "/auth";
    }
});

async function showInfoScreen(message, success = false) {
    const infoScreen = document.getElementById("infoScreen");
    const infoScreenText = document.getElementById("infoScreenText");

    infoScreenText.textContent = message;

    infoScreen.classList.toggle("infoScreenSuccess", success);
    infoScreen.classList.add("infoScreenVisible");

    await sleep(2500);

    infoScreen.classList.remove("infoScreenVisible");
}
async function fetchUsername() {
    try {
        const response = await fetch("/user/username", {
            method: "GET",
            credentials: "include"
        });
        const data = await response.json();
        if (response.ok) {
            document.getElementById("sidePanelUsername").textContent = data.username;
        }
    } catch (error) {
        console.error("Error fetching username:", error);
        throw error;
    }
}
