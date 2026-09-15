from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Response, Cookie, Request
from fastapi.middleware.cors import CORSMiddleware
from services.ssh import SSH
from services.rcon import RCON
import os
from dotenv import load_dotenv
import re
from contextlib import asynccontextmanager
import asyncio
from pydantic import BaseModel
import models.models as models
from collections import deque
from services.sqlite import SQLITE
from services.encryption import Encryption
from services.auth import AUTH
from services.errorMessage import errorMessage

load_dotenv()
ip = os.getenv("SSH_IP")
rconPort = os.getenv("RCON_PORT")
rconPassword = os.getenv("RCON_PASSWORD")
allowRegistration = os.getenv("ALLOW_REGISTRATION", "").lower() == "true"

dockerContainerName = "create"
serverDirectory = "/mnt/serverData/mcDomiCreate/"
serverFilesDirectory = "/mnt/serverData/mcDomiCreate/data/"
dockerComposeFile = "docker-compose.yaml"

sql = SQLITE()
encryptionKey = os.getenv("ENCRYPTION_KEY").encode()
if not encryptionKey:
    raise RuntimeError("ENCRYPTION_KEY fehlt.")
encryption = Encryption(encryptionKey)
auth = AUTH(sql, encryption)
error = errorMessage()

rcon: RCON | None = None
ssh: SSH | None = None
logTask: asyncio.Task | None = None
logTaskLock = asyncio.Lock()

@asynccontextmanager
async def lifespan(app: FastAPI):
    #connections
    global rcon, ssh
    await sql.connect()
    
    #db management
    await sql.execute("""
        CREATE TABLE IF NOT EXISTS server(
            serverId INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT NOT NULL,
            port INTEGER NOT NULL,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)
    
    result = await sql.fetchone("SELECT * FROM server")
    if result:
        ssh = SSH(result[1], result[2], result[3], encryption.decryptSecret(result[4]))
        await ssh.connect()
        rcon = await RCON.create(ip, rconPort, ssh, serverFilesDirectory)
        await startLogWatcher()
        
    
    yield
    logTask.cancel()
    try:
        await logTask
    except asyncio.CancelledError:
        pass
    

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

secureCookie = False

connectedClients: set[WebSocket] = set()
logBuffer = deque(maxlen=200)

#auth endpoints
@app.post("/register")
async def register(user: models.userInput, response: Response):
    #check if its first user
    isFirstUser = await auth.isFirstUser()
    
    #if its first user or registration is allowed -> continue
    if isFirstUser == True or allowRegistration == True:
        if isFirstUser:
            role = "admin"
        else:
            role = "user"
            
        isUsernameValid = await auth.validateUsername(user.username)
        if isUsernameValid.get("valid") == False:
            raise HTTPException(status_code=400, detail=error.usernameRequirementNotFulfilled)
            
        isPasswordValid = await auth.validatePassword(user.password)
        if isPasswordValid.get("valid") == False:
            raise HTTPException(status_code=400, detail=error.passwordRequirementNotFulfilled)
        
        result = await auth.register(user.username, user.password, role)
        #if resgistration was successful -> set cookie and return message
        if result.get("message"):
            sessionToken = result.get("sessionToken")
            sessionExpirationHours = result.get("sessionExpirationHours")
            response.set_cookie(
                key="sessionToken",
                value=sessionToken,
                httponly=True,
                secure=secureCookie,
                samesite="lax",
                max_age=sessionExpirationHours * 3600,
                path="/",
            )
            return {
                "message": result.get("message"),
            }
        else:
            if(result.get("error") == "1"):
                raise HTTPException(status_code=409, detail=error.userAlreadyExists)
            else:
                raise HTTPException(status_code=500, detail=error.registrationFailed)
    else:
        raise HTTPException(status_code=403, detail=error.registrationDisabled)

@app.post("/login")
async def login(user: models.userInput, request: Request, response: Response):
    
    #check if user is logged in
    currentSessionToken = request.cookies.get("sessionToken")
    if currentSessionToken:
        isValidSession = await auth.verifySession(currentSessionToken)
        isValidSession = isValidSession.get("valid")
        if isValidSession == True:
            raise HTTPException(status_code=409, detail=error.alreadyLoggedIn)
        else:
            response.delete_cookie("sessionToken", path="/")
    
    #attempt login
    result = await auth.login(user.username, user.password)
    if result.get("error"):
        if result.get("statusCode") == 401:
            raise HTTPException(status_code=401, detail=error.invalidUsernameOrPassword)
        else:
            raise HTTPException(status_code=500, detail=error.loginFailed)
        
    #generate session
    sessionToken = result.get("sessionToken")
    if sessionToken:
        sessionExpirationHours = result.get("sessionExpirationHours")
        response.set_cookie(
            key="sessionToken",
            value=sessionToken,
            httponly=True,
            secure=secureCookie,
            samesite="lax",
            max_age=sessionExpirationHours * 3600,
            path="/",
        )
        return {
            "message": result.get("message"),
        }
    else:
        raise HTTPException(status_code=500, detail=error.loginFailed)

@app.get("/verifySession")
async def verifySession(request: Request):
    currentSessionToken = request.cookies.get("sessionToken")
    if not currentSessionToken:
        raise HTTPException(status_code=401, detail=error.noActiveSession)
    
    isValid = await auth.verifySession(currentSessionToken)
    if isValid.get("valid")== True:
        return{"valid": True}
    else:
        raise HTTPException(status_code=401, detail=error.invalidSession)
    
@app.post("/logout")
async def logout(request: Request, response: Response):
    currentSessionToken = request.cookies.get("sessionToken")
    if not currentSessionToken:
        raise HTTPException(status_code=401, detail=error.noActiveSession)   
    
    result = await auth.logout(currentSessionToken)
    response.delete_cookie("sessionToken", path="/")
    return {"message": result.get("message")}

@app.post("/logout/all")
async def logoutAll(request: Request, response: Response):
    currentSessionToken = request.cookies.get("sessionToken")
    if not currentSessionToken:
        raise HTTPException(status_code=401, detail=error.noActiveSession)   
    
    isValid = await auth.verifySession(currentSessionToken)
    if isValid.get("valid")== True:
        username = isValid.get("username")
        result = await auth.logoutAllSessions(username)
        response.delete_cookie("sessionToken", path="/")
        return {"message": error.logoutAllSuccess}
    else:
        raise HTTPException(status_code=401, detail=error.invalidSession)

@app.get("/users")
async def getUsers(request: Request):
    currentSessionToken = request.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    if isValidSession == True:
        role = await auth.getUserRole(currentSessionToken)
        role = role.get("role")
        if role != "admin":
            raise HTTPException(status_code=403, detail=error.noPermission)
        
        users = await auth.getAllUsers()
        return {"users": users}
    else:
        raise HTTPException(status_code=401, detail=error.invalidSession)

@app.get("session/count")
async def sessionCount(request: Request, response: Response):
    currentSessionToken = request.cookies.get("sessionToken")
    if not currentSessionToken:
        raise HTTPException(status_code=401, detail=error.noActiveSession)
    
    isValid = await auth.verifySession(currentSessionToken)
    if isValid.get("valid") == True:
        username = isValid.get("username")
        result = await auth.countSessions(username)
        print(result)
        
    else:
        raise HTTPException(status_code=401, detail=error.invalidSession)
    
    
@app.post("/user/verifyPassword")
async def verifyPassword(password: models.password, request: Request, response: Response):
    currentSessionToken = request.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    if isValidSession == True:
        username = await auth.getUsernameBySession(currentSessionToken)
        username = username.get("username")
        result = await auth.verifyPassword(username, password.password)
        if result.get("valid") == True:
            return {"valid": True}
        else:
            raise HTTPException(status_code=401, detail=error.invalidPassword)
    else:
        raise HTTPException(status_code=401, detail=error.invalidSession)
    
@app.post("/user/delete")
async def deleteUser(username: models.username, request: Request, response: Response):
    currentSessionToken = request.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    if isValidSession == True:
        currentUsername = await auth.getUsernameBySession(currentSessionToken)
        currentUsername = currentUsername.get("username")
        if currentUsername == username.username:
            raise HTTPException(status_code=403, detail="You cannot delete your own account.")
        role = await auth.getUserRole(currentSessionToken)
        role = role.get("role")
        if role != "admin":
            raise HTTPException(status_code=403, detail=error.noPermission)
        
        result = await auth.deleteUser(username.username)
        if result.get("error"):
            raise HTTPException(status_code=500, detail=error.userDeletionError)
        else:
            return {"message": result.get("message")}
        
@app.get("/user/role/session")
async def getUserRole(request: Request, response: Response):
    currentSessionToken = request.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    if isValidSession == True:
        username = await auth.getUsernameBySession(currentSessionToken)
        username = username.get("username")
        role = await auth.getUserRoleByUsername(username)
        role = role.get("role")
        return{"role": role}
    else:
        raise HTTPException(status_code=401, detail=error.invalidSession)

        
    
    

#server endpoints
@app.get("/status")
async def status(request: Request):
    currentSessionToken = request.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    if isValidSession == True:
        if(ssh is None):
            raise HTTPException(status_code=500, detail=error.sshNotConfigured)
        try:
            result = await ssh.run(f'docker ps | grep {dockerContainerName}')
            if 'healthy' in result.stdout:
                return {"status": "healthy"}
            elif 'starting' in result.stdout:
                return {"status": "starting"}
            elif 'unhealthy' in result.stdout:
                return {"status": "unhealthy"}
            else:
                return {"status": "offline"}
            
        except Exception as e:
            print(f"Error fetching server status: {str(e)}")
            raise HTTPException(status_code=500, detail=error.serverStatusUnavailable)
    else:
        raise HTTPException(status_code=401, detail=error.invalidSession)

@app.get("/stats")
async def stats(request: Request):
    currentSessionToken = request.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    if isValidSession == True:
        if(ssh is None):
            raise HTTPException(status_code=500, detail=error.sshNotConfigured)
        try:
            await rcon.updateRconPassword()
            playerCount = await rcon.run("list")
            playerCountRegex = re.search(r"There are (\d+) of a max of (\d+) players online:", playerCount)
            if playerCountRegex:
                currentPlayers = int(playerCountRegex.group(1))
                maxPlayers = int(playerCountRegex.group(2))

            cpuUsage = await ssh.run(f'docker stats {dockerContainerName} --no-stream --format "{{{{.CPUPerc}}}}"')
            memUsage = await ssh.run(f'docker stats {dockerContainerName} --no-stream --format "{{{{.MemUsage}}}}"')
            currentMemUsage = memUsage.stdout.strip().split("/")[0]
            maxMem = memUsage.stdout.strip().split("/")[1]
            
            uptimeCmd = (
                f"echo $(( ($(date +%s) - "
                f"$(date -d \"$(docker inspect -f '{{{{.State.StartedAt}}}}' {dockerContainerName})\" +%s)) ))"
            )
            
            uptimeResult = await ssh.run(uptimeCmd)
            uptimeSeconds = int(uptimeResult.stdout.strip())
            uptimeHours, uptimeRemainder = divmod(uptimeSeconds, 3600)
            uptimeMinutes = uptimeRemainder // 60
            uptime = f"{uptimeHours:02d}:{uptimeMinutes:02d}"
            

            return {
                "currentPlayers": currentPlayers,
                "maxPlayers": maxPlayers,
                "cpuUsage": cpuUsage.stdout.strip(),
                "currentMemUsage": currentMemUsage,
                "maxMem": maxMem,
                'uptime': uptime
            }
            
        except Exception as e:
            print(f"Error fetching server stats: {str(e)}")
            raise HTTPException(status_code=500, detail=error.serverStatsUnavailable)
        
    else:
        raise HTTPException(status_code=401, detail=error.invalidSession)

@app.post("/server/startstop")
async def serverStartStop(request: Request):
    currentSessionToken = request.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    if isValidSession == True:
        if(ssh is None):
            raise HTTPException(status_code=500, detail=error.sshNotConfigured)
        
        role = await auth.getUserRole(currentSessionToken)
        role = role.get("role")
        if role != "admin":
            raise HTTPException(status_code=403, detail=error.noPermission)
        
        try:
            status = await ssh.run(f'docker ps | grep {dockerContainerName}')
            if 'healthy' in status.stdout:
                await ssh.runInDir(serverDirectory, f'docker stop {dockerContainerName}')
                return {"message": "Server stop command executed successfully."}
            else:
                await ssh.runInDir(serverDirectory, f'docker start {dockerContainerName}')
                return {"message": "Server start command executed successfully."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=error.serverStartStopFailed)
    else:
        raise HTTPException(status_code=401, detail=error.invalidSession)

@app.post("/server/restart")
async def serverRestart(request: Request):
    currentSessionToken = request.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    if isValidSession == True:
        if(ssh is None):
            raise HTTPException(status_code=500, detail=error.sshNotConfigured)
        
        role = await auth.getUserRole(currentSessionToken)
        role = role.get("role")
        if role != "admin":
            raise HTTPException(status_code=403, detail=error.noPermission)
        
        try:
            await ssh.runInDir(serverDirectory, f'docker restart {dockerContainerName}')
            return {"message": "Server restart command executed successfully."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=error.serverRestartFailed)
    else:
        raise HTTPException(status_code=401, detail=error.invalidSession)

@app.get("/server/data")
async def serverData(request: Request):
    currentSessionToken = request.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    if isValidSession == True:
        if(ssh is None):
            raise HTTPException(status_code=500, detail=error.sshNotConfigured)
        try:
            serverNameResult = await ssh.runInDir(serverDirectory, f'cat {dockerComposeFile} | grep container_name')
            serverNameMatch = re.search(r"container_name:\s*([a-zA-Z0-9_-]+)", serverNameResult.stdout)
            serverName = serverNameMatch.group(1) if serverNameMatch else "Unknown"
            
            serverVersionResult = await ssh.runInDir(serverDirectory, f'cat {dockerComposeFile} | grep VERSION')
            serverVersionMatch = re.search(r'VERSION:\s*"([^"]+)"', serverVersionResult.stdout)
            serverVersion = serverVersionMatch.group(1) if serverVersionMatch else "Unknown"
            
            return {
                "serverName": serverName,
                "serverVersion": serverVersion,
                "ip": await ssh.getIp()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=error.serverDataUnavailable)
    else:
        raise HTTPException(status_code=401, detail=error.invalidSession)

@app.websocket("/server/logs")
async def serverLogs(websocket: WebSocket):
    currentSessionToken = websocket.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    if isValidSession == True:
        await websocket.accept()
        if(ssh is None):
            await websocket.send_text("SSH not configured")
            return
        
        for line in logBuffer:
            await websocket.send_text(line)
        connectedClients.add(websocket)
        try:
            while True:
                await websocket.receive_text()

        except WebSocketDisconnect:
            connectedClients.discard(websocket)
    else:
        await websocket.accept()
        await websocket.send_text("Invalid session token")
        await websocket.close()
        
async def watchLogs():
    if(ssh is None):
        return
    async for line in ssh.stream(
        f"tail -n 150 -F {serverFilesDirectory}logs/latest.log"
    ):
        if line:
            logBuffer.append(line)
            for websocket in connectedClients.copy():
                await websocket.send_text(line)
   
async def stopLogWatcher():
    global logTask
    if logTask is None:
        return
    logTask.cancel()
    try:
        await logTask
    except asyncio.CancelledError:
        pass
    finally:
        logTask = None
    
async def startLogWatcher():
    global logTask
    if ssh is None:
        return
    if logTask is None or logTask.done():
        logTask = asyncio.create_task(watchLogs())
        
async def restartLogWatcher():
    async with logTaskLock:
        await stopLogWatcher()
        await startLogWatcher()
                
@app.post("/server/sendCommand")
async def sendCommand(command:models.commandInput, request: Request):
    currentSessionToken = request.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    if isValidSession == True:
        if(ssh is None):
            raise HTTPException(status_code=500, detail=error.sshNotConfigured)
        
        role = await auth.getUserRole(currentSessionToken)
        role = role.get("role")
        if role != "admin":
            raise HTTPException(status_code=403, detail=error.noPermission)

        try:
            await rcon.updateRconPassword()
            response = await rcon.run(command.command)
            logBuffer.append(response)
            return {"response": response}
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=error.serverCommandFailed)
    else:
        raise HTTPException(status_code=401, detail=error.invalidSession)

@app.post("/server/sshConfig")
async def sshConfig(sshConfig: models.sshConfig, request: Request):
    currentSessionToken = request.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    if isValidSession == True:
        
        role = await auth.getUserRole(currentSessionToken)
        role = role.get("role")
        if role != "admin":
            raise HTTPException(status_code=403, detail=error.noPermission)
        
        try:
            testSSH = SSH(sshConfig.ip, sshConfig.port, sshConfig.username, sshConfig.password)
            try:
                await testSSH.connect()
                await testSSH.close()
                result = await sql.fetchone("SELECT * FROM server WHERE ip = ? AND port = ?", (sshConfig.ip, sshConfig.port))
                if result:
                    await sql.execute("UPDATE server SET username = ?, password = ? WHERE ip = ? AND port = ?", (sshConfig.username, encryption.encryptSecret(sshConfig.password), sshConfig.ip, sshConfig.port))
                    return {"detail": "SSH configuration updated successfully."}
                else:
                    try:
                        await sql.execute("INSERT INTO server (ip, port, username, password) VALUES (?, ?, ?, ?)", (sshConfig.ip, sshConfig.port, sshConfig.username, encryption.encryptSecret(sshConfig.password)))
                        global ssh, rcon
                        ssh = SSH(sshConfig.ip, sshConfig.port, sshConfig.username, sshConfig.password)
                        await ssh.connect()
                        rcon = await RCON.create(sshConfig.ip, rconPort, ssh, serverFilesDirectory)
                        await restartLogWatcher()
                        return {"detail": "SSH configuration saved and connected successfully."}
                    except Exception as e:
                        print(f"Error saving SSH configuration: {str(e)}")
                        raise HTTPException(status_code=500, detail=error.sshConfigSaveFailed)
                        
            except Exception as e:
                print(f"Error connecting to SSH server: {str(e)}")
                raise HTTPException(status_code=400, detail=error.sshConnectFailed)
            
        except Exception as e:
            print(f"Error during SSH configuration: {str(e)}")
            raise HTTPException(status_code=500, detail=error.sshConfigFailed)
    else:
        raise HTTPException(status_code=401, detail=error.invalidSession)

@app.get("/user/username")
async def getUsername(request: Request):
    currentSessionToken = request.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    if isValidSession == True:
        username = await sql.fetchone("SELECT username FROM userSession WHERE sessionToken = ?", (encryption.hashSessionToken(currentSessionToken),))
        return {"username": username}
    else:
        raise HTTPException(status_code=401, detail=error.invalidSession)
    
