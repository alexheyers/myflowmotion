#!/usr/bin/env python3
"""Stufen-Bilder für die Lusion-Studio-Stationen — gpt-image-2, Porzellan/Ivory-Look."""
import base64, json, sys, time
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent
ENV = ROOT.parent / "_Content-Pipeline" / ".env"
ASSETS = ROOT / "assets"

key = None
for line in ENV.read_text().splitlines():
    if line.startswith("OPENAI_API_KEY"):
        key = line.split("=", 1)[1].strip().strip('"').strip("'")
if not key:
    sys.exit("OPENAI_API_KEY nicht in .env gefunden")

LOG = ROOT / "tools" / "gen_stage_images.log"
def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")

STYLE = (
    "Minimalist premium 3D render, seamless warm ivory background (#F2EFE8). "
    "Smooth glossy porcelain-white material, soft diffuse studio lighting, delicate "
    "contact shadows, subtle color bleed between objects, Scandinavian design-agency "
    "aesthetic, generous negative space, photorealistic CGI quality. "
    "Accent colors only: teal (#1AA591), coral pink (#E94B5D), deep navy (#0E2244). "
    "No text, no logos, no people, no watermarks."
)

IMAGES = {
    "stage-verstehen.jpg": (
        "A smooth glossy porcelain capsule-shaped voice node hovering in space, emitting "
        "delicate concentric sound-wave rings made of thin glowing teal lines, one small "
        "coral-pink accent sphere orbiting nearby, a few navy dots floating like data. " + STYLE
    ),
    "stage-designen.jpg": (
        "Glossy porcelain spheres and rounded pipe elbows arranged as a clean system map "
        "seen slightly from above, connected by thin deep-navy lines, one node glowing teal, "
        "one node coral pink, the layout suggesting an elegant network blueprint. " + STYLE
    ),
    "stage-bauen.jpg": (
        "A delicate porcelain mechanical assembly: smooth white robotic pipe segments "
        "precisely connecting glowing translucent teal modules into a growing structure, "
        "one coral-pink module just being placed, fine navy details, a sense of calm "
        "construction and orchestration. " + STYLE
    ),
}

headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
results = {}
for fname, prompt in IMAGES.items():
    out = ASSETS / fname
    if out.exists():
        log(f"SKIP {fname} (existiert)")
        results[fname] = "skipped"
        continue
    log(f"START {fname}")
    try:
        resp = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers=headers,
            json={
                "model": "gpt-image-2",
                "prompt": prompt,
                "n": 1,
                "size": "1024x1536",
                "quality": "high",
                "output_format": "jpeg",
            },
            timeout=300,
        )
        if resp.status_code == 200:
            b64 = resp.json()["data"][0]["b64_json"]
            out.write_bytes(base64.b64decode(b64))
            log(f"  SAVED {fname} ({out.stat().st_size // 1024}KB)")
            results[fname] = "ok"
        else:
            log(f"  ERROR {resp.status_code}: {resp.text[:300]}")
            results[fname] = f"error_{resp.status_code}"
    except Exception as e:
        log(f"  EXCEPTION: {e}")
        results[fname] = f"exception: {e}"

log(f"DONE — {json.dumps(results)}")
