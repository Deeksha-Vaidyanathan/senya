"""
SignAI — FastAPI backend

All Pika calls go through the claude CLI using the locally authenticated
Pika MCP — no API key required. Runs locally only.

Endpoints:
  POST /process          — process a video URL
  POST /process/upload   — upload a video file and process it
  GET  /dictionary/stats — dictionary coverage stats
  GET  /health           — health check
"""

import os
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
import dictionary as dict_
from pipeline import process_video
import pika_client as pika

load_dotenv()

executor = ThreadPoolExecutor(max_workers=2)

@asynccontextmanager
async def lifespan(app: FastAPI):
    dict_.load()
    yield

app = FastAPI(title="SignAI", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/app", StaticFiles(directory=frontend_path, html=True), name="frontend")


class ProcessRequest(BaseModel):
    video_url: str
    pip_position: str = "bottom-right"


@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/dictionary/stats")
def dictionary_stats():
    return dict_.stats()

@app.post("/process")
def process_url(req: ProcessRequest):
    try:
        return process_video(req.video_url, req.pip_position)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process/upload")
def process_upload(file: UploadFile = File(...), pip_position: str = "bottom-right"):
    try:
        file_bytes = file.file.read()
        video_url = pika.upload_asset(file_bytes, file.filename or "upload.mp4")
        return process_video(video_url, pip_position)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
