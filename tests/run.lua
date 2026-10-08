-- Headless tests: stubs just enough of Balatro to drive Darkest Deck's hooks.
-- Run from the repo root: luajit tests/run.lua
for _, m in ipairs({ "data", "core", "battle", "look" }) do
  package.preload["ddeck." .. m] = function() return dofile("mod/DarkestDeck/ddeck/" .. m .. ".lua") end
end

local fails, passes = 0, 0
local function check(name, cond, extra)
  if cond then passes = passes + 1 else fails = fails + 1; print("FAIL " .. name .. (extra ~= nil and (": " .. tostring(extra)) or "")) end
end

-- deterministic pseudorandom we can steer: queued values first, then 0.99
local rolls = {}
function pseudorandom(seed) local v = table.remove(rolls, 1); return v or 0.99 end

local messages, dollars, attention = {}, 0, {}
function card_eval_status_text(card, kind, a, b, c, extra) messages[#messages + 1] = { card = card, msg = extra.message } end
function attention_text(args) attention[#attention + 1] = args.text end
function ease_dollars(n) dollars = dollars + n end
function play_sound() end
function localize(k) return k end
function number_format(n) return tostring(n) end
function Event(t) return t end
local events = {}
G = { C = { RED = {}, MULT = {}, CHIPS = {}, XMULT = {}, MONEY = {}, GREEN = {}, FILTER = {}, ORANGE = {}, PURPLE = {}, BLACK = {} },
      GAME = { probabilities = { normal = 1 }, round_resets = { ante = 1 }, chips = 0, current_round = { hands_left = 3 },
               starting_params = { hands = 4, discards = 3, joker_slots = 5, ante_scaling = 1 } },
      ASSET_ATLAS = {}, STATES = { SELECTING_HAND = 1, HAND_PLAYED = 2, SHOP = 5 }, STAGES = { RUN = 2 }, STAGE = 2,
      E_MANAGER = { add_event = function(_, e) events[#events + 1] = e end },
      P_BLINDS = { bl_wall = {}, bl_mouth = {}, bl_hook = {}, bl_needle = {}, bl_final_vessel = {}, bl_final_acorn = {},
                   bl_manacle = {}, bl_plant = {}, bl_water = {}, bl_final_heart = {} },
      play = {},
      localization = { descriptions = { Joker = {}, Back = {}, Blind = {} } } }
local function run_events()
  local guard = 0
  while #events > 0 and guard < 200 do
    guard = guard + 1
    local e = table.remove(events, 1)
    if not e.func() then events[#events + 1] = e end
  end
end

-- Minimal stand-ins for Balatro's classes and globals the mod wraps
Game = {}
function Game:init_item_prototypes()
  self.P_CENTERS = { b_black = { key = "b_black", pos = { x = 0, y = 2 }, set = "Back" },
                     j_joker = { key = "j_joker", set = "Joker", name = "Joker", pos = { x = 0, y = 0 } } }
  self.P_CENTER_POOLS = { Joker = { self.P_CENTERS.j_joker }, Back = { self.P_CENTERS.b_black } }
  self.P_JOKER_RARITY_POOLS = { { self.P_CENTERS.j_joker }, {}, {}, {} }
end
function Game:set_render_settings() end
local hand_played_calls = 0
function Game:update_hand_played() hand_played_calls = hand_played_calls + 1; G.STATE_COMPLETE = true end
local game_draws = 0
function Game:draw() game_draws = game_draws + 1 end
local loc_inited = false
function init_localization() loc_inited = G.localization.descriptions.Joker.j_ddeck_crusader ~= nil end
local ui_vars
function generate_card_ui(_c, full, specific_vars) ui_vars = specific_vars; return {} end
function get_new_boss() return "bl_vanilla_boss" end
function ease_background_colour(args) G._bg = args end
Card = {}; Card.__index = Card
function Card:set_sprites() end
function Card:calculate_joker(context) return "vanilla" end
function Card:generate_UIBox_ability_table() return generate_card_ui(self.config.center, nil, nil) end
function Card:juice_up() end
function Card:remove() self.removed = true end
function Card:draw() end
function Card:set_ability(center) self.config.center = center; self.ability = { set = center.set, extra = { stress = 0 } } end
function Card:set_cost() end
Back = {}
function Back:apply_to_run() end
Blind = {}
function Blind:set_blind(blind, reset)
  self.config = { blind = blind }; self.boss = blind and blind.boss or false
  self.chips = 300; G.GAME.chips = 0
end
Sprite = {}
local sprite_draws = 0
function Sprite:draw() sprite_draws = sprite_draws + 1 end

local function new_card(center)
  return setmetatable({ config = { center = center }, ability = { set = center.set, extra = { stress = 0 } },
    T = {}, states = { drag = {} }, children = { center = { pinch = {} } } }, Card)
end
G.jokers = { cards = {}, config = { card_limit = 5 },
  remove_card = function(self, c) for i, x in ipairs(self.cards) do if x == c then table.remove(self.cards, i) end end end,
  emplace = function(self, c) self.cards[#self.cards + 1] = c end }
function create_card(_t, area, l, r, s, so, key)
  local c = new_card(G.P_CENTERS[key or "j_joker"]); c.add_to_deck = function() end; return c
end

---------------------------------------------------------------------------
local DD = require("ddeck.core")
DD.install()
check("all hooks installed", DD.hooked == #DD.D.hooks_order - 1, DD.hooked)
DD.load_companion(true, { "tests/fixtures/dd" })
check("dd path found", DD.dd_path == "tests/fixtures/dd", DD.dd_path)

-- prototypes: heroes are the only Jokers
G.P_CENTERS = nil
Game.init_item_prototypes(G)
check("15 heroes, nothing else, in the Joker pool", #G.P_CENTER_POOLS.Joker == 15, #G.P_CENTER_POOLS.Joker)
for _, c in ipairs(G.P_CENTER_POOLS.Joker) do if not c.ddeck_hero then check("vanilla joker in pool", false, c.key) end end
check("rarity pools hold only heroes", #G.P_JOKER_RARITY_POOLS[1] + #G.P_JOKER_RARITY_POOLS[2] + #G.P_JOKER_RARITY_POOLS[3] == 15)
check("deck registered", G.P_CENTER_POOLS.Back[2].key == "b_ddeck_expedition")
Game.init_item_prototypes(G)
check("no duplicates on re-init", #G.P_CENTER_POOLS.Joker == 15)

-- localization incl. boss renames
init_localization()
check("loc injected before parsing", loc_inited)
check("Hag renames The Hook", G.localization.descriptions.Blind.bl_hook.name == "The Hag")
check("small blind renamed", G.localization.descriptions.Blind.bl_small.name == "Corridor Ambush")

-- any vanilla Joker that gets created becomes a hero
local made = create_card("Joker", G.jokers, nil, nil, nil, nil, "j_joker")
check("create_card turns vanilla jokers into heroes", DD.hero_key(made) ~= nil, made.config.center.key)

-- stats from the install vs fallback
check("crusader mult from install (13)", DD.stat("j_ddeck_crusader", "a") == 13)
check("crusader max HP from install (33)", DD.max_hp("j_ddeck_crusader") == 33)
check("crusader deathblow from install (67)", DD.deathblow("j_ddeck_crusader") == 67)
check("highwayman crit 10%*4", DD.stat("j_ddeck_highwayman", "b") == 40)
check("vestal fallback hp", DD.max_hp("j_ddeck_vestal") == 24)
check("'-' stat uses fallback as value", DD.stat("j_ddeck_leper", "a") == 3)
local ms = DD.monster_stats("bone_soldier")
check("monster stats from install", ms.hp == 9 and ms.dmg_min == 2 and ms.dmg_max == 7 and ms.from, ms.hp)
check("monster fallback", DD.monster_stats("madman").hp == 14)

-- difficulty and starting party
G.jokers.cards = {}
Back.apply_to_run({ effect = { center = G.P_CENTERS.b_ddeck_expedition } })
run_events()
local sp = G.GAME.starting_params
check("blinds x3", sp.ante_scaling == 3)
check("hands 4->3, discards 3->2", sp.hands == 3 and sp.discards == 2)
check("party of four slots", G.jokers.config.card_limit == 4)
check("expedition party", #G.jokers.cards == 4 and G.jokers.cards[1].config.center.key == "j_ddeck_crusader")
G.jokers.cards = {}
sp.ante_scaling, sp.hands, sp.discards = 1, 4, 3
rolls = { 0.0, 0.0, 0.2, 0.4, 0.6 }
Back.apply_to_run({ effect = { center = G.P_CENTERS.b_black } })
run_events()
check("other decks hire 4 distinct heroes", #G.jokers.cards == 4)

-- hero scoring
local P = G.P_CENTERS
local cru, hw, pd, ves = new_card(P.j_ddeck_crusader), new_card(P.j_ddeck_highwayman), new_card(P.j_ddeck_plague_doctor), new_card(P.j_ddeck_vestal)
G.jokers.cards = { cru, hw, pd, ves }
G.GAME.ddeck = { enemies = {} }
local r = cru:calculate_joker({ cardarea = G.jokers, joker_main = true })
check("crusader +13", r and r.mult_mod == 13)
G.GAME.ddeck.enemies = { { alive = true, kind = "unholy" } }
r = cru:calculate_joker({ cardarea = G.jokers, joker_main = true })
check("crusader doubled vs unholy", r and r.mult_mod == 26)
rolls = { 0.9 }
r = hw:calculate_joker({ cardarea = G.jokers, joker_main = true })
check("highwayman rank 2: chips, no X", r and r.chip_mod == 55 and r.Xmult_mod == nil)
G.jokers.cards = { hw, cru, pd, ves }
rolls = { 0.1 }
r = hw:calculate_joker({ cardarea = G.jokers, joker_main = true })
check("highwayman rank 1 crit: X3", r and r.Xmult_mod == 3, r and r.Xmult_mod)
G.jokers.cards = { cru, hw, pd, ves }
local club = { is_suit = function(_, s) return s == "Clubs" end }
local diamond = { is_suit = function(_, s) return s == "Diamonds" end }
r = pd:calculate_joker({ cardarea = G.hand, individual = true, other_card = club })
check("plague doctor club +7", r and r.h_mult == 7)
local gr = new_card(P.j_ddeck_grave_robber)
r = gr:calculate_joker({ cardarea = G.play, individual = true, other_card = diamond })
check("grave robber scored diamond +8", r and r.mult == 8)
local lep = new_card(P.j_ddeck_leper)
rolls = { 0.1 }
r = lep:calculate_joker({ cardarea = G.jokers, joker_main = true })
check("leper misses 1 in 3", r and r.message == "Miss!")
rolls = { 0.9 }
r = lep:calculate_joker({ cardarea = G.jokers, joker_main = true })
check("leper X3", r and r.Xmult_mod == 3)
local hel = new_card(P.j_ddeck_hellion)
G.jokers.cards = { hel }
r = hel:calculate_joker({ cardarea = G.jokers, joker_main = true })
check("hellion rank 1 X2", r and r.Xmult_mod == 2)
local arb = new_card(P.j_ddeck_arbalest)
G.jokers.cards = { cru, hw, arb }
r = arb:calculate_joker({ cardarea = G.jokers, joker_main = true })
check("arbalest rank 3 X2.5", r and r.Xmult_mod == 2.5)
local jes = new_card(P.j_ddeck_jester)
G.GAME.ddeck.hands_this_blind = 2
r = jes:calculate_joker({ cardarea = G.jokers, joker_main = true })
check("jester ballad grows (3 hands x4)", r and r.mult_mod == 12, r and r.mult_mod)
check("vanilla card untouched", Card.calculate_joker(new_card({ name = "Joker", set = "Joker" }), {}) == "vanilla")

-- encounters
G.jokers.cards = { cru, hw, pd, ves }
G.GAME.round_resets.ante = 1
G.GAME.ddeck = nil
rolls = {}
Blind.set_blind(G.GAME.blind or {}, { key = "bl_small" })
G.GAME.blind = { chips = 300, boss = false }
local en = DD.enemies()
check("small blind: 2 enemies", #en == 2, #en)
check("enemies from the Ruins", en[1].key and DD.D.monsters[en[1].key].area == "ruins")
check("last enemy falls at 100%", math.abs(en[#en].dies_at - 1) < 1e-9)

-- enemy phase: partial score kills the first enemy, survivors attack and stress
for _, h in ipairs(G.jokers.cards) do h.ability.extra = { stress = 0 } end
G.GAME.chips = math.ceil(300 * en[1].dies_at)
dollars = 0
rolls = {}
DD.enemy_phase()
check("first enemy slain by score", en[1].alive == false and en[2].alive == true)
check("hands_this_blind counted", G.GAME.ddeck.hands_this_blind == 1)
local stressed = DD.extra(cru).stress
check("living enemy stresses the party", stressed > 0, stressed)
-- attacks hurt someone (rolls default 0.99 => no dodge, max damage, rank 4 target)
local hurt = false
for _, h in ipairs(G.jokers.cards) do if DD.extra(h).hp < DD.max_hp(DD.hero_key(h)) then hurt = true end end
check("enemy attack wounded a hero", hurt)

-- Man-at-Arms guards
local maa = new_card(P.j_ddeck_man_at_arms)
G.jokers.cards = { cru, maa }
rolls = { 0.1 }
check("man-at-arms takes the hit", DD.pick_target() == maa)
G.jokers.cards = { cru, hw, pd, ves }

-- Death's Door and death
DD.extra(ves).hp = 3
rolls = { 0.0 }
DD.hurt(ves, 5, "Bone Soldier")
check("0 HP = Death's Door, alive", DD.extra(ves).hp == 0 and not DD.extra(ves).dead)
rolls = { 0.9 }  -- above vestal deathblow resist (67)
DD.hurt(ves, 2, "Bone Soldier")
check("hit at Death's Door kills", DD.extra(ves).dead == true)
run_events()
check("dead hero removed", #G.jokers.cards == 3 and ves.removed)
DD.extra(cru).hp = 0
rolls = { 0.1 }
DD.hurt(cru, 2, "x")
check("deathblow resisted", not DD.extra(cru).dead)
DD.heal(cru, 5)
check("healing leaves Death's Door", DD.extra(cru).hp == 5)

-- stress: resolve, heart attack -> Death's Door, then death
DD.extra(hw).stress = 98; DD.extra(hw).state = nil
rolls = { 0.9, 0.01 }
DD.add_stress(hw, 5)
check("resolve at 100 -> affliction", DD.extra(hw).state == "abusive", DD.extra(hw).state)
DD.extra(hw).hp = 10
DD.add_stress(hw, 200)
check("heart attack: Death's Door, stress 170", DD.extra(hw).hp == 0 and DD.extra(hw).stress == 170 and not DD.extra(hw).dead)
DD.add_stress(hw, 50)
check("second heart attack kills", DD.extra(hw).dead == true)
run_events()

-- party wipe ends the round
G.jokers.cards = { pd }
DD.extra(pd).hp = 0
G.GAME.ddeck.enemies = { { name = "Madman", alive = true, dies_at = 1, dmg_min = 1, dmg_max = 1, stress = 0, kind = "human" } }
G.GAME.chips = 0
G.GAME.current_round.hands_left = 2
rolls = { 0.9, 0.9, 0.9, 0.9, 0.9, 0.9 }
DD.enemy_phase()
check("party wiped", DD.extra(pd).dead == true)
check("wipe sets hands_left 0", G.GAME.current_round.hands_left == 0)
run_events()

-- victory clears enemies, no attacks
local h2 = new_card(P.j_ddeck_crusader)
G.jokers.cards = { h2 }
G.GAME.ddeck.enemies = { { name = "A", alive = true, dies_at = 1, dmg_min = 50, dmg_max = 50, stress = 50, kind = "human" } }
G.GAME.chips = 300
DD.enemy_phase()
check("victory: no damage", DD.extra(h2).hp == 33 and DD.extra(h2).stress == 0)

-- vestal heals the most wounded after the hand
local v2, c2 = new_card(P.j_ddeck_vestal), new_card(P.j_ddeck_crusader)
G.jokers.cards = { c2, v2 }
DD.extra(c2).hp = 20
DD.hero_after_hand(v2)
check("vestal heals 5", DD.extra(c2).hp == 25)

-- bosses and camp
G.GAME.round_resets.ante = 5
rolls = { 0.0 }
check("weald boss blind", get_new_boss() == "bl_hook")
G.jokers.cards = { new_card(P.j_ddeck_vestal), new_card(P.j_ddeck_crusader), new_card(P.j_ddeck_man_at_arms), new_card(P.j_ddeck_grave_robber) }
for _, h in ipairs(G.jokers.cards) do DD.extra(h).stress = 60; DD.extra(h).hp = 10 end
DD.extra(G.jokers.cards[2]).state = "hopeless"
local plan = DD.plan_camp()
local cost = 0
for _, o in ipairs(plan) do cost = cost + o.skill.cost end
check("camp within 12 respite", cost <= 12 and #plan >= 2, cost)
check("camp picks Sanctuary first", plan[1].skill.key == "sanctuary")
G.GAME.ddeck = {}
G.GAME.current_round.hands_left = 3
G.GAME.blind = {}
Blind.set_blind(G.GAME.blind, { key = "bl_hook", boss = true })
G.GAME.blind.chips = G.GAME.blind.chips
check("boss encounter has the Hag", DD.enemies()[#DD.enemies()].key == "hag")
check("camp ran before the boss", G.GAME.ddeck.camped and G.GAME.ddeck.camped["5"])
check("camp healed", DD.extra(G.jokers.cards[1]).hp > 10)
check("camp relieved stress", DD.extra(G.jokers.cards[1]).stress < 60)
check("+1 hand from Unparalleled Command", G.GAME.current_round.hands_left == 4)
local before = G.GAME.current_round.hands_left
Blind.set_blind(G.GAME.blind, { key = "bl_hook", boss = true })
check("camp once per ante", G.GAME.current_round.hands_left == before)

-- tooltip vars
local tt = new_card(P.j_ddeck_highwayman)
G.jokers.cards = { tt }
tt:generate_UIBox_ability_table()
check("tooltip numbers", ui_vars and ui_vars[1] == 55 and ui_vars[4] == 3)
check("tooltip HP + stress line", ui_vars and tostring(ui_vars[2]):find("HP 23/23") and tostring(ui_vars[2]):find("Stress"), ui_vars and ui_vars[2])
check("pending vars cleared", DD._pending_vars == nil)

-- update_hand_played queues the enemy phase before Balatro's own check
G.STATE_COMPLETE = false
events = {}
Game.update_hand_played(G, 0)
check("enemy phase queued", #events == 1 and hand_played_calls == 1)
events = {}

-- the look
G.GAME.round_resets.ante = 1
check("ante 1 = Ruins", DD.current_area().key == "ruins")
G.GAME.round_resets.ante = 7
check("ante 7 = Cove", DD.current_area().key == "cove")
G.GAME.round_resets.ante = 8
check("ante 8 = Darkest Dungeon", DD.current_area().key == "darkest")
ease_background_colour({ delay = 2 })
check("background in Darkest colours", G._bg and math.abs(G._bg.new_colour[1] - 0x5A / 255) < 1e-6 and G._bg.delay == 2)
local imgs = DD.area_images(DD.D.areas.ruins)
check("listing sorts rooms and corridors", #imgs.rooms == 1 and #imgs.walls == 2, #imgs.rooms .. "/" .. #imgs.walls)
G.GAME.ddeck = { area = "ruins", blind_kind = "boss", blind_index = 3 }
DD.pick_backdrop()
check("boss gets a room", G.GAME.ddeck.backdrop and G.GAME.ddeck.backdrop.wide)
G.GAME.ddeck.blind_kind = "small"
DD.pick_backdrop()
local a1 = G.GAME.ddeck.backdrop.list[G.GAME.ddeck.backdrop.start]
G.GAME.ddeck.blind_index = 4
DD.pick_backdrop()
local a2 = G.GAME.ddeck.backdrop.list[G.GAME.ddeck.backdrop.start]
check("next blind, different corridor", a1 ~= a2, a1 .. " " .. a2)
Sprite.draw({}); Game.draw(G); Card.draw(new_card(P.j_ddeck_crusader), "card")
check("draw hooks call originals", sprite_draws == 1 and game_draws == 1)

-- parsers
local p = DD.PARSE.monster_info("stats: .hp 20 .def 10%\nskill: .id \"buff\" .type \"ranged\"\nskill: .id \"hit\" .dmg 3 6\n")
check("monster parser skips skills without dmg", p["stats.hp"] == 20 and p["skill.dmg_min"] == 3 and p["skill.dmg_max"] == 6)
local cfg = DD.parse_cfg('DD_PATH="D:/Games/DarkestDungeon"\r\n')
check("cfg DD_PATH", cfg.DD_PATH == "D:/Games/DarkestDungeon")

print(string.format("%d passed, %d failed", passes, fails))
os.exit(fails == 0 and 0 or 1)
