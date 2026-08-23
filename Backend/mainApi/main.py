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

load_dotenv()
ip = os.getenv("SSH_IP")
rconPort = os.getenv("RCON_PORT")
rconPassword = os.getenv("RCON_PASSWORD")
allowRegistration = os.getenv("ALLOW_REGISTRATION")

dockerContainerName = "create"
serverDirectory = "/mnt/serverData/mcDomiCreate/"
serverFilesDirectory = "/mnt/serverData/mcDomiCreate/data/"
dockerComposeFile = "docker-compose.yaml"

sql = SQLITE()
encryption_key = os.getenv("ENCRYPTION_KEY").encode()
encryption = Encryption(encryption_key)
auth = AUTH(sql, encryption)

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
        result = await auth.register(user.username, user.password)
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
                "status_code": 200,
                "message": result.get("message"),
            }
        else:
            raise HTTPException(status_code=500, detail="Registration failed.")
    else:
        raise HTTPException(status_code=403, detail="Registration is disabled.")

@app.post("/login")
async def login(user: models.userInput, request: Request, response: Response):
    
    #check if user is logged in
    currentSessionToken = request.cookies.get("sessionToken")
    if currentSessionToken:
        raise HTTPException(status_code=409, detail="Already logged in.")
    
    #attempt login
    result = await auth.login(user.username, user.password)
    if result.get("error"):
        if result.get("statusCode") == 401:
            raise HTTPException(status_code=401, detail="Invalid username or password.")
        else:
            raise HTTPException(status_code=500, detail="Server error during login.")
        
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
            "status_code": 200,
            "message": result.get("message"),
        }
    else:
        raise HTTPException(status_code=500, detail="Server error during login.")

@app.get("/verifySession")
async def verifySession(request: Request):
    currentSessionToken = request.cookies.get("sessionToken")
    if not currentSessionToken:
        raise HTTPException(status_code=401, detail="No running session found.")
    
    isValid = await auth.verifySession(currentSessionToken)
    if isValid.get("valid")== True:
        return{"status_code": 200, "valid": True}
    else:
        raise HTTPException(status_code=401, detail="Invalid session token.")
    
@app.post("/logout")
async def logout(request: Request, response: Response):
    currentSessionToken = request.cookies.get("sessionToken")
    if not currentSessionToken:
        raise HTTPException(status_code=401, detail="No running session found.")   
    
    result = await auth.logout(currentSessionToken)
    response.delete_cookie("sessionToken", path="/")
    return {"status_code": 200, "message": result.get("message")}


#server endpoints
@app.get("/status")
async def status(request: Request):
    currentSessionToken = request.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    if isValidSession == True:
        if(ssh is None):
            raise HTTPException(status_code=500, detail="SSH not configured")
        try:
            result = await ssh.run(f'docker ps | grep {dockerContainerName}')
            if 'healthy' in result.stdout:
                return {"status": "healthy", "status_code": 200}
            elif 'starting' in result.stdout:
                return {"status": "starting", "status_code": 200}
            elif 'unhealthy' in result.stdout:
                return {"status": "unhealthy", "status_code": 200}
            else:
                return {"status": "offline", "status_code": 200}
            
        except Exception as e:
            print(f"Error fetching server status: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed fetching server status.")
    else:
        raise HTTPException(status_code=401, detail="Invalid session token.")
    
@app.get("/stats")
async def stats(request: Request):
    currentSessionToken = request.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    if isValidSession == True:
        if(ssh is None):
            raise HTTPException(status_code=500, detail="SSH not configured")
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
                'uptime': uptime,
                'status_code': 200
            }
            
        except Exception as e:
            print(f"Error fetching server stats: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed fetching server stats.")
        
    else:
        raise HTTPException(status_code=401, detail="Invalid session token.")

@app.get("/server/startstop")
async def serverStartStop(request: Request):
    currentSessionToken = request.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    if isValidSession == True:
        if(ssh is None):
            raise HTTPException(status_code=500, detail="SSH not configured")
        try:
            status = await ssh.run(f'docker ps | grep {dockerContainerName}')
            if 'healthy' in status.stdout:
                await ssh.runInDir(serverDirectory, f'docker stop {dockerContainerName}')
                return {"message": "Server stop command executed successfully.", "status_code": 200}
            else:
                await ssh.runInDir(serverDirectory, f'docker start {dockerContainerName}')
                return {"message": "Server start command executed successfully.", "status_code": 200}
        except Exception as e:
            raise HTTPException(status_code=500, detail="Operation =server-startstop= failed.")
    else:
        raise HTTPException(status_code=401, detail="Invalid session token.")

@app.get("/server/restart")
async def serverRestart(request: Request):
    currentSessionToken = request.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    if isValidSession == True:
        if(ssh is None):
            raise HTTPException(status_code=500, detail="SSH not configured")
        try:
            await ssh.runInDir(serverDirectory, f'docker restart {dockerContainerName}')
            return {"message": "Server restart command executed successfully.", "status_code": 200}
        except Exception as e:
            raise HTTPException(status_code=500, detail="Operation =server-restart= failed.")
    else:
        raise HTTPException(status_code=401, detail="Invalid session token.") 

@app.get("/server/data")
async def serverData(request: Request):
    currentSessionToken = request.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    if isValidSession == True:
        if(ssh is None):
            return {"status": "not configured"}
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
            raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(status_code=401, detail="Invalid session token.")
    
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
            raise HTTPException(status_code=500, detail="SSH not configured")
        try:
            await rcon.updateRconPassword()
            response = await rcon.run(command.command)
            logBuffer.append(response)
            return {"response": response, "status_code": 200}
        
        except Exception as e:
            raise HTTPException(status_code=500, detail="Failed sending command to server.")
    else:
        raise HTTPException(status_code=401, detail="Invalid session token.")
    
@app.post("/server/sshConfig")
async def sshConfig(sshConfig: models.sshConfig, request: Request):
    currentSessionToken = request.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    if isValidSession == True:
        try:
            testSSH = SSH(sshConfig.ip, sshConfig.port, sshConfig.username, sshConfig.password)
            try:
                await testSSH.connect()
                await testSSH.close()
                result = await sql.fetchone("SELECT * FROM server WHERE ip = ? AND port = ?", (sshConfig.ip, sshConfig.port))
                if result:
                    await sql.execute("UPDATE server SET username = ?, password = ? WHERE ip = ? AND port = ?", (sshConfig.username, encryption.encryptSecret(sshConfig.password), sshConfig.ip, sshConfig.port))
                else:
                    try:
                        await sql.execute("INSERT INTO server (ip, port, username, password) VALUES (?, ?, ?, ?)", (sshConfig.ip, sshConfig.port, sshConfig.username, encryption.encryptSecret(sshConfig.password)))
                        global ssh, rcon
                        ssh = SSH(sshConfig.ip, sshConfig.port, sshConfig.username, sshConfig.password)
                        await ssh.connect()
                        rcon = await RCON.create(sshConfig.ip, rconPort, ssh, serverFilesDirectory)
                        await restartLogWatcher()
                        raise HTTPException(status_code=200, detail="SSH configuration saved and connected successfully.")
                    except Exception as e:
                        print(f"Error saving SSH configuration: {str(e)}")
                        raise HTTPException(status_code=500, detail="Failed to save SSH configuration.")
                        
            except Exception as e:
                print(f"Error connecting to SSH server: {str(e)}")
                raise HTTPException(status_code=400, detail="Failed to connect to SSH server. Please check your credentials and try again.")
            
        except Exception as e:
            print(f"Error during SSH configuration: {str(e)}")
            raise HTTPException(status_code=500, detail="SSH configuration failed.")
    else:
        raise HTTPException(status_code=401, detail="Invalid session token.")