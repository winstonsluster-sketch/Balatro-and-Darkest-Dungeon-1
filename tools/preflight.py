"""Preflight: lay every sheet's rows and columns over each other and list what
would fail: unfilled cells, references between sheets that don't resolve, and
rows whose code isn't implemented in the mod. Exit 1 if anything blocks."""
import re, sys
from sheets import load, ROOT

NA_OK = {("heroes","stat_a"), ("heroes","stat_b"), ("heroes","suit"), ("monsters","boss_blind")}
VANILLA_BACKS = {"b_red","b_blue","b_yellow","b_green","b_black","b_magic","b_nebula","b_ghost",
                 "b_abandoned","b_checkered","b_zodiac","b_painted","b_anaglyph","b_plasma","b_erratic","b_challenge"}
# vanilla boss blinds whose effect needs no #vars# in their text
BOSS_OK = {"bl_wall","bl_mouth","bl_manacle","bl_plant","bl_hook","bl_needle","bl_water","bl_final_heart",
           "bl_final_vessel","bl_final_acorn","bl_club","bl_goad","bl_window","bl_head","bl_psychic","bl_eye","bl_flint","bl_mark"}
SUITS = {"Spades","Hearts","Clubs","Diamonds"}
KINDS = {"unholy","beast","human","eldritch"}

def main():
    s = load()
    core = "\n".join(p.read_text() for p in (ROOT/"mod/DarkestDeck/ddeck").glob("*.lua") if p.name != "data.lua")
    P, W = [], []
    for name, sh in s.items():
        for i, row in enumerate(sh["rows"]):
            rid = row.get("key", f"#{i}")
            for col in sh["columns"]:
                v = row.get(col)
                if v is None or v == "" or v == []: P.append(f"{name}.{rid}.{col}: empty")
                elif v == "-" and (name, col) not in NA_OK: P.append(f"{name}.{rid}.{col}: '-' not allowed here")
            extra = set(row) - set(sh["columns"])
            if extra: P.append(f"{name}.{rid}: cells outside the columns: {sorted(extra)}")
            if row.get("verified") != "ingame": W.append(f"{name}.{rid}: verified={row.get('verified')}")
    heroes = {r["key"]: r for r in s["heroes"]["rows"]}
    classes = {r["dd_class"] for r in heroes.values()}
    files = {r["key"]: r for r in s["companion_files"]["rows"]}
    fields = set(files["hero_info"]["fields"])
    areas = {r["key"]: r for r in s["areas"]["rows"]}
    K = {r["key"]: r["value"] for r in s["constants"]["rows"]}
    # decks
    for d in s["decks"]["rows"]:
        for h in d["party"]:
            if h not in heroes: P.append(f"decks.{d['key']}.party: unknown hero {h}")
        if len(d["party"]) > K.get("party_size", 99): P.append(f"decks.{d['key']}.party: bigger than party_size")
        if d["art_from"] not in VANILLA_BACKS: P.append(f"decks.{d['key']}.art_from: not a vanilla deck")
    # heroes
    for h in heroes.values():
        for c in ("stat_a","stat_b"):
            if h[c] != "-" and h[c] not in fields: P.append(f"heroes.{h['key']}.{c}: {h[c]} not in companion_files.hero_info.fields")
        if h["suit"] != "-" and h["suit"] not in SUITS: P.append(f"heroes.{h['key']}.suit: bad suit")
        if not h["key"].startswith("j_ddeck_"): P.append(f"heroes.{h['key']}: key must start with j_ddeck_")
        if h["rarity"] not in (1,2,3): P.append(f"heroes.{h['key']}.rarity: 1-3")
        used = {int(n) for t in h["text"] for n in re.findall(r"#(\d+)#", t)}
        m = re.search(r"ABILITY\.%s\s*=\s*{\s*vars\s*=\s*(\d+)" % h["ability"], core)
        if not m: P.append(f"heroes.{h['key']}.ability: ABILITY.{h['ability']} not implemented (with vars = N first)")
        elif used and max(used) > int(m.group(1)): P.append(f"heroes.{h['key']}.text: uses #{max(used)}# but ability fills {m.group(1)}")
    xs = [h["atlas_x"] for h in heroes.values()]
    if len(set(xs)) != len(xs): P.append("heroes.atlas_x: duplicates")
    for r in range(1, 4):
        if not any(h["rarity"] == r for h in heroes.values()): P.append(f"heroes: no hero of rarity {r} (that pool would be empty)")
    # states
    kinds = {r["kind"] for r in s["states"]["rows"]}
    if kinds != {"affliction","virtue"}: P.append(f"states.kind: need affliction and virtue, have {kinds}")
    for r in s["states"]["rows"]:
        if not re.search(r"EFFECT\.%s\b" % r["effect"], core): P.append(f"states.{r['key']}.effect: EFFECT.{r['effect']} not implemented")
    # monsters
    bosses_used = set()
    for m in s["monsters"]["rows"]:
        if m["area"] not in areas: P.append(f"monsters.{m['key']}.area: unknown area {m['area']}")
        if m["kind"] not in KINDS: P.append(f"monsters.{m['key']}.kind: {m['kind']} not in {sorted(KINDS)}")
        if m["fallback_dmg_min"] > m["fallback_dmg_max"]: P.append(f"monsters.{m['key']}: dmg min > max")
        if m["boss_blind"] != "-":
            if m["boss_blind"] not in BOSS_OK: P.append(f"monsters.{m['key']}.boss_blind: {m['boss_blind']} not a usable vanilla boss")
            if m["boss_blind"] in bosses_used: P.append(f"monsters.{m['key']}.boss_blind: {m['boss_blind']} used twice (its name is replaced)")
            bosses_used.add(m["boss_blind"])
            if m["boss_text"] == ["-"]: P.append(f"monsters.{m['key']}.boss_text: a boss needs text")
    for a in areas:
        regular = [m for m in s["monsters"]["rows"] if m["area"] == a and m["boss_blind"] == "-"]
        bosses = [m for m in s["monsters"]["rows"] if m["area"] == a and m["boss_blind"] != "-"]
        if len(regular) < K["big_enemies"]: P.append(f"areas.{a}: only {len(regular)} regular monsters, Big Blind needs {K['big_enemies']}")
        if not bosses: P.append(f"areas.{a}: no boss")
    # camping
    for c in s["camping"]["rows"]:
        if c["hero"] != "any" and c["hero"] not in classes: P.append(f"camping.{c['key']}.hero: {c['hero']} is no hero's dd_class")
        if c["cost"] > K["respite"]: P.append(f"camping.{c['key']}.cost: more than a camp's respite")
        if not re.search(r"CAMP\.%s\b" % c["effect"], core): P.append(f"camping.{c['key']}.effect: CAMP.{c['effect']} not implemented")
    for cls in classes:
        if not any(c["hero"] == cls for c in s["camping"]["rows"]): P.append(f"camping: hero {cls} has no camping skill")
    # areas
    nxt = 0
    for a in sorted(areas.values(), key=lambda r: r["ante_from"]):
        if a["ante_from"] != nxt: P.append(f"areas.{a['key']}: antes {nxt}..{a['ante_from']-1} have no area")
        if a["ante_to"] < a["ante_from"]: P.append(f"areas.{a['key']}: ante_to before ante_from")
        nxt = a["ante_to"] + 1
        for c in ("colour_main","colour_light","colour_dark"):
            if not re.fullmatch(r"#[0-9A-Fa-f]{6}", a[c]): P.append(f"areas.{a['key']}.{c}: not #RRGGBB")
    # constants and files used by code
    for r in s["constants"]["rows"]:
        if f"C.{r['key']}" not in core: P.append(f"constants.{r['key']}: never read by the code")
        if not re.search(r"function\s+[\w.:]*%s\s*\(" % r["used_by"], core): P.append(f"constants.{r['key']}.used_by: function {r['used_by']} not found")
    for r in s["companion_files"]["rows"]:
        if r["parse"] != "png" and not re.search(r"PARSE\.%s\b" % r["parse"], core): P.append(f"companion_files.{r['key']}.parse: PARSE.{r['parse']} not implemented")
        if f"companion_files.{r['key']}" not in core: P.append(f"companion_files.{r['key']}: never read by the code")
    toml = (ROOT/"mod/DarkestDeck/lovely.toml").read_text()
    for r in s["hooks"]["rows"]:
        if r["kind"] == "lovely_copy_append":
            if f'target = "{r["target"]}"' not in toml: P.append(f"hooks.{r['key']}: not in lovely.toml")
        elif f'"{r["target"]}"' not in core: P.append(f"hooks.{r['key']}: wrap of {r['target']} not in code")
    data = ROOT/"mod/DarkestDeck/ddeck/data.lua"
    if not data.exists() or data.stat().st_mtime < max(f.stat().st_mtime for f in (ROOT/"design/sheets").glob("*.json")):
        P.append("data.lua is older than the sheets: run tools/gen.py")
    if "-v" in sys.argv:
        for w in W: print("note:", w)
    for p in P: print("BLOCK:", p)
    print(f"preflight: {len(P)} blocking, {len(W)} rows not yet verified in game")
    sys.exit(1 if P else 0)

if __name__ == "__main__": main()
