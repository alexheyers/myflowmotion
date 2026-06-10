#!/usr/bin/env python3
"""Lusion-Imagefilm (~35s): 2 neue Sora-Szenen + bestehende 3 → 5-Szenen-Schnitt."""
import sys, time, subprocess
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent
ENV = ROOT.parent / "_Content-Pipeline" / ".env"
LOG = ROOT / "tools" / "gen_reel_film.log"

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

NO_TEXT = (" Strictly no text, no letters, no numbers, no symbols, no logos anywhere."
           " No captions, no graphics overlays.")
CLIPS = {
    "S1": "Premium 3D design-agency film opening. Seamless warm ivory void (#F2EFE8): smooth "
          "glossy porcelain pipe elbows, discs and capsule nodes drift weightlessly toward each "
          "other and softly assemble into a loose floating cluster, gentle rigid-body collisions, "
          "delicate contact shadows and soft color bleed; one node is teal, one is coral pink, "
          "one deep navy. Very slow orbiting camera, minimalist Scandinavian aesthetic, soft "
          "studio light, shallow depth of field." + NO_TEXT,
    "S5": "Cinematic resolution shot. Deep navy-blue space (#0E2244) filled with thousands of "
          "tiny glowing teal and coral particles forming a chaotic swirling cloud; the particles "
          "slowly organize themselves into an elegant ordered network of connected glowing nodes "
          "— a living system map — then the whole network condenses into a single bright teal "
          "orb that gently descends and lands among glossy porcelain objects on a bright ivory "
          "surface, the scene transitioning from dark to warm light. Slow majestic camera, "
          "subtle bloom, awe and calm." + NO_TEXT,
}

jobs = {}
for name, prompt in CLIPS.items():
    for attempt in range(5):
        r = requests.post("https://api.openai.com/v1/videos", headers=H,
            files={"model": (None, "sora-2"), "prompt": (None, prompt),
                   "seconds": (None, "8"), "size": (None, "1280x720")},
            timeout=120)
        if r.status_code in (200, 201):
            jobs[name] = r.json()["id"]
            log(f"{name} angelegt: {jobs[name]}")
            break
        log(f"{name} Versuch {attempt+1}: {r.status_code} — warte 20s")
        time.sleep(20)
    else:
        sys.exit(f"{name} liess sich nicht anlegen")

done = {}
deadline = time.time() + 1200
while len(done) < len(jobs) and time.time() < deadline:
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
            log(f"{name} geladen ({p.stat().st_size//1024}KB)")
        elif st in ("failed", "cancelled"):
            sys.exit(f"FAILED {name}: {j.get('error')}")
if len(done) < len(jobs):
    sys.exit("Timeout")

# Quellen: A = Lady am Desk (Anfang des aktuellen Reels), B/C aus /tmp oder aus Reel schneiden
A = ROOT / "assets" / "reel.mp4"
B = Path("/tmp/reel-clip-B.mp4")
C = Path("/tmp/reel-clip-C.mp4")
if not B.exists() or not C.exists():
    # aus dem bestehenden 21s-Reel schneiden (A 0-6.3, B 6.3-13.1, C 13.1-21.3)
    subprocess.run(["ffmpeg","-y","-v","error","-i",str(A),"-filter_complex",
        "[0:v]trim=6.5:13,setpts=PTS-STARTPTS[b];[0:v]trim=13.3:21.2,setpts=PTS-STARTPTS[c]",
        "-map","[b]","-an","/tmp/reel-clip-B.mp4","-map","[c]","-an","/tmp/reel-clip-C.mp4"], check=True)
log("Schnitt: S1 + A + B + C + S5 mit xfades")
# Längen: S1 7.5 / A 6.3 / B 6.5 / C 7 / S5 8 — xfade 0.7
subprocess.run(["ffmpeg","-y","-v","error",
    "-i", str(done["S1"]), "-i", str(A), "-i", str(B), "-i", str(C), "-i", str(done["S5"]),
    "-filter_complex",
    "[0:v]trim=0:7.5,setpts=PTS-STARTPTS,scale=1280:720,format=yuv420p[s1];"
    "[1:v]trim=0:6.3,setpts=PTS-STARTPTS,scale=1280:720,format=yuv420p[a];"
    "[2:v]trim=0:6.5,setpts=PTS-STARTPTS,scale=1280:720,format=yuv420p[b];"
    "[3:v]trim=0:7,setpts=PTS-STARTPTS,scale=1280:720,format=yuv420p[c];"
    "[4:v]scale=1280:720,format=yuv420p[s5];"
    "[s1][a]xfade=transition=fade:duration=0.7:offset=6.8[x1];"
    "[x1][b]xfade=transition=fade:duration=0.7:offset=12.4[x2];"
    "[x2][c]xfade=transition=fade:duration=0.7:offset=18.2[x3];"
    "[x3][s5]xfade=transition=fade:duration=0.7:offset=24.5[v]",
    "-map","[v]","-an","-c:v","libx264","-crf","28","-preset","medium",
    "-movflags","+faststart","/tmp/reel-film.mp4"], check=True)
subprocess.run(["cp","/tmp/reel-film.mp4",str(A)], check=True)
d = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(A)],
                   capture_output=True, text=True).stdout.strip()
log(f"FERTIG: {A} ({A.stat().st_size//1024}KB, {d}s)")
