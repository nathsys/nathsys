#!/usr/bin/env python3
"""Render the README graphics in assets/, each in a light and a dark variant.

The header pulls total contributions and stars earned from the GitHub API.
Lilex (SIL OFL 1.1, assets/fonts) is embedded in every SVG, because a README
image cannot load fonts from anywhere else.

Usage: GITHUB_TOKEN=... python3 scripts/render.py
"""
import base64
import json
import math
import os
import random
import sys
import urllib.request
from datetime import datetime, timezone
from xml.sax.saxutils import escape

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "assets")
USER = os.environ.get("GH_USER", "nathsys")

NAME = "Nathanael Mohanu"
KICKER = "EMBEDDED SYSTEMS · HARDWARE SECURITY"
SUBTITLE = "MSc Computer & Embedded Systems Engineering, TU Delft"
STATUS = "Open to internships in NL"

PROJECTS = [
    ("bootloader", "Rust",
     "A slotted UART bootloader for the STM32F4 that fits in under 16 KB. It checks the "
     "application's vector table before handing over control, and receives firmware updates "
     "as CRC-32 framed messages that go through a sector-guarded flash driver.",
     ["no_std", "STM32F4", "UART", "CRC-32", "probe-rs"]),
    ("pyke", "C++",
     "A single-threaded perft engine built for raw throughput. It uses templates, PEXT "
     "lookup tables and AVX-512 counting, and matches exact perft counts through depth 9.",
     ["C++20", "BMI2", "AVX-512", "PEXT"]),
    ("sunsnake", "C++",
     "A reusable chess move-generation library. It is fuzzed against Stockfish, matches "
     "exact perft counts through depth 8, and runs its test suite in CI.",
     ["C++20", "CMake", "Fuzzing", "GitHub Actions"]),
]

SKILLS = [
    ("LANGUAGES", ["Rust", "C", "C++", "Python", "Java"]),
    ("EMBEDDED", ["ARM Cortex-M", "STM32", "RISC-V", "FPGA (Artix-7)", "UART"]),
    ("SECURITY", ["Side-channel analysis", "TVLA", "SNR", "CPA", "ChipWhisperer"]),
    ("TOOLING", ["Git", "GitHub Actions", "CMake", "Cargo", "probe-rs", "Linux"]),
]

SECTIONS = [("about", "01", "About me"), ("projects", "02", "Projects"), ("skills", "03", "Skillset")]

# Neutral text that matches GitHub's own, plus one orange accent.
THEMES = {
    "dark": dict(text="#e6edf3", body="#c9d1d9", muted="#8b949e", faint="#30363d",
                 chip="#161b22", trace="#484f58", accent="#ff7a45"),
    "light": dict(text="#1f2328", body="#31373d", muted="#59636e", faint="#d1d9e0",
                  chip="#f6f8fa", trace="#afb8c1", accent="#e8590c"),
}
FAMILY = "Lilex, ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
ADVANCE = 0.6          # Lilex is monospaced: every glyph is 600/1000 em wide
W = 840


def width(s, size):
    return len(s) * size * ADVANCE


def font_css(weights):
    rules = []
    for weight, name in ((400, "Regular"), (500, "Medium"), (700, "Bold")):
        if weight in weights:
            with open(os.path.join(OUT, "fonts", f"Lilex-{name}.subset.woff2"), "rb") as f:
                data = base64.b64encode(f.read()).decode()
            rules.append(f"@font-face{{font-family:Lilex;font-weight:{weight};"
                         f"src:url(data:font/woff2;base64,{data}) format('woff2')}}")
    return "<style>" + "".join(rules) + "</style>"


def t(x, y, s, size, fill, weight=400, anchor="start", spacing=0):
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}"{ls}>{escape(s)}</text>')


def svg(h, body, title, weights=(400, 500, 700), extra_defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" '
            f'font-family="{FAMILY}" role="img"><title>{escape(title)}</title>'
            f'<defs>{font_css(weights)}{extra_defs}</defs>{body}</svg>\n')


def wrap(text, size, max_w):
    per_line = int(max_w // (size * ADVANCE))
    lines, line = [], ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > per_line:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + [line]


# ---------------------------------------------------------------- GitHub data

def gql(token, query, variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.load(resp)
    if "errors" in body:
        sys.exit(f"GraphQL error: {body['errors']}")
    return body["data"]["user"]


def fetch_stats(token):
    u = gql(token, """
      query($login: String!) {
        user(login: $login) {
          createdAt
          repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
            nodes { stargazerCount }
          }
        }
      }""", {"login": USER})
    stars = sum(r["stargazerCount"] for r in u["repositories"]["nodes"])

    # Each contributions query covers at most one year, so ask for every year since sign-up.
    first = datetime.fromisoformat(u["createdAt"].replace("Z", "+00:00")).year
    now = datetime.now(timezone.utc)
    parts = []
    for y in range(first, now.year + 1):
        end = now.strftime("%Y-%m-%dT%H:%M:%SZ") if y == now.year else f"{y}-12-31T23:59:59Z"
        parts.append(f'y{y}: contributionsCollection(from: "{y}-01-01T00:00:00Z", to: "{end}") '
                     "{ contributionCalendar { totalContributions } }")
    years = gql(token, "query($login: String!) { user(login: $login) { %s } }" % " ".join(parts),
                {"login": USER})
    return sum(v["contributionCalendar"]["totalContributions"] for v in years.values()), stars


# ---------------------------------------------------------------- header

def power_trace(w, rounds=10):
    """A stylised AES-128 power trace: idle, then ten bursts of clocked activity."""
    rng = random.Random(7)
    lead = tail = 0
    rlen = (w - lead - tail) / (rounds - 0.25)
    bounds = [(lead + i * rlen, lead + i * rlen + rlen * (0.75 if i == rounds - 1 else 1))
              for i in range(rounds)]
    pts = []
    for xi in range(w * 2 + 1):
        x = xi / 2
        act = 0.08
        for i, (a, b) in enumerate(bounds):
            if a <= x < b:
                f = (x - a) / (b - a)
                steps = 3 if i == rounds - 1 else 4
                s = min(int(f * steps), steps - 1)
                act = [0.95, 0.55, 0.8, 0.45][s] * (0.75 + 0.25 * math.sin(f * math.pi))
                if (f * steps) % 1 < 0.08:
                    act *= 0.3
        spike = math.exp(-((x % 5) / 5) * 5)
        pts.append((x, act * spike * (0.7 + 0.3 * rng.random()) + 0.03 * rng.gauss(0, 1)))
    return pts, bounds


def line_path(pts, y0, amp):
    return "M" + " L".join(f"{x:.1f} {y0 - v * amp:.1f}" for x, v in pts)


def hero(c, contributions, stars):
    H = 292
    out = [t(0, 22, KICKER, 13, c["accent"], 700, spacing=2),
           t(-2, 76, NAME, 46, c["text"], 700, spacing=-1),
           t(0, 110, SUBTITLE, 16, c["muted"])]

    pts, bounds = power_trace(W)
    y0, amp = 214, 62
    a, b = bounds[0]
    hot = [p for p in pts if a <= p[0] <= b]
    area = line_path(hot, y0, amp) + f" L{hot[-1][0]:.1f} {y0} L{hot[0][0]:.1f} {y0} Z"
    out.append(f'<path d="{area}" fill="url(#glow)"/>')
    out.append(f'<path d="{line_path([p for p in pts if p[0] >= b], y0, amp)}" fill="none" '
               f'stroke="{c["trace"]}" stroke-width="1" stroke-linejoin="round"/>')
    out.append(f'<path d="{line_path(hot, y0, amp)}" fill="none" stroke="{c["accent"]}" '
               f'stroke-width="1.3" stroke-linejoin="round"/>')

    y = 276
    out.append(f'<line x1="0" y1="{y - 30}" x2="{W}" y2="{y - 30}" stroke="{c["faint"]}"/>')
    num = f'font-weight="700" fill="{c["accent"]}"'
    out.append(f'<text x="0" y="{y}" font-size="14" fill="{c["muted"]}" xml:space="preserve">'
               f'<tspan {num}>{contributions:,}</tspan> contributions'
               f'<tspan fill="{c["faint"]}">   /   </tspan>'
               f'<tspan {num}>{stars:,}</tspan> stars earned</text>')
    out.append(t(W - 20, y, STATUS, 14, c["text"], 500, "end"))
    out.append(f'<circle cx="{W - 5}" cy="{y - 5}" r="4" fill="{c["accent"]}"/>')
    out.append(f'<circle cx="{W - 5}" cy="{y - 5}" r="7.5" fill="none" stroke="{c["accent"]}" '
               f'stroke-opacity=".35"/>')

    glow = (f'<linearGradient id="glow" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{c["accent"]}" stop-opacity=".35"/>'
            f'<stop offset="1" stop-color="{c["accent"]}" stop-opacity="0"/></linearGradient>')
    title = f"{NAME}. {SUBTITLE}. {contributions:,} contributions, {stars:,} stars earned. {STATUS}."
    return svg(H, "".join(out), title, extra_defs=glow)


# ---------------------------------------------------------------- sections

def section_title(c, number, label):
    H = 46
    x = width(number, 14) + 14
    end = x + width(label, 22) + 18
    out = [t(0, 30, number, 14, c["accent"], 700),
           t(x, 31, label, 22, c["text"], 700),
           f'<line x1="{end:.1f}" y1="24" x2="{W}" y2="24" stroke="{c["faint"]}"/>']
    return svg(H, "".join(out), label, weights=(700,))


def chips(c, x, y, items, max_x, size=13, gap=8, h=28):
    """Lay out tag chips left to right, wrapping at max_x. Returns (svg, bottom y)."""
    out, cx, cy = [], x, y
    for item in items:
        w = width(item, size) + 24
        if cx + w > max_x and cx > x:
            cx, cy = x, cy + h + gap
        out.append(f'<rect x="{cx + 0.5:.1f}" y="{cy + 0.5:.1f}" width="{w - 1:.1f}" height="{h - 1}" '
                   f'rx="6" fill="{c["chip"]}" stroke="{c["faint"]}"/>')
        out.append(t(cx + 12, cy + h / 2 + size * 0.36, item, size, c["body"]))
        cx += w + gap
    return "".join(out), cy + h


def project_card(c, name, lang, desc, tags):
    pad = 28
    lines = wrap(desc, 15, W - 2 * pad)
    desc_y = 92
    tag_y = desc_y + (len(lines) - 1) * 25 + 28
    tags_svg, bottom = chips(c, pad, tag_y, tags, W - pad, size=12, h=26)
    H = int(bottom + pad)
    out = [f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="12" fill="none" stroke="{c["faint"]}"/>',
           f'<rect x="0" y="22" width="3" height="34" rx="1.5" fill="{c["accent"]}"/>',
           t(pad, 48, name, 22, c["text"], 700)]
    lx = pad + width(name, 22) + 22
    out.append(f'<circle cx="{lx:.1f}" cy="41" r="4.5" fill="{c["accent"]}"/>')
    out.append(t(lx + 12, 46, lang, 13, c["muted"], 500))
    out.append(f'<path d="M{W - 44} 46 L{W - 32} 34 M{W - 41} 34 H{W - 32} V43" fill="none" '
               f'stroke="{c["muted"]}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>')
    for i, line in enumerate(lines):
        out.append(t(pad, desc_y + i * 25, line, 15, c["body"]))
    out.append(tags_svg)
    return svg(H, "".join(out), f"{name} ({lang}): {desc}")


def skills(c):
    label_w = 150
    out, y = [], 0
    for i, (label, items) in enumerate(SKILLS):
        row, bottom = chips(c, label_w, y + 14, items, W)
        out.append(t(0, y + 14 + 19, label, 12, c["accent"], 700, spacing=1.5))
        out.append(row)
        y = bottom + 14
        if i < len(SKILLS) - 1:
            out.append(f'<line x1="0" y1="{y:.1f}" x2="{W}" y2="{y:.1f}" stroke="{c["faint"]}" '
                       f'stroke-dasharray="2 4"/>')
    title = "Skillset. " + " ".join(f"{label.title()}: {', '.join(items)}." for label, items in SKILLS)
    return svg(int(y + 2), "".join(out), title, weights=(400, 700))


def main():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("Set GITHUB_TOKEN")
    contributions, stars = fetch_stats(token)
    for mode, c in THEMES.items():
        files = {f"hero-{mode}.svg": hero(c, contributions, stars),
                 f"skills-{mode}.svg": skills(c)}
        for slug, number, label in SECTIONS:
            files[f"section-{slug}-{mode}.svg"] = section_title(c, number, label)
        for p in PROJECTS:
            files[f"project-{p[0]}-{mode}.svg"] = project_card(c, *p)
        for name, body in files.items():
            with open(os.path.join(OUT, name), "w") as f:
                f.write(body)
    print(f"contributions={contributions} stars={stars}")


if __name__ == "__main__":
    main()
