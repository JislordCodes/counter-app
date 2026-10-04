"""EPUB 3 builder (reflowable, KDP-ready) from the shared document model."""
import html as _h
import io, os, re

from ebooklib import epub
from PIL import Image

from .core import ROOT, load_book, inl_text, Figure

IMG = os.path.join(ROOT, "images")
DIST = os.path.join(ROOT, "dist")

CSS = """
@charset "utf-8";
html { -webkit-text-size-adjust: 100%; }
body { margin: 0; padding: 0; line-height: 1.38; text-align: justify; hyphens: auto; -webkit-hyphens: auto; widows: 2; orphans: 2; }
p { margin: 0 0 0.7em 0; text-indent: 0; }
h1, h2, h3, h4, h5 { font-family: Georgia, "Times New Roman", serif; font-weight: bold; text-align: left; hyphens: none; -webkit-hyphens: none; page-break-after: avoid; break-after: avoid; line-height: 1.2; }
h1.part { text-align: center; font-size: 1.9em; margin: 22% 0 0.4em 0; page-break-before: always; letter-spacing: 0.02em; }
p.partnum { text-align: center; font-family: Arial, Helvetica, sans-serif; font-size: 0.78em; letter-spacing: 0.3em; text-transform: uppercase; margin: 0; text-indent: 0; }
p.partlist { text-align: center; font-family: Arial, Helvetica, sans-serif; font-size: 0.82em; margin: 0.15em 0; text-indent: 0; }
p.chlabel { font-family: Arial, Helvetica, sans-serif; font-size: 0.74em; letter-spacing: 0.28em; text-transform: uppercase; margin: 2.2em 0 0.3em 0; text-align: left; }
h1.chapter { font-size: 1.75em; margin: 0 0 0.9em 0; padding-bottom: 0.35em; border-bottom: 2px solid currentColor; page-break-before: avoid; }
h1.chapter.plain { margin-top: 2em; }
h2 { font-size: 1.28em; margin: 1.6em 0 0.55em 0; padding-bottom: 0.18em; border-bottom: 1px solid #999; }
h3 { font-size: 1.1em; font-style: italic; margin: 1.3em 0 0.45em 0; }
h4 { font-size: 0.8em; letter-spacing: 0.1em; text-transform: uppercase; font-family: Arial, Helvetica, sans-serif; margin: 1em 0 0.3em 0; }
p.lead { font-style: italic; font-size: 1.07em; line-height: 1.45; margin-bottom: 1em; }
ul, ol { margin: 0.4em 0 0.9em 0; padding-left: 1.4em; }
li { margin: 0 0 0.35em 0; text-align: left; }
li > p { margin: 0 0 0.3em 0; }
a { color: inherit; text-decoration: underline; }
figure { margin: 1.2em 0 1.3em 0; padding: 0; text-align: center; page-break-inside: avoid; break-inside: avoid; }
figure img { max-width: 100%; height: auto; }
figcaption { font-family: Arial, Helvetica, sans-serif; font-size: 0.78em; line-height: 1.35; text-align: left; margin-top: 0.45em; color: #444; }
figcaption b { letter-spacing: 0.06em; text-transform: uppercase; font-size: 0.92em; }
table { width: 100%; border-collapse: collapse; margin: 0.9em 0 1.3em 0; font-family: Arial, Helvetica, sans-serif; font-size: 0.8em; line-height: 1.3; text-align: left; hyphens: none; -webkit-hyphens: none; }
th { background: #2b2b2b; color: #fff; text-align: left; padding: 0.38em 0.5em; font-size: 0.92em; }
td { padding: 0.36em 0.5em; border-bottom: 1px solid #c8c8c8; vertical-align: top; }
tr:nth-child(even) td { background: #f4f4f4; }
table.kv { border: 1px solid #aaa; }
table.kv th { text-transform: uppercase; letter-spacing: 0.14em; font-size: 0.78em; }
table.kv td.k { width: 31%; font-weight: bold; background: #ececec; }
table.kv tr:nth-child(even) td { background: transparent; }
table.kv tr:nth-child(even) td.k { background: #ececec; }
aside.callout { margin: 1em 0 1.2em 0; padding: 0.6em 0.8em; border-left: 4px solid #555; background: #f1f1f1; font-size: 0.95em; page-break-inside: avoid; break-inside: avoid; text-align: left; }
aside.callout.important { border-left-color: #000; background: #e8e8e8; }
aside.callout .lab { display: block; font-family: Arial, Helvetica, sans-serif; font-size: 0.7em; letter-spacing: 0.16em; text-transform: uppercase; font-weight: bold; margin-bottom: 0.25em; }
aside.callout p { margin: 0 0 0.4em 0; }
hr.divider { border: 0; border-top: 1px solid #999; width: 20%; margin: 1.6em auto; }
div.titlepage { text-align: center; margin-top: 18%; }
div.titlepage h1 { text-align: center; font-size: 2.3em; letter-spacing: 0.06em; margin: 0; border: 0; }
div.titlepage p.t2 { font-family: Arial, Helvetica, sans-serif; letter-spacing: 0.4em; font-size: 0.95em; margin: 0.4em 0 0 0; text-indent: 0; text-align: center; }
div.titlepage p.t3 { font-style: italic; font-size: 1.1em; margin: 2em 8% 0 8%; text-indent: 0; text-align: center; }
div.titlepage p.t4 { font-family: Arial, Helvetica, sans-serif; letter-spacing: 0.3em; font-size: 0.9em; margin-top: 3.5em; text-indent: 0; text-align: center; font-weight: bold; }
div.copyright { font-size: 0.86em; margin-top: 8%; text-align: left; }
div.copyright p { margin-bottom: 0.6em; }
nav ol, ol.toc { list-style: none; padding-left: 0; margin: 0; }
ol.toc li { margin: 0.25em 0; }
ol.toc li.part { margin-top: 1em; font-weight: bold; font-family: Georgia, serif; }
ol.toc ol { padding-left: 1.2em; list-style: none; }
ol.toc a { text-decoration: none; }
div.credits p { font-size: 0.78em; line-height: 1.3; margin: 0 0 0.45em 0; text-align: left; hyphens: none; -webkit-hyphens: none; }
div.cover { text-align: center; margin: 0; padding: 0; }
div.cover img { max-width: 100%; max-height: 100%; }
"""


def e(s):
    return _h.escape(s, quote=True)


def inl(nodes):
    out = []
    for n in nodes:
        k = n[0]
        if k == "t":
            out.append(e(n[1]))
        elif k == "b":
            out.append("<b>" + inl(n[1]) + "</b>")
        elif k == "i":
            out.append("<i>" + inl(n[1]) + "</i>")
        elif k == "a":
            out.append(f'<a href="{e(n[1])}">' + inl(n[2]) + "</a>")
        elif k == "br":
            out.append("<br/>")
    return "".join(out)


class Ctx:
    def __init__(self, book):
        self.book = book
        self.images = {}  # id -> filename in epub


def small_image(path, out_path, width, quality):
    im = Image.open(path)
    im = im.convert("L") if path.lower().endswith(".jpg") and im.mode == "L" else im.convert("RGB")
    if im.width > width:
        im = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)
    im.save(out_path, "JPEG", quality=quality, optimize=True, progressive=False)


def figure_html(ctx, fid):
    f = ctx.book.figures[fid]
    name = f"images/{fid}.jpg"
    ctx.images[fid] = name
    lab = e(f.label)
    return (f'<figure id="fig-{fid}"><img src="{name}" alt="{e(f.caption)}"/>'
            f'<figcaption><b>{lab}.</b> {e(f.caption)}</figcaption></figure>')


def block_html(ctx, b, pending):
    k = b[0]
    if k == "h2":
        return f"<h2>{inl(b[1])}</h2>"
    if k == "h3":
        return f"<h3>{inl(b[1])}</h3>"
    if k == "h4":
        return f"<h4>{inl(b[1])}</h4>"
    if k == "p":
        return f"<p>{inl(b[1])}</p>"
    if k == "lead":
        return f'<p class="lead">{inl(b[1])}</p>'
    if k == "ul":
        return "<ul>" + "".join("<li>" + "".join(block_html(ctx, x, []) if x[0] != "p" else inl(x[1]) for x in it) + "</li>" for it in b[1]) + "</ul>"
    if k == "ol":
        start = f' start="{b[1]}"' if b[1] != 1 else ""
        return f"<ol{start}>" + "".join("<li>" + "".join(block_html(ctx, x, []) if x[0] != "p" else inl(x[1]) for x in it) + "</li>" for it in b[2]) + "</ol>"
    if k == "table":
        _, kind, title, header, rows = b
        if kind in ("glance", "kv"):
            head = f'<tr><th colspan="2">{e(title)}</th></tr>' if title else ""
            body = "".join(f'<tr><td class="k">{inl(r[0])}</td><td>{inl(r[1])}</td></tr>' for r in rows)
            return f'<table class="kv">{head}{body}</table>'
        head = "<tr>" + "".join(f"<th>{inl(c)}</th>" for c in header) + "</tr>" if header else ""
        body = "".join("<tr>" + "".join(f"<td>{inl(c)}</td>" for c in r) + "</tr>" for r in rows)
        return f"<table>{head}{body}</table>"
    if k == "callout":
        _, kind, label, inner = b
        cls = "important" if kind == "important" else ""
        lab = f'<span class="lab">{e(label)}</span>' if label else ""
        return f'<aside class="callout {cls}">{lab}' + "".join(block_html(ctx, x, []) for x in inner) + "</aside>"
    if k == "hr":
        return '<hr class="divider"/>'
    return ""


def blocks_html(ctx, blocks):
    out = []
    pending = []
    prev = None
    for b in blocks:
        if b[0] == "figure":
            if prev in ("h2", "h3", "h4", "figure", None) or pending:
                pending.append(b[1])
            else:
                out.append(figure_html(ctx, b[1]))
            prev = "figure"
            continue
        out.append(block_html(ctx, b, pending))
        if b[0] not in ("h2", "h3", "h4"):
            out.extend(figure_html(ctx, f) for f in pending)
            pending = []
        prev = b[0]
    out.extend(figure_html(ctx, f) for f in pending)
    return "\n".join(out)


def page(title, body, lang="en-GB"):
    return (f'<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="{lang}" xml:lang="{lang}">'
            f'<head><title>{e(title)}</title></head><body>{body}</body></html>')


def build_epub(out_path, cover_jpg):
    book = load_book()
    ctx = Ctx(book)
    eb = epub.EpubBook()
    eb.set_identifier("dolomites-travel-guide-2027-dave-velaquez")
    eb.set_title(book.title + ": " + book.subtitle)
    eb.set_language("en-GB")
    eb.add_author(book.author)
    eb.add_metadata("DC", "description", "A practical 2027 planning guide to Italy's Dolomites: reservations and access rules, real costs, where to stay, six regions, hikes, huts, via ferrata, cycling, winter, food, itineraries, safety and packing.")
    eb.add_metadata("DC", "subject", "Travel")
    eb.add_metadata("DC", "subject", "Dolomites")
    eb.add_metadata("DC", "rights", "Copyright 2026 Dave Velaquez. All rights reserved.")
    eb.add_metadata("DC", "date", "2026-10-04")

    # images
    tmp = os.path.join(ROOT, "build", "epub_img")
    os.makedirs(tmp, exist_ok=True)
    for fid, f in book.figures.items():
        src = f.path("ebook")
        if f.kind == "map":
            small_image(src, os.path.join(tmp, fid + ".jpg"), 960, 78)
        else:
            small_image(src, os.path.join(tmp, fid + ".jpg"), 760, 64)
    buf = io.BytesIO()
    Image.open(cover_jpg).convert("RGB").save(buf, "JPEG", quality=86, optimize=True)
    eb.set_cover("images/cover.jpg", buf.getvalue(), create_page=False)
    css = epub.EpubItem(uid="css", file_name="style/book.css", media_type="text/css", content=CSS)
    eb.add_item(css)

    items = []  # (item, nav entries)
    spine = []

    def add_page(fn, title, body, nav=True):
        it = epub.EpubHtml(title=title, file_name=fn, lang="en-GB")
        it.content = page(title, body)
        it.add_item(css)
        eb.add_item(it)
        spine.append(it)
        return it

    cover = epub.EpubHtml(title="Cover", file_name="cover.xhtml", lang="en-GB")
    cover.content = page("Cover", '<div class="cover"><img src="images/cover.jpg" alt="Cover: Dolomites Travel Guide 2027 by Dave Velaquez"/></div>')
    cover.add_item(css)
    eb.add_item(cover)
    spine.append(cover)

    words = book.title.replace(" 2027", "").split()
    tp = add_page("titlepage.xhtml", "Title page",
                  f'<div class="titlepage"><h1>{e(words[0].upper())}</h1><p class="t2">{e(" ".join(words[1:]).upper())} 2027</p>'
                  f'<p class="t3">{e(book.subtitle)}</p><p class="t4">{e(book.author.upper())}</p></div>')
    cp = blocks_html(ctx, book.copyright)
    add_page("copyright.xhtml", "Copyright",
             f'<div class="copyright"><p><b>{e(book.title)}</b><br/><i>{e(book.subtitle)}</i></p><p><b>2027 edition</b></p>{cp}'
             f'<p>Photographs are used under free licences; credits are listed in Appendix F. Maps contain data © OpenStreetMap contributors.</p></div>')

    toc_placeholder = add_page("contents.xhtml", "Contents", "")
    nav_tree = []

    # front
    for i, s in enumerate(book.front):
        fn = f"front{i}.xhtml"
        it = add_page(fn, s.title, f'<h1 class="chapter plain">{inl([("t", s.title)])}</h1>' + blocks_html(ctx, s.blocks))
        nav_tree.append((it, s.title, []))

    # parts and chapters
    for p in book.parts:
        pi = add_page(f"part{p.num}.xhtml", p.title,
                      f'<p class="partnum">Part {p.num}</p><h1 class="part">{e(p.title)}</h1>'
                      + "".join(f'<p class="partlist">{e(c.label)}. {e(c.title)}</p>' for c in p.chapters))
        node = (pi, f"Part {p.num}: {p.title}", [])
        nav_tree.append(node)
        for c in p.chapters:
            body = f'<p class="chlabel">Chapter {e(c.label)}</p><h1 class="chapter">{e(c.title)}</h1>' + blocks_html(ctx, c.blocks)
            it = add_page(f"ch{int(c.label):02d}.xhtml", c.title, body)
            subs = [(it, inl_text(b[1]), "") for b in c.blocks if b[0] == "h2"]
            node[2].append((it, f"{c.label}. {c.title}", subs))
    # appendices
    first_app = True
    for s in book.appendices:
        if s.kind == "divider":
            ai = add_page("appendices.xhtml", "Appendices", '<h1 class="part">Appendices</h1>')
            node = (ai, "Appendices", [])
            nav_tree.append(node)
            continue
        if s.label == "F":
            blocks = []
            group = []
            parts = []
            for b in s.blocks:
                if b[0] == "p" and b[1] and b[1][0][0] == "b" and inl_text(b[1][0][1]).startswith("Figure "):
                    group.append(b)
                else:
                    if group:
                        parts.append('<div class="credits">' + "".join(f"<p>{inl(g[1])}</p>" for g in group) + "</div>")
                        group = []
                    parts.append(block_html(ctx, b, []))
            if group:
                parts.append('<div class="credits">' + "".join(f"<p>{inl(g[1])}</p>" for g in group) + "</div>")
            body = f'<p class="chlabel">Appendix {e(s.label)}</p><h1 class="chapter">{e(s.title)}</h1>' + "\n".join(parts)
        else:
            body = f'<p class="chlabel">Appendix {e(s.label)}</p><h1 class="chapter">{e(s.title)}</h1>' + blocks_html(ctx, s.blocks)
        it = add_page(f"app{s.label}.xhtml", s.title, body)
        node[2].append((it, f"{s.label}. {s.title}", []))
    for i, s in enumerate(book.back):
        it = add_page(f"back{i}.xhtml", s.title, f'<h1 class="chapter plain">{e(s.title)}</h1>' + blocks_html(ctx, s.blocks))
        nav_tree.append((it, s.title, []))

    # list of maps (page)
    lom = "<h1 class=\"chapter plain\">List of maps</h1><ol class=\"toc\">"
    for fid, f in book.figures.items():
        if f.kind == "map":
            short = re.split(r"(?<=[a-z0-9\)])\. ", f.caption)[0].rstrip(".")
            owner = next(it for it in spine if it.file_name.startswith(("ch", "front")) and f'id="fig-{fid}"' in it.content)
            lom += f'<li><a href="{owner.file_name}#fig-{fid}">{e(f.label)}. {e(short)}</a></li>'
    lom += "</ol>"
    lm = add_page("maps.xhtml", "List of maps", lom)

    # visible contents page
    def toc_li(it, title, kids):
        s = f'<li><a href="{it.file_name}">{e(title)}</a>'
        if kids:
            s += "<ol>" + "".join(toc_li(*k[:2], k[2]) if len(k) == 3 else "" for k in kids) + "</ol>"
        return s + "</li>"

    vis = '<h1 class="chapter plain">Contents</h1><ol class="toc">'
    for it, title, kids in nav_tree:
        if it.file_name.startswith("part"):
            vis += f'<li class="part"><a href="{it.file_name}">{e(title)}</a><ol>'
            for ch in kids:
                vis += f'<li><a href="{ch[0].file_name}">{e(ch[1])}</a></li>'
            vis += "</ol></li>"
        elif it.file_name == "appendices.xhtml":
            vis += f'<li class="part"><a href="{it.file_name}">{e(title)}</a><ol>'
            for ch in kids:
                vis += f'<li><a href="{ch[0].file_name}">{e(ch[1])}</a></li>'
            vis += "</ol></li>"
        else:
            vis += f'<li><a href="{it.file_name}">{e(title)}</a></li>'
    vis += f'<li><a href="maps.xhtml">List of maps</a></li></ol>'
    toc_placeholder.content = page("Contents", vis)

    # NCX/nav tree (two levels: parts -> chapters, with sections under chapters)
    def nav_item(it, title, kids):
        return epub.Link(it.file_name, title, it.file_name.replace(".xhtml", ""))

    toc = []
    for it, title, kids in nav_tree:
        if kids:
            sub = []
            for ch in kids:
                sections = [epub.Link(f"{ch[0].file_name}", ch[1], ch[0].file_name.replace(".xhtml", ""))]
                sub.append(epub.Link(ch[0].file_name, ch[1], ch[0].file_name.replace(".xhtml", "")))
            toc.append(((epub.Section(title, it.file_name)), sub))
        else:
            toc.append(epub.Link(it.file_name, title, it.file_name.replace(".xhtml", "")))
    toc.append(epub.Link("maps.xhtml", "List of maps", "maps"))
    eb.toc = toc

    for fid in ctx.images:
        with open(os.path.join(tmp, fid + ".jpg"), "rb") as fh:
            eb.add_item(epub.EpubItem(uid="img_" + fid, file_name=f"images/{fid}.jpg", media_type="image/jpeg", content=fh.read()))
    eb.add_item(epub.EpubNcx())
    nav = epub.EpubNav()
    nav.add_item(css)
    eb.add_item(nav)
    eb.spine = [spine[0], "nav"] + spine[1:]
    # keep cover first, then nav is hidden as part of the spine but linear="no" is not available in ebooklib: use default
    epub.write_epub(out_path, eb, {"epub3_pages": False})
    return out_path


if __name__ == "__main__":
    os.makedirs(DIST, exist_ok=True)
    out = build_epub(os.path.join(DIST, "draft.epub"), os.path.join(DIST, "draft-ebook-cover.jpg"))
    print(out, round(os.path.getsize(out) / 1e6, 1), "MB")
