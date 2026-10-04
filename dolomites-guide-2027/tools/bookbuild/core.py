"""Load the manuscript into a clean document model that every output format (Typst PDF, DOCX, EPUB) builds from.

Model
  Book: title, subtitle, author, copyright (blocks), front (list of Section), parts (list of Part),
        appendices (Section list), back (Section list), figures (dict id -> Figure)
  Part: num, title, chapters (Chapter list)
  Chapter / Section: kind, label, title, blocks
Blocks are tuples:
  ("h2", inl) ("h3", inl) ("h4", inl) ("p", inl) ("lead", inl)
  ("ul", [item_blocks...]) ("ol", start, [item_blocks...])
  ("table", kind, title_inl_or_None, header_cells, rows)   kind in {"glance", "kv", "data"}; cells are inline lists
  ("callout", kind, label, [blocks])                        kind in {"wik", "important", "tip", "note"}
  ("figure", fid) ("hr",)
Inline nodes: ("t", str) ("b", [..]) ("i", [..]) ("a", url, [..]) ("br",)
"""
import glob, os, re
from dataclasses import dataclass, field

import markdown
from bs4 import BeautifulSoup, NavigableString, Tag
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MS = os.path.join(ROOT, "manuscript")
IMG = os.path.join(ROOT, "images")
SMALL = {"a", "an", "and", "as", "at", "but", "by", "for", "in", "of", "on", "or", "the", "to", "with"}

FIG_RE = re.compile(r"<!-- FIG:(\w+) -->\s*!\[(.*?)\]\((.*?)\)\s*\*(.*?)\*\s*<!-- /FIG -->", re.S)


def _md():
    return markdown.Markdown(extensions=["tables", "smarty", "sane_lists"])


def smart(s):
    return BeautifulSoup(_md().convert(s), "html.parser").get_text().strip()


def title_case(s):
    words = s.lower().split()
    out = []
    for i, w in enumerate(words):
        out.append(w if (w in SMALL and 0 < i < len(words) - 1) else w[:1].upper() + w[1:])
    return " ".join(out)


@dataclass
class Figure:
    id: str
    chap: int
    n: int
    label: str
    caption: str
    kind: str  # photo | map
    w: int = 0
    h: int = 0

    def path(self, edition):
        d = "print" if edition == "print" else "ebook"
        for ext in ("jpg", "png"):
            p = os.path.join(IMG, d, f"{self.id}.{ext}")
            if os.path.exists(p):
                return p
        raise FileNotFoundError(f"{self.id} ({d})")

    def rel(self, edition):
        return "/" + os.path.relpath(self.path(edition), ROOT).replace(os.sep, "/")


@dataclass
class Section:
    kind: str  # chapter | appendix | front | back | divider
    label: str  # "7", "A", ""
    title: str
    blocks: list = field(default_factory=list)
    key: str = ""


@dataclass
class Part:
    num: str
    title: str
    chapters: list = field(default_factory=list)


@dataclass
class Book:
    title: str = ""
    subtitle: str = ""
    author: str = ""
    copyright: list = field(default_factory=list)
    front: list = field(default_factory=list)
    parts: list = field(default_factory=list)
    appendices: list = field(default_factory=list)
    back: list = field(default_factory=list)
    figures: dict = field(default_factory=dict)


# ------------------------------------------------------------------ inline
def inl(node):
    out = []
    for c in node.children:
        if isinstance(c, NavigableString):
            s = re.sub(r"\s+", " ", str(c))
            if s:
                out.append(("t", s))
        elif isinstance(c, Tag):
            n = c.name
            if n in ("strong", "b"):
                out.append(("b", inl(c)))
            elif n in ("em", "i"):
                out.append(("i", inl(c)))
            elif n == "a":
                out.append(("a", c.get("href", ""), inl(c)))
            elif n == "br":
                out.append(("br",))
            elif n == "code":
                out.append(("t", c.get_text()))
            else:
                out.extend(inl(c))
    return out


def inl_text(nodes):
    s = ""
    for n in nodes:
        if n[0] == "t":
            s += n[1]
        elif n[0] in ("b", "i"):
            s += inl_text(n[1])
        elif n[0] == "a":
            s += inl_text(n[2])
        elif n[0] == "br":
            s += " "
    return s


def strip_edges(nodes):
    nodes = list(nodes)
    if nodes and nodes[0][0] == "t":
        nodes[0] = ("t", nodes[0][1].lstrip())
        if not nodes[0][1]:
            nodes = nodes[1:]
    if nodes and nodes[-1][0] == "t":
        nodes[-1] = ("t", nodes[-1][1].rstrip())
        if not nodes[-1][1]:
            nodes = nodes[:-1]
    return nodes


# ------------------------------------------------------------------ blocks
CALLOUT = {"wish i'd known": "wik", "wish i’d known": "wik", "important": "important", "tip": "tip"}


def callout_from(blocks):
    """Turn the blocks of a blockquote into (kind, label, blocks)."""
    kind, label = "note", None
    if blocks and blocks[0][0] == "p" and blocks[0][1] and blocks[0][1][0][0] == "b":
        lab = inl_text(blocks[0][1][0][1]).strip()
        key = lab.rstrip(":.").lower()
        if key in CALLOUT:
            kind, label = CALLOUT[key], lab.rstrip(":.")
            rest = strip_edges(blocks[0][1][1:])
            if rest and rest[0][0] == "t":
                rest[0] = ("t", re.sub(r"^[:.\s]+", "", rest[0][1]))
            blocks = ([("p", rest)] if rest else []) + blocks[1:]
        elif lab.endswith((":", ".")) and len(lab) < 60:
            kind, label = "note", lab.rstrip(":.")
            rest = strip_edges(blocks[0][1][1:])
            blocks = ([("p", rest)] if rest else []) + blocks[1:]
    return ("callout", kind, label, blocks)


def table_block(t):
    def cells(tr):
        return [strip_edges(inl(td)) for td in tr.find_all(["th", "td"], recursive=False)]

    head = [cells(tr) for tr in (t.find("thead").find_all("tr") if t.find("thead") else [])]
    body = [cells(tr) for tr in (t.find("tbody").find_all("tr") if t.find("tbody") else [])]
    header = head[0] if head else []
    ncol = max([len(header)] + [len(r) for r in body]) if (header or body) else 0
    for r in body:
        while len(r) < ncol:
            r.append([])
    htxt = [inl_text(c).strip() for c in header]
    first_bold = body and all(len(r[0]) == 1 and r[0][0][0] == "b" for r in body if r and r[0])
    if ncol == 2 and first_bold:
        title = htxt[0] if htxt and htxt[0] and not htxt[1:][0:1] == [None] and not any(htxt[1:]) else None
        kind = "glance" if title else "kv"
        return ("table", kind, title, [], body)
    if not any(htxt):
        header = []
    return ("table", "data", None, header, body)


def blocks_of(parent, figs):
    out = []
    for el in parent.children:
        if isinstance(el, NavigableString):
            continue
        n = el.name
        if n in ("h1", "h2", "h3", "h4"):
            out.append((n, strip_edges(inl(el))))
        elif n == "p":
            txt = el.get_text().strip()
            m = re.fullmatch(r"@@FIG:(\w+)@@", txt)
            if m:
                out.append(("figure", m.group(1)))
            else:
                p_inl = strip_edges(inl(el))
                lab = inl_text(p_inl[0][1]).strip().rstrip(":.").lower() if p_inl and p_inl[0][0] == "b" else ""
                if lab in CALLOUT:
                    out.append(callout_from([("p", p_inl)]))
                else:
                    out.append(("p", p_inl))
        elif n in ("ul", "ol"):
            items = []
            for li in el.find_all("li", recursive=False):
                sub = [c for c in li.children if isinstance(c, Tag) and c.name in ("ul", "ol", "p")]
                if sub:
                    items.append(blocks_of(li, figs))
                else:
                    items.append([("p", strip_edges(inl(li)))])
            start = int(el.get("start", 1)) if n == "ol" else 1
            out.append(("ul", items) if n == "ul" else ("ol", start, items))
        elif n == "table":
            out.append(table_block(el))
        elif n == "blockquote":
            out.append(callout_from(blocks_of(el, figs)))
        elif n == "hr":
            out.append(("hr",))
    return out


def load_md(path, figs, counters):
    text = open(path, encoding="utf-8").read()

    def figsub(m):
        fid, alt = m.group(1), m.group(2)
        mm = re.match(r"Figure (\d+)\.(\d+)\. (.*)", alt, re.S)
        f = Figure(fid, int(mm.group(1)), int(mm.group(2)), f"Figure {mm.group(1)}.{mm.group(2)}", smart(mm.group(3)),
                   "map" if fid[0] in "MI" else "photo")
        with Image.open(f.path("print")) as im:
            f.w, f.h = im.size
        figs[fid] = f
        return f"\n\n@@FIG:{fid}@@\n\n"

    text = FIG_RE.sub(figsub, text)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    assert "@@FIG" not in re.sub(r"@@FIG:\w+@@", "", text), path
    html = _md().convert(text)
    return BeautifulSoup(html, "html.parser")


def load_book():
    book = Book()
    figs = book.figures
    counters = {}
    files = sorted(glob.glob(os.path.join(MS, "*.md")))
    cur_part = None
    for path in files:
        base = os.path.basename(path)
        soup = load_md(path, figs, counters)
        blocks = blocks_of(soup, figs)
        if base.startswith("00-"):
            # title block, copyright, front sections
            i = 0
            assert blocks[0][0] == "h1"
            book.title = inl_text(blocks[0][1])
            book.subtitle = inl_text(blocks[1][1])
            book.author = inl_text(blocks[2][1])
            sec = None
            for b in blocks[3:]:
                if b[0] == "hr":
                    continue
                if b[0] == "h2":
                    t = inl_text(b[1])
                    if t == "Copyright and Notice":
                        sec = "copyright"
                        continue
                    sec = Section("front", "", t)
                    book.front.append(sec)
                    continue
                if sec == "copyright":
                    book.copyright.append(b)
                elif sec is not None:
                    sec.blocks.append(b)
            continue
        if base.startswith("20-"):
            sec = None
            for b in blocks:
                if b[0] == "hr":
                    continue
                if b[0] == "h1":
                    t = inl_text(b[1])
                    m = re.match(r"Appendix ([A-Z]): (.*)", t)
                    if t == "APPENDICES":
                        sec = Section("divider", "", "Appendices")
                        book.appendices.append(sec)
                    elif m:
                        sec = Section("appendix", m.group(1), m.group(2))
                        book.appendices.append(sec)
                    else:
                        sec = Section("back", "", t)
                        book.back.append(sec)
                    continue
                if sec is not None:
                    # appendix H3 (kept as sub-heading level)
                    sec.blocks.append(b)
            continue
        # chapters
        sec = None
        for b in blocks:
            if b[0] == "h1":
                t = inl_text(b[1])
                m = re.match(r"PART (\d+): (.*)", t)
                if m:
                    cur_part = Part(m.group(1), title_case(m.group(2)))
                    book.parts.append(cur_part)
                    continue
                m = re.match(r"(\d+)\. (.*)", t)
                assert m, t
                sec = Section("chapter", m.group(1), m.group(2))
                cur_part.chapters.append(sec)
                continue
            if sec is not None:
                sec.blocks.append(b)
    # lead paragraph: first paragraph of each chapter
    for p in book.parts:
        for ch in p.chapters:
            for i, b in enumerate(ch.blocks):
                if b[0] == "p":
                    if len(inl_text(b[1])) < 520:
                        ch.blocks[i] = ("lead", b[1])
                    break
                if b[0] in ("h2", "table", "figure"):
                    break
    return book


def all_blocks(book):
    for s in book.front:
        yield from s.blocks
    for p in book.parts:
        for c in p.chapters:
            yield from c.blocks
    for s in book.appendices + book.back:
        yield from s.blocks


if __name__ == "__main__":
    b = load_book()
    print(b.title, "|", b.subtitle, "|", b.author)
    print("front:", [s.title for s in b.front])
    for p in b.parts:
        print("PART", p.num, p.title, [c.label + " " + c.title for c in p.chapters])
    print("appendices:", [(s.label, s.title) for s in b.appendices], "back:", [s.title for s in b.back])
    import collections
    kinds = collections.Counter()
    for blk in all_blocks(b):
        kinds[blk[0] + (":" + blk[1] if blk[0] in ("table", "callout") else "")] += 1
    print(dict(kinds))
    print("figures:", len(b.figures))
