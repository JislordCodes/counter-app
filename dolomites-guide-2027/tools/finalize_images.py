"""Download the chosen photos, make print (greyscale) and ebook (colour) versions, and write the credits.

selection.json format:
  { "SLOT": {"idx": 3, "caption": "...", "aspect": 1.5, "ax": 0.5, "ay": 0.5, "file": "07-....md", "after": "## 1. Seceda"} }
"""
import csv, json, os, re, sys, time, urllib.parse, urllib.request
from PIL import Image, ImageOps, ImageEnhance

sys.path.insert(0, os.path.dirname(__file__))
from find_candidates import get, strip, API, UA

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "images")
SEL = json.load(open(os.path.join(IMG, "selection.json")))
os.makedirs(os.path.join(IMG, "original"), exist_ok=True)
os.makedirs(os.path.join(IMG, "print"), exist_ok=True)
os.makedirs(os.path.join(IMG, "ebook"), exist_ok=True)


def thumb_url(title, width=1920):
    params = dict(action="query", titles=title, prop="imageinfo", iiprop="url|size", iiurlwidth=str(width), format="json")
    d = json.loads(get(API + "?" + urllib.parse.urlencode(params)))
    ii = list(d["query"]["pages"].values())[0]["imageinfo"][0]
    return ii.get("thumburl") or ii["url"], ii["width"], ii["height"]


def crop(im, aspect, ax=0.5, ay=0.5):
    w, h = im.size
    cur = w / h
    if aspect is None or abs(cur - aspect) < 0.02:
        return im
    if cur > aspect:  # too wide: crop width
        nw = int(h * aspect)
        x0 = int((w - nw) * ax)
        return im.crop((x0, 0, x0 + nw, h))
    nh = int(w / aspect)
    y0 = int((h - nh) * ay)
    return im.crop((0, y0, w, y0 + nh))


def make(slot, spec):
    cand = json.load(open(os.path.join(IMG, "candidates", spec.get("src", slot.split("#")[0]) + ".json")))[spec["idx"]]
    base = slot
    fn = os.path.join(IMG, "original", base + ".jpg")
    if os.path.exists(fn):
        try:
            Image.open(fn).verify()
        except Exception:
            os.remove(fn)  # half-written or error page: fetch again
    if not os.path.exists(fn):
        url, w, h = thumb_url(cand["title"], 1920)
        data = get(url)
        tmp = fn + ".part"
        open(tmp, "wb").write(data)
        Image.open(tmp).verify()
        os.replace(tmp, fn)
        time.sleep(6.0)
    im = Image.open(fn).convert("RGB")
    im = crop(im, spec.get("aspect"), spec.get("ax", 0.5), spec.get("ay", 0.5))
    # print version: greyscale, 300 dpi at 5.5 in (or half width)
    pw = spec.get("print_w", 1650)
    p = im.copy()
    if p.width > pw:
        p = p.resize((pw, int(p.height * pw / p.width)), Image.LANCZOS)
    g = ImageOps.grayscale(p)
    g = ImageOps.autocontrast(g, cutoff=0.5)
    g = ImageEnhance.Contrast(g).enhance(1.08)
    g.save(os.path.join(IMG, "print", base + ".jpg"), quality=88, dpi=(300, 300), optimize=True)
    # ebook version: colour, 1200 px
    e = im.copy()
    if e.width > 1200:
        e = e.resize((1200, int(e.height * 1200 / e.width)), Image.LANCZOS)
    e.save(os.path.join(IMG, "ebook", base + ".jpg"), quality=76, optimize=True)
    return cand


def credit_line(c):
    artist = c["artist"] or "Unknown author"
    artist = re.sub(r"\s+", " ", artist)[:90]
    title = c["title"].replace("File:", "")
    lic = c["license"]
    note = ""
    if c["lic"] == "BY-SA":
        note = " Adapted (cropped and converted to greyscale for print); the adaptation is shared under the same licence."
    elif c["lic"] == "BY":
        note = " Cropped and converted to greyscale for print."
    return dict(title=title, author=artist, license=lic, license_url=c["license_url"], page=c["page"], note=note.strip(), kind=c["lic"])


def main():
    rows = []
    for slot, spec in SEL.items():
        try:
            cand = make(slot, spec)
        except Exception as e:
            print("FAILED", slot, e)
            continue
        r = credit_line(cand)
        r["slot"] = slot
        r["caption"] = spec["caption"]
        rows.append(r)
        print("ok", slot, r["license"])
    json.dump(rows, open(os.path.join(IMG, "credits.json"), "w"), indent=1, ensure_ascii=False)
    with open(os.path.join(IMG, "credits.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
