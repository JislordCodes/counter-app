"""Paperback wrap built from the author's own supplied front and back artwork, on KDP's cover-template geometry.

The artwork is never cropped or stretched: each image is scaled (uniformly) to the 9 in trim height and centred on its
6 in trim box, so every piece of lettering in it keeps its shape and nothing readable can be cut off. The thin margins
that are left (outer bleed, the gap beside the spine, the spine itself) are filled by mirroring the artwork's own edge
or by a smooth blend of the two edges. Only the spine lettering is added as live text.
"""
import os

import numpy as np
import typst
from PIL import Image, ImageFilter

from .core import ROOT
from .cover import BARCODE, BLEED, DPI, FONTS, GOLD, IMG, PREAMBLE, SPINE_PER_PAGE

ART_FRONT = os.path.join(IMG, "art-front.webp")
ART_BACK = os.path.join(IMG, "art-back.webp")
ART_BACK_BOX = (691, 1398, 929, 1518)  # the white barcode placeholder drawn into the back artwork (x0, y0, x1, y1 px)
SPINE_AUTHOR = "David Rakitic"          # must read the same as the name on the supplied front cover


def _scale_to_height(im, h_px):
    return im.resize((int(round(im.width * h_px / im.height)), h_px), Image.LANCZOS)


def _remove_barcode_box(arr):
    """Paint over the white placeholder with texture from just above it (KDP prints its own barcode box there)."""
    x0, y0, x1, y1 = ART_BACK_BOX
    x0, y0, x1, y1 = x0 - 3, y0 - 3, x1 + 3, y1 + 3
    h = y1 - y0
    arr[y0:y1, x0:x1] = arr[y0 - h:y0, x0:x1][::-1]
    return arr


def compose(pages):
    spine = round(pages * SPINE_PER_PAGE, 4)
    wi = BLEED + 6 + spine + 6 + BLEED
    W, H = int(round(wi * DPI)), int(round(9.25 * DPI))
    bl = int(round(BLEED * DPI))
    th = int(round(9 * DPI))
    tw = int(round(6 * DPI))
    back = Image.fromarray(_remove_barcode_box(np.array(Image.open(ART_BACK).convert("RGB"))))
    front = Image.open(ART_FRONT).convert("RGB")
    back, front = _scale_to_height(back, th), _scale_to_height(front, th)

    def vpad(im):
        return np.pad(np.array(im), ((bl, H - th - bl), (0, 0), (0, 0)), mode="reflect")
    B, F = vpad(back), vpad(front)
    x_spine_l = bl + tw
    x_front_trim = int(round((BLEED + 6 + spine) * DPI))
    xb = bl + (tw - B.shape[1]) // 2
    xf = x_front_trim + (tw - F.shape[1]) // 2
    canvas = np.zeros((H, W, 3), dtype=np.float32)
    canvas[:, xb:xb + B.shape[1]] = B
    canvas[:, xf:xf + F.shape[1]] = F
    canvas[:, :xb] = B[:, :xb][:, ::-1]                                     # outer bleed, back
    right = W - (xf + F.shape[1])
    canvas[:, xf + F.shape[1]:] = F[:, F.shape[1] - right:][:, ::-1]        # outer bleed, front
    x0, x1 = xb + B.shape[1], xf                                            # gap + spine

    def edge(a, left):
        c = a[:, :8].mean(axis=1) if left else a[:, -8:].mean(axis=1)
        im = Image.fromarray(c[:, None, :].astype(np.uint8)).filter(ImageFilter.GaussianBlur(70))
        return np.array(im)[:, 0, :].astype(np.float32)
    e0, e1 = edge(B, False), edge(F, True)
    t = np.linspace(0, 1, x1 - x0)[None, :, None]
    t = t * t * (3 - 2 * t)
    band = e0[:, None, :] * (1 - t) + e1[:, None, :] * t
    xs = np.arange(x0, x1)
    ramp = np.clip(np.minimum((xs - x0) / max(x_spine_l - x0, 1), (x1 - xs) / max(x1 - x_front_trim, 1)), 0, 1)
    ramp = (ramp * ramp * (3 - 2 * ramp))[None, :, None] * 0.55
    navy = np.array((7, 22, 52), dtype=np.float32)[None, None, :]
    canvas[:, x0:x1] = band * (1 - ramp) + navy * ramp
    img = Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8))
    return img, dict(spine=spine, width_in=wi, height_in=9.25, px=(W, H), art_x=(xb, xf), art_w=(B.shape[1], F.shape[1]))


def render_print(pages, out_pdf, out_png=None):
    img, dims = compose(pages)
    os.makedirs(IMG, exist_ok=True)
    img.save(os.path.join(IMG, "wrap-art-bg.png"), dpi=(DPI, DPI))
    spine, wi = dims["spine"], dims["width_in"]
    sz_t = min(17.0, spine * 72 * 0.46)
    sz_s = min(9.6, spine * 72 * 0.27)
    sz_y = min(14.0, spine * 72 * 0.38)
    typ = PREAMBLE % dict(gold=GOLD) + rf'''
#set page(width: {wi}in, height: 9.25in, margin: 0pt)
#set text(font: sans, fill: white, lang: "en", region: "gb")
#image("/images/cover/wrap-art-bg.png", width: {wi}in, height: 9.25in)
// spine lettering (live text), reading top to bottom, 0.0625 in or more clear of the fold on each side
#place(top + left, dx: {BLEED + 6}in, dy: {BLEED + 0.45}in)[
  #box(width: {spine}in, height: 8.1in)[
    #align(center + horizon)[
      #rotate(90deg, reflow: true)[
        #box(width: 8.1in)[
          #grid(columns: (1fr, auto), align: (left + horizon, right + horizon),
            text(font: display, size: {sz_t:.1f}pt, weight: 900, tracking: 0.07em, fill: goldg)[DOLOMITES#h(10pt)#text(font: sans, size: {sz_s + 0.4:.1f}pt, weight: 600, tracking: 0.3em, fill: white)[TRAVEL GUIDE]#h(10pt)#text(font: display, size: {sz_y:.1f}pt, weight: 700, fill: gold)[2027]],
            text(font: display, size: {sz_s + 0.5:.1f}pt, weight: 600, tracking: 0.24em, fill: white)[{SPINE_AUTHOR.upper()}])
        ]
      ]
    ]
  ]
]
// barcode area x {BARCODE[0]}-{BARCODE[2]} in, y {BARCODE[1]}-{BARCODE[3]} in is left clear on purpose: KDP prints the ISBN barcode here
'''
    path = os.path.join(ROOT, "build", "cover-print-art.typ")
    open(path, "w", encoding="utf-8").write(typ)
    typst.compile(path, output=out_pdf, root=ROOT, font_paths=[FONTS])
    if out_png:
        typst.compile(path, output=out_png, root=ROOT, font_paths=[FONTS], format="png", ppi=100)
    return dims


def art_margins(dims):
    """Measure how close the artwork's own lettering comes to KDP's lines (inches, on the wrap).

    Looks at the lettering rows only: the part above the mountains on the front (plus the gold badge) and the text
    column on the back. Gold and cream pixels are treated as lettering; clouds and sunlit rock are excluded by region."""
    out = {}
    for name, path, x_page in (("back", ART_BACK, dims["art_x"][0]), ("front", ART_FRONT, dims["art_x"][1])):
        a = np.array(Image.open(path).convert("RGB")).astype(int)
        h, w = a.shape[:2]
        r, g, b = a[..., 0], a[..., 1], a[..., 2]
        gold = (r > 200) & (g > 150) & (b < 140) & (r - b > 90)
        cream = (r > 225) & (g > 215) & (b > 190) & (abs(r - b) < 45)
        m = np.zeros((h, w), bool)
        if name == "front":
            m[: int(h * 0.368)] = gold[: int(h * 0.368)]                 # title block and icon row
            y0, y1 = int(h * 0.37), int(h * 0.505)                        # gold badge
            badge = (r > 230) & (g > 190) & (b < 120)
            m[y0:y1, int(w * 0.70):] |= badge[y0:y1, int(w * 0.70):]
            y0, y1 = int(h * 0.915), int(h * 0.95)                        # author line and its rules
            m[y0:y1] |= (gold | cream)[y0:y1]
        else:
            m[: int(h * 0.72)] = (gold | cream)[: int(h * 0.72)]          # text column, list and author block
            m[int(h * 0.40):, int(w * 0.86):] = False                      # clouds on the right
        ys, xs = np.where(m)
        sc = 9.0 * DPI / h
        out[name] = dict(x0=(x_page + xs.min() * sc) / DPI, x1=(x_page + (xs.max() + 1) * sc) / DPI,
                         y0=BLEED + ys.min() * sc / DPI, y1=BLEED + (ys.max() + 1) * sc / DPI)
    wi = dims["width_in"]
    trim_r = wi - BLEED
    fold_l, fold_r = BLEED + 6, BLEED + 6 + dims["spine"]
    bk, fr = out["back"], out["front"]
    return dict(
        back_left=bk["x0"] - BLEED, back_top=bk["y0"] - BLEED, back_fold=fold_l - bk["x1"],
        front_right=trim_r - fr["x1"], front_top=fr["y0"] - BLEED, front_fold=fr["x0"] - fold_r,
        front_bottom=(9.25 - BLEED) - fr["y1"])
