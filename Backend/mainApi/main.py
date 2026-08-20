from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from services.ssh import SSH
from services.rcon import RCON
import os
from dotenv import load_dotenv
from datetime import datetime, timezone
import re

load_dotenv()
app = FastAPI()
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

ip = os.getenv("SSH_IP")
port = os.getenv("SSH_PORT")
username = os.getenv("SSH_USER")
password = os.getenv("SSH_PASSWORD")
rconPort = os.getenv("RCON_PORT")
rconPassword = os.getenv("RCON_PASSWORD")

ssh = SSH(ip, port, username, password)
rcon = RCON(ip, rconPort, rconPassword)

dockerContainerName = "create"

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
        playerCount = await rcon.run("list")
        playerCountRegex = re.search(r"There are (\d+) of a max of (\d+) players online:", playerCount)
        if playerCountRegex:
            currentPlayers = int(playerCountRegex.group(1))
            maxPlayers = int(playerCountRegex.group(2))

        cpuUsage = await ssh.run(f'docker stats {dockerContainerName} --no-stream --format "{{{{.CPUPerc}}}}"')
        memUsage = await ssh.run(f'docker stats {dockerContainerName} --no-stream --format "{{{{.MemUsage}}}}"')
        
        return {
            "currentPlayers": currentPlayers,
            "maxPlayers": maxPlayers,
            "cpuUsage": cpuUsage.stdout.strip(),
            "memUsage": memUsage.stdout.strip(),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

