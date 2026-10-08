"""Preflight: lay every sheet's rows and columns over each other and list what
would fail: unfilled cells, references between sheets that don't resolve, and
rows whose code isn't implemented in the mod. Exit 1 if anything blocks."""
import re, sys
from sheets import load, ROOT

NA_OK = {("heroes", "stat_b"), ("heroes", "suit")}   # "-" means "not used" here
VANILLA_BACKS = {"b_red","b_blue","b_yellow","b_green","b_black","b_magic","b_nebula","b_ghost",
                 "b_abandoned","b_checkered","b_zodiac","b_painted","b_anaglyph","b_plasma","b_erratic","b_challenge"}
SUITS = {"Spades","Hearts","Clubs","Diamonds"}

def main():
    s = load()
    core = "\n".join(p.read_text() for p in (ROOT/"mod/DarkestDeck/ddeck").glob("*.lua") if p.name != "data.lua")
    problems, warnings = [], []
    # 1. every row x column cell filled
    for name, sh in s.items():
        for i, row in enumerate(sh["rows"]):
            rid = row.get("key", f"#{i}")
            for col in sh["columns"]:
                v = row.get(col)
                if v is None or v == "" or v == []:
                    problems.append(f"{name}.{rid}.{col}: empty")
                elif v == "-" and (name, col) not in NA_OK:
                    problems.append(f"{name}.{rid}.{col}: '-' not allowed here")
            extra = set(row) - set(sh["columns"])
            if extra: problems.append(f"{name}.{rid}: cells outside the columns: {sorted(extra)}")
            if row.get("verified") != "ingame":
                warnings.append(f"{name}.{rid}: verified={row.get('verified')} (not yet checked in the running game)")
    heroes = {r["key"]: r for r in s["heroes"]["rows"]}
    fields = set(next(r for r in s["companion_files"]["rows"] if r["key"]=="hero_info")["fields"])
    consts = {r["key"] for r in s["constants"]["rows"]}
    # 2. references
    for d in s["decks"]["rows"]:
        for h in d["party"]:
            if h not in heroes: problems.append(f"decks.{d['key']}.party: unknown hero {h}")
        if d["art_from"] not in VANILLA_BACKS: problems.append(f"decks.{d['key']}.art_from: not a vanilla deck")
    for h in heroes.values():
        for c in ("stat_a","stat_b"):
            if h[c] != "-" and h[c] not in fields: problems.append(f"heroes.{h['key']}.{c}: {h[c]} not in companion_files.hero_info.fields")
        if h["suit"] != "-" and h["suit"] not in SUITS: problems.append(f"heroes.{h['key']}.suit: bad suit")
        if not h["key"].startswith("j_ddeck_"): problems.append(f"heroes.{h['key']}: key must start with j_ddeck_")
        # text placeholders must be ones the ability fills
        used = {int(n) for t in h["text"] for n in re.findall(r"#(\d+)#", t)}
        m = re.search(r"ABILITY\.%s\s*=\s*{[^}]*vars\s*=\s*(\d+)" % h["ability"], core)
        if not m: problems.append(f"heroes.{h['key']}.ability: ABILITY.{h['ability']} not implemented (or no vars=N)")
        elif used and max(used) > int(m.group(1)): problems.append(f"heroes.{h['key']}.text: uses #{max(used)}# but ability fills {m.group(1)}")
    xs = [h["atlas_x"] for h in heroes.values()]
    if len(set(xs)) != len(xs): problems.append("heroes.atlas_x: duplicates")
    kinds = {r["kind"] for r in s["states"]["rows"]}
    if kinds != {"affliction","virtue"}: problems.append(f"states.kind: need affliction and virtue, have {kinds}")
    # 3. implemented in code
    for r in s["states"]["rows"]:
        if not re.search(r"EFFECT\.%s\b" % r["effect"], core): problems.append(f"states.{r['key']}.effect: EFFECT.{r['effect']} not implemented")
    for r in s["constants"]["rows"]:
        if f"C.{r['key']}" not in core: problems.append(f"constants.{r['key']}: never read by the code")
        if not re.search(r"function\s+[\w.:]*%s\s*\(" % r["used_by"], core): problems.append(f"constants.{r['key']}.used_by: function {r['used_by']} not found")
    toml = (ROOT/"mod/DarkestDeck/lovely.toml").read_text() if (ROOT/"mod/DarkestDeck/lovely.toml").exists() else ""
    for r in s["hooks"]["rows"]:
        if r["kind"] == "lovely_copy_append":
            if f'target = "{r["target"]}"' not in toml: problems.append(f"hooks.{r['key']}: not in lovely.toml")
        elif f'"{r["target"]}"' not in core: problems.append(f"hooks.{r['key']}: wrap of {r['target']} not in code")
    for r in s["companion_files"]["rows"]:
        if r["parse"] != "png" and not re.search(r"PARSE\.%s\b" % r["parse"], core): problems.append(f"companion_files.{r['key']}.parse: PARSE.{r['parse']} not implemented")
    data = ROOT/"mod/DarkestDeck/ddeck/data.lua"
    if not data.exists() or data.stat().st_mtime < max(f.stat().st_mtime for f in (ROOT/"design/sheets").glob("*.json")):
        problems.append("data.lua is older than the sheets: run tools/gen.py")
    for w in warnings: print("note:", w)
    for p in problems: print("BLOCK:", p)
    print(f"preflight: {len(problems)} blocking, {len(warnings)} notes")
    sys.exit(1 if problems else 0)

if __name__ == "__main__": main()
