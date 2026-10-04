"""Greyscale print maps for the guide: terrain hillshade + OpenStreetMap vector tiles + our own labels and routes."""
import json, math, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.patches import Polygon as MPoly
from scipy.ndimage import gaussian_filter
from scipy.spatial import cKDTree
import networkx as nx
import mapkit as mk

OUT = os.path.join(mk.ROOT, "images", "maps")
GEO = json.load(open(os.path.join(OUT, "geocode.json")))
ATTR = "© OpenStreetMap contributors · Terrain: Mapzen/AWS Terrain Tiles (EU-DEM, Copernicus)"
HALO = [pe.withStroke(linewidth=2.4, foreground="white")]
ROAD_W = {"motorway": 1.9, "trunk": 1.5, "primary": 1.2, "secondary": 0.9, "tertiary": 0.55, "unclassified": 0.4, "residential": 0.3}
RANK = {"motorway": 5, "trunk": 4, "primary": 3, "secondary": 2, "tertiary": 1, "unclassified": 0, "residential": 0}


MANUAL = json.load(open(os.path.join(OUT, "manual_coords.json")))


def geo(key):
    if key in MANUAL:
        return tuple(MANUAL[key])
    v = GEO.get(key)
    if isinstance(v, list) and v:
        return v[0]["lon"], v[0]["lat"]
    if isinstance(v, (list, tuple)) and len(v) == 2:
        return tuple(v)
    raise KeyError(key)


def road_graph(feats, spec_join=30):
    G = nx.Graph()
    nodes = []
    for lname, p, t, co in feats:
        if lname != "streets" or t != "LineString":
            continue
        kind = p.get("kind")
        if kind in ("rail", "light_rail", "tram", "subway", "funicular", "narrow_gauge", "monorail", "ferry"):
            continue
        pts = [(round(x / 8) * 8, round(y / 8) * 8) for x, y in co]
        for a, b in zip(pts, pts[1:]):
            if a == b:
                continue
            w = math.hypot(a[0] - b[0], a[1] - b[1])
            pen = {"path": 2.2, "footway": 2.2, "steps": 4, "track": 1.6, "service": 3, "cycleway": 2}.get(kind, 1.0)
            if G.has_edge(a, b):
                continue
            G.add_edge(a, b, weight=w * pen, kind=kind)
    ns = list(G.nodes)
    if len(ns) > 1:
        tree = cKDTree(np.array(ns))
        for i, j in tree.query_pairs(spec_join):
            if not G.has_edge(ns[i], ns[j]):
                d = math.hypot(ns[i][0] - ns[j][0], ns[i][1] - ns[j][1])
                G.add_edge(ns[i], ns[j], weight=3 * d + 5, kind="join")
    return G


def snap(G, tree, ns, lon, lat):
    x, y = mk.merc(lon, lat)
    d, i = tree.query((x, y))
    return ns[i], d


def route_path(G, waypoints, kinds_ok=None):
    ns = list(G.nodes)
    tree = cKDTree(np.array(ns))
    pts = []
    for a, b in zip(waypoints, waypoints[1:]):
        na, da = snap(G, tree, ns, *a)
        nb, db = snap(G, tree, ns, *b)
        try:
            path = nx.shortest_path(G, na, nb, weight="weight")
        except nx.NetworkXNoPath:
            # bridge a small gap in the map data: join the closest nodes of the two road pieces
            ca = np.array(list(nx.node_connected_component(G, na)))
            cb = list(nx.node_connected_component(G, nb))
            dd, ii = cKDTree(np.array(cb)).query(ca)
            k = int(dd.argmin())
            if dd[k] < 400:
                u, v = tuple(ca[k]), cb[int(ii[k])]
                G.add_edge(u, v, weight=3 * float(dd[k]) + 5, kind="join")
                print("   bridged a", round(float(dd[k])), "m gap between", a, b)
                path = nx.shortest_path(G, na, nb, weight="weight")
            else:
                print("   no path between", a, b, "snap distances", round(da), round(db))
                path = [na, nb]
        pts.extend(path if not pts else path[1:])
    return pts


def render(spec):
    bbox = spec["bbox"]
    w, s, e, n = bbox
    fw = spec.get("width_in", 5.6)
    x0, y0 = mk.merc(w, s)
    x1, y1 = mk.merc(e, n)
    fh = fw * (y1 - y0) / (x1 - x0)
    z = spec.get("zoom", 11)
    vz = spec.get("vzoom", z)
    el, ext = mk.terrain((w - 0.03, s - 0.02, e + 0.03, n + 0.02), z)
    el = gaussian_filter(el, spec.get("smooth", 0.9))
    hs = mk.hillshade(el, ext, vert=spec.get("vert", 1.7))
    fig = plt.figure(figsize=(fw, fh + 0.22), dpi=300)
    ax = fig.add_axes([0, 0.035, 1, 0.965])
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.axis("off")
    ev = np.clip((el - 300) / 3000.0, 0, 1)
    base = spec.get('light', 0.50)
    shade = np.clip((base + (1 - base) * hs) * (1.0 - 0.15 * ev) + 0.10, 0, 1)
    ax.imshow(shade, cmap="Greys_r", vmin=0.2, vmax=1.0, extent=ext, origin="upper", interpolation="bilinear", zorder=0)
    xs = np.linspace(ext[0], ext[1], el.shape[1])
    ys = np.linspace(ext[3], ext[2], el.shape[0])
    ax.contour(xs, ys, el, levels=np.arange(500, 3500, spec.get("contour_step", 500)), colors="#444", linewidths=0.16, alpha=0.45, zorder=1)

    feats = list(mk.vt_features(bbox, vz, ["streets", "water_polygons", "land", "aerialways", "public_transport"]))
    # land cover and water
    # forest tint: drawn into one mask so overlapping tile buffers do not stack into stripes
    from PIL import Image as _Im, ImageDraw as _Dr
    mw = int(fw * 220)
    mh = int(mw * (y1 - y0) / (x1 - x0))
    fmask = _Im.new("L", (mw, mh), 0)
    fd = _Dr.Draw(fmask)
    for l, p, t, co in feats:
        if l == "land" and t == "Polygon" and p.get("kind") == "forest":
            fd.polygon([((a - x0) / (x1 - x0) * mw, (y1 - b) / (y1 - y0) * mh) for a, b in co[0]], fill=255)
    ov = np.zeros((mh, mw, 4), dtype=np.float32)
    ov[:, :, 3] = np.array(fmask, dtype=np.float32) / 255.0 * 0.07
    ax.imshow(ov, extent=(x0, x1, y0, y1), origin="upper", interpolation="bilinear", zorder=0.5, aspect="auto")
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    for l, p, t, co in feats:
        if l == "water_polygons" and t == "Polygon":
            k = p.get("kind")
            if k in ("water", "lake", "reservoir", "river"):
                ax.add_patch(MPoly(co[0], closed=True, fc="white", ec="#222", lw=0.45, zorder=2))
            elif k == "glacier":
                ax.add_patch(MPoly(co[0], closed=True, fc="white", ec="#666", lw=0.4, ls=(0, (2, 2)), alpha=0.85, zorder=1.5))
    import re as _re
    tile_places = []
    for l, p, t, co in mk.vt_features(bbox, min(vz, 12), ["place_labels"]):
        if l == "place_labels" and t == "Point" and p.get("kind") in ("city", "town", "village", "hamlet"):
            nm = " | ".join(str(p.get(k, "")) for k in ("name", "name_it", "name_de"))
            tile_places.append((nm, co))

    def tile_place(regex, near):
        rx = _re.compile(regex, _re.I)
        cand = [(nm, co) for nm, co in tile_places if rx.search(nm)]
        if not cand:
            return None
        nx0, ny0 = mk.merc(*near)
        cand.sort(key=lambda c: (c[1][0] - nx0) ** 2 + (c[1][1] - ny0) ** 2)
        return cand[0][1]
    poi_cache = []
    poi_loaded = [False]

    def poi_find(regex, near=None):
        if not poi_loaded[0]:
            poi_loaded[0] = True
            for l, p, t, co in mk.vt_features(bbox, 14, ["pois", "public_transport", "place_labels"]):
                if t == "Point" and p.get("name"):
                    poi_cache.append((p["name"], l, p.get("kind"), co))
        rx = _re.compile(regex, _re.I)
        cand = [(nm, co) for nm, l, k, co in poi_cache if rx.search(nm)]
        if not cand:
            return None
        if near:
            nx0, ny0 = mk.merc(*near)
            cand.sort(key=lambda c: (c[1][0] - nx0) ** 2 + (c[1][1] - ny0) ** 2)
        lon_lat = cand[0][1]
        # return lon/lat for downstream code
        lon = lon_lat[0] / 20037508.342789244 * 180.0
        lat = math.degrees(2 * math.atan(math.exp(lon_lat[1] / 20037508.342789244 * math.pi)) - math.pi / 2)
        return lon, lat

    def resolve(item):
        if isinstance(item, dict):
            r = poi_find(item["poi"], item.get("near"))
            if not r:
                print("   !! poi not found:", item["poi"])
                raise KeyError(item["poi"])
            return r
        return geo(item) if isinstance(item, str) else item
    show_paths = spec.get("paths", False)
    order = ["residential", "unclassified", "service", "track", "path", "footway", "tertiary", "secondary", "primary", "trunk", "motorway"]
    lines = [(l, p, co) for l, p, t, co in feats if l == "streets" and t == "LineString"]
    lines.sort(key=lambda r: order.index(r[1].get("kind")) if r[1].get("kind") in order else -1)
    for l, p, co in lines:
        k = p.get("kind")
        xs_, ys_ = zip(*co)
        if k in ("rail",):
            ax.plot(xs_, ys_, color="black", lw=1.7, zorder=3, solid_capstyle="butt")
            ax.plot(xs_, ys_, color="white", lw=0.8, ls=(0, (3, 3)), zorder=3.1)
        elif k in ("path", "footway", "track", "steps"):
            if show_paths:
                ax.plot(xs_, ys_, color="#222", lw=0.45 if k != "track" else 0.55, ls=(0, (2.2, 1.6)), zorder=2.6, alpha=0.8)
        elif k in ROAD_W:
            if RANK[k] < RANK[spec.get("road_min", "secondary")]:
                continue
            lw = ROAD_W[k] * spec.get("road_scale", 1.0)
            ax.plot(xs_, ys_, color="white", lw=lw + 0.9, zorder=3.3, solid_capstyle="round")
            ax.plot(xs_, ys_, color="#111" if k in ("motorway", "trunk") else "#333", lw=lw, zorder=3.4, solid_capstyle="round")
    for l, p, t, co in feats:
        if l == "aerialways" and t == "LineString" and spec.get("lifts", True):
            xs_, ys_ = zip(*co)
            k = p.get("kind")
            if k in ("cable_car", "gondola", "mixed_lift"):
                ax.plot(xs_, ys_, color="#111", lw=0.9, ls=(0, (4, 1.5, 1, 1.5)), zorder=3.6)
            elif spec.get("all_lifts", False):
                ax.plot(xs_, ys_, color="#444", lw=0.5, ls=(0, (1, 1.5)), zorder=3.5)

    # routes computed on the OSM network
    G = None
    for r in spec.get("routes", []):
        if G is None:
            G = road_graph(feats, spec.get("join", 30))
        try:
            wp = [resolve(k) for k in r["via"]]
        except KeyError:
            print("  !! route skipped")
            continue
        path = route_path(G, wp)
        xs_, ys_ = zip(*path)
        ax.plot(xs_, ys_, color="white", lw=r.get("lw", 3.2) + 1.8, zorder=8, solid_capstyle="round", solid_joinstyle="round")
        ax.plot(xs_, ys_, color=r.get("color", "black"), lw=r.get("lw", 3.2), ls=r.get("ls", "-"), zorder=8.1, solid_capstyle="round", solid_joinstyle="round")
    for r in spec.get("straight", []):
        pts = [mk.merc(*resolve(k)) for k in r["via"]]
        xs_, ys_ = zip(*pts)
        ax.plot(xs_, ys_, color="white", lw=r.get("lw", 2.6) + 1.6, zorder=8, solid_capstyle="round")
        ax.plot(xs_, ys_, color="black", lw=r.get("lw", 2.6), ls=r.get("ls", (0, (4, 2))), zorder=8.1, solid_capstyle="round")

    markers = {"place": ("o", 3.4), "peak": ("^", 4.6), "pass": ("s", 3.2), "lake": ("o", 3.0), "hut": ("D", 3.2),
               "lift": ("P", 3.8), "poi": ("*", 6.0), "air": ("X", 5.5), "station": ("s", 3.4)}
    texts = []
    numbered = {v for v in spec.get('numbers', {}).values() if isinstance(v, str)}
    for item in spec.get("labels", []):
        key, label, kind = item[0], item[1], item[2]
        opts = item[3] if len(item) > 3 else {}
        try:
            if "lonlat" in opts:
                lon, lat = opts["lonlat"]
            elif "poi" in opts:
                lon, lat = resolve({"poi": opts["poi"], "near": opts.get("near")})
            else:
                lon, lat = geo(key)
        except KeyError:
            print("  !! no coordinates:", key)
            continue
        px, py = mk.merc(lon, lat)
        if kind == "place" and "lonlat" not in opts:
            tp = tile_place(opts.get("rx", key), (lon, lat))
            if tp and math.hypot(tp[0] - px, tp[1] - py) < 12000:
                px, py = tp
        if not (x0 < px < x1 and y0 < py < y1):
            continue
        m, ms = markers.get(kind, markers["place"])
        is_num = key in numbered
        if kind != "none" and not is_num:
            ax.plot(px, py, marker=m, ms=ms, mfc="black", mec="white", mew=0.7, zorder=9, ls="none")
        fs = opts.get("fs", spec.get("fs", 6.3))
        weight = "bold" if kind in ("place", "air") and opts.get("bold", True) else "normal"
        style = "italic" if kind in ("peak", "pass", "lake", "hut", "lift") else "normal"
        dx, dy = opts.get("off", (4, 2.5))
        if is_num:
            dx = 11 if opts.get('ha', 'left') == 'left' else -11
        tx = ax.text(px + dx * (x1 - x0) / 420.0, py + dy * (y1 - y0) / 420.0, label, fontsize=fs, fontweight=weight,
                     fontstyle=style, color="black", zorder=10, ha=opts.get("ha", "left"), va="center", path_effects=HALO)
        texts.append(tx)
    for num, key in spec.get("numbers", {}).items():
        try:
            lon, lat = resolve(key)
        except KeyError:
            print("  !! number not placed:", num, key)
            continue
        px, py = mk.merc(lon, lat)
        ax.text(px, py, str(num), fontsize=7.2, fontweight="bold", color="white", ha="center", va="center", zorder=11,
                bbox=dict(boxstyle="circle,pad=0.28", fc="black", ec="white", lw=0.9))
    for lab in spec.get("area_labels", []):
        lon, lat, txt = lab[0], lab[1], lab[2]
        px, py = mk.merc(lon, lat)
        ax.text(px, py, txt, fontsize=spec.get("area_fs", 7.5), fontweight="bold", color="#222", ha="center", va="center",
                zorder=7, alpha=0.8, path_effects=[pe.withStroke(linewidth=2.6, foreground="white")], linespacing=1.0)

    km = spec.get("scale_km", 10)
    sc = 1000.0 / math.cos(math.radians((s + n) / 2))
    bx, by = x0 + (x1 - x0) * 0.04, y0 + (y1 - y0) * 0.05
    ax.plot([bx, bx + km * sc], [by, by], color="black", lw=2.6, zorder=12, solid_capstyle="butt")
    ax.plot([bx, bx + km * sc / 2], [by, by], color="white", lw=1.0, zorder=12.1, solid_capstyle="butt")
    ax.text(bx + km * sc / 2, by + (y1 - y0) * 0.022, f"{km} km", fontsize=6, ha="center", va="bottom", zorder=12, path_effects=HALO)
    nx_, ny_ = x1 - (x1 - x0) * 0.04, y1 - (y1 - y0) * 0.18
    ax.annotate("", xy=(nx_, ny_ + (y1 - y0) * 0.10), xytext=(nx_, ny_), arrowprops=dict(arrowstyle="-|>", color="black", lw=1.3), zorder=12)
    ax.text(nx_, ny_ + (y1 - y0) * 0.115, "N", fontsize=7, fontweight="bold", ha="center", va="bottom", zorder=12, path_effects=HALO)
    ax.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec="black", lw=0.9, zorder=13))
    fig.text(0.5, 0.008, ATTR, fontsize=4.7, ha="center", va="bottom", color="#222")
    fn = os.path.join(OUT, spec["id"] + ".png")
    fig.savefig(fn, dpi=300, facecolor="white")
    plt.close(fig)
    print("saved", fn)
    return fn
