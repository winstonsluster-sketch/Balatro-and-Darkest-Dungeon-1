"""Shared loader for the design sheets (design/sheets/*.json)."""
import json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
SHEETS = ROOT / "design" / "sheets"

def load():
    out = {}
    for f in sorted(SHEETS.glob("*.json")):
        d = json.loads(f.read_text())
        out[d["sheet"]] = d
    return out
