"""Rebuild contact sheets for the given slots from saved candidates (uses title-keyed thumbnails)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from find_candidates import sheet, CAND
from slots import S
by = {s["id"]: s for s in S}
for sid in sys.argv[1:]:
    sheet(by[sid], json.load(open(os.path.join(CAND, sid + ".json"))))
    print("sheet", sid, flush=True)
