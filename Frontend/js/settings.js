const sshIp = document.getElementById("sshIp");
const sshPort = document.getElementById("sshPort");
const sshUsername = document.getElementById("sshUsername");
const sshPassword = document.getElementById("sshPassword");
const serverSetupTabSSHSubmit = document.getElementById("serverSetupTabSSHSubmit");
const buttonLogoutAllSessions = document.getElementById("buttonLogoutAllSessions");
const buttonDeleteUserScreenClose = document.getElementById("buttonDeleteUserScreenClose");
const buttonDeleteUserScreenConfirm = document.getElementById("buttonDeleteUserScreenConfirm");
const confirmDeletionPasswordInput = document.getElementById("confirmDeletionPasswordInput");
let username;
let deleteUsername;


function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function checkAuthStatus(){
    try{
        result = await fetch("http://127.0.0.1:8000/verifySession", {
            method: "GET",
            credentials: "include",
            headers: {
                "Content-Type": "application/json"
            }
        });
        const data = await result.json();
        console.log(data);
        if(!result.ok){
            window.location.href = "../pages/auth.html";
        }
        else{
            await fetchUsername();
        }
    }
    catch (error) {
        window.location.href = "../pages/auth.html";
        console.error("Error checking authentication status:", error);
    }
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

        const userElements = document.querySelectorAll(".userSettingsUserItem");
        for(const userElement of userElements){
            if(!userElement.classList.contains("addUserItem")){
                userElement.remove();
            }
        }

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

                const currentUserResponse = await fetch("http://127.0.0.1:8000/users/user/session", {
                    method: "GET",
                    credentials: "include"
                });
                const currentUserData = await currentUserResponse.json();
                console.log(currentUserData);

                const initiatorRoleResponse = await fetch("http://127.0.0.1:8000/user/role/session", {
                    method: "GET",
                    credentials: "include"
                });
                const initiatorRoleData = await initiatorRoleResponse.json();
                const initiatorRole = initiatorRoleData.role;

                //role selector for admin users to change roles of other users
                if(initiatorRole === "admin" && user.username !== currentUserData.username){
                    const roleSelectorDiv = document.createElement("div");
                    roleSelectorDiv.classList.add("roleSelectorDiv");
                    const roleSelect = document.createElement("select");
                    roleSelect.classList.add("mainSelectStyle");
                    roleSelect.style.maxWidth = "100px";
                    const roleOption1 = document.createElement("option");
                    roleOption1.value = "admin";
                    roleOption1.textContent = "Admin";

                    const roleOption2 = document.createElement("option");
                    roleOption2.value = "mod";
                    roleOption2.textContent = "Mod";

                    const roleOption3 = document.createElement("option");
                    roleOption3.value = "user";
                    roleOption3.textContent = "User";

                    roleSelect.appendChild(roleOption1);
                    roleSelect.appendChild(roleOption2);
                    roleSelect.appendChild(roleOption3);

                    roleSelect.value = user.role;
                    roleSelectorDiv.appendChild(roleSelect);
                    userItem.appendChild(roleSelectorDiv);


                    roleSelect.addEventListener("change", async (event) => {
                        const confirmRoleChangesScreen = document.getElementById("confirmRoleChangesScreen");
                        confirmRoleChangesScreen.classList.remove("infoScreenPopupHidden");

                        //implement close button
                        const closeButton = document.getElementById("buttonConfirmRoleChangesScreenClose");
                        closeButton.addEventListener("click", () => {
                            confirmRoleChangesScreen.classList.add("infoScreenPopupHidden");
                            roleSelect.value = user.role;
                        });

                        //implement confirm button
                        const confirmButton = document.getElementById("buttonConfirmRoleChanges");
                        passwordInput = document.getElementById("confirmRoleChangesPasswordInput");
                        password = passwordInput.value;
                        confirmButton.addEventListener("click", async () => {
                            const passwordInput = document.getElementById("confirmRoleChangesPasswordInput");
                            const password = passwordInput.value;
                            const roleUpdateResult = await fetch("http://127.0.0.1:8000/user/role/update", {
                                method: "POST",
                                credentials: "include",
                                headers: {
                                    "Content-Type": "application/json"
                                },
                                body: JSON.stringify({
                                    username: user.username,
                                    newRole: roleSelect.value,
                                    password: password
                                })
                            });
                            const roleUpdateData = await roleUpdateResult.json();
                            if (roleUpdateResult.ok) {
                                passwordInput.classList.remove("mainInputStyleFalse");
                                passwordInput.classList.add("mainInputStyleTrue");
                                await showInfoScreen("User role updated successfully.", true);
                                confirmRoleChangesScreen.classList.add("infoScreenPopupHidden");
                                user.role = roleSelect.value;
                                passwordInput.value = "";
                            } else {
                                if(roleUpdateResult.status === 401){
                                    passwordInput.value = "";
                                    passwordInput.classList.add("mainInputStyleFalse");
                                }
                                await showInfoScreen(roleUpdateData.detail, false);
                                roleSelect.value = user.role;
                            }

                        });             
                    });

                }
                else{
                    const roleSpan = document.createElement("span");
                    roleSpan.textContent = user.role;
                    userItem.appendChild(roleSpan);
                }
                
                if(initiatorRole === "admin" && user.username !== currentUserData.username){
                    const deleteUserButton = document.createElement("i");
                    deleteUserButton.classList.add("fa-solid", "fa-trash");
                    deleteUserButton.style.color = "var(--status-danger)";
                    userItem.appendChild(deleteUserButton);
                    

                    deleteUserButton.addEventListener("click", async () => {
                        const deletUserScreen = document.getElementById("deleteUserScreen");
                        deleteUsername = user.username;
                        deletUserScreen.classList.remove("infoScreenPopupHidden");
                    });
                }
            }
        }
        else {
            document.getElementById("userSettingsTab").style.display = "none";
        }
    }
    catch (error) {
        console.error('Error fetching users:', error);
    }
}

async function deleteUser(username) {
    try {
        const deleteResponse = await fetch("http://127.0.0.1:8000/user/delete", {
            method: "POST",
            credentials: "include",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ username: username })
        });
        const responseData = await deleteResponse.json();
        if (deleteResponse.ok) {
            confirmDeletionPasswordInput.value = "";
            const deletUserScreen = document.getElementById("deleteUserScreen");
            deletUserScreen.classList.add("infoScreenPopupHidden");
            await fetchAllUsers();
            await showInfoScreen("User deleted successfully.", true);
        }
        else {
            await showInfoScreen(responseData.detail, false);
        }
    } catch (error) {
        console.error("Error deleting user:", error);
        throw error;
    }
}

async function fetchUsername() {
    try {
        const response = await fetch("http://127.0.0.1:8000/user/username", {
            method: "GET",
            credentials: "include"
        });
        const data = await response.json();
        if (response.ok) {
            username = data.username;
        }
    } catch (error) {
        console.error("Error fetching username:", error);
        throw error;
    }
}

buttonLogoutAllSessions.addEventListener("click", async () => {
    try {
        const response = await fetch("http://127.0.0.1:8000/logout/all", {
            method: "POST",
            credentials: "include",
            headers: {
                "Content-Type": "application/json"
            }
        });
        const result = await response.json();
        if (response.ok) {
            await showInfoScreen("Successfully logged out from all sessions.", true);
            sleep(2000);
            await checkAuthStatus();
        }
    } catch (error) {
        console.error("Error logging out all sessions:", error);
    }
});

buttonDeleteUserScreenClose.addEventListener("click", () => {
    const deletUserScreen = document.getElementById("deleteUserScreen");
    deletUserScreen.classList.add("infoScreenPopupHidden");
});

buttonDeleteUserScreenConfirm.addEventListener("click", async () => {
    let confirmDeletionPassword = confirmDeletionPasswordInput.value;
    const response = await fetch("http://127.0.0.1:8000/user/verifyPassword", {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ password: confirmDeletionPassword })
    });
    const result = await response.json();
    console.log(result);
    if (response.ok) {
        confirmDeletionPasswordInput.classList.remove("mainInputStyleFalse");
        confirmDeletionPasswordInput.classList.add("mainInputStyleTrue");
        await deleteUser(deleteUsername);;
        deleteUsername = null;
        const deletUserScreen = document.getElementById("deleteUserScreen");
        deletUserScreen.classList.add("infoScreenPopupHidden");
    } else {
        confirmDeletionPasswordInput.value = "";
        showInfoScreen("The password you entered is invalid. Please try again.", false);
        confirmDeletionPasswordInput.classList.add("mainInputStyleFalse");
    }
});


document.addEventListener("keydown", async (event) => {
    if (event.key === "Escape") {
        const deletUserScreen = document.getElementById("deleteUserScreen");
        deletUserScreen.classList.add("infoScreenPopupHidden");
    }
});

fetchAllUsers();
