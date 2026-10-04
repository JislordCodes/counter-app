"""Convert rendered maps to print (greyscale, 300 dpi) and ebook (1200 px) versions."""
import glob, os
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "images")
for d in ("print", "ebook"):
    os.makedirs(os.path.join(IMG, d), exist_ok=True)
for fn in sorted(glob.glob(os.path.join(IMG, "maps", "*.png"))):
    name = os.path.splitext(os.path.basename(fn))[0]
    im = Image.open(fn).convert("L")
    im.save(os.path.join(IMG, "print", name + ".png"), optimize=True, dpi=(300, 300))
    e = im
    if e.width > 1200:
        e = e.resize((1200, int(e.height * 1200 / e.width)), Image.LANCZOS)
    e.save(os.path.join(IMG, "ebook", name + ".png"), optimize=True)
    print(name, im.size, "->", e.size)
