"""
Pika client that calls Pika MCP tools via the claude CLI.
No API key required — uses the locally authenticated Claude Code session.
"""

import json
import subprocess

def _claude(prompt: str, schema: dict) -> dict:
    """Run a claude -p call with Pika MCP and return parsed structured output."""
    cmd = [
        "claude", "-p", prompt,
        "--output-format", "json",
        "--json-schema", json.dumps(schema),
        "--allowedTools", "mcp__pika-mcp__*",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        raise RuntimeError(f"claude CLI error: {result.stderr}")
    outer = json.loads(result.stdout)
    if "structured_output" not in outer or not outer["structured_output"]:
        raise RuntimeError(
            f"Pika MCP did not return structured output. "
            f"Response: {outer.get('result', '')[:200]}"
        )
    return outer["structured_output"]


def add_captions(video_url: str, style: str = "classic") -> dict:
    """Returns {url, transcript}."""
    return _claude(
        f'Do two things with this video: {video_url}. '
        f'1) Use the Pika transcribe_audio tool to get the transcript text. '
        f'2) Use the Pika add_captions tool with style="{style}" to get the captioned video URL. '
        f'Return both the captioned video URL and the transcript text.',
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
    url = result.get("url", "")
    if not url:
        raise RuntimeError("Pika edit_concat returned no URL — is Pika MCP connected?")
    return url


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
    url = result.get("url", "")
    if not url:
        raise RuntimeError("Pika edit_pip returned no URL — is Pika MCP connected?")
    return url
