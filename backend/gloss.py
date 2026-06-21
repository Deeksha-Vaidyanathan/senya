"""
Convert English transcript to ASL gloss tokens.

Uses claude CLI (no API key needed — runs in local Claude Code session).
Falls back to rule-based if claude CLI is unavailable.
"""

import os
import re
import json
import subprocess

_STRIP = {
    "a", "an", "the", "is", "are", "was", "were", "am", "be", "been", "being",
    "do", "does", "did", "will", "would", "could", "should", "shall", "may",
    "might", "must", "have", "has", "had", "of", "to", "in", "on", "at",
    "by", "for", "with", "about", "into", "through", "during", "it", "its",
}

def _rule_based(transcript: str) -> list[str]:
    words = re.sub(r"[^a-zA-Z\s'-]", "", transcript).split()
    return [w.upper() for w in words if w.lower() not in _STRIP]

def _claude_gloss(transcript: str) -> list[str]:
    prompt = (
        "Convert this English text to ASL gloss notation. "
        "Rules: remove articles (a/an/the), use topic-comment structure, "
        "present tense only, CAPITALIZE all tokens. "
        "Return only the gloss tokens as a JSON array of strings.\n\n"
        f"Text: {transcript}"
    )
    schema = json.dumps({
        "type": "object",
        "properties": {
            "tokens": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["tokens"]
    })
    result = subprocess.run(
        ["claude", "-p", prompt, "--output-format", "json", "--json-schema", schema],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    outer = json.loads(result.stdout)
    return [t.strip().upper() for t in outer["structured_output"]["tokens"] if t.strip()]

def to_asl_gloss(transcript: str) -> list[str]:
    try:
        return _claude_gloss(transcript)
    except Exception as e:
        print(f"  Claude gloss failed ({e}), using rule-based fallback")
        return _rule_based(transcript)
