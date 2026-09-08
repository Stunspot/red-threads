"""Assemble the portable offline RED THREADS atlas without dependencies."""
from __future__ import annotations
import json
from pathlib import Path
TOKEN = "__RED_THREADS_CASE_JSON__"
def render(data: dict) -> str:
    """Return one self-contained atlas; supplied values remain inert JSON text."""
    if not isinstance(data, dict):
        raise TypeError("case data must be a dictionary")
    template = (Path(__file__).resolve().parent.parent / "assets" / "atlas.html").read_text(encoding="utf-8")
    if template.count(TOKEN) != 1:
        raise ValueError("atlas template must contain exactly one case placeholder")
    payload = json.dumps(data, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    for character, escaped in (("&", "\\u0026"), ("<", "\\u003c"), (">", "\\u003e"), ("\u2028", "\\u2028"), ("\u2029", "\\u2029")):
        payload = payload.replace(character, escaped)
    return template.replace(TOKEN, payload)
