const authLoginButton = document.getElementById("authLoginButton");
const authRegisterButton = document.getElementById("authRegisterButton");
const authConfirmButton = document.getElementById("authConfirmButton");


authLoginButton.addEventListener("click", () => {
    const username = document.getElementById("usernameInput").value;
    const password = document.getElementById("passwordInput").value;

    if(username.length < 1){
        document.getElementById("usernameInput").classList.add("authInputError");
    }
    else{
        document.getElementById("usernameInput").classList.remove("authInputError");
        document.getElementById("usernameInput").classList.add("authInputSuccess");
    }

    if(password.length < 1){
        document.getElementById("passwordInput").classList.add("authInputError");
    }
    else{
        document.getElementById("usernameInput").classList.remove("authInputError");
        document.getElementById("passwordInput").classList.add("authInputSuccess");
    }
});

authRegisterButton.addEventListener("click", () => {

    const username = document.getElementById("usernameInput").value;
    const password = document.getElementById("passwordInput").value;
    
    if(username.length < 1){
        document.getElementById("usernameInput").classList.add("authInputError");
    }
    else{
        document.getElementById("usernameInput").classList.remove("authInputError");
        document.getElementById("usernameInput").classList.add("authInputSuccess");
    }

    if(password.length < 1){
        document.getElementById("passwordInput").classList.add("authInputError");
    }
    else{
        document.getElementById("usernameInput").classList.remove("authInputError");
        document.getElementById("passwordInput").classList.add("authInputSuccess");
    }

    if(username.length > 0 && password.length > 0){
        document.getElementById("authLoginButton").classList.add("authButtonHidden");
        document.getElementById("authRegisterButton").classList.add("authButtonHidden");
        document.getElementById("authRegisterForm").classList.add("authRegisterFormActive");
    }
});

authConfirmButton.addEventListener("click", async () => {
    const username = document.getElementById("usernameInput").value;
    const password = document.getElementById("passwordInput").value;
    const confirmPassword = document.getElementById("registerConfirmPasswordInput").value;

    if(username.length < 1){
        document.getElementById("usernameInput").classList.add("authInputError");
    }
    else{
        document.getElementById("usernameInput").classList.remove("authInputError");
        document.getElementById("usernameInput").classList.add("authInputSuccess");
    }

    if(password.length < 1){
        document.getElementById("passwordInput").classList.add("authInputError");
    }
    else{
        document.getElementById("passwordInput").classList.remove("authInputError");
        document.getElementById("passwordInput").classList.add("authInputSuccess");
    }

    if(confirmPassword.length < 1 || confirmPassword !== password){
        document.getElementById("registerConfirmPasswordInput").classList.add("authInputError");
    }
    else{
        document.getElementById("registerConfirmPasswordInput").classList.remove("authInputError");
        document.getElementById("registerConfirmPasswordInput").classList.add("authInputSuccess");
    }

    if(password === confirmPassword){
        document.getElementById("registerConfirmPasswordInput").classList.remove("authInputError");
        document.getElementById("registerConfirmPasswordInput").classList.add("authInputSuccess");
        if(username.length > 0 && password.length > 0){
            result = await fetch("http://127.0.0.1:8000/register", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    username: username,
                    password: password
                })
            });
            const data = await result.json();
            if(data.error){
                document.getElementById("authContainer").classList.add("authContainerRed");
            }
            else{
                document.getElementById("authContainer").classList.add("authContainerGreen");
                console.log(data);
            }
        }
    }
});