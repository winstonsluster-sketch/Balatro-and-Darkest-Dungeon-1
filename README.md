# Darkest Deck

**Balatro × Darkest Dungeon.** Your Darkest Dungeon party fills Balatro's Joker slots, and every hand you play pushes them closer to breaking.

A [lovely-injector](https://github.com/ethangreen-dev/lovely-injector) mod for Balatro that reads hero stats and portraits from **your own installed copy of Darkest Dungeon** while it runs. No Darkest Dungeon files are shipped. Single player. Published on [Melty](https://melty.gg), which installs it, installs lovely and tells the mod where Darkest Dungeon is, all in one click.

## What you get
Balatro becomes a Darkest Dungeon expedition. It is built to be **very hard**.

**Your party**
- **Heroes are the only Jokers.** There are 15 Darkest Dungeon classes, and shops, packs and tarots only ever give heroes.
- **Real portraits and stats.** Each hero's portrait, damage, HP, dodge and deathblow resistance are read from your own Darkest Dungeon install.
- **A party of four.** You have 4 Joker slots, and a hero's position is its rank: rank 1 is the leftmost.
- **Each class works like its Darkest Dungeon self.**
  - **Crusader:** Smite is doubled against Unholy foes.
  - **Highwayman:** crits, plus Point Blank in rank 1.
  - **Plague Doctor:** Blight from Clubs held in hand.
  - **Vestal:** heals the most wounded hero.
  - **Hellion:** Iron Swan in rank 1, but stresses herself.
  - **Man-at-Arms:** guards the party and bolsters it against Stress.
  - **Bounty Hunter:** paid per kill.
  - **Grave Robber:** Diamonds, and dodges twice as often.
  - **Occultist:** random hexes and random heals.
  - **Leper:** a huge Chop that can miss.
  - **Jester:** a ballad that builds through a fight, and soothes the most stressed hero.
  - **Houndmaster:** doubled against Beasts.
  - **Arbalest:** sniper in the back ranks, and a medic.
  - **Antiquarian:** finds gold at the end of each round.
  - **Abomination:** changes form every hand.

**Every Blind is a fight**
- **Monster teams.** Each Blind is a team of real Darkest Dungeon monsters from the current area. Their stats come from your install, and they show on screen.
- **Your score cuts them down** one by one.
- **The survivors strike back.** After every hand each one attacks a hero (front ranks are hit most, and the Man-at-Arms takes half the hits). Every hand spent in the fight also adds Stress to the whole party.
- **Death's Door.** At 0 HP a hero is at Death's Door, and the next hit can kill them for good. If the whole party falls, the run ends.
- **Afflictions and Virtues.** At 100 Stress a hero becomes Abusive, Hopeless or Selfish, or Stalwart or Powerful. At 200 Stress a hero has a heart attack.
- **Bosses.** Every Boss Blind is a Darkest Dungeon boss of the area: the Necromancer, the Prophet, the Swine Prince, the Formless Flesh, the Hag, the Brigand Fusillade, the Siren, the Drowned Crew, the Shuffling Horror or the Heart of Darkness. Each one carries a Balatro boss effect that fits it.

**Camp, only before a boss**
- The party spends 12 respite points on their classes' camping skills: Zealous Speech, Sanctuary, Gallows Humor, Unparalleled Command, Marking the Path, Pilfer and more.
- There is no other healing or rest, and heroes never heal by themselves.

**The look**
- **A new dungeon backdrop every Blind**, read from your install. Small and Big Blinds get corridors; bosses get a room. The areas go Ruins (Antes 1–2), Warrens, Weald, Cove (Ante 7) and the Darkest Dungeon (Ante 8+).
- **The shop sits in front of the Hamlet.**
- **Area colours and torchlight.** The area's colours repaint the background, and a torchlight vignette darkens as Stress rises.

**Difficulty**
- Blinds are 3× Balatro's size.
- You get 1 fewer hand and 1 fewer discard.
- Enemy damage grows every Ante.

**Decks**
- **Expedition Deck:** the classic Crusader, Highwayman, Plague Doctor and Vestal.
- **Every other deck:** hires a random party.

## How it's built
- `design/sheets/*.json`: the source of truth. Each row is one hero, state, rule, deck, file read or game hook; each column is one property.
- `tools/gen.py` turns the sheets into `mod/DarkestDeck/ddeck/data.lua` (one Lua table per row).
- `tools/preflight.py` lays the sheets over each other and the code, and lists empty cells, broken references and unimplemented rows. Run it before every build.
- `mod/DarkestDeck/`: the mod as installed (`lovely.toml`, `ddeck/core.lua`). It uses one lovely patch, a copy-append to `main.lua`; everything else wraps Balatro functions at runtime.
- `tests/run.lua`: headless tests with a stubbed Balatro (`luajit tests/run.lua`). `tests/atlas/`: renders the hero card art in real LÖVE 11.5 (`xvfb-run love tests/atlas "$PWD"`).
- `tools/package.py`: builds `dist/DarkestDeck-<version>.zip`. `design/melty.draft.json` is the validated Melty install recipe (moves to `melty.json` at the root once publishing is agreed).

```
python3 tools/gen.py && python3 tools/preflight.py && luajit tests/run.lua && python3 tools/package.py
```

## Where Darkest Dungeon is read from
Melty writes `DD_PATH=<your Darkest Dungeon folder>` into `Mods/DarkestDeck/companion.cfg` before every Play. The mod then reads:
- `heroes/<class>/<class>.info.darkest` for stats;
- `heroes/<class>/<class>_A/<class>_portrait_roster.png` and the class's guild header for art;
- `dungeons/<area>/*.png` for the backdrops (rooms and corridor walls, found by listing the folder);
- `monsters/<family>/<family>_A/<family>_A.info.darkest` for monster HP and damage;
- `campaign/town/` for the Hamlet behind the shop.

The log lists what it found, so file names can be corrected after the first run.

If something can't be read, the mod falls back to built-in stats and a drawn initial, and logs why in `%AppData%/Balatro/darkestdeck.log`.

## Status
v0.3.0. Built and tested headless (78 tests) plus real-LÖVE renders of the card art and the look (`xvfb-run love tests/look "$PWD" <ante> <stress>`). **Not yet tested inside the running game.**

## Credits
- Balatro by LocalThunk / Playstack. Darkest Dungeon by Red Hook Studios. You need your own copy of both.
- lovely-injector by ethangreen-dev (installed by Melty).
- Built with Claude Code, using the universal-modder toolkit.
