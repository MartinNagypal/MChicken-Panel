from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Response, Cookie, Request
from fastapi.middleware.cors import CORSMiddleware
from services.ssh import SSH
from services.rcon import RCON
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
import asyncio
from pydantic import BaseModel
import models.models as models
from collections import deque
from services.sqlite import SQLITE
from services.encryption import Encryption
from services.auth import AUTH
from services.server import SERVER
from services.logWatcher import LogWatcher
from services.errorMessage import errorMessage

from routes.auth import router as routerAuth 
from routes.user import router as routerUser
from routes.server import router as routerServer

load_dotenv()
ip = os.getenv("SSH_IP")
rconPort = os.getenv("RCON_PORT")
rconPassword = os.getenv("RCON_PASSWORD")
allowRegistration = os.getenv("ALLOW_REGISTRATION", "").lower() == "true"

dockerContainerName = "create"
serverDirectory = "/mnt/serverData/mcDomiCreate/"
serverFilesDirectory = "/mnt/serverData/mcDomiCreate/data/"
dockerComposeFile = "docker-compose.yaml"

server = SERVER(dockerContainerName, serverDirectory, serverFilesDirectory, dockerComposeFile, ip, rconPort, rconPassword, allowRegistration)

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

logWatcher = LogWatcher()

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
        try:
            ssh = SSH(result[1], result[2], result[3], encryption.decryptSecret(result[4]))
            await asyncio.wait_for(ssh.connect(), timeout=3)
            app.state.ssh = ssh
            rcon = await RCON.create(result[1], rconPort, ssh, serverFilesDirectory)
            app.state.rcon = rcon
            
        except (asyncio.TimeoutError, TimeoutError):
            print(f"SSH not available")
            app.state.ssh = None
            app.state.rcon = None

        except Exception as e:
            print(f"Startup connection error: {type(e).__name__}: {e}")
            app.state.ssh = None
            app.state.rcon = None

        await logWatcher.start(app)
        
    
    yield
    await logWatcher.stop()
    

secureCookie = False

app = FastAPI(lifespan=lifespan)
app.include_router(routerAuth)
app.include_router(routerUser)
app.include_router(routerServer)
app.state.sql = sql
app.state.auth = auth
app.state.encryption = encryption
app.state.error = error
app.state.ssh = ssh
app.state.rcon = rcon
app.state.secureCookie = secureCookie
app.state.allowRegistration = allowRegistration
app.state.server = server
app.state.logWatcher = logWatcher
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