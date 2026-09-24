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
from routes.static import router as routerStatic

from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()
allowRegistration = os.getenv("ALLOW_REGISTRATION", "").lower() == "true"
dockerContainerName = "create"
serverDirectory = "/mnt/serverData/mcDomiCreate/"
serverFilesDirectory = "/mnt/serverData/mcDomiCreate/data/"
dockerComposeFile = "docker-compose.yaml"
#root@mc:/mnt/serverData/mc170626

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
            password TEXT NOT NULL,
            rconPort INTEGER NOT NULL,
            containerName TEXT NOT NULL,
            dirToServerData TEXT NOT NULL,
            dirToDC_File TEXT NOT NULL,
            dirToBackups TEXT
        )
    """)
    
    result = await sql.fetchone("SELECT * FROM server")
    if result:
        server = SERVER(result[6], result[8], result[7], app.state.compose, result[1], result[5], app.state.allowRegistration)
        app.state.server = server
        try:
            ssh = SSH(result[1], result[2], result[3], encryption.decryptSecret(result[4]))
            await asyncio.wait_for(ssh.connect(), timeout=3)
            app.state.ssh = ssh
            rcon = await RCON.create(result[1], result[5], ssh, result[7])
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
    if app.state.ssh is not None:
        await app.state.ssh.close()
    await logWatcher.stop()
    

secureCookie = False

app = FastAPI(lifespan=lifespan)
app.include_router(routerAuth)
app.include_router(routerUser)
app.include_router(routerServer)
app.include_router(routerStatic)

app.state.sql = sql
app.state.auth = auth
app.state.encryption = encryption
app.state.error = error
app.state.ssh = ssh
app.state.rcon = rcon
app.state.secureCookie = secureCookie
app.state.allowRegistration = allowRegistration
app.state.logWatcher = logWatcher
app.state.compose = "docker-compose.yaml"
app.state.server = None
app.state.ssh = None
app.state.rcon = None

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "Frontend"
PAGES_DIR = FRONTEND_DIR / "pages"
app.state.projectRoot = PROJECT_ROOT
app.state.frontendDir = FRONTEND_DIR
app.state.pagesDir = PAGES_DIR

app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")
app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8000",
        "http://localhost:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)