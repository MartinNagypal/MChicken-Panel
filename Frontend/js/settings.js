const buttonServerSetupTabConfigureServer = document.getElementById("serverSetupTabConfigureServer");
const buttonLogoutAllSessions = document.getElementById("buttonLogoutAllSessions");
const buttonDeleteUserScreenClose = document.getElementById("buttonDeleteUserScreenClose");
const buttonAddUser = document.getElementById("addUserItem");
let username;


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

/*
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
*/

buttonServerSetupTabConfigureServer.addEventListener("click", async () => {
    await configureServer();
});

async function configureServer(){
    const attributes = []
    attributes.push(document.getElementById("sshIp")); //0
    attributes.push(document.getElementById("sshPort")); //1 optional
    attributes.push(document.getElementById("sshUsername")); //2
    attributes.push(document.getElementById("sshPassword")); //3
    attributes.push(document.getElementById("rconPort")); //4 optional
    attributes.push(document.getElementById("containerName")); //5
    attributes.push(document.getElementById("dirToServerData")); //6
    attributes.push(document.getElementById("dirToDC_File")); //7
    attributes.push(document.getElementById("dirToBackups")); //8 optional

    let sshPort = attributes[1].value;
    let rconPort = attributes[4].value;
    let dirToBackups = attributes[8].value;

    let allParametersFilled = true;

    for(let i = 0; i < attributes.length; i++){
        if(!attributes[i].value && i!==1 && i!==4 && i!==8){
            attributes[i].classList.add("mainInputStyleFalse");
            allParametersFilled = false;
        }
        else{
            attributes[i].classList.remove("mainInputStyleFalse");
            attributes[i].classList.add("mainInputStyleTrue");
        }
    }

    if(!allParametersFilled){
        await showInfoScreen("Please fill out all required fields.", false);
        for(let i = 0; i < attributes.length; i++){
            attributes[i].classList.remove("mainInputStyleFalse");
        }
        return;
    }

    if(!attributes[1].value){
        sshPort = 22;
    }

    if(!attributes[4].value){
        rconPort = 25575;
    }

    if(!attributes[8].value){
        dirToBackups = "none";
    }

    //validate IP
    if(!validateIPaddress(attributes[0].value)){
        attributes[0].classList.remove("mainInputStyleTrue");
        attributes[0].classList.add("mainInputStyleFalse");

        for(let i = 0; i < attributes.length; i++){
            attributes[i].classList.remove("mainInputStyleTrue");
        }

        return
    }

    if(!validatePort(sshPort)){
        attributes[1].classList.remove("mainInputStyleTrue");
        attributes[1].classList.add("mainInputStyleFalse");

        for(let i = 0; i < attributes.length; i++){
            attributes[i].classList.remove("mainInputStyleTrue");
        }

        return
    }

    if(!validatePort(rconPort)){
        attributes[4].classList.remove("mainInputStyleTrue");
        attributes[4].classList.add("mainInputStyleFalse");

        for(let i = 0; i < attributes.length; i++){
            attributes[i].classList.remove("mainInputStyleTrue");
        }

        return
    }

    if(allParametersFilled){
        response = await fetch('http://127.0.0.1:8000/server/configure', {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                sshIp: attributes[0].value,
                sshPort: sshPort,
                sshUsername: attributes[2].value,
                sshPassword: attributes[3].value, 
                rconPort: rconPort,
                containerName: attributes[5].value,
                dirToServerData: attributes[6].value,
                dirToDC_File: attributes[7].value,
                dirToBackups: dirToBackups
            })
        });
        data = await response.json();
        if(!response.ok){
            await showInfoScreen(data.detail, false);
            for(let i = 0; i < attributes.length; i++){
                attributes[i].classList.remove("mainInputStyleTrue");
            }
        }
        else{
            await showInfoScreen("Server succesfully configured.", true);
            for(let i = 0; i < attributes.length; i++){
                attributes[i].classList.remove("mainInputStyleTrue");
            }
        }
    }
    else{
        await showInfoScreen("Please fill out all required fields.", false);
        for(let i = 0; i < attributes.length; i++){
            attributes[i].classList.remove("mainInputStyleFalse");
        }
    }

}

async function getCurrentServerConfig(){
    response = await fetch('http://127.0.0.1:8000/server/configure/current', {
        method: 'GET',
        credentials: 'include'
    });
    data = await response.json();
    if(response.ok){
        const attributes = []
        attributes.push(document.getElementById("sshIp")); //0
        attributes.push(document.getElementById("sshPort")); //1 optional
        attributes.push(document.getElementById("sshUsername")); //2
        attributes.push(document.getElementById("rconPort")); //3 optional
        attributes.push(document.getElementById("containerName")); //4
        attributes.push(document.getElementById("dirToServerData")); //5
        attributes.push(document.getElementById("dirToDC_File")); //6
        attributes.push(document.getElementById("dirToBackups")); //7 optional

        attributes[0].setAttribute("placeholder", data.ip);
        attributes[1].setAttribute("placeholder", data.port);
        attributes[2].setAttribute("placeholder", data.username);
        attributes[3].setAttribute("placeholder", data.rconPort);
        attributes[4].setAttribute("placeholder", data.containerName);
        attributes[5].setAttribute("placeholder", data.dirToServerData);
        attributes[6].setAttribute("placeholder", data.dirToDC_File);
        attributes[7].setAttribute("placeholder", data.dirToBackups);
    }    
}

getCurrentServerConfig();

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
                                confirmRoleChangesScreen.classList.add("infoScreenPopupHidden");
                                await showInfoScreen("User role updated successfully.", true);
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
                        deletUserScreen.classList.remove("infoScreenPopupHidden");

                        //event listener for confirm button
                        const buttonDeleteUserScreenConfirm = document.getElementById("buttonDeleteUserScreenConfirm");
                        const confirmDeletionPasswordInput = document.getElementById("confirmDeletionPasswordInput");

                        buttonDeleteUserScreenConfirm.addEventListener("click", async () => {
                            const password = confirmDeletionPasswordInput.value;
                            deletUserScreen.classList.add("infoScreenPopupHidden");
                            await deleteUser(user.username, password);
                            confirmDeletionPasswordInput.value = "";
                        });

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

async function deleteUser(username, password) {
    try {
        const deleteResponse = await fetch("http://127.0.0.1:8000/user/delete", {
            method: "POST",
            credentials: "include",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ username: username, password: password })
        });
        const responseData = await deleteResponse.json();
        if (deleteResponse.ok) {
            confirmDeletionPasswordInput.value = "";
            const deletUserScreen = document.getElementById("deleteUserScreen");
            await fetchAllUsers();
            await showInfoScreen("User deleted successfully.", true);
            deletUserScreen.classList.add("infoScreenPopupHidden");
        } 
        else if(deleteResponse.status === 401){
            confirmDeletionPasswordInput.value = "";
            confirmDeletionPasswordInput.classList.add("mainInputStyleFalse");
            await showInfoScreen(responseData.detail, false);
        }
        else {
            await showInfoScreen(responseData.detail, false);
        }
    } catch (error) {
        console.error("Error deleting user:", error);
        throw error;
    }
}

buttonAddUser.addEventListener("click", async () => {
    const addUserScreen = document.getElementById("addUserScreen");
    addUserScreen.classList.remove("infoScreenPopupHidden");


    //close event listener
    const closeButton = document.getElementById("buttonAddUserPopupClose");
    closeButton.addEventListener("click", () => {
        addUserScreen.classList.add("infoScreenPopupHidden");
    });

    document.addEventListener("keydown", async (event) => {
        if (event.key === "Escape") {
            addUserScreen.classList.add("infoScreenPopupHidden");
        }
    });

    //validate username and password inputs
    const buttonAddUserConfirm = document.getElementById("buttonAddUserConfirm");
    buttonAddUserConfirm.addEventListener("click", async () => {
        const usernameInput = document.getElementById("addUserUsernameInput");
        const passwordInput = document.getElementById("addUserPasswordInput");

        if(!validateUsername(usernameInput.value)){
            usernameInput.classList.add("mainInputStyleFalse");
        }
        else{
            usernameInput.classList.remove("mainInputStyleFalse");
            usernameInput.classList.add("mainInputStyleTrue");
        }

        if(!validatePassword(passwordInput.value)){
            passwordInput.classList.add("mainInputStyleFalse");
        }
        else{
            passwordInput.classList.remove("mainInputStyleFalse");
            passwordInput.classList.add("mainInputStyleTrue");
        }

        if(validateUsername(usernameInput.value) && validatePassword(passwordInput.value)){
            const roleSelect = document.getElementById("addUserRoleSelect");
            const newUsername = usernameInput.value;
            const newPassword = passwordInput.value;
            const newRole = roleSelect.value;

            try {
                const response = await fetch("http://127.0.0.1:8000/users/user/create", {
                    method: "POST",
                    credentials: "include",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        username: newUsername,
                        password: newPassword,
                        role: newRole
                    })
                });
                if (response.ok) {
                    addUserScreen.classList.add("infoScreenPopupHidden");
                    await fetchAllUsers();
                    await showInfoScreen("User created successfully.", true);
                    usernameInput.value = "";
                    passwordInput.value = "";
                    roleSelect.value = "user";

                } else {
                    const data = await response.json();
                    await showInfoScreen(data.detail, false);
                }
            } catch (error) {
                console.error("Error creating user:", error);
                await showInfoScreen("Error creating user. Please try again.", false);
            }
        }
    });
});

function validatePassword(password){
    const pwMinLength = 8;
    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasNumber = /[0-9]/.test(password);

    return password.length >= pwMinLength && hasUpperCase && hasLowerCase && hasNumber;
}

function validateUsername(username){
    const usernameMinLength = 4;
    const usernameMaxLength = 16; 
    return username.length >= usernameMinLength && username.length <= usernameMaxLength;
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

function validateIPaddress(ipaddress) {
    return /^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/.test(ipaddress);
}

function validatePort(port) {
    return /^(6553[0-5]|655[0-2][0-9]|65[0-4][0-9]{2}|6[0-4][0-9]{3}|[1-5]?[0-9]{1,4})$/.test(port);
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

document.addEventListener("keydown", async (event) => {
    if (event.key === "Escape") {
        const deletUserScreen = document.getElementById("deleteUserScreen");
        deletUserScreen.classList.add("infoScreenPopup");
    }
});

fetchAllUsers();
