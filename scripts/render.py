#!/usr/bin/env python3
"""Render the README graphics in assets/, each in a light and a dark variant.

The header pulls total contributions and stars earned from the GitHub API.
Text is drawn from Lilex glyph outlines (SIL OFL 1.1, assets/fonts), so it
looks identical in every browser at every scale. scripts/extract_glyphs.py
produced the outlines.

Usage: GITHUB_TOKEN=... python3 scripts/render.py
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from xml.sax.saxutils import escape

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "assets")
USER = os.environ.get("GH_USER", "nathsys")

NAME = "Nathanael Mohanu"
SUBTITLE = "MSc Computer & Embedded Systems Engineering, TU Delft"
STATUS = "open to internships in the Netherlands"

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
     ["C++20", "CMake", "fuzzing", "GitHub Actions"]),
]

SKILLS = [
    ("Languages", ["Rust", "C", "C++", "Python", "Java"]),
    ("Embedded", ["ARM Cortex-M", "STM32", "RISC-V", "FPGA (Artix-7)", "UART"]),
    ("Security", ["side-channel analysis", "TVLA", "SNR", "CPA", "ChipWhisperer"]),
    ("Tooling", ["Git", "GitHub Actions", "CMake", "Cargo", "probe-rs", "Linux"]),
]

ABOUT_INTRO = "I'm Nathan, an MSc student in Computer & Embedded Systems Engineering at TU Delft."
THESIS = dict(
    kind="Bachelor thesis",
    place="Leiden University (LIACS)",
    title="Side-channel analysis of the PROACT chip prototype",
    points=[
        "Captured 160,000 power traces from four cryptographic co-processors on an FPGA: "
        "two AES cores, Ascon and Xoodyak",
        "Wrote the capture firmware in C and the analysis pipelines in Python for TVLA, SNR and CPA",
        "Found significant data-dependent leakage in all four co-processors",
        "Recovered the full AES-128 key from both AES cores with first-order CPA",
    ],
)
ABOUT_OUTRO = ("I'm looking for internships in the Netherlands in embedded systems, firmware, "
               "hardware security or software.")
CONTACT = ("Get in touch on ", "LinkedIn")

SECTIONS = [("about", "About me"), ("projects", "Projects"), ("thesis", "Thesis"), ("skills", "Skillset")]

# Neutral text that matches GitHub's own, plus one accent (dark theme, light theme).
ACCENTS = {
    "pine": ("#80b2a3", "#2a453d"),   # #2a453d on light; same hue lightened to stay readable on dark
    "lime": ("#b5e853", "#4f7a0a"),
    "cyan": ("#5cc8e8", "#0b6e8a"),
    "rose": ("#f28bb0", "#b4235a"),
}
ACCENT = os.environ.get("ACCENT", "pine")
THEMES = {
    "dark": dict(text="#e6edf3", body="#c9d1d9", muted="#8b949e", faint="#30363d",
                 accent=ACCENTS[ACCENT][0]),
    "light": dict(text="#1f2328", body="#31373d", muted="#59636e", faint="#d1d9e0",
                  accent=ACCENTS[ACCENT][1]),
}
with open(os.path.join(OUT, "fonts", "lilex-glyphs.json")) as f:
    FONT = json.load(f)
UPM = FONT["unitsPerEm"]
ADVANCE = FONT["advance"] / UPM      # Lilex is monospaced: every glyph is 600/1000 em wide
W = 840
_used = set()                        # glyphs referenced by the SVG being built


def runs(x, y, parts, size, anchor="start", spacing=0):
    """Draw text from glyph outlines. parts is a list of (text, fill, weight) runs."""
    k = size / UPM
    step = FONT["advance"] + spacing / k
    n = sum(len(text) for text, _, _ in parts)
    if anchor == "end":
        x -= (n * step - spacing / k) * k
    out, i = [], 0
    for text, fill, weight in parts:
        uses = []
        for ch in text:
            if ch in FONT["glyphs"][str(weight)]:
                gid = f"g{weight}-{ord(ch):x}"
                _used.add((gid, str(weight), ch))
                uses.append(f'<use href="#{gid}" x="{i * step:.0f}"/>')
            i += 1
        if uses:
            out.append(f'<g fill="{fill}" transform="translate({x:.1f} {y:.1f}) scale({k:.4f} {-k:.4f})">'
                       + "".join(uses) + "</g>")
    return "".join(out)


def t(x, y, s, size, fill, weight=400, anchor="start", spacing=0):
    return runs(x, y, [(s, fill, weight)], size, anchor, spacing)


def rule(y, c):
    return f'<line x1="0" y1="{y - 0.5:.1f}" x2="{W}" y2="{y - 0.5:.1f}" stroke="{c["faint"]}"/>'


def svg(h, body, title):
    defs = "".join(f'<path id="{gid}" d="{FONT["glyphs"][w][ch]}"/>' for gid, w, ch in sorted(_used))
    _used.clear()
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" '
            f'preserveAspectRatio="none" role="img"><title>{escape(title)}</title><defs>{defs}</defs>{body}</svg>\n')


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


# ---------------------------------------------------------------- graphics

def hero(c, contributions, stars):
    H = 154
    out = [t(-2, 52, NAME, 46, c["text"], 700, spacing=-1),
           t(0, 88, SUBTITLE, 16, c["muted"]),
           rule(116, c)]
    y = 146
    out.append(runs(0, y, [(f"{contributions:,}", c["accent"], 700),
                           (" contributions  \u00b7  ", c["muted"], 400),
                           (f"{stars:,}", c["accent"], 700),
                           (" stars earned", c["muted"], 400)], 14))
    out.append(t(W, y, STATUS, 14, c["text"], 500, "end"))
    title = f"{NAME}. {SUBTITLE}. {contributions:,} contributions, {stars:,} stars earned. {STATUS}."
    return svg(H, "".join(out), title)


def section_title(c, label):
    H = 52                 # the top padding separates sections, so the README needs no spacers
    out = [t(0, 34, label, 21, c["text"], 700), rule(H, c)]
    return svg(H, "".join(out), label)


def paragraph(c, x, y, text, max_w, size=15, lead=25, fill=None):
    """Wrapped body text. Returns (svg, y of the last baseline)."""
    out = []
    lines = wrap(text, size, max_w)
    for i, line in enumerate(lines):
        out.append(t(x, y + i * lead, line, size, fill or c["body"]))
    return "".join(out), y + (len(lines) - 1) * lead


def about(c):
    out = []
    body, y = paragraph(c, 0, 26, ABOUT_INTRO, W)
    out.append(body)
    body, y = paragraph(c, 0, y + 34, ABOUT_OUTRO, W)
    out.append(body)
    return svg(int(y + 8), "".join(out), f"{ABOUT_INTRO} {ABOUT_OUTRO}")


def thesis_alt():
    return " ".join([f'{THESIS["kind"]}, {THESIS["place"]}: {THESIS["title"]}.']
                    + [p + "." for p in THESIS["points"]])


def thesis(c):
    y = 28
    out = [t(0, y, THESIS["title"], 17, c["text"], 700),
           t(W, y, THESIS["place"], 13, c["muted"], 500, "end")]
    y += 26
    out.append(t(0, y, THESIS["kind"], 14, c["accent"], 700))
    y += 36
    for point in THESIS["points"]:
        out.append(f'<rect x="2" y="{y - 7}" width="6" height="6" fill="{c["accent"]}"/>')
        body, y = paragraph(c, 22, y, point, W - 22)
        out.append(body)
        y += 30
    return svg(int(y - 16), "".join(out), thesis_alt())


def contact(c):
    lead, link = CONTACT
    x = len(lead) * 15 * ADVANCE
    out = [t(0, 30, lead, 15, c["body"]),
           t(x, 30, link, 15, c["accent"], 700),
           f'<line x1="{x:.1f}" y1="35.5" x2="{x + len(link) * 15 * ADVANCE:.1f}" y2="35.5" '
           f'stroke="{c["accent"]}"/>']
    return svg(44, "".join(out), lead + link)


def project_row(c, name, lang, desc, tags):
    y = 28
    out = [t(0, y, name, 19, c["accent"], 700), t(W, y, lang, 13, c["muted"], 500, "end")]
    y += 32
    for line in wrap(desc, 15, W):
        out.append(t(0, y, line, 15, c["body"]))
        y += 25
    out.append(t(0, y + 4, " · ".join(tags), 13, c["muted"]))
    H = int(y + 22)
    out.append(rule(H, c))
    return svg(H, "".join(out), f"{name} ({lang}): {desc}")


def skills(c):
    label_w = 160
    out, y = [], 0
    for label, items in SKILLS:
        lines = wrap(", ".join(items), 15, W - label_w)
        y += 32
        out.append(t(0, y, label, 14, c["accent"], 500))
        for i, line in enumerate(lines):
            out.append(t(label_w, y + i * 25, line, 15, c["body"]))
        y += (len(lines) - 1) * 25 + 16
        out.append(rule(y, c))
    title = "Skillset. " + " ".join(f"{label}: {', '.join(items)}." for label, items in SKILLS)
    return svg(int(y) + 4, "".join(out), title)


def main():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("Set GITHUB_TOKEN")
    contributions, stars = fetch_stats(token)
    for mode, c in THEMES.items():
        files = {f"hero-{mode}.svg": hero(c, contributions, stars),
                 f"skills-{mode}.svg": skills(c),
                 f"about-{mode}.svg": about(c),
                 f"thesis-{mode}.svg": thesis(c),
                 f"contact-{mode}.svg": contact(c)}
        for slug, label in SECTIONS:
            files[f"section-{slug}-{mode}.svg"] = section_title(c, label)
        for p in PROJECTS:
            files[f"project-{p[0]}-{mode}.svg"] = project_row(c, *p)
        for name, body in files.items():
            with open(os.path.join(OUT, name), "w") as f:
                f.write(body)
    print(f"contributions={contributions} stars={stars}")


if __name__ == "__main__":
    main()
