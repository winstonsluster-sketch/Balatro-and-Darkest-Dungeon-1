-- Darkest Deck: Darkest Dungeon heroes as Balatro Jokers, with Stress.
-- The rows in ddeck/data.lua (generated from design/sheets) drive everything here.
-- Hero stats and portraits are read from the player's own Darkest Dungeon install.

local D = require("ddeck.data")

local DDeck = { D = D, C = {}, version = "0.2.0", stats = {}, images = {}, installed = false }
_G.DDeck = DDeck
local C = DDeck.C
for k, row in pairs(D.constants) do C[k] = row.value end

---------------------------------------------------------------------------
-- Logging (to the console lovely captures, and to <save dir>/darkestdeck.log)
---------------------------------------------------------------------------
function DDeck.log(msg)
  msg = "[DarkestDeck] " .. tostring(msg)
  print(msg)
  if love and love.filesystem and love.filesystem.append then
    pcall(love.filesystem.append, "darkestdeck.log", msg .. "\n")
  end
end
local log = DDeck.log

---------------------------------------------------------------------------
-- Companion: find the player's Darkest Dungeon folder and read from it
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

-- Paths where companion.cfg may be: Melty writes DD_PATH there before every Play.
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
end

function DDeck.find_dd(extra_candidates)
  local tried = {}
  local cands = {}
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

-- heroes/<cls>/<cls>.info.darkest: one record per line, "key: .field v v .field v".
-- The first weapon:/armour: lines are the level-0 ones.
function PARSE.info_darkest(text)
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
      recs[rec] = fields
    end
  end
  local function num(rec, field, i)
    local v = recs[rec] and recs[rec][field] and recs[rec][field][i or 1]
    return v and tonumber((v:gsub("%%", ""))) or nil
  end
  return {
    ["weapon.dmg_min"] = num("weapon", "dmg", 1),
    ["weapon.dmg_max"] = num("weapon", "dmg", 2),
    ["weapon.crit"]    = num("weapon", "crit"),
    ["weapon.spd"]     = num("weapon", "spd"),
    ["armour.hp"]      = num("armour", "hp"),
    ["armour.def"]     = num("armour", "def"),
  }
end

local function fill(template, cls)
  return (template:gsub("{class}", cls))
end

function DDeck.load_companion(force, extra_candidates)
  if DDeck.companion_loaded and not force then return end
  DDeck.companion_loaded = true
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
      for _, tmpl in ipairs(D.companion_files.hero_info.paths) do
        local txt = read_file(dd .. "/" .. fill(tmpl, h.dd_class))
        if txt then stats = PARSE.info_darkest(txt); stats._from = tmpl; break end
      end
    end
    DDeck.stats[key] = stats
    log(h.name .. ": " .. (stats._from and ("stats from " .. fill(stats._from, h.dd_class)) or "fallback stats"))
  end
end

-- Value of a hero stat column (stat_a/stat_b), times its scale, from the player's install.
function DDeck.stat(key, which)
  local h = D.heroes[key]
  local name = h["stat_" .. which]
  if name == "-" then return 0 end
  DDeck.load_companion()
  local v = DDeck.stats[key] and DDeck.stats[key][name]
  if v == nil then v = h["fallback_" .. which] end
  return v * h["scale_" .. which]
end

---------------------------------------------------------------------------
-- Hero art: build an atlas (normal / afflicted / virtuous rows) from portraits
---------------------------------------------------------------------------
local PX, PY, S = 71, 95, 2
DDeck.ATLAS = "ddeck_heroes"
DDeck.ROW = { normal = 0, affliction = 1, virtue = 2 }

local function hex(c, a)
  c = c:gsub("#", "")
  return tonumber(c:sub(1, 2), 16) / 255, tonumber(c:sub(3, 4), 16) / 255, tonumber(c:sub(5, 6), 16) / 255, a or 1
end

local function load_image(path)
  local data = read_file(path)
  if not data then return nil end
  local ok, img = pcall(function()
    local fd = love.filesystem.newFileData(data, "ddeck.png")
    return love.graphics.newImage(love.image.newImageData(fd))
  end)
  return ok and img or nil
end

local function first_image(dd, row, cls)
  if not dd then return nil end
  for _, tmpl in ipairs(row.paths) do
    local img = load_image(dd .. "/" .. fill(tmpl, cls))
    if img then return img, fill(tmpl, cls) end
  end
end

local function draw_fit(img, x, y, w, h, cover)
  local iw, ih = img:getDimensions()
  local s = cover and math.max(w / iw, h / ih) or math.min(w / iw, h / ih)
  love.graphics.draw(img, x + (w - iw * s) / 2, y + (h - ih * s) / 2, 0, s, s)
end

local function draw_card(h, x, y, state_kind, imgs, font)
  local g = love.graphics
  local w, ht, r = PX * S, PY * S, 5 * S
  g.setColor(hex("#120D0B"))
  g.rectangle("fill", x, y, w, ht, r, r)
  if imgs.header then
    g.setScissor(x + 2 * S, y + 2 * S, w - 4 * S, ht - 4 * S)
    g.setColor(1, 1, 1, 0.35)
    draw_fit(imgs.header, x, y, w, ht, true)
    g.setScissor()
  end
  -- portrait window
  local px, py, pw, ph = x + 8 * S, y + 9 * S, w - 16 * S, 56 * S
  g.setColor(hex("#000000"))
  g.rectangle("fill", px, py, pw, ph)
  if imgs.portrait then
    g.setScissor(px, py, pw, ph)
    g.setColor(1, 1, 1, 1)
    draw_fit(imgs.portrait, px, py, pw, ph, true)
    g.setScissor()
  else
    g.setColor(hex(h.frame_colour))
    local big = imgs.big_font or font
    g.setFont(big)
    g.printf(h.name:sub(1, 1), px, py + ph / 2 - big:getHeight() / 2, pw, "center")
  end
  g.setLineWidth(1.5 * S)
  g.setColor(hex(h.frame_colour))
  g.rectangle("line", px, py, pw, ph)
  -- state overlay
  if state_kind == "affliction" then
    g.setColor(0.7, 0.05, 0.05, 0.35)
    g.rectangle("fill", px, py, pw, ph)
  elseif state_kind == "virtue" then
    g.setColor(1, 0.85, 0.3, 0.22)
    g.rectangle("fill", px, py, pw, ph)
  end
  -- name plate
  g.setFont(font)
  g.setColor(hex(h.frame_colour))
  g.printf(h.name, x + 3 * S, y + 70 * S, w - 6 * S, "center")
  -- outer frame
  local frame = state_kind == "affliction" and "#B3261E" or state_kind == "virtue" and "#E8C547" or h.frame_colour
  g.setLineWidth((state_kind == "normal" and 2 or 3) * S)
  g.setColor(hex(frame))
  g.rectangle("line", x + 1.5 * S, y + 1.5 * S, w - 3 * S, ht - 3 * S, r, r)
end

function DDeck.build_atlas()
  if not (love and love.graphics and G and G.ASSET_ATLAS) then return end
  DDeck.load_companion()
  local cols = 0
  for _, key in ipairs(D.heroes_order) do cols = math.max(cols, D.heroes[key].atlas_x + 1) end
  local font = love.graphics.newFont(7 * S)
  local big = love.graphics.newFont(30 * S)
  local canvas = love.graphics.newCanvas(cols * PX * S, 3 * PY * S)
  love.graphics.push("all")
  love.graphics.setCanvas(canvas)
  love.graphics.clear(0, 0, 0, 0)
  love.graphics.origin()
  for _, key in ipairs(D.heroes_order) do
    local h = D.heroes[key]
    local imgs = DDeck.images[key]
    if not imgs then
      imgs = { big_font = big }
      local p, pfrom = first_image(DDeck.dd_path, D.companion_files.hero_portrait, h.dd_class)
      local hd = first_image(DDeck.dd_path, D.companion_files.hero_header, h.dd_class)
      imgs.portrait, imgs.header = p, hd
      log(h.name .. ": portrait " .. (pfrom or "not found, drawing initial"))
      DDeck.images[key] = imgs
    end
    imgs.big_font = big
    for kind, row in pairs(DDeck.ROW) do
      draw_card(h, h.atlas_x * PX * S, row * PY * S, kind, imgs, font)
    end
  end
  love.graphics.pop()
  local image = love.graphics.newImage(canvas:newImageData(), { mipmaps = true, dpiscale = S })
  G.ASSET_ATLAS[DDeck.ATLAS] = { name = DDeck.ATLAS, image = image, type = "asset_atli", px = PX, py = PY }
  log("hero atlas built")
end

function DDeck.state_kind(card)
  local ex = card.ability and card.ability.extra
  local st = type(ex) == "table" and ex.state and D.states[ex.state]
  return st and st.kind or "normal"
end

function DDeck.apply_sprite(card)
  local center = card.config and card.config.center
  local A = G.ASSET_ATLAS and G.ASSET_ATLAS[DDeck.ATLAS]
  local s = card.children and card.children.center
  if not (center and center.ddeck_hero and A and s and s.set_sprite_pos) then return end
  s.atlas = A
  s:set_sprite_pos({ x = center.pos.x, y = DDeck.ROW[DDeck.state_kind(card)] })
end

---------------------------------------------------------------------------
-- Registering the Jokers and the deck
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
  for _, key in ipairs(D.heroes_order) do
    local h = D.heroes[key]
    local c = {
      key = key, name = h.name, set = "Joker", order = 150 + h.order, rarity = h.rarity, cost = h.cost,
      unlocked = true, discovered = true, alerted = true, start_alerted = true,
      blueprint_compat = true, eternal_compat = true, perishable_compat = true,
      pos = { x = h.atlas_x, y = 0 }, effect = "", cost_mult = 1.0,
      config = { extra = { stress = 0, state = nil, state_rounds = 0 } },
      ddeck_hero = key,
    }
    g.P_CENTERS[key] = c
    put_in_pool(g.P_CENTER_POOLS and g.P_CENTER_POOLS.Joker, c)
    put_in_pool(g.P_JOKER_RARITY_POOLS and g.P_JOKER_RARITY_POOLS[h.rarity], c)
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
  log("registered " .. #D.heroes_order .. " heroes and " .. #D.decks_order .. " deck(s)")
end

function DDeck.inject_loc()
  local L = G and G.localization
  if not (L and L.descriptions) then return end
  L.descriptions.Joker = L.descriptions.Joker or {}
  L.descriptions.Back = L.descriptions.Back or {}
  for key, h in pairs(D.heroes) do
    L.descriptions.Joker[key] = { name = h.name, text = h.text }
  end
  for key, d in pairs(D.decks) do
    L.descriptions.Back[key] = { name = d.name, text = d.text }
  end
end

function DDeck.give_party(list)
  G.E_MANAGER:add_event(Event({
    func = function()
      if not (G.jokers and G.jokers.cards) then return false end
      for _, key in ipairs(list) do
        local card = create_card("Joker", G.jokers, nil, nil, nil, nil, key)
        card:add_to_deck()
        G.jokers:emplace(card)
      end
      return true
    end,
  }))
end

---------------------------------------------------------------------------
-- Stress, afflictions and virtues
---------------------------------------------------------------------------
local function extra(card)
  card.ability.extra = type(card.ability.extra) == "table" and card.ability.extra or {}
  local ex = card.ability.extra
  ex.stress = ex.stress or 0
  ex.state_rounds = ex.state_rounds or 0
  return ex
end
DDeck.extra = extra

local function heroes_in_play()
  local list = {}
  for _, c in ipairs((G.jokers and G.jokers.cards) or {}) do
    if c.config and c.config.center and c.config.center.ddeck_hero and not extra(c).dead then list[#list + 1] = c end
  end
  return list
end
DDeck.heroes_in_play = heroes_in_play

local function say(card, text, colour)
  if card_eval_status_text then
    card_eval_status_text(card, "extra", nil, nil, nil, { message = text, colour = colour })
  end
end

local function state(card)
  local ex = extra(card)
  return ex.state and D.states[ex.state] or nil
end
DDeck.state = state

local function roll(seed)
  return pseudorandom(seed)
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
  if virtuous then
    ex.stress = C.virtue_reset
    ex.state_rounds = C.virtue_rounds
  end
  say(card, s.name .. "!", { hex(s.colour) })
  if card.juice_up then card:juice_up(0.6, 0.6) end
  if play_sound then play_sound(virtuous and "polychrome1" or "cancel", 1, 0.7) end
  DDeck.apply_sprite(card)
  return s
end

function DDeck.heart_attack(card)
  local ex = extra(card)
  if ex.dead then return end
  ex.dead = true
  say(card, "Heart Attack!", G.C and G.C.RED)
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

function DDeck.add_stress(card, amount, quiet)
  local ex = extra(card)
  if ex.dead or amount == 0 then return end
  local st = state(card)
  if amount > 0 and st and st.effect == "no_stress_xmult" then return end -- EFFECT.no_stress_xmult
  local before = ex.stress
  ex.stress = math.max(0, math.min(C.heart_attack_at, ex.stress + amount))
  local delta = ex.stress - before
  if delta ~= 0 and not quiet then
    say(card, (delta > 0 and "+" or "") .. delta .. " Stress", delta > 0 and { hex("#7B3FA0") } or { hex("#5BA3D0") })
  end
  if not st and ex.stress >= C.resolve_at then
    DDeck.resolve(card)
  elseif st and st.kind == "affliction" and ex.stress >= C.heart_attack_at then
    DDeck.heart_attack(card)
  end
end

local EFFECT = {}
DDeck.EFFECT = EFFECT
-- Afflictions
EFFECT.stress_others = function(card, s)     -- Abusive: lash out at the party
  for _, other in ipairs(heroes_in_play()) do
    if other ~= card then DDeck.add_stress(other, s.value) end
  end
end
EFFECT.disable_ability = function() end      -- Hopeless: checked in score/held/after
EFFECT.lose_money_eor = function(card, s)    -- Selfish: pockets some gold
  if ease_dollars then ease_dollars(-s.value) end
  say(card, "-$" .. s.value, G.C and G.C.MONEY)
end
-- Virtues (scoring side, in score())
EFFECT.no_stress_xmult = function() end
EFFECT.xmult = function() end

local function disabled(card)
  local st = state(card)
  return st and st.effect == "disable_ability"
end

---------------------------------------------------------------------------
-- Hero abilities: vars = how many #n# values the tooltip text can use
---------------------------------------------------------------------------
local ABILITY = {}
DDeck.ABILITY = ABILITY

ABILITY.smite = { vars = 2,
  score = function(card, key, ctx, res) res.mult_mod = DDeck.stat(key, "a") end,
  loc = function(card, key, v) v[1] = DDeck.stat(key, "a") end,
}
ABILITY.pistol_shot = { vars = 4,
  odds = function(key)
    local pct = math.max(1, DDeck.stat(key, "b"))
    return math.max(1, math.floor(100 / pct + 0.5))
  end,
  score = function(card, key, ctx, res)
    res.chip_mod = DDeck.stat(key, "a")
    local normal = (G.GAME and G.GAME.probabilities and G.GAME.probabilities.normal) or 1
    if roll("ddeck_crit") < normal / ABILITY.pistol_shot.odds(key) then
      res.Xmult_mod = 2
      res.crit = true
    end
  end,
  loc = function(card, key, v)
    v[1] = DDeck.stat(key, "a")
    v[3] = (G.GAME and G.GAME.probabilities and G.GAME.probabilities.normal) or 1
    v[4] = ABILITY.pistol_shot.odds(key)
  end,
}
ABILITY.noxious_blast = { vars = 2,
  held = function(card, key, ctx)
    local h = D.heroes[key]
    local other = ctx.other_card
    if other and other.is_suit and other:is_suit(h.suit) then
      if other.debuff then return { message = localize and localize("k_debuffed") or "Debuffed", colour = G.C.RED, card = card } end
      return { h_mult = DDeck.stat(key, "a"), card = card }
    end
  end,
  loc = function(card, key, v) v[1] = DDeck.stat(key, "a") end,
}
ABILITY.divine_grace = { vars = 3,
  score = function(card, key, ctx, res) res.chip_mod = DDeck.stat(key, "a") end,
  after = function(card, key)
    local heal = D.heroes[key].stress_heal
    for _, other in ipairs(heroes_in_play()) do
      if other ~= card then DDeck.add_stress(other, -heal) end
    end
  end,
  loc = function(card, key, v) v[1] = DDeck.stat(key, "a"); v[3] = D.heroes[key].stress_heal end,
}

function DDeck.score(card, key, ctx)
  local h = D.heroes[key]
  local ab = ABILITY[h.ability]
  local res = {}
  if not disabled(card) and ab.score then ab.score(card, key, ctx, res) end
  local st = state(card)
  if st and (st.effect == "xmult" or st.effect == "no_stress_xmult") then -- EFFECT.xmult
    res.Xmult_mod = (res.Xmult_mod or 1) * st.value
  end
  if not (res.mult_mod or res.chip_mod or res.Xmult_mod) then return nil end
  local msg, colour
  if res.Xmult_mod then
    msg = res.crit and ("Critical! X" .. res.Xmult_mod) or ("X" .. res.Xmult_mod .. " Mult")
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

function DDeck.on_hand_played(card, key)
  local h = D.heroes[key]
  local ab = ABILITY[h.ability]
  DDeck.add_stress(card, h.stress_per_hand)
  if not disabled(card) and ab.after then ab.after(card, key) end
  local st = state(card)
  if st and EFFECT[st.effect] and st.effect == "stress_others" then EFFECT[st.effect](card, st) end
end

function DDeck.on_discard(card)
  DDeck.add_stress(card, C.discard_stress)
end

function DDeck.on_round_end(card)
  local ex = extra(card)
  if ex.dead then return end
  local st = state(card)
  if st and st.effect == "lose_money_eor" then EFFECT.lose_money_eor(card, st) end
  ex.stress = math.max(0, ex.stress - C.camp_relief)
  if st and st.kind == "virtue" then
    ex.state_rounds = ex.state_rounds - 1
    if ex.state_rounds <= 0 then ex.state = nil; say(card, "Virtue fades", G.C and G.C.FILTER) end
  elseif st and st.kind == "affliction" and ex.stress < C.clear_below then
    ex.state = nil
    say(card, "Recovered", G.C and G.C.GREEN)
  else
    say(card, "Camp: -" .. C.camp_relief .. " Stress", { hex("#5BA3D0") })
  end
  DDeck.apply_sprite(card)
end

function DDeck.calculate(card, key, ctx)
  local h = D.heroes[key]
  local ab = ABILITY[h.ability]
  if ctx.joker_main then
    return DDeck.score(card, key, ctx)
  end
  if ctx.individual and ctx.cardarea == G.hand and not ctx.end_of_round and not ctx.repetition then
    if ab.held and not disabled(card) then return ab.held(card, key, ctx) end
    return nil
  end
  if ctx.blueprint then return nil end -- copies score, but only the real hero feels the Stress
  if ctx.after and ctx.cardarea == G.jokers then
    DDeck.on_hand_played(card, key)
  elseif ctx.pre_discard then
    DDeck.on_discard(card)
  elseif ctx.end_of_round and not ctx.individual and not ctx.repetition and not ctx.game_over then
    DDeck.on_round_end(card)
  end
  return nil
end

function DDeck.loc_vars(card)
  local key = card.config.center.ddeck_hero
  local h = D.heroes[key]
  local v = { 0, "", 0, 0 }
  ABILITY[h.ability].loc(card, key, v)
  local ex = extra(card)
  local st = state(card)
  if st then
    v[2] = st.text .. "  (Stress " .. ex.stress .. ")"
  else
    v[2] = "Stress " .. ex.stress .. "/" .. C.resolve_at
  end
  if disabled(card) then v[1] = 0 end
  return v
end

---------------------------------------------------------------------------
-- The look: dungeon area per Ante, its colours, its corridor art, torchlight
---------------------------------------------------------------------------
local function colour(c) return { hex(c, 1) } end

function DDeck.current_area()
  local ante = (G and G.GAME and G.GAME.round_resets and G.GAME.round_resets.ante) or 0
  for _, key in ipairs(D.areas_order) do
    local a = D.areas[key]
    if ante >= a.ante_from and ante <= a.ante_to then return a end
  end
  return D.areas[D.areas_order[1]]
end

-- All candidate corridor paths for an area, in the order they are tried.
function DDeck.backdrop_paths(area)
  local out = {}
  for n = 1, C.corridor_tiles do
    for _, tmpl in ipairs(D.companion_files.area_backdrop.paths) do
      out[#out + 1] = (tmpl:gsub("{area}", area.dd_folder):gsub("{n}", tostring(n)))
    end
  end
  return out
end

-- Loads every corridor image found for an area (once), so the backdrop can tile them.
function DDeck.load_backdrops(area)
  DDeck.backdrops = DDeck.backdrops or {}
  if DDeck.backdrops[area.key] then return DDeck.backdrops[area.key] end
  local list, seen = {}, {}
  DDeck.load_companion()
  if DDeck.dd_path then
    for _, rel in ipairs(DDeck.backdrop_paths(area)) do
      if not seen[rel] and #list < C.corridor_tiles then
        seen[rel] = true
        local img = load_image(DDeck.dd_path .. "/" .. rel)
        if img then list[#list + 1] = img end
      end
    end
  end
  log(area.name .. ": " .. #list .. " corridor image(s) found in dungeons/" .. area.dd_folder)
  DDeck.backdrops[area.key] = list
  return list
end

function DDeck.draw_backdrop()
  local area = DDeck.current_area()
  local imgs = DDeck.load_backdrops(area)
  if #imgs == 0 then return end
  local g = love.graphics
  local canvas = g.getCanvas()
  local W, H
  if canvas then W, H = canvas:getDimensions() else W, H = g.getDimensions() end
  g.push("all")
  g.origin()
  g.setShader()
  g.setColor(1, 1, 1, C.backdrop_alpha)
  -- a corridor: the area's wall images side by side, scaled to the screen's height
  local x, i = 0, 1
  while x < W do
    local img = imgs[i]
    local s = H / img:getHeight()
    g.draw(img, x, 0, 0, s, s)
    x = x + img:getWidth() * s
    i = i % #imgs + 1
  end
  g.pop()
  if not DDeck.backdrop_logged then DDeck.backdrop_logged = true; log("backdrop drawn (" .. area.name .. ")") end
end

-- Torchlight: the vignette darkens as the party's average Stress rises.
function DDeck.torch_alpha()
  local heroes = (G and G.jokers and G.STAGE == (G.STAGES and G.STAGES.RUN)) and heroes_in_play() or {}
  if #heroes == 0 then return C.torch_min end
  local total = 0
  for _, c in ipairs(heroes) do total = total + extra(c).stress end
  local t = math.min(1, (total / #heroes) / C.resolve_at)
  return C.torch_min + (C.torch_max - C.torch_min) * t
end

function DDeck.draw_torchlight()
  local g = love.graphics
  if not DDeck.vignette then
    local n = 256
    local id = love.image.newImageData(n, n)
    id:mapPixel(function(x, y)
      local dx, dy = (x - n / 2) / (n / 2), (y - n / 2) / (n / 2)
      local d = math.min(1, math.sqrt(dx * dx + dy * dy))
      return 0.03, 0.01, 0.0, d ^ 2.2
    end)
    DDeck.vignette = g.newImage(id)
  end
  local W, H = g.getDimensions()
  g.push("all")
  g.origin()
  g.setShader()
  g.setColor(1, 1, 1, DDeck.torch_alpha())
  g.draw(DDeck.vignette, 0, 0, 0, W / 256, H / 256)
  g.pop()
end

-- Replaces whatever colours Balatro asks for with the current area's.
function DDeck.area_colours(args)
  local a = DDeck.current_area()
  args = args or {}
  local out = {}
  for k, v in pairs(args) do out[k] = v end
  out.new_colour = colour(a.colour_light)
  out.special_colour = colour(a.colour_main)
  out.tertiary_colour = colour(a.colour_dark)
  out.contrast = a.contrast
  return out
end

---------------------------------------------------------------------------
-- Hooks (see design/sheets/hooks.json)
---------------------------------------------------------------------------
local function resolve_path(path)
  local obj, field = path:match("^([%w_]+)%.([%w_]+)$")
  if obj then return _G[obj], field end
  return _G, path
end

local function wrap(path, make)
  local tbl, field = resolve_path(path)
  if type(tbl) ~= "table" or type(tbl[field]) ~= "function" then
    log("could not hook " .. path .. " (not found)")
    return false
  end
  tbl[field] = make(tbl[field])
  return true
end
DDeck.wrap = wrap

function DDeck.install()
  if DDeck.installed then return end
  DDeck.installed = true
  local ok = 0

  ok = ok + (wrap("Game.init_item_prototypes", function(orig)
    return function(self, ...)
      local r = orig(self, ...)
      local s, e = pcall(DDeck.register_centers, self)
      if not s then log("register failed: " .. tostring(e)) end
      return r
    end
  end) and 1 or 0)

  ok = ok + (wrap("init_localization", function(orig)
    return function(...)
      local s, e = pcall(DDeck.inject_loc)
      if not s then log("localization failed: " .. tostring(e)) end
      return orig(...)
    end
  end) and 1 or 0)

  ok = ok + (wrap("Game.set_render_settings", function(orig)
    return function(self, ...)
      local r = orig(self, ...)
      local s, e = pcall(DDeck.build_atlas)
      if not s then log("atlas failed: " .. tostring(e)) end
      return r
    end
  end) and 1 or 0)

  ok = ok + (wrap("Card.set_sprites", function(orig)
    return function(self, _center, _front)
      local r = orig(self, _center, _front)
      if _center and _center.ddeck_hero then pcall(DDeck.apply_sprite, self) end
      return r
    end
  end) and 1 or 0)

  ok = ok + (wrap("Card.calculate_joker", function(orig)
    return function(self, context)
      local key = self.config and self.config.center and self.config.center.ddeck_hero
      if key then
        if self.debuff then return nil end
        return DDeck.calculate(self, key, context or {})
      end
      return orig(self, context)
    end
  end) and 1 or 0)

  ok = ok + (wrap("Card.generate_UIBox_ability_table", function(orig)
    return function(self, ...)
      if self.config and self.config.center and self.config.center.ddeck_hero then
        local s, v = pcall(DDeck.loc_vars, self)
        DDeck._pending_vars = s and v or nil
      end
      local r = orig(self, ...)
      DDeck._pending_vars = nil
      return r
    end
  end) and 1 or 0)

  ok = ok + (wrap("generate_card_ui", function(orig)
    return function(_c, full_UI_table, specific_vars, ...)
      if DDeck._pending_vars and _c and _c.ddeck_hero then
        specific_vars = DDeck._pending_vars
        DDeck._pending_vars = nil
      end
      return orig(_c, full_UI_table, specific_vars, ...)
    end
  end) and 1 or 0)

  ok = ok + (wrap("Back.apply_to_run", function(orig)
    return function(self, ...)
      local r = orig(self, ...)
      local c = self.effect and self.effect.center
      if c and c.ddeck_party then DDeck.give_party(c.ddeck_party) end
      return r
    end
  end) and 1 or 0)

  ok = ok + (wrap("ease_background_colour", function(orig)
    return function(args, ...)
      local s, v = pcall(DDeck.area_colours, args)
      return orig(s and v or args, ...)
    end
  end) and 1 or 0)

  ok = ok + (wrap("Sprite.draw", function(orig)
    return function(self, ...)
      local r = orig(self, ...)
      if G and self == G.SPLASH_BACK and G.STAGE == (G.STAGES and G.STAGES.RUN) then
        local s, e = pcall(DDeck.draw_backdrop)
        if not s and not DDeck.backdrop_err then DDeck.backdrop_err = true; log("backdrop failed: " .. tostring(e)) end
      end
      return r
    end
  end) and 1 or 0)

  ok = ok + (wrap("Game.draw", function(orig)
    return function(self, ...)
      local r = orig(self, ...)
      local s, e = pcall(DDeck.draw_torchlight)
      if not s and not DDeck.torch_err then DDeck.torch_err = true; log("torchlight failed: " .. tostring(e)) end
      return r
    end
  end) and 1 or 0)

  log("v" .. DDeck.version .. " installed " .. ok .. "/11 hooks")
end

return DDeck
