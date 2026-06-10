#!/usr/bin/env python3
"""Keyframe für das neue Reel — gpt-image-2, 16:9, strikt textfrei."""
import base64, sys, time
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent
ENV = ROOT.parent / "_Content-Pipeline" / ".env"
OUT = ROOT / "assets" / "reel-keyframe.jpg"

key = None
for line in ENV.read_text().splitlines():
    if line.startswith("OPENAI_API_KEY"):
        key = line.split("=", 1)[1].strip().strip('"').strip("'")
if not key:
    sys.exit("OPENAI_API_KEY nicht gefunden")

PROMPT = (
    "Cinematic photographic still, bright Scandinavian studio loft flooded with soft "
    "window daylight. An attractive young woman in her mid-20s with voluminous curly "
    "red hair, light freckles and striking blue eyes sits at a clean light-wood desk, "
    "working focused on a sleek modern laptop, a genuine subtle smile. The laptop "
    "screen shows ONLY abstract minimal glowing teal interface shapes and soft "
    "gradients — strictly no letters, no words, no numbers, no symbols. Warm ivory "
    "walls, a small teal ceramic mug and a coral-pink closed notebook as the only "
    "color accents, shallow depth of field, premium design-agency photography, "
    "photorealistic. Absolutely no text, no letters, no logos, no writing anywhere "
    "in the image — not on the screen, not on walls, not on objects."
)

print(f"[{time.strftime('%H:%M:%S')}] START reel-keyframe", flush=True)
resp = requests.post(
    "https://api.openai.com/v1/images/generations",
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    json={"model": "gpt-image-2", "prompt": PROMPT, "n": 1,
          "size": "1536x1024", "quality": "medium", "output_format": "jpeg"},
    timeout=300,
)
if resp.status_code != 200:
    sys.exit(f"ERROR {resp.status_code}: {resp.text[:300]}")
OUT.write_bytes(base64.b64decode(resp.json()["data"][0]["b64_json"]))
print(f"[{time.strftime('%H:%M:%S')}] SAVED {OUT} ({OUT.stat().st_size//1024}KB)", flush=True)
