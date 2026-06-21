"""
SignAI — FastAPI backend

Endpoints:
  POST /process          — process a video URL
  POST /process/upload   — upload a video file and process it
  GET  /dictionary/stats — dictionary coverage stats
  GET  /health           — health check
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
import dictionary as dict_
from pipeline import process_video

load_dotenv()

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
outputs_path = os.path.join(frontend_path, "outputs")
os.makedirs(outputs_path, exist_ok=True)

if os.path.exists(frontend_path):
    app.mount("/outputs", StaticFiles(directory=outputs_path), name="outputs")
    app.mount("/app", StaticFiles(directory=frontend_path, html=True), name="frontend")


class ProcessRequest(BaseModel):
    video_url: str
    pip_position: str = "bottom-right"
    transcript: str | None = None


@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/dictionary/stats")
def dictionary_stats():
    return dict_.stats()

@app.post("/process")
def process_url(req: ProcessRequest):
    try:
        return process_video(req.video_url, req.pip_position, req.transcript or None)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process/upload")
def process_upload(
    file: UploadFile = File(...),
    pip_position: str = "bottom-right",
    transcript: str | None = Form(None),
):
    try:
        file_bytes = file.file.read()
        return process_video(
            video_url="",
            pip_position=pip_position,
            transcript_override=transcript or None,
            video_bytes=file_bytes,
            video_filename=file.filename or "upload.mp4",
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
