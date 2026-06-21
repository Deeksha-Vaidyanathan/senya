"""
Local video assembly using the bundled ffmpeg binary from imageio_ffmpeg.
Replaces Pika edit_concat and edit_pip — no API required.
"""

import os
import subprocess
import tempfile
import uuid
from pathlib import Path

import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
OUTPUT_DIR = Path(__file__).parent.parent / "frontend" / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _run(cmd: list[str]):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg error: {result.stderr[-600:]}")


TARGET_W = 480
TARGET_H = 480

# Normalize to consistent codec, resolution, fps, and color range.
# setrange=limited converts JPEG full-range (yuvj420p/pc) to standard TV range (yuv420p/tv)
# so all clips have identical pixel format for concat.
_NORMALIZE_VF = (
    f"scale={TARGET_W}:{TARGET_H}:force_original_aspect_ratio=decrease,"
    f"pad={TARGET_W}:{TARGET_H}:(ow-iw)/2:(oh-ih)/2,"
    f"fps=25,format=yuv420p,setrange=limited"
)


def _normalize(clip_path: str) -> str:
    """Re-encode any clip (GIF, JPG, MP4) to a consistent 480x480 h264 yuv420p MP4."""
    ext = Path(clip_path).suffix.lower()
    tmp = tempfile.mktemp(suffix=".mp4")
    base_flags = ["-c:v", "libx264", "-crf", "23", "-pix_fmt", "yuv420p"]
    if ext in (".jpg", ".jpeg", ".png"):
        _run([FFMPEG, "-y", "-loop", "1", "-i", clip_path,
              "-t", "2", "-vf", _NORMALIZE_VF] + base_flags + [tmp])
    else:
        _run([FFMPEG, "-y", "-i", clip_path,
              "-vf", _NORMALIZE_VF] + base_flags + [tmp])
    return tmp


def concat(clip_paths: list[str]) -> str:
    """Concatenate clips into a single MP4. Returns output file path."""
    normalized = [_normalize(p) for p in clip_paths]

    list_file = tempfile.mktemp(suffix=".txt")
    with open(list_file, "w") as f:
        for p in normalized:
            f.write(f"file '{p}'\n")

    output = tempfile.mktemp(suffix=".mp4")
    _run([
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0", "-i", list_file,
        "-c:v", "libx264", "-crf", "23",
        "-r", "25", "-pix_fmt", "yuv420p",
        output,
    ])
    os.unlink(list_file)
    return output


def pip_overlay(base_path: str, overlay_path: str, position: str = "bottom-right") -> str:
    """
    Overlay the signing video (quarter size) onto the base video.
    Returns a /outputs/<filename> URL path served by FastAPI.
    """
    _POSITIONS = {
        "bottom-right": "W-w-10:H-h-10",
        "bottom-left":  "10:H-h-10",
        "top-right":    "W-w-10:10",
        "top-left":     "10:10",
    }
    pos = _POSITIONS.get(position, "W-w-10:H-h-10")

    output_name = f"result_{uuid.uuid4().hex}.mp4"
    output_path = str(OUTPUT_DIR / output_name)

    # Scale overlay to 1/3 of the base video's height, preserving aspect ratio.
    # scale2ref ensures the avatar is consistently sized relative to the base video
    # regardless of the base video's resolution.
    _run([
        FFMPEG, "-y",
        "-i", base_path,
        "-i", overlay_path,
        "-filter_complex",
        f"[1:v][0:v]scale2ref=h=main_h/3:w=-2[ov][base];[base][ov]overlay={pos}:eof_action=pass[v]",
        "-map", "[v]",
        "-map", "0:a?",
        "-c:v", "libx264", "-crf", "23",
        "-c:a", "aac",
        output_path,
    ])
    return f"/outputs/{output_name}"


def download_video(url: str) -> str:
    """Download a video from a direct URL to a temp file. Returns the local path."""
    import requests

    _streaming_sites = ("youtube.com", "youtu.be", "vimeo.com", "tiktok.com", "instagram.com", "twitter.com", "x.com")
    if any(s in url for s in _streaming_sites):
        raise ValueError(
            "Streaming site URLs (YouTube, Vimeo, TikTok, etc.) can't be downloaded directly. "
            "Download the video file to your computer and use the Upload tab instead."
        )

    resp = requests.get(url, timeout=60, stream=True)
    resp.raise_for_status()

    ct = resp.headers.get("content-type", "")
    if "text/html" in ct:
        raise ValueError(
            f"The URL returned an HTML page, not a video file. "
            "Use a direct link ending in .mp4, .mov, or .webm, or upload the file instead."
        )

    ext = ".mp4"
    if "webm" in ct:
        ext = ".webm"
    elif "quicktime" in ct or "mov" in ct:
        ext = ".mov"

    tmp = tempfile.mktemp(suffix=ext)
    with open(tmp, "wb") as f:
        for chunk in resp.iter_content(65536):
            f.write(chunk)
    return tmp
