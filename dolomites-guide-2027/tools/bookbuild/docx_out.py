"""DOCX builder (paperback and ebook editions) from the shared document model.

Print edition: 6x9 in, mirrored margins, odd/even running heads, chapters start on right-hand pages,
roman then arabic page numbers, a real Word table of contents (with cached entries).
Ebook edition: reflowable, no headers/footers, colour images, hyperlinked contents.
Real Word styles throughout (Heading 1-4, Caption, TOC 1-2), real bulleted/numbered lists, repeating table headers.
"""
import copy, os, re, subprocess, sys, tempfile

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT, WD_TAB_LEADER, WD_LINE_SPACING
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Emu, Inches, Pt, RGBColor

from .core import ROOT, load_book, inl_text
from .typ import col_weights, nbsp

SERIF, SANS, DISPLAY = "Garamond", "Calibri", "Georgia"
INK = RGBColor(0x14, 0x14, 0x14)
ACC_P = RGBColor(0x1E, 0x1E, 0x1E)  # print accent (near-black)
ACC_E = RGBColor(0x1F, 0x4D, 0x63)  # ebook accent
HDR_HEX = {"print": "262626", "ebook": "1F4D63"}
TINT_HEX = {"print": "EDEDED", "ebook": "E6EEF2"}
ZEBRA_HEX = {"print": "F6F6F6", "ebook": "F3F7F9"}
RULE_HEX = "A6A6A6"
BAR_HEX = {"wik": ("3C3C3C", "F0F0F0"), "important": ("000000", "E6E6E6"), "tip": ("6E6E6E", "F4F4F4"), "note": ("808080", "F6F6F6")}
BAR_HEX_E = {"wik": ("C8742F", "FBF1E6"), "important": ("A53A2C", "F9EBE8"), "tip": ("3C7A5A", "EAF4EE"), "note": ("6C7F89", "F3F7F9")}


# ------------------------------------------------------------------ low-level helpers
def set_cell_shade(cell, hex_fill):
    tcPr = cell._tc.get_or_add_tcPr()
    for old in tcPr.findall(qn("w:shd")):
        tcPr.remove(old)
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill)
    tcPr.append(shd)


def set_cell_borders(cell, **kw):
    tcPr = cell._tc.get_or_add_tcPr()
    b = tcPr.find(qn("w:tcBorders"))
    if b is None:
        b = OxmlElement("w:tcBorders")
        tcPr.append(b)
    for edge in ("top", "left", "bottom", "right"):
        spec = kw.get(edge)
        el = b.find(qn(f"w:{edge}"))
        if el is None:
            el = OxmlElement(f"w:{edge}")
            b.append(el)
        if spec is None:
            el.set(qn("w:val"), "nil")
        else:
            sz, color = spec
            el.set(qn("w:val"), "single")
            el.set(qn("w:sz"), str(sz))
            el.set(qn("w:space"), "0")
            el.set(qn("w:color"), color)


def set_cell_margins(table, top=50, bottom=50, left=90, right=90):
    tblPr = table._tbl.tblPr
    m = OxmlElement("w:tblCellMar")
    for k, v in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        e = OxmlElement(f"w:{k}")
        e.set(qn("w:w"), str(v))
        e.set(qn("w:type"), "dxa")
        m.append(e)
    tblPr.append(m)


def set_table_fixed(table, widths_twips):
    tbl = table._tbl
    tblPr = tbl.tblPr
    lay = OxmlElement("w:tblLayout")
    lay.set(qn("w:type"), "fixed")
    tblPr.append(lay)
    w = tblPr.find(qn("w:tblW"))
    if w is None:
        w = OxmlElement("w:tblW")
        tblPr.append(w)
    w.set(qn("w:w"), str(sum(widths_twips)))
    w.set(qn("w:type"), "dxa")
    grid = tbl.tblGrid
    for i, gc in enumerate(grid.findall(qn("w:gridCol"))):
        gc.set(qn("w:w"), str(widths_twips[i]))
    for row in table.rows:
        for i, c in enumerate(row.cells):
            if i < len(widths_twips):
                c.width = Emu(int(widths_twips[i] * 635))


def row_no_split(row):
    trPr = row._tr.get_or_add_trPr()
    e = OxmlElement("w:cantSplit")
    trPr.append(e)


def row_header(row):
    trPr = row._tr.get_or_add_trPr()
    e = OxmlElement("w:tblHeader")
    trPr.append(e)


def para_border(p, side="bottom", sz=6, color="808080", space=4):
    pPr = p._p.get_or_add_pPr()
    b = pPr.find(qn("w:pBdr"))
    if b is None:
        b = OxmlElement("w:pBdr")
        pPr.append(b)
    e = OxmlElement(f"w:{side}")
    e.set(qn("w:val"), "single")
    e.set(qn("w:sz"), str(sz))
    e.set(qn("w:space"), str(space))
    e.set(qn("w:color"), color)
    b.append(e)


def add_field(run, instr):
    f1 = OxmlElement("w:fldChar")
    f1.set(qn("w:fldCharType"), "begin")
    it = OxmlElement("w:instrText")
    it.set(qn("xml:space"), "preserve")
    it.text = f" {instr} "
    f2 = OxmlElement("w:fldChar")
    f2.set(qn("w:fldCharType"), "separate")
    t = OxmlElement("w:t")
    t.text = "1"
    f3 = OxmlElement("w:fldChar")
    f3.set(qn("w:fldCharType"), "end")
    for el in (f1, it, f2, t, f3):
        run._r.append(el)


def set_style_font(style, name, size=None, bold=None, italic=None, color=None, caps=None, spacing=None):
    f = style.font
    f.name = name
    rPr = style.element.get_or_add_rPr()
    rf = rPr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rPr.insert(0, rf)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rf.set(qn(a), name)
    for a in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
        if rf.get(qn(a)) is not None:
            del rf.attrib[qn(a)]
    if size is not None:
        f.size = Pt(size)
    if bold is not None:
        f.bold = bold
    if italic is not None:
        f.italic = italic
    if color is not None:
        f.color.rgb = color
    if caps is not None:
        f.small_caps = caps
    if spacing is not None:
        sp = OxmlElement("w:spacing")
        sp.set(qn("w:val"), str(int(spacing * 20)))
        rPr.append(sp)


SETTINGS_ORDER = ["writeProtection", "view", "zoom", "removePersonalInformation", "removeDateAndTime", "doNotDisplayPageBoundaries",
                  "displayBackgroundShape", "printPostScriptOverText", "printFractionalCharacterWidth", "printFormsData", "embedTrueTypeFonts",
                  "embedSystemFonts", "saveSubsetFonts", "saveFormsData", "mirrorMargins", "alignBordersAndEdges", "bordersDoNotSurroundHeader",
                  "bordersDoNotSurroundFooter", "gutterAtTop", "hideSpellingErrors", "hideGrammaticalErrors", "activeWritingStyle", "proofState",
                  "formsDesign", "attachedTemplate", "linkStyles", "stylePaneFormatFilter", "stylePaneSortMethod", "documentType", "mailMerge",
                  "revisionView", "trackRevisions", "doNotTrackMoves", "doNotTrackFormatting", "documentProtection", "autoFormatOverride",
                  "styleLockTheme", "styleLockQFSet", "defaultTabStop", "autoHyphenation", "consecutiveHyphenLimit", "hyphenationZone",
                  "doNotHyphenateCaps", "showEnvelope", "summaryLength", "clickAndTypeStyle", "defaultTableStyle", "evenAndOddHeaders",
                  "bookFoldRevPrinting", "bookFoldPrinting", "bookFoldPrintingSheets", "drawingGridHorizontalSpacing",
                  "drawingGridVerticalSpacing", "displayHorizontalDrawingGridEvery", "displayVerticalDrawingGridEvery",
                  "doNotUseMarginsForDrawingGridOrigin", "drawingGridHorizontalOrigin", "drawingGridVerticalOrigin", "doNotShadeFormData",
                  "noPunctuationKerning", "characterSpacingControl", "printTwoOnOne", "strictFirstAndLastChars", "noLineBreaksAfter",
                  "noLineBreaksBefore", "savePreviewPicture", "doNotValidateAgainstSchema", "saveInvalidXml", "ignoreMixedContent",
                  "alwaysShowPlaceholderText", "doNotDemarcateInvalidXml", "saveXmlDataOnly", "useXSLTWhenSaving", "saveThroughXslt",
                  "showXMLTags", "alwaysMergeEmptyNamespace", "updateFields", "hdrShapeDefaults", "footnotePr", "endnotePr", "compat",
                  "docVars", "rsids", "mathPr", "attachedSchema", "themeFontLang", "clrSchemeMapping", "doNotIncludeSubdocsInStats",
                  "doNotAutoCompressPictures", "forceUpgrade", "captions", "readModeInkLockDown", "smartTagType", "schemaLibrary",
                  "shapeDefaults", "doNotEmbedSmartTags", "decimalSymbol", "listSeparator"]


def add_setting(settings_el, name, **attrs):
    el = OxmlElement(f"w:{name}")
    for k, v in attrs.items():
        el.set(qn(f"w:{k}"), str(v))
    old = settings_el.find(qn(f"w:{name}"))
    if old is not None:
        settings_el.remove(old)
    settings_el.append(el)


def sort_settings(settings_el):
    kids = list(settings_el)
    def key(e):
        tag = e.tag.split("}")[1]
        return SETTINGS_ORDER.index(tag) if tag in SETTINGS_ORDER else 999
    kids.sort(key=key)
    for k in kids:
        settings_el.remove(k)
    for k in kids:
        settings_el.append(k)


# ------------------------------------------------------------------ builder
class DocBuilder:
    def __init__(self, book, edition, toc_pages=None):
        self.book = book
        self.ed = edition
        self.print = edition == "print"
        self.toc_pages = toc_pages or {}
        self.doc = Document()
        self.bm_id = 100
        self.toc_entries = []  # (level, title, bookmark)
        self.accent = ACC_P if self.print else ACC_E
        self.text_w = Inches(4.53 if self.print else 4.6)
        self.num_ids = {}
        self.next_num = 50
        self.heading_pages = {}
        self._setup()

    # ---- document, styles, numbering
    def _setup(self):
        d = self.doc
        s = d.sections[0]
        s.page_width, s.page_height = Inches(6), Inches(9)
        if self.print:
            s.left_margin, s.right_margin = Inches(0.85), Inches(0.62)  # inside, outside (mirrored)
            s.top_margin, s.bottom_margin = Inches(0.75), Inches(0.85)
            s.header_distance, s.footer_distance = Inches(0.4), Inches(0.4)
        else:
            s.left_margin = s.right_margin = Inches(0.7)
            s.top_margin = s.bottom_margin = Inches(0.8)
        st = d.styles
        n = st["Normal"]
        set_style_font(n, SERIF, 11.5, color=INK)
        n.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        n.paragraph_format.space_after = Pt(4.5)
        n.paragraph_format.space_before = Pt(0)
        n.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
        n.paragraph_format.line_spacing = 1.08
        n.paragraph_format.widow_control = True
        rPr = n.element.get_or_add_rPr()
        lang = OxmlElement("w:lang")
        lang.set(qn("w:val"), "en-GB")
        rPr.append(lang)

        def hstyle(name, size, before, after, italic=False, color=None, align=WD_ALIGN_PARAGRAPH.LEFT, caps=None):
            h = st[name]
            set_style_font(h, DISPLAY, size, bold=True, italic=italic, color=color or self.accent, caps=caps)
            pf = h.paragraph_format
            pf.space_before, pf.space_after = Pt(before), Pt(after)
            pf.keep_with_next = True
            pf.keep_together = True
            pf.alignment = align
            pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
            return h

        h1 = hstyle("Heading 1", 28, 0, 14, align=WD_ALIGN_PARAGRAPH.CENTER)
        hstyle("Heading 2", 25, 0, 6)
        h3 = hstyle("Heading 3", 14.5, 20, 7)
        hstyle("Heading 4", 12, 13, 4, italic=True)
        for nm in ("Heading 3",):
            para_border_style(st[nm], "bottom", 4, RULE_HEX, 3)

        def custom(name, base="Normal", font=SERIF, size=None, bold=None, italic=None, color=None, align=None, before=None, after=None,
                   keep_next=None, spacing=None, caps=None, line=None):
            from docx.enum.style import WD_STYLE_TYPE
            sty = st.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
            sty.base_style = st[base]
            set_style_font(sty, font, size, bold, italic, color, caps=caps, spacing=spacing)
            pf = sty.paragraph_format
            if align is not None:
                pf.alignment = align
            if before is not None:
                pf.space_before = Pt(before)
            if after is not None:
                pf.space_after = Pt(after)
            if keep_next is not None:
                pf.keep_with_next = keep_next
            if line is not None:
                pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
                pf.line_spacing = line
            return sty

        L, C = WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER
        custom("Lead", italic=True, size=12.2, line=1.12, after=6)
        custom("Figure", align=C, before=8, after=2, keep_next=True)
        custom("Figure Caption", font=SANS, size=8.2, color=RGBColor(0x37, 0x37, 0x37), align=L, before=0, after=10, line=1.0)
        custom("Table Text", font=SANS, size=8.4, align=L, before=0, after=0, line=1.0)
        custom("Callout Text", size=10.4, align=WD_ALIGN_PARAGRAPH.JUSTIFY, before=0, after=3, line=1.05)
        custom("Callout Label", font=SANS, size=7.4, bold=True, align=L, before=0, after=2, spacing=1.2, keep_next=True)
        custom("List Item", before=0, after=2.5, align=L)
        custom("Credits", font=SANS, size=7.7, align=L, before=0, after=4, line=1.0)
        custom("Front Heading", font=DISPLAY, size=25, bold=True, color=self.accent, align=L, before=0, after=14, keep_next=True)
        custom("Part Number", font=SANS, size=9.5, bold=True, color=RGBColor(0x60, 0x60, 0x60), align=C, spacing=3.2, before=0, after=8)
        custom("Part Entry", font=SANS, size=9.6, color=RGBColor(0x37, 0x37, 0x37), align=C, before=0, after=2)
        custom("Title Big", font=DISPLAY, size=38, bold=True, color=self.accent, align=C, before=0, after=0, spacing=1)
        custom("Title Small", font=SANS, size=14, bold=True, color=self.accent, align=C, before=0, after=6, spacing=8)
        custom("Title Sub", font=DISPLAY, size=15, italic=True, color=RGBColor(0x30, 0x30, 0x30), align=C, before=14, after=0)
        custom("Title Author", font=SANS, size=12, bold=True, color=self.accent, align=C, before=0, after=0, spacing=4.5)
        custom("Copyright Text", size=9.6, align=L, before=0, after=6, line=1.04)
        custom("Header Text", font=SANS, size=7.4, align=L, before=0, after=0, spacing=1.4, color=RGBColor(0x40, 0x40, 0x40))
        custom("Footer Text", font=SANS, size=8.4, align=L, before=0, after=0, color=RGBColor(0x40, 0x40, 0x40))
        for nm, lvl, left, size, bold in (("TOC 1", 1, 0, 11.5, True), ("TOC 2", 2, 0.18, 10.6, False)):
            try:
                t = st[nm]
            except KeyError:
                from docx.enum.style import WD_STYLE_TYPE
                t = st.add_style(nm, WD_STYLE_TYPE.PARAGRAPH)
                t.base_style = st["Normal"]
            set_style_font(t, SERIF if lvl == 2 else DISPLAY, size, bold=bold, color=self.accent if lvl == 1 else INK)
            t.paragraph_format.alignment = L
            t.paragraph_format.left_indent = Inches(left)
            t.paragraph_format.space_before = Pt(8 if lvl == 1 else 0)
            t.paragraph_format.space_after = Pt(2.2)
            t.paragraph_format.tab_stops.add_tab_stop(self.text_w, WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
            t.paragraph_format.keep_with_next = lvl == 1
        # numbering definitions
        self._init_numbering()
        # settings
        se = d.settings.element
        if self.print:
            add_setting(se, "mirrorMargins")
            add_setting(se, "evenAndOddHeaders")
        add_setting(se, "autoHyphenation")
        add_setting(se, "consecutiveHyphenLimit", val=2)
        add_setting(se, "hyphenationZone", val=360)
        add_setting(se, "updateFields")
        sort_settings(se)
        cp = d.core_properties
        cp.title = f"{self.book.title}: {self.book.subtitle}"
        cp.author = self.book.author
        cp.subject = "Travel guide to Italy's Dolomites, 2027 edition"
        cp.keywords = "Dolomites, travel guide, Italy, 2027"
        cp.language = "en-GB"

    def _init_numbering(self):
        np_ = self.doc.part.numbering_part
        num = np_.numbering_definitions._numbering
        bullet = parse_xml(
            f'<w:abstractNum {nsdecls("w")} w:abstractNumId="900"><w:multiLevelType w:val="hybridMultilevel"/>'
            f'<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="•"/><w:lvlJc w:val="left"/>'
            f'<w:pPr><w:ind w:left="300" w:hanging="220"/></w:pPr><w:rPr><w:rFonts w:ascii="{SERIF}" w:hAnsi="{SERIF}"/></w:rPr></w:lvl></w:abstractNum>')
        decimal = parse_xml(
            f'<w:abstractNum {nsdecls("w")} w:abstractNumId="901"><w:multiLevelType w:val="hybridMultilevel"/>'
            f'<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="decimal"/><w:lvlText w:val="%1."/><w:lvlJc w:val="left"/>'
            f'<w:pPr><w:ind w:left="340" w:hanging="300"/></w:pPr><w:rPr><w:rFonts w:ascii="{SANS}" w:hAnsi="{SANS}"/><w:b/><w:sz w:val="18"/></w:rPr></w:lvl></w:abstractNum>')
        first_num = num.find(qn("w:num"))
        for a in (bullet, decimal):
            if first_num is not None:
                first_num.addprevious(a)
            else:
                num.append(a)
        num.append(parse_xml(f'<w:num {nsdecls("w")} w:numId="900"><w:abstractNumId w:val="900"/></w:num>'))
        self.bullet_num = 900

    def new_ordered_num(self, start):
        nid = 950 + self.next_num
        self.next_num += 1
        num = self.doc.part.numbering_part.numbering_definitions._numbering
        num.append(parse_xml(
            f'<w:num {nsdecls("w")} w:numId="{nid}"><w:abstractNumId w:val="901"/>'
            f'<w:lvlOverride w:ilvl="0"><w:startOverride w:val="{start}"/></w:lvlOverride></w:num>'))
        return nid

    # ---- runs and paragraphs
    def runs(self, p, nodes, bold=False, italic=False, size=None, color=None, font=None):
        for n in nodes:
            k = n[0]
            if k == "t":
                r = p.add_run(nbsp(n[1]))
                r.bold = bold or None
                r.italic = italic or None
                if size:
                    r.font.size = Pt(size)
                if color is not None:
                    r.font.color.rgb = color
                if font:
                    r.font.name = font
            elif k == "b":
                self.runs(p, n[1], True, italic, size, color, font)
            elif k == "i":
                self.runs(p, n[1], bold, True, size, color, font)
            elif k == "a":
                self.runs(p, n[2], bold, italic, size, color, font)
            elif k == "br":
                p.add_run().add_break(WD_BREAK.LINE)

    def para(self, nodes, style="Normal", **kw):
        p = self.doc.add_paragraph(style=style)
        self.runs(p, nodes, **kw)
        return p

    def bookmark(self, p, name):
        self.bm_id += 1
        s = OxmlElement("w:bookmarkStart")
        s.set(qn("w:id"), str(self.bm_id))
        s.set(qn("w:name"), name)
        e = OxmlElement("w:bookmarkEnd")
        e.set(qn("w:id"), str(self.bm_id))
        p._p.insert(1 if p._p.pPr is not None else 0, s)
        p._p.append(e)

    def heading(self, text, level, toc=True, page_break=False):
        p = self.doc.add_paragraph(style=f"Heading {level}")
        r = p.add_run(nbsp(text))
        if toc and level <= 2:
            name = f"_Toc{len(self.toc_entries) + 1:04d}"
            self.bookmark(p, name)
            self.toc_entries.append((level, text, name))
        return p

    # ---- sections
    def section(self, kind="odd", hdr_odd=None, hdr_even=None, fmt="decimal", start=None, first_blank=True, first_footer=True):
        d = self.doc
        sec = d.add_section(WD_SECTION.ODD_PAGE if (self.print and kind == "odd") else WD_SECTION.NEW_PAGE)
        self._section_hf(sec, hdr_odd, hdr_even, fmt, start, first_blank, first_footer)
        return sec

    def _section_hf(self, sec, hdr_odd, hdr_even, fmt, start, first_blank=True, first_footer=True):
        sectPr = sec._sectPr
        for old in sectPr.findall(qn("w:pgNumType")):
            sectPr.remove(old)
        pg = OxmlElement("w:pgNumType")
        pg.set(qn("w:fmt"), fmt)
        if start is not None:
            pg.set(qn("w:start"), str(start))
        # pgNumType must come before cols/titlePg etc. - insert after pgMar
        mar = sectPr.find(qn("w:pgMar"))
        mar.addnext(pg)
        if not self.print:
            return
        sec.different_first_page_header_footer = True
        for part, link in ((sec.header, 0), (sec.even_page_header, 0), (sec.first_page_header, 0), (sec.footer, 0),
                           (sec.even_page_footer, 0), (sec.first_page_footer, 0)):
            part.is_linked_to_previous = False
        self._fill_hf(sec.header, hdr_odd, right=True, number=False)
        self._fill_hf(sec.even_page_header, hdr_even, right=False, number=False)
        self._fill_hf(sec.first_page_header, None, right=True, number=False)
        self._fill_hf(sec.footer, None, right=True, number=True)
        self._fill_hf(sec.even_page_footer, None, right=False, number=True)
        self._fill_hf(sec.first_page_footer, None, right=None, number=first_footer)

    def _fill_hf(self, part, text, right, number, style=None):
        for p in list(part.paragraphs)[1:]:
            p._p.getparent().remove(p._p)
        p = part.paragraphs[0]
        for r in list(p.runs):
            r._r.getparent().remove(r._r)
        if number:
            p.style = self.doc.styles["Footer Text"]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if right is None else (WD_ALIGN_PARAGRAPH.RIGHT if right else WD_ALIGN_PARAGRAPH.LEFT)
            r = p.add_run()
            r.bold = True
            add_field(r, "PAGE")
        else:
            p.style = self.doc.styles["Header Text"]
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if right else WD_ALIGN_PARAGRAPH.LEFT
            if text:
                r = p.add_run(text.upper())
                para_border(p, "bottom", 4, "9A9A9A", 4)

    # ---- content blocks
    def figure(self, fid):
        f = self.book.figures[fid]
        path = self.sized_image(f)
        p = self.doc.add_paragraph(style="Figure")
        r = p.add_run()
        maxh = Inches(6.0 if f.kind == "map" else 4.1)
        w = self.text_w
        if f.h / f.w * w > maxh:
            pic = r.add_picture(path, height=maxh)
        else:
            pic = r.add_picture(path, width=w)
        pic._inline.docPr.set("descr", f.caption)
        pic._inline.docPr.set("title", f.label)
        cp = self.doc.add_paragraph(style="Figure Caption")
        rr = cp.add_run(f.label.upper() + "  ")
        rr.bold = True
        rr.font.size = Pt(7.4)
        rr.font.color.rgb = self.accent
        cp.add_run(nbsp(f.caption))
        cp.paragraph_format.keep_together = True

    def sized_image(self, f):
        """Image at exactly the resolution it prints at (300 dpi for the paperback), cached on disk."""
        from PIL import Image
        src = f.path("print" if self.print else "ebook")
        want = 1400 if self.print else 1200
        out_dir = os.path.join(ROOT, "build", "docx_img_" + self.ed)
        os.makedirs(out_dir, exist_ok=True)
        ext = ".png" if (self.print and src.endswith(".png")) else ".jpg"
        out = os.path.join(out_dir, f.id + ext)
        if not os.path.exists(out):
            im = Image.open(src)
            if im.width > want:
                im = im.resize((want, int(im.height * want / im.width)), Image.LANCZOS)
            if ext == ".png":
                im.convert("L").save(out, optimize=True, dpi=(300, 300))
            else:
                im.convert("L" if (self.print and im.mode == "L") else "RGB").save(out, quality=84, optimize=True, dpi=(300, 300))
        return out

    def blocks(self, bl):
        pending = []
        prev = None
        for b in bl:
            k = b[0]
            if k == "figure":
                if prev in ("h2", "h3", "h4", "figure", None) or pending:
                    pending.append(b[1])
                else:
                    self.figure(b[1])
                prev = "figure"
                continue
            self.block(b)
            if k not in ("h2", "h3", "h4"):
                for f in pending:
                    self.figure(f)
                pending = []
            prev = k
        for f in pending:
            self.figure(f)

    def block(self, b):
        k = b[0]
        if k == "h2":
            self.doc.add_paragraph(style="Heading 3").add_run(nbsp(inl_text(b[1])))
        elif k == "h3":
            self.doc.add_paragraph(style="Heading 4").add_run(nbsp(inl_text(b[1])))
        elif k == "h4":
            self.doc.add_paragraph(style="Heading 4").add_run(nbsp(inl_text(b[1])))
        elif k == "p":
            self.para(b[1])
        elif k == "lead":
            self.para(b[1], "Lead")
        elif k == "ul":
            self.list_items(b[1], self.bullet_num)
        elif k == "ol":
            self.list_items(b[2], self.new_ordered_num(b[1]))
        elif k == "table":
            self.table(b)
        elif k == "callout":
            self.callout(b)
        elif k == "hr":
            p = self.doc.add_paragraph(style="Normal")
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.add_run("•  •  •")

    def list_items(self, items, num_id, tight_after=True):
        last = None
        for it in items:
            first = True
            for x in it:
                if x[0] == "p":
                    p = self.doc.add_paragraph(style="List Item")
                    self.runs(p, x[1])
                    if first:
                        pPr = p._p.get_or_add_pPr()
                        numPr = OxmlElement("w:numPr")
                        il = OxmlElement("w:ilvl")
                        il.set(qn("w:val"), "0")
                        ni = OxmlElement("w:numId")
                        ni.set(qn("w:val"), str(num_id))
                        numPr.append(il)
                        numPr.append(ni)
                        pPr.append(numPr)
                    else:
                        p.paragraph_format.left_indent = Inches(0.2)
                    first = False
                    last = p
                else:
                    self.block(x)
        if last is not None:
            last.paragraph_format.space_after = Pt(8)

    def cell_text(self, cell, nodes, bold=False, color=None, size=None, style="Table Text"):
        p = cell.paragraphs[0]
        p.style = self.doc.styles[style]
        self.runs(p, nodes, bold=bold, color=color, size=size)
        return p

    def table(self, b):
        _, kind, title, header, rows = b
        hdr = HDR_HEX[self.ed]
        W = int(self.text_w.inches * 1440)
        if kind in ("glance", "kv"):
            lab = max((len(inl_text(r[0])) for r in rows), default=8)
            kw = int((1.0 if lab <= 14 else (1.18 if lab <= 20 else 1.4)) * 1440)
            nrows = len(rows) + (1 if title else 0)
            t = self.doc.add_table(rows=nrows, cols=2)
            set_table_fixed(t, [kw, W - kw])
            set_cell_margins(t, 45, 45, 100, 100)
            t.alignment = WD_TABLE_ALIGNMENT.CENTER
            i0 = 0
            if title:
                c = t.rows[0].cells[0].merge(t.rows[0].cells[1])
                set_cell_shade(c, hdr)
                p = c.paragraphs[0]
                p.style = self.doc.styles["Table Text"]
                r = p.add_run(title.upper())
                r.bold = True
                r.font.size = Pt(7.6)
                r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                p.paragraph_format.keep_with_next = True
                i0 = 1
            for i, row in enumerate(rows):
                tr = t.rows[i0 + i]
                row_no_split(tr)
                a, bcell = tr.cells
                set_cell_shade(a, TINT_HEX[self.ed])
                self.cell_text(a, row[0], bold=True, size=8.3)
                self.cell_text(bcell, row[1])
                for c in (a, bcell):
                    set_cell_borders(c, bottom=(2, RULE_HEX) if i < len(rows) - 1 else (6, "8A8A8A"), top=None, left=None, right=None)
                if i < len(rows) - 1:
                    for c in tr.cells:
                        for p in c.paragraphs:
                            p.paragraph_format.keep_with_next = True
            self._after_table()
            return
        ncol = max([len(header)] + [len(r) for r in rows])
        wts = col_weights(rows, header, ncol, total=float(W) / 20)
        widths = [int(round(x / 100 * W)) for x in wts]
        widths[-1] += W - sum(widths)
        t = self.doc.add_table(rows=len(rows) + (1 if header else 0), cols=ncol)
        set_table_fixed(t, widths)
        set_cell_margins(t, 40, 40, 80, 80)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        i0 = 0
        if header:
            tr = t.rows[0]
            row_header(tr)
            row_no_split(tr)
            for j, c in enumerate(tr.cells):
                set_cell_shade(c, hdr)
                p = c.paragraphs[0]
                p.style = self.doc.styles["Table Text"]
                self.runs(p, header[j] if j < len(header) else [], bold=True, color=RGBColor(0xFF, 0xFF, 0xFF), size=7.9)
                p.paragraph_format.keep_with_next = True
            i0 = 1
        for i, row in enumerate(rows):
            tr = t.rows[i0 + i]
            row_no_split(tr)
            for j, c in enumerate(tr.cells):
                self.cell_text(c, row[j] if j < len(row) else [])
                if i % 2 == 1:
                    set_cell_shade(c, ZEBRA_HEX[self.ed])
                set_cell_borders(c, bottom=(2, RULE_HEX), top=None, left=None, right=None)
        if len(rows) <= 8:
            for tr in t.rows[:-1]:
                for c in tr.cells:
                    for p in c.paragraphs:
                        p.paragraph_format.keep_with_next = True
        self._after_table()

    def _after_table(self):
        p = self.doc.add_paragraph(style="Normal")
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
        p.paragraph_format.line_spacing = Pt(7)

    def callout(self, b):
        _, kind, label, inner = b
        bar, fill = (BAR_HEX if self.print else BAR_HEX_E).get(kind, BAR_HEX["note"])
        W = int(self.text_w.inches * 1440)
        t = self.doc.add_table(rows=1, cols=1)
        set_table_fixed(t, [W])
        set_cell_margins(t, 90, 90, 200, 160)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        c = t.rows[0].cells[0]
        row_no_split(t.rows[0])
        set_cell_shade(c, fill)
        set_cell_borders(c, left=(28, bar), top=None, bottom=None, right=None)
        first = True
        if label:
            p = c.paragraphs[0]
            p.style = self.doc.styles["Callout Label"]
            r = p.add_run(label.upper())
            r.font.color.rgb = RGBColor.from_string(bar)
            first = False
        for x in inner:
            if x[0] in ("p", "lead"):
                p = c.paragraphs[0] if first else c.add_paragraph()
                first = False
                p.style = self.doc.styles["Callout Text"]
                self.runs(p, x[1])
            elif x[0] in ("ul", "ol"):
                for it in (x[1] if x[0] == "ul" else x[2]):
                    p = c.paragraphs[0] if first else c.add_paragraph()
                    first = False
                    p.style = self.doc.styles["Callout Text"]
                    p.paragraph_format.left_indent = Inches(0.16)
                    p.paragraph_format.first_line_indent = Inches(-0.16)
                    p.add_run("• ")
                    for y in it:
                        if y[0] == "p":
                            self.runs(p, y[1])
        self._after_table()

    # ---- pieces
    def title_page(self):
        d = self.doc
        words = self.book.title.replace(" 2027", "").split()
        for _ in range(5):
            d.add_paragraph(style="Normal")
        d.add_paragraph(style="Title Big").add_run(words[0].upper())
        d.add_paragraph(style="Title Small").add_run(" ".join(words[1:]).upper())
        p = d.add_paragraph(style="Title Small")
        r = p.add_run("2027")
        r.font.name = DISPLAY
        r.font.size = Pt(18)
        r.bold = False
        r.font.color.rgb = RGBColor(0x60, 0x60, 0x60)
        d.add_paragraph(style="Title Sub").add_run(self.book.subtitle)
        for _ in range(7):
            d.add_paragraph(style="Normal")
        d.add_paragraph(style="Title Author").add_run(self.book.author.upper())

    def copyright_page(self):
        d = self.doc
        p = d.add_paragraph(style="Page Break")if False else d.add_paragraph(style="Normal")
        p.add_run().add_break(WD_BREAK.PAGE)
        for _ in range(8):
            d.add_paragraph(style="Normal")
        p = d.add_paragraph(style="Copyright Text")
        r = p.add_run(self.book.title)
        r.bold = True
        r.font.name = DISPLAY
        r.font.size = Pt(11)
        d.add_paragraph(style="Copyright Text").add_run(self.book.subtitle).italic = True
        d.add_paragraph(style="Copyright Text").add_run("2027 edition").bold = True
        for b in self.book.copyright:
            if b[0] == "p":
                self.para(b[1], "Copyright Text")
        d.add_paragraph(style="Copyright Text").add_run(
            "Photographs are used under free licences; credits are listed in Appendix F. Maps contain data © OpenStreetMap contributors.")

    def toc_placeholder(self):
        """Mark the place where the contents go; filled after all headings are known."""
        self.toc_anchor = self.doc.add_paragraph(style="Normal")

    def fill_toc(self, entries, lom_entries):
        """Insert the TOC field with cached entries before toc_anchor."""
        anchor = self.toc_anchor._p
        paras = []
        first = True
        n = len(entries)
        for i, (level, text, bm) in enumerate(entries):
            p = OxmlElement("w:p")
            pPr = OxmlElement("w:pPr")
            ps = OxmlElement("w:pStyle")
            ps.set(qn("w:val"), "TOC1" if level == 1 else "TOC2")
            pPr.append(ps)
            p.append(pPr)
            if first:
                for kind, instr in (("begin", None), ("instr", ' TOC \\o "1-2" \\h \\z \\u '), ("separate", None)):
                    r = OxmlElement("w:r")
                    if kind == "instr":
                        it = OxmlElement("w:instrText")
                        it.set(qn("xml:space"), "preserve")
                        it.text = instr
                        r.append(it)
                    else:
                        fc = OxmlElement("w:fldChar")
                        fc.set(qn("w:fldCharType"), kind)
                        r.append(fc)
                    p.append(r)
                first = False
            h = OxmlElement("w:hyperlink")
            h.set(qn("w:anchor"), bm)
            h.set(qn("w:history"), "1")
            for part in (text, "\t", self.toc_pages.get(bm, "")):
                r = OxmlElement("w:r")
                if part == "\t":
                    r.append(OxmlElement("w:tab"))
                else:
                    t = OxmlElement("w:t")
                    t.set(qn("xml:space"), "preserve")
                    t.text = part
                    r.append(t)
                h.append(r)
            p.append(h)
            if i == n - 1:
                r = OxmlElement("w:r")
                fc = OxmlElement("w:fldChar")
                fc.set(qn("w:fldCharType"), "end")
                r.append(fc)
                p.append(r)
            paras.append(p)
        for p in paras:
            anchor.addprevious(p)
        anchor.getparent().remove(anchor)

    # ---- the whole book
    def build(self):
        b = self.book
        d = self.doc
        bt = b.title
        # section 0: title page + copyright, roman numerals, no running heads
        self._section_hf(d.sections[0], None, None, "lowerRoman", 1, first_footer=False)
        self.title_page()
        self.copyright_page()
        # contents
        self.section("odd", None, None, "lowerRoman")
        d.add_paragraph(style="Front Heading").add_run("Contents")
        self.toc_placeholder()
        lom = d.add_paragraph(style="Front Heading")
        lom.paragraph_format.page_break_before = True
        lom.add_run("List of maps")
        for fid, f in b.figures.items():
            if f.kind == "map":
                short = MAP_NAMES.get(fid) or f.caption.split(". ")[0].rstrip(".")
                p = d.add_paragraph(style="TOC 2")
                p.paragraph_format.left_indent = Inches(0)
                p.add_run(f"{f.label}   {short}")
        # front sections
        for i, s in enumerate(b.front):
            if i == 0:
                self.section("odd", s.title, bt, "lowerRoman")
                self.heading(s.title, 2)
            else:
                self.doc.add_paragraph(style="Heading 3").add_run(nbsp(s.title))
            self.blocks(s.blocks)
        # parts and chapters
        first_main = True
        for p in b.parts:
            self.section("odd", None, None, "decimal", 1 if first_main else None, first_footer=False)
            first_main = False
            for _ in range(9):
                d.add_paragraph(style="Normal")
            d.add_paragraph(style="Part Number").add_run(f"PART {p.num}")
            self.heading(p.title, 1)
            for c in p.chapters:
                d.add_paragraph(style="Part Entry").add_run(f"{c.label}    {c.title}")
            for c in p.chapters:
                short = c.title.split(":")[0]
                self.section("odd", short, bt, "decimal")
                p_ = self.heading(f"{c.label}. {c.title}", 2)
                p_.paragraph_format.space_before = Pt(60)
                para_border(p_, "bottom", 8, "404040", 8)
                p_.paragraph_format.space_after = Pt(16)
                self.blocks(c.blocks)
        # appendices
        for s in b.appendices:
            if s.kind == "divider":
                self.section("odd", None, None, "decimal", first_footer=False)
                for _ in range(9):
                    d.add_paragraph(style="Normal")
                d.add_paragraph(style="Part Number").add_run("REFERENCE")
                self.heading("Appendices", 1)
                for a in b.appendices:
                    if a.kind == "appendix":
                        d.add_paragraph(style="Part Entry").add_run(f"{a.label}    {a.title}")
                continue
            short = s.title.split(":")[0]
            self.section("odd" if s.label == "A" else "next", f"Appendix {s.label}", bt, "decimal")
            p_ = self.heading(f"Appendix {s.label}: {s.title}", 2)
            p_.paragraph_format.space_before = Pt(28)
            para_border(p_, "bottom", 8, "404040", 8)
            p_.paragraph_format.space_after = Pt(14)
            if s.label == "F":
                self.credits_blocks(s.blocks)
            else:
                self.blocks(s.blocks)
        for i, s in enumerate(b.back):
            self.section("next", s.title, bt, "decimal")
            p_ = self.heading(s.title, 2)
            p_.paragraph_format.space_before = Pt(28)
            para_border(p_, "bottom", 8, "404040", 8)
            p_.paragraph_format.space_after = Pt(14)
            self.blocks(s.blocks)
        return self

    def credits_blocks(self, blocks):
        for blk in blocks:
            if blk[0] == "p" and blk[1] and blk[1][0][0] == "b" and inl_text(blk[1][0][1]).startswith("Figure "):
                self.para(blk[1], "Credits")
            else:
                self.block(blk)

    def save(self, path):
        self.doc.save(path)


MAP_NAMES = {
    'M01': 'The Dolomites at a glance', 'M02': 'Getting to the Dolomites', 'M03': 'Val Gardena and Alpe di Siusi',
    'M04': 'The Sella Ronda and the four great passes', 'M05': "Cortina d'Ampezzo and its mountains", 'M06': 'Tre Cime, Sesto and Braies',
    'M07': 'Val di Fassa, Catinaccio and Marmolada', 'M08': 'Plan de Corones, Brixen and Bolzano', 'M09': 'The Tre Cime loop',
    'M10': 'Seceda and Col Raiser', 'M11': 'Alpe di Siusi: Compatsch to Saltria', 'M12': 'The Lagazuoi cable car',
    'M14': 'The Alta Via 1, Lago di Braies to La Pissa', 'I05': 'Five-day route', 'I07': 'Seven-day route', 'I10': 'Ten-day route',
}


def para_border_style(style, side, sz, color, space):
    pPr = style.element.get_or_add_pPr()
    b = OxmlElement("w:pBdr")
    e = OxmlElement(f"w:{side}")
    e.set(qn("w:val"), "single")
    e.set(qn("w:sz"), str(sz))
    e.set(qn("w:space"), str(space))
    e.set(qn("w:color"), color)
    b.append(e)
    pPr.append(b)


def soffice_pdf(docx_path, outdir):
    env = dict(os.environ, HOME="/tmp/lo_home")
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", outdir, docx_path],
                   capture_output=True, timeout=300, env=env)
    return os.path.join(outdir, os.path.splitext(os.path.basename(docx_path))[0] + ".pdf")


def heading_pages(pdf, entries, first_main_title):
    """Find the displayed page number of each TOC entry in a LibreOffice-rendered PDF."""
    import pymupdf
    doc = pymupdf.open(pdf)
    texts = [re.sub(r"\s+", " ", p.get_text()) for p in doc]
    # the first main page = page that contains the first part heading text
    pages = {}
    start = 0
    # skip contents pages: find the page of 'List of maps' heading end
    for i, t in enumerate(texts):
        if "How to Use This Guide" in t[:200] and i > 3:
            start = i
            break
    main_start = None
    cur = start
    for level, text, bm in entries:
        key = re.sub(r"\s+", " ", text)
        for i in range(cur, len(texts)):
            if key in texts[i]:
                cur = i
                pages[bm] = i
                break
    first_l1 = next((bm for lvl, t, bm in entries if lvl == 1), None)
    if first_l1 in pages:
        main_start = pages[first_l1]
    out = {}
    for bm, i in pages.items():
        if main_start is not None and i >= main_start:
            out[bm] = str(i - main_start + 1)
        else:
            out[bm] = roman(i + 1)
    return out


def roman(n):
    vals = [(10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")]
    s = ""
    for v, r in vals:
        while n >= v:
            s += r
            n -= v
    return s


def build_docx(edition, out_path):
    book = load_book()
    first = DocBuilder(book, edition).build()
    entries = list(first.toc_entries)
    first.fill_toc(entries, [])
    tmpd = tempfile.mkdtemp()
    p1 = os.path.join(tmpd, "pass1.docx")
    first.save(p1)
    pages = {}
    if edition == "print":
        pdf = soffice_pdf(p1, tmpd)
        pages = heading_pages(pdf, entries, "")
    second = DocBuilder(book, edition, toc_pages=pages).build()
    second.fill_toc(list(second.toc_entries), [])
    second.save(out_path)
    return out_path, len(entries), pages


if __name__ == "__main__":
    ed = sys.argv[1] if len(sys.argv) > 1 else "print"
    os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
    out = os.path.join(ROOT, "dist", f"draft-{ed}.docx")
    print(build_docx(ed, out)[:2])
