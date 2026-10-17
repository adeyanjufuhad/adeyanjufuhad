"""Draw the last N days of contributions as a dot-matrix graph that matches the banner.

Runs in the profile-art workflow (stdlib only). Needs GITHUB_TOKEN in the env.
Usage: python activity.py <login> <output.svg> [days]
"""
import datetime as dt
import json
import math
import os
import sys
import urllib.request

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar { weeks { contributionDays { date contributionCount } } }
    }
  }
}
"""

BG = "#0b0e1c"
BORDER = "#2a2f5a"
EMPTY = "#1a1f3d"
SOFT = "#c9cdf0"
DIM = "#5a64a8"
PEACH = "#f2a68b"
# bottom row to top row: deep lilac, lilac, peach, pale gold
RAMP = ["#4a5287", "#5f6ab0", "#8b95dc", "#b9a0c8", "#e8a9a8", "#f2a68b", "#f8b59d", "#ffd0b0"]

W, H = 860, 230
ROWS = 12
PAD_X = 40
TOP = 64
DY = 11


def fetch(login):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}", "User-Agent": "profile-art"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    if "errors" in body:
        raise SystemExit(f"GraphQL error: {body['errors']}")
    weeks = body["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return [(d["date"], d["contributionCount"]) for w in weeks for d in w["contributionDays"]]


def colour(row):
    return RAMP[min(len(RAMP) - 1, int(row / (ROWS - 1) * (len(RAMP) - 1) + 0.5))]


def render(days):
    n = len(days)
    dx = (W - PAD_X * 2) / (n - 1)
    peak = max(c for _, c in days) or 1
    total = sum(c for _, c in days)
    active = sum(1 for _, c in days if c)
    peak_i = max(range(n), key=lambda i: days[i][1])

    def fmt(d):
        return dt.date.fromisoformat(d).strftime("%b %d").replace(" 0", " ")

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
         f'aria-label="{total} contributions in the last {n} days">']
    o.append('<style>'
             'text{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace}'
             '@keyframes rise{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}'
             '.c{opacity:0;animation:rise .5s cubic-bezier(.2,.7,.2,1) forwards}'
             '@keyframes pulse{0%,100%{opacity:.35}50%{opacity:1}}'
             '.pk{animation:pulse 2.4s ease-in-out infinite}'
             '</style>')
    o.append(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="{BG}" stroke="{BORDER}"/>')
    o.append(f'<text x="{PAD_X - 6}" y="34" font-size="15" font-weight="700" fill="{PEACH}">contribution activity</text>')
    o.append(f'<text x="{W - PAD_X + 6}" y="34" font-size="13" text-anchor="end" fill="{SOFT}">'
             f'<tspan fill="{PEACH}" font-weight="700">{total}</tspan> contributions · '
             f'<tspan fill="{PEACH}" font-weight="700">{active}</tspan>/{n} days active</text>')

    base_y = TOP + (ROWS - 1) * DY
    for i, (date, c) in enumerate(days):
        x = PAD_X + i * dx
        lit = 0 if c == 0 else max(1, math.ceil(math.sqrt(c / peak) * ROWS))
        o.append(f'<g class="c" style="animation-delay:{i * 18}ms"><title>{fmt(date)}: {c}</title>')
        for r in range(ROWS):
            y = base_y - r * DY
            if r < lit:
                o.append(f'<circle cx="{x:.1f}" cy="{y}" r="3.6" fill="{colour(r)}"/>')
            else:
                o.append(f'<circle cx="{x:.1f}" cy="{y}" r="1.6" fill="{EMPTY}"/>')
        o.append('</g>')

    if days[peak_i][1]:
        px = PAD_X + peak_i * dx
        py = TOP - 14  # the peak column is always full height
        o.append(f'<text class="pk" x="{px:.1f}" y="{py}" font-size="11" text-anchor="middle" fill="#ffd0b0">'
                 f'▼ {days[peak_i][1]}</text>')

    ly = base_y + 26
    for i in (0, n // 2, n - 1):
        anchor = "start" if i == 0 else "end" if i == n - 1 else "middle"
        o.append(f'<text x="{PAD_X + i * dx:.1f}" y="{ly}" font-size="11" text-anchor="{anchor}" fill="{DIM}">'
                 f'{fmt(days[i][0])}</text>')
    o.append('</svg>')
    return "\n".join(o)


def main():
    login, out = sys.argv[1], sys.argv[2]
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    today = dt.date.today().isoformat()
    days = [d for d in fetch(login) if d[0] <= today][-n:]
    with open(out, "w", encoding="utf-8") as f:
        f.write(render(days))
    print(f"wrote {out}: {len(days)} days, {sum(c for _, c in days)} contributions")


if __name__ == "__main__":
    main()
