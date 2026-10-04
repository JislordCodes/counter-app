"""Small map toolkit: open terrain tiles + OpenStreetMap vectors -> print-ready greyscale maps.

Data and credits
  * Terrain: Mapzen/AWS Terrain Tiles (EU-DEM, Copernicus) - public tiles, attribution required.
  * Vectors: OpenStreetMap contributors (ODbL) - attribution required.
"""
import hashlib, io, json, math, os, time, urllib.parse, urllib.request
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "images", "maps", "cache")
os.makedirs(CACHE, exist_ok=True)
UA = "DolomitesTravelGuideMaps/1.0 (https://github.com/JislordCodes/counter-app; book maps)"
OVERPASS = "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
TERRAIN = "https://elevation-tiles-prod.s3.amazonaws.com/terrarium/{z}/{x}/{y}.png"


def merc(lon, lat):
    x = lon * 20037508.342789244 / 180.0
    y = math.log(math.tan((90 + lat) * math.pi / 360.0)) / (math.pi / 180.0) * 20037508.342789244 / 180.0
    return x, y


def tile_of(lon, lat, z):
    n = 2 ** z
    x = (lon + 180.0) / 360.0 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return x, y


def _get(url, data=None, tries=4, timeout=120):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:
            last = e
            time.sleep(8 * (i + 1) if "429" in str(e) or "504" in str(e) else 2 * (i + 1))
    raise last


def overpass(query):
    key = hashlib.md5(query.encode()).hexdigest()
    fn = os.path.join(CACHE, key + ".json")
    if os.path.exists(fn):
        return json.load(open(fn))
    raw = _get(OVERPASS, data=urllib.parse.urlencode({"data": query}).encode())
    d = json.loads(raw)
    json.dump(d, open(fn, "w"))
    time.sleep(1.5)
    return d


def terrain(bbox, z):
    """bbox = (west, south, east, north). Returns (elevation array, extent in web-mercator metres)."""
    w, s, e, n = bbox
    x0, y1 = tile_of(w, s, z)
    x1, y0 = tile_of(e, n, z)
    tx0, tx1, ty0, ty1 = int(x0), int(x1), int(y0), int(y1)
    W = (tx1 - tx0 + 1) * 256
    H = (ty1 - ty0 + 1) * 256
    arr = np.zeros((H, W), dtype=np.float32)
    for tx in range(tx0, tx1 + 1):
        for ty in range(ty0, ty1 + 1):
            fn = os.path.join(CACHE, f"t_{z}_{tx}_{ty}.png")
            if not os.path.exists(fn):
                open(fn, "wb").write(_get(TERRAIN.format(z=z, x=tx, y=ty)))
            im = np.array(Image.open(fn).convert("RGB")).astype(np.float32)
            el = im[:, :, 0] * 256 + im[:, :, 1] + im[:, :, 2] / 256 - 32768
            arr[(ty - ty0) * 256:(ty - ty0 + 1) * 256, (tx - tx0) * 256:(tx - tx0 + 1) * 256] = el
    # mercator extent of the stitched tiles
    def tile_xy(tx, ty):
        n_ = 2 ** z
        lon = tx / n_ * 360.0 - 180.0
        lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * ty / n_))))
        return merc(lon, lat)
    xl, yt = tile_xy(tx0, ty0)
    xr, yb = tile_xy(tx1 + 1, ty1 + 1)
    return arr, (xl, xr, yb, yt)


def hillshade(el, extent, az=315, alt=40, vert=1.8):
    xl, xr, yb, yt = extent
    dx = (xr - xl) / el.shape[1]
    dy = (yt - yb) / el.shape[0]
    gy, gx = np.gradient(el * vert, dy, dx)
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    azr, altr = np.radians(360 - az + 90), np.radians(alt)
    hs = np.sin(altr) * np.cos(slope) + np.cos(altr) * np.sin(slope) * np.cos(azr - aspect)
    return np.clip(hs, 0, 1)


def way_xy(el):
    return [merc(p["lon"], p["lat"]) for p in el.get("geometry", [])]


# ---------------------------------------------------------------- vector tiles (VersaTiles, OpenStreetMap data)
import gzip

VT_URL = "https://tiles.versatiles.org/tiles/osm/{z}/{x}/{y}"
_W = 40075016.68557849
_H = _W / 2


def vt(z, x, y):
    import mapbox_vector_tile as mvt
    fn = os.path.join(CACHE, f"v_{z}_{x}_{y}.pbf")
    if not os.path.exists(fn):
        open(fn, "wb").write(_get(VT_URL.format(z=z, x=x, y=y), timeout=40))
        time.sleep(0.25)
    raw = open(fn, "rb").read()
    try:
        raw = gzip.decompress(raw)
    except Exception:
        pass
    return mvt.decode(raw, y_coord_down=True)


def _tile_xy_to_merc(z, tx, ty, px, py, ext):
    n = 2 ** z
    fx = (tx + px / ext) / n
    fy = (ty + py / ext) / n
    return (-_H + fx * _W, _H - fy * _W)


def vt_features(bbox, z, layers):
    """Yield (layer, props, geom_type, coords_in_mercator) for every feature in tiles covering bbox."""
    w, s, e, n = bbox
    x0, y1 = tile_of(w, s, z)
    x1, y0 = tile_of(e, n, z)
    for tx in range(int(x0), int(x1) + 1):
        for ty in range(int(y0), int(y1) + 1):
            d = vt(z, tx, ty)
            for lname in layers:
                lay = d.get(lname)
                if not lay:
                    continue
                ext = lay.get("extent", 4096)
                for f in lay["features"]:
                    g = f["geometry"]
                    t = g["type"]
                    c = g["coordinates"]
                    conv = lambda pt: _tile_xy_to_merc(z, tx, ty, pt[0], pt[1], ext)
                    if t == "LineString":
                        yield lname, f["properties"], t, [conv(p) for p in c]
                    elif t == "MultiLineString":
                        for ln in c:
                            yield lname, f["properties"], "LineString", [conv(p) for p in ln]
                    elif t == "Polygon":
                        yield lname, f["properties"], t, [[conv(p) for p in ring] for ring in c]
                    elif t == "MultiPolygon":
                        for poly in c:
                            yield lname, f["properties"], "Polygon", [[conv(p) for p in ring] for ring in poly]
                    elif t == "Point":
                        yield lname, f["properties"], t, conv(c)
                    elif t == "MultiPoint":
                        for p in c:
                            yield lname, f["properties"], "Point", conv(p)
