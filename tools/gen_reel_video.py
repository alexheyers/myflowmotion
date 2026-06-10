#!/usr/bin/env python3
"""Reel-Video via OpenAI Sora-2 — Image-to-Video aus dem gpt-image-2-Keyframe."""
import sys, time, subprocess
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent
ENV = ROOT.parent / "_Content-Pipeline" / ".env"
KEYFRAME = ROOT / "assets" / "reel-keyframe.jpg"
REF = Path("/tmp/reel-ref-1280.jpg")
OUT_RAW = Path("/tmp/reel-sora-raw.mp4")
LOG = ROOT / "tools" / "gen_reel_video.log"

key = None
for line in ENV.read_text().splitlines():
    if line.startswith("OPENAI_API_KEY"):
        key = line.split("=", 1)[1].strip().strip('"').strip("'")
if not key:
    sys.exit("OPENAI_API_KEY nicht gefunden")
H = {"Authorization": f"Bearer {key}"}

def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")

# Referenzbild auf exakt 1280x720 bringen (Sora verlangt Übereinstimmung mit size)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(KEYFRAME),
                "-vf", "scale=1280:854:force_original_aspect_ratio=increase,crop=1280:720",
                "-q:v", "2", str(REF)], check=True)
log(f"Referenz: {REF} ({REF.stat().st_size//1024}KB)")

PROMPT = (
    "Bright Scandinavian studio loft, soft window daylight. The young woman with "
    "voluminous curly red hair, freckles and blue eyes works calmly and focused on her "
    "laptop, fingers typing lightly. Halfway through she glances up toward the camera "
    "with a warm genuine smile, then returns to her work. The teal abstract glow on the "
    "laptop lid shifts gently. Camera: very slow, subtle push-in, locked-off tripod "
    "feel, cinematic shallow depth of field. Natural quiet office ambience. "
    "Strictly no text, no letters, no numbers, no logos, no writing anywhere — not on "
    "any screen, wall or object. No captions, no subtitles, no graphics overlays."
)

log("START Sora-2 Videogenerierung (12s, 1280x720)")
resp = requests.post(
    "https://api.openai.com/v1/videos", headers=H,
    data={"model": "sora-2", "prompt": PROMPT, "seconds": "12", "size": "1280x720"},
    files={"input_reference": ("ref.jpg", REF.read_bytes(), "image/jpeg")},
    timeout=120,
)
if resp.status_code not in (200, 201):
    sys.exit(f"ERROR create {resp.status_code}: {resp.text[:400]}")
vid = resp.json()
vid_id = vid["id"]
log(f"Job angelegt: {vid_id} status={vid.get('status')}")

while True:
    time.sleep(15)
    r = requests.get(f"https://api.openai.com/v1/videos/{vid_id}", headers=H, timeout=60)
    j = r.json()
    st = j.get("status")
    log(f"status={st} progress={j.get('progress')}")
    if st == "completed":
        break
    if st in ("failed", "cancelled"):
        sys.exit(f"FAILED: {j.get('error')}")

r = requests.get(f"https://api.openai.com/v1/videos/{vid_id}/content", headers=H, timeout=300)
OUT_RAW.write_bytes(r.content)
log(f"Roh-Video: {OUT_RAW} ({OUT_RAW.stat().st_size//1024}KB)")

# Komprimieren als Loop-Textur, ersetzt assets/reel.mp4
final = ROOT / "assets" / "reel.mp4"
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(OUT_RAW),
                "-an", "-c:v", "libx264", "-crf", "28", "-preset", "medium",
                "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(final)], check=True)
log(f"FERTIG: {final} ({final.stat().st_size//1024}KB)")
