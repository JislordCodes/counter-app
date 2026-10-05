"""Cover builder: paperback wraparound (PDF, 300 dpi, KDP template maths) and ebook front cover (JPEG 1600x2560).

Design: a deep alpine sky that fades from navy into the photograph's own sky, the Tre Cime rising in the lower half,
a large Playfair Display Black title, alpenglow-amber accents, and a quiet back cover with the book description.
All text is live type in Typst; only the sky and the photograph are raster.
"""
import io, os, sys

import numpy as np
import typst
from PIL import Image, ImageFilter

from .core import ROOT

IMG = os.path.join(ROOT, "images", "cover")
FONTS = os.path.join(ROOT, "build", "fonts")
PHOTO = os.path.join(IMG, "tre-cime-3840.jpg")

NAVY = (11, 36, 56)
NAVY2 = (21, 58, 88)
AMBER = "#f0b45b"
SPINE_PER_PAGE = 0.002252  # KDP black-and-white interior, white paper, inches per page
DPI = 300

BACK_HEAD = "Plan the Dolomites once,#linebreak()and get it right."
BACK_P1 = ("The Dolomites are as famous for reservations as for views. In 2026, the Seceda lifts, Lago di Braies by car, "
           "the Tre Cime toll road and the Alpe di Siusi road all had booking or timed-access rules in summer.")
BACK_P2 = ("This guide shows what to book, when to book it and what it costs. It then takes you through six regions "
           "with At-a-Glance boxes, honest downsides and plans for good and bad weather.")
BACK_LIST = [
    "What to reserve first, and when booking opens",
    "Real daily budgets, lift passes and hidden costs",
    "Six regions, with 16 maps and 79 photographs",
    "20 hikes, mountain huts, via ferrata and cycling",
    "Ready-to-follow itineraries for 3 to 10 days",
    "Car-free, budget and rainy-day plans",
    "Safety, rescue costs, packing lists and a pre-trip checklist",
]
BACK_NOTE = "Prices and rules are 2026 figures. Appendix C lists the official sites to check before you book."


def _grad(h, top, bot):
    t = np.linspace(0, 1, h)[:, None, None]
    a = np.array(top, dtype=np.float32)[None, None, :]
    b = np.array(bot, dtype=np.float32)[None, None, :]
    return a + (b - a) * t


def front_background(W, H, photo_frac=0.56, zoom=1.16):
    """Front panel raster (W x H px): sky gradient + photograph at the bottom, blended seamlessly."""
    ph = Image.open(PHOTO).convert("RGB")
    pw = int(W * zoom)
    phh = int(ph.height * pw / ph.width)
    ph = ph.resize((pw, phh), Image.LANCZOS)
    left = int((pw - W) * 0.50)
    ph = ph.crop((left, 0, left + W, phh))
    # make the photograph a touch richer and a little darker at the very top
    from PIL import ImageEnhance
    ph = ImageEnhance.Contrast(ph).enhance(1.07)
    ph = ImageEnhance.Color(ph).enhance(1.08)
    y0 = H - phh
    if y0 < 0:
        ph = ph.crop((0, -y0, W, phh))
        y0, phh = 0, ph.height
    arr = np.zeros((H, W, 3), dtype=np.float32)
    # sky layer: top rows of the photo stretched upward and heavily blurred, so the colour continues smoothly
    row = np.array(ph.crop((0, 0, W, 30)).resize((W, 1), Image.BILINEAR)).astype(np.float32)  # 1 x W x 3
    row = 0.72 * row.mean(axis=1, keepdims=True) + 0.28 * row
    sky = np.repeat(row, max(y0, 1), axis=0)
    sky_img = Image.fromarray(sky.astype(np.uint8)).filter(ImageFilter.GaussianBlur(max(W // 14, 40)))
    sky = np.array(sky_img).astype(np.float32)
    # darken toward the top (navy)
    t = np.linspace(0, 1, max(y0, 1))[:, None, None]
    navy = np.array(NAVY, dtype=np.float32)[None, None, :]
    k = np.clip(1.0 - t, 0, 1) ** 0.85
    sky = sky * (1 - 0.93 * k) + navy * (0.93 * k)
    arr[:y0] = sky[:y0]
    arr[y0:] = np.array(ph).astype(np.float32)
    # feather the seam between sky and photograph
    seam = 190 * H // 2775
    for i in range(seam):
        a = i / seam
        a = a * a * (3 - 2 * a)
        y = y0 + i
        if y >= H:
            break
        sky_row = sky[min(y0 - 1, max(0, y0 - 1))] if y0 > 0 else arr[y]
        arr[y] = arr[y] * a + sky_row * (1 - a)
    # darken bottom for the author line
    bt = int(H * 0.86)
    g = np.clip((np.arange(H) - bt) / max(H - bt, 1), 0, 1)[:, None, None] ** 1.4
    arr = arr * (1 - 0.62 * g) + np.array(NAVY, dtype=np.float32)[None, None, :] * (0.62 * g)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def plain_background(W, H, top=NAVY, bottom=NAVY2):
    return Image.fromarray(np.clip(_grad(H, top, bottom), 0, 255).astype(np.uint8)).resize((W, H)) if False else \
        Image.fromarray(np.clip(np.repeat(_grad(H, top, bottom), W, axis=1), 0, 255).astype(np.uint8))


# ------------------------------------------------------------------ Typst text layers
PREAMBLE = r'''
#let sans = ("Source Sans 3", "Liberation Sans")
#let display = ("Playfair Display", "Liberation Serif")
#let amber = rgb("%(amber)s")
#let peaks(w: 30pt, c: white) = box(width: w, height: w * 0.42)[
  #polygon(fill: c, (0%%, 100%%), (0%%, 55%%), (10%%, 20%%), (19%%, 55%%), (27%%, 8%%), (37%%, 52%%), (50%%, 0%%), (58%%, 40%%), (66%%, 14%%), (76%%, 55%%), (86%%, 28%%), (100%%, 70%%), (100%%, 100%%))
]
'''


def front_text(H):
    """Front-panel text laid out for a trim box 6in wide and H inches tall (9 for print, 9.6 for the ebook)."""
    k = H / 9.0
    return rf'''
#set par(justify: false, spacing: 0pt, leading: 0pt)
#align(center)[
  #v({0.78*k}in)
  #stack(dir: ltr, spacing: 9pt, line(length: 30pt, stroke: 0.9pt + amber), text(font: sans, size: 9.4pt, weight: 700, tracking: 0.42em, fill: amber)[#upper[2027 edition]], line(length: 30pt, stroke: 0.9pt + amber))
  #v({0.98*k}in)
  #text(font: display, size: 57pt, weight: 900, tracking: 0.05em, fill: white)[DOLOMITES]
  #v(11pt)
  #text(font: sans, size: 21pt, weight: 600, tracking: 0.56em, fill: white)[TRAVEL GUIDE]
  #v({0.26*k}in)
  #peaks(w: 34pt, c: amber)
  #v({0.2*k}in)
  #block(width: 4.2in)[#set par(leading: 0.55em)
    #text(font: display, size: 14.4pt, style: "italic", fill: rgb("#e7eef3"))[Plan Your Trip to Italy's Dolomites]]
  #v(9pt)
  #text(font: sans, size: 8.6pt, weight: 600, tracking: 0.2em, fill: rgb("#c9d8e2"))[#upper[Reservations · Costs · Hikes · Itineraries · Maps]]
]
'''


def front_author(H):
    k = H / 9.0
    return rf'''
#align(center)[
  #text(font: sans, size: 14pt, weight: 700, tracking: 0.38em, fill: white)[DAVE VELAQUEZ]
]
'''


def seal(diam_in=0.94):
    return rf'''
#box(width: {diam_in}in, height: {diam_in}in, radius: 50%, fill: amber, stroke: 1.6pt + white, inset: 0pt)[
  #align(center + horizon)[
    #set par(leading: 0.26em)
    #text(font: sans, size: 6.2pt, weight: 700, tracking: 0.14em, fill: rgb("#0b2438"))[WITH]#linebreak()
    #text(font: display, size: 17.5pt, weight: 900, fill: rgb("#0b2438"))[16 MAPS]#linebreak()
    #text(font: sans, size: 6.1pt, weight: 700, tracking: 0.1em, fill: rgb("#0b2438"))[AND 79 PHOTOS]
  ]
]
'''


def render_print(pages, out_pdf, out_png=None):
    spine = round(pages * SPINE_PER_PAGE, 4)
    wi = 0.125 + 6 + spine + 6 + 0.125
    hi = 9.25
    W, H = int(round(wi * DPI)), int(round(hi * DPI))
    xf = 0.125 + 6 + spine  # x where the front panel starts (inches)
    # backgrounds
    bg = Image.new("RGB", (W, H))
    left_w = int(round(xf * DPI))
    bg.paste(plain_background(left_w, H, NAVY, (24, 66, 98)), (0, 0))
    front = front_background(W - left_w, H, photo_frac=0.56)
    bg.paste(front, (left_w, 0))
    # blend the spine/back gradient into the front so the sky is continuous at the fold
    path_bg = os.path.join(IMG, "wrap-bg.png")
    bg.save(path_bg, dpi=(DPI, DPI))
    spine_x = 0.125 + 6
    back_x = 0.125 + 0.62
    back_w = 6 - 1.24
    items = "\n".join(
        f'  #grid(columns: (14pt, 1fr), column-gutter: 0pt, text(fill: amber, size: 9.6pt)[#sym.diamond.filled], text(size: 10.6pt)[{t}])\n  #v(4.6pt)'
        for t in BACK_LIST)
    typ = PREAMBLE % dict(amber=AMBER) + rf'''
#set page(width: {wi}in, height: {hi}in, margin: 0pt)
#set text(font: sans, fill: white, lang: "en", region: "gb")
#image("/images/cover/wrap-bg.png", width: {wi}in, height: {hi}in)

// ---------------- front (trim box starts at x = {xf}in, y = 0.125in)
#place(top + left, dx: {xf}in, dy: 0.125in)[
  #box(width: 6in, height: 9in)[
    {front_text(9.0)}
  ]
]
#place(top + left, dx: {xf + 4.8}in, dy: 4.82in)[{seal()}]
#place(top + left, dx: {xf}in, dy: 8.28in)[#box(width: 6in)[{front_author(9.0)}]]

// ---------------- spine
#place(top + left, dx: {spine_x}in, dy: 0pt)[
  #box(width: {spine}in, height: {hi}in)[
    #align(center + horizon)[
      #rotate(90deg, reflow: true)[
        #box(width: 7.9in)[
          #grid(columns: (1fr, auto), align: (left + horizon, right + horizon),
            text(font: display, size: {min(17.0, spine*72*0.5):.1f}pt, weight: 900, tracking: 0.07em, fill: white)[DOLOMITES#h(9pt)#text(font: sans, size: {min(10.0, spine*72*0.3):.1f}pt, weight: 600, tracking: 0.3em)[TRAVEL GUIDE]#h(9pt)#text(font: display, size: {min(14.0, spine*72*0.4):.1f}pt, weight: 400, fill: amber)[2027]],
            text(font: sans, size: {min(9.5, spine*72*0.27):.1f}pt, weight: 700, tracking: 0.26em, fill: white)[DAVE VELAQUEZ])
        ]
      ]
    ]
  ]
]

// ---------------- back
#place(top + left, dx: {back_x}in, dy: 0.9in)[
  #box(width: {back_w}in)[
    #set par(justify: false, leading: 0.52em)
    #text(font: display, size: 21.5pt, weight: 700, fill: white)[{BACK_HEAD}]
    #v(7pt)
    #line(length: 38pt, stroke: 1.6pt + amber)
    #v(11pt)
    #set text(size: 11pt, fill: rgb("#e7eef3"))
    #set par(justify: true, leading: 0.58em, spacing: 0.95em)
    {BACK_P1}

    {BACK_P2}
    #v(5pt)
    #text(font: sans, size: 8.2pt, weight: 700, tracking: 0.22em, fill: amber)[INSIDE]
    #v(5pt)
{items}
    #v(6pt)
    #text(size: 9pt, style: "italic", fill: rgb("#b7c9d6"))[{BACK_NOTE}]
  ]
]
// keep-clear area for the KDP barcode (lower corners of the back cover)
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
    bg = front_background(W, H, photo_frac=0.5)
    bg.save(os.path.join(IMG, "ebook-bg.png"))
    typ = PREAMBLE % dict(amber=AMBER) + rf'''
#set page(width: 6in, height: {hi}in, margin: 0pt)
#set text(font: sans, fill: white, lang: "en", region: "gb")
#image("/images/cover/ebook-bg.png", width: 6in, height: {hi}in)
#place(top + left)[#box(width: 6in, height: {hi}in)[{front_text(hi)}]]
#place(top + left, dx: 4.8in, dy: 5.46in)[{seal()}]
#place(top + left, dx: 0pt, dy: {hi - 0.78}in)[#box(width: 6in)[{front_author(hi)}]]
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


if __name__ == "__main__":
    pages = int(sys.argv[1]) if len(sys.argv) > 1 else 229
    os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
    print(render_print(pages, os.path.join(ROOT, "dist", "draft-cover.pdf"), os.path.join(IMG, "preview")))
    print(render_ebook(os.path.join(ROOT, "dist", "draft-ebook-cover.jpg")))
