from fastapi import FastAPI, HTTPException
from ssh import SSH
import os
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

ip = os.getenv("SSH_IP")
port = os.getenv("SSH_PORT")
username = os.getenv("SSH_USER")
password = os.getenv("SSH_PASSWORD")

ssh = SSH(ip, port, username, password)

@app.get("/")
async def root():
    result = await ssh.run("ls -la")
    return {"ssh": result.stdout.strip()}