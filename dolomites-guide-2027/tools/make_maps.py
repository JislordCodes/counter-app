import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from render_map import render

MAPS = {}

# ---------------------------------------------------------------- Map 1: regional overview
MAPS["M01"] = dict(
    id="M01", bbox=(10.95, 46.27, 12.55, 46.92), zoom=11, scale_km=20, adjust=True, fs=6.0,
    roads="primary|secondary", lifts=False,
    labels=[
        ("Bolzano", r"^Bolzano|Bozen", "place", dict(near=(11.35, 46.50), kinds=["city", "town"])),
        ("Bressanone", r"Bressanone|Brixen", "place", dict(near=(11.66, 46.72), kinds=["city", "town"])),
        ("Brunico", r"Brunico|Bruneck", "place", dict(near=(11.94, 46.80), kinds=["city", "town"])),
        ("Dobbiaco", r"Dobbiaco|Toblach", "place", dict(near=(12.22, 46.73), kinds=["village", "town"])),
        ("San Candido", r"San Candido|Innichen", "place", dict(near=(12.28, 46.73), kinds=["village", "town"])),
        ("Sesto", r"^Sesto|Sexten", "place", dict(near=(12.35, 46.70), kinds=["village"])),
        ("Cortina d'Ampezzo", r"Cortina", "place", dict(near=(12.14, 46.54), kinds=["town", "village"])),
        ("Corvara", r"Corvara", "place", dict(near=(11.87, 46.55), kinds=["village"])),
        ("Ortisei", r"Ortisei", "place", dict(near=(11.67, 46.57), kinds=["village", "town"])),
        ("Selva", r"Selva|Wolkenstein|Sëlva", "place", dict(near=(11.76, 46.56), kinds=["village"])),
        ("Canazei", r"Canazei", "place", dict(near=(11.77, 46.48), kinds=["village"])),
        ("Moena", r"Moena", "place", dict(near=(11.66, 46.38), kinds=["village"])),
        ("Marmolada", r"Marmolada|Punta Penia", "peak", dict(near=(11.85, 46.43))),
        ("Tre Cime", r"Cima Grande|Tre Cime|Drei Zinnen", "peak", dict(near=(12.30, 46.62))),
        ("Sassolungo", r"Sassolungo|Langkofel|Plattkofel", "peak", dict(near=(11.72, 46.51))),
        ("Piz Boè", r"Piz Bo[eè]", "peak", dict(near=(11.81, 46.51))),
        ("Catinaccio", r"Catinaccio|Rosengarten", "peak", dict(near=(11.63, 46.46))),
        ("Sciliar", r"Sciliar|Schlern|Santner|Petz", "peak", dict(near=(11.58, 46.52))),
        ("Seceda", r"Seceda|Sass Rigais|Sass Rigàis", "peak", dict(near=(11.72, 46.60))),
        ("Kronplatz", r"Kronplatz|Plan de Corones", "peak", dict(near=(11.95, 46.74))),
        ("Tofane", r"Tofana di Mezzo|Tofane", "peak", dict(near=(12.07, 46.55))),
        ("L. di Braies", r"Pragser Wildsee|Braies", "lake", dict(near=(12.08, 46.69), kinds=[""])),
    ],
    numbers={},
)

if __name__ == "__main__":
    ids = sys.argv[1:] or list(MAPS)
    for i in ids:
        render(MAPS[i])
