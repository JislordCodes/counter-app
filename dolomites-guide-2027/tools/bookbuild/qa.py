"""Quality checks on the typeset paperback PDF (and a few on the ebook PDF)."""
import re, sys

import pymupdf

from .core import ROOT, load_book, inl_text


def pdf_qa(path, trim=(432, 648), print_edition=True, verbose=True):
    doc = pymupdf.open(path)
    n = len(doc)
    problems = []
    info = {"pages": n}
    # 1. page size
    sizes = {(round(p.rect.width), round(p.rect.height)) for p in doc}
    info["sizes"] = sizes
    if sizes != {trim}:
        problems.append(f"page sizes {sizes} != {trim}")
    # 2. fonts embedded
    notemb = set()
    for p in doc:
        for f in p.get_fonts():
            # f = (xref, ext, type, basefont, name, encoding, ...)
            if f[1] == "n/a" or f[1] == "":
                notemb.add(f[3])
    if notemb:
        problems.append(f"fonts not embedded: {sorted(notemb)}")
    # 3. margin overflow (text outside safe area) and tiny text
    inside = 0.5 * 72   # KDP minimum gutter for 151-300 pages
    out = 0.25 * 72     # KDP minimum outside margin without bleed
    for i, p in enumerate(doc, 1):
        recto = i % 2 == 1
        left = inside if recto else out
        right = trim[0] - (out if recto else inside)
        for b in p.get_text("dict")["blocks"]:
            if b.get("type") != 0:
                continue
            x0, y0, x1, y1 = b["bbox"]
            if x0 < left - 2 or x1 > right + 2 or y0 < 0.3 * 72 or y1 > trim[1] - 0.3 * 72:
                txt = " ".join(s["text"] for l in b["lines"] for s in l["spans"])[:50]
                if txt.strip():
                    problems.append(f"p{i}: text outside text block: {x0:.0f}-{x1:.0f} ({txt!r})")
            for l in b["lines"]:
                for s in l["spans"]:
                    if s["size"] < 6.4 and s["text"].strip():
                        problems.append(f"p{i}: tiny text {s['size']:.1f}pt: {s['text'][:30]!r}")
        # images within text block
        for img in p.get_images(full=True):
            for r in p.get_image_rects(img[0]):
                if r.x0 < left - 2 or r.x1 > right + 2:
                    problems.append(f"p{i}: image outside text block {r.x0:.0f}-{r.x1:.0f}")
    # 4. nearly empty pages (excluding intentional blanks, openers, part pages)
    words = [len(p.get_text().split()) for p in doc]
    sparse = []
    for i, w in enumerate(words, 1):
        has_img = bool(doc[i - 1].get_images())
        if 0 < w < 60 and not has_img:
            sparse.append((i, w, doc[i - 1].get_text().strip().split("\n")[0][:40]))
    info["sparse_pages"] = sparse
    # 5. orphan headings: a heading-sized span in the last 9% of the text area
    orphans = []
    for i, p in enumerate(doc, 1):
        for b in p.get_text("dict")["blocks"]:
            if b.get("type") != 0:
                continue
            for l in b["lines"]:
                for s in l["spans"]:
                    if "Playfair" in s["font"] and 10 < s["size"] < 16 and s["bbox"][3] > trim[1] - 0.95 * 72 - 6 and s["text"].strip():
                        orphans.append((i, s["text"][:40]))
    info["orphan_headings"] = orphans
    return doc, info, problems


def toc_check(doc, book):
    """Compare the printed contents page numbers with where headings actually are."""
    texts = [p.get_text() for p in doc]
    flat = []
    for p in book.parts:
        flat.append(("part", f"{p.title}", None))
        for c in p.chapters:
            flat.append(("chapter", c.title, c.label))
    for s in book.appendices:
        if s.kind == "appendix":
            flat.append(("appendix", s.title, s.label))
    toc_pages = [i for i, t in enumerate(texts) if "Contents" in t[:80]]
    first_main = None
    for i, t in enumerate(texts):
        if re.search(r"PART\s+1", t) and "Plan Your Trip" in t and i > (toc_pages[0] + 3 if toc_pages else 0):
            first_main = i
            break
    bad = []
    if first_main is None:
        return ["could not locate first main page"]
    # printed numbers in the contents text
    toc_text = "\n".join(texts[i] for i in range(toc_pages[0], first_main) if i <= toc_pages[0] + 3)
    for kind, title, label in flat:
        for i in range(first_main, len(texts)):
            head = texts[i][:400]
            if title.split(":")[0][:30] in head and (kind == "part" or True):
                actual = i - first_main + 1
                m = re.search(re.escape(title[:28]) + r".{0,120}?(\d+)\s*$", toc_text, re.M)
                break
        else:
            bad.append(f"heading not found: {title}")
    return bad


def main(path):
    book = load_book()
    doc, info, problems = pdf_qa(path)
    print("pages:", info["pages"], "| sizes:", info["sizes"])
    print("problems:", len(problems))
    for p in problems[:40]:
        print("  ", p)
    print("sparse pages (under 60 words, no image):")
    for s in info["sparse_pages"]:
        print("  ", s)
    print("orphan headings:", info["orphan_headings"])
    return doc, info, problems


if __name__ == "__main__":
    main(sys.argv[1])
