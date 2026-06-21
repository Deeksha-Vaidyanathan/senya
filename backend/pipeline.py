"""
Core pipeline: video → captioned video + ASL signing overlay.

Steps:
  1. transcript  → from manual input or Pika transcribe_audio
  2. gloss        → ASL gloss tokens from transcript (Claude)
  3. lookup       → match tokens to local source clip files
  4. concat       → stitch clips with local ffmpeg
  5. pip          → overlay signing video with local ffmpeg
"""

import pika_client as pika
from gloss import to_asl_gloss
import dictionary as dict_
import local_ffmpeg


def _fuzzy_local_lookup(token: str) -> str | None:
    """Exact match first, then strip common suffixes for a stem match."""
    path = dict_.local_lookup(token)
    if path:
        return path
    word = token.lower()
    for suffix in ("ing", "ed", "es", "s", "er", "ly"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            path = dict_.local_lookup(word[: -len(suffix)])
            if path:
                return path
    return None


def process_video(
    video_url: str,
    pip_position: str = "bottom-right",
    transcript_override: str | None = None,
    video_bytes: bytes | None = None,
    video_filename: str = "upload.mp4",
) -> dict:
    # Step 1: get transcript
    if transcript_override:
        print("[1/4] Using provided transcript.")
        transcript = transcript_override
        captioned_url = video_url
    else:
        print("[1/4] Transcribing via Pika...")
        try:
            result = pika.add_captions(video_url, style="classic")
            transcript = result.get("transcript", "")
            captioned_url = result.get("url") or video_url
        except Exception as e:
            raise ValueError(
                f"Auto-transcription failed: {e}. "
                "Please paste the transcript manually in the Transcript field."
            )
        if not transcript:
            raise ValueError(
                "Could not extract transcript from video. "
                "Please paste the transcript manually in the Transcript field."
            )
    print(f"  Transcript: {transcript[:80]}...")

    # Step 2: convert to ASL gloss
    print("[2/4] Converting to ASL gloss...")
    gloss_tokens = to_asl_gloss(transcript)
    print(f"  Gloss: {' '.join(gloss_tokens)}")

    # Step 3: match tokens to local clip files
    print("[3/4] Looking up sign clips...")
    clip_paths = []
    missing = []
    for token in gloss_tokens:
        path = _fuzzy_local_lookup(token)
        if path:
            clip_paths.append(path)
        else:
            missing.append(token)

    if missing:
        print(f"  Missing: {missing}")

    if not clip_paths:
        raise ValueError(
            f"No matching signs found for gloss: {' '.join(gloss_tokens) or '(empty)'}. "
            "Try a simpler sentence using common words like: hello, want, eat, food, good, help."
        )

    print(f"  Found {len(clip_paths)}/{len(gloss_tokens)} signs.")

    # Step 4: concat clips locally
    print("[3/4] Concatenating sign clips...")
    signing_path = local_ffmpeg.concat(clip_paths)

    # Step 5: get base video as local file
    print("[4/4] Overlaying signing avatar...")
    if video_bytes is not None:
        import tempfile, os
        ext = os.path.splitext(video_filename)[1] or ".mp4"
        base_path = tempfile.mktemp(suffix=ext)
        with open(base_path, "wb") as f:
            f.write(video_bytes)
    else:
        base_path = local_ffmpeg.download_video(video_url)

    output_path = local_ffmpeg.pip_overlay(base_path, signing_path, pip_position)

    return {
        "output_url": f"http://localhost:8000{output_path}",
        "transcript": transcript,
        "gloss": gloss_tokens,
        "signs_found": len(clip_paths),
        "signs_total": len(gloss_tokens),
        "missing_signs": missing,
    }
