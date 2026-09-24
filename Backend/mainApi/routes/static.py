from fastapi import FastAPI, APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Response, Cookie, Request
import models.models as models

from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


router = APIRouter(tags=["Static"])

@router.get("/")
async def index(request: Request):
    PAGES_DIR = request.app.state.pagesDir
    return FileResponse(PAGES_DIR / "index.html")

@router.get("/dashboard")
async def dashboard(request: Request):
    PAGES_DIR = request.app.state.pagesDir
    return FileResponse(PAGES_DIR / "index.html")

@router.get("/auth")
async def login_page(request: Request):
    PAGES_DIR = request.app.state.pagesDir
    return FileResponse(PAGES_DIR / "auth.html")

@router.get("/settings")
async def settings_page(request: Request):
    PAGES_DIR = request.app.state.pagesDir
    return FileResponse(PAGES_DIR / "settings.html")

@router.get("/console")
async def console_page(request: Request):
    PAGES_DIR = request.app.state.pagesDir
    return FileResponse(PAGES_DIR / "console.html")

@router.get("/backups")
async def backups_page(request: Request):
    PAGES_DIR = request.app.state.pagesDir
    return FileResponse(PAGES_DIR / "backups.html")