"""Generates the SVG artwork for the profile README (dark + light variants).

Run:  py scripts/build_assets.py
Edit the PROJECTS / SECTIONS lists below, re-run, commit.
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets"

THEMES = {
    "dark": dict(bg="#0d1117", card="#11161d", border="#262c36", text="#f0f6fc",
                 muted="#8b949e", accent="#c3f73a", moon="#fcd34d", grid="#2a313c"),
    "light": dict(bg="#ffffff", card="#f6f8fa", border="#d0d7de", text="#1f2328",
                  muted="#59636e", accent="#4d7c0f", moon="#d97706", grid="#d8dee4"),
}

SANS = "'Inter','Segoe UI',-apple-system,BlinkMacSystemFont,Helvetica,Arial,sans-serif"
MONO = "ui-monospace,'SFMono-Regular','JetBrains Mono',Consolas,Menlo,monospace"


def mono_text(x, y, s, size, fill, extra=""):
    """Monospace text forced to an exact width so layout math works on every OS."""
    w = len(s) * size * 0.6
    return (f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{size}" fill="{fill}" '
            f'textLength="{w:.1f}" lengthAdjust="spacingAndGlyphs" {extra}>{s}</text>'), w


# ---------------------------------------------------------------- header
def header(t):
    W, H = 1200, 340
    tag = "building small tools that fix annoying things"
    size, cw = 24, 24 * 0.6
    tx, ty = 96, 262
    n = len(tag)
    dur = n * 0.055
    widths = ";".join(f"{i * cw:.1f}" for i in range(n + 1))
    xs = ";".join(f"{tx + i * cw:.1f}" for i in range(n + 1))
    typed, _ = mono_text(tx, ty, tag, size, t["text"], 'clip-path="url(#type)"')
    prompt, _ = mono_text(64, ty, "$", size, t["accent"])
    label, lw = mono_text(64, 96, "~/dxk-labs", 16, t["accent"])
    loc, _ = mono_text(64 + lw + 14, 96, "// adelaide, au  // [YOUR ROLE HERE]", 16, t["muted"])

    cx, cy = 1000, 170
    orbits = ""
    for r, d, dot, rad in [(62, 12, t["accent"], 5), (104, 21, t["muted"], 4), (146, 34, t["moon"], 3.5)]:
        orbits += (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{t["muted"]}" stroke-opacity="0.35" stroke-dasharray="2 6"/>'
                   f'<g><circle cx="{cx + r}" cy="{cy}" r="{rad}" fill="{dot}"/>'
                   f'<animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" '
                   f'to="360 {cx} {cy}" dur="{d}s" repeatCount="indefinite"/></g>')
    stars = ""
    for i, (sx, sy) in enumerate([(820, 60), (1150, 90), (870, 290), (1130, 280), (760, 200), (1170, 190)]):
        stars += (f'<circle cx="{sx}" cy="{sy}" r="1.6" fill="{t["text"]}">'
                  f'<animate attributeName="opacity" values="0.1;0.9;0.1" dur="{3 + i * 0.7:.1f}s" '
                  f'begin="{i * 0.4:.1f}s" repeatCount="indefinite"/></circle>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="dxk labs: building small tools that fix annoying things">
<defs>
  <pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.1" fill="{t["grid"]}"/></pattern>
  <linearGradient id="fade" x1="0" x2="1"><stop offset="0.25" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff" stop-opacity="1"/></linearGradient>
  <mask id="m"><rect width="{W}" height="{H}" fill="url(#fade)"/></mask>
  <radialGradient id="glow" cx="{cx}" cy="{cy}" r="260" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{t["accent"]}" stop-opacity="0.16"/><stop offset="1" stop-color="{t["accent"]}" stop-opacity="0"/></radialGradient>
  <mask id="crescent"><rect width="{W}" height="{H}" fill="#fff"/><circle cx="{cx + 16}" cy="{cy - 12}" r="30" fill="#000"/></mask>
  <clipPath id="type"><rect x="{tx}" y="{ty - 30}" height="44" width="0"><animate attributeName="width" values="{widths}" dur="{dur:.2f}s" begin="0.9s" calcMode="discrete" fill="freeze"/></rect></clipPath>
  <clipPath id="frame"><rect width="{W}" height="{H}" rx="22"/></clipPath>
  <style>
    .rise{{opacity:0;animation:rise .9s cubic-bezier(.2,.7,.2,1) forwards}}
    @keyframes rise{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:none}}}}
  </style>
</defs>
<g clip-path="url(#frame)">
  <rect width="{W}" height="{H}" fill="{t["bg"]}"/>
  <rect width="{W}" height="{H}" fill="url(#dots)" mask="url(#m)"/>
  <rect width="{W}" height="{H}" fill="url(#glow)"/>
  {stars}
  {orbits}
  <circle cx="{cx}" cy="{cy}" r="34" fill="{t["moon"]}" mask="url(#crescent)"/>
</g>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="22" fill="none" stroke="{t["border"]}"/>
<g class="rise">{label}{loc}</g>
<g class="rise" style="animation-delay:.15s"><text x="58" y="200" font-family="{SANS}" font-size="108" font-weight="800" letter-spacing="-4" fill="{t["text"]}">dxk labs<tspan fill="{t["accent"]}">.</tspan></text></g>
<g class="rise" style="animation-delay:.3s">{prompt}{typed}</g>
<rect x="{tx}" y="{ty - 22}" width="{cw:.1f}" height="28" fill="{t["accent"]}">
  <animate attributeName="x" values="{xs}" dur="{dur:.2f}s" begin="0.9s" calcMode="discrete" fill="freeze"/>
  <animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1.05s" repeatCount="indefinite"/>
</rect>
</svg>'''


# ---------------------------------------------------------------- project cards
def glyph(kind, t):
    c = t["accent"]
    g = {
        "moon": f'<circle cx="0" cy="0" r="46" fill="{c}"/><circle cx="20" cy="-16" r="42" fill="{t["card"]}"/>',
        "chat": f'<rect x="-50" y="-38" width="100" height="68" rx="16" fill="none" stroke="{c}" stroke-width="7"/>'
                f'<path d="M-24 30 L-34 52 L-4 30" fill="{c}"/>'
                f'<circle cx="-22" cy="-4" r="6" fill="{c}"/><circle cx="0" cy="-4" r="6" fill="{c}"/><circle cx="22" cy="-4" r="6" fill="{c}"/>',
        "mail": f'<rect x="-52" y="-36" width="104" height="72" rx="10" fill="none" stroke="{c}" stroke-width="7"/>'
                f'<path d="M-50 -30 L0 8 L50 -30" fill="none" stroke="{c}" stroke-width="7" stroke-linejoin="round"/>'
                f'<path d="M-66 -10 h-14 M-66 10 h-22" stroke="{c}" stroke-width="6" stroke-linecap="round"/>',
        "wave": "".join(f'<rect x="{x - 5}" y="{-h / 2}" width="10" height="{h}" rx="5" fill="{c}">'
                        f'<animate attributeName="height" values="{h};{h * 0.4:.0f};{h}" dur="{0.9 + i * 0.13:.2f}s" repeatCount="indefinite"/>'
                        f'<animate attributeName="y" values="{-h / 2};{-h * 0.2:.0f};{-h / 2}" dur="{0.9 + i * 0.13:.2f}s" repeatCount="indefinite"/></rect>'
                        for i, (x, h) in enumerate([(-48, 30), (-24, 70), (0, 100), (24, 60), (48, 36)])),
    }[kind]
    return f'<g transform="translate(508 150)" opacity="0.14">{g}</g>'


def card(p, t):
    W, H = 600, 230
    tag, _ = mono_text(32, 50, p["tag"], 12, t["muted"], 'letter-spacing="1"')
    st = p["status"]
    sw = len(st) * 12 * 0.6
    px = W - 32 - sw - 30
    status = (f'<rect x="{px}" y="30" width="{sw + 30}" height="28" rx="14" fill="none" stroke="{t["border"]}"/>'
              f'<circle cx="{px + 14}" cy="44" r="4" fill="{t["accent"]}"><animate attributeName="opacity" values="1;0.25;1" dur="2s" repeatCount="indefinite"/></circle>'
              + mono_text(px + 24, 48.5, st, 12, t["text"])[0])
    desc = "".join(f'<text x="32" y="{140 + i * 26}" font-family="{SANS}" font-size="17" fill="{t["muted"]}">{line}</text>'
                   for i, line in enumerate(p["desc"]))
    foot, _ = mono_text(32, 204, p["foot"], 13, t["accent"])
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{p["title"]}">
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="16" fill="{t["card"]}" stroke="{t["border"]}"/>
{glyph(p["glyph"], t)}
{tag}{status}
<text x="30" y="102" font-family="{SANS}" font-size="34" font-weight="750" letter-spacing="-1" fill="{t["text"]}">{p["title"]}</text>
{desc}{foot}
</svg>'''


PROJECTS = [
    dict(slug="sleep-fixer", glyph="moon", tag="FLUTTER · DART · MOBILE", status="shipping",
         title="Sleep Fixer",
         desc=["Fix a wrecked sleep schedule 15 minutes at a time,",
               "not all at once. Prototyped in App Inventor → Flutter."],
         foot="→ dxk-labs/sleep-fixer-legacy"),
    dict(slug="ask-chatgpt", glyph="chat", tag="JAVASCRIPT · CHROME MV3", status="★ 3 · MIT",
         title="Ask ChatGPT",
         desc=["Highlight any text, right-click, get an answer.",
               "A tiny Chrome extension that skips the copy-paste."],
         foot="→ dxk-labs/ask-chatgpt-extension"),
    dict(slug="outlook-roomier", glyph="mail", tag="JS · CSS · FIREFOX + CHROME", status="in the lab",
         title="Outlook Roomier",
         desc=["Outlook Web, minus the claustrophobia. Full-bleed",
               "inbox, wider reading pane, tighter rows."],
         foot="→ [REPO LINK PLACEHOLDER]"),
    dict(slug="slapwindows", glyph="wave", tag="PYTHON · AUDIO · WINDOWS", status="in the lab",
         title="SlapWindows",
         desc=["Slap your laptop. It reacts. Mic-based impact",
               "detection — SlapMac, but for Windows."],
         foot="→ [REPO LINK PLACEHOLDER]"),
]


# ---------------------------------------------------------------- section headers
def section(num, name, t):
    W, H = 1200, 56
    a, aw = mono_text(2, 36, num, 15, t["accent"])
    b, bw = mono_text(2 + aw + 12, 36, name, 15, t["text"])
    x1 = 2 + aw + 12 + bw + 20
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{name}">
<defs><linearGradient id="l" x1="0" x2="1"><stop offset="0" stop-color="{t["border"]}"/><stop offset="1" stop-color="{t["border"]}" stop-opacity="0"/></linearGradient></defs>
{a}{b}<rect x="{x1:.1f}" y="31" width="{W - x1:.1f}" height="1" fill="url(#l)"/>
</svg>'''


SECTIONS = [("01", "about"), ("02", "experience"), ("03", "projects"), ("04", "education"),
            ("05", "stack"), ("06", "activity"), ("07", "contact")]


# ---------------------------------------------------------------- footer
def footer(t):
    W, H = 1200, 110
    s, sw = mono_text(0, 70, "thanks for scrolling  ·  dxk labs  ·  adelaide", 13, t["muted"])
    x = (W - sw) / 2
    s = s.replace('x="0"', f'x="{x:.1f}"', 1)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="thanks for scrolling">
<defs><linearGradient id="h" x1="0" x2="1"><stop offset="0" stop-color="{t["accent"]}" stop-opacity="0"/><stop offset=".5" stop-color="{t["accent"]}"/><stop offset="1" stop-color="{t["accent"]}" stop-opacity="0"/></linearGradient>
<mask id="c"><rect width="{W}" height="{H}" fill="#fff"/><circle cx="{W / 2 + 7}" cy="24" r="10" fill="#000"/></mask></defs>
<rect y="30" width="{W}" height="1" fill="url(#h)" opacity=".6"/>
<circle cx="{W / 2}" cy="30" r="12" fill="{t["bg"]}"/>
<circle cx="{W / 2}" cy="30" r="11" fill="{t["moon"]}" mask="url(#c)"/>
{s}
</svg>'''


def main():
    OUT.mkdir(exist_ok=True)
    for name, t in THEMES.items():
        files = {f"header-{name}.svg": header(t), f"footer-{name}.svg": footer(t)}
        for p in PROJECTS:
            files[f"card-{p['slug']}-{name}.svg"] = card(p, t)
        for num, sec in SECTIONS:
            files[f"section-{sec}-{name}.svg"] = section(num, sec, t)
        for fn, svg in files.items():
            (OUT / fn).write_text(svg, encoding="utf-8")
    print(f"wrote {len(list(OUT.glob('*.svg')))} svgs to {OUT}")


if __name__ == "__main__":
    main()
