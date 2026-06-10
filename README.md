# MyFlowMotion — Lusion-Edition

Lusion-inspirierte 3D-Variante der MyFlowMotion-Homepage. Branch `lusion-edition` — jede Design-Variante lebt in diesem Repo als eigener Branch.

**Live-Referenz der Analyse:** https://lusion.co/ (Three.js r158, Custom-WebGL-Engine)

## Was drin steckt (v2 — eine Szene, eine Kamerafahrt)

- **Eine Datei** (`index.html`), kein Build-Step — Three.js 0.158 via CDN-importmap
- **Persistente 3D-Szene mit 6 Stationen:** Hero-Cluster → pinkes Reel → Projekte → Tunnelflug durchs Void → Licht/About → Sticker-Finale. Farb-Dramaturgie über Keyframes, Kamera fliegt durch die Szene
- **Squishy-Cluster (Lusion-Rezept):** In **Blender headless** generierte GLB-Objekte, CPU-Starrkörper-Physik (Zentripetalkraft, Paar-Kollision, Abroll-Drall, Maus-Pushback) — die „Weichheit" kommt aus analytischem Nachbar-Shading im Fragment-Shader (Sphere-Occlusion-AO, Soft-Shadows, farbige GI, Nachbar-Reflexionen) + prozeduraler Matcap
- **ScreenPaint-Smear:** Quarter-Res-Ping-Pong-Velocity-Feld; der finale Frame wird entlang der Cursor-Spur 9-Tap-verschmiert + RGB-Shimmer
- **Post-Stack:** Szene-RT (4× MSAA) → 2 Bloom-Mips → Grade (Sättigung, Kontrast, Vignette, chromatische Aberration im Tunnel, Grain)
- **Transmorph:** Projektbilder als DOM-synchrone GL-Planes; Klick morpht zur Vollbild-Story
- **Second-Order-Dynamics** (t3ssel8r-Feder) für Scroll- und Kamera-Smoothing
- **Fallbacks:** `prefers-reduced-motion`/kein WebGL2 → statische, voll lesbare Seite

## Design

Ivory `#F2EFE8` · Ink-Navy `#0E2244` · Teal `#1AA591` · Pink `#E94B5D` — Playfair Display / Lato / JetBrains Mono.

## Lokal ansehen

```bash
python3 -m http.server 8765
# → http://localhost:8765
```

© 2026 Alex Heyers · MyFlowMotion
