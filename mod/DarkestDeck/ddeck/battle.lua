-- Darkest Deck: Blinds are fights. Each Blind is a team of Darkest Dungeon monsters
-- from the current area; your score cuts them down one by one, and after every hand
-- the survivors attack (HP) and wear on the party (Stress). Bosses come after a camp.

local DDeck = _G.DDeck
local D, C = DDeck.D, DDeck.C
local log, say, extra, roll = DDeck.log, DDeck.say, DDeck.extra, DDeck.roll
local guarded = DDeck.guarded

function DDeck.current_area()
  local ante = (G and G.GAME and G.GAME.round_resets and G.GAME.round_resets.ante) or 0
  for _, key in ipairs(D.areas_order) do
    local a = D.areas[key]
    if ante >= a.ante_from and ante <= a.ante_to then return a end
  end
  return D.areas[D.areas_order[#D.areas_order]]
end

local function area_monsters(area_key, bosses)
  local list = {}
  for _, key in ipairs(D.monsters_order) do
    local m = D.monsters[key]
    if m.area == area_key and ((m.boss_blind ~= "-") == bosses) then list[#list + 1] = m end
  end
  return list
end
DDeck.area_monsters = area_monsters

local function pick(list, seed)
  return list[math.floor(roll(seed) * #list) + 1] or list[1]
end

function DDeck.boss_for_blind(blind_key)
  for _, key in ipairs(D.monsters_order) do
    local m = D.monsters[key]
    if m.boss_blind == blind_key then return m end
  end
end

local function enemy(m)
  local s = DDeck.monster_stats(m.key)
  return { key = m.key, name = m.name, kind = m.kind, hp = s.hp, dmg_min = s.dmg_min, dmg_max = s.dmg_max,
           stress = m.stress, alive = true, boss = m.boss_blind ~= "-" }
end

-- A new team of monsters for the Blind about to be fought.
function DDeck.new_encounter(blind_key, is_boss)
  G.GAME.ddeck = G.GAME.ddeck or {}
  local dd = G.GAME.ddeck
  local area = DDeck.current_area()
  local team = {}
  local regular = area_monsters(area.key, false)
  if is_boss then
    local b = DDeck.boss_for_blind(blind_key) or pick(area_monsters(area.key, true), "ddeck_boss")
    for _ = 1, C.boss_minions do team[#team + 1] = enemy(pick(regular, "ddeck_minion")) end
    team[#team + 1] = enemy(b)
  else
    local n = blind_key == "bl_small" and C.small_enemies or C.big_enemies
    for _ = 1, n do team[#team + 1] = enemy(pick(regular, "ddeck_team")) end
  end
  local total = 0
  for _, e in ipairs(team) do total = total + e.hp end
  local acc = 0
  for _, e in ipairs(team) do
    acc = acc + e.hp
    e.dies_at = acc / total   -- fraction of the Blind's score at which this one falls
  end
  dd.enemies = team
  dd.area = area.key
  dd.hands_this_blind = 0
  dd.blind_kind = is_boss and "boss" or (blind_key == "bl_small" and "small" or "big")
  dd.blind_index = (dd.blind_index or 0) + 1
  local names = {}
  for _, e in ipairs(team) do names[#names + 1] = e.name end
  log("encounter in " .. area.name .. ": " .. table.concat(names, ", "))
  if DDeck.pick_backdrop then guarded("pick_backdrop", DDeck.pick_backdrop) end
  return team
end

function DDeck.enemies()
  return (G and G.GAME and G.GAME.ddeck and G.GAME.ddeck.enemies) or {}
end

function DDeck.enemy_alive_of_kind(kind)
  for _, e in ipairs(DDeck.enemies()) do
    if e.alive and e.kind == kind then return true end
  end
  return false
end

function DDeck.living_enemies()
  local list = {}
  for _, e in ipairs(DDeck.enemies()) do if e.alive then list[#list + 1] = e end end
  return list
end

-- Score so far cuts the team down, front to back.
function DDeck.check_kills()
  local blind = G.GAME and G.GAME.blind
  if not (blind and blind.chips and blind.chips > 0) then return {} end
  local frac = (G.GAME.chips or 0) / blind.chips
  local slain = {}
  for _, e in ipairs(DDeck.enemies()) do
    if e.alive and frac >= e.dies_at - 1e-9 then
      e.alive = false
      slain[#slain + 1] = e
      DDeck.announce(e.name .. " slain!", G.C and G.C.RED)
      for _, h in ipairs(DDeck.heroes_in_play()) do
        local ab = DDeck.ABILITY[D.heroes[DDeck.hero_key(h)].ability]
        if ab.on_kill and not DDeck.disabled(h) then ab.on_kill(h, DDeck.hero_key(h)) end
      end
    end
  end
  return slain
end

-- Who an enemy hits: the Man-at-Arms guards; otherwise the front ranks get hit most.
function DDeck.pick_target()
  local heroes = DDeck.heroes_in_play()
  if #heroes == 0 then return nil end
  for _, h in ipairs(heroes) do
    if D.heroes[DDeck.hero_key(h)].ability == "guard" and not DDeck.disabled(h)
        and roll("ddeck_guard") * 100 < C.guard_chance then
      return h
    end
  end
  local weights = { C.rank_w1, C.rank_w2, C.rank_w3, C.rank_w4 }
  local total = 0
  for i = 1, #heroes do total = total + weights[math.min(i, 4)] end
  local r = roll("ddeck_target") * total
  for i, h in ipairs(heroes) do
    r = r - weights[math.min(i, 4)]
    if r <= 0 then return h end
  end
  return heroes[#heroes]
end

function DDeck.enemy_attack(e)
  local target = DDeck.pick_target()
  if not target then return end
  local key = DDeck.hero_key(target)
  local ab = DDeck.ABILITY[D.heroes[key].ability]
  local dodge = DDeck.dodge(key) * C.dodge_scale * (ab.dodge_mult or 1)
  if roll("ddeck_dodge") * 100 < dodge then
    say(target, "Dodged " .. e.name, G.C and G.C.GREEN)
    return
  end
  local ante = (G.GAME.round_resets and G.GAME.round_resets.ante) or 1
  local base = e.dmg_min + math.floor(roll("ddeck_dmg") * (e.dmg_max - e.dmg_min + 1))
  local dmg = math.max(1, math.floor(base * (1 + C.enemy_dmg_per_ante * math.max(0, ante - 1)) + 0.5))
  DDeck.hurt(target, dmg, e.name)
end

-- Runs once after each hand is scored, before Balatro decides what happens next.
function DDeck.enemy_phase()
  local dd = G.GAME and G.GAME.ddeck
  if not (dd and dd.enemies and G.GAME.blind and G.GAME.blind.chips and G.GAME.blind.chips > 0) then return end
  DDeck.check_kills()
  local won = G.GAME.chips >= G.GAME.blind.chips
  for _, h in ipairs(DDeck.heroes_in_play()) do DDeck.hero_after_hand(h) end
  dd.hands_this_blind = (dd.hands_this_blind or 0) + 1
  if won then
    for _, e in ipairs(dd.enemies) do e.alive = false end
    return
  end
  local living = DDeck.living_enemies()
  for _, e in ipairs(living) do DDeck.enemy_attack(e) end
  -- every hand spent in the fight wears on everyone still standing
  local bolster = 0
  for _, h in ipairs(DDeck.heroes_in_play()) do
    if D.heroes[DDeck.hero_key(h)].ability == "guard" and not DDeck.disabled(h) then
      bolster = math.max(bolster, DDeck.stat(DDeck.hero_key(h), "b"))
    end
  end
  local stress = 0
  for _, e in ipairs(living) do stress = stress + math.max(0, e.stress - bolster) end
  if stress > 0 then
    for _, h in ipairs(DDeck.heroes_in_play()) do DDeck.add_stress(h, stress) end
  end
  if #DDeck.heroes_in_play() == 0 and #(G.jokers and G.jokers.cards or {}) > 0 then
    DDeck.announce("The party has fallen", G.C and G.C.RED)
  end
  if #DDeck.heroes_in_play() == 0 then
    G.GAME.current_round.hands_left = 0
  end
end

---------------------------------------------------------------------------
-- Camp: only right before a Boss Blind
---------------------------------------------------------------------------
local CAMP = {}
DDeck.CAMP = CAMP
CAMP.stress_party = function(user, v)
  for _, h in ipairs(DDeck.heroes_in_play()) do DDeck.add_stress(h, -v) end
end
CAMP.stress_others = function(user, v)
  for _, h in ipairs(DDeck.heroes_in_play()) do if h ~= user then DDeck.add_stress(h, -v) end end
end
CAMP.stress_self = function(user, v) if user then DDeck.add_stress(user, -v) end end
CAMP.heal_party_pct = function(user, v)
  for _, h in ipairs(DDeck.heroes_in_play()) do
    DDeck.heal(h, math.max(1, math.floor(DDeck.max_hp(DDeck.hero_key(h)) * v / 100 + 0.5)))
  end
end
CAMP.cure_self = function(user) if user then extra(user).state = nil end end
CAMP.boss_hands = function(user, v)
  local cr = G.GAME.current_round
  if cr then cr.hands_left = (cr.hands_left or 0) + v end
end
CAMP.boss_weaken = function(user, v)
  local b = G.GAME.blind
  if b and b.chips then
    b.chips = math.floor(b.chips * (1 - v / 100))
    if number_format then b.chip_text = number_format(b.chips) end
  end
end
CAMP.money = function(user, v) if ease_dollars then ease_dollars(v) end end

-- Chooses camping skills by priority within the respite budget.
function DDeck.plan_camp()
  local heroes = DDeck.heroes_in_play()
  local options = {}
  for _, h in ipairs(heroes) do
    local cls = D.heroes[DDeck.hero_key(h)].dd_class
    for _, key in ipairs(D.camping_order) do
      local s = D.camping[key]
      if s.hero == cls then options[#options + 1] = { skill = s, user = h } end
    end
  end
  for _, key in ipairs(D.camping_order) do
    local s = D.camping[key]
    if s.hero == "any" then options[#options + 1] = { skill = s, user = nil } end
  end
  table.sort(options, function(a, b)
    if a.skill.priority ~= b.skill.priority then return a.skill.priority > b.skill.priority end
    return a.skill.cost < b.skill.cost
  end)
  local left, plan = C.respite, {}
  for _, o in ipairs(options) do
    if o.skill.cost <= left then plan[#plan + 1] = o; left = left - o.skill.cost end
  end
  return plan
end

function DDeck.run_camp()
  local dd = G.GAME.ddeck
  local ante = (G.GAME.round_resets and G.GAME.round_resets.ante) or 0
  dd.camped = dd.camped or {}
  if dd.camped[tostring(ante)] then return end
  dd.camped[tostring(ante)] = true
  DDeck.announce("You make camp before the boss", G.C and G.C.ORANGE)
  for _, o in ipairs(DDeck.plan_camp()) do
    local who = o.user and D.heroes[DDeck.hero_key(o.user)].name or "The party"
    log("camp: " .. who .. " uses " .. o.skill.name .. " (" .. o.skill.text .. ")")
    if o.user then say(o.user, o.skill.name, G.C and G.C.ORANGE) end
    CAMP[o.skill.effect](o.user, o.skill.value)
  end
  for _, h in ipairs(DDeck.heroes_in_play()) do
    local ex = extra(h)
    local st = DDeck.state(h)
    if st and st.kind == "virtue" then ex.state = nil end
    if st and st.kind == "affliction" and ex.stress < C.clear_below then
      ex.state = nil
      say(h, "Recovered", G.C and G.C.GREEN)
    end
    if DDeck.apply_sprite then DDeck.apply_sprite(h) end
  end
end

function DDeck.boss_for_ante()
  local area = DDeck.current_area()
  local b = pick(area_monsters(area.key, true), "ddeck_boss")
  return b and b.boss_blind
end

function DDeck.install_battle()
  local wrap = DDeck.wrap

  wrap("get_new_boss", function(orig)
    return function(...)
      local ok, key = pcall(DDeck.boss_for_ante)
      if ok and key and G.P_BLINDS and G.P_BLINDS[key] then return key end
      return orig(...)
    end
  end)

  wrap("Blind.set_blind", function(orig)
    return function(self, blind, reset, silent)
      local r = orig(self, blind, reset, silent)
      if blind and not reset then
        guarded("encounter", function()
          local key = blind.key or (self.config and self.config.blind and self.config.blind.key)
          DDeck.new_encounter(key, self.boss)
          if not self.boss then
            local names = {}
            for _, e in ipairs(DDeck.enemies()) do names[#names + 1] = e.name end
            self.loc_name = table.concat(names, ", ")
          else
            DDeck.run_camp()
          end
        end)
      end
      return r
    end
  end)

  wrap("Game.update_hand_played", function(orig)
    return function(self, dt)
      if not G.STATE_COMPLETE then
        G.E_MANAGER:add_event(Event({ trigger = "immediate", func = function()
          guarded("enemy_phase", DDeck.enemy_phase)
          return true
        end }))
      end
      return orig(self, dt)
    end
  end)
end

return DDeck
