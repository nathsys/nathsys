#!/usr/bin/env python3
"""Render the README graphics in assets/, each in a light and a dark variant.

The header pulls total contributions and stars earned from the GitHub API.
Lilex (SIL OFL 1.1, assets/fonts) is embedded in every SVG, because a README
image cannot load fonts from anywhere else.

Usage: GITHUB_TOKEN=... python3 scripts/render.py
"""
import base64
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
SUBTITLE = "Embedded systems and hardware security. MSc student at TU Delft."
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

SECTIONS = [("about", "About me"), ("projects", "Projects"), ("skills", "Skillset")]

# Neutral text that matches GitHub's own, plus one accent (dark theme, light theme).
ACCENTS = {
    "lime": ("#b5e853", "#4f7a0a"),
    "cyan": ("#5cc8e8", "#0b6e8a"),
    "rose": ("#f28bb0", "#b4235a"),
}
ACCENT = os.environ.get("ACCENT", "lime")
THEMES = {
    "dark": dict(text="#e6edf3", body="#c9d1d9", muted="#8b949e", faint="#30363d",
                 accent=ACCENTS[ACCENT][0]),
    "light": dict(text="#1f2328", body="#31373d", muted="#59636e", faint="#d1d9e0",
                  accent=ACCENTS[ACCENT][1]),
}
FAMILY = "Lilex, ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
ADVANCE = 0.6          # Lilex is monospaced: every glyph is 600/1000 em wide
W = 840


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


def rule(y, c):
    return f'<line x1="0" y1="{y - 0.5:.1f}" x2="{W}" y2="{y - 0.5:.1f}" stroke="{c["faint"]}"/>'


def svg(h, body, title, weights=(400, 500, 700)):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" '
            f'font-family="{FAMILY}" role="img"><title>{escape(title)}</title>'
            f'<defs>{font_css(weights)}</defs>{body}</svg>\n')


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
    H = 160
    out = [t(-2, 52, NAME, 46, c["text"], 700, spacing=-1),
           t(0, 88, SUBTITLE, 16, c["muted"]),
           rule(116, c)]
    y = 146
    num = f'font-weight="700" fill="{c["accent"]}"'
    out.append(f'<text x="0" y="{y}" font-size="14" fill="{c["muted"]}" xml:space="preserve">'
               f'<tspan {num}>{contributions:,}</tspan> contributions  ·  '
               f'<tspan {num}>{stars:,}</tspan> stars earned</text>')
    out.append(t(W, y, STATUS, 14, c["text"], 500, "end"))
    title = f"{NAME}. {SUBTITLE} {contributions:,} contributions, {stars:,} stars earned. {STATUS}."
    return svg(H, "".join(out), title)


def section_title(c, label):
    H = 78                 # the top padding separates sections, so the README needs no spacers
    out = [t(0, 60, label, 21, c["text"], 700), rule(H, c)]
    return svg(H, "".join(out), label, weights=(700,))


def project_row(c, name, lang, desc, tags):
    y = 36
    out = [t(0, y, name, 19, c["accent"], 700), t(W, y, lang, 13, c["muted"], 500, "end")]
    y += 32
    for line in wrap(desc, 15, W):
        out.append(t(0, y, line, 15, c["body"]))
        y += 25
    out.append(t(0, y + 4, "  ·  ".join(tags), 13, c["muted"]))
    H = int(y + 30)
    out.append(rule(H, c))
    return svg(H, "".join(out), f"{name} ({lang}): {desc}")


def skills(c):
    label_w = 160
    out, y = [], 0
    for label, items in SKILLS:
        lines = wrap(", ".join(items), 15, W - label_w)
        y += 38
        out.append(t(0, y, label, 14, c["accent"], 500))
        for i, line in enumerate(lines):
            out.append(t(label_w, y + i * 25, line, 15, c["body"]))
        y += (len(lines) - 1) * 25 + 20
        out.append(rule(y, c))
    title = "Skillset. " + " ".join(f"{label}: {', '.join(items)}." for label, items in SKILLS)
    return svg(int(y) + 16, "".join(out), title, weights=(400, 500))


def main():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("Set GITHUB_TOKEN")
    contributions, stars = fetch_stats(token)
    for mode, c in THEMES.items():
        files = {f"hero-{mode}.svg": hero(c, contributions, stars),
                 f"skills-{mode}.svg": skills(c)}
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
