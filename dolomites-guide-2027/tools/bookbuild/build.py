import os, sys, time
import pymupdf
fitz = pymupdf

from .core import ROOT, load_book
from .typ import build_typ, compile_pdf

DIST = os.path.join(ROOT, "dist")


def blank_pages(pdf):
    """Physical pages (1-based) that are blank spacer pages: no image and almost no text."""
    doc = fitz.open(pdf)
    out = []
    for i, page in enumerate(doc, 1):
        words = page.get_text().split()
        if not page.get_images() and len(words) <= 7:
            out.append(i)
    return out


def main(edition="print", name=None, cover=None):
    os.makedirs(DIST, exist_ok=True)
    book = load_book()
    out = os.path.join(DIST, name or f"draft-{edition}.pdf")
    t = time.time()
    blanks = ()
    for attempt in range(3):
        src = build_typ(book, edition, cover_image=cover, blanks=blanks)
        compile_pdf(src, out, f"book-{edition}")
        nb = tuple(blank_pages(out))
        if nb == blanks:
            break
        blanks = nb
    if edition == "print":
        n = len(pymupdf.open(out))
        if n % 2 == 1:  # print on whole sheets: end on a blank left-hand page
            src = build_typ(book, edition, cover_image=cover, blanks=blanks) + "\n#page(footer: none)[]\n"
            compile_pdf(src, out, f"book-{edition}")
    print("built", out, round(time.time() - t, 1), "s", "blank pages:", len(blanks), "| pages:", len(pymupdf.open(out)))
    return out


if __name__ == "__main__":
    main(*(sys.argv[1:] or ["print"]))
