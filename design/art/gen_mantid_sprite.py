"""MANTID-7 as a top-down 32x32 pixel sprite in a Quasimorph-like style.

Top-down view, facing right, one floor tile in size. Muted greys, desaturated
red armour, soft dark outline, small hot glows for optics and vents.
Run: python3 gen_mantid_sprite.py  (writes mantid_sprite*.png next to it)
"""
from pathlib import Path
from PIL import Image

HERE = Path(__file__).parent
S = 32

PAL = {
    "o": (22, 22, 25),     # outline
    "k": (36, 37, 41),     # deep shadow
    "d": (54, 56, 61),     # dark grey
    "m": (78, 81, 86),     # mid grey
    "l": (108, 111, 115),  # light grey
    "h": (146, 148, 150),  # highlight
    "w": (190, 190, 186),  # blade edge
    "R": (64, 22, 22),     # red shadow
    "r": (112, 34, 30),    # red
    "q": (156, 52, 40),    # red light
    "e": (255, 84, 56),    # glow
    "E": (255, 196, 150),  # glow core
    "b": (150, 112, 52),   # brass (ammo)
}

px = {}  # (x, y) -> palette key, painted in order (later wins)
thin = set()  # limb pixels: drop-shadowed but not outlined
THIN = [False]


def put(x, y, c):
    if 0 <= x < S and 0 <= y < S:
        px[(x, y)] = c
        if THIN[0]:
            thin.add((x, y))
        else:
            thin.discard((x, y))


def line(x0, y0, x1, y1, c):
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        put(x0, y0, c)
        if (x0, y0) == (x1, y1):
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def rows(x0, y0, art):
    """Stamp an ASCII block; '.' is transparent."""
    for j, row in enumerate(art):
        for i, c in enumerate(row):
            if c != ".":
                put(x0 + i, y0 + j, c)


def leg(hip, knee, foot, upper):
    # 2px femur lit on its top edge, 1px tibia; drawn without outline
    THIN[0] = True
    line(hip[0], hip[1] + 1, knee[0], knee[1] + 1, "k")
    line(*hip, *knee, "l" if upper else "m")
    line(*knee, *foot, "m" if upper else "d")
    put(*knee, "q")
    put(*foot, "h" if upper else "l")  # claw tip
    THIN[0] = False


# ---- legs (painted first so the body overlaps their roots)
# upper side (lit) — far from the light's shadow
leg((16, 12), (20, 6), (24, 3), True)    # front
leg((14, 12), (14, 5), (12, 1), True)    # mid
leg((11, 12), (7, 6), (2, 4), True)      # rear
# lower side (shadowed), braced wider for the stance
leg((16, 20), (21, 26), (25, 29), False)
leg((14, 20), (15, 27), (12, 30), False)
leg((11, 20), (6, 25), (1, 27), False)

# ---- raptorial scythe arms, flared out and forward in a strike stance
THIN[0] = True
# upper arm raised high and forward, blade hooked back toward the head
line(19, 12, 22, 7, "k"); line(19, 11, 22, 6, "l")
put(22, 6, "q"); put(23, 6, "r")
rows(22, 1, [
    "..hww...",
    ".w...wh.",
    "......ww",
    ".......w",
    "......wh",
    ".....h..",
])
line(23, 3, 27, 3, "l"); put(23, 4, "k")
# lower arm cocked back low, blade swept forward and inward
line(19, 20, 22, 25, "k"); line(20, 20, 23, 25, "m")
put(23, 25, "q"); put(22, 25, "R")
rows(22, 25, [
    "..d..hww",
    "..hww..w",
    ".......h",
])
line(25, 26, 27, 26, "m")
THIN[0] = False

# ---- abdomen: segmented hull with red dorsal carapace
rows(3, 11, [
    "...dmmmmd...",
    "..mlqqqqlm..",
    ".mlqqqqqrrm.",
    "mlqqrqqrrrmd",
    "mlqrrqrrrRmd",
    "mmqrrrrrRRmd",
    "dmrrrRrRRRmd",
    ".dmrRRRRRmd.",
    "..dmmddmmd..",
    "...kekkek...",
    "....k..k....",
])
# segment seams on the carapace
for x in (6, 9, 12):
    for y in range(13, 19):
        c = px.get((x, y))
        if c in ("r", "q", "R"):
            put(x, y, {"q": "r", "r": "R", "R": "k"}[c])
put(1, 16, "d"); put(2, 16, "m"); put(0, 16, "h")  # sensor stinger

# ---- thorax: armoured core plate
rows(13, 11, [
    ".kmlllk.",
    "kmhllllm",
    "mlmmmmld",
    "mlmeEmld",   # power core seen through the top vent
    "mlmeemld",
    "mmmmmmmd",
    "dmrrrrmd",
    "kddddddk",
    ".kkkkkk.",
])
# ammo belt feeding the turret from the abdomen
put(12, 13, "b"); put(13, 12, "b"); put(14, 12, "b")

# ---- dorsal twin autocannon, barrels to the front
rows(15, 12, [
    "ommo",
    "mlhm",
    "ommo",
])
line(19, 13, 25, 13, "l"); line(19, 15, 25, 15, "l")
put(19, 14, "d"); put(20, 14, "k"); put(21, 14, "k")
put(25, 13, "h"); put(25, 15, "m")

# ---- head with compound optics and mandibles
rows(21, 12, [
    "kmlk..",
    "mlmmd.",
    "dmeEe.",
    "dmmed.",
    "dmeed.",
    "kddk..",
])
put(26, 14, "w"); put(27, 15, "h")   # mandibles, top lit
put(26, 18, "l"); put(27, 17, "m")

# ---- compose: drop shadow, outer outline, colours
spr = Image.new("RGBA", (S, S), (0, 0, 0, 0))
mask = set(px)
for (x, y) in mask - thin:
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        n = (x + dx, y + dy)
        if n not in mask and 0 <= n[0] < S and 0 <= n[1] < S:
            spr.putpixel(n, PAL["o"] + (255,))
outl = {p for p in ((x, y) for x in range(S) for y in range(S)) if spr.getpixel(p)[3]}
full = mask | outl
shadow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
for (x, y) in full:
    if 0 <= x + 1 < S and 0 <= y + 2 < S:
        shadow.putpixel((x + 1, y + 2), (0, 0, 0, 110))
for (x, y), c in px.items():
    spr.putpixel((x, y), PAL[c] + (255,))
out = Image.alpha_composite(shadow, spr)
out.save(HERE / "mantid_sprite.png")
out.resize((S * 8, S * 8), Image.NEAREST).save(HERE / "mantid_sprite_x8.png")

# ---- in-context preview on a dim metal floor tile grid at the game's ~3x scale
T = 32
floor = Image.new("RGBA", (T * 3, T * 3), (40, 44, 46, 255))
for x in range(T * 3):
    for y in range(T * 3):
        v = 40 + ((x * 7 + y * 13) % 5)
        if x % T in (0, T - 1) or y % T in (0, T - 1):
            v = 30
        floor.putpixel((x, y), (v, v + 4, v + 6, 255))
floor.alpha_composite(out, (T, T))
floor.resize((T * 9, T * 9), Image.NEAREST).save(HERE / "mantid_sprite_preview.png")
