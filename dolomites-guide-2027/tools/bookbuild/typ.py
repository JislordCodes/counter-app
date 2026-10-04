"""Typst emitter: turns the book model into a typeset PDF (paperback interior or ebook PDF).

The look: EB Garamond text, Playfair Display titles, Source Sans 3 for boxes and tables.
Paperback is greyscale; the ebook PDF uses a restrained alpine colour accent.
"""
import os, re

import typst

from .core import ROOT, load_book, inl_text

FONT_DIR = os.path.join(ROOT, "build", "fonts")

THEMES = {
    "print": dict(
        acc='luma(30)', acc2='luma(95)', tint='luma(238)', tint2='luma(247)', rule='luma(150)', hdr='luma(38)',
        wik_bar='luma(60)', wik_fill='luma(240)', imp_bar='luma(0)', imp_fill='luma(232)', tip_bar='luma(110)', tip_fill='luma(244)',
        link='luma(0)'),
    "ebook": dict(
        acc='rgb("#1f4d63")', acc2='rgb("#6c7f89")', tint='rgb("#e9f0f3")', tint2='rgb("#f5f8f9")', rule='rgb("#9fb6c1")', hdr='rgb("#1f4d63")',
        wik_bar='rgb("#c8742f")', wik_fill='rgb("#fbf1e6")', imp_bar='rgb("#a53a2c")', imp_fill='rgb("#f9ebe8")', tip_bar='rgb("#3c7a5a")', tip_fill='rgb("#eaf4ee")',
        link='rgb("#1f4d63")'),
}

MAP_SHORT = {
    'M01': 'The Dolomites at a glance', 'M02': 'Getting to the Dolomites', 'M03': 'Val Gardena and Alpe di Siusi',
    'M04': 'The Sella Ronda and the four great passes', 'M05': "Cortina d'Ampezzo and its mountains", 'M06': 'Tre Cime, Sesto and Braies',
    'M07': 'Val di Fassa, Catinaccio and Marmolada', 'M08': 'Plan de Corones, Brixen and Bolzano', 'M09': 'The Tre Cime loop',
    'M10': 'Seceda and Col Raiser', 'M11': 'Alpe di Siusi: Compatsch to Saltria', 'M12': 'The Lagazuoi cable car',
    'M14': 'The Alta Via 1, Lago di Braies to La Pissa', 'I05': 'Five-day route', 'I07': 'Seven-day route', 'I10': 'Ten-day route',
}
NBSP = " "
ZWSP = "​"


def esc(s):
    s = s.replace("\\", "\\\\")
    for ch in "#$*_@<>[]~`":
        s = s.replace(ch, "\\" + ch)
    s = s.replace("//", "\\/\\/").replace("/*", "\\/\\*")
    return s


def soften_domains(s):
    def f(m):
        t = m.group(0)
        if len(t) < 16:
            return t
        return re.sub(r"([./])", r"\1" + ZWSP, t)

    return re.sub(r"[A-Za-z0-9À-ɏ-]+(?:\.[A-Za-z0-9À-ɏ/_-]+)+", f, s)


def nbsp(s):
    s = re.sub(r"(\d) (m|km|min|kg|cm|mm|hours?|hrs?|days?|nights?|euros?|per cent|%|°C)\b", lambda m: m.group(1) + NBSP + m.group(2), s)
    s = re.sub(r"\b(Chapter|Chapters|Appendix|Figure|Part|Ch\.|No\.) (\d|[A-F]\b)", lambda m: m.group(1) + NBSP + m.group(2), s)
    s = re.sub(r"\b(Mt|St|Rif\.|Passo|Lago|Val|Via|Monte) ([A-Z])", lambda m: m.group(1) + NBSP + m.group(2), s)
    return s


def tx(s):
    s = nbsp(soften_domains(s))
    s = esc(s)
    return s


def tstr(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def ti(nodes):
    out = []
    for n in nodes:
        k = n[0]
        if k == "t":
            out.append(tx(n[1]))
        elif k == "b":
            out.append("#strong[" + ti(n[1]) + "]")
        elif k == "i":
            out.append("#emph[" + ti(n[1]) + "]")
        elif k == "a":
            out.append("#link(" + tstr(n[1]) + ")[" + ti(n[2]) + "]")
        elif k == "br":
            out.append("#linebreak()")
    s = "".join(out)
    # a paragraph must not start with markup that Typst would read as a list or heading
    s = re.sub(r"^(\d+)\.(\s)", r"\1\\.\2", s)
    s = re.sub(r"^([-+/=])", r"\\\1", s)
    return s


# ------------------------------------------------------------------ blocks
def col_weights(rows, header, ncol, total=324.0):
    """Column widths in points: proportional to content, but never narrower than the longest unbreakable word."""
    def words(nodes):
        return [w for w in re.split(r"[\s/\u2013-]+", inl_text(nodes)) if w]

    minw, want = [], []
    for c in range(ncol):
        cells = [r[c] for r in rows if c < len(r)] + ([header[c]] if header and c < len(header) else [])
        longest = max([len(w) for cell in cells for w in words(cell)] + [3])
        lens = [len(inl_text(cell)) for cell in cells]
        avg = sum(lens) / max(len(lens), 1)
        mx = max(lens) if lens else 5
        minw.append(longest * 4.6 + 13)
        want.append(max(0.55 * avg + 0.45 * min(mx, 60), 6) * 4.1 + 13)
    scale = total / sum(want)
    w = [max(m, x * scale) for m, x in zip(minw, want)]
    for _ in range(6):
        over = sum(w) - total
        if over <= 0.5:
            break
        free = [i for i in range(ncol) if w[i] > minw[i] + 0.5]
        room = sum(w[i] - minw[i] for i in free)
        if room <= 0:
            break
        for i in free:
            w[i] -= over * (w[i] - minw[i]) / room
    tot = sum(w)
    return [round(x / tot * 100, 2) for x in w]


class Emitter:
    def __init__(self, book, edition):
        self.book = book
        self.ed = edition
        self.out = []
        self.pending = []  # figures waiting to be placed after the next content block

    # --- helpers
    def w(self, s):
        self.out.append(s)

    def figure(self, fid):
        f = self.book.figures[fid]
        path = f.rel(self.ed)
        textw = 4.55  # inches (print text block); ebook is 4.76 but the same rule is safe
        maxh = 6.0 if f.kind == "map" else 4.3
        if f.h / f.w * textw > maxh:
            img = f'align(center, image({tstr(path)}, height: {maxh}in))'
        else:
            img = f'image({tstr(path)}, width: 100%)' if f.kind == 'map' else f'align(center, image({tstr(path)}, width: 90%))'
        cap = ti([("t", f.caption)])
        label = f.label.upper()
        return (f'#figure(placement: auto, kind: {tstr(f.kind)}, supplement: none, numbering: none, '
                f'{img}, '
                f'caption: [#text(font: sans, size: 7.4pt, weight: 700, tracking: 0.09em, fill: acc)[{label}]#h(5pt){cap}])<fig-{fid}>')

    def flush_figs(self):
        for fid in self.pending:
            self.w(self.figure(fid))
            self.w("\n\n")
        self.pending = []

    def blocks(self, bl, chapter_ctx=True):
        prev = None
        for b in bl:
            k = b[0]
            if k == "figure":
                # place the picture after the first content block that follows a heading
                if prev in ("h2", "h3", "h4", "figure", None) or self.pending:
                    self.pending.append(b[1])
                else:
                    self.w(self.figure(b[1]) + "\n\n")
                prev = "figure"
                continue
            self.block(b)
            if k not in ("h2", "h3", "h4"):
                self.flush_figs()
            prev = k
        self.flush_figs()

    def block(self, b):
        k = b[0]
        if k == "h2":
            self.w(f"#sec[{ti(b[1])}]\n\n")
        elif k == "h3":
            self.w(f"#sub[{ti(b[1])}]\n\n")
        elif k == "h4":
            self.w(f"#subsub[{ti(b[1])}]\n\n")
        elif k == "p":
            self.w(ti(b[1]) + "\n\n")
        elif k == "lead":
            self.w(f"#lead[{ti(b[1])}]\n\n")
        elif k == "ul":
            items = b[1]
            n = len(items)
            avg = sum(len(inl_text(sum([x[1] for x in it if x[0] == 'p'], []))) for it in items) / max(n, 1)
            body = self.list_items(items, "list")
            if n >= 8 and avg < 46 and all(len(it) == 1 for it in items):
                self.w(f"#columns(2, gutter: 16pt)[{body}]\n\n")
            else:
                self.w(body + "\n\n")
        elif k == "ol":
            self.w(self.list_items(b[2], "enum", start=b[1]) + "\n\n")
        elif k == "table":
            self.table(b)
        elif k == "callout":
            _, kind, label, inner = b
            e = Emitter(self.book, self.ed)
            e.blocks(inner)
            self.w(f"#callout({tstr(kind)}, {tstr(label) if label else 'none'})[{''.join(e.out)}]\n\n")
        elif k == "hr":
            self.w("#divider()\n\n")

    def list_items(self, items, kind, start=1):
        parts = []
        for it in items:
            e = Emitter(self.book, self.ed)
            e.blocks(it)
            parts.append("[" + "".join(e.out).strip() + "]")
        if kind == "list":
            return "#bullets(" + ", ".join(parts) + ")"
        return f"#numbered({start}, " + ", ".join(parts) + ")"

    def cell(self, nodes):
        return "[" + ti(nodes) + "]"

    def table(self, b):
        _, kind, title, header, rows = b
        if kind in ("glance", "kv"):
            lab = max((len(inl_text(r[0])) for r in rows), default=8)
            kw = 1.0 if lab <= 14 else (1.18 if lab <= 20 else 1.4)
            cells = []
            for r in rows:
                cells.append(self.cell(r[0]))
                cells.append(self.cell(r[1]))
            t = tstr(title) if title else "none"
            self.w(f"#kvtable({t}, {kw}in, {', '.join(cells)})\n\n")
        else:
            ncol = max([len(header)] + [len(r) for r in rows])
            wts = col_weights(rows, header, ncol)
            cols = ", ".join(f"{x}fr" for x in wts)
            hdr = "(" + ", ".join(self.cell(c) for c in header) + ("," if len(header) == 1 else "") + ")" if header else "()"
            body = []
            for r in rows:
                body.extend(self.cell(c) for c in r)
            keep = "true" if len(rows) <= 9 else "false"
            self.w(f"#datatable(({cols},), {hdr}, keep: {keep}, {', '.join(body)})\n\n")

    # --- credits (two-column small print)
    def credits(self, blocks):
        group, out = [], []
        for b in blocks:
            if b[0] == "p" and b[1] and b[1][0][0] == "b" and inl_text(b[1][0][1]).startswith("Figure "):
                group.append(b)
            else:
                if group:
                    out.append(("credits", group))
                    group = []
                out.append(b)
        if group:
            out.append(("credits", group))
        return out


def smart_cap(s):
    return s


# ------------------------------------------------------------------ template
TEMPLATE = r'''
#let sans = ("Source Sans 3", "Liberation Sans")
#let serif = ("EB Garamond", "Liberation Serif", "DejaVu Serif")
#let display = ("Playfair Display", "EB Garamond", "Liberation Serif")
#let acc = %(acc)s
#let acc2 = %(acc2)s
#let tint = %(tint)s
#let tint2 = %(tint2)s
#let rule = %(rule)s
#let hdr = %(hdr)s
#let PRINT = %(is_print)s
#let BOOKTITLE = %(booktitle)s
#let CH = %(ch)s
#let PT = %(pt)s
#let BLANKS = %(blanks)s

#set document(title: %(doctitle)s, author: %(author)s, keywords: ("Dolomites", "travel guide", "Italy", "2027"))
#set text(font: serif, size: 11pt, lang: "en", region: "gb", hyphenate: true, features: ("lnum",), fill: luma(8),
  costs: (hyphenation: 100%%, runt: 100%%, widow: 100%%, orphan: 100%%))
#set par(justify: true, leading: 0.56em, spacing: 0.72em, linebreaks: "optimized")
#set list(marker: text(fill: acc, size: 9pt)[•], indent: 0pt, body-indent: 0.62em, spacing: 0.42em)
#set enum(indent: 0pt, body-indent: 0.55em, spacing: 0.42em)
#set strong(delta: 200)
#set place(clearance: 16pt)
#show link: it => { set text(fill: %(link)s); it }
#set figure(gap: 7pt)
#show figure.caption: it => { set text(font: sans, size: 8.2pt, fill: luma(55)); set par(justify: false, leading: 0.45em); align(left, it.body) }

#let peaks(w: 30pt, c: acc) = box(width: w, height: w * 0.42, baseline: 0pt)[
  #polygon(fill: c, (0%%, 100%%), (0%%, 55%%), (10%%, 20%%), (19%%, 55%%), (27%%, 8%%), (37%%, 52%%), (50%%, 0%%), (58%%, 40%%), (66%%, 14%%), (76%%, 55%%), (86%%, 28%%), (100%%, 70%%), (100%%, 100%%))
]
#let divider() = align(center, block(above: 16pt, below: 16pt, peaks(w: 22pt, c: acc2)))

#let pgnum(p) = {
  let hits = query(<part1>)
  if hits.len() == 0 { return numbering("i", p) }
  let p0 = hits.first().location().page()
  if p < p0 { numbering("i", p) } else { str(p - p0 + 1) }
}

#let to-recto() = {
  if PRINT { pagebreak(to: "odd", weak: true) } else { pagebreak(weak: true) }
}

// ---- headings
#show heading: set text(hyphenate: false)
#show heading.where(level: 1): it => {
  to-recto()
  let info = PT.at(str(it.label))
  block(width: 100%%, height: 100%%)[
    #align(center + horizon)[
      #peaks(w: 54pt, c: acc)
      #v(18pt)
      #text(font: sans, size: 9.5pt, weight: 600, tracking: 0.34em, fill: acc2)[#info.at("num")]
      #v(12pt)
      #block(width: 3.6in)[#set par(justify: false, leading: 0.3em)
        #text(font: display, size: 30pt, weight: 700, fill: acc)[#it.body]]
      #v(14pt)
      #line(length: 36pt, stroke: 1.1pt + acc2)
      #v(16pt)
      #block(width: 3.4in)[#set par(justify: false, leading: 0.5em)
        #set text(font: sans, size: 9.6pt, fill: luma(55))
        #for c in info.at("chapters") [#c.at(0)#h(6pt)#c.at(1)#linebreak()]]
    ]
  ]
}

#show heading.where(level: 2): it => {
  let info = CH.at(str(it.label))
  if info.at("recto", default: "yes") == "yes" { to-recto() } else { pagebreak(weak: true) }
  v(if info.at("recto", default: "yes") == "yes" { 0.85in } else { 0.35in })
  if info.at("label") != none {
    text(font: sans, size: 9pt, weight: 600, tracking: 0.3em, fill: acc2)[#info.at("label")]
    v(7pt)
  }
  block(width: 100%%)[#set par(justify: false, leading: 0.3em)
    #text(font: display, size: 26pt, weight: 700, fill: acc)[#it.body]]
  v(9pt)
  line(length: 40pt, stroke: 1.3pt + acc)
  v(18pt)
}

#show heading.where(level: 3): it => {
  block(sticky: true, above: 22pt, below: 9pt, width: 100%%)[
    #set par(justify: false, leading: 0.3em)
    #text(font: display, size: 14.2pt, weight: 700, fill: acc)[#it.body]
    #v(-1pt)
    #line(length: 100%%, stroke: 0.45pt + rule)
  ]
}
#show heading.where(level: 4): it => {
  block(sticky: true, above: 15pt, below: 7pt, width: 100%%)[
    #set par(justify: false, leading: 0.3em)
    #text(font: display, size: 11.6pt, weight: 700, style: "italic", fill: acc)[#it.body]
  ]
}
#show heading.where(level: 5): it => {
  block(sticky: true, above: 11pt, below: 3pt)[#text(font: sans, size: 8.4pt, weight: 700, tracking: 0.12em, fill: acc2)[#upper(it.body)]]
}

#let sec(body) = heading(level: 3, outlined: true, body)
#let sub(body) = heading(level: 4, outlined: false, body)
#let subsub(body) = heading(level: 5, outlined: false, body)
#let lead(body) = { set text(size: 11.9pt, style: "italic", fill: luma(30)); set par(leading: 0.6em); body; v(2pt) }

// ---- lists
#let bullets(..items) = block(above: 0.6em, below: 0.85em)[#list(tight: true, ..items.pos())]
#let numbered(start, ..items) = block(above: 0.6em, below: 0.85em)[#enum(tight: true, start: start, numbering: n => text(font: sans, weight: 700, size: 9pt, fill: acc)[#n.], ..items.pos())]

// ---- boxes
#let callout(kind, label, body) = {
  let (bar, fill) = if kind == "wik" { (%(wik_bar)s, %(wik_fill)s) } else if kind == "important" { (%(imp_bar)s, %(imp_fill)s) } else if kind == "tip" { (%(tip_bar)s, %(tip_fill)s) } else { (acc2, tint2) }
  block(width: 100%%, above: 11pt, below: 12pt, breakable: false, fill: fill, inset: (left: 12pt, right: 10pt, y: 8pt), stroke: (left: 2.8pt + bar), radius: (right: 3pt))[
    #if label != none [#text(font: sans, size: 7.3pt, weight: 700, tracking: 0.16em, fill: bar)[#upper(label)]#v(3.5pt)]
    #set text(size: 10.2pt)
    #set par(leading: 0.5em, spacing: 0.55em)
    #body
  ]
}

#let kvtable(title, kcol, ..cells) = {
  let c = cells.pos()
  let nrows = calc.div-euclid(c.len(), 2)
  let long = nrows > 8
  block(width: 100%%, above: 10pt, below: 13pt, breakable: long, stroke: if long { none } else { 0.55pt + rule }, radius: 2.5pt, clip: not long)[
    #set par(justify: false, leading: 0.42em, spacing: 0.4em)
    #set text(hyphenate: false)
    #table(columns: (kcol, 1fr), inset: (x: 7pt, y: if long { 3.4pt } else { 4.4pt }), stroke: (x, y) => (bottom: if y < nrows - 1 + (if title != none { 1 } else { 0 }) { 0.3pt + rule } else if long { 0.55pt + rule } else { none }, top: if long and y == 0 { 0.55pt + rule } else { none }),
      fill: (x, y) => if title != none and y == 0 { hdr } else if x == 0 { tint } else { none },
      ..(if title != none { (table.cell(colspan: 2, inset: (x: 7pt, y: 4.6pt))[#text(font: sans, size: 7.6pt, weight: 700, tracking: 0.18em, fill: white)[#upper(title)]],) } else { () }),
      ..c.enumerate().map(((i, x)) => if calc.even(i) { text(font: sans, size: 8.3pt, weight: 600, fill: acc, features: ("lnum", "tnum"))[#x] } else { text(font: sans, size: 8.5pt, features: ("lnum", "tnum"))[#x] }))
  ]
}

#let datatable(cols, header, keep: false, ..cells) = {
  let c = cells.pos()
  let n = cols.len()
  let nrows = calc.div-euclid(c.len(), n)
  let pad = if nrows >= 26 { 2.9pt } else { 4pt }
  block(width: 100%%, above: 9pt, below: 13pt, breakable: not keep)[
    #set par(justify: false, leading: 0.42em, spacing: 0.4em)
    #show table.cell: it => { set text(font: sans, size: 8.2pt, hyphenate: false, features: ("lnum", "tnum")); it }
    #table(columns: cols, inset: (x: 5.5pt, y: pad), stroke: (x, y) => (bottom: 0.3pt + rule),
      fill: (x, y) => if header.len() > 0 and y == 0 { hdr } else if calc.odd(y + (if header.len() > 0 { 1 } else { 0 })) { tint2 } else { none },
      ..(if header.len() > 0 { (table.header(..header.map(h => table.cell(text(fill: white, weight: 700, size: 7.8pt, tracking: 0.04em)[#h]))),) } else { () }),
      ..c)
  ]
}

#let toc-entry(lbl, num, title, bold: false) = context {
  let hits = query(lbl)
  if hits.len() > 0 {
    let loc = hits.first().location()
    let pg = pgnum(loc.page())
    link(lbl)[
      #block(above: 0pt, below: if bold { 5.5pt } else { 4.2pt })[
        #set par(justify: false, leading: 0.4em)
        #if num != none { box(width: 1.55em)[#text(font: sans, size: 9pt, weight: 700, fill: acc)[#num]] }
        #text(size: if bold { 11pt } else { 10.6pt }, weight: if bold { "semibold" } else { "regular" })[#title]
        #box(width: 1fr, repeat[#text(fill: luma(150))[ . ]])#h(3pt)#text(font: sans, size: 8.8pt)[#pg]
      ]
    ]
  }
}

#let toc-part(lbl, num, title) = context {
  let hits = query(lbl)
  if hits.len() > 0 {
    let loc = hits.first().location()
    let pg = pgnum(loc.page())
    link(lbl)[
      #block(above: 14pt, below: 6pt, sticky: true)[
        #set par(justify: false)
        #text(font: sans, size: 8pt, weight: 700, tracking: 0.22em, fill: acc2)[#num]#h(9pt)#text(font: display, size: 12pt, weight: 700, fill: acc)[#title]
        #h(1fr)#text(font: sans, size: 8.8pt)[#pg]
      ]
    ]
  }
}

#let footer-fn = context {
  let pg = here().page()
  let openers = query(heading.where(level: 1).or(heading.where(level: 2))).any(h => h.location().page() == pg)
  let parts = query(heading.where(level: 1)).any(h => h.location().page() == pg)
  let n = pgnum(pg)
  set text(font: sans, size: 8pt, fill: luma(60), tracking: 0.04em)
  if BLANKS.contains(pg) { none }
  else if parts { none }
  else if openers { align(center, n) }
  else if PRINT {
    let hs = query(heading.where(level: 2).before(here()))
    let short = if hs.len() > 0 { CH.at(str(hs.last().label)).at("short") } else { "" }
    line(length: 100%%, stroke: 0.25pt + rule)
    v(-3pt)
    if calc.odd(pg) { align(right)[#text(tracking: 0.12em, size: 7.2pt)[#upper(short)]#h(9pt)#strong[#n]] }
    else { align(left)[#strong[#n]#h(9pt)#text(tracking: 0.12em, size: 7.2pt)[#upper(BOOKTITLE)]] }
  } else {
    align(center, n)
  }
}
'''

PAGE_PRINT = '#set page(width: 6in, height: 9in, margin: (inside: 0.85in, outside: 0.62in, top: 0.72in, bottom: 0.9in), footer: footer-fn, footer-descent: 22%)\n'
PAGE_EBOOK = '#set page(width: 6in, height: 9in, margin: (x: 0.62in, top: 0.68in, bottom: 0.85in), footer: footer-fn, footer-descent: 22%)\n'


def build_typ(book, edition, cover_image=None, blanks=()):
    th = THEMES[edition]
    is_print = edition == "print"
    em = Emitter(book, edition)

    # heading metadata
    ch = {}
    pt = {}
    for p in book.parts:
        pt[f"part{p.num}"] = dict(num=f"PART {p.num}", chapters=[(c.label, c.title) for c in p.chapters])
    pt['appdiv'] = dict(num='REFERENCE', chapters=[(a.label, a.title) for a in book.appendices if a.kind == 'appendix'])
    entries = []

    def short(t):
        return t.split(":")[0].strip()

    for s in book.front:
        ch[f"front{len(entries)}"] = dict(label=None, short=short(s.title))
        entries.append((f"front{len(entries)}", s))
    ch_entries = {}
    for p in book.parts:
        for c in p.chapters:
            ch[f"ch{c.label}"] = dict(label=f"CHAPTER {c.label}", short=short(c.title))
    for s in book.appendices:
        key = "appdiv" if s.kind == "divider" else f"app{s.label}"
        ch[key] = dict(label=(f"APPENDIX {s.label}" if s.label else None), short=short(s.title), recto="no")
    for i, s in enumerate(book.back):
        ch[f"back{i}"] = dict(label=None, short=s.title, recto="no")
    ch["toc"] = dict(label=None, short="Contents")
    ch["lom"] = dict(label=None, short="List of maps")

    def dict_typ(d):
        def val(v):
            if v is None:
                return "none"
            if isinstance(v, str):
                return tstr(v)
            if isinstance(v, list):
                return "(" + ", ".join("(" + ", ".join(tstr(x) for x in t) + ",)" if isinstance(t, tuple) else tstr(t) for t in v) + ",)"
            return tstr(str(v))
        return "(" + ", ".join(f"{tstr(k)}: (" + ", ".join(f"{tstr(k2)}: {val(v2)}" for k2, v2 in v.items()) + ",)" for k, v in d.items()) + ",)"

    head = TEMPLATE % dict(
        **th, is_print="true" if is_print else "false", booktitle=tstr(book.title.upper()),
        ch=dict_typ(ch), pt=dict_typ(pt), blanks='(' + ''.join(f'{b}, ' for b in blanks) + '0,)', doctitle=tstr(book.title + ": " + book.subtitle), author=tstr(book.author))
    out = [head, PAGE_PRINT if is_print else PAGE_EBOOK]

    title_words = book.title.replace(" 2027", "").split()  # Dolomites Travel Guide
    big = title_words[0].upper()
    small = " ".join(title_words[1:]).upper()
    year = "2027"

    # ---------------- front pages
    if not is_print and cover_image:
        out.append(f'#page(margin: 0pt, footer: none)[#image({tstr(cover_image)}, width: 100%, height: 100%, fit: "cover")]\n')
    if is_print:
        out.append(f'''#page(footer: none)[
  #align(center + horizon)[
    #peaks(w: 40pt, c: acc)
    #v(14pt)
    #set par(justify: false)
    #text(font: display, size: 25pt, weight: 700, fill: acc)[Dolomites Travel Guide 2027]
  ]
]
#page(footer: none)[]
''')
    out.append(f'''#page(footer: none)[
  #align(center)[
    #v(1.05in)
    #peaks(w: 64pt, c: acc)
    #v(24pt)
    #text(font: display, size: 50pt, weight: 900, fill: acc, tracking: 0.04em)[{big}]
    #v(2pt)
    #text(font: sans, size: 13pt, weight: 600, tracking: 0.42em, fill: acc)[{small}]
    #v(10pt)
    #text(font: display, size: 20pt, weight: 400, fill: acc2, tracking: 0.3em)[{year}]
    #v(22pt)
    #line(length: 46pt, stroke: 1.1pt + acc2)
    #v(20pt)
    #block(width: 3.5in)[#set par(justify: false, leading: 0.5em)
      #text(font: display, size: 14.5pt, style: "italic", fill: luma(35))[{esc(book.subtitle)}]]
  ]
  #place(bottom + center, dy: -0.35in)[
    #text(font: sans, size: 10.5pt, weight: 600, tracking: 0.3em, fill: acc)[{esc(book.author.upper())}]
  ]
]
''')
    cp = Emitter(book, edition)
    cp.blocks(book.copyright)
    cp_body = ''.join(cp.out)
    credit_note = ("Photographs are used under free licences; credits are listed in Appendix F. "
                   "Maps contain data © OpenStreetMap contributors.")
    out.append(f'''#page(footer: none)[
  #set text(size: 9.6pt)
  #set par(leading: 0.5em, spacing: 0.65em)
  #v(1fr)
  #align(left)[
    #text(font: display, size: 12pt, weight: 700, fill: acc)[{esc(book.title)}]
    #v(2pt)
    #text(style: "italic")[{esc(book.subtitle)}]
    #v(10pt)
    #strong[2027 edition]
    #v(10pt)
    {cp_body}
    #text(size: 9pt)[{esc(credit_note)}]
  ]
]
''')

    # ---------------- contents
    out.append('#heading(level: 2, outlined: false)[Contents] <toc>\n')
    for p in book.parts:
        pass
    toc = []
    if book.front:
        for i, s in enumerate(book.front):
            toc.append(f'#toc-entry(<front{i}>, none, {tstr(s.title)})')
    for p in book.parts:
        toc.append(f'#toc-part(<part{p.num}>, "PART {p.num}", {tstr(p.title)})')
        for c in p.chapters:
            toc.append(f'#toc-entry(<ch{c.label}>, {tstr(c.label)}, {tstr(c.title)})')
    toc.append('#toc-part(<appdiv>, "", "Appendices")')
    for s in book.appendices:
        if s.kind == "appendix":
            toc.append(f'#toc-entry(<app{s.label}>, {tstr(s.label)}, {tstr(s.title)})')
    toc.append('#v(8pt)')
    for i, s in enumerate(book.back):
        toc.append(f'#toc-entry(<back{i}>, none, {tstr(s.title)}, bold: true)')
    toc.append('#toc-entry(<lom>, none, "List of maps", bold: true)')
    out.append("\n".join(toc) + "\n\n")

    # list of maps
    out.append('#heading(level: 2, outlined: false)[List of maps] <lom>\n')
    lom = []
    for fid, f in book.figures.items():
        if f.kind == "map":
            first = MAP_SHORT.get(fid) or re.split(r"(?<=[a-z0-9\)])\. ", f.caption)[0].rstrip(".")
            lom.append(f'#toc-entry(<fig-{fid}>, none, {tstr(first)})')
    out.append("\n".join(lom) + "\n\n")

    # ---------------- front sections, parts, chapters
    started_main = False

    def emit_section(sec, label, secs_key):
        e = Emitter(book, edition)
        if sec.kind == "appendix" and sec.label == "F":
            e.blocks_credits = True
        blocks = sec.blocks
        e.blocks(blocks)
        return "".join(e.out)

    def numbering_switch():
        return '#set page(numbering: "1")\n#counter(page).update(1)\n'

    for i, s_ in enumerate(book.front):
        if i == 0:
            out.append(f'#heading(level: 2, outlined: true)[{esc(s_.title)}] <front{i}>\n')
        else:
            out.append(f'#heading(level: 3, outlined: true)[{esc(s_.title)}] <front{i}>\n')
        out.append(emit_section(s_, i, "front"))
    first_part = True
    for p in book.parts:
        first_part = False
        out.append(f'#heading(level: 1, outlined: true)[{esc(p.title)}] <part{p.num}>\n')
        for c in p.chapters:
            out.append(f'#heading(level: 2, outlined: true)[{esc(c.title)}] <ch{c.label}>\n')
            out.append(emit_section(c, c.label, "ch"))
    for s in book.appendices:
        if s.kind == "divider":
            out.append(f'#heading(level: 1, outlined: true)[Appendices] <appdiv>\n')
            continue
        out.append(f'#heading(level: 2, outlined: true)[{esc(s.title)}] <app{s.label}>\n')
        if s.label == "F":
            out.append(credits_section(book, s, edition))
        else:
            out.append(emit_section(s, s.label, "app"))
    for i, s in enumerate(book.back):
        lvl = 2 if i == 0 else 3
        out.append(f'#heading(level: {lvl}, outlined: true)[{esc(s.title)}] <back{i}>\n')
        out.append(emit_section(s, i, "back"))
    return "".join(out)


def credits_section(book, s, edition):
    e = Emitter(book, edition)
    grouped = e.credits(s.blocks)
    for b in grouped:
        if b[0] == "credits":
            items = []
            for p in b[1]:
                items.append("#block(breakable: false, below: 3.6pt)[" + ti(p[1]) + "]")
            e.w("#[\n#set text(size: 7.4pt, font: sans)\n#set par(justify: false, leading: 0.4em)\n#columns(2, gutter: 14pt)[\n" + "\n".join(items) + "\n]\n]\n\n")
        else:
            e.blocks([b])
    return "".join(e.out)


def compile_pdf(typ_source, out_pdf, name):
    path = os.path.join(ROOT, "build", f"{name}.typ")
    open(path, "w", encoding="utf-8").write(typ_source)
    typst.compile(path, output=out_pdf, root=ROOT, font_paths=[FONT_DIR])
    return path
