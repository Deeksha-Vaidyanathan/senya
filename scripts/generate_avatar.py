"""
Script 2a: Generate the base avatar character image via Pika MCP (claude CLI).

Run this ONCE before generate_dict.py.
Saves the avatar URL to dictionary/avatar.json.
"""

import json
import subprocess
from pathlib import Path

AVATAR_PATH = Path(__file__).parent.parent / "dictionary" / "avatar.json"

MCP_CONFIG = json.dumps({
    "mcpServers": {
        "pika-mcp": {"type": "url", "url": "https://mcp.pika.me/api/mcp"}
    }
})

PROMPT = (
    "Use the Pika generate_image tool to create: "
    "A friendly person from the shoulders up, facing the camera directly, "
    "clean light gray background, neutral expression, arms and hands visible, "
    "wearing a dark solid-color shirt for hand contrast, photorealistic, "
    "soft studio lighting, no text, no watermarks. "
    "Return the image URL."
)

SCHEMA = json.dumps({
    "type": "object",
    "properties": {"url": {"type": "string"}},
    "required": ["url"]
})

def main():
    if AVATAR_PATH.exists():
        existing = json.loads(AVATAR_PATH.read_text())
        print(f"Avatar already exists: {existing['url']}")
        print("Delete dictionary/avatar.json to regenerate.")
        return

    print("Generating avatar character...")
    result = subprocess.run(
        ["claude", "-p", PROMPT,
         "--output-format", "json",
         "--json-schema", SCHEMA,
         "--mcp-config", MCP_CONFIG,
         "--allowedTools", "mcp__pika-mcp__*"],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return

    outer = json.loads(result.stdout)
    url = outer["structured_output"]["url"]
    AVATAR_PATH.write_text(json.dumps({"url": url}, indent=2))
    print(f"Avatar saved: {url}")

if __name__ == "__main__":
    main()
