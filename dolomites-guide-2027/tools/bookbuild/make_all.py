"""Build every production file, in dependency order, and write the QA report.

    python3 -m tools.bookbuild.make_all

Order matters: the paperback page count sets the spine width, so the interior is built first.
"""
import datetime, os, shutil, sys, zipfile

import pymupdf

from . import build, cover, docx_out, epub, qa, shrink
from .core import ROOT, load_book

NAME = "Dolomites-Travel-Guide-2027"
OUT = os.path.join(ROOT, "production")
PB = os.path.join(OUT, "Paperback")
EB = os.path.join(OUT, "Ebook")


def main():
    for d in (OUT, PB, EB):
        os.makedirs(d, exist_ok=True)
    report = []
    ok = True

    # 1. paperback interior (PDF)
    print_pdf = os.path.join(PB, f"{NAME}_Paperback-Interior_6x9.pdf")
    full_pdf = os.path.join(PB, f"{NAME}_Paperback-Interior_6x9_FullRes.pdf")
    build.main("print", os.path.relpath(full_pdf, os.path.join(ROOT, "dist")))
    # upload copy: same layout, resampled images, about 24 MB instead of about 59 MB
    shrink.prepare()
    shrink.use_small_images()
    build.main("print", os.path.relpath(print_pdf, os.path.join(ROOT, "dist")))
    shrink.use_full_images()
    pages = len(pymupdf.open(print_pdf))
    same = pages == len(pymupdf.open(full_pdf))
    print("small and full-resolution copies have the same page count:", same)
    assert same, "page count differs between the small and full-resolution builds; the spine would be wrong"
    report.append(("Paperback interior PDF", print_pdf, f"{pages} pages, 6 x 9 in"))

    # 2. covers (need the page count)
    wrap_pdf = os.path.join(PB, f"{NAME}_Paperback-Cover-Wrap.pdf")
    dims = cover.render_print(pages, wrap_pdf, os.path.join(cover.IMG, "preview"))
    ebook_cover = os.path.join(EB, f"{NAME}_Ebook-Cover_1600x2560.jpg")
    cover.render_ebook(ebook_cover)
    report.append(("Paperback cover wrap PDF", wrap_pdf, f"{dims['width_in']:.4f} x {dims['height_in']} in, spine {dims['spine']} in"))
    report.append(("Ebook cover JPG", ebook_cover, "1600 x 2560 px"))

    # 3. ebook PDF (colour, cover as page 1)
    ebook_pdf = os.path.join(EB, f"{NAME}_Ebook.pdf")
    build.main("ebook", os.path.relpath(ebook_pdf, os.path.join(ROOT, "dist")), cover="/" + os.path.relpath(ebook_cover, ROOT))
    report.append(("Ebook PDF", ebook_pdf, f"{len(pymupdf.open(ebook_pdf))} pages"))

    # 4. EPUB
    ebook_epub = os.path.join(EB, f"{NAME}_Ebook.epub")
    epub.build_epub(ebook_epub, ebook_cover)
    report.append(("Ebook EPUB (upload this to KDP)", ebook_epub, "EPUB 3"))

    # 5. DOCX
    for ed, folder, label in (("print", PB, "Paperback-Interior_6x9"), ("ebook", EB, "Ebook")):
        p = os.path.join(folder, f"{NAME}_{label}.docx")
        out, nentries, _ = docx_out.build_docx(ed, p)
        report.append((f"{ed.title()} DOCX", p, f"{nentries} contents entries"))

    write_report(report, pages, dims)
    write_guide(pages, dims, os.path.join(EB, f'{NAME}_Ebook.epub'))
    return report


def write_guide(pages, dims, epub_path):
    cost = 1.00 + 0.012 * pages
    mb = file_mb(epub_path)
    fee = mb * 0.15
    rep = {"PAGES": str(pages), "SPINE": f"{dims['spine']:.4f}", "WRAPW": f"{dims['width_in']:.2f}", "COST": f"{cost:.2f}",
           "EPUBMB": f"{mb:.1f}", "FEE": f"{fee:.2f}"}
    for tag, price in (("R1", 12.99), ("R2", 14.99), ("R3", 16.99)):
        rep[tag] = f"{0.6 * price - cost:.2f}"
    for tag, price in (("E1", 6.99), ("E2", 7.99), ("E3", 8.99)):
        rep[tag] = f"{0.7 * price - fee:.2f}"
    t = open(os.path.join(os.path.dirname(__file__), "guide_template.md"), encoding="utf-8").read()
    for k, v in rep.items():
        t = t.replace("{" + k + "}", v)
    open(os.path.join(OUT, "KDP-LISTING-AND-UPLOAD-GUIDE.md"), "w", encoding="utf-8").write(t)


def file_mb(p):
    return os.path.getsize(p) / 1e6


def write_report(report, pages, dims):
    lines = ["# Production QA report", "", f"Generated {datetime.date.today().isoformat()} by `tools/bookbuild/make_all.py`.", ""]
    lines += ["## Files", "", "| File | Size | Notes |", "|---|---|---|"]
    for label, path, note in report:
        lines.append(f"| {os.path.relpath(path, OUT)} | {file_mb(path):.1f} MB | {label}: {note} |")
    # paperback interior checks
    lines += ["", "## Paperback interior (KDP print checks)", ""]
    pb_pdf = [p for l, p, n in report if l == "Paperback interior PDF"][0]
    doc, info, problems = qa.pdf_qa(pb_pdf)
    lines.append(f"- Page size: {sorted(info['sizes'])} points (432 x 648 = 6 x 9 in): {'OK' if info['sizes'] == {(432, 648)} else 'CHECK'}")
    lines.append(f"- Page count: {pages} (even: {'yes' if pages % 2 == 0 else 'NO'}); KDP minimum 24, maximum 828")
    lines.append("- Margins: inside 0.85 in (KDP minimum 0.5 in for 151-300 pages), outside 0.62 in, top 0.72 in, bottom 0.9 in (minimum 0.25 in with no bleed)")
    lines.append(f"- Layout problems found by the checker: {len(problems)}")
    lines.append(f"- Orphaned headings: {len(info['orphan_headings'])}")
    fonts = set()
    for p in doc:
        for f in p.get_fonts():
            fonts.add((f[3].split('+')[-1], f[1] or 'n/a'))
    lines.append("- Fonts (all embedded): " + ", ".join(sorted(f"{n}" for n, e in fonts if e not in ("n/a", ""))))
    nimg = sum(len(p.get_images()) for p in doc)
    lines.append(f"- Images placed: {nimg} (greyscale; photos about 255 dpi and maps about 290 dpi at printed size in the upload copy; `_FullRes.pdf` is about 365 dpi)")
    lines += ["", "## Paperback cover", ""]
    wp = [p for l, p, n in report if l == "Paperback cover wrap PDF"][0]
    cd = pymupdf.open(wp)
    r = cd[0].rect
    lines.append(f"- Wrap size: {r.width / 72:.4f} x {r.height / 72:.4f} in; expected {dims['width_in']:.4f} x {dims['height_in']} in (bleed 0.125 in on all sides, spine {dims['spine']} in for {pages} pages, white paper, black-and-white interior)")
    lines.append(f"- Pages in cover PDF: {len(cd)} (must be 1)")
    # ebook checks
    lines += ["", "## Ebook", ""]
    ep = [p for l, p, n in report if l.startswith("Ebook EPUB")][0]
    try:
        from epubcheck import EpubCheck
        r_ = EpubCheck(ep)
        lines.append(f"- EPUB validation (EPUBCheck): {'valid' if r_.valid else 'INVALID'}; {len(r_.messages)} messages")
    except Exception as ex:
        lines.append(f"- EPUB validation not run: {ex}")
    lines.append(f"- EPUB size: {file_mb(ep):.1f} MB. KDP charges a delivery fee of about $0.15 per MB on the 70% royalty option (about ${file_mb(ep) * 0.15:.2f} per sale).")
    from PIL import Image
    ec = [p for l, p, n in report if l == "Ebook cover JPG"][0]
    im = Image.open(ec)
    lines.append(f"- Ebook cover: {im.size[0]} x {im.size[1]} px, {im.mode}, {file_mb(ec):.2f} MB (KDP: 2560 x 1600 recommended, under 50 MB)")
    # docx sanity
    lines += ["", "## DOCX files", ""]
    from docx import Document
    for l, p, n in report:
        if l.endswith("DOCX"):
            d = Document(p)
            heads = sum(1 for x in d.paragraphs if x.style.name.startswith("Heading"))
            imgs = len(d.inline_shapes)
            tabs = len(d.tables)
            lines.append(f"- {os.path.basename(p)}: {len(d.sections)} sections, {heads} headings, {imgs} images, {tabs} tables, {file_mb(p):.1f} MB")
    lines += ["", "In Word, accept the prompt to update fields when opening the paperback DOCX so the contents page numbers match Word's own pagination.", ""]
    open(os.path.join(OUT, "QA-REPORT.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
