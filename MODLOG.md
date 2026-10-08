# MODLOG

## 2026-10-08: v0.1.0 built (untested in game)
- Route: Balatro host via **lovely-injector only** (Melty auto-installs v0.10.0). Steamodded is not usable (players would install it by hand).
- Darkest Dungeon is the companion. Melty `settings` writes `DD_PATH={game:darkest-dungeon}` into `{appdata}/Balatro/Mods/DarkestDeck/companion.cfg`. `launch.kind=game` takes no env, so this is the route. validate_recipe and one_click_check: valid, one click yes.
- Hooks: module patches for `ddeck.data`/`ddeck.core` plus a copy-append to main.lua that calls `install()`. Runtime wraps: `Game.init_item_prototypes`, `init_localization`, `Game.set_render_settings`, `Card.set_sprites`, `Card.calculate_joker`, `Card.generate_UIBox_ability_table` + `generate_card_ui`, `Back.apply_to_run`.
- Vanilla anchors came from Steamodded's lovely patches (exact vanilla lines), not from Balatro's code; the game isn't available in this cloud container.
- DD formats come from the universal-modder field note `knowledge/games/darkest-dungeon/data-mod-randomizer.md`. Hero class names live in compiled `.loc2`, so names are hard-coded in the sheet.
- Portrait path `heroes/<cls>/<cls>_A/<cls>_portrait_roster.png` is unconfirmed. The code probes 4 candidates and logs which one hit.
- Next: run on the user's PC with both games installed and check `%AppData%/Balatro/darkestdeck.log` for "installed 8/8 hooks", stats from the install, and portraits found.

## 2026-10-08: v0.2.0 adds the Darkest Dungeon look (untested in game)
- New `areas` sheet: Ruins/Warrens/Weald/Cove/Darkest per Ante.
- Hooks: `ease_background_colour` (repaint), `Sprite.draw` (backdrop after `G.SPLASH_BACK`, run stage only), `Game.draw` (torchlight vignette).
- Corridor file names follow the community pattern `dungeons/<area>/<area>.corridor_wall.<n>.png` (720x720). Unconfirmed: the log reports how many were found per area.
- Music and sounds are not possible: Darkest Dungeon packs them in FMOD banks.

## 2026-10-08: v0.3.0 is the full Darkest Dungeon redesign (untested in game)
- Sheets: heroes (15 classes), monsters (29 regulars + 10 bosses mapped onto vanilla boss blinds), camping (18 skills), constants (difficulty, rank weights, Death's Door).
- New hooks:
  - `create_card`: any Joker becomes a hero.
  - `get_new_boss`: area boss.
  - `Blind.set_blind`: encounter, plus camp before a boss.
  - `Game.update_hand_played`: the enemy phase, queued before Balatro's own win/lose check, so a party wipe can set hands_left = 0.
  - `Card.draw`: HP/Stress bars.
- Unknown DD file names are found by listing folders with `dir /b` through io.popen (lovely's console means no window flash), and logged.
- Unverified in game: G.SPLASH_BACK being the in-run background, G.STATES names, attention_text arguments, Card.draw layer names, blind.key in set_blind, banner position.
