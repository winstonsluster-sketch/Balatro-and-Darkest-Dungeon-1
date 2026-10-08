-- Darkest Deck: Balatro becomes a Darkest Dungeon expedition.
-- Heroes are the only Jokers, Blinds are monster teams that wound and stress the party,
-- camps come before bosses. ddeck/data.lua (generated from design/sheets) drives it all.
-- Hero, monster and area art and stats are read from the player's own Darkest Dungeon.

local D = require("ddeck.data")

local DDeck = { D = D, C = {}, version = "0.3.0", stats = {}, mstats = {}, images = {}, listings = {}, installed = false }
_G.DDeck = DDeck
local C = DDeck.C
for k, row in pairs(D.constants) do C[k] = row.value end

---------------------------------------------------------------------------
-- Logging (console, and <save dir>/darkestdeck.log)
---------------------------------------------------------------------------
function DDeck.log(msg)
  msg = "[DarkestDeck] " .. tostring(msg)
  print(msg)
  if love and love.filesystem and love.filesystem.append then
    pcall(love.filesystem.append, "darkestdeck.log", msg .. "\n")
  end
end
local log = DDeck.log

function DDeck.hex(c, a)
  c = c:gsub("#", "")
  return tonumber(c:sub(1, 2), 16) / 255, tonumber(c:sub(3, 4), 16) / 255, tonumber(c:sub(5, 6), 16) / 255, a or 1
end
local hex = DDeck.hex
function DDeck.colour(c) return { hex(c, 1) } end

---------------------------------------------------------------------------
-- Companion: the player's Darkest Dungeon folder
---------------------------------------------------------------------------
local PARSE = {}
DDeck.PARSE = PARSE

local function read_file(path)
  local f = io.open(path, "rb")
  if not f then return nil end
  local data = f:read("*a")
  f:close()
  return data
end
DDeck.read_file = read_file

local function parse_cfg(text)
  local out = {}
  for line in (text or ""):gmatch("[^\r\n]+") do
    local k, v = line:match("^%s*([%w_]+)%s*[=:]%s*(.-)%s*$")
    if k then
      v = v:gsub('^"(.*)"$', "%1"):gsub("^'(.*)'$", "%1")
      out[k] = v
    end
  end
  return out
end
DDeck.parse_cfg = parse_cfg

local function cfg_candidates()
  local list = {}
  local ok, lovely = pcall(require, "lovely")
  if ok and type(lovely) == "table" and lovely.mod_dir then
    list[#list + 1] = lovely.mod_dir .. "/DarkestDeck/companion.cfg"
  end
  if love and love.filesystem and love.filesystem.getSaveDirectory then
    list[#list + 1] = love.filesystem.getSaveDirectory() .. "/Mods/DarkestDeck/companion.cfg"
  end
  return list
end

local function looks_like_dd(path)
  if not path or path == "" then return false end
  return read_file(path .. "/heroes/crusader/crusader.info.darkest") ~= nil
      or read_file(path .. "/darkest.exe") ~= nil
end

function DDeck.find_dd(extra_candidates)
  local tried, cands = {}, {}
  for _, p in ipairs(extra_candidates or {}) do cands[#cands + 1] = p end
  for _, cfgp in ipairs(cfg_candidates()) do
    local cfg = parse_cfg(read_file(cfgp))
    if cfg.DD_PATH and cfg.DD_PATH ~= "" then cands[#cands + 1] = cfg.DD_PATH end
  end
  local env = os.getenv("DARKESTDECK_DD")
  if env then cands[#cands + 1] = env end
  cands[#cands + 1] = "C:/Program Files (x86)/Steam/steamapps/common/DarkestDungeon"
  cands[#cands + 1] = "C:/Program Files/Steam/steamapps/common/DarkestDungeon"
  for _, p in ipairs(cands) do
    p = p:gsub("\\", "/"):gsub("/+$", "")
    tried[#tried + 1] = p
    if looks_like_dd(p) then return p end
  end
  return nil, tried
end

-- Lists files under <DD>/<rel> matching a wildcard; paths come back relative to the DD folder.
function DDeck.list_dir(rel, pattern, recursive)
  local key = rel .. "|" .. pattern .. "|" .. tostring(recursive)
  if DDeck.listings[key] then return DDeck.listings[key] end
  local out = {}
  DDeck.listings[key] = out
  local dd = DDeck.dd_path
  if not (dd and io.popen) then return out end
  local base = dd .. "/" .. rel
  local windows = package.config:sub(1, 1) == "\\"
  local cmd
  if windows then
    cmd = 'dir /b ' .. (recursive and "/s " or "") .. '"' .. base:gsub("/", "\\") .. "\\" .. pattern .. '" 2>nul'
  else
    cmd = 'find "' .. base .. '" ' .. (recursive and "" or "-maxdepth 1 ") .. '-name "' .. pattern .. '" 2>/dev/null'
  end
  local ok, f = pcall(io.popen, cmd)
  if not ok or not f then return out end
  local lower_dd = dd:lower()
  for line in f:lines() do
    line = line:gsub("\r", ""):gsub("\\", "/")
    if line ~= "" then
      local relpath
      if line:lower():sub(1, #lower_dd) == lower_dd then
        relpath = line:sub(#dd + 2)
      elseif line:find("/") then
        relpath = nil
      else
        relpath = rel .. "/" .. line
      end
      if relpath then out[#out + 1] = relpath end
    end
  end
  f:close()
  table.sort(out)
  return out
end

-- Some class folders may be named differently (hound_master vs houndmaster).
function DDeck.class_folder(cls)
  DDeck.class_folders = DDeck.class_folders or {}
  if DDeck.class_folders[cls] then return DDeck.class_folders[cls] end
  local found = cls
  if DDeck.dd_path and not read_file(DDeck.dd_path .. "/heroes/" .. cls .. "/" .. cls .. ".info.darkest") then
    local want = cls:gsub("_", "")
    for _, p in ipairs(DDeck.list_dir("heroes", "*.info.darkest", true)) do
      local folder = p:match("^heroes/([^/]+)/")
      if folder and folder:gsub("_", "") == want then found = folder; break end
    end
  end
  DDeck.class_folders[cls] = found
  return found
end

local function nums(recs, rec, field, i)
  local v = recs[rec] and recs[rec][field] and recs[rec][field][i or 1]
  return v and tonumber((v:gsub("%%", ""))) or nil
end

-- "key: .field v v .field v" lines; the first line of each key is kept (level 0).
local function records(text, keep)
  local recs = {}
  for line in (text or ""):gmatch("[^\r\n]+") do
    local rec, rest = line:match("^%s*([%w_]+):%s*(.*)$")
    if rec and not recs[rec] then
      local fields, cur = {}, nil
      for tok in rest:gmatch("%S+") do
        local f = tok:match("^%.([%a_][%w_]*)$")
        if f then cur = f; fields[cur] = {}
        elseif cur then table.insert(fields[cur], tok) end
      end
      if not keep or keep(rec, fields) then recs[rec] = fields end
    end
  end
  return recs
end

function PARSE.info_darkest(text)
  local r = records(text)
  return {
    ["weapon.dmg_min"] = nums(r, "weapon", "dmg", 1),
    ["weapon.dmg_max"] = nums(r, "weapon", "dmg", 2),
    ["weapon.crit"]    = nums(r, "weapon", "crit"),
    ["weapon.spd"]     = nums(r, "weapon", "spd"),
    ["armour.hp"]      = nums(r, "armour", "hp"),
    ["armour.def"]     = nums(r, "armour", "def"),
    ["resistances.death_blow"] = nums(r, "resistances", "death_blow"),
  }
end

-- Monsters: stats .hp, and the first skill line that has a .dmg.
function PARSE.monster_info(text)
  local r = records(text, function(rec, fields) return rec ~= "skill" or fields.dmg ~= nil end)
  return {
    ["stats.hp"] = nums(r, "stats", "hp"),
    ["skill.dmg_min"] = nums(r, "skill", "dmg", 1),
    ["skill.dmg_max"] = nums(r, "skill", "dmg", 2),
  }
end

local function fill(template, vars)
  return (template:gsub("{(%w+)}", function(k) return vars[k] or ("{" .. k .. "}") end))
end
DDeck.fill = fill

function DDeck.load_companion(force, extra_candidates)
  if DDeck.companion_loaded and not force then return end
  DDeck.companion_loaded = true
  DDeck.listings, DDeck.class_folders, DDeck.mstats = {}, nil, {}
  local dd, tried = DDeck.find_dd(extra_candidates)
  DDeck.dd_path = dd
  if not dd then
    log("Darkest Dungeon folder not found (tried: " .. table.concat(tried or {}, "; ") .. "); using built-in fallbacks")
  else
    log("reading Darkest Dungeon from " .. dd)
  end
  for _, key in ipairs(D.heroes_order) do
    local h = D.heroes[key]
    local stats = {}
    if dd then
      local folder = DDeck.class_folder(h.dd_class)
      for _, tmpl in ipairs(D.companion_files.hero_info.paths) do
        local rel = fill(tmpl, { class = folder })
        local txt = read_file(dd .. "/" .. rel)
        if txt then stats = PARSE.info_darkest(txt); stats._from = rel; break end
      end
    end
    DDeck.stats[key] = stats
    log(h.name .. ": " .. (stats._from and ("stats from " .. stats._from) or "fallback stats"))
  end
end

function DDeck.monster_stats(mkey)
  if DDeck.mstats[mkey] then return DDeck.mstats[mkey] end
  DDeck.load_companion()
  local m = D.monsters[mkey]
  local s = {}
  if DDeck.dd_path then
    for _, tmpl in ipairs(D.companion_files.monster_info.paths) do
      local rel = fill(tmpl, { family = m.dd_family })
      local txt = read_file(DDeck.dd_path .. "/" .. rel)
      if txt then s = PARSE.monster_info(txt); s._from = rel; break end
    end
    if not s._from then
      local found = DDeck.list_dir("monsters/" .. m.dd_family, "*.info.darkest", true)[1]
      local txt = found and read_file(DDeck.dd_path .. "/" .. found)
      if txt then s = PARSE.monster_info(txt); s._from = found end
    end
  end
  local out = {
    hp = s["stats.hp"] or m.fallback_hp,
    dmg_min = s["skill.dmg_min"] or m.fallback_dmg_min,
    dmg_max = s["skill.dmg_max"] or m.fallback_dmg_max,
    from = s._from,
  }
  if out.dmg_min > out.dmg_max then out.dmg_min = out.dmg_max end
  DDeck.mstats[mkey] = out
  log(m.name .. ": " .. (out.from and ("stats from " .. out.from) or "fallback stats"))
  return out
end

-- A hero stat column (stat_a / stat_b) times its scale; "-" means "use the fallback as a fixed value".
function DDeck.stat(key, which)
  local h = D.heroes[key]
  local name = h["stat_" .. which]
  local v
  if name ~= "-" then
    DDeck.load_companion()
    v = DDeck.stats[key] and DDeck.stats[key][name]
  end
  if v == nil then v = h["fallback_" .. which] end
  return v * h["scale_" .. which]
end

local function hero_base(key, stat, fallback_col)
  DDeck.load_companion()
  local v = DDeck.stats[key] and DDeck.stats[key][stat]
  return v or D.heroes[key][fallback_col]
end
function DDeck.max_hp(key) return hero_base(key, "armour.hp", "fallback_hp") end
function DDeck.dodge(key) return hero_base(key, "armour.def", "fallback_dodge") end
function DDeck.deathblow(key) return hero_base(key, "resistances.death_blow", "fallback_deathblow") end

---------------------------------------------------------------------------
-- Shared helpers
---------------------------------------------------------------------------
function DDeck.roll(seed)
  return pseudorandom(seed)
end
local roll = DDeck.roll

function DDeck.hero_key(card)
  return card and card.config and card.config.center and card.config.center.ddeck_hero
end

local function extra(card)
  card.ability.extra = type(card.ability.extra) == "table" and card.ability.extra or {}
  local ex = card.ability.extra
  ex.stress = ex.stress or 0
  if ex.hp == nil then
    local key = DDeck.hero_key(card)
    ex.hp = key and DDeck.max_hp(key) or 1
  end
  return ex
end
DDeck.extra = extra

function DDeck.heroes_in_play()
  local list = {}
  for _, c in ipairs((G.jokers and G.jokers.cards) or {}) do
    if DDeck.hero_key(c) and not extra(c).dead then list[#list + 1] = c end
  end
  return list
end
local heroes_in_play = DDeck.heroes_in_play

function DDeck.rank(card)
  for i, c in ipairs((G.jokers and G.jokers.cards) or {}) do
    if c == card then return i end
  end
  return 99
end

function DDeck.say(card, text, colour)
  if card_eval_status_text then
    card_eval_status_text(card, "extra", nil, nil, nil, { message = text, colour = colour })
  end
end
local say = DDeck.say

function DDeck.announce(text, colour)
  log(text)
  if attention_text and G and G.play then
    pcall(attention_text, {
      text = text, scale = 0.8, hold = 1.4, major = G.play, align = "cm",
      offset = { x = 0, y = -2.5 }, backdrop_colour = colour or (G.C and G.C.BLACK), silent = true,
    })
  end
end

---------------------------------------------------------------------------
-- Stress, afflictions, virtues, Death's Door
---------------------------------------------------------------------------
local function state(card)
  local ex = extra(card)
  return ex.state and D.states[ex.state] or nil
end
DDeck.state = state

function DDeck.state_kind(card)
  local st = state(card)
  return st and st.kind or "normal"
end

local function weighted_pick(kind, seed)
  local rows, total = {}, 0
  for _, key in ipairs(D.states_order) do
    local s = D.states[key]
    if s.kind == kind then rows[#rows + 1] = s; total = total + s.weight end
  end
  local r = roll(seed) * total
  for _, s in ipairs(rows) do
    r = r - s.weight
    if r <= 0 then return s end
  end
  return rows[#rows]
end

function DDeck.resolve(card)
  local ex = extra(card)
  local virtuous = roll("ddeck_resolve") * 100 < C.virtue_chance
  local s = weighted_pick(virtuous and "virtue" or "affliction", virtuous and "ddeck_virtue" or "ddeck_affliction")
  ex.state = s.key
  if virtuous then ex.stress = C.virtue_reset end
  say(card, s.name .. "!", { hex(s.colour) })
  if card.juice_up then card:juice_up(0.6, 0.6) end
  if play_sound then play_sound(virtuous and "polychrome1" or "cancel", 1, 0.7) end
  if DDeck.apply_sprite then DDeck.apply_sprite(card) end
  return s
end

-- Removes a hero for good (death); the Joker is destroyed.
function DDeck.kill_hero(card, why)
  local ex = extra(card)
  if ex.dead then return end
  ex.dead = true
  ex.hp = 0
  say(card, why or "Slain!", G.C and G.C.RED)
  log(D.heroes[DDeck.hero_key(card)].name .. " died: " .. tostring(why))
  card.getting_sliced = true
  G.E_MANAGER:add_event(Event({
    func = function()
      if play_sound then play_sound("tarot1") end
      card.T.r = -0.2
      if card.juice_up then card:juice_up(0.3, 0.4) end
      card.states.drag.is = true
      card.children.center.pinch.x = true
      G.E_MANAGER:add_event(Event({
        trigger = "after", delay = 0.3, blockable = false,
        func = function()
          G.jokers:remove_card(card)
          card:remove()
          return true
        end,
      }))
      return true
    end,
  }))
end

function DDeck.heart_attack(card)
  local ex = extra(card)
  if ex.dead then return end
  if ex.hp > 0 then
    ex.hp = 0
    ex.stress = C.heart_attack_reset
    say(card, "Heart Attack! Death's Door", G.C and G.C.RED)
  else
    DDeck.kill_hero(card, "Heart Attack!")
  end
end

function DDeck.add_stress(card, amount, quiet)
  local ex = extra(card)
  if ex.dead or amount == 0 then return end
  local st = state(card)
  if amount > 0 and st and st.effect == "no_stress_xmult" then return end
  local before = ex.stress
  ex.stress = math.max(0, math.min(C.heart_attack_at, ex.stress + amount))
  local delta = ex.stress - before
  if delta ~= 0 and not quiet then
    say(card, (delta > 0 and "+" or "") .. delta .. " Stress", delta > 0 and { hex("#7B3FA0") } or { hex("#5BA3D0") })
  end
  if ex.stress >= C.heart_attack_at then
    DDeck.heart_attack(card)
  elseif not st and ex.stress >= C.resolve_at then
    DDeck.resolve(card)
  end
end

function DDeck.heal(card, amount, quiet)
  local ex = extra(card)
  if ex.dead or amount <= 0 then return 0 end
  local max = DDeck.max_hp(DDeck.hero_key(card))
  local before = ex.hp
  ex.hp = math.min(max, ex.hp + amount)
  local got = ex.hp - before
  if got > 0 and not quiet then say(card, "+" .. got .. " HP", G.C and G.C.GREEN) end
  return got
end

-- Damage from an enemy. At 0 HP a hero is at Death's Door; a further hit may kill.
function DDeck.hurt(card, amount, source)
  local ex = extra(card)
  if ex.dead then return end
  if ex.hp > 0 then
    ex.hp = math.max(0, ex.hp - amount)
    say(card, "-" .. amount .. " HP", G.C and G.C.RED)
    if ex.hp == 0 then say(card, "Death's Door!", G.C and G.C.RED) end
  else
    local key = DDeck.hero_key(card)
    if roll("ddeck_deathblow") * 100 < DDeck.deathblow(key) then
      say(card, "Deathblow Resisted!", G.C and G.C.FILTER)
    else
      DDeck.kill_hero(card, "Slain by " .. (source or "the dark"))
    end
  end
end

function DDeck.most_wounded()
  local best, gap = nil, 0
  for _, c in ipairs(heroes_in_play()) do
    local missing = DDeck.max_hp(DDeck.hero_key(c)) - extra(c).hp
    if missing > gap then best, gap = c, missing end
  end
  return best
end

function DDeck.most_stressed()
  local best, s = nil, 0
  for _, c in ipairs(heroes_in_play()) do
    if extra(c).stress > s then best, s = c, extra(c).stress end
  end
  return best
end

local EFFECT = {}
DDeck.EFFECT = EFFECT
EFFECT.stress_others = function(card, s)     -- Abusive
  for _, other in ipairs(heroes_in_play()) do
    if other ~= card then DDeck.add_stress(other, s.value) end
  end
end
EFFECT.disable_ability = function() end      -- Hopeless (checked by disabled())
EFFECT.lose_money_eor = function(card, s)    -- Selfish
  if ease_dollars then ease_dollars(-s.value) end
  say(card, "-$" .. s.value, G.C and G.C.MONEY)
end
EFFECT.no_stress_xmult = function() end      -- Stalwart (add_stress, score)
EFFECT.xmult = function() end                -- Powerful (score)

local function disabled(card)
  local st = state(card)
  if st and st.effect == "disable_ability" then return true end
  return extra(card).charmed == true
end
DDeck.disabled = disabled

---------------------------------------------------------------------------
-- Hero abilities. vars = how many #n# values the tooltip can use.
-- score: joker_main; held: each card held in hand; played: each scored card;
-- after: once per hand in the enemy phase; loc: tooltip numbers.
---------------------------------------------------------------------------
local ABILITY = {}
DDeck.ABILITY = ABILITY

local function foe_alive(kind)
  return DDeck.enemy_alive_of_kind and DDeck.enemy_alive_of_kind(kind)
end
local function normal_prob()
  return (G.GAME and G.GAME.probabilities and G.GAME.probabilities.normal) or 1
end

ABILITY.smite = { vars = 2,
  score = function(card, key, ctx, res)
    res.mult_mod = DDeck.stat(key, "a") * (foe_alive("unholy") and 2 or 1)
  end,
  loc = function(card, key, v) v[1] = DDeck.stat(key, "a") end,
}
ABILITY.pistol_shot = { vars = 4,
  odds = function(key) return math.max(1, math.floor(100 / math.max(1, DDeck.stat(key, "b")) + 0.5)) end,
  score = function(card, key, ctx, res)
    res.chip_mod = DDeck.stat(key, "a")
    local x = 1
    if roll("ddeck_crit") < normal_prob() / ABILITY.pistol_shot.odds(key) then x = x * 2; res.crit = true end
    if DDeck.rank(card) == 1 then x = x * 1.5 end
    if x > 1 then res.Xmult_mod = x end
  end,
  loc = function(card, key, v) v[1] = DDeck.stat(key, "a"); v[3] = normal_prob(); v[4] = ABILITY.pistol_shot.odds(key) end,
}
ABILITY.noxious_blast = { vars = 2,
  held = function(card, key, ctx)
    local other = ctx.other_card
    if other and other.is_suit and other:is_suit(D.heroes[key].suit) then
      if other.debuff then return { message = localize and localize("k_debuffed") or "Debuffed", colour = G.C.RED, card = card } end
      return { h_mult = DDeck.stat(key, "a"), card = card }
    end
  end,
  loc = function(card, key, v) v[1] = DDeck.stat(key, "a") end,
}
ABILITY.divine_grace = { vars = 3,
  score = function(card, key, ctx, res) res.chip_mod = DDeck.stat(key, "a") end,
  after = function(card, key)
    local t = DDeck.most_wounded()
    if t then DDeck.heal(t, DDeck.stat(key, "b")) end
  end,
  loc = function(card, key, v) v[1] = DDeck.stat(key, "a"); v[3] = DDeck.stat(key, "b") end,
}
ABILITY.iron_swan = { vars = 4,
  score = function(card, key, ctx, res)
    res.Xmult_mod = DDeck.rank(card) == 1 and DDeck.stat(key, "b") or DDeck.stat(key, "a")
  end,
  after = function(card, key) DDeck.add_stress(card, D.heroes[key].self_stress) end,
  always_after = true,
  loc = function(card, key, v) v[1] = DDeck.stat(key, "a"); v[3] = DDeck.stat(key, "b"); v[4] = D.heroes[key].self_stress end,
}
ABILITY.guard = { vars = 3,
  score = function(card, key, ctx, res) res.mult_mod = DDeck.stat(key, "a") end,
  loc = function(card, key, v) v[1] = DDeck.stat(key, "a"); v[3] = DDeck.stat(key, "b") end,
}
ABILITY.collect_bounty = { vars = 3,
  score = function(card, key, ctx, res) res.mult_mod = DDeck.stat(key, "a") end,
  on_kill = function(card, key)
    local v = DDeck.stat(key, "b")
    if ease_dollars then ease_dollars(v) end
    say(card, "Bounty $" .. v, G.C and G.C.MONEY)
  end,
  loc = function(card, key, v) v[1] = DDeck.stat(key, "a"); v[3] = DDeck.stat(key, "b") end,
}
ABILITY.pick_to_face = { vars = 2,
  dodge_mult = 2,
  played = function(card, key, ctx)
    local other = ctx.other_card
    if other and other.is_suit and other:is_suit(D.heroes[key].suit) then
      return { mult = DDeck.stat(key, "a"), card = card }
    end
  end,
  loc = function(card, key, v) v[1] = DDeck.stat(key, "a") end,
}
ABILITY.abyss = { vars = 3,
  score = function(card, key, ctx, res)
    local n = math.floor(roll("ddeck_abyss") * (DDeck.stat(key, "a") + 1))
    if n > 0 then res.mult_mod = n end
  end,
  after = function(card, key)
    local t = DDeck.most_wounded()
    if t then DDeck.heal(t, math.floor(roll("ddeck_wyrd") * (DDeck.stat(key, "b") + 1))) end
  end,
  loc = function(card, key, v) v[1] = DDeck.stat(key, "a"); v[3] = DDeck.stat(key, "b") end,
}
ABILITY.chop = { vars = 4,
  score = function(card, key, ctx, res)
    if roll("ddeck_chop") < normal_prob() / DDeck.stat(key, "b") then
      res.miss = true
    else
      res.Xmult_mod = DDeck.stat(key, "a")
    end
  end,
  loc = function(card, key, v) v[1] = DDeck.stat(key, "a"); v[3] = normal_prob(); v[4] = DDeck.stat(key, "b") end,
}
ABILITY.battle_ballad = { vars = 4,
  current = function(key)
    local n = (G.GAME and G.GAME.ddeck and G.GAME.ddeck.hands_this_blind) or 0
    return math.floor(DDeck.stat(key, "a") * (n + 1))
  end,
  score = function(card, key, ctx, res) res.mult_mod = ABILITY.battle_ballad.current(key) end,
  after = function(card, key)
    local t = DDeck.most_stressed()
    if t then DDeck.add_stress(t, -DDeck.stat(key, "b")) end
  end,
  loc = function(card, key, v)
    v[1] = math.floor(DDeck.stat(key, "a")); v[3] = ABILITY.battle_ballad.current(key); v[4] = DDeck.stat(key, "b")
  end,
}
ABILITY.hounds_rush = { vars = 2,
  score = function(card, key, ctx, res) res.chip_mod = DDeck.stat(key, "a") * (foe_alive("beast") and 2 or 1) end,
  loc = function(card, key, v) v[1] = DDeck.stat(key, "a") end,
}
ABILITY.sniper_shot = { vars = 3,
  score = function(card, key, ctx, res)
    if DDeck.rank(card) >= 3 then res.Xmult_mod = DDeck.stat(key, "a") end
  end,
  after = function(card, key)
    local t = DDeck.most_wounded()
    if t then DDeck.heal(t, DDeck.stat(key, "b")) end
  end,
  loc = function(card, key, v) v[1] = DDeck.stat(key, "a"); v[3] = DDeck.stat(key, "b") end,
}
ABILITY.antiquities = { vars = 3,
  score = function(card, key, ctx, res) res.mult_mod = DDeck.stat(key, "a") end,
  round_end = function(card, key)
    local v = DDeck.stat(key, "b")
    if ease_dollars then ease_dollars(v) end
    say(card, "Antiquities $" .. v, G.C and G.C.MONEY)
  end,
  loc = function(card, key, v) v[1] = DDeck.stat(key, "a"); v[3] = DDeck.stat(key, "b") end,
}
ABILITY.transform = { vars = 4,
  score = function(card, key, ctx, res)
    if extra(card).beast then res.Xmult_mod = DDeck.stat(key, "b") else res.mult_mod = DDeck.stat(key, "a") end
  end,
  after = function(card, key)
    local ex = extra(card)
    if ex.beast then
      for _, o in ipairs(heroes_in_play()) do if o ~= card then DDeck.add_stress(o, 5) end end
    end
    ex.beast = not ex.beast
    say(card, ex.beast and "Transform!" or "Human again", G.C and G.C.FILTER)
  end,
  always_after = true,
  loc = function(card, key, v)
    v[1] = DDeck.stat(key, "a"); v[3] = DDeck.stat(key, "b"); v[4] = extra(card).beast and "Beast now" or "Human now"
  end,
}

function DDeck.score(card, key, ctx)
  local ab = ABILITY[D.heroes[key].ability]
  local res = {}
  if not disabled(card) and ab.score then ab.score(card, key, ctx, res) end
  local st = state(card)
  if st and (st.effect == "xmult" or st.effect == "no_stress_xmult") then
    res.Xmult_mod = (res.Xmult_mod or 1) * st.value
  end
  if res.miss then
    res.miss = nil
    return { message = "Miss!", colour = G.C and G.C.RED, card = card }
  end
  if not (res.mult_mod or res.chip_mod or res.Xmult_mod) then return nil end
  local msg, colour
  if res.Xmult_mod then
    msg = (res.crit and "Critical! X" or "X") .. res.Xmult_mod .. (res.crit and "" or " Mult")
    colour = G.C and G.C.XMULT
  elseif res.mult_mod then
    msg = "+" .. res.mult_mod .. " Mult"; colour = G.C and G.C.MULT
  else
    msg = "+" .. res.chip_mod .. " Chips"; colour = G.C and G.C.CHIPS
  end
  res.crit = nil
  res.message, res.colour, res.card = msg, colour, card
  return res
end

-- Once per hand, from the enemy phase: abilities' after-hand effects and afflictions.
function DDeck.hero_after_hand(card)
  local key = DDeck.hero_key(card)
  local ab = ABILITY[D.heroes[key].ability]
  if ab.after and (ab.always_after or not disabled(card)) then ab.after(card, key) end
  local st = state(card)
  if st and st.effect == "stress_others" then EFFECT.stress_others(card, st) end
end

function DDeck.on_discard(card)
  DDeck.add_stress(card, C.discard_stress)
end

function DDeck.on_round_end(card, key)
  local ex = extra(card)
  if ex.dead then return end
  ex.charmed = nil
  local st = state(card)
  if st and st.effect == "lose_money_eor" then EFFECT.lose_money_eor(card, st) end
  local ab = ABILITY[D.heroes[key].ability]
  if ab.round_end and not disabled(card) then ab.round_end(card, key) end
end

function DDeck.calculate(card, key, ctx)
  local ab = ABILITY[D.heroes[key].ability]
  if extra(card).dead then return nil end
  if ctx.joker_main then return DDeck.score(card, key, ctx) end
  if ctx.individual and not ctx.end_of_round and not ctx.repetition then
    if ctx.cardarea == G.hand and ab.held and not disabled(card) then return ab.held(card, key, ctx) end
    if ctx.cardarea == G.play and ab.played and not disabled(card) then return ab.played(card, key, ctx) end
    return nil
  end
  if ctx.blueprint then return nil end -- copies score, but only the real hero suffers
  if ctx.pre_discard then
    DDeck.on_discard(card)
  elseif ctx.end_of_round and not ctx.individual and not ctx.repetition and not ctx.game_over then
    DDeck.on_round_end(card, key)
  end
  return nil
end

function DDeck.loc_vars(card)
  local key = DDeck.hero_key(card)
  local h = D.heroes[key]
  local v = { 0, "", 0, 0 }
  ABILITY[h.ability].loc(card, key, v)
  local ex = extra(card)
  local hp = ex.hp > 0 and ("HP " .. ex.hp .. "/" .. DDeck.max_hp(key)) or "DEATH'S DOOR"
  local line = hp .. "  Stress " .. ex.stress .. "/" .. C.resolve_at
  local st = state(card)
  if st then line = st.text .. "  |  " .. line end
  if disabled(card) then v[1] = 0 end
  v[2] = line
  return v
end

---------------------------------------------------------------------------
-- Registering heroes (the only Jokers) and the deck; names and texts
---------------------------------------------------------------------------
local function put_in_pool(pool, center)
  if not pool then return end
  for i = #pool, 1, -1 do
    if pool[i].key == center.key then table.remove(pool, i) end
  end
  pool[#pool + 1] = center
end

function DDeck.register_centers(g)
  DDeck.load_companion()
  -- heroes replace every vanilla Joker in the pools (vanilla ones stay defined for old saves)
  if g.P_CENTER_POOLS then g.P_CENTER_POOLS.Joker = {} end
  g.P_JOKER_RARITY_POOLS = { {}, {}, {}, {} }
  for _, key in ipairs(D.heroes_order) do
    local h = D.heroes[key]
    local c = {
      key = key, name = h.name, set = "Joker", order = 150 + h.order, rarity = h.rarity, cost = h.cost,
      unlocked = true, discovered = true, alerted = true, start_alerted = true,
      blueprint_compat = true, eternal_compat = true, perishable_compat = true,
      pos = { x = h.atlas_x, y = 0 }, effect = "", cost_mult = 1.0,
      config = { extra = { stress = 0 } },
      ddeck_hero = key,
    }
    g.P_CENTERS[key] = c
    put_in_pool(g.P_CENTER_POOLS and g.P_CENTER_POOLS.Joker, c)
    put_in_pool(g.P_JOKER_RARITY_POOLS[h.rarity], c)
  end
  for _, key in ipairs(D.decks_order) do
    local d = D.decks[key]
    local art = g.P_CENTERS[d.art_from]
    local c = {
      key = key, name = d.name, set = "Back", order = d.order, stake = 1,
      unlocked = true, discovered = true, alerted = true,
      pos = art and { x = art.pos.x, y = art.pos.y } or { x = 0, y = 0 },
      config = { ddeck_party = d.party },
      ddeck_party = d.party,
    }
    g.P_CENTERS[key] = c
    put_in_pool(g.P_CENTER_POOLS and g.P_CENTER_POOLS.Back, c)
  end
  log("registered " .. #D.heroes_order .. " heroes (the only Jokers) and " .. #D.decks_order .. " deck(s)")
end

DDeck.BLIND_NAMES = {
  bl_small = { name = "Corridor Ambush", text = { "Monsters lurk in the corridor" } },
  bl_big = { name = "Room Battle", text = { "A pack of monsters guards the room" } },
}

function DDeck.inject_loc()
  local L = G and G.localization
  if not (L and L.descriptions) then return end
  L.descriptions.Joker = L.descriptions.Joker or {}
  L.descriptions.Back = L.descriptions.Back or {}
  L.descriptions.Blind = L.descriptions.Blind or {}
  for key, h in pairs(D.heroes) do L.descriptions.Joker[key] = { name = h.name, text = h.text } end
  for key, d in pairs(D.decks) do L.descriptions.Back[key] = { name = d.name, text = d.text } end
  for key, b in pairs(DDeck.BLIND_NAMES) do L.descriptions.Blind[key] = { name = b.name, text = b.text } end
  for _, m in pairs(D.monsters) do
    if m.boss_blind ~= "-" then L.descriptions.Blind[m.boss_blind] = { name = m.name, text = m.boss_text } end
  end
end

function DDeck.random_hero_key(seed, rarity)
  local pool = {}
  for _, key in ipairs(D.heroes_order) do
    if not rarity or D.heroes[key].rarity == rarity then pool[#pool + 1] = key end
  end
  if #pool == 0 then pool = D.heroes_order end
  return pool[math.floor(roll(seed) * #pool) + 1] or pool[1]
end

-- Harder runs: bigger Blinds, fewer hands and discards, a party of four.
function DDeck.apply_difficulty()
  local sp = G.GAME and G.GAME.starting_params
  if not sp then return end
  sp.ante_scaling = (sp.ante_scaling or 1) * C.ante_scaling
  sp.hands = math.max(1, (sp.hands or 4) + C.hands_delta)
  sp.discards = math.max(0, (sp.discards or 3) + C.discards_delta)
  sp.joker_slots = C.party_size
end

function DDeck.give_party(list)
  G.E_MANAGER:add_event(Event({
    func = function()
      if not (G.jokers and G.jokers.cards) then return false end
      local sp = G.GAME.starting_params
      if G.GAME.round_resets then
        G.GAME.round_resets.hands = sp.hands
        G.GAME.round_resets.discards = sp.discards
      end
      if G.jokers.config then G.jokers.config.card_limit = sp.joker_slots end
      for _, key in ipairs(list) do
        local card = create_card("Joker", G.jokers, nil, nil, nil, nil, key)
        card:add_to_deck()
        G.jokers:emplace(card)
      end
      return true
    end,
  }))
end

function DDeck.starting_party(center)
  if center and center.ddeck_party then return center.ddeck_party end
  local list, used = {}, {}
  local tries = 0
  while #list < C.party_size and tries < 50 do
    tries = tries + 1
    local key = DDeck.random_hero_key("ddeck_party", 1)
    if not used[key] then used[key] = true; list[#list + 1] = key end
  end
  return list
end

---------------------------------------------------------------------------
-- Hooks (see design/sheets/hooks.json)
---------------------------------------------------------------------------
local function resolve_path(path)
  local obj, field = path:match("^([%w_]+)%.([%w_]+)$")
  if obj then return _G[obj], field end
  return _G, path
end

function DDeck.wrap(path, make)
  local tbl, field = resolve_path(path)
  if type(tbl) ~= "table" or type(tbl[field]) ~= "function" then
    log("could not hook " .. path .. " (not found)")
    return false
  end
  tbl[field] = make(tbl[field])
  DDeck.hooked = (DDeck.hooked or 0) + 1
  return true
end
local wrap = DDeck.wrap

local function guarded(name, fn, ...)
  local ok, err = pcall(fn, ...)
  if not ok then
    DDeck.errors = DDeck.errors or {}
    if not DDeck.errors[name] then DDeck.errors[name] = true; log(name .. " failed: " .. tostring(err)) end
  end
  return ok, err
end
DDeck.guarded = guarded

function DDeck.install()
  if DDeck.installed then return end
  DDeck.installed = true
  DDeck.hooked = 0
  require("ddeck.battle")
  require("ddeck.look")

  wrap("Game.init_item_prototypes", function(orig)
    return function(self, ...)
      local r = orig(self, ...)
      guarded("register", DDeck.register_centers, self)
      return r
    end
  end)

  wrap("init_localization", function(orig)
    return function(...)
      guarded("localization", DDeck.inject_loc)
      return orig(...)
    end
  end)

  wrap("Card.calculate_joker", function(orig)
    return function(self, context)
      local key = DDeck.hero_key(self)
      if key then
        if self.debuff then return nil end
        return DDeck.calculate(self, key, context or {})
      end
      return orig(self, context)
    end
  end)

  wrap("Card.generate_UIBox_ability_table", function(orig)
    return function(self, ...)
      if DDeck.hero_key(self) then
        local s, v = pcall(DDeck.loc_vars, self)
        DDeck._pending_vars = s and v or nil
      end
      local r = orig(self, ...)
      DDeck._pending_vars = nil
      return r
    end
  end)

  wrap("generate_card_ui", function(orig)
    return function(_c, full_UI_table, specific_vars, ...)
      if DDeck._pending_vars and _c and _c.ddeck_hero then
        specific_vars = DDeck._pending_vars
        DDeck._pending_vars = nil
      end
      return orig(_c, full_UI_table, specific_vars, ...)
    end
  end)

  wrap("create_card", function(orig)
    return function(_type, area, legendary, _rarity, skip_materialize, soulable, forced_key, key_append)
      local card = orig(_type, area, legendary, _rarity, skip_materialize, soulable, forced_key, key_append)
      if card and card.ability and card.ability.set == "Joker" and not DDeck.hero_key(card) then
        local key = DDeck.random_hero_key("ddeck_hire")
        guarded("hire", function()
          card:set_ability(G.P_CENTERS[key])
          if card.set_cost then card:set_cost() end
        end)
      end
      return card
    end
  end)

  wrap("Back.apply_to_run", function(orig)
    return function(self, ...)
      local r = orig(self, ...)
      guarded("difficulty", DDeck.apply_difficulty)
      local c = self.effect and self.effect.center
      DDeck.give_party(DDeck.starting_party(c))
      return r
    end
  end)

  DDeck.install_battle()
  DDeck.install_look()
  log("v" .. DDeck.version .. " installed " .. DDeck.hooked .. "/" .. #D.hooks_order - 1 .. " hooks")
end

return DDeck
