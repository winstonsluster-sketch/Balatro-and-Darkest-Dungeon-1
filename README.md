# Darkest Deck

**Balatro × Darkest Dungeon.** Your Darkest Dungeon party fills Balatro's Joker slots, and every hand you play pushes them closer to breaking.

A [lovely-injector](https://github.com/ethangreen-dev/lovely-injector) mod for Balatro that reads hero stats and portraits from **your own installed copy of Darkest Dungeon** while it runs. No Darkest Dungeon files are shipped. Single player. Published on [Melty](https://melty.gg), which installs it, installs lovely and tells the mod where Darkest Dungeon is, all in one click.

## What you get
- **Four hero Jokers** with their real Darkest Dungeon portraits; their numbers come from each class's level-0 stats in your install:
  - **Crusader**: +Mult equal to his weapon's max damage (Smite).
  - **Highwayman**: +Chips (5× weapon max damage) and a crit chance (4× his crit %) for **X2** Mult.
  - **Plague Doctor**: each **Club** held in hand gives +Mult (Blight).
  - **Vestal**: +Chips equal to her max HP; each hand, the other heroes lose 5 Stress.
- **Stress**: each hand adds Stress to every hero (6–8 by class), and each discard adds 3. At **100** a hero's resolve is tested:
  - 75%: an **Affliction**. *Abusive* stresses the others, *Hopeless* turns off the hero's ability, *Selfish* takes $2 every round.
  - 25%: a **Virtue**. *Stalwart* gives X1.5 Mult and no Stress gain; *Powerful* gives X2 Mult. It lasts one round.
  - An afflicted hero who reaches **200** has a **heart attack** and dies (the Joker is destroyed).
- **Camping**: at the end of each round every hero loses 15 Stress; an Affliction clears below 50.
- **Expedition Deck**: start a run with the whole party. Heroes also appear in the shop (Uncommon) on any deck.

## How it's built
- `design/sheets/*.json`: the source of truth. Each row is one hero, state, rule, deck, file read or game hook; each column is one property.
- `tools/gen.py` turns the sheets into `mod/DarkestDeck/ddeck/data.lua` (one Lua table per row).
- `tools/preflight.py` lays the sheets over each other and the code, and lists empty cells, broken references and unimplemented rows. Run it before every build.
- `mod/DarkestDeck/`: the mod as installed (`lovely.toml`, `ddeck/core.lua`). It uses one lovely patch, a copy-append to `main.lua`; everything else wraps Balatro functions at runtime.
- `tests/run.lua`: headless tests with a stubbed Balatro (`luajit tests/run.lua`). `tests/atlas/`: renders the hero card art in real LÖVE 11.5 (`xvfb-run love tests/atlas "$PWD"`).
- `tools/package.py`: builds `dist/DarkestDeck-<version>.zip`. `melty.json` is the Melty install recipe.

```
python3 tools/gen.py && python3 tools/preflight.py && luajit tests/run.lua && python3 tools/package.py
```

## Where Darkest Dungeon is read from
Melty writes `DD_PATH=<your Darkest Dungeon folder>` into `Mods/DarkestDeck/companion.cfg` before every Play. The mod then reads:
- `heroes/<class>/<class>.info.darkest` for stats;
- `heroes/<class>/<class>_A/<class>_portrait_roster.png` and the class's guild header for art.

If something can't be read, the mod falls back to built-in stats and a drawn initial, and logs why in `%AppData%/Balatro/darkestdeck.log`.

## Status
v0.1.0. Built and tested headless (47 tests) plus a real-LÖVE art render. **Not yet tested inside the running game.**

## Credits
- Balatro by LocalThunk / Playstack. Darkest Dungeon by Red Hook Studios. You need your own copy of both.
- lovely-injector by ethangreen-dev (installed by Melty).
- Built with Claude Code, using the universal-modder toolkit.
