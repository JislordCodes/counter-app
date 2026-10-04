"""Contact sheets of the FINISHED photos (after crop) with their captions, for a last check by eye.

Output: images/final_sheets/F01.jpg ... (12 photos per sheet, 4 columns x 3 rows)
"""
import json, os, sys, textwrap
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "images")
OUT = os.path.join(IMG, "final_sheets")
os.makedirs(OUT, exist_ok=True)
sel = json.load(open(os.path.join(IMG, "selection.json")))
ids = [k for k in sel if os.path.exists(os.path.join(IMG, "print", k + ".jpg"))]
missing = [k for k in sel if k not in ids]
print("ready:", len(ids), "missing:", missing)

font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 15)
W, H, PER = 420, 330, 12
for n in range(0, len(ids), PER):
    chunk = ids[n:n + PER]
    sheet = Image.new("RGB", (4 * W, 3 * H), "white")
    d = ImageDraw.Draw(sheet)
    for k, sid in enumerate(chunk):
        x, y = (k % 4) * W, (k // 4) * H
        im = Image.open(os.path.join(IMG, "ebook", sid + ".jpg")).convert("RGB")
        im.thumbnail((W - 10, H - 80))
        sheet.paste(im, (x + 5, y + 5))
        d.text((x + 6, y + 6), sid, fill="red", font=big)
        for j, line in enumerate(textwrap.wrap(sel[sid]["caption"], 58)[:4]):
            d.text((x + 5, y + H - 72 + j * 14), line, fill="black", font=font)
    sheet.save(os.path.join(OUT, f"F{n // PER + 1:02d}.jpg"), quality=82)
    print("sheet", n // PER + 1, [c for c in chunk])
