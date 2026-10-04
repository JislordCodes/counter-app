"""Search Wikimedia Commons for free-licence images for every slot, rank them, and make contact sheets.

Only these licences are kept: public domain, CC0, CC BY (any version) and, flagged, CC BY-SA.
Everything with NC (non-commercial) or ND (no derivatives) is dropped.
"""
import html, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
from slots import S

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAND = os.path.join(ROOT, "images", "candidates")
THUMB = os.path.join(ROOT, "images", "thumbs")
SHEET = os.path.join(ROOT, "images", "sheets")
UA = "DolomitesTravelGuideImageResearch/1.0 (https://github.com/JislordCodes/counter-app; book research)"
API = "https://commons.wikimedia.org/w/api.php"


def get(url, tries=6):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            last = e
            ra = e.headers.get("Retry-After") if e.headers else None
            wait = float(ra) if ra and ra.isdigit() else 25 * (i + 1) if e.code == 429 else 2 * (i + 1)
            time.sleep(min(wait, 120))
        except Exception as e:
            last = e
            time.sleep(2 * (i + 1))
    raise last


def strip(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def lic_class(short, usage=""):
    t = (short or "").lower()
    if any(x in t for x in ["-nc", " nc", "-nd", " nd", "noncommercial", "gfdl", "fair use", "copyrighted"]):
        return None
    if "cc0" in t or "public domain" in t or t.startswith("pd") or "pdm" in t:
        return "PD"
    if t.startswith("cc by-sa"):
        return "BY-SA"
    if t.startswith("cc by"):
        return "BY"
    return None


def search(query, limit=40):
    params = dict(action="query", generator="search", gsrsearch=query + " filetype:bitmap", gsrnamespace="6",
                  gsrlimit=str(limit), prop="imageinfo", iiprop="url|size|mime|extmetadata", iiurlwidth="640", format="json")
    data = json.loads(get(API + "?" + urllib.parse.urlencode(params)))
    return list((data.get("query", {}).get("pages", {})).values())


def parse(page):
    ii = page["imageinfo"][0]
    em = ii.get("extmetadata", {})
    g = lambda k: em.get(k, {}).get("value", "")
    short = g("LicenseShortName")
    return dict(
        title=page["title"], width=ii["width"], height=ii["height"], mime=ii["mime"],
        url=ii["url"], thumb=ii.get("thumburl", ""), page=ii.get("descriptionurl", ""),
        license=short, lic=lic_class(short), license_url=g("LicenseUrl"),
        artist=strip(g("Artist")), credit=strip(g("Credit")), desc=strip(g("ImageDescription")),
        cats=g("Categories").replace("|", "; "), date=strip(g("DateTimeOriginal")),
        restrictions=g("Restrictions"), attribution_required=g("AttributionRequired"))


def score(c, slot):
    text_t = c["title"].lower()
    text_c = c["cats"].lower()
    text_d = c["desc"].lower()
    blob = text_t + " " + text_c + " " + text_d
    if slot["must"] and not any(m in blob for m in slot["must"]):
        return None
    if any(a in blob for a in slot["avoid"]):
        return None
    s = 0
    for m in slot["must"]:
        s += 3 * (m in text_t) + 2 * (m in text_c) + 1 * (m in text_d)
    if "featured pictures" in text_c or "valued image" in text_c:
        s += 4
    if "quality images" in text_c:
        s += 3
    s += {"PD": 3, "BY": 2, "BY-SA": 0}[c["lic"]]
    s += min(c["width"], 8000) / 4000.0
    if c["width"] >= c["height"]:
        s += 0.5
    if "personality" in c["restrictions"].lower():
        s -= 1.5
    return s


def candidates_for(slot):
    seen = {}
    failed = 0
    for q in slot["queries"][:2]:
        try:
            for p in search(q, limit=50):
                if "imageinfo" not in p:
                    continue
                c = parse(p)
                if c["mime"] != "image/jpeg" or c["lic"] is None or c["width"] < slot["min_w"]:
                    continue
                seen[c["title"]] = c
        except Exception as e:
            failed += 1
            print("  search failed", slot["id"], q, e, flush=True)
        time.sleep(9.0)
        good = [c for c in seen.values() if score(c, slot) is not None]
        if len(good) >= 6:
            break
    if failed and not seen:
        return None
    out = []
    for c in seen.values():
        sc = score(c, slot)
        if sc is not None:
            c["score"] = round(sc, 2)
            out.append(c)
    out.sort(key=lambda x: -x["score"])
    return out[:6]


def sheet(slot, cands):
    tiles = []
    for i, c in enumerate(cands):
        fn = os.path.join(THUMB, f"{slot['id']}_{i}.jpg")
        if not os.path.exists(fn):
            try:
                with open(fn, "wb") as f:
                    f.write(get(c["thumb"]))
                time.sleep(1.0)
            except Exception as e:
                print("  thumb failed", c["title"], e, flush=True)
                continue
        tiles.append((i, c, fn))
    if not tiles:
        return
    W, H = 420, 330
    cols = 4
    rows = (len(tiles) + cols - 1) // cols
    img = Image.new("RGB", (cols * W, rows * H), "white")
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    except Exception:
        font = big = ImageFont.load_default()
    for k, (i, c, fn) in enumerate(tiles):
        x, y = (k % cols) * W, (k // cols) * H
        try:
            im = Image.open(fn).convert("RGB")
            im.thumbnail((W - 10, H - 70))
            img.paste(im, (x + 5, y + 5))
        except Exception:
            pass
        d.text((x + 6, y + 6), str(i), fill="red", font=big)
        t = c["title"].replace("File:", "")[:52]
        d.text((x + 5, y + H - 62), t, fill="black", font=font)
        d.text((x + 5, y + H - 46), f'{c["lic"]} | {c["width"]}px | s={c["score"]}', fill="navy", font=font)
        d.text((x + 5, y + H - 30), (c["artist"] or "?")[:50], fill="gray", font=font)
    img.save(os.path.join(SHEET, f"{slot['id']}.jpg"), quality=80)


def run(slot):
    path = os.path.join(CAND, slot["id"] + ".json")
    if os.path.exists(path):
        cands = json.load(open(path))
    else:
        cands = candidates_for(slot)
        if cands is None:
            return
        json.dump(cands, open(path, "w"), indent=1, ensure_ascii=False)
    sheet(slot, cands)
    n = {k: sum(1 for c in cands if c["lic"] == k) for k in ("PD", "BY", "BY-SA")}
    print(f'{slot["id"]:6} {len(cands)} candidates {n}', flush=True)


if __name__ == "__main__":
    ids = set(sys.argv[1:])
    todo = [s for s in S if not ids or s["id"] in ids]
    with ThreadPoolExecutor(max_workers=1) as ex:
        list(ex.map(run, todo))
