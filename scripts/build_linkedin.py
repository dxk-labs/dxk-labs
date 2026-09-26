"""Builds the LinkedIn-style profile: linkedin.toml -> assets/li/*.svg + README.linkedin.md

Run:  py scripts/build_linkedin.py
"""
import base64
import html
import sys
import tomllib
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_assets import THEMES as BRAND, glyph  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "linkedin.toml"
OUT = ROOT / "assets" / "li"
README = ROOT / "README.linkedin.md"

W, PAD = 800, 24
TX = PAD + 48 + 8  # entry text column: LinkedIn's 48px logo + 8px gap
FONT = "-apple-system,system-ui,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif"

THEMES = {
    "light": dict(card="#ffffff", border="#dcdad6", text="#191919", muted="#666666", blue="#0a66c2",
                  on_blue="#ffffff", divider="#e8e8e8", chip="#e9e5df", chip_icon="#8c8c8c",
                  otw_box="#dde7f1", otw="#01754f"),
    "dark": dict(card="#1b1f23", border="#38434f", text="#e9e9e9", muted="#a8a8a8", blue="#71b7fb",
                 on_blue="#000000", divider="#38434f", chip="#38434f", chip_icon="#a8a8a8",
                 otw_box="#1d3044", otw="#4ec38c"),
}
BANNER = BRAND["dark"]


# ---------------------------------------------------------------- helpers
def esc(s):
    return html.escape(str(s), quote=True)


def est(s, size, bold=False):
    return len(s) * size * (0.53 if bold else 0.485)


def wrap(s, size, width, bold=False):
    lines = []
    for para in str(s).strip().split("\n"):
        para = para.strip()
        if not para:
            lines.append("")
            continue
        cur = ""
        for word in para.split():
            nxt = f"{cur} {word}".strip()
            if cur and est(nxt, size, bold) > width:
                lines.append(cur)
                cur = word
            else:
                cur = nxt
        lines.append(cur)
    return lines


def clip(s, size, width, bold=False):
    if est(s, size, bold) <= width:
        return s
    while s and est(s + "…", size, bold) > width:
        s = s[:-1]
    return s.rstrip() + "…"


def text(x, y, s, size=14, fill="#000", weight=400, anchor="start", extra=""):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}" {extra}>{esc(s)}</text>')


def para(x, y, s, t, width, size=14, lh=20):
    out = ""
    for line in wrap(s, size, width):
        if line:
            out += text(x, y, line, size, t["text"])
        y += lh if line else lh * 0.6
    return out, y


def divider(x1, y, t):
    return f'<rect x="{x1}" y="{y:.1f}" width="{W - PAD - x1}" height="1" fill="{t["divider"]}"/>'


def svg(h, body, label, t, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" '
            f'height="{h:.0f}" viewBox="0 0 {W} {h:.0f}" role="img" aria-label="{esc(label)}"><defs>{defs}</defs>'
            f'<rect x="0.5" y="0.5" width="{W - 1}" height="{h - 1:.0f}" rx="8" fill="{t["card"]}" stroke="{t["border"]}"/>'
            f'{body}</svg>')


_clip_ids = iter(range(10**6))
ORGS = {}  # company / school / organization name -> its entry, so honors can borrow a logo


def image_uri(rel):
    f = ROOT / rel
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".svg": "image/svg+xml",
            ".webp": "image/webp"}.get(f.suffix.lower(), "image/png")
    return f"data:{mime};base64,{base64.b64encode(f.read_bytes()).decode()}"


def org_logo(x, y, size, t, e):
    """Real image if `logo = "assets/logos/..."` is set (and exists), else the text tile, else LinkedIn's grey building."""
    e = e or {}
    if e.get("logo") and (ROOT / e["logo"]).exists():
        return logo(x, y, size, t, img=image_uri(e["logo"]))
    return logo(x, y, size, t, e.get("logo_text", ""), e.get("logo_color", ""), e.get("logo_text_color", "#fff"))


def logo(x, y, size, t, label="", color="", fg="#fff", round_=False, img=None):
    r = size / 2 if round_ else 4
    if img:
        cid = f"lg{next(_clip_ids)}"
        return (f'<clipPath id="{cid}"><rect x="{x}" y="{y:.1f}" width="{size}" height="{size}" rx="{r}"/></clipPath>'
                f'<image href="{img}" xlink:href="{img}" x="{x}" y="{y:.1f}" width="{size}" height="{size}" '
                f'preserveAspectRatio="xMidYMid meet" clip-path="url(#{cid})"/>')
    if label and color:
        return (f'<rect x="{x}" y="{y:.1f}" width="{size}" height="{size}" rx="{r}" fill="{color}"/>'
                + text(x + size / 2, y + size / 2 + size * 0.13, label, size * 0.36, fg, 700, "middle"))
    s = size / 48  # LinkedIn's grey "no logo" building
    return (f'<rect x="{x}" y="{y:.1f}" width="{size}" height="{size}" rx="{r}" fill="{t["chip"]}"/>'
            f'<g transform="translate({x} {y:.1f}) scale({s:.3f})" fill="{t["chip_icon"]}">'
            f'<rect x="14" y="12" width="20" height="26" rx="1"/><rect x="18" y="16" width="4" height="4" fill="{t["chip"]}"/>'
            f'<rect x="26" y="16" width="4" height="4" fill="{t["chip"]}"/><rect x="18" y="24" width="4" height="4" fill="{t["chip"]}"/>'
            f'<rect x="26" y="24" width="4" height="4" fill="{t["chip"]}"/><rect x="21" y="31" width="6" height="7" fill="{t["chip"]}"/></g>')


def icon(kind, x, y, t, color=None):
    c = color or t["muted"]
    g = {
        "diamond": f'<rect x="-4.5" y="-4.5" width="9" height="9" transform="rotate(45)" fill="none" stroke="{c}" stroke-width="1.6"/>',
        "profile": f'<rect x="-8" y="-8" width="16" height="16" rx="3" fill="none" stroke="{c}" stroke-width="1.6"/>'
                   f'<circle cx="0" cy="-2" r="2.6" fill="{c}"/><path d="M-4.5 5 a4.5 3.5 0 0 1 9 0" fill="{c}"/>',
        "link": f'<path d="M-2 2 L2 -2 M-1 -4.5 l2 -2 a3.2 3.2 0 0 1 4.5 4.5 l-2 2 M1 4.5 l-2 2 a3.2 3.2 0 0 1 -4.5 -4.5 l2 -2" '
                f'fill="none" stroke="{c}" stroke-width="1.7" stroke-linecap="round"/>',
        "mail": f'<rect x="-8" y="-6" width="16" height="12" rx="2" fill="none" stroke="{c}" stroke-width="1.6"/>'
                f'<path d="M-7 -4.5 L0 1 L7 -4.5" fill="none" stroke="{c}" stroke-width="1.6"/>',
        "arrow": f'<path d="M-6 0 H6 M1 -5 L6 0 L1 5" fill="none" stroke="{c}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
        "chevron": f'<path d="M-3 -6 L3 0 L-3 6" fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
        "plus": f'<path d="M0 -6 V6 M-6 0 H6" stroke="{c}" stroke-width="2" stroke-linecap="round"/>',
        "send": f'<path d="M-7 -6 L7 0 L-7 6 L-4 0 Z" fill="{c}"/>',
    }[kind]
    return f'<g transform="translate({x:.1f} {y:.1f})">{g}</g>'


def button(x, y, label, style, t, ico=None):
    w = est(label, 16, True) + 32 + (22 if ico else 0)
    fill, stroke, fg = {"filled": (t["blue"], t["blue"], t["on_blue"]),
                        "outline": ("none", t["blue"], t["blue"]),
                        "ghost": ("none", t["muted"], t["muted"])}[style]
    tx = x + 16
    out = f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="32" rx="16" fill="{fill}" stroke="{stroke}"/>'
    if ico:
        out += icon(ico, tx + 7, y + 16, t, fg)
        tx += 22
    return out + text(tx, y + 21.5, label, 16, fg, 600), w


def section_title(title, t):
    return text(PAD, 44, title, 20, t["text"], 600)


# ---------------------------------------------------------------- avatar
def avatar_data(url):
    if not url:
        return None
    cache = OUT / "avatar.cache"  # "<url>\n<mime>\n<bytes>" so rebuilds don't hit the network
    if cache.exists():
        c_url, mime, raw = cache.read_bytes().split(b"\n", 2)
        if c_url.decode() == url:
            return f"data:{mime.decode()};base64,{base64.b64encode(raw).decode()}"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            mime, raw = r.headers.get_content_type(), r.read()
    except OSError:
        return None
    cache.write_bytes(f"{url}\n{mime}\n".encode() + raw)
    return f"data:{mime};base64,{base64.b64encode(raw).decode()}"


# ---------------------------------------------------------------- cards
def top_card(d, t, av):
    BH, cx, cy, r = 196, 104, 186, 76
    defs = (f'<clipPath id="bn"><path d="M0 8 a8 8 0 0 1 8 -8 h{W - 16} a8 8 0 0 1 8 8 v{BH - 8} h-{W} z"/></clipPath>'
            f'<clipPath id="av"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath>'
            f'<pattern id="dots" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1" fill="{BANNER["grid"]}"/></pattern>'
            f'<radialGradient id="glow" cx="640" cy="98" r="240" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{BANNER["accent"]}" stop-opacity=".2"/><stop offset="1" stop-color="{BANNER["accent"]}" stop-opacity="0"/></radialGradient>'
            f'<mask id="cres"><rect width="{W}" height="{BH}" fill="#fff"/><circle cx="652" cy="86" r="24" fill="#000"/></mask>'
            f'<path id="otw" d="M {cx + 69 * -0.94:.2f} {cy + 69 * -0.34:.2f} A 69 69 0 0 0 {cx + 69 * 0.17:.2f} {cy + 69 * 0.985:.2f}"/>')
    orbit = ""
    for rr, dur, col, dot in [(48, 12, BANNER["accent"], 4), (80, 21, BANNER["muted"], 3.5), (112, 34, BANNER["moon"], 3)]:
        orbit += (f'<circle cx="640" cy="98" r="{rr}" fill="none" stroke="{BANNER["muted"]}" stroke-opacity=".35" stroke-dasharray="2 6"/>'
                  f'<g><circle cx="{640 + rr}" cy="98" r="{dot}" fill="{col}"/><animateTransform attributeName="transform" '
                  f'type="rotate" from="0 640 98" to="360 640 98" dur="{dur}s" repeatCount="indefinite"/></g>')
    body = (f'<g clip-path="url(#bn)"><rect width="{W}" height="{BH}" fill="{BANNER["bg"]}"/>'
            f'<rect width="{W}" height="{BH}" fill="url(#dots)" opacity=".7"/><rect width="{W}" height="{BH}" fill="url(#glow)"/>'
            f'{orbit}<circle cx="640" cy="98" r="27" fill="{BANNER["moon"]}" mask="url(#cres)"/>'
            f'<text x="{W - 20}" y="{BH - 16}" font-family="ui-monospace,Consolas,monospace" font-size="12" fill="{BANNER["muted"]}" text-anchor="end">dxk labs.</text></g>')

    # avatar + #OPENTOWORK frame
    body += f'<circle cx="{cx}" cy="{cy}" r="{r + 4}" fill="{t["card"]}"/>'
    if av:
        body += f'<image href="{av}" xlink:href="{av}" x="{cx - r}" y="{cy - r}" width="{2 * r}" height="{2 * r}" clip-path="url(#av)" preserveAspectRatio="xMidYMid slice"/>'
    else:
        initials = "".join(w[0] for w in d["name"].strip("[]").split()[:2]).upper() or "?"
        body += f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{t["chip"]}"/>' + text(cx, cy + 14, initials, 40, t["muted"], 600, "middle")
    if d.get("open_to_work"):
        body += (f'<use href="#otw" xlink:href="#otw" fill="none" stroke="{t["otw"]}" stroke-width="15" stroke-linecap="round"/>'
                 f'<text font-family="{FONT}" font-size="10.5" font-weight="700" fill="#fff" letter-spacing=".6" dy="3.8">'
                 f'<textPath href="#otw" xlink:href="#otw" startOffset="50%" text-anchor="middle">#OPENTOWORK</textPath></text>')

    # right column: current company + school
    rx, ry = 528, BH + 106
    for label, lg in [(d["experience"][0]["company"] if d.get("experience") else "", d["experience"][0] if d.get("experience") else {}),
                      (d["education"][0]["school"] if d.get("education") else "", d["education"][0] if d.get("education") else {})]:
        if label:
            body += org_logo(rx, ry - 22, 32, t, lg)
            body += text(rx + 44, ry - 1, clip(label, 14, W - PAD - rx - 44, True), 14, t["text"], 600)
            ry += 44

    # identity
    y = BH + 108
    pron = f'<tspan dx="8" font-size="14" font-weight="400" fill="{t["muted"]}">{esc(d["pronouns"])}</tspan>' if d.get("pronouns") else ""
    body += (f'<text x="{PAD}" y="{y}" font-family="{FONT}" font-size="24" font-weight="600" fill="{t["text"]}">'
             f'{esc(d["name"])}{pron}</text>')
    y += 28
    if d.get("headline"):
        for line in wrap(d["headline"], 16, 480):
            body += text(PAD, y, line, 16, t["text"])
            y += 22
    y += 6
    loc = f'{esc(d["location"])} · ' if d.get("location") else ""
    body += (f'<text x="{PAD}" y="{y}" font-family="{FONT}" font-size="14" fill="{t["muted"]}">{loc}'
             f'<tspan fill="{t["blue"]}" font-weight="600">Contact info</tspan></text>')
    if d.get("stats"):
        y += 24
        body += text(PAD, y, d["stats"], 14, t["blue"], 600)
    y += 18

    bx = PAD
    for label, style, ico in [("Follow", "filled", "plus"), ("Message", "outline", "send"), ("More", "ghost", None)]:
        b, bw = button(bx, y, label, style, t, ico)
        body += b
        bx += bw + 8
    y += 32

    if d.get("open_to_work"):
        y += 16
        bw = 380
        lines = wrap(d["open_to_work_roles"], 14, bw - 32)
        bh = 78 + 20 * len(lines)
        body += f'<rect x="{PAD}" y="{y}" width="{bw}" height="{bh}" rx="8" fill="{t["otw_box"]}"/>'
        yy = y + 26
        body += text(PAD + 16, yy, "Open to work", 14, t["text"], 600)
        for line in lines:
            yy += 20
            body += text(PAD + 16, yy, line, 14, t["text"])
        yy += 20
        body += text(PAD + 16, yy, clip(d.get("open_to_work_details", ""), 14, bw - 32), 14, t["muted"])
        body += text(PAD + 16, yy + 22, "Show details", 14, t["blue"], 600)
        y += bh
    return svg(y + 24, body, ": ".join(filter(None, [d["name"], d.get("headline")])), t, defs)


def about_card(d, t):
    body = section_title("About", t)
    p, y = para(PAD, 76, d["about"], t, W - 2 * PAD)
    body += p
    if d.get("top_skills"):
        y += 8
        body += f'<rect x="{PAD}" y="{y:.1f}" width="{W - 2 * PAD}" height="72" rx="8" fill="none" stroke="{t["border"]}"/>'
        body += icon("diamond", PAD + 24, y + 27, t, t["text"])
        body += text(PAD + 40, y + 32, "Top skills", 14, t["text"], 600)
        body += text(PAD + 16, y + 54, clip(" • ".join(d["top_skills"]), 14, W - 2 * PAD - 72), 14, t["text"])
        body += icon("arrow", W - PAD - 28, y + 36, t, t["text"])
        y += 72
    return svg(y + 24, body, "About", t)


def featured_card(d, t):
    items = d.get("featured", [])[:3]
    body = section_title("Featured", t)
    gap, y0, th = 12, 64, 124
    cw = (W - 2 * PAD - gap * 2) / 3
    for i, f in enumerate(items):
        x = PAD + i * (cw + gap)
        cid = f"th{i}"
        body += (f'<clipPath id="{cid}"><path d="M{x:.1f} {y0 + 8} a8 8 0 0 1 8 -8 h{cw - 16:.1f} a8 8 0 0 1 8 8 v{th - 8} h-{cw:.1f} z"/></clipPath>'
                 f'<rect x="{x:.1f}" y="{y0}" width="{cw:.1f}" height="220" rx="8" fill="none" stroke="{t["border"]}"/>'
                 f'<g clip-path="url(#{cid})"><rect x="{x:.1f}" y="{y0}" width="{cw:.1f}" height="{th}" fill="{BANNER["card"]}"/>'
                 + glyph(f.get("glyph", "moon"), BANNER, x + cw / 2, y0 + th / 2, 1, 0.62)
                 + f'<rect x="{x:.1f}" y="{y0}" width="{cw:.1f}" height="{th}" fill="url(#fg)"/></g>')
        yy = y0 + th + 24
        body += text(x + 12, yy, "Link", 12, t["muted"], 600)
        lines = wrap(f["title"], 14, cw - 24, True)
        if len(lines) > 2:
            lines = [lines[0], clip(lines[1] + " " + lines[2], 14, cw - 24, True)]
        for line in lines:
            yy += 20
            body += text(x + 12, yy, line, 14, t["text"], 600)
        body += text(x + 12, y0 + 206, clip(f["source"], 12, cw - 24), 12, t["muted"])
    if len(d.get("featured", [])) > 3:
        ax, ay = W - PAD + 2, y0 + th / 2
        body += (f'<circle cx="{ax}" cy="{ay}" r="18" fill="{t["card"]}" stroke="{t["border"]}"/>'
                 + icon("chevron", ax + 1, ay, t, t["text"]))
    defs = (f'<radialGradient id="fg" cx=".5" cy=".5" r=".7"><stop offset="0" stop-color="{BANNER["accent"]}" stop-opacity=".22"/>'
            f'<stop offset="1" stop-color="{BANNER["accent"]}" stop-opacity="0"/></radialGradient>')
    return svg(y0 + 220 + 24, body, "Featured", t, defs)


def entries_card(title, entries, t, render, rule_x=TX):
    body = section_title(title, t)
    y = 64
    for i, e in enumerate(entries):
        if i:
            body += divider(rule_x, y, t)
            y += 16
        b, y = render(e, y, t)
        body += b
        y += 16
    return svg(y + 4, body, title, t)


def experience_entry(e, y, t):
    tx, w = TX, W - PAD - TX
    b = org_logo(PAD, y, 48, t, e)
    y += 16
    b += text(tx, y, e["title"], 16, t["text"], 600)
    y += 22
    b += text(tx, y, " · ".join(filter(None, [e["company"], e.get("type")])), 14, t["text"])
    for meta in filter(None, [e.get("dates"), e.get("location")]):
        y += 20
        b += text(tx, y, meta, 14, t["muted"])
    if e.get("description"):
        p, y = para(tx, y + 28, e["description"], t, w)
        b += p
        y -= 20
    if e.get("skills"):
        y += 30
        b += icon("diamond", tx + 7, y - 5, t, t["text"])
        b += (f'<text x="{tx + 22}" y="{y}" font-family="{FONT}" font-size="14" fill="{t["text"]}">'
              f'<tspan font-weight="600">Skills: </tspan>{esc(clip(e["skills"], 14, w - 80))}</text>')
    return b, max(y, y) + 4


def info_entry(e, y, t, title, lines, show_logo=True):
    """title in bold, then (text, muted?) lines, then an optional description; blank lines are skipped."""
    tx, y0 = (TX if show_logo else PAD), y
    b = org_logo(PAD, y, 48, t, e) if show_logo else ""
    y += 16
    b += text(tx, y, title, 16, t["text"], 600)
    y += 2
    for line, muted in lines:
        if line:
            y += 20
            b += text(tx, y, line, 14, t["muted"] if muted else t["text"])
    if e.get("associated"):
        y += 14
        b += org_logo(tx, y, 24, t, ORGS.get(e["associated"]))
        b += text(tx + 32, y + 17, f'Associated with {e["associated"]}', 14, t["text"])
        y += 24
    if e.get("description"):
        p, y = para(tx, y + 28, e["description"], t, W - PAD - tx)
        b += p
        y -= 20
    return b, max(y + 4, y0 + 52 if show_logo else 0)  # never shorter than the logo


def education_entry(e, y, t):
    return info_entry(e, y, t, e["school"], [(e.get("degree"), False), (e.get("dates"), True)])


def volunteering_entry(e, y, t):
    return info_entry(e, y, t, e["role"], [(e.get("organization"), False),
                                           (" · ".join(filter(None, [e.get("dates"), e.get("cause")])), True)])


def honor_entry(e, y, t):
    issued = " · ".join(filter(None, [f'Issued by {e["issuer"]}' if e.get("issuer") else "", e.get("date")]))
    return info_entry(e, y, t, e["title"], [(issued, True)], show_logo=bool(e.get("logo") or e.get("logo_text")))


def skill_entry(e, y, t):
    b = text(PAD, y + 16, e["name"], 16, t["text"], 600)
    if e.get("context"):
        b += logo(PAD, y + 30, 24, t)
        b += text(PAD + 34, y + 47, e["context"], 14, t["text"])
        return b, y + 54
    return b, y + 20


def skills_card(d, t):
    body = section_title("Skills", t)
    y = 64
    for i, e in enumerate(d.get("skills", [])):
        if i:
            body += divider(PAD, y, t)
            y += 16
        b, y = skill_entry(e, y, t)
        body += b
        y += 16
    return svg(y + 8, body, "Skills", t)


def contact_card(d, t):
    body = section_title("Contact info", t)
    y = 64
    for c in d.get("contact", []):
        body += icon(c.get("icon", "link"), PAD + 10, y + 20, t, t["text"])
        body += text(PAD + 36, y + 16, c["label"], 16, t["text"], 600)
        body += text(PAD + 36, y + 38, c["value"], 14, t["blue"], 600)
        y += 60
    return svg(y + 12, body, "Contact info", t)


# ---------------------------------------------------------------- output
def picture(name, alt, href=None):
    pic = (f'<picture><source media="(prefers-color-scheme: dark)" srcset="assets/li/{name}-dark.svg">'
           f'<img alt="{esc(alt)}" src="assets/li/{name}-light.svg" width="100%"></picture>')
    return f'<a href="{esc(href)}">{pic}</a>' if href else pic


SECTIONS = [  # (key in linkedin.toml, card name, alt text, link) — a section is skipped when its key is missing/empty
    ("about", "about", "About", None),
    ("featured", "featured", "Featured", "https://github.com/dxk-labs?tab=repositories"),
    ("experience", "experience", "Experience", None),
    ("education", "education", "Education", None),
    ("volunteering", "volunteering", "Volunteering", None),
    ("skills", "skills", "Skills", None),
    ("honors", "honors", "Honors & awards", None),
    ("contact", "contact", "Contact info", None),
]


def links(items, label):
    row = " · ".join(f'<a href="{esc(i["url"])}">{esc(label(i))}</a>' for i in items if i.get("url"))
    return f'<p align="center"><sub>{row}</sub></p>' if row else ""


def readme(d):
    parts = ["<!-- Generated by scripts/build_linkedin.py from linkedin.toml. Edit the TOML, not this file. -->",
             picture("top", ": ".join(filter(None, [d["name"], d.get("headline")])))]
    for key, card, alt, href in SECTIONS:
        if d.get(key):
            parts.append(picture(card, alt, href))
            if key == "featured":
                parts.append(links(d[key], lambda f: f["title"].split(" — ")[0]))
            if key == "contact":
                parts.append(links(d[key], lambda c: c["label"].replace("Your ", "")))
    return "\n\n".join(p for p in parts if p) + "\n"


def main():
    d = tomllib.loads(DATA.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.svg"):
        old.unlink()
    av = avatar_data(d.get("avatar", ""))
    for key, name in [("experience", "company"), ("education", "school"), ("volunteering", "organization")]:
        ORGS.update({e[name]: e for e in d.get(key, []) if e.get(name)})
    # `hidden = true` on any entry keeps it in the TOML but off the profile
    for key, val in list(d.items()):
        if isinstance(val, list) and val and isinstance(val[0], dict):
            d[key] = [e for e in val if not e.get("hidden")]
    for name, t in THEMES.items():
        builders = {
            "about": lambda: about_card(d, t),
            "featured": lambda: featured_card(d, t),
            "experience": lambda: entries_card("Experience", d["experience"], t, experience_entry),
            "education": lambda: entries_card("Education", d["education"], t, education_entry),
            "skills": lambda: skills_card(d, t),
            "volunteering": lambda: entries_card("Volunteering", d["volunteering"], t, volunteering_entry),
            "honors": lambda: entries_card("Honors & awards", d["honors"], t, honor_entry,
                                           TX if any(h.get("logo") or h.get("logo_text") for h in d["honors"]) else PAD),
            "contact": lambda: contact_card(d, t),
        }
        cards = {"top": top_card(d, t, av)}
        cards.update({card: builders[card]() for key, card, _, _ in SECTIONS if d.get(key)})
        for k, v in cards.items():
            (OUT / f"{k}-{name}.svg").write_text(v, encoding="utf-8")
    README.write_text(readme(d), encoding="utf-8")
    print(f"built linkedin profile -> {README.name} + {len(list(OUT.glob('*.svg')))} svgs")


if __name__ == "__main__":
    main()
