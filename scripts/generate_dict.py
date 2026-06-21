"""
Script 2b: Generate Pika avatar sign clips via Pika MCP (claude CLI).

For each word with a source clip but no generated clip, calls
generate_reference_video via the claude CLI (no API key needed).

Run AFTER download_signs.py and generate_avatar.py.
Saves progress to dictionary/index.json after every word — safe to re-run.
"""

import json
import subprocess
import time
from pathlib import Path

INDEX_PATH = Path(__file__).parent.parent / "dictionary" / "index.json"
AVATAR_PATH = Path(__file__).parent.parent / "dictionary" / "avatar.json"

MCP_CONFIG = json.dumps({
    "mcpServers": {
        "pika-mcp": {"type": "url", "url": "https://mcp.pika.me/api/mcp"}
    }
})

SCHEMA = json.dumps({
    "type": "object",
    "properties": {"url": {"type": "string"}},
    "required": ["url"]
})

def load_json(path):
    return json.loads(path.read_text()) if path.exists() else {}

def save_index(index):
    INDEX_PATH.write_text(json.dumps(index, indent=2))

def upload_source(source_path: str) -> str:
    """Upload local file to Pika and return hosted URL."""
    prompt = (
        f"Use the Pika upload_asset tool to upload the file at this path: {source_path}. "
        f"Return the hosted URL."
    )
    result = subprocess.run(
        ["claude", "-p", prompt,
         "--output-format", "json",
         "--json-schema", SCHEMA,
         "--mcp-config", MCP_CONFIG,
         "--allowedTools", "mcp__pika-mcp__*"],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    outer = json.loads(result.stdout)
    return outer["structured_output"]["url"]

def generate_sign_clip(word: str, avatar_url: str, source_url: str) -> str:
    prompt = (
        f"Use the Pika generate_reference_video tool with these parameters: "
        f"prompt='<<<image_1>>> performs the ASL sign for \"{word}\", replicating the exact "
        f"hand shape and movement shown in <<<video_1>>>. Clean neutral background, clear hand "
        f"visibility, no cuts, no text.', "
        f"reference_images=['{avatar_url}'], "
        f"reference_videos=['{source_url}'], "
        f"provider='kling', duration=3, aspect_ratio='1:1', sound=false, "
        f"prompt_adherence='strict', "
        f"negative_prompt='blur, distortion, watermark, text overlay, extra people'. "
        f"Return the output video URL."
    )
    result = subprocess.run(
        ["claude", "-p", prompt,
         "--output-format", "json",
         "--json-schema", SCHEMA,
         "--mcp-config", MCP_CONFIG,
         "--allowedTools", "mcp__pika-mcp__*"],
        capture_output=True, text=True, timeout=600
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    outer = json.loads(result.stdout)
    return outer["structured_output"]["url"]

def main():
    index = load_json(INDEX_PATH)
    avatar = load_json(AVATAR_PATH)

    if not avatar.get("url"):
        print("No avatar found. Run generate_avatar.py first.")
        return

    avatar_url = avatar["url"]
    words = [w for w, v in index.items() if v.get("source") and not v.get("pika_asset_url")]
    print(f"{len(words)} words to generate.\n")

    for word in words:
        print(f"[generate] {word}")
        source_path = index[word]["source"]

        try:
            print("  Uploading source clip...")
            source_url = upload_source(source_path)
        except Exception as e:
            print(f"  [!] Upload failed: {e}")
            continue

        try:
            url = generate_sign_clip(word, avatar_url, source_url)
            print(f"  [ok] {url}")
            index[word]["pika_asset_url"] = url
            index[word]["verified"] = False
        except Exception as e:
            print(f"  [!] Generation failed: {e}")

        save_index(index)
        time.sleep(1)

    print("\nDone. Review clips and set verified=true for good ones in dictionary/index.json.")

if __name__ == "__main__":
    main()
