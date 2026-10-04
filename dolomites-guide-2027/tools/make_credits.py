"""Write Appendix F (image credits) from images/credits.json and images/figure_numbers.json."""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "images")
APP = os.path.join(ROOT, "manuscript", "20-appendices.md")

credits = {r["slot"]: r for r in json.load(open(os.path.join(IMG, "credits.json")))}
nums = json.load(open(os.path.join(IMG, "figure_numbers.json")))  # [[label, id], ...] in book order

PREAMBLE = """# Appendix F: Image Credits and Sources

Photographs come from Wikimedia Commons and are used under the free licences named below. Where a licence is CC BY-SA, photographs that were cropped or converted to greyscale for print are adaptations and are shared under the same licence. Each entry gives the figure number, the file title on Wikimedia Commons, the creator and the licence. Licence terms: CC BY 4.0 and other versions at creativecommons.org/licenses/by; CC BY-SA at creativecommons.org/licenses/by-sa; CC0 and public-domain files carry no conditions.

Italy has no general freedom-of-panorama rule for modern buildings and artworks, so photographs in this book show landscape, historic buildings, food and everyday scenes.

**Maps.** All maps in this book were drawn for it from open data. Map data © OpenStreetMap contributors, available under the Open Database Licence (openstreetmap.org/copyright). Terrain shading uses Mapzen/AWS Terrain Tiles, which include data from EU-DEM (Copernicus). Routes on the maps are drawn from the map data and are for planning only; follow signs and current local information on the ground.

**Photographs**

"""


def clean_author(a):
    a = re.sub(r"\s+", " ", a or "").strip()
    if "Wolfgang Moroder" in a:
        return "Wolfgang Moroder"
    a = re.sub(r"No machine-readable author provided\.?\s*", "", a)
    a = re.sub(r"~commonswiki assumed.*$", "", a).strip()
    a = re.sub(r"^Picture by\s+", "", a)
    a = re.sub(r"^User:", "", a)
    if a.count("(") > a.count(")"):
        a += ")"
    return a or "Unknown author"


def short_lic(c):
    return c["license"] or c["kind"]


def entry(label, sid):
    c = credits[sid]
    adapt = ""
    if c["kind"] == "BY-SA":
        adapt = " Cropped and converted to greyscale for print; adaptation shared under the same licence."
    elif c["kind"] == "BY":
        adapt = " Cropped and converted to greyscale for print."
    author = clean_author(c["author"])
    return f'**{label}.** "{c["title"]}", by {author}. Wikimedia Commons. {short_lic(c)}.{adapt}'


def main():
    lines = []
    for label, sid in nums:
        if sid in credits:
            lines.append(entry(label, sid))
    body = PREAMBLE + "\n\n".join(lines) + "\n\n---\n\n"
    text = open(APP, encoding="utf-8").read()
    new = re.sub(r"# Appendix F: Image Credits and Sources.*?(?=# About the Author)", lambda m: body, text, flags=re.S)
    open(APP, "w", encoding="utf-8").write(new)
    print("credits written:", len(lines))


if __name__ == "__main__":
    main()
