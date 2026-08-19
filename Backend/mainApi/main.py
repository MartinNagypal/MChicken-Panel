from fastapi import FastAPI, HTTPException
from ssh import SSH
from rcon import RCON
import os
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

ip = os.getenv("SSH_IP")
port = os.getenv("SSH_PORT")
username = os.getenv("SSH_USER")
password = os.getenv("SSH_PASSWORD")
rconPort = os.getenv("RCON_PORT")
rconPassword = os.getenv("RCON_PASSWORD")

ssh = SSH(ip, port, username, password)
rcon = RCON(ip, rconPort, rconPassword)

raw=os.getenv("RCON_PASSWORD")
print(f"DEBUG len={len(raw) if raw else None}, repr={repr(raw)}")

@app.get("/")
async def root():
    result = await rcon.run("list")
    return {"rcon": result}
