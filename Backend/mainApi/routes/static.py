from fastapi import FastAPI, APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Response, Cookie, Request
import models.models as models

from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


router = APIRouter(tags=["Static"])