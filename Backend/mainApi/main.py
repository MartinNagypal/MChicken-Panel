from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
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

load_dotenv()
ip = os.getenv("SSH_IP")
port = os.getenv("SSH_PORT")
username = os.getenv("SSH_USER")
password = os.getenv("SSH_PASSWORD")
rconPort = os.getenv("RCON_PORT")
rconPassword = os.getenv("RCON_PASSWORD")

dockerContainerName = "create"
serverDirectory = "/mnt/serverData/mcDomiCreate/"
serverFilesDirectory = "/mnt/serverData/mcDomiCreate/data/"
dockerComposeFile = "docker-compose.yaml"

sql = SQLITE()

#ssh = SSH(ip, port, username, password)
rcon: RCON | None = None
ssh: SSH | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    #connections
    global rcon, ssh
    await sql.connect()
    rcon = await RCON.create(ip, rconPort, ssh, serverFilesDirectory)
    logTask = asyncio.create_task(watchLogs())
    
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
    
    await sql.execute("""
        CREATE TABLE IF NOT EXISTS systemUser(
            userId INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)
    
    result = await sql.fetchone("SELECT * FROM server")
    if result:
        ssh = SSH(result[1], result[2], result[3], result[4])
        await ssh.connect()
    
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
connectedClients: set[WebSocket] = set()
logBuffer = deque(maxlen=200)

@app.get("/status")
async def status():
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
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/stats")
async def stats():
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
        raise HTTPException(status_code=500, detail={
            "error": "Error fetching server stats",
            "details": str(e),
            "errorCode": 500
        })

@app.get("/server/startstop")
async def serverStartStop():
    try:
        status = await ssh.run(f'docker ps | grep {dockerContainerName}')
        if 'healthy' in status.stdout:
            await ssh.runInDir(serverDirectory, f'docker stop {dockerContainerName}')
            return {"message": "Server stop command executed successfully."}
        else:
            await ssh.runInDir(serverDirectory, f'docker start {dockerContainerName}')
            return {"message": "Server start command executed successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/server/restart")
async def serverRestart():
    try:
        await ssh.runInDir(serverDirectory, f'docker restart {dockerContainerName}')
        return {"message": "Server restart command executed successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 

@app.get("/server/data")
async def serverData():
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
    
@app.websocket("/server/logs")
async def serverLogs(websocket: WebSocket):
    await websocket.accept()
    for line in logBuffer:
        await websocket.send_text(line)
    connectedClients.add(websocket)
    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        connectedClients.discard(websocket)
        
async def watchLogs():
    async for line in ssh.stream(
        f"tail -n 150 -F {serverFilesDirectory}logs/latest.log"
    ):
        if line:
            logBuffer.append(line)
            for websocket in connectedClients.copy():
                await websocket.send_text(line)
                
@app.post("/server/sendCommand")
async def sendCommand(command:models.commandInput):
    try:
        await rcon.updateRconPassword()
        response = await rcon.run(command.command)
        logBuffer.append(response)
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/server/sshConfig")
async def sshConfig(sshConfig: models.sshConfig):
    try:
        testSSH = SSH(sshConfig.ip, sshConfig.port, sshConfig.username, sshConfig.password)
        try:
            await testSSH.connect()
            await testSSH.close()
            result = await sql.fetchone("SELECT * FROM server WHERE ip = ? AND port = ?", (sshConfig.ip, sshConfig.port))
            if result:
                await sql.execute("UPDATE server SET username = ?, password = ? WHERE ip = ? AND port = ?", (sshConfig.username, sshConfig.password, sshConfig.ip, sshConfig.port))
            else:
                await sql.execute("INSERT INTO server (ip, port, username, password) VALUES (?, ?, ?, ?)", (sshConfig.ip, sshConfig.port, sshConfig.username, sshConfig.password))
                return {"message": "SSH configuration saved successfully."}
        except Exception as e:
            return {"error": f"Failed to connect to SSH server: {str(e)}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))