from fastapi import FastAPI, HTTPException
from Backend/mainApi/services.py import SSHManager

app = FastAPI()
ssh_manager = SSHManager(
    host="localhost",
    port=22,
    username="user",
    password="password"
)

@app.get("/")
def root():
    return {"message": "Hello, World!"}
