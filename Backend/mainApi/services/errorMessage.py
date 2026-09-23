class errorMessage:
    def __init__(self):
        self.usernameRequirementNotFulfilled = "Username requirement not fulfilled."
        self.passwordRequirementNotFulfilled = "Password requirement not fulfilled."
        self.invalidUsernameOrPassword = "Invalid username or password."
        self.userAlreadyExists = "User already exists."
        self.registrationFailed = "Registration failed. Try again later."
        self.registrationDisabled = "Registration is disabled."
        self.loginFailed = "Login failed. Try again later."
        self.alreadyLoggedIn = "Already logged in."
        self.noActiveSession = "No active session found. Please log in."
        self.invalidSession = "Session is invalid or expired."
        self.sshConnectExists = "SSH is already connected."
        self.configurationAlreadyExists = "This configuration already exists"
        self.sshNotConfigured = "SSH is not configured"
        self.sshNotReachable = "SSH is not reachable."
        self.sshConnectionFailed = "SSH connection failed."
        self.sshConfigSaveFailed = "The SSH configuration could not be saved."
        self.sshConfigFailed = "The SSH configuration could not be processed"
        self.__websockerInvalidSession= "Your session is invalid or has expired. Please log in again."
        self.serverStatusUnavailable = "The server status could not be retrieved."
        self.serverStatsUnavailable = "The server statistics could not be retrieved."
        self.serverStartStopFailed = "Operation Server start/stop failed."
        self.serverRestartFailed = "Operation Server restart failed."
        self.serverDataUnavailable = "The Server information could not be retrieved."
        self.serverCommandFailed = "The server command could not be executed."
        self.noPermission = "You do not have permission to perform this action."
        self.logoutAllSuccess = "Succesfully has been logged out from all sessions."
        self.userDeletionError = "The user could not be deleted. Please try again later."
        self.invalidPassword = "The password you entered is invalid. Please try again."
        self.userRoleUpdateError = "The user role could not be updated. Please try again later."
        self.rconError = "The RCON connection could not be established. Please check your configuration."
        self.invalidIp = "IP Adress is Invalid."
        self.invalidSshPort = "SSH Port is invalid."
        self.invalidRconPort = "RCON Port is invalid."
        self.noServerConfigured = "noServerConfogured."
        self.internalServerError ="Internal Server Error."
        self.nothingToUpdate = "No server found to update."
        
    async def validateIp(self, ip):
        parts = ip.split(".")
        
        if len(parts) != 4:
            return False

        for part in parts:
            if not part.isdigit():
                return False

            number = int(part)

            if number < 0 or number > 255:
                return False

        return True
    
    async def validatePort(self, port):
        try:
            port = int(port)
            return 1 <= port <= 65535
        except (ValueError, TypeError):
            return False
        