"""Second pass for slots the text search could not fill: browse Wikimedia Commons categories instead.

For a slot we look for categories by name, list the files in the best ones and keep free-licence
JPEGs of enough size. Category membership is the relevance signal, so no keyword filter is applied
(only the slot's 'avoid' words). Usage: find_by_category.py SLOT[=category query] ...
"""
import json, os, sys, time, urllib.parse

sys.path.insert(0, os.path.dirname(__file__))
from find_candidates import API, CAND, get, parse, sheet, strip
from slots import S

BYID = {s["id"]: s for s in S}
DELAY = 9.0


def api(**params):
    params["format"] = "json"
    d = json.loads(get(API + "?" + urllib.parse.urlencode(params)))
    time.sleep(DELAY)
    return d


def find_categories(q, n=4):
    d = api(action="query", list="search", srsearch=q, srnamespace="14", srlimit=str(n))
    return [r["title"] for r in d.get("query", {}).get("search", [])]


def files_in(cat, limit=80):
    d = api(action="query", generator="categorymembers", gcmtitle=cat, gcmtype="file", gcmlimit=str(limit),
            prop="imageinfo", iiprop="url|size|mime|extmetadata", iiurlwidth="640")
    return list(d.get("query", {}).get("pages", {}).values())


def rank(c, slot):
    s = 0.0
    cats = c["cats"].lower()
    if "featured pictures" in cats or "valued image" in cats:
        s += 4
    if "quality images" in cats:
        s += 3
    s += {"PD": 3, "BY": 2, "BY-SA": 0}[c["lic"]]
    s += min(c["width"], 8000) / 4000.0
    if c["width"] >= c["height"]:
        s += 0.5
    if "personality" in c["restrictions"].lower():
        s -= 1.5
    for m in slot["must"]:
        if m in c["title"].lower():
            s += 1.5
    return round(s, 2)


def run(sid, q=None):
    slot = BYID[sid]
    qs = q.split("|") if q else slot["queries"][:2]
    cats = []
    for qq in qs:
        for c in find_categories(qq):
            if c not in cats:
                cats.append(c)
    print(sid, "categories:", cats[:5], flush=True)
    seen = {}
    for cat in cats[:3]:
        try:
            pages = files_in(cat)
        except Exception as e:
            print("  failed", cat, e, flush=True)
            continue
        for p in pages:
            if "imageinfo" not in p:
                continue
            c = parse(p)
            if c["mime"] != "image/jpeg" or c["lic"] is None or c["width"] < slot["min_w"]:
                continue
            blob = (c["title"] + " " + c["cats"] + " " + c["desc"]).lower()
            if any(a in blob for a in slot["avoid"]):
                continue
            c["from_category"] = cat
            seen[c["title"]] = c
        if len(seen) >= 12:
            break
    out = []
    for c in seen.values():
        c["score"] = rank(c, slot)
        out.append(c)
    out.sort(key=lambda x: -x["score"])
    out = out[:8]
    path = os.path.join(CAND, sid + ".json")
    old = json.load(open(path)) if os.path.exists(path) else []
    if out or not old:
        json.dump(out, open(path, "w"), indent=1, ensure_ascii=False)
        sheet(slot, out)
    n = {k: sum(1 for c in out if c["lic"] == k) for k in ("PD", "BY", "BY-SA")}
    print(f"{sid:6} {len(out)} candidates {n}", flush=True)


if __name__ == "__main__":
    for a in sys.argv[1:]:
        sid, _, q = a.partition("=")
        run(sid, q or None)
