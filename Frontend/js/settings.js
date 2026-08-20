const sshIp = document.getElementById("sshIp");
const sshPort = document.getElementById("sshPort");
const sshUsername = document.getElementById("sshUsername");
const sshPassword = document.getElementById("sshPassword");
const serverSetupTabSSHSubmit = document.getElementById("serverSetupTabSSHSubmit");

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
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ ip, port, username, password })
        });
        const result = await response.json();
        console.log(result);
    }

    console.log(`SSH IP: ${ip}, Port: ${port}, Username: ${username}, Password: ${password}`);
    // Here you can add the logic to send this data to your backend or perform any other action.
});
