"""
Core pipeline: video → captioned video + ASL signing overlay.

Steps:
  1. add_captions  → captioned source video + transcript
  2. gloss          → ASL gloss tokens from transcript
  3. concat         → stitch sign clips into continuous signing video
  4. pip            → overlay signing video onto captioned source
"""

import pika_client as pika
from gloss import to_asl_gloss
import dictionary as dict_


def process_video(video_url: str, pip_position: str = "bottom-right") -> dict:
    # Step 1: transcribe + burn captions in one call
    print(f"[1/4] Adding captions...")
    captions_result = pika.add_captions(video_url, style="classic")
    captioned_url = captions_result["url"]
    transcript = captions_result["transcript"]
    print(f"  Transcript: {transcript[:80]}...")

    # Step 2: convert transcript to ASL gloss
    print(f"[2/4] Converting to ASL gloss...")
    gloss_tokens = to_asl_gloss(transcript)
    print(f"  Gloss: {' '.join(gloss_tokens)}")

    # Step 3: look up sign clips and concat
    print(f"[3/4] Looking up sign clips...")
    clip_urls = []
    missing = []
    for token in gloss_tokens:
        url = dict_.lookup(token)
        if url:
            clip_urls.append(url)
        else:
            missing.append(token)

    if missing:
        print(f"  Missing from dictionary: {missing}")

    if not clip_urls:
        raise ValueError("No sign clips found. Dictionary may be empty.")

    print(f"  Found {len(clip_urls)}/{len(gloss_tokens)} signs. Concatenating...")
    signing_video_url = pika.edit_concat(clip_urls)

    # Step 4: pip overlay
    print(f"[4/4] Overlaying signing avatar...")
    final_url = pika.edit_pip(captioned_url, signing_video_url, position=pip_position)

    return {
        "output_url": final_url,
        "transcript": transcript,
        "gloss": gloss_tokens,
        "signs_found": len(clip_urls),
        "signs_total": len(gloss_tokens),
        "missing_signs": missing,
    }
