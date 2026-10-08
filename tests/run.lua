-- Headless tests: stubs just enough of Balatro to drive Darkest Deck's hooks.
-- Run: luajit tests/run.lua
package.path = "mod/DarkestDeck/?.lua;" .. package.path
package.preload["ddeck.data"] = function() return dofile("mod/DarkestDeck/ddeck/data.lua") end
package.preload["ddeck.core"] = function() return dofile("mod/DarkestDeck/ddeck/core.lua") end

local fails, passes = 0, 0
local function check(name, cond, extra)
  if cond then passes = passes + 1 else fails = fails + 1; print("FAIL " .. name .. (extra and (": " .. tostring(extra)) or "")) end
end

-- deterministic pseudorandom we can steer
local rolls = {}
function pseudorandom(seed) local v = table.remove(rolls, 1); return v or 0.99 end

local messages, dollars = {}, 0
function card_eval_status_text(card, kind, a, b, c, extra) messages[#messages + 1] = { card = card, msg = extra.message } end
function ease_dollars(n) dollars = dollars + n end
function play_sound() end
function localize(k) return k end
function Event(t) return t end
local events = {}
G = { C = { RED = {}, MULT = {}, CHIPS = {}, XMULT = {}, MONEY = {}, GREEN = {}, FILTER = {} },
      GAME = { probabilities = { normal = 1 } }, ASSET_ATLAS = {},
      E_MANAGER = { add_event = function(_, e) events[#events + 1] = e end },
      localization = { descriptions = { Joker = {}, Back = {} } } }
local function run_events()
  local guard = 0
  while #events > 0 and guard < 100 do
    guard = guard + 1
    local e = table.remove(events, 1)
    if not e.func() then events[#events + 1] = e end
  end
end

-- Minimal Game / Card / Back classes standing in for Balatro's
Game = {}
function Game:init_item_prototypes()
  self.P_CENTERS = { b_black = { key = "b_black", pos = { x = 0, y = 2 }, set = "Back" } }
  self.P_CENTER_POOLS = { Joker = {}, Back = { self.P_CENTERS.b_black } }
  self.P_JOKER_RARITY_POOLS = { {}, {}, {}, {} }
end
function Game:set_render_settings() end
local loc_inited = false
function init_localization() loc_inited = G.localization.descriptions.Joker.j_ddeck_crusader ~= nil end
local ui_vars
function generate_card_ui(_c, full, specific_vars) ui_vars = specific_vars; return {} end
Card = {}; Card.__index = Card
function Card:set_sprites() end
function Card:calculate_joker(context) return "vanilla" end
function Card:generate_UIBox_ability_table() return generate_card_ui(self.config.center, nil, nil) end
function Card:juice_up() end
function Card:remove() self.removed = true end
Back = {}
function Back:apply_to_run() end
local bg_args
function ease_background_colour(args) bg_args = args end
Sprite = {}
local sprite_draws = 0
function Sprite:draw() sprite_draws = sprite_draws + 1 end
local game_draws = 0
function Game:draw() game_draws = game_draws + 1 end

local function new_card(center)
  return setmetatable({ config = { center = center }, ability = { extra = { stress = 0, state_rounds = 0 } },
    T = {}, states = { drag = {} }, children = { center = { pinch = {} } } }, Card)
end
G.jokers = { cards = {}, remove_card = function(self, c)
  for i, x in ipairs(self.cards) do if x == c then table.remove(self.cards, i) end end end,
  emplace = function(self, c) self.cards[#self.cards + 1] = c end }
function create_card(_t, area, l, r, s, so, key) local c = new_card(G.P_CENTERS[key]); c.add_to_deck = function() end; return c end

-- 1. install
local DD = require("ddeck.core")
DD.install()
check("hooks wrapped", Card.calculate_joker ~= nil)
-- point the companion reader at the fixture install
DD.load_companion(true, { "tests/fixtures/dd" })
check("dd path found", DD.dd_path == "tests/fixtures/dd", DD.dd_path)

-- 2. prototypes
G.P_CENTERS = nil
Game.init_item_prototypes(G)
check("crusader registered", G.P_CENTERS.j_ddeck_crusader and G.P_CENTERS.j_ddeck_crusader.set == "Joker")
check("4 heroes in Joker pool", #G.P_CENTER_POOLS.Joker == 4, #G.P_CENTER_POOLS.Joker)
check("heroes in uncommon pool", #G.P_JOKER_RARITY_POOLS[2] == 4)
check("deck in Back pool", G.P_CENTER_POOLS.Back[2] and G.P_CENTER_POOLS.Back[2].key == "b_ddeck_expedition")
check("deck art copied from Black Deck", G.P_CENTERS.b_ddeck_expedition.pos.y == 2)
Game.init_item_prototypes(G) -- idempotent
check("no duplicates on re-init", #G.P_CENTER_POOLS.Joker == 4)

-- 3. localization
init_localization()
check("loc injected before parsing", loc_inited)

-- 4. stats from install vs fallback
check("crusader mult read from install (13)", DD.stat("j_ddeck_crusader", "a") == 13, DD.stat("j_ddeck_crusader", "a"))
check("highwayman chips 11*5", DD.stat("j_ddeck_highwayman", "a") == 55)
check("highwayman crit 10%*4 -> 40", DD.stat("j_ddeck_highwayman", "b") == 40)
check("vestal falls back to 24 hp", DD.stat("j_ddeck_vestal", "a") == 24)
check("pistol odds 1 in 3", DD.ABILITY.pistol_shot.odds("j_ddeck_highwayman") == 3)

-- 5. scoring
local cru = new_card(G.P_CENTERS.j_ddeck_crusader)
local hw  = new_card(G.P_CENTERS.j_ddeck_highwayman)
local pd  = new_card(G.P_CENTERS.j_ddeck_plague_doctor)
local ves = new_card(G.P_CENTERS.j_ddeck_vestal)
G.jokers.cards = { cru, hw, pd, ves }
local r = cru:calculate_joker({ cardarea = G.jokers, joker_main = true })
check("crusader +13 mult", r and r.mult_mod == 13)
rolls = { 0.1 }
r = hw:calculate_joker({ cardarea = G.jokers, joker_main = true })
check("highwayman chips + crit", r and r.chip_mod == 55 and r.Xmult_mod == 2, r and r.message)
rolls = { 0.9 }
r = hw:calculate_joker({ cardarea = G.jokers, joker_main = true })
check("highwayman no crit", r and r.Xmult_mod == nil)
local club = { is_suit = function(_, s) return s == "Clubs" end }
local heart = { is_suit = function(_, s) return s == "Hearts" end }
r = pd:calculate_joker({ cardarea = G.hand, individual = true, other_card = club })
check("plague doctor club held +7", r and r.h_mult == 7)
check("plague doctor heart nil", pd:calculate_joker({ cardarea = G.hand, individual = true, other_card = heart }) == nil)
check("vanilla jokers untouched", Card.calculate_joker(new_card({ name = "Joker" }), {}) == "vanilla")

-- 6. stress per hand, vestal heal
cru:calculate_joker({ cardarea = G.jokers, after = true })
check("crusader +6 stress", cru.ability.extra.stress == 6, cru.ability.extra.stress)
ves:calculate_joker({ cardarea = G.jokers, after = true })
check("vestal heals crusader by 5", cru.ability.extra.stress == 1, cru.ability.extra.stress)
check("vestal own stress 7", ves.ability.extra.stress == 7)
cru:calculate_joker({ pre_discard = true })
check("discard +3", cru.ability.extra.stress == 4)
cru:calculate_joker({ cardarea = G.jokers, after = true, blueprint = true })
check("blueprint copy adds no stress", cru.ability.extra.stress == 4)

-- 7. resolve -> affliction
cru.ability.extra.stress = 98
rolls = { 0.9, 0.01 }  -- not virtuous; pick first affliction (abusive)
cru:calculate_joker({ cardarea = G.jokers, after = true })
check("resolve at 100 -> abusive", cru.ability.extra.state == "abusive", cru.ability.extra.state)
local hw_before = hw.ability.extra.stress
cru:calculate_joker({ cardarea = G.jokers, after = true })
check("abusive stresses others +4", hw.ability.extra.stress == hw_before + 4)

-- hopeless disables ability
pd.ability.extra.state = "hopeless"
check("hopeless PD no held mult", pd:calculate_joker({ cardarea = G.hand, individual = true, other_card = club }) == nil)
pd.ability.extra.state = nil

-- 8. virtue
hw.ability.extra.stress = 99
rolls = { 0.1, 0.99 } -- virtuous; pick last virtue (powerful)
hw:calculate_joker({ cardarea = G.jokers, after = true })
check("virtue powerful", hw.ability.extra.state == "powerful", hw.ability.extra.state)
check("virtue resets stress to 40", hw.ability.extra.stress == 40)
rolls = { 0.9 }
r = hw:calculate_joker({ cardarea = G.jokers, joker_main = true })
check("powerful X2", r and r.Xmult_mod == 2)
hw:calculate_joker({ end_of_round = true })
check("virtue fades after a round", hw.ability.extra.state == nil)
check("camp relief 15", hw.ability.extra.stress == 25, hw.ability.extra.stress)

-- stalwart gains no stress
ves.ability.extra.state = "stalwart"; local vs = ves.ability.extra.stress
ves:calculate_joker({ cardarea = G.jokers, after = true })
check("stalwart no stress", ves.ability.extra.stress == vs)
ves.ability.extra.state = nil

-- 9. selfish & recovery
pd.ability.extra.state = "selfish"; pd.ability.extra.stress = 60; dollars = 0
pd:calculate_joker({ end_of_round = true })
check("selfish -$2", dollars == -2)
check("affliction clears below 50", pd.ability.extra.state == nil and pd.ability.extra.stress == 45)
pd:calculate_joker({ end_of_round = true, game_over = true })
check("no camp on game over", pd.ability.extra.stress == 45)

-- 10. heart attack
cru.ability.extra.stress = 196
cru:calculate_joker({ cardarea = G.jokers, after = true })
check("heart attack marks dead", cru.ability.extra.dead == true)
run_events()
check("dead hero removed from jokers", #G.jokers.cards == 3 and cru.removed)

-- 11. tooltip vars
hw:generate_UIBox_ability_table()
check("tooltip vars passed", ui_vars and ui_vars[1] == 55 and ui_vars[4] == 3, ui_vars and ui_vars[1])
check("tooltip stress line", ui_vars and tostring(ui_vars[2]):find("Stress"))
check("pending vars cleared", DD._pending_vars == nil)

-- 12. expedition deck gives the party
G.jokers.cards = {}
local back = { effect = { center = G.P_CENTERS.b_ddeck_expedition } }
Back.apply_to_run(back)
run_events()
check("party of 4 at run start", #G.jokers.cards == 4)
check("party order", G.jokers.cards[1].config.center.key == "j_ddeck_crusader" and G.jokers.cards[4].config.center.key == "j_ddeck_vestal")

-- 13. info.darkest parser handles decimals and missing records
local p = DD.PARSE.info_darkest("weapon: .name \"x\" .atk 0.5 .dmg 4 8 .crit 2% .spd 3\n")
check("parser dmg", p["weapon.dmg_max"] == 8 and p["weapon.crit"] == 2)
check("parser missing armour", p["armour.hp"] == nil)
-- 14. cfg parsing (what Melty writes)
local cfg = DD.parse_cfg('DD_PATH="D:/Games/Steam/steamapps/common/DarkestDungeon"\r\nX=1\n')
check("cfg DD_PATH", cfg.DD_PATH == "D:/Games/Steam/steamapps/common/DarkestDungeon")

-- 15. the look
G.GAME.round_resets = { ante = 1 }
check("ante 1 is the Ruins", DD.current_area().key == "ruins")
G.GAME.round_resets.ante = 4
check("ante 4 is the Warrens", DD.current_area().key == "warrens")
G.GAME.round_resets.ante = 12
check("ante 12 is the Darkest Dungeon", DD.current_area().key == "darkest")
G.GAME.round_resets.ante = 5
ease_background_colour({ new_colour = { 1, 0, 0, 1 }, delay = 2 })
check("background repainted in Weald colours", bg_args and math.abs(bg_args.new_colour[1] - 0x4C / 255) < 1e-6 and bg_args.delay == 2)
check("contrast from sheet", bg_args.contrast == 1.2)
local paths = DD.backdrop_paths(DD.D.areas.cove)
check("backdrop paths templated", paths[1] == "dungeons/cove/cove.corridor_wall.1.png", paths[1])
check("backdrop path count", #paths == 12 * 3)
-- torchlight follows party stress
G.STAGES = { RUN = 2 }; G.STAGE = 2
G.jokers.cards = { new_card(G.P_CENTERS.j_ddeck_crusader), new_card(G.P_CENTERS.j_ddeck_vestal) }
check("calm party = torch_min", math.abs(DD.torch_alpha() - DD.C.torch_min) < 1e-9)
G.jokers.cards[1].ability.extra.stress = 100; G.jokers.cards[2].ability.extra.stress = 100
check("stressed party = torch_max", math.abs(DD.torch_alpha() - DD.C.torch_max) < 1e-9)
G.STAGE = 1
check("menus = torch_min", math.abs(DD.torch_alpha() - DD.C.torch_min) < 1e-9)
-- draw hooks call through even without love (pcall catches)
Sprite.draw({}); Game.draw(G)
check("draw hooks call originals", sprite_draws == 1 and game_draws == 1)

print(string.format("%d passed, %d failed", passes, fails))
os.exit(fails == 0 and 0 or 1)
