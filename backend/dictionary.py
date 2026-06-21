"""In-memory dictionary loaded from index.json at startup."""

import json
from pathlib import Path

INDEX_PATH = Path(__file__).parent.parent / "dictionary" / "index.json"

_index: dict = {}

def load():
    global _index
    if INDEX_PATH.exists():
        _index = json.loads(INDEX_PATH.read_text())
    print(f"Dictionary loaded: {len(_index)} words, "
          f"{sum(1 for v in _index.values() if v.get('pika_asset_url'))} with generated clips")

def lookup(word: str) -> str | None:
    """Return the Pika asset URL for a word, or None if not in dictionary."""
    entry = _index.get(word.lower())
    if entry and entry.get("pika_asset_url"):
        return entry["pika_asset_url"]
    return None

def stats() -> dict:
    total = len(_index)
    generated = sum(1 for v in _index.values() if v.get("pika_asset_url"))
    verified = sum(1 for v in _index.values() if v.get("verified"))
    return {"total": total, "generated": generated, "verified": verified}
