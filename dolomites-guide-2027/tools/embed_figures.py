"""Insert chosen photos and maps into the manuscript, with numbered figure captions.

Photos come from images/selection.json (only slots that finalize_images.py produced a file for).
Maps are listed in MAPS below. Each figure is written as a markdown image with the path
images/print/<ID>.<ext>; the build step swaps that for images/ebook/ in the ebook.
Re-running is safe: every block is wrapped in <!-- FIG:ID --> markers and replaced in place.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MS = os.path.join(ROOT, "manuscript")
IMG = os.path.join(ROOT, "images")

# slot -> (manuscript file prefix, heading text start, "after" | "before")
PLACE = {
    "C01a": ("01", "# 1. How the Dolomites Work", "after"),
    "C01b": ("01", "## Three languages, many names", "after"),
    "M01": ("01", "## The regions in one view", "after"),
    "C02s": ("02", "## Summer: late June", "after"),
    "C02m": ("02", "## Autumn: late September", "before"),
    "C02a": ("02", "## Autumn: late September", "after"),
    "C02w": ("02", "## Winter: December", "after"),
    "C02p": ("02", "## Spring: April", "after"),
    "C03a": ("03", "## Seceda lifts", "after"),
    "C03b": ("03", "## Lago di Braies", "after"),
    "C03c": ("03", "## Tre Cime di Lavaredo toll road", "after"),
    "C03d": ("03", "## Alpe di Siusi", "after"),
    "M02": ("04", "## Choose your airport", "after"),
    "C04a": ("04", "## By train", "after"),
    "C04b": ("04", "## Driving", "after"),
    "C04c": ("04", "## Public transport inside", "after"),
    "C04d": ("04", "## Lift passes and summer cards", "after"),
    "C05a": ("05", "## Food and drink", "after"),
    "C06a": ("06", "### Ortisei, Santa Cristina", "after"),
    "C06b": ("06", "## Types of accommodation", "after"),
    "C06c": ("06", "### Alta Badia: Corvara", "after"),
    "M03": ("07", "## Overview", "after"),
    "C07a": ("07", "### 1. Seceda", "after"),
    "M10": ("07", "### 1. Seceda", "after"),
    "C07b": ("07", "### 2. Alpe di Siusi", "after"),
    "M11": ("07", "### 2. Alpe di Siusi", "after"),
    "C07c": ("07", "### 3. Sassolungo", "after"),
    "C07f": ("07", "### 3. Sassolungo", "after"),
    "C07d": ("07", "### 4. Val di Funes", "after"),
    "C07e": ("07", "### 5. Ortisei", "before"),
    "M04": ("08", "## Overview", "after"),
    "C08a": ("08", "## The four great passes", "after"),
    "C08b": ("08", "## 3. Piz Bo", "after"),
    "C08c": ("08", "## 4. Lago Pisciad", "after"),
    "C08d": ("08", "## 4. Lago Pisciad", "after"),
    "C08e": ("08", "## 5. Alta Badia villages", "after"),
    "C08f": ("08", "## 5. Alta Badia villages", "after"),
    "C08g": ("08", "## 5. Alta Badia villages", "after"),
    "M05": ("09", "## Overview", "after"),
    "C09a": ("09", "## 1. Cortina town", "after"),
    "C09b": ("09", "## 2. Cinque Torri", "after"),
    "C09g": ("09", "## 2. Cinque Torri", "after"),
    "C09c": ("09", "## 3. Lagazuoi", "after"),
    "M12": ("09", "## 3. Lagazuoi", "after"),
    "C09d": ("09", "## 4. Passo Giau", "after"),
    "C09e": ("09", "## 5. Lago di Sorapis", "after"),
    "C09f": ("09", "## 6. Faloria", "after"),
    "M06": ("10", "## Overview", "after"),
    "C10a": ("10", "## 1. Tre Cime di Lavaredo loop", "after"),
    "M09": ("10", "## 1. Tre Cime di Lavaredo loop", "after"),
    "C10b": ("10", "### Ways to reach the Tre Cime", "before"),
    "C10c": ("10", "## 2. Cadini di Misurina", "after"),
    "C10d": ("10", "## 2. Cadini di Misurina", "after"),
    "C10e": ("10", "## 3. Val Fiscalina", "after"),
    "C10h": ("10", "## 4. Lago di Braies", "after"),
    "C10i": ("10", "## 5. Alta Via 1", "after"),
    "C10f": ("10", "## 6. Val Pusteria towns", "after"),
    "C10g": ("10", "## 6. Val Pusteria towns", "after"),
    "M07": ("11", "## Overview", "after"),
    "C11a": ("11", "## 1. Catinaccio", "after"),
    "C11b": ("11", "## 1. Catinaccio", "after"),
    "C11c": ("11", "## 2. Marmolada", "after"),
    "C11f": ("11", "## 2. Marmolada", "after"),
    "C11d": ("11", "## 3. Lago di Carezza", "after"),
    "C11e": ("11", "## 5. The villages", "after"),
    "M08": ("12", "## Overview", "after"),
    "C12a": ("12", "## 1. Bolzano", "after"),
    "C12d": ("12", "## 2. The Renon", "after"),
    "C12f": ("12", "## 2. The Renon", "after"),
    "C12b": ("12", "## 3. Brixen", "after"),
    "C12c": ("12", "## 3. Brixen", "after"),
    "C12e": ("12", "## 4. Plan de Corones", "after"),
    "C13a": ("13", "## How to choose a hike", "after"),
    "C13c": ("13", "### Trail markings", "after"),
    "C13b": ("13", "## Mountain huts (rifugi)", "after"),
    "M14": ("13", "## The Alta Via 1", "after"),
    "C13d": ("13", "## The Alta Via 1", "after"),
    "C14a": ("14", "## Via ferrata", "after"),
    "C14b": ("14", "## Cycling", "after"),
    "C14e": ("14", "### Easy cycle paths", "after"),
    "C14c": ("14", "### Bike parks and lifts", "after"),
    "C14d": ("14", "## Paragliding, spas", "after"),
    "C15a": ("15", "## Dolomiti Superski explained", "after"),
    "C15b": ("15", "## The Sella Ronda ski circuit", "after"),
    "C15e": ("15", "## Cortina after the Olympics", "after"),
    "C15c": ("15", "## For non-skiers", "after"),
    "C15d": ("15", "## For non-skiers", "after"),
    "C16a": ("16", "### Dishes you will see everywhere", "after"),
    "C16f": ("16", "### Ladin dishes", "after"),
    "C16b": ("16", "### Cheese and local products", "after"),
    "C16e": ("16", "### T", "after"),
    "C16d": ("16", "### Wine", "after"),
    "C16c": ("16", "## Drinks", "before"),
    "C17d": ("17", "### The Ladin people", "after"),
    "C17a": ("17", "## The Great War in the mountains", "after"),
    "C17b": ("17", "## Mountains and mountaineers", "before"),
    "C17c": ("17", "## The legend of the pink mountains", "after"),
    "C17f": ("17", "## Responsible travel", "after"),
    "C17e": ("17", "## Photography guide", "after"),
    "I05": ("18", "## 2. Five days", "after"),
    "I07": ("18", "## 3. Seven days", "after"),
    "I10": ("18", "## 4. Ten days", "after"),
    "C19b": ("19", "### Thunderstorm rules", "after"),
    "C19a": ("19", "## Emergencies", "after"),
}

MAPS = {
    "M01": "The Dolomites at a glance. The numbers on the map are the chapters that cover each area.",
    "M02": "Getting to the Dolomites: the main airports, the Brenner motorway (A22) and the Pusteria railway.",
    "M03": "Val Gardena and Alpe di Siusi. 1 Seceda, 2 Alpe di Siusi (Compatsch), 3 Sassolungo, 4 Santa Maddalena, 5 Ortisei. Dash-dot lines are cable cars and lifts.",
    "M04": "The Sella Ronda and the four great passes. 1 Passo Gardena, 2 Passo Sella, 3 Passo Pordoi, 4 Passo Campolongo. The heavy line is the road circuit.",
    "M05": "Cortina d'Ampezzo and its mountains. 1 Cortina, 2 Cinque Torri, 3 Lagazuoi, 4 Passo Giau, 5 Lago di Sorapis, 6 Tofana di Mezzo.",
    "M06": "Tre Cime, Sesto and Braies. 1 Tre Cime, 2 Cadini di Misurina, 3 Val Fiscalina (Fondovalle), 4 Lago di Braies. The dashed line is the road from Dobbiaco to Rifugio Auronzo.",
    "M07": "Val di Fassa, Catinaccio and Marmolada. 1 Gardeccia and the Vajolet Towers, 2 Malga Ciapela (Marmolada cable car), 3 Lago di Carezza, 4 Col Rodella.",
    "M08": "Plan de Corones, Brixen and Bolzano. 1 Bolzano, 2 Soprabolzano (Renon), 3 Bressanone, 4 Neustift Abbey, 5 Plan de Corones.",
    "M09": "The Tre Cime loop. The dashed line follows the usual route from Rifugio Auronzo past Rifugio Lavaredo and Forcella Lavaredo to Rifugio Locatelli, then back by the Langalm side.",
    "M10": "Seceda and Col Raiser. Dash-dot lines are cable cars and lifts; dotted lines are walking paths.",
    "M11": "Alpe di Siusi: the easy walk from Compatsch to Saltria (dashed), passing the Sanon hut.",
    "M12": "The Lagazuoi cable car, rising from Passo Falzarego to the hut at the top.",
    "M14": "The Alta Via 1 from Lago di Braies to La Pissa. The huts are joined by straight lines, so this shows the order of the stages, not the path of the trail.",
    "I05": "Five-day route: Ortisei, Passo Gardena, Cortina (solid), Tre Cime (dashed) and Lago di Braies (dotted).",
    "I07": "Seven-day route: Val Gardena, the passes to Cortina, then Dobbiaco and Sesto.",
    "I10": "Ten-day route: Bolzano, Ortisei, Canazei, Cortina and Sesto.",
}
MAP_CREDIT = "Map data © OpenStreetMap contributors (ODbL). Terrain: Mapzen/AWS Terrain Tiles (EU-DEM, Copernicus)."


def figures():
    """id -> (relative image path, caption, alt)"""
    out = {}
    sel = json.load(open(os.path.join(IMG, "selection.json")))
    for sid, spec in sel.items():
        for ext in ("jpg",):
            if os.path.exists(os.path.join(IMG, "print", sid + "." + ext)):
                out[sid] = (f"images/print/{sid}.{ext}", spec["caption"])
    for mid, cap in MAPS.items():
        fn = os.path.join(IMG, "print", mid + ".png")
        if os.path.exists(fn):
            out[mid] = (f"images/print/{mid}.png", cap)
    return out


def main():
    figs = figures()
    by_file = {}
    for fid, (pf, head, mode) in PLACE.items():
        if fid in figs:
            by_file.setdefault(pf, []).append((fid, head, mode))
    nfig = 0
    credits_order = []
    for fn in sorted(os.listdir(MS)):
        m = re.match(r"(\d\d)-", fn)
        if not m or m.group(1) not in by_file:
            continue
        path = os.path.join(MS, fn)
        text = open(path, encoding="utf-8").read()
        # remove earlier insertions and the old placeholders
        text = re.sub(r"<!-- FIG:(\w+) -->.*?<!-- /FIG -->\n?\n?", "", text, flags=re.S)
        text = re.sub(r"<!-- FIGURE:[^\n]*-->\n?\n?", "", text)
        lines = text.split("\n")
        # find insertion points
        inserts = {}  # line index -> list of block strings
        items = by_file[m.group(1)]
        chapter = int(m.group(1))
        # order figures by their position in the file, then by PLACE order
        pos = []
        for fid, head, mode in items:
            idx = next((i for i, l in enumerate(lines) if l.startswith(head)), None)
            if idx is None:
                print("heading not found:", fn, head, fid)
                continue
            pos.append((idx if mode == "before" else idx + 0.5, fid, mode, idx))
        pos.sort(key=lambda p: (p[0], list(PLACE).index(p[1])))
        k = 0
        for _, fid, mode, idx in pos:
            k += 1
            path_img, cap = figs[fid]
            label = f"Figure {chapter}.{k}"
            block = (f"<!-- FIG:{fid} -->\n![{label}. {cap}]({path_img})\n\n"
                     f"*{label}. {cap}*\n<!-- /FIG -->\n")
            if mode == "before":
                ins = idx
            else:
                ins = idx + 2 if idx + 1 < len(lines) and lines[idx + 1].strip() == "" else idx + 1
            inserts.setdefault(ins, []).append(block)
            credits_order.append((label, fid))
            nfig += 1
        new = []
        for i, l in enumerate(lines):
            if i in inserts:
                if new and new[-1] != "":
                    new.append("")
                for b in inserts[i]:
                    new.extend(b.rstrip("\n").split("\n"))
                    new.append("")
            new.append(l)
        # when inserting right after a heading the heading line itself came before: fix blank lines
        out = "\n".join(new)
        out = re.sub(r"\n{3,}", "\n\n", out)
        open(path, "w", encoding="utf-8").write(out)
    json.dump(credits_order, open(os.path.join(IMG, "figure_numbers.json"), "w"), indent=1)
    print("figures embedded:", nfig)


if __name__ == "__main__":
    main()
