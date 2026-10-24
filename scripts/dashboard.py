#!/usr/bin/env python3
"""Render assets/dashboard.svg for the profile README from live GitHub data.

Usage: GITHUB_TOKEN=... python3 scripts/dashboard.py [output.svg]
"""
import json
import math
import os
import sys
import urllib.request
from datetime import date, datetime, timezone
from xml.sax.saxutils import escape

USER = os.environ.get("GH_USER", "nathsys")
NAME = "Nathanael Mohanu"
SUBTITLE = "MSc Computer & Embedded Systems Engineering, TU Delft"
STATUS = "Open to internships in NL"
FOCUS = "Embedded systems, hardware security, performance"
CORE = ["Rust", "C", "C++", "Python", "STM32", "RISC-V", "FPGA",
        "Side-channel analysis", "CMake", "Linux"]

# Palette: brown #382b26 and sage #b8c2b9, plus shades mixed from the two.
BG = "#382b26"
BORDER = "#4d403a"
TEXT = "#dde3dd"
SAGE = "#b8c2b9"
MUTED = "#8f928b"
LEVELS = ["#473d38", "#5e5852", "#7e7e77", "#9ea49c", "#b8c2b9"]
SLICES = ["#b8c2b9", "#9ea49c", "#7e7e77", "#655e58", "#4f4540", "#3f3430"]
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"

W = 840
GAP = 16
PAD = 24

QUERY = """
query($login: String!) {
  user(login: $login) {
    createdAt
    followers { totalCount }
    repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { contributionCount date weekday } }
      }
    }
  }
}
"""


def fetch(token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.load(resp)
    if "errors" in body:
        sys.exit(f"GraphQL error: {body['errors']}")
    return body["data"]["user"]


def fmt(n):
    if n >= 1000:
        return f"{n / 1000:.1f}k".replace(".0k", "k")
    return str(n)


def text_width(s, size):
    return len(s) * size * 0.53


def card(x, y, w, h):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" '
            f'fill="{BG}" stroke="{BORDER}"/>')


def t(x, y, s, size=13, fill=TEXT, weight=400, anchor="start", extra=""):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{anchor}"{extra}>{escape(s)}</text>')


# 24x24 line icons, drawn at the given position and scale.
ICONS = {
    "folder": '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    "star": '<path d="M12 3l2.8 5.7 6.2.9-4.5 4.4 1.1 6.2L12 17.3 6.4 20.2l1.1-6.2L3 9.6l6.2-.9z"/>',
    "pulse": '<path d="M3 12h4l3-7 4 14 3-7h4"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "grid": '<rect x="4" y="4" width="6" height="6" rx="1"/><rect x="14" y="4" width="6" height="6" rx="1"/>'
            '<rect x="4" y="14" width="6" height="6" rx="1"/><rect x="14" y="14" width="6" height="6" rx="1"/>',
    "pie": '<path d="M12 3a9 9 0 1 0 9 9h-9z"/><path d="M15 3.5A9 9 0 0 1 20.5 9H15z"/>',
    "code": '<path d="M9 7l-5 5 5 5M15 7l5 5-5 5"/>',
}


def icon(name, x, y, size=18, color=MUTED):
    s = size / 24
    return (f'<g transform="translate({x} {y}) scale({s:.3f})" fill="none" stroke="{color}" '
            f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</g>')


def render(u):
    repos = u["repositories"]
    stars = sum(r["stargazerCount"] for r in repos["nodes"])
    cal = u["contributionsCollection"]["contributionCalendar"]
    created = datetime.fromisoformat(u["createdAt"].replace("Z", "+00:00"))
    years = max(1, math.floor((datetime.now(timezone.utc) - created).days / 365.25))

    langs = {}
    for r in repos["nodes"]:
        for e in r["languages"]["edges"]:
            langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
    total_bytes = sum(langs.values()) or 1
    ranked = sorted(langs.items(), key=lambda kv: -kv[1])
    top = ranked[:5]
    rest = sum(v for _, v in ranked[5:])
    if rest:
        top.append(("Other", rest))

    out = []
    y = 0

    # Header
    h = 96
    out.append(card(0.5, y + 0.5, W - 1, h))
    out.append(t(PAD, y + 44, NAME, 24, TEXT, 600))
    out.append(t(PAD, y + 70, SUBTITLE, 14, MUTED))
    pw = text_width(STATUS, 12) + 40
    px = W - PAD - pw
    out.append(f'<rect x="{px:.1f}" y="{y + 34}" width="{pw:.1f}" height="28" rx="14" '
               f'fill="none" stroke="{SAGE}" stroke-opacity=".55"/>')
    out.append(f'<circle cx="{px + 15:.1f}" cy="{y + 48}" r="4" fill="{SAGE}"/>')
    out.append(t(px + 26, y + 52, STATUS, 12, SAGE, 500))
    y += h + GAP

    # Stat tiles
    stats = [("folder", fmt(repos["totalCount"]), "PUBLIC REPOS"),
             ("star", fmt(stars), "STARS EARNED"),
             ("pulse", fmt(cal["totalContributions"]), "CONTRIBUTIONS"),
             ("clock", str(years), "YEARS ON GITHUB")]
    tw = (W - GAP * 3) / 4
    th = 112
    for i, (ic, val, label) in enumerate(stats):
        x = i * (tw + GAP)
        cx = x + tw / 2
        out.append(card(x + 0.5, y + 0.5, tw - 1, th))
        out.append(icon(ic, cx - 9, y + 16))
        out.append(t(cx, y + 70, val, 30, TEXT, 600, "middle"))
        out.append(t(cx, y + 94, label, 11, MUTED, 500, "middle", ' letter-spacing="1"'))
    y += th + GAP

    # Contributions
    weeks = cal["weeks"][-53:]
    gx = PAD + 30
    step = (W - PAD - gx) / 53
    cell = step - 3
    gh = 7 * step
    h = 84 + gh + 44
    out.append(card(0.5, y + 0.5, W - 1, h))
    out.append(icon("grid", PAD, y + 22))
    out.append(t(PAD + 28, y + 37, "Contributions", 16, TEXT, 600))
    out.append(t(W - PAD, y + 37, f"{cal['totalContributions']:,} in the last year", 13, MUTED, 400, "end"))
    gy = y + 84
    peak = max((d["contributionCount"] for w in weeks for d in w["contributionDays"]), default=0) or 1
    last_month = None
    for wi, wk in enumerate(weeks):
        x = gx + wi * step
        first = date.fromisoformat(wk["contributionDays"][0]["date"])
        if first.month != last_month and wi < len(weeks) - 2:
            if last_month is not None or first.day <= 7:
                out.append(t(x, gy - 9, first.strftime("%b"), 10, MUTED))
            last_month = first.month
        for d in wk["contributionDays"]:
            c = d["contributionCount"]
            lvl = 0 if c == 0 else min(4, 1 + int(3 * c / peak))
            out.append(f'<rect x="{x:.1f}" y="{gy + d["weekday"] * step:.1f}" width="{cell:.1f}" height="{cell:.1f}" '
                       f'rx="2" fill="{LEVELS[lvl]}"><title>{c} on {d["date"]}</title></rect>')
    for wd, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append(t(PAD, gy + wd * step + 9, name, 10, MUTED))
    ly = gy + gh + 14
    lx = W - PAD - 5 * step - 30
    out.append(t(lx - 6, ly + 9, "Less", 10, MUTED, 400, "end"))
    for i, c in enumerate(LEVELS):
        out.append(f'<rect x="{lx + i * step:.1f}" y="{ly}" width="{cell:.1f}" height="{cell:.1f}" rx="2" fill="{c}"/>')
    out.append(t(lx + 5 * step + 4, ly + 9, "More", 10, MUTED))
    out.append(t(PAD, ly + 9, "Last 52 weeks of activity", 10, MUTED))
    y += h + GAP

    # Tech stack: core technologies + language breakdown
    cw = (W - GAP) / 2
    h = 214
    out.append(card(0.5, y + 0.5, cw - 1, h))
    out.append(icon("code", PAD, y + 22))
    out.append(t(PAD + 28, y + 37, "Core technologies", 16, TEXT, 600))
    cx, cy = PAD, y + 62
    for name in CORE:
        w = text_width(name, 12) + 24
        if cx + w > cw - PAD:
            cx, cy = PAD, cy + 36
        out.append(f'<rect x="{cx:.1f}" y="{cy}" width="{w:.1f}" height="26" rx="13" '
                   f'fill="#43362f" stroke="{BORDER}"/>')
        out.append(t(cx + w / 2, cy + 17, name, 12, SAGE, 500, "middle"))
        cx += w + 8
    out.append(f'<line x1="{PAD}" y1="{y + h - 62}" x2="{cw - PAD}" y2="{y + h - 62}" stroke="{BORDER}"/>')
    out.append(t(PAD, y + h - 38, "FOCUS", 11, MUTED, 500, "start", ' letter-spacing="1"'))
    out.append(t(PAD, y + h - 18, FOCUS, 12.5, SAGE))

    x0 = cw + GAP
    out.append(card(x0 + 0.5, y + 0.5, cw - 1, h))
    out.append(icon("pie", x0 + PAD, y + 22))
    out.append(t(x0 + PAD + 28, y + 37, "Languages", 16, TEXT, 600))
    r, sw = 52, 16
    dcx, dcy = x0 + PAD + r + sw / 2, y + 62 + r + sw / 2 + 4
    circ = 2 * math.pi * r
    off = 0.0
    out.append(f'<circle cx="{dcx}" cy="{dcy}" r="{r}" fill="none" stroke="{BORDER}" stroke-width="{sw}"/>')
    for i, (name, size) in enumerate(top):
        frac = size / total_bytes
        seg = frac * circ
        out.append(f'<circle cx="{dcx}" cy="{dcy}" r="{r}" fill="none" stroke="{SLICES[i]}" '
                   f'stroke-width="{sw}" stroke-dasharray="{seg:.2f} {circ - seg:.2f}" '
                   f'stroke-dashoffset="{-off:.2f}" transform="rotate(-90 {dcx} {dcy})"/>')
        off += seg
    out.append(t(dcx, dcy + 5, f"{len(langs)} langs", 12, MUTED, 500, "middle"))
    lx = dcx + r + sw / 2 + 28
    for i, (name, size) in enumerate(top):
        ry = y + 70 + i * 22
        out.append(f'<circle cx="{lx + 5}" cy="{ry - 4}" r="5" fill="{SLICES[i]}" stroke="{BORDER}"/>')
        out.append(t(lx + 18, ry, name, 13, TEXT))
        out.append(t(W - PAD, ry, f"{100 * size / total_bytes:.0f}%", 13, MUTED, 400, "end"))
    y += h

    height = y + 1
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" '
            f'viewBox="0 0 {W} {height}" font-family="{FONT}" role="img" aria-labelledby="t d">'
            f'<title id="t">{escape(NAME)}: GitHub overview</title>'
            f'<desc id="d">{repos["totalCount"]} public repositories, {stars} stars, '
            f'{cal["totalContributions"]} contributions in the last year.</desc>'
            + "".join(out) + "</svg>\n")


def main():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("Set GITHUB_TOKEN")
    path = sys.argv[1] if len(sys.argv) > 1 else "assets/dashboard.svg"
    svg = render(fetch(token))
    with open(path, "w") as f:
        f.write(svg)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
