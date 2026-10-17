"""Bake the ascii.rest "scramble" decode effect into an animated SVG for a GitHub README.

GitHub strips scripts from README images, so every frame is precomputed here and
played back with a discrete SMIL translate (no JS needed).

Usage: python gen_scramble.py <output.svg>
Edit PHRASES / colours below to change what cycles.
"""
import math
import sys
from xml.sax.saxutils import escape

PHRASES = [
    "Fuhad Adeyanju",
    "Full Stack Developer",
    "Mobile App Developer",
    "I wrote an <h1> tag once",
]

# --- port of scramble.ts -------------------------------------------------------
COLS = 44
FPS = 20
GLYPHS = "!<>-_\\/[]{}=+*^?#%&$@0123456789abcdefxyz"
OUT = 0.022   # seconds between columns breaking up
IN = 0.05     # seconds between columns settling
LEAD = 0.32   # seconds of pure noise before the first column settles
HOLD = 1.9    # seconds a settled phrase stays


def u32(x):
    return x & 0xFFFFFFFF


def i32(x):
    x &= 0xFFFFFFFF
    return x - 0x100000000 if x >= 0x80000000 else x


def imul(a, b):
    return i32(u32(a) * u32(b))


def mulberry32(a):
    state = [i32(a)]

    def rand():
        state[0] = i32(state[0] + 0x6D2B79F5)
        a = state[0]
        t = imul(a ^ (u32(a) >> 15), 1 | a)
        t = i32(i32(t + imul(t ^ (u32(t) >> 7), 61 | t)) ^ t)
        return u32(t ^ (u32(t) >> 14)) / 4294967296

    return rand


def build(phrases):
    lst = [p[: COLS - 4] for p in (phrases or [""])]
    rand = mulberry32(77)
    placed = [{"text": p, "x": (COLS - len(p)) // 2} for p in lst]

    at = 0.0
    steps = []
    for i, to in enumerate(placed):
        frm = placed[(i + len(placed) - 1) % len(placed)]
        lo = min(frm["x"], to["x"])
        hi = max(frm["x"] + len(frm["text"]), to["x"] + len(to["text"]))
        out, settle = [], []
        for c in range(lo, hi):
            out.append(at + (c - lo) * OUT + rand() * 0.06)
            settle.append(at + LEAD + (c - lo) * IN + rand() * 0.14)
        s = {"from": frm, "to": to, "lo": lo, "hi": hi, "out": out, "settle": settle, "start": at}
        at = max(at + LEAD, *settle) + HOLD
        s["end"] = at
        steps.append(s)
    period = at
    offset = steps[0]["end"] - 0.7

    def char_at(p, c):
        return p["text"][c - p["x"]] if p["x"] <= c < p["x"] + len(p["text"]) else " "

    def frame(t):
        """Returns a list of (char, kind) where kind is 'text', 'noise' or None."""
        now = ((t + offset) % period + period) % period
        s = next((st for st in steps if now < st["end"]), steps[0])
        tick = math.floor(now * 20)
        line = [(" ", None)] * COLS
        for c in range(COLS):
            if c < s["lo"] or c >= s["hi"]:
                continue
            k = c - s["lo"]
            a, b = char_at(s["from"], c), char_at(s["to"], c)
            if now < s["out"][k]:
                line[c] = (a, "text")
            elif now >= s["settle"][k]:
                line[c] = (b, "text")
            elif a == " " and b == " " and now < s["out"][k] + 0.12:
                line[c] = (" ", None)
            else:
                h = imul(c ^ imul(tick, 0x27D4EB2D), 0x9E3779B1)
                h = imul(h ^ (u32(h) >> 15), 0x85EBCA77)
                line[c] = (GLYPHS[u32(h ^ (u32(h) >> 13)) % len(GLYPHS)], "noise")
        return line

    return frame, period


# --- SVG ----------------------------------------------------------------------
FS = 26
CW = FS * 0.6
W = 860
HEADER_H = 34
PROMPT_H = 34
LINE_H = 56
PAD_BOTTOM = 22
H = HEADER_H + PROMPT_H + LINE_H + PAD_BOTTOM

BG = "#0b0e1c"
BAR = "#121733"
PEACH = "#f2a68b"
LILAC = "#8b95dc"
NOISE = "#5a64a8"
DIM = "#4a5287"
SOFT = "#c9cdf0"


def run_spans(line):
    """Group consecutive same-kind chars into tspans."""
    out, buf, kind = [], "", "x"
    for ch, k in line:
        k = k or "text"  # spaces can share whatever run they sit in
        if ch == " " and buf:
            buf += ch
            continue
        if k != kind and buf:
            out.append((kind, buf))
            buf = ""
        kind = k
        buf += ch
    if buf:
        out.append((kind, buf))
    return "".join(
        f'<tspan class="{"n" if k == "noise" else "t"}">{escape(txt)}</tspan>' for k, txt in out
    )


def main(path):
    frame, period = build(PHRASES)
    n = round(period * FPS)
    rendered = [run_spans(frame(i * period / n)) for i in range(n)]

    # collapse identical consecutive frames into one entry with a longer duration
    uniq, starts = [], []
    for i, f in enumerate(rendered):
        if not uniq or uniq[-1] != f:
            uniq.append(f)
            starts.append(i / n)

    line_w = COLS * CW
    x0 = (W - line_w) / 2
    y_top = HEADER_H + PROMPT_H
    base = y_top + LINE_H / 2 + FS * 0.35

    o = []
    o.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
             f'role="img" aria-label="{escape(" · ".join(PHRASES))}">')
    o.append(f'<title>{escape(" · ".join(PHRASES))}</title>')
    o.append('<defs>')
    o.append(f'<linearGradient id="g" gradientUnits="userSpaceOnUse" x1="{x0:.0f}" y1="0" x2="{x0 + line_w:.0f}" y2="0">'
             f'<stop offset="0" stop-color="{PEACH}"/><stop offset="1" stop-color="{LILAC}"/></linearGradient>')
    o.append(f'<clipPath id="win"><rect x="0" y="{y_top}" width="{W}" height="{LINE_H}"/></clipPath>')
    o.append('</defs>')
    o.append('<style>'
             'text{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono","Courier New",monospace;white-space:pre}'
             f'.s{{font-size:{FS}px;font-weight:700}}'
             '.t{fill:url(#g)}'
             f'.n{{fill:{NOISE};font-weight:400}}'
             '.p{font-size:13px}'
             '</style>')

    o.append(f'<rect width="{W}" height="{H}" rx="12" fill="{BG}"/>')
    o.append(f'<path d="M0 12a12 12 0 0 1 12-12h{W - 24}a12 12 0 0 1 12 12v{HEADER_H - 12}h-{W}z" fill="{BAR}"/>')
    for k, c in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
        o.append(f'<circle cx="{20 + k * 18}" cy="{HEADER_H / 2}" r="5.5" fill="{c}"/>')
    o.append(f'<text class="p" x="{W / 2}" y="{HEADER_H / 2 + 4.5}" text-anchor="middle" fill="{DIM}">fuhad@github: ~</text>')
    o.append(f'<text class="p" x="28" y="{HEADER_H + 24}"><tspan fill="{PEACH}">~</tspan>'
             f'<tspan fill="{LILAC}"> $ </tspan><tspan fill="{SOFT}">whoami</tspan></text>')

    o.append('<g clip-path="url(#win)"><g>')
    vals = ";".join(f"0 {-k * LINE_H}" for k in range(len(uniq)))
    times = ";".join(f"{s:.5f}".rstrip("0").rstrip(".") if s else "0" for s in starts)
    o.append(f'<animateTransform attributeName="transform" type="translate" calcMode="discrete" '
             f'values="{vals}" keyTimes="{times}" dur="{period:.3f}s" repeatCount="indefinite"/>')
    for k, spans in enumerate(uniq):
        o.append(f'<text class="s" x="{x0:.1f}" y="{base + k * LINE_H:.1f}" textLength="{line_w:.1f}" '
                 f'lengthAdjust="spacing" xml:space="preserve">{spans}</text>')
    o.append('</g></g>')
    o.append('</svg>')

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(o))
    print(f"wrote {path}: period {period:.2f}s, {n} frames, {len(uniq)} unique")


if __name__ == "__main__":
    main(sys.argv[1])
