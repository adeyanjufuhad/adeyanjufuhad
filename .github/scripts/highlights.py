"""Highlights panel: six tiles, each with a hand-drawn 8x8 pixel icon.

Static: edit TILES and rerun.  Usage: python highlights.py <output.svg>
"""
import sys
from xml.sax.saxutils import escape

INK = {"a": "#f2a68b", "b": "#8b95dc", "c": "#ffd0b0", "d": "#4a5287"}

ICONS = {
    "cap": [
        "........",
        "...aa...",
        ".aaaaaa.",
        "aaaaaaaa",
        ".abbbba.",
        "..bbbb.c",
        "..bbbb.c",
        ".......c",
    ],
    "trophy": [
        ".aaaaaa.",
        "c.aaaa.c",
        "c.acaa.c",
        ".caaaac.",
        "...aa...",
        "...aa...",
        "..bbbb..",
        ".bbbbbb.",
    ],
    "rocket": [
        "...cc...",
        "..cccc..",
        "..cbbc..",
        "..cccc..",
        ".dccccd.",
        "dd.cc.dd",
        "...aa...",
        "..a..a..",
    ],
    "coins": [
        "..aaaa..",
        ".acccca.",
        "..aaaa..",
        ".acccca.",
        "..aaaa..",
        ".acccca.",
        "..aaaa..",
        "........",
    ],
    "globe": [
        "..bbbb..",
        ".baabbb.",
        "baaabbab",
        "bbaabbbb",
        "bbbbaaab",
        "bbbbaabb",
        ".bbbbab.",
        "..bbbb..",
    ],
    "shield": [
        ".bbbbbb.",
        "bbccccbb",
        "bbcaacbb",
        "bbcaacbb",
        ".bccccb.",
        ".bbccbb.",
        "..bbbb..",
        "...bb...",
    ],
}

TILES = [
    ("cap", "Computer Engineering", "student @ OAU"),
    ("trophy", "Best Graduating Student", "Nupat Technologies"),
    ("rocket", "Co-founder × 2", "two startups, built from zero"),
    ("coins", "Founder, SOVA", "digitising Ajo · Esusu · Adashe"),
    ("globe", "Shipped for the UK", "Luxe Estate property portal"),
    ("shield", "CheckAm", "scam checker in English + Pidgin"),
]

W = 860
COLS = 2
GAP = 14
TW = (W - GAP * (COLS + 1)) / COLS
TH = 86
PX = 6  # size of one icon pixel
H = int(GAP + (TH + GAP) * ((len(TILES) + COLS - 1) // COLS))


def icon(name, x, y):
    out = []
    for r, row in enumerate(ICONS[name]):
        for c, ch in enumerate(row):
            if ch != ".":
                out.append(f'<rect x="{x + c * PX}" y="{y + r * PX}" width="{PX - .6}" height="{PX - .6}" fill="{INK[ch]}"/>')
    return "".join(out)


def main(path):
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
         f'aria-label="{escape("; ".join(f"{t}: {s}" for _, t, s in TILES))}">']
    o.append('<style>'
             'text{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace}'
             '@keyframes in{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}'
             '.t{opacity:0;animation:in .6s cubic-bezier(.2,.7,.2,1) forwards}'
             '@keyframes blink{0%,92%,100%{opacity:1}96%{opacity:.25}}'
             '.i{animation:blink 5s steps(1) infinite}'
             '</style>')
    for k, (name, title, sub) in enumerate(TILES):
        x = GAP + (k % COLS) * (TW + GAP)
        y = GAP + (k // COLS) * (TH + GAP)
        o.append(f'<g class="t" style="animation-delay:{k * 120}ms">')
        o.append(f'<rect x="{x:.1f}" y="{y}" width="{TW:.1f}" height="{TH}" rx="10" fill="#0b0e1c" stroke="#2a2f5a"/>')
        o.append(f'<rect x="{x:.1f}" y="{y}" width="4" height="{TH}" rx="2" fill="{INK["a"] if k % 2 == 0 else INK["b"]}" opacity=".8"/>')
        o.append(f'<g class="i" style="animation-delay:{k * 0.8:.1f}s">{icon(name, x + 24, y + (TH - 8 * PX) / 2)}</g>')
        o.append(f'<text x="{x + 94:.1f}" y="{y + 38}" font-size="16" font-weight="700" fill="#ffd0b0">{escape(title)}</text>')
        o.append(f'<text x="{x + 94:.1f}" y="{y + 61}" font-size="13" fill="#9aa1d6">{escape(sub)}</text>')
        o.append('</g>')
    o.append('</svg>')
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(o))
    print(f"wrote {path} ({W}x{H})")


if __name__ == "__main__":
    main(sys.argv[1])
