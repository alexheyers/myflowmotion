# MyFlowMotion — Lusion-Edition

Lusion-inspirierte 3D-Variante der MyFlowMotion-Homepage. Branch `lusion-edition` — jede Design-Variante lebt in diesem Repo als eigener Branch.

**Live-Referenz der Analyse:** https://lusion.co/ (Three.js r158, Custom-WebGL-Engine)

## Was drin steckt

- **Eine Datei** (`index.html`), kein Build-Step — Three.js 0.158 via CDN-importmap
- **Velocity-Feld:** 192²-Ping-Pong-FBO — der Cursor hinterlässt eine Spur, die Bilder verzerrt
- **Transmorph:** Projektbilder sind WebGL-Planes (DOM-synchronisiert); Klick morpht die Karte zum Vollbild
- **Partikel-Morph:** 9.000 Punkte wechseln per Scroll die Form (Fibonacci-Kugel → Torus-Knoten → Doppel-Helix), mit Maus-Abstoßung
- **Scrollgezeichnete Linien,** Loader mit Prozent-Counter, Custom Cursor, Marquee
- **Fallbacks:** `prefers-reduced-motion` → statisch · ohne WebGL2 → normale Bilder + Overlay

## Design

Ivory `#F2EFE8` · Ink-Navy `#0E2244` · Teal `#1AA591` · Pink `#E94B5D` — Playfair Display / Lato / JetBrains Mono.

## Lokal ansehen

```bash
python3 -m http.server 8765
# → http://localhost:8765
```

© 2026 Alex Heyers · MyFlowMotion
