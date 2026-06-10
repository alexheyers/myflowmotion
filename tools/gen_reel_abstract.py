#!/usr/bin/env python3
"""Abstrakter Lusion-Film: 4 Makro-Szenen (Ink/Glas/Porzellan-Slowmo/Fasern), kein Mensch."""
import sys, time, subprocess
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent
ENV = ROOT.parent / "_Content-Pipeline" / ".env"
LOG = ROOT / "tools" / "gen_reel_abstract.log"

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

NT = " No text, no letters, no numbers, no logos, no people. No captions."
CLIPS = {
    "INK": "Extreme macro, high-speed cinematography: a drop of vivid turquoise ink blooms "
           "underwater in warm cream-colored milky liquid, unfolding into billowing silky "
           "clouds; a ribbon of soft coral-pink ink joins and the two colors swirl around "
           "each other in elegant slow vortices. Studio lighting, velvety texture, hypnotic, "
           "premium commercial aesthetic." + NT,
    "GLASS": "A floating blob of liquid glass hovers in a seamless warm ivory void, slowly "
             "morphing between a sphere, a torus and a flowing ribbon; its surface refracts "
             "soft turquoise and coral-pink studio lights, caustic light patterns dance on "
             "the floor below. Ultra-realistic CGI render look, very slow camera orbit, "
             "mesmerizing, premium design aesthetic." + NT,
    "SLOWMO": "Extreme slow-motion macro: two smooth glossy white ceramic shapes — a rounded "
              "pipe elbow and a capsule — drift together in a bright ivory studio and touch "
              "gently; on contact a delicate cloud of fine rose-pink powder lifts off their "
              "surfaces and hangs shimmering in the air, particles catching the light. "
              "Shallow depth of field, phantom-camera aesthetic, elegant and surprising." + NT,
    "FIBER": "Fast cinematic flythrough inside a luminous network of glowing fiber strands in "
            "deep navy-blue space: turquoise and warm coral light pulses race along the "
            "fibers past the camera, strands branch and converge like a living neural map, "
            "depth haze, lens bloom, exhilarating sense of speed that ends in a calm wide "
            "shot of the whole glowing network." + NT,
}

jobs = {}
for name, prompt in CLIPS.items():
    for attempt in range(4):
        r = requests.post("https://api.openai.com/v1/videos", headers=H,
            files={"model": (None, "sora-2"), "prompt": (None, prompt),
                   "seconds": (None, "8"), "size": (None, "1280x720")}, timeout=120)
        if r.status_code in (200, 201):
            jobs[name] = r.json()["id"]
            log(f"{name} angelegt: {jobs[name]}")
            break
        log(f"{name} Versuch {attempt+1}: {r.status_code}")
        time.sleep(15)
    if name not in jobs:
        log(f"{name} liess sich nicht anlegen — wird übersprungen")

done = {}
deadline = time.time() + 1500
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
            p = Path(f"/tmp/reel-abs-{name}.mp4")
            p.write_bytes(c.content)
            done[name] = p
            log(f"{name} geladen ({p.stat().st_size//1024}KB)")
        elif st in ("failed", "cancelled"):
            log(f"{name} FAILED: {j.get('error')} — übersprungen")
            jobs.pop(name)

order = [n for n in ["INK", "GLASS", "SLOWMO", "FIBER"] if n in done]
if len(order) < 2:
    sys.exit(f"zu wenige Szenen fertig: {order}")
log(f"Schnitt: {' + '.join(order)}")
inputs, filters, labels = [], [], []
for i, name in enumerate(order):
    inputs += ["-i", str(done[name])]
    filters.append(f"[{i}:v]trim=0:7.6,setpts=PTS-STARTPTS,scale=1280:720,format=yuv420p[c{i}]")
    labels.append((f"c{i}", 7.6))
chain, acc = labels[0][0], labels[0][1]
for k in range(1, len(labels)):
    out = f"x{k}"
    filters.append(f"[{chain}][{labels[k][0]}]xfade=transition=fade:duration=0.7:offset={acc-0.7:.1f}[{out}]")
    chain = out
    acc += labels[k][1] - 0.7
subprocess.run(["ffmpeg","-y","-v","error",*inputs,
    "-filter_complex",";".join(filters),
    "-map",f"[{chain}]","-an","-c:v","libx264","-crf","27","-preset","medium",
    "-movflags","+faststart","/tmp/reel-abstract.mp4"], check=True)
final = ROOT / "assets" / "reel.mp4"
subprocess.run(["cp","/tmp/reel-abstract.mp4",str(final)], check=True)
d = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(final)],
                   capture_output=True, text=True).stdout.strip()
log(f"FERTIG: {final} ({final.stat().st_size//1024}KB, {d}s)")
