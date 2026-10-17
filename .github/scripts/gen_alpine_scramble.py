"""Put the scramble decode text inside the alpine dawn banner, as one animated SVG.

The GIF is embedded as a data URI (an SVG shown as a README image can't load
external files), and the scramble frames from gen_scramble.py play on top of it.

Usage: python gen_alpine_scramble.py <alpine-dawn.gif> <output.svg>
"""
import base64
import io
import sys
from xml.sax.saxutils import escape

import gen_scramble as sc

sc.COLS = 28  # longest phrase is 24 chars; less padding lets the text run larger

CROP = (40, 440)   # rows of the 1280x640 scene to keep: summits down to the top of the reflection
W, H = 1280, CROP[1] - CROP[0]
FS = 46
CW = FS * 0.6
LINE_H = 70
CY = 393 - CROP[0]  # vertical centre of the text: the dark far treeline
NOISE = "#7781c4"


def crop_gif(path):
    """Crop every frame to CROP, keeping timing and the scene's exact colours."""
    from PIL import Image, ImageSequence

    src = Image.open(path)
    frames, durs = [], []
    for fr in ImageSequence.Iterator(src):
        frames.append(fr.convert("RGB").crop((0, CROP[0], W, CROP[1])))
        durs.append(fr.info.get("duration", 70))
    colours = sorted({c for f in frames for _, c in f.getcolors(1 << 16)})
    assert len(colours) <= 255, len(colours)
    index = {c: i for i, c in enumerate(colours)}
    clear = len(colours)  # extra palette slot: "unchanged since the last frame"
    palette = [v for c in colours for v in c] + [0, 0, 0] * (256 - len(colours))

    # Store only the pixels that change, like the original encoder did; the rest
    # are transparent over the frame before (disposal 1 keeps it).
    out, prev = [], None
    for f in frames:
        px = [index[c] for c in f.get_flattened_data()] if hasattr(f, "get_flattened_data") else [index[c] for c in f.getdata()]
        data = px if prev is None else [clear if a == b else a for a, b in zip(px, prev)]
        im = Image.new("P", f.size)
        im.putpalette(palette)
        im.putdata(data)
        out.append(im)
        prev = px
    buf = io.BytesIO()
    out[0].save(buf, "GIF", save_all=True, append_images=out[1:], duration=durs, loop=0,
                transparency=clear, disposal=1, optimize=False)
    return buf.getvalue()


def main(gif_path, out_path):
    gif = base64.b64encode(crop_gif(gif_path)).decode()
    frame, period = sc.build(sc.PHRASES)
    n = round(period * sc.FPS)
    rendered = [sc.run_spans(frame(i * period / n)) for i in range(n)]
    uniq, starts = [], []
    for i, f in enumerate(rendered):
        if not uniq or uniq[-1] != f:
            uniq.append(f)
            starts.append(i / n)

    line_w = sc.COLS * CW
    x0 = (W - line_w) / 2
    y_top = CY - LINE_H / 2
    base = CY + FS * 0.35
    label = escape(" · ".join(sc.PHRASES))

    o = []
    o.append(f'<svg xmlns="http://www.w3.org/2000/svg" '
             f'viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{label}">')
    o.append(f'<title>{label}</title>')
    o.append('<defs>')
    o.append(f'<linearGradient id="g" gradientUnits="userSpaceOnUse" x1="{x0:.0f}" y1="0" x2="{x0 + line_w:.0f}" y2="0">'
             f'<stop offset="0" stop-color="{sc.PEACH}"/><stop offset=".5" stop-color="#ffd0b0"/>'
             f'<stop offset="1" stop-color="{sc.LILAC}"/></linearGradient>')
    o.append(f'<radialGradient id="shade" cx=".5" cy=".5" r=".5">'
             f'<stop offset="0" stop-color="#05070f" stop-opacity=".78"/>'
             f'<stop offset=".6" stop-color="#05070f" stop-opacity=".45"/>'
             f'<stop offset="1" stop-color="#05070f" stop-opacity="0"/></radialGradient>')
    o.append(f'<filter id="glow" filterUnits="userSpaceOnUse" x="0" y="{y_top - 20}" width="{W}" height="{LINE_H + 40}">'
             '<feGaussianBlur in="SourceGraphic" stdDeviation="6" result="b"/>'
             '<feColorMatrix in="b" type="matrix" values="1 0 0 0 0  0 .75 0 0 0  0 0 .7 0 0  0 0 0 .55 0" result="c"/>'
             '<feMerge><feMergeNode in="c"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
    o.append(f'<clipPath id="win"><rect x="0" y="{y_top}" width="{W}" height="{LINE_H}"/></clipPath>')
    o.append('</defs>')
    o.append('<style>'
             'text{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono","Courier New",monospace;white-space:pre}'
             f'.s{{font-size:{FS}px;font-weight:700}}'
             '.t{fill:url(#g)}'
             f'.n{{fill:{NOISE};font-weight:400}}'
             '</style>')

    o.append(f'<image width="{W}" height="{H}" href="data:image/gif;base64,{gif}"/>')
    # a soft pool of shadow on the water so the text reads over the reflections
    o.append(f'<ellipse cx="{W / 2}" cy="{CY}" rx="{line_w * 0.62:.0f}" ry="{LINE_H * 0.95:.0f}" fill="url(#shade)"/>')

    o.append('<g clip-path="url(#win)"><g filter="url(#glow)"><g>')
    vals = ";".join(f"0 {-k * LINE_H}" for k in range(len(uniq)))
    times = ";".join(f"{s:.5f}".rstrip("0").rstrip(".") if s else "0" for s in starts)
    o.append(f'<animateTransform attributeName="transform" type="translate" calcMode="discrete" '
             f'values="{vals}" keyTimes="{times}" dur="{period:.3f}s" repeatCount="indefinite"/>')
    for k, spans in enumerate(uniq):
        o.append(f'<text class="s" x="{x0:.1f}" y="{base + k * LINE_H:.1f}" textLength="{line_w:.1f}" '
                 f'lengthAdjust="spacing" xml:space="preserve">{spans}</text>')
    o.append('</g></g></g>')
    o.append('</svg>')

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(o))
    print(f"wrote {out_path}: period {period:.2f}s, {len(uniq)} unique frames")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
