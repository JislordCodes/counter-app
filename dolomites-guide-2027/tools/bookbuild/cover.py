"""Cover builder: paperback wraparound (PDF, 300 dpi, built to KDP's own cover-template geometry) and the ebook front cover.

Geometry comes from the template that KDP's cover calculator produces (PAPERBACK 6 x 9 in, black and white, white paper):
  page          = 0.125 bleed + 6 back + spine + 6 front + 0.125 bleed  by  9.25 in
  spine         = pages x 0.002252 in
  live area     = 0.125 in inside the trim; nothing readable within 0.125 in of the spine fold
  spine text    = 0.0625 in clear on each side of the text
  barcode area  = 2.0 x 1.2 in, x 3.875-5.875 in, y 7.675-8.875 in (page coordinates, lower right of the back cover)

All text is live type in Typst; only the sky and the photograph are raster.
"""
import os, sys

import numpy as np
import typst
from PIL import Image, ImageEnhance, ImageFilter

from .core import ROOT

IMG = os.path.join(ROOT, "images", "cover")
FONTS = os.path.join(ROOT, "build", "fonts")
PHOTO = os.path.join(IMG, "tre-cime-3840.jpg")

AUTHOR = "Dave Velaquez"
NAVY = (9, 30, 62)
NAVY2 = (20, 52, 98)
GOLD = "#f2c14e"
SPINE_PER_PAGE = 0.002252  # KDP black-and-white interior, white paper, inches per page
DPI = 300
BLEED = 0.125
BARCODE = (3.875, 7.675, 5.875, 8.875)  # x0, y0, x1, y1 in page inches (KDP template)

BACK_HEAD_1 = "Plan the Dolomites once,"
BACK_HEAD_2 = "and get it right."
BACK_P1 = ("The Dolomites are as famous for reservations as for views. In 2026, the Seceda lifts, Lago di Braies by car, "
           "the Tre Cime toll road and the Alpe di Siusi road all had booking or timed-access rules in summer. "
           "Arrive without a plan and you can lose a day, or a viewpoint.")
BACK_P2 = ("This guide shows what to book, when to book it and what it costs. It then takes you through six regions "
           "with At-a-Glance boxes, honest downsides and plans for good and bad weather.")
BACK_LIST = [
    ("cal", "What to reserve first, and when booking opens"),
    ("coins", "Real daily budgets, lift passes and hidden costs"),
    ("map", "Six regions, with 16 maps and 79 photographs"),
    ("hike", "20 hikes, mountain huts, via ferrata and cycling"),
    ("route", "Ready-to-follow itineraries for 3 to 10 days"),
    ("bus", "Car-free, budget and rainy-day plans"),
    ("shield", "Safety, rescue costs, packing lists and a pre-trip checklist"),
]
BACK_NOTE = "Prices and rules are 2026 figures. Appendix C lists the official sites to check before you book."
BACK_BLURB = f"{AUTHOR} writes practical travel guides built around one idea: a good trip starts with a clear plan."


def _grad(h, top, bot):
    t = np.linspace(0, 1, h)[:, None, None]
    a = np.array(top, dtype=np.float32)[None, None, :]
    b = np.array(bot, dtype=np.float32)[None, None, :]
    return a + (b - a) * t


# ------------------------------------------------------------------ raster backgrounds
def front_background(W, H, zoom=1.16):
    """Front panel raster (W x H px): sky gradient + photograph at the bottom, blended seamlessly."""
    ph = Image.open(PHOTO).convert("RGB")
    pw = int(W * zoom)
    phh = int(ph.height * pw / ph.width)
    ph = ph.resize((pw, phh), Image.LANCZOS)
    left = int((pw - W) * 0.50)
    ph = ph.crop((left, 0, left + W, phh))
    ph = ImageEnhance.Contrast(ph).enhance(1.08)
    ph = ImageEnhance.Color(ph).enhance(1.12)
    y0 = H - phh
    if y0 < 0:
        ph = ph.crop((0, -y0, W, phh))
        y0, phh = 0, ph.height
    arr = np.zeros((H, W, 3), dtype=np.float32)
    row = np.array(ph.crop((0, 0, W, 30)).resize((W, 1), Image.BILINEAR)).astype(np.float32)
    row = 0.72 * row.mean(axis=1, keepdims=True) + 0.28 * row
    sky = np.repeat(row, max(y0, 1), axis=0)
    sky_img = Image.fromarray(sky.astype(np.uint8)).filter(ImageFilter.GaussianBlur(max(W // 14, 40)))
    sky = np.array(sky_img).astype(np.float32)
    t = np.linspace(0, 1, max(y0, 1))[:, None, None]
    navy = np.array(NAVY, dtype=np.float32)[None, None, :]
    k = np.clip(1.0 - t, 0, 1) ** 0.8
    sky = sky * (1 - 0.95 * k) + navy * (0.95 * k)
    arr[:y0] = sky[:y0]
    arr[y0:] = np.array(ph).astype(np.float32)
    seam = 190 * H // 2775
    for i in range(seam):
        a = i / seam
        a = a * a * (3 - 2 * a)
        y = y0 + i
        if y >= H:
            break
        sky_row = sky[min(y0 - 1, max(0, y0 - 1))] if y0 > 0 else arr[y]
        arr[y] = arr[y] * a + sky_row * (1 - a)
    bt = int(H * 0.84)  # darken the foot of the cover so the author line reads
    g = np.clip((np.arange(H) - bt) / max(H - bt, 1), 0, 1)[:, None, None] ** 1.3
    arr = arr * (1 - 0.66 * g) + np.array(NAVY, dtype=np.float32)[None, None, :] * (0.66 * g)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def back_background(W, H):
    """Back and spine panel: navy gradient with a faint ghost of the same mountains at lower left (kept off the barcode area)."""
    base = np.clip(np.repeat(_grad(H, NAVY, NAVY2), W, axis=1), 0, 255).astype(np.float32)
    ph = Image.open(PHOTO).convert("RGB")
    pw = int(W * 1.45)
    phh = int(ph.height * pw / ph.width)
    ph = ph.resize((pw, phh), Image.LANCZOS).crop((0, 0, W, phh))
    ph = ImageEnhance.Color(ph).enhance(0.8)
    arr = np.array(ph).astype(np.float32) * 0.62
    h2 = min(phh, int(H * 0.40))
    arr = arr[phh - h2:]
    yy = np.linspace(0, 1, h2)[:, None]
    xx = np.linspace(0, 1, W)[None, :]
    alpha = np.clip(yy ** 1.6, 0, 1) * 0.42 * np.clip((0.60 - xx) / 0.22, 0, 1)
    base[H - h2:] = base[H - h2:] * (1 - alpha[..., None]) + arr * alpha[..., None]
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))


# ------------------------------------------------------------------ Typst text layers
PREAMBLE = r'''
#let sans = ("Source Sans 3", "Liberation Sans")
#let serif = ("EB Garamond", "Liberation Serif")
#let display = ("Playfair Display", "Liberation Serif")
#let gold = rgb("%(gold)s")
#let goldg = gradient.linear(rgb("#fbe7a6"), rgb("#efbf49"), rgb("#c98b21"), angle: 90deg)
#let ivory = rgb("#f6f1e3")
#let peaks(w: 30pt, c: gold) = box(width: w, height: w * 0.42)[
  #polygon(fill: c, (0%%, 100%%), (0%%, 55%%), (10%%, 20%%), (19%%, 55%%), (27%%, 8%%), (37%%, 52%%), (50%%, 0%%), (58%%, 40%%), (66%%, 14%%), (76%%, 55%%), (86%%, 28%%), (100%%, 70%%), (100%%, 100%%))
]
#let ico(n, h: 11pt) = image("/images/cover/icons/" + n + ".svg", height: h)
'''


def front_layers(H):
    """Front panel, laid out for a trim box 6 in wide and H in tall (9 for print, 9.6 for the ebook)."""
    k = H / 9.0
    items = [("cal", "Reservations"), ("coins", "Costs"), ("hike", "Hikes"), ("route", "Itineraries"), ("map", "Maps")]
    cells = []
    for i, (ic, lab) in enumerate(items):
        if i:
            cells.append('line(angle: 90deg, length: 11pt, stroke: 0.6pt + rgb("#f2c14e99"))')
        cells.append(f'grid(columns: 2, column-gutter: 3.4pt, align: horizon, ico("{ic}", h: 10.5pt), text(font: sans, size: 7.5pt, weight: 600, tracking: 0.1em, fill: ivory)[#upper[{lab}]])')
    row = ",\n      ".join(cells)
    return rf'''
#set par(justify: false, spacing: 0pt, leading: 0pt)
#place(top + center, dy: {0.62*k}in)[
  #grid(columns: (1.4in, auto, 1.4in), column-gutter: 11pt, align: horizon, line(length: 100%, stroke: 0.9pt + gold), peaks(w: 38pt), line(length: 100%, stroke: 0.9pt + gold))
]
#place(top + center, dy: {1.08*k}in)[#text(font: display, size: 57pt, weight: 900, tracking: 0.03em, fill: goldg)[DOLOMITES]]
#place(top + center, dy: {2.02*k}in)[#text(font: display, size: 34pt, weight: 900, tracking: 0.07em, fill: white)[TRAVEL GUIDE]]
#place(top + center, dy: {2.74*k}in)[
  #grid(columns: (1.3in, auto, 1.3in), column-gutter: 13pt, align: horizon, line(length: 100%, stroke: 0.9pt + gold), text(font: display, size: 30pt, weight: 700, tracking: 0.12em, fill: goldg)[2027], line(length: 100%, stroke: 0.9pt + gold))
]
#place(top + center, dy: {3.33*k}in)[#text(font: serif, size: 16pt, style: "italic", fill: ivory)[Plan Your Trip to Italy's Dolomites]]
#place(top + center, dy: {3.82*k}in)[
  #grid(columns: {len(cells)}, column-gutter: 7pt, align: horizon,
      {row})
]
#place(top + left, dx: 4.46in, dy: {4.78*k}in)[{seal(1.1)}]
#place(top + center, dy: {H - 0.92}in)[
  #grid(columns: (0.95in, auto, 0.95in), column-gutter: 12pt, align: horizon, line(length: 100%, stroke: 0.8pt + gold), text(font: display, size: 14.5pt, weight: 600, tracking: 0.3em, fill: white)[{AUTHOR.upper()}], line(length: 100%, stroke: 0.8pt + gold))
]
'''


def seal(d=1.1):
    return rf'''
#box(width: {d}in, height: {d}in)[
  #place(center + horizon, circle(radius: {d/2}in, fill: gradient.linear(rgb("#f8d675"), rgb("#e3a82f"), angle: 90deg), stroke: 1.4pt + rgb("#fff3c9")))
  #place(center + horizon, circle(radius: {d/2 - 0.06}in, stroke: (paint: rgb("#7a5412"), thickness: 0.6pt, dash: "dotted")))
  #align(center + horizon)[
    #set par(leading: 0.22em)
    #text(font: serif, size: 9pt, style: "italic", fill: rgb("#0b1f3f"))[with]#linebreak()
    #text(font: display, size: 13.2pt, weight: 900, fill: rgb("#0b1f3f"))[16 MAPS]#linebreak()
    #text(font: serif, size: 8.5pt, style: "italic", fill: rgb("#0b1f3f"))[and]#linebreak()
    #text(font: display, size: 9.4pt, weight: 900, fill: rgb("#0b1f3f"))[79 PHOTOS]
  ]
]
'''


def back_layers(spine):
    items = "\n".join(
        f'  #grid(columns: (22pt, 1fr), column-gutter: 3pt, align: horizon, ico("{ic}", h: 12.5pt), text(font: serif, size: 11.4pt, fill: ivory)[{t}])\n  #v(6.6pt)'
        for ic, t in BACK_LIST)
    return rf'''
#set par(justify: false, spacing: 0pt, leading: 0pt)
// back trim box: 6 x 9 in; content column 0.55 in from the left trim and 0.65 in from the spine fold
#place(top + left, dx: 0.55in, dy: 0.62in)[
  #box(width: 4.8in)[
    #grid(columns: (1fr, auto, 1fr), column-gutter: 10pt, align: horizon, line(length: 100%, stroke: 0.8pt + gold), peaks(w: 30pt), line(length: 100%, stroke: 0.8pt + gold))
    #v(24pt)
    #align(center)[#set par(leading: 0.46em)
      #text(font: display, size: 25.5pt, weight: 700, fill: white)[{BACK_HEAD_1}]#linebreak()
      #text(font: display, size: 28pt, weight: 700, style: "italic", fill: goldg)[{BACK_HEAD_2}]]
    #v(17pt)
    #set par(justify: false, leading: 0.5em, spacing: 0.85em)
    #text(font: serif, size: 11.7pt, fill: ivory)[{BACK_P1}]

    #text(font: serif, size: 11.7pt, fill: ivory)[{BACK_P2}]
    #v(12pt)
    #grid(columns: (1fr, auto, 1fr), column-gutter: 9pt, align: horizon, line(length: 100%, stroke: 0.8pt + gold), text(font: sans, size: 9.4pt, weight: 700, tracking: 0.22em, fill: gold)[INSIDE YOU'LL FIND], line(length: 100%, stroke: 0.8pt + gold))
    #v(11pt)
{items}
    #v(3pt)
    #line(length: 100%, stroke: 0.7pt + rgb("#f2c14e88"))
    #v(6pt)
    #text(font: serif, size: 9.8pt, style: "italic", fill: rgb("#c9d6e6"))[{BACK_NOTE}]
  ]
]
// author block, bottom left (clear of the barcode area)
#place(top + left, dx: 0.55in, dy: 7.62in)[
  #box(width: 2.95in)[
    #grid(columns: (auto, 1fr), column-gutter: 9pt, align: horizon, peaks(w: 30pt), text(font: display, size: 12pt, weight: 600, tracking: 0.26em, fill: white)[{AUTHOR.upper()}])
    #v(5pt)
    #line(length: 100%, stroke: 0.7pt + gold)
    #v(6pt)
    #set par(leading: 0.46em)
    #text(font: serif, size: 10.2pt, fill: ivory)[{BACK_BLURB}]
  ]
]
'''


def spine_layer(spine):
    sz_t = min(17.0, spine * 72 * 0.46)
    sz_s = min(9.6, spine * 72 * 0.27)
    sz_y = min(14.0, spine * 72 * 0.38)
    return rf'''
#box(width: {spine}in, height: 8.1in)[
  #align(center + horizon)[
    #rotate(90deg, reflow: true)[
      #box(width: 8.1in)[
        #grid(columns: (1fr, auto), align: (left + horizon, right + horizon),
          text(font: display, size: {sz_t:.1f}pt, weight: 900, tracking: 0.07em, fill: goldg)[DOLOMITES#h(10pt)#text(font: sans, size: {sz_s + 0.4:.1f}pt, weight: 600, tracking: 0.3em, fill: white)[TRAVEL GUIDE]#h(10pt)#text(font: display, size: {sz_y:.1f}pt, weight: 700, fill: gold)[2027]],
          text(font: display, size: {sz_s + 0.5:.1f}pt, weight: 600, tracking: 0.24em, fill: white)[{AUTHOR.upper()}])
      ]
    ]
  ]
]
'''


def render_print(pages, out_pdf, out_png=None):
    spine = round(pages * SPINE_PER_PAGE, 4)
    wi = BLEED + 6 + spine + 6 + BLEED
    hi = 9.25
    W, H = int(round(wi * DPI)), int(round(hi * DPI))
    xf = BLEED + 6 + spine   # page x where the front trim box starts
    left_w = int(round(xf * DPI))
    bg = Image.new("RGB", (W, H))
    bg.paste(back_background(left_w, H), (0, 0))
    bg.paste(front_background(W - left_w, H), (left_w, 0))
    os.makedirs(IMG, exist_ok=True)
    bg.save(os.path.join(IMG, "wrap-bg.png"), dpi=(DPI, DPI))
    typ = PREAMBLE % dict(gold=GOLD) + rf'''
#set page(width: {wi}in, height: {hi}in, margin: 0pt)
#set text(font: sans, fill: white, lang: "en", region: "gb")
#image("/images/cover/wrap-bg.png", width: {wi}in, height: {hi}in)

// front trim box (x = {xf:.4f} in, y = 0.125 in)
#place(top + left, dx: {xf}in, dy: {BLEED}in)[#box(width: 6in, height: 9in)[{front_layers(9.0)}]]
// back trim box (x = 0.125 in, y = 0.125 in)
#place(top + left, dx: {BLEED}in, dy: {BLEED}in)[#box(width: 6in, height: 9in)[{back_layers(spine)}]]
// spine
#place(top + left, dx: {BLEED + 6}in, dy: {BLEED + 0.45}in)[{spine_layer(spine)}]
// barcode area x {BARCODE[0]}-{BARCODE[2]} in, y {BARCODE[1]}-{BARCODE[3]} in is left clear on purpose: KDP prints the ISBN barcode here
'''
    path = os.path.join(ROOT, "build", "cover-print.typ")
    open(path, "w", encoding="utf-8").write(typ)
    typst.compile(path, output=out_pdf, root=ROOT, font_paths=[FONTS])
    if out_png:
        typst.compile(path, output=out_png, root=ROOT, font_paths=[FONTS], format="png", ppi=100)
    return dict(spine=spine, width_in=wi, height_in=hi, px=(W, H))


def render_ebook(out_jpg):
    W, H = 1600, 2560
    hi = 9.6
    bg = front_background(W, H)
    bg.save(os.path.join(IMG, "ebook-bg.png"))
    typ = PREAMBLE % dict(gold=GOLD) + rf'''
#set page(width: 6in, height: {hi}in, margin: 0pt)
#set text(font: sans, fill: white, lang: "en", region: "gb")
#image("/images/cover/ebook-bg.png", width: 6in, height: {hi}in)
#place(top + left)[#box(width: 6in, height: {hi}in)[{front_layers(hi)}]]
'''
    path = os.path.join(ROOT, "build", "cover-ebook.typ")
    open(path, "w", encoding="utf-8").write(typ)
    png = os.path.join(IMG, "ebook-cover.png")
    typst.compile(path, output=png, root=ROOT, font_paths=[FONTS], format="png", ppi=1600 / 6)
    im = Image.open(png).convert("RGB")
    if im.size != (W, H):
        im = im.resize((W, H), Image.LANCZOS)
    im.save(out_jpg, quality=93, dpi=(300, 300), optimize=True, subsampling=0)
    return im.size


# ------------------------------------------------------------------ verification against the KDP template geometry
def verify_wrap(pdf, pages):
    """Check the finished wrap against KDP's template rules. Returns (problems, facts)."""
    import pymupdf
    spine = round(pages * SPINE_PER_PAGE, 4)
    wi = BLEED + 6 + spine + 6 + BLEED
    d = pymupdf.open(pdf)
    pg = d[0]
    problems, facts = [], {}
    r = pg.rect
    facts["page_in"] = (round(r.width / 72, 4), round(r.height / 72, 4))
    if len(d) != 1:
        problems.append(f"{len(d)} pages (must be 1)")
    if abs(r.width / 72 - wi) > 0.005 or abs(r.height / 72 - 9.25) > 0.005:
        problems.append(f"page {r.width/72:.4f} x {r.height/72:.4f} in, expected {wi:.4f} x 9.25")
    trim_l, trim_r, trim_t, trim_b = BLEED, wi - BLEED, BLEED, 9.25 - BLEED
    fold_l, fold_r = BLEED + 6, BLEED + 6 + spine
    live = 0.125
    worst = dict(back_front_edge=9, spine_fold=9, spine_side=9)
    nsp = 0
    for b in pg.get_text("dict")["blocks"]:
        if b.get("type") != 0:
            continue
        for ln in b["lines"]:
            for s in ln["spans"]:
                if not s["text"].strip():
                    continue
                x0, y0, x1, y1 = [v / 72 for v in s["bbox"]]
                txt = s["text"][:30]
                if s["size"] < 7:
                    problems.append(f"text under 7 pt: {txt!r} ({s['size']:.1f} pt)")
                in_spine = x0 >= fold_l - 0.02 and x1 <= fold_r + 0.02
                if in_spine:
                    nsp += 1
                    gap = min(x0 - fold_l, fold_r - x1)
                    worst["spine_side"] = min(worst["spine_side"], gap)
                    if gap < 0.0625:
                        problems.append(f"spine text closer than 0.0625 in to the fold: {txt!r} ({gap:.3f} in)")
                    if y0 < trim_t + live or y1 > trim_b - live:
                        problems.append(f"spine text outside the live area vertically: {txt!r}")
                else:
                    e = min(x0 - trim_l, trim_r - x1, y0 - trim_t, trim_b - y1) if (x1 <= fold_l or x0 >= fold_r) else -1
                    worst["back_front_edge"] = min(worst["back_front_edge"], e)
                    if e < live:
                        problems.append(f"text inside the trim safety margin: {txt!r} ({e:.3f} in)")
                    fold = (fold_l - x1) if x1 <= fold_l else (x0 - fold_r)
                    worst["spine_fold"] = min(worst["spine_fold"], fold)
                    if fold < live:
                        problems.append(f"text within 0.125 in of the spine fold: {txt!r} ({fold:.3f} in)")
                bx0, by0, bx1, by1 = BARCODE
                if x0 < bx1 and x1 > bx0 and y0 < by1 and y1 > by0:
                    problems.append(f"text overlaps the barcode area: {txt!r}")
    facts.update({k: round(v, 3) for k, v in worst.items()}, spine_in=spine, spine_text_spans=nsp)
    fonts = {f[3].split("+")[-1] for f in pg.get_fonts() if f[1] in ("n/a", "")}
    if fonts:
        problems.append(f"fonts not embedded: {sorted(fonts)}")
    # background must reach the page edge (full bleed)
    full = False
    for img in pg.get_images(full=True):
        for ir in pg.get_image_rects(img[0]):
            if ir.x0 <= 0.5 and ir.y0 <= 0.5 and ir.x1 >= r.width - 0.5 and ir.y1 >= r.height - 0.5:
                full = True
    if not full:
        problems.append("background image does not cover the full page including bleed")
    return problems, facts


def draw_guides(pdf, pages, out_png, ppi=100):
    """Overlay KDP's guide rectangles (bleed, trim, live area, spine, barcode) on the wrap and save a PNG for review."""
    import pymupdf
    spine = round(pages * SPINE_PER_PAGE, 4)
    wi = BLEED + 6 + spine + 6 + BLEED
    d = pymupdf.open(pdf)
    pg = d[0]
    s = 72

    def R(x0, y0, x1, y1):
        return pymupdf.Rect(x0 * s, y0 * s, x1 * s, y1 * s)
    pg.draw_rect(R(*BARCODE), color=None, fill=(1, 1, 0), fill_opacity=0.55)
    pg.draw_rect(R(BLEED + 6 - 0.125, 0, BLEED + 6 + spine + 0.125, 9.25), color=None, fill=(1, 0.4, 0.4), fill_opacity=0.18)
    pg.draw_rect(R(BLEED, BLEED, wi - BLEED, 9.25 - BLEED), color=(0, 0, 0), width=1.2)
    pg.draw_rect(R(BLEED + 0.125, BLEED + 0.125, wi - BLEED - 0.125, 9.25 - BLEED - 0.125), color=(0.1, 0.8, 0.2), width=0.8, dashes="[3 3] 0")
    for x in (BLEED + 6, BLEED + 6 + spine):
        pg.draw_line((x * s, 0), (x * s, 9.25 * s), color=(0.2, 0.5, 1), width=1.0, dashes="[4 3] 0")
    pg.get_pixmap(dpi=ppi).save(out_png)


if __name__ == "__main__":
    pages = int(sys.argv[1]) if len(sys.argv) > 1 else 216
    os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
    print(render_print(pages, os.path.join(ROOT, "dist", "draft-cover.pdf"), os.path.join(IMG, "preview")))
    print(render_ebook(os.path.join(ROOT, "dist", "draft-ebook-cover.jpg")))
