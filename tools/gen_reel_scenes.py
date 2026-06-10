#!/usr/bin/env python3
"""Reel v3: 2 weitere Sora-Szenen mit der Curly-Lady, dann 3-Szenen-Schnitt."""
import sys, time, subprocess
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent
ENV = ROOT.parent / "_Content-Pipeline" / ".env"
REF = Path("/tmp/reel-ref-1280.jpg")
LOG = ROOT / "tools" / "gen_reel_scenes.log"

key = None
for line in ENV.read_text().splitlines():
    if line.startswith("OPENAI_API_KEY"):
        key = line.split("=", 1)[1].strip().strip('"').strip("'")
H = {"Authorization": f"Bearer {key}"}

def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")

if not REF.exists():
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(ROOT / "assets" / "reel-keyframe.jpg"),
                    "-vf", "scale=1280:854:force_original_aspect_ratio=increase,crop=1280:720",
                    "-q:v", "2", str(REF)], check=True)

BASE_LADY = ("The same young woman with voluminous curly red hair, light freckles, blue eyes, "
             "white linen shirt, in the same bright Scandinavian studio loft with warm ivory "
             "walls and soft window daylight. ")
NO_TEXT = (" Strictly no text, no letters, no numbers, no symbols, no logos anywhere — not on "
           "any screen, wall or object. No captions, no graphics overlays.")

CLIPS = {
    "B": BASE_LADY + "Close over-the-shoulder shot: her hands typing lightly on the sleek "
         "laptop, the screen filled only with flowing abstract teal gradient waves and soft "
         "glowing particles. The camera orbits very slowly from behind her shoulder around to "
         "her profile, cinematic shallow depth of field, calm and focused mood." + NO_TEXT,
    "C": BASE_LADY + "She leans back from the laptop and a delicate cloud of tiny glowing teal "
         "and coral particles rises from the device, swirling like a miniature galaxy in the "
         "bright room. She watches it with a delighted calm smile, the lights reflecting "
         "subtly in her blue eyes. Slow gentle camera pull-out, magical but realistic." + NO_TEXT,
}

jobs = {}
for name, prompt in CLIPS.items():
    r = requests.post("https://api.openai.com/v1/videos", headers=H,
        data={"model": "sora-2", "prompt": prompt, "seconds": "8", "size": "1280x720"},
        files={"input_reference": ("ref.jpg", REF.read_bytes(), "image/jpeg")}, timeout=120)
    if r.status_code not in (200, 201):
        sys.exit(f"ERROR create {name}: {r.status_code} {r.text[:300]}")
    jobs[name] = r.json()["id"]
    log(f"Clip {name} angelegt: {jobs[name]}")

done = {}
while len(done) < len(jobs):
    time.sleep(15)
    for name, vid in jobs.items():
        if name in done:
            continue
        j = requests.get(f"https://api.openai.com/v1/videos/{vid}", headers=H, timeout=60).json()
        st = j.get("status")
        log(f"{name}: {st} {j.get('progress')}")
        if st == "completed":
            c = requests.get(f"https://api.openai.com/v1/videos/{vid}/content", headers=H, timeout=300)
            p = Path(f"/tmp/reel-clip-{name}.mp4")
            p.write_bytes(c.content)
            done[name] = p
            log(f"{name} geladen: {p} ({p.stat().st_size//1024}KB)")
        elif st in ("failed", "cancelled"):
            sys.exit(f"FAILED {name}: {j.get('error')}")

# Schnitt: Szene A (erste 7s des bestehenden Reels) + B + C, weich verbunden
A = ROOT / "assets" / "reel.mp4"
final = ROOT / "assets" / "reel.mp4"
subprocess.run(["ffmpeg", "-y", "-v", "error",
    "-i", str(A), "-i", str(done["B"]), "-i", str(done["C"]),
    "-filter_complex",
    "[0:v]trim=0:7,setpts=PTS-STARTPTS,scale=1280:720,format=yuv420p[a];"
    "[1:v]trim=0:7.5,setpts=PTS-STARTPTS,scale=1280:720,format=yuv420p[b];"
    "[2:v]scale=1280:720,format=yuv420p[c];"
    "[a][b]xfade=transition=fade:duration=0.7:offset=6.3[ab];"
    "[ab][c]xfade=transition=fade:duration=0.7:offset=13.1[v]",
    "-map", "[v]", "-an", "-c:v", "libx264", "-crf", "28", "-preset", "medium",
    "-movflags", "+faststart", "/tmp/reel-final.mp4"], check=True)
subprocess.run(["cp", "/tmp/reel-final.mp4", str(final)], check=True)
log(f"FERTIG: {final} ({final.stat().st_size//1024}KB)")
