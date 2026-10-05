"""Smaller upload copy of the paperback interior.

The full-resolution images (about 365 dpi) give a 59 MB PDF. Resampling them with Lanczos to about
255 dpi (photos) and 290 dpi (maps) gives about 24 MB with the same layout. Maps stay lossless PNG
with about 50 grey levels; photos are JPEG q78. (PDF-level recompression was tried and rejected: it
produced striped lines and doubled labels on the maps.)
"""
import glob, os

from PIL import Image

from . import core

SMALL = os.path.join(core.ROOT, "images", "print_small")
PHOTO_W = 1200   # px; photos print about 4.7 in wide
MAP_W = 1500     # px; maps print 5.2 in wide


def prepare():
    os.makedirs(SMALL, exist_ok=True)
    for old in glob.glob(os.path.join(SMALL, "*")):
        os.remove(old)
    for f in glob.glob(os.path.join(core.IMG, "print", "*")):
        b = os.path.splitext(os.path.basename(f))[0]
        im = Image.open(f).convert("L")
        if b.startswith("M"):
            if im.width > MAP_W:
                im = im.resize((MAP_W, round(im.height * MAP_W / im.width)), Image.LANCZOS)
            im = im.point(lambda v: (v // 5) * 5 + 2 if v < 250 else 255)
            im.save(os.path.join(SMALL, b + ".png"), optimize=True)
        else:
            if im.width > PHOTO_W:
                im = im.resize((PHOTO_W, round(im.height * PHOTO_W / im.width)), Image.LANCZOS)
            im.save(os.path.join(SMALL, b + ".jpg"), quality=78, optimize=True)


_ORIGINAL_PATH = core.Figure.path


def use_full_images():
    core.Figure.path = _ORIGINAL_PATH


def use_small_images():
    """Point the print build at the resampled images; call use_full_images() afterwards."""
    def path(self, edition):
        for ext in ("jpg", "png"):
            p = os.path.join(SMALL, f"{self.id}.{ext}")
            if os.path.exists(p):
                return p
        raise FileNotFoundError(self.id)
    core.Figure.path = path
