const sshIp = document.getElementById("sshIp");
const sshPort = document.getElementById("sshPort");
const sshUsername = document.getElementById("sshUsername");
const sshPassword = document.getElementById("sshPassword");
const serverSetupTabSSHSubmit = document.getElementById("serverSetupTabSSHSubmit");

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

serverSetupTabSSHSubmit.addEventListener("click", async () => {
    const ip = sshIp.value;
    let port = sshPort.value;
    const username = sshUsername.value;
    const password = sshPassword.value;

    if(!ip){
        sshIp.classList.add("mainInputStyleFalse");
    }
    else{
        sshIp.classList.remove("mainInputStyleFalse");
    }
    if(!port){
        port = 22; // Default SSH port
    }
    if(!username){
        sshUsername.classList.add("mainInputStyleFalse");
    }
    else{
        sshUsername.classList.remove("mainInputStyleFalse");
    }
    if(!password){
        sshPassword.classList.add("mainInputStyleFalse");
    }
    else{
        sshPassword.classList.remove("mainInputStyleFalse");
    }

    if(ip && port && username && password) {
        response = await fetch('http://127.0.0.1:8000/server/sshConfig', {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ ip, port, username, password })
        });
        const result = await response.json();
        if(response.ok){
            await showInfoScreen("SSH configuration saved successfully.", true);
        }
        else{
            await showInfoScreen(result.detail, false);
        }
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

async function fetchAllUsers() {
    try {
        const response = await fetch("http://127.0.0.1:8000/users", {
            method: "GET",
            credentials: "include"
        });
        const data = await response.json();
        if(response.ok){
            console.log(data);
            const userSettingsList = document.getElementById("userSettingsList");
            for (const user of data.users.users) {
                const userItem = document.createElement("div");
                userItem.classList.add("userSettingsUserItem");
                userSettingsList.appendChild(userItem);
                const userItemSpan = document.createElement("span");
                const userProfileIcon = document.createElement("i");
                const usernameSpan = document.createElement("span");
                userItemSpan.classList.add("userSettingsUserItemName");
                userProfileIcon.classList.add("fa-solid", "fa-user");
                userProfileIcon.style.color = "var(--accent-primary)";
                usernameSpan.textContent = user.username;
                userItemSpan.appendChild(userProfileIcon);
                userItemSpan.appendChild(usernameSpan);
                userItem.appendChild(userItemSpan);
                const roleSpan = document.createElement("span");
                roleSpan.textContent = user.role;
                userItem.appendChild(roleSpan);
                const deleteUserButton = document.createElement("i");
                deleteUserButton.classList.add("fa-solid", "fa-trash");
                deleteUserButton.style.color = "var(--status-danger)";
                userItem.appendChild(deleteUserButton);
            }
        }
    }
    catch (error) {
        console.error('Error fetching users:', error);
    }
}

fetchAllUsers();
