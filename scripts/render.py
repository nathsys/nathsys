#!/usr/bin/env python3
"""Render the README header (assets/hero-light.svg and assets/hero-dark.svg).

Pulls total contributions and stars earned from the GitHub API.
Usage: GITHUB_TOKEN=... python3 scripts/render.py
"""
import json
import math
import os
import random
import sys
import urllib.request
from datetime import datetime, timezone
from xml.sax.saxutils import escape

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
USER = os.environ.get("GH_USER", "nathsys")

NAME = "Nathanael Mohanu"
SUBTITLE = "Embedded systems and hardware security. MSc student at TU Delft."
STATUS = "Open to internships in NL"

# Neutral text that matches GitHub's own, plus one orange accent.
THEMES = {
    "dark": dict(text="#e6edf3", muted="#8b949e", faint="#30363d", trace="#484f58", accent="#ff7a45"),
    "light": dict(text="#1f2328", muted="#59636e", faint="#d1d9e0", trace="#afb8c1", accent="#e8590c"),
}
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"


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

    # The API caps each contributions query at one year, so ask for every year since sign-up.
    first = datetime.fromisoformat(u["createdAt"].replace("Z", "+00:00")).year
    now = datetime.now(timezone.utc)
    parts = []
    for y in range(first, now.year + 1):
        start = f"{y}-01-01T00:00:00Z"
        end = now.strftime("%Y-%m-%dT%H:%M:%SZ") if y == now.year else f"{y}-12-31T23:59:59Z"
        parts.append(f'y{y}: contributionsCollection(from: "{start}", to: "{end}") '
                     "{ contributionCalendar { totalContributions } }")
    years = gql(token, "query($login: String!) { user(login: $login) { %s } }" % " ".join(parts),
                {"login": USER})
    contributions = sum(v["contributionCalendar"]["totalContributions"] for v in years.values())
    return contributions, stars


def power_trace(width, rounds=10):
    """A stylised AES-128 power trace: idle, then ten bursts of clocked activity."""
    rng = random.Random(7)
    lead, tail = 24, 24
    rlen = (width - lead - tail) / (rounds - 0.25)
    bounds = [(lead + i * rlen, lead + i * rlen + rlen * (0.75 if i == rounds - 1 else 1))
              for i in range(rounds)]
    pts = []
    for xi in range(width * 2 + 1):
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


def path(pts, y0, amp):
    return "M" + " L".join(f"{x:.1f} {y0 - v * amp:.1f}" for x, v in pts)


def t(x, y, s, size, fill, weight=400, anchor="start"):
    return (f'<text x="{x}" y="{y}" font-family="{SANS}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}">{escape(s)}</text>')


def hero(c, contributions, stars):
    W, H = 840, 230
    out = [t(0, 44, NAME, 36, c["text"], 700), t(1, 76, SUBTITLE, 16, c["muted"])]

    pts, bounds = power_trace(W)
    y0, amp = 158, 44
    a, b = bounds[0]
    for seg, col, sw in (([p for p in pts if p[0] <= a], c["trace"], 1),
                         ([p for p in pts if a <= p[0] <= b], c["accent"], 1.2),
                         ([p for p in pts if p[0] >= b], c["trace"], 1)):
        out.append(f'<path d="{path(seg, y0, amp)}" fill="none" stroke="{col}" stroke-width="{sw}" '
                   f'stroke-linejoin="round"/>')

    # Stats on the left and availability on the right. tspans flow with the font.
    y = 212
    num = f'font-weight="600" fill="{c["text"]}"'
    out.append(f'<text x="0" y="{y}" font-family="{SANS}" font-size="14" fill="{c["muted"]}" '
               f'xml:space="preserve"><tspan {num}>{contributions:,}</tspan> contributions'
               f'<tspan fill="{c["faint"]}">     |     </tspan>'
               f'<tspan {num}>{stars:,}</tspan> stars earned</text>')
    out.append(t(W - 18, y, STATUS, 14, c["text"], 500, "end"))
    out.append(f'<circle cx="{W - 5}" cy="{y - 5}" r="4" fill="{c["accent"]}"/>')

    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
            f'role="img"><title>{escape(NAME)}: {contributions:,} contributions, {stars:,} stars earned'
            f'</title>{"".join(out)}</svg>\n')


def main():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("Set GITHUB_TOKEN")
    contributions, stars = fetch_stats(token)
    os.makedirs(OUT, exist_ok=True)
    for mode, c in THEMES.items():
        with open(os.path.join(OUT, f"hero-{mode}.svg"), "w") as f:
            f.write(hero(c, contributions, stars))
    print(f"contributions={contributions} stars={stars}")


if __name__ == "__main__":
    main()
