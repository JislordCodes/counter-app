"""Production audit of the manuscript: structure, tables, placeholders, cross-references, typography.

Prints a report; exit status 0 always (it is a report, not a gate).
"""
import glob, os, re, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MS = os.path.join(ROOT, "manuscript")
files = sorted(glob.glob(os.path.join(MS, "*.md")))
chapters = {}
issues = collections.defaultdict(list)


def add(kind, f, ln, msg):
    issues[kind].append(f"{os.path.basename(f)}:{ln}: {msg}")


for f in files:
    lines = open(f, encoding="utf-8").read().split("\n")
    base = os.path.basename(f)
    m = re.match(r"(\d\d)-", base)
    in_fig = False
    prev_level = 0
    table_cols = None
    for i, l in enumerate(lines, 1):
        if l.startswith("<!-- FIG:"):
            in_fig = True
        if l.startswith("<!-- /FIG"):
            in_fig = False
            continue
        if in_fig:
            continue
        h = re.match(r"^(#{1,4}) (.*)$", l)
        if h:
            lvl = len(h.group(1))
            if prev_level and lvl > prev_level + 1:
                add("heading jumps", f, i, f"h{prev_level} -> h{lvl}: {l[:60]}")
            prev_level = lvl
            if m and lvl == 1 and re.match(r"\d+\. ", h.group(2)):
                chapters[int(m.group(1))] = h.group(2)
        if re.search(r"\[[^\]\n]*\](?!\()", l) and not l.startswith("!["):
            if not re.match(r"^\s*\|", l) or "[" in l:
                add("bracket placeholders", f, i, l[:100])
        if re.search(r"TODO|VERIFY|XXX|\?\?\?|FIXME|lorem", l, re.I):
            add("todo markers", f, i, l[:100])
        if "  " in l.strip() and not l.lstrip().startswith("|"):
            add("double spaces", f, i, l[:80])
        if l.rstrip() != l and not l.endswith("  "):
            add("trailing space", f, i, repr(l[-12:]))
        if l.count("**") % 2 == 1:
            add("unbalanced bold", f, i, l[:90])
        # table row column consistency
        if l.startswith("|"):
            cols = len(re.findall(r"(?<!\\)\|", l)) - 1
            if table_cols is None:
                table_cols = cols
            elif cols != table_cols:
                add("table column mismatch", f, i, f"{cols} vs {table_cols}: {l[:70]}")
            if re.search(r"\|\s*\|", l) and not re.match(r"^\|\s*\|\s*\|\s*$", l) and "---" not in l:
                add("empty table cell", f, i, l[:90])
        else:
            table_cols = None
        for pat, name in ((r"\s,", "space before comma"), (r"\.\.(?!\.)", "double period"), (r" - ", "spaced hyphen"),
                          (r"\bteh\b|\brecieve\b|\bseperate\b|\boccured\b", "typo")):
            if re.search(pat, l) and not l.startswith("|---"):
                add(name, f, i, l[:100])

text_all = "\n".join(open(f, encoding="utf-8").read() for f in files)
for m in re.finditer(r"\bChapter (\d+)\b", text_all):
    if int(m.group(1)) not in chapters and int(m.group(1)) != 0:
        issues["bad chapter refs"].append(f"Chapter {m.group(1)}")
for m in re.finditer(r"\bAppendix ([A-Z])\b", text_all):
    if m.group(1) not in "ABCDEF":
        issues["bad appendix refs"].append(f"Appendix {m.group(1)}")
for m in re.finditer(r"\bPart (\d+)\b", text_all):
    if int(m.group(1)) > 6:
        issues["bad part refs"].append(f"Part {m.group(1)}")

print("Chapters found:", sorted(chapters))
for k, v in issues.items():
    print(f"\n== {k} ({len(v)})")
    for x in v[:25]:
        print("  ", x)
if not issues:
    print("No issues found.")
