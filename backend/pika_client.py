"""
Pika client that calls Pika MCP tools via the claude CLI.
No API key required — uses the locally authenticated Claude Code session.
"""

import json
import subprocess

MCP_CONFIG = json.dumps({
    "mcpServers": {
        "pika-mcp": {
            "type": "url",
            "url": "https://mcp.pika.me/api/mcp"
        }
    }
})

def _claude(prompt: str, schema: dict) -> dict:
    """Run a claude -p call with Pika MCP and return parsed structured output."""
    cmd = [
        "claude", "-p", prompt,
        "--output-format", "json",
        "--json-schema", json.dumps(schema),
        "--mcp-config", MCP_CONFIG,
        "--allowedTools", "mcp__pika-mcp__*",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        raise RuntimeError(f"claude CLI error: {result.stderr}")

    outer = json.loads(result.stdout)
    # structured output lives in outer["structured_output"]
    return outer["structured_output"]


def add_captions(video_url: str, style: str = "classic") -> dict:
    """Returns {url, transcript}."""
    return _claude(
        f'Use the Pika add_captions tool on this video: {video_url} with style="{style}". '
        f'Return the output video URL and the transcript text.',
        {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "transcript": {"type": "string"}
            },
            "required": ["url", "transcript"]
        }
    )


def upload_asset(file_bytes: bytes, filename: str) -> str:
    """Upload a local file via Pika and return the hosted URL."""
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix=os.path.splitext(filename)[1], delete=False) as f:
        f.write(file_bytes)
        tmp_path = f.name
    try:
        result = _claude(
            f'Use the Pika upload_asset tool to upload the file at path: {tmp_path}. '
            f'Return the hosted URL.',
            {
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"]
            }
        )
        return result["url"]
    finally:
        os.unlink(tmp_path)


def edit_concat(clip_urls: list[str]) -> str:
    """Concatenate clips and return output URL."""
    urls_str = ", ".join(clip_urls)
    result = _claude(
        f'Use the Pika edit_concat tool to concatenate these video clips in order: {urls_str}. '
        f'Return the output video URL.',
        {
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"]
        }
    )
    return result["url"]


def edit_pip(base_url: str, overlay_url: str, position: str = "bottom-right") -> str:
    """Overlay signing avatar onto the base video. Returns output URL."""
    result = _claude(
        f'Use the Pika edit_pip tool with base_video_url="{base_url}", '
        f'overlay_video_url="{overlay_url}", position="{position}". '
        f'Return the output video URL.',
        {
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"]
        }
    )
    return result["url"]
