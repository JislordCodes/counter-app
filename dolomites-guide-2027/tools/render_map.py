"""Render one map from a spec dict. See make_maps.py for the specs."""
import math, os, re
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.patches import Polygon
from scipy.ndimage import gaussian_filter
from adjustText import adjust_text
import mapkit as mk

OUT = os.path.join(mk.ROOT, "images", "maps")
os.makedirs(OUT, exist_ok=True)
ATTR = "© OpenStreetMap contributors · Terrain: Mapzen/AWS Terrain Tiles (EU-DEM, Copernicus)"
HALO = [pe.withStroke(linewidth=2.2, foreground="white")]


def ov_query(bbox, parts):
    w, s, e, n = bbox
    bb = f"({s},{w},{n},{e})"
    body = "".join(p.replace("BBOX", bb) for p in parts)
    return f"[out:json][timeout:90];({body});out geom;"


def chunks(bbox, step=0.30):
    w, s, e, n = bbox
    nx = max(1, math.ceil((e - w) / step))
    ny = max(1, math.ceil((n - s) / (step * 0.7)))
    for i in range(nx):
        for j in range(ny):
            yield (round(w + (e - w) * i / nx, 4), round(s + (n - s) * j / ny, 4),
                   round(w + (e - w) * (i + 1) / nx, 4), round(s + (n - s) * (j + 1) / ny, 4))


def fetch(bbox, roads="primary|secondary", tert=False, lakes=True, rails=True, lifts=False):
    seen = {}
    for cb in chunks(bbox):
        parts = [f'way["highway"~"^(motorway|trunk|{roads})$"]BBOX;']
        if tert:
            parts.append('way["highway"="tertiary"]BBOX;')
        if rails:
            parts.append('way["railway"="rail"]BBOX;')
        if lakes:
            parts.append('way["natural"="water"]["name"]BBOX;')
        if lifts:
            parts.append('way["aerialway"~"^(cable_car|gondola|chair_lift|mixed_lift)$"]["name"]BBOX;')
        for el in mk.overpass(ov_query(cb, parts))["elements"]:
            seen[(el["type"], el["id"])] = el
    return list(seen.values())


def pois(bbox, extra=""):
    seen = {}
    for cb in chunks(bbox, 0.5):
        w, s_, e, n = cb
        bb = f"({s_},{w},{n},{e})"
        q = ('[out:json][timeout:90];('
             f'node["place"~"^(city|town|village|hamlet)$"]{bb};'
             f'node["natural"~"^(peak|saddle)$"]["name"]{bb};'
             f'node["mountain_pass"="yes"]["name"]{bb};'
             f'node["tourism"~"^(alpine_hut|viewpoint|attraction)$"]["name"]{bb};'
             f'node["aerialway"="station"]["name"]{bb};'
             f'{extra});out;')
        for el in mk.overpass(q)["elements"]:
            seen[el["id"]] = el
    return list(seen.values())


def find(pl, regex, kinds=None, near=None):
    """Find a named OSM node. regex matches name / name:it / name:de. near=(lon,lat) picks the closest."""
    rx = re.compile(regex, re.I)
    best = []
    for el in pl:
        t = el.get("tags", {})
        names = " | ".join(t.get(k, "") for k in ("name", "name:it", "name:de", "name:lld", "alt_name", "int_name"))
        if not rx.search(names):
            continue
        if kinds and not any(k in t.get("place", "") + t.get("natural", "") + t.get("mountain_pass", "") + t.get("tourism", "") + t.get("aerialway", "") for k in kinds):
            continue
        best.append((el["lon"], el["lat"], t))
    if not best:
        return None
    if near:
        best.sort(key=lambda b: (b[0] - near[0]) ** 2 + (b[1] - near[1]) ** 2)
    return best[0]


def render(spec):
    bbox = spec["bbox"]
    w, s, e, n = bbox
    fw = spec.get("width_in", 5.6)
    x0, y0 = mk.merc(w, s)
    x1, y1 = mk.merc(e, n)
    fh = fw * (y1 - y0) / (x1 - x0)
    el, ext = mk.terrain((w - 0.05, s - 0.04, e + 0.05, n + 0.04), spec.get("zoom", 11))
    el = gaussian_filter(el, spec.get("smooth", 0.8))
    hs = mk.hillshade(el, ext, vert=spec.get("vert", 1.6))
    fig = plt.figure(figsize=(fw, fh + 0.25), dpi=300)
    ax = fig.add_axes([0, 0.04, 1, 0.96])
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.axis("off")
    shade = 0.45 + 0.55 * hs
    # lighten valleys a touch, darken high ground, so relief reads in greyscale
    ev = np.clip((el - 300) / 3000.0, 0, 1)
    shade = np.clip(shade * (1.0 - 0.18 * ev) + 0.10, 0, 1)
    ax.imshow(shade, cmap="Greys_r", vmin=0.15, vmax=1.0, extent=ext, origin="upper", interpolation="bilinear", zorder=0)
    if spec.get("contours", True):
        xs = np.linspace(ext[0], ext[1], el.shape[1])
        ys = np.linspace(ext[3], ext[2], el.shape[0])
        ax.contour(xs, ys, el, levels=np.arange(500, 3500, spec.get("contour_step", 500)), colors="#555", linewidths=0.18, alpha=0.5, zorder=1)

    data = fetch(bbox, roads=spec.get("roads", "primary|secondary"), tert=spec.get("tertiary", False), lifts=spec.get("lifts", False))
    hi_ref = set(spec.get("highlight_refs", []))
    for d in data:
        t = d.get("tags", {})
        pts = mk.way_xy(d)
        if len(pts) < 2:
            continue
        xs_, ys_ = zip(*pts)
        if t.get("natural") == "water":
            if len(pts) > 3 and pts[0] == pts[-1]:
                ax.add_patch(Polygon(pts, closed=True, fc="white", ec="#333", lw=0.4, alpha=0.95, zorder=2))
        elif t.get("railway") == "rail":
            ax.plot(xs_, ys_, color="black", lw=1.6, zorder=3, solid_capstyle="butt")
            ax.plot(xs_, ys_, color="white", lw=0.9, ls=(0, (3, 3)), zorder=3.1)
        elif t.get("aerialway"):
            ax.plot(xs_, ys_, color="#222", lw=0.8, ls=(0, (1, 1.5)), zorder=3.2)
        elif t.get("highway"):
            hw = t["highway"]
            ref = t.get("ref", "")
            is_hi = any(r in ref.replace(";", " ").split() or r in ref for r in hi_ref) if hi_ref else False
            if is_hi:
                ax.plot(xs_, ys_, color="white", lw=4.2, zorder=4, solid_capstyle="round")
                ax.plot(xs_, ys_, color="black", lw=2.6, zorder=4.1, solid_capstyle="round")
            else:
                lw = {"motorway": 2.0, "trunk": 1.6, "primary": 1.3, "secondary": 1.0, "tertiary": 0.6}.get(hw, 0.6)
                ax.plot(xs_, ys_, color="white", lw=lw + 1.2, zorder=3.3, solid_capstyle="round")
                ax.plot(xs_, ys_, color="#222" if hw in ("motorway", "trunk") else "#444", lw=lw, zorder=3.4, solid_capstyle="round")

    pl = pois(bbox, extra=spec.get("extra_pois", ""))
    texts = []
    markers = {"place": ("o", 3.2, "black"), "peak": ("^", 4.2, "black"), "pass": ("s", 3.0, "black"), "lake": ("o", 3.0, "#000"),
               "hut": ("D", 3.0, "black"), "lift": ("P", 3.4, "black"), "poi": ("*", 5.5, "black"), "air": ("X", 5, "black")}
    for item in spec.get("labels", []):
        label, regex, kind = item[0], item[1], item[2]
        opts = item[3] if len(item) > 3 else {}
        pos = None
        if "lonlat" in opts:
            pos = (opts["lonlat"][0], opts["lonlat"][1])
        elif regex:
            f = find(pl, regex, opts.get("kinds"), opts.get("near"))
            if f:
                pos = (f[0], f[1])
        if not pos:
            print("  !! not found:", label)
            continue
        px, py = mk.merc(*pos)
        if not (x0 < px < x1 and y0 < py < y1):
            continue
        m, ms, col = markers.get(kind, markers["place"])
        ax.plot(px, py, marker=m, ms=ms, mfc="black", mec="white", mew=0.6, zorder=6, ls="none")
        fs = opts.get("fs", spec.get("fs", 6.2))
        weight = "bold" if kind in ("place",) and opts.get("bold", True) else "normal"
        style = "italic" if kind in ("peak", "pass", "lake") else "normal"
        tx = ax.text(px, py, label, fontsize=fs, fontweight=weight, fontstyle=style, color="black", zorder=7,
                     ha=opts.get("ha", "left"), va="center", path_effects=HALO)
        off = opts.get("off", (4, 3))
        tx.set_position((px + off[0] * (x1 - x0) / 400.0, py + off[1] * (y1 - y0) / 400.0))
        texts.append(tx)
    for num, (lon, lat) in spec.get("numbers", {}).items():
        px, py = mk.merc(lon, lat)
        ax.text(px, py, str(num), fontsize=7, fontweight="bold", color="white", ha="center", va="center", zorder=9,
                bbox=dict(boxstyle="circle,pad=0.25", fc="black", ec="white", lw=0.8))
    for r in spec.get("routes", []):
        pts = [mk.merc(*p) for p in r["pts"]]
        xs_, ys_ = zip(*pts)
        ax.plot(xs_, ys_, color="white", lw=3.6, zorder=8, solid_capstyle="round")
        ax.plot(xs_, ys_, color="black", lw=1.8, ls=r.get("ls", (0, (4, 2))), zorder=8.1, solid_capstyle="round")
    for a in spec.get("arrows", []):
        pass
    if spec.get("adjust", False) and texts:
        adjust_text(texts, ax=ax, expand=(1.05, 1.2), arrowprops=dict(arrowstyle="-", color="#333", lw=0.4))

    # scale bar and north arrow
    km = spec.get("scale_km", 20)
    lat_mid = (s + n) / 2
    sc = 1000.0 / math.cos(math.radians(lat_mid))
    bx, by = x0 + (x1 - x0) * 0.04, y0 + (y1 - y0) * 0.05
    ax.plot([bx, bx + km * sc], [by, by], color="black", lw=2.4, zorder=10, solid_capstyle="butt")
    ax.text(bx + km * sc / 2, by + (y1 - y0) * 0.02, f"{km} km", fontsize=6, ha="center", va="bottom", zorder=10, path_effects=HALO)
    nx, ny = x1 - (x1 - x0) * 0.04, y1 - (y1 - y0) * 0.17
    ax.annotate("", xy=(nx, ny + (y1 - y0) * 0.10), xytext=(nx, ny), arrowprops=dict(arrowstyle="-|>", color="black", lw=1.2), zorder=10)
    ax.text(nx, ny + (y1 - y0) * 0.11, "N", fontsize=7, fontweight="bold", ha="center", va="bottom", zorder=10, path_effects=HALO)
    ax.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec="black", lw=0.8, zorder=11))
    fig.text(0.5, 0.012, ATTR, fontsize=4.6, ha="center", va="bottom", color="#333")
    fn = os.path.join(OUT, spec["id"] + ".png")
    fig.savefig(fn, dpi=300, facecolor="white")
    plt.close(fig)
    print("saved", fn)
    return fn
