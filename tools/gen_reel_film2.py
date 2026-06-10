#!/usr/bin/env python3
"""Recovery: S5 weiterpollen, S1 neu anlegen (entschärfter Prompt), dann 5-Szenen-Schnitt."""
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

NO_TEXT = (" No text, no letters, no numbers, no logos anywhere. No captions.")
PROMPT_S1 = ("Minimalist 3D animation, premium design aesthetic. On a seamless warm cream "
             "background, smooth glossy white ceramic shapes — rounded pipe elbows, discs and "
             "capsules — float gently and drift together into a loose calm cluster. One shape "
             "is turquoise, one is soft coral, one dark blue. Soft studio light, delicate "
             "shadows, very slow orbiting camera, shallow depth of field." + NO_TEXT)

jobs = {"S5": "video_6a29941e3bb481919bf3b710876756fa0fa9d90dce5a2741"}
for attempt in range(4):
    r = requests.post("https://api.openai.com/v1/videos", headers=H,
        files={"model": (None, "sora-2"), "prompt": (None, PROMPT_S1),
               "seconds": (None, "8"), "size": (None, "1280x720")}, timeout=120)
    if r.status_code in (200, 201):
        jobs["S1"] = r.json()["id"]
        log(f"S1 neu angelegt: {jobs['S1']}")
        break
    log(f"S1 Versuch {attempt+1}: {r.status_code}")
    time.sleep(20)
else:
    sys.exit("S1 liess sich nicht anlegen")

done = {}
deadline = time.time() + 1200
while len(done) < len(jobs) and time.time() < deadline:
    time.sleep(15)
    for name, vid in list(jobs.items()):
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
            log(f"{name} FAILED: {j.get('error')} — Szene wird übersprungen")
            jobs.pop(name)
if not done:
    sys.exit("keine neue Szene fertig")

A = ROOT / "assets" / "reel.mp4"
B, C = Path("/tmp/reel-clip-B.mp4"), Path("/tmp/reel-clip-C.mp4")
if not B.exists() or not C.exists():
    subprocess.run(["ffmpeg","-y","-v","error","-i",str(A),"-filter_complex",
        "[0:v]trim=6.5:13,setpts=PTS-STARTPTS[b];[0:v]trim=13.3:21.2,setpts=PTS-STARTPTS[c]",
        "-map","[b]","-an","/tmp/reel-clip-B.mp4","-map","[c]","-an","/tmp/reel-clip-C.mp4"], check=True)

seq = []
if "S1" in done: seq.append(("s1", str(done["S1"]), 7.5))
seq += [("a", str(A), 6.3), ("b", str(B), 6.5), ("c", str(C), 7.0)]
if "S5" in done: seq.append(("s5", str(done["S5"]), 8.0))

inputs, filters, labels = [], [], []
for i, (lbl, path, dur) in enumerate(seq):
    inputs += ["-i", path]
    filters.append(f"[{i}:v]trim=0:{dur},setpts=PTS-STARTPTS,scale=1280:720,format=yuv420p[{lbl}]")
    labels.append((lbl, dur))
chain, acc = labels[0][0], labels[0][1]
for k in range(1, len(labels)):
    out = f"x{k}"
    filters.append(f"[{chain}][{labels[k][0]}]xfade=transition=fade:duration=0.7:offset={acc-0.7:.1f}[{out}]")
    chain = out
    acc += labels[k][1] - 0.7
subprocess.run(["ffmpeg","-y","-v","error",*inputs,
    "-filter_complex",";".join(filters),
    "-map",f"[{chain}]","-an","-c:v","libx264","-crf","28","-preset","medium",
    "-movflags","+faststart","/tmp/reel-film.mp4"], check=True)
subprocess.run(["cp","/tmp/reel-film.mp4",str(A)], check=True)
d = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(A)],
                   capture_output=True, text=True).stdout.strip()
log(f"FERTIG: {A} ({A.stat().st_size//1024}KB, {d}s)")
