-- Darkest Deck: the look. Hero cards from Darkest Dungeon portraits, a different
-- dungeon backdrop for every Blind, the Hamlet behind the shop, the area's colours,
-- torchlight, HP and Stress bars under each hero, and the enemy team on screen.
-- All art is read from the player's own Darkest Dungeon install.

local DDeck = _G.DDeck
local D, C = DDeck.D, DDeck.C
local log, hex, extra, fill = DDeck.log, DDeck.hex, DDeck.extra, DDeck.fill
local guarded = DDeck.guarded

local function load_image(rel)
  DDeck.image_cache = DDeck.image_cache or {}
  if DDeck.image_cache[rel] ~= nil then return DDeck.image_cache[rel] or nil end
  local img = false
  if DDeck.dd_path then
    local data = DDeck.read_file(DDeck.dd_path .. "/" .. rel)
    if data then
      local ok, res = pcall(function()
        local fd = love.filesystem.newFileData(data, "ddeck.png")
        return love.graphics.newImage(love.image.newImageData(fd))
      end)
      if ok then img = res end
    end
  end
  DDeck.image_cache[rel] = img
  return img or nil
end
DDeck.load_image = load_image

local function in_state(name)
  return G and G.STATES and G.STATE == G.STATES[name]
end
local function in_run()
  return G and G.STAGES and G.STAGE == G.STAGES.RUN
end

---------------------------------------------------------------------------
-- Hero cards: atlas with normal / afflicted / virtuous rows
---------------------------------------------------------------------------
local PX, PY, S = 71, 95, 2
DDeck.ATLAS = "ddeck_heroes"
DDeck.ROW = { normal = 0, affliction = 1, virtue = 2 }

local function draw_fit(img, x, y, w, h, cover)
  local iw, ih = img:getDimensions()
  local s = cover and math.max(w / iw, h / ih) or math.min(w / iw, h / ih)
  love.graphics.draw(img, x + (w - iw * s) / 2, y + (h - ih * s) / 2, 0, s, s)
end

local function first_image(paths, vars)
  for _, tmpl in ipairs(paths) do
    local rel = fill(tmpl, vars)
    local img = load_image(rel)
    if img then return img, rel end
  end
end

local function find_portrait(h)
  local folder = DDeck.class_folder(h.dd_class)
  local img, rel = first_image(D.companion_files.hero_portrait.paths, { class = folder })
  if img then return img, rel end
  for _, p in ipairs(DDeck.list_dir("heroes/" .. folder, "*portrait_roster*.png", true)) do
    img = load_image(p)
    if img then return img, p end
  end
end

local function draw_card(h, x, y, kind, imgs, font, big)
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
  local px, py, pw, ph = x + 8 * S, y + 9 * S, w - 16 * S, 56 * S
  g.setColor(0, 0, 0, 1)
  g.rectangle("fill", px, py, pw, ph)
  if imgs.portrait then
    g.setScissor(px, py, pw, ph)
    g.setColor(1, 1, 1, 1)
    draw_fit(imgs.portrait, px, py, pw, ph, true)
    g.setScissor()
  else
    g.setColor(hex(h.frame_colour))
    g.setFont(big)
    g.printf(h.name:sub(1, 1), px, py + ph / 2 - big:getHeight() / 2, pw, "center")
  end
  g.setLineWidth(1.5 * S)
  g.setColor(hex(h.frame_colour))
  g.rectangle("line", px, py, pw, ph)
  if kind == "affliction" then
    g.setColor(0.7, 0.05, 0.05, 0.35); g.rectangle("fill", px, py, pw, ph)
  elseif kind == "virtue" then
    g.setColor(1, 0.85, 0.3, 0.22); g.rectangle("fill", px, py, pw, ph)
  end
  g.setFont(font)
  g.setColor(hex(h.frame_colour))
  g.printf(h.name, x + 3 * S, y + 70 * S, w - 6 * S, "center")
  local frame = kind == "affliction" and "#B3261E" or kind == "virtue" and "#E8C547" or h.frame_colour
  g.setLineWidth((kind == "normal" and 2 or 3) * S)
  g.setColor(hex(frame))
  g.rectangle("line", x + 1.5 * S, y + 1.5 * S, w - 3 * S, ht - 3 * S, r, r)
end

function DDeck.build_atlas()
  if not (love and love.graphics and G and G.ASSET_ATLAS) then return end
  DDeck.load_companion()
  local cols = 0
  for _, key in ipairs(D.heroes_order) do cols = math.max(cols, D.heroes[key].atlas_x + 1) end
  local font, big = love.graphics.newFont(7 * S), love.graphics.newFont(30 * S)
  local canvas = love.graphics.newCanvas(cols * PX * S, 3 * PY * S)
  love.graphics.push("all")
  love.graphics.setCanvas(canvas)
  love.graphics.clear(0, 0, 0, 0)
  love.graphics.origin()
  for _, key in ipairs(D.heroes_order) do
    local h = D.heroes[key]
    local imgs = DDeck.images[key]
    if not imgs then
      imgs = {}
      local p, from = find_portrait(h)
      imgs.portrait = p
      imgs.header = first_image(D.companion_files.hero_header.paths, { class = DDeck.class_folder(h.dd_class) })
      log(h.name .. ": portrait " .. (from or "not found, drawing initial"))
      DDeck.images[key] = imgs
    end
    for kind, row in pairs(DDeck.ROW) do
      draw_card(h, h.atlas_x * PX * S, row * PY * S, kind, imgs, font, big)
    end
  end
  love.graphics.pop()
  local image = love.graphics.newImage(canvas:newImageData(), { mipmaps = true, dpiscale = S })
  G.ASSET_ATLAS[DDeck.ATLAS] = { name = DDeck.ATLAS, image = image, type = "asset_atli", px = PX, py = PY }
  log("hero atlas built")
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
-- Backdrops: a different dungeon image every Blind, the Hamlet in the shop
---------------------------------------------------------------------------
-- Every image file for an area, sorted into wide rooms and square corridor walls.
function DDeck.area_images(area)
  DDeck.area_cache = DDeck.area_cache or {}
  if DDeck.area_cache[area.key] then return DDeck.area_cache[area.key] end
  local files = DDeck.list_dir("dungeons/" .. area.dd_folder, "*.png", false)
  if #files == 0 then
    -- no listing: probe numbered names
    for n = 1, C.corridor_tiles do
      for _, tmpl in ipairs(D.companion_files.area_backdrop.paths) do
        local rel = fill(tmpl, { area = area.dd_folder, n = tostring(n) })
        if DDeck.read_file((DDeck.dd_path or "") .. "/" .. rel) then files[#files + 1] = rel end
      end
    end
  end
  local out = { rooms = {}, walls = {} }
  for _, rel in ipairs(files) do
    local name = rel:lower():match("[^/]+$") or ""
    if name:find("room") then out.rooms[#out.rooms + 1] = rel
    elseif name:find("corridor") and not name:find("door") and not name:find("mid") and not name:find("fg") then
      out.walls[#out.walls + 1] = rel
    end
  end
  log(area.name .. ": " .. #out.rooms .. " room and " .. #out.walls .. " corridor image(s) in dungeons/" .. area.dd_folder
      .. (#files > 0 and (" (e.g. " .. files[1] .. ")") or ""))
  DDeck.area_cache[area.key] = out
  return out
end

-- Chosen when a Blind starts: Small/Big get corridors, the boss gets a room.
function DDeck.pick_backdrop()
  local dd = G.GAME.ddeck
  local area = D.areas[dd.area] or DDeck.current_area()
  local imgs = DDeck.area_images(area)
  local list = (dd.blind_kind == "boss" and #imgs.rooms > 0) and imgs.rooms or imgs.walls
  if #list == 0 then list = imgs.rooms end
  if #list == 0 then dd.backdrop = nil; return end
  local i = ((dd.blind_index or 1) * 7 + math.floor(DDeck.roll("ddeck_backdrop") * #list)) % #list + 1
  dd.backdrop = { list = list, start = i, wide = (list == imgs.rooms) }
end

function DDeck.hamlet_image()
  if DDeck.hamlet ~= nil then return DDeck.hamlet or nil end
  DDeck.hamlet = false
  local img, from = first_image(D.companion_files.hamlet.paths, {})
  if not img then
    -- the widest image whose name looks like a town backdrop
    local best, bw = nil, 0
    local checked = 0
    for _, rel in ipairs(DDeck.list_dir("campaign/town", "*.png", true)) do
      local name = rel:lower():match("[^/]+$") or ""
      if (name:find("bg") or name:find("background") or name:find("town") or name:find("hamlet")) and checked < 40 then
        checked = checked + 1
        local im = load_image(rel)
        if im and im:getWidth() > bw then best, bw, from = im, im:getWidth(), rel end
      end
    end
    img = best
  end
  log("Hamlet backdrop: " .. (from or "not found"))
  DDeck.hamlet = img or false
  return img
end

local function dim(W, H)
  local g = love.graphics
  g.setColor(0, 0, 0, C.backdrop_dim)
  g.rectangle("fill", 0, 0, W, H)
  g.setColor(0, 0, 0, C.backdrop_dim)
  g.rectangle("fill", 0, H * 0.6, W, H * 0.4)
end

function DDeck.draw_backdrop()
  local g = love.graphics
  local canvas = g.getCanvas()
  local W, H
  if canvas then W, H = canvas:getDimensions() else W, H = g.getDimensions() end
  g.push("all")
  g.origin()
  g.setShader()
  g.setColor(1, 1, 1, 1)
  local drew = false
  if in_state("SHOP") then
    local img = DDeck.hamlet_image()
    if img then draw_fit(img, 0, 0, W, H, true); drew = "Hamlet" end
  else
    local bd = G.GAME and G.GAME.ddeck and G.GAME.ddeck.backdrop
    if bd and #bd.list > 0 then
      if bd.wide then
        local img = load_image(bd.list[bd.start])
        if img then draw_fit(img, 0, 0, W, H, true); drew = bd.list[bd.start] end
      else
        -- a corridor: wall images side by side at full height
        local x, i, guard = 0, bd.start, 0
        while x < W and guard < 20 do
          guard = guard + 1
          local img = load_image(bd.list[i])
          if img then
            local s = H / img:getHeight()
            g.draw(img, x, 0, 0, s, s)
            x = x + img:getWidth() * s
            drew = drew or bd.list[i]
          end
          i = i % #bd.list + 1
        end
      end
    end
  end
  if drew then dim(W, H) end
  g.pop()
  if drew and DDeck.last_drawn ~= drew then DDeck.last_drawn = drew; log("backdrop: " .. drew) end
end

-- Replaces whatever colours Balatro asks for with the current area's.
function DDeck.area_colours(args)
  local a = DDeck.current_area()
  local out = {}
  for k, v in pairs(args or {}) do out[k] = v end
  out.new_colour = DDeck.colour(a.colour_light)
  out.special_colour = DDeck.colour(a.colour_main)
  out.tertiary_colour = DDeck.colour(a.colour_dark)
  out.contrast = a.contrast
  return out
end

---------------------------------------------------------------------------
-- Torchlight, hero bars, enemy banner
---------------------------------------------------------------------------
function DDeck.torch_alpha()
  local heroes = in_run() and DDeck.heroes_in_play() or {}
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

-- HP (red) and Stress (ten pips, like Darkest Dungeon) under a hero card, in Balatro's game units.
function DDeck.draw_hero_bars(card)
  if not (card.area and G.jokers and card.area == G.jokers and card.VT) then return end
  local key = DDeck.hero_key(card)
  if not key then return end
  local ex = extra(card)
  local g = love.graphics
  local unit = (G.TILESCALE or 1) * (G.TILESIZE or 1)
  local x, y, w = card.VT.x, card.VT.y + card.VT.h + 0.06, card.VT.w
  g.push("all")
  g.scale(unit)
  g.setShader()
  local frac = math.max(0, ex.hp / DDeck.max_hp(key))
  g.setColor(0.08, 0.02, 0.02, 0.9)
  g.rectangle("fill", x, y, w, 0.13)
  g.setColor(ex.hp > 0 and 0.78 or 0.35, 0.1, 0.1, 1)
  g.rectangle("fill", x, y, w * frac, 0.13)
  local pips, gap = 10, 0.03
  local pw = (w - gap * (pips - 1)) / pips
  for i = 1, pips do
    local lit = ex.stress >= i * 10
    local over = ex.stress >= 100 + i * 10
    if over then g.setColor(0.55, 0.2, 0.75, 1)
    elseif lit then g.setColor(0.92, 0.9, 0.85, 1)
    else g.setColor(0.15, 0.13, 0.12, 0.9) end
    g.rectangle("fill", x + (i - 1) * (pw + gap), y + 0.18, pw, 0.09)
  end
  g.pop()
end

function DDeck.draw_enemy_banner()
  if not (in_run() and in_state("SELECTING_HAND")) then return end
  local enemies = DDeck.enemies()
  if #enemies == 0 then return end
  local g = love.graphics
  local W, H = g.getDimensions()
  local size = math.max(10, math.floor(H / 48))
  DDeck.banner_fonts = DDeck.banner_fonts or {}
  local font = DDeck.banner_fonts[size] or g.newFont(size)
  DDeck.banner_fonts[size] = font
  local area = D.areas[(G.GAME.ddeck and G.GAME.ddeck.area) or ""] or DDeck.current_area()
  local lh = size * 1.6
  local bw = W * 0.34
  local bx, by = W * 0.36, H * 0.42
  local bh = lh * (#enemies + 1) + size * 0.6
  g.push("all")
  g.origin()
  g.setShader()
  g.setFont(font)
  g.setColor(0.05, 0.03, 0.03, 0.78)
  g.rectangle("fill", bx, by, bw, bh, 6, 6)
  g.setColor(hex("#8B1A1A"))
  g.setLineWidth(2)
  g.rectangle("line", bx, by, bw, bh, 6, 6)
  g.setColor(hex("#C9A227"))
  g.print(area.name, bx + size * 0.6, by + size * 0.3)
  local prev = 0
  local blind = G.GAME.blind
  local frac = (blind and blind.chips and blind.chips > 0) and (G.GAME.chips or 0) / blind.chips or 0
  for i, e in ipairs(enemies) do
    local y = by + lh * i + size * 0.2
    local share = e.dies_at - prev
    local left = e.alive and math.max(0, math.min(1, (e.dies_at - frac) / share)) or 0
    prev = e.dies_at
    g.setColor(e.alive and (e.boss and { hex("#E8C547") } or { 0.9, 0.86, 0.8, 1 }) or { 0.4, 0.38, 0.36, 1 })
    g.print((e.alive and "" or "x ") .. e.name, bx + size * 0.6, y)
    local hx0, hw = bx + bw * 0.52, bw * 0.24
    g.setColor(0.15, 0.03, 0.03, 1)
    g.rectangle("fill", hx0, y + size * 0.25, hw, size * 0.55)
    g.setColor(0.75, 0.1, 0.1, 1)
    g.rectangle("fill", hx0, y + size * 0.25, hw * left, size * 0.55)
    if e.alive then
      g.setColor(0.85, 0.82, 0.78, 1)
      g.print(e.dmg_min .. "-" .. e.dmg_max .. "  " .. e.stress .. "s", hx0 + hw + size * 0.5, y)
    end
  end
  g.pop()
end

function DDeck.install_look()
  local wrap = DDeck.wrap

  wrap("Game.set_render_settings", function(orig)
    return function(self, ...)
      local r = orig(self, ...)
      guarded("atlas", DDeck.build_atlas)
      return r
    end
  end)

  wrap("Card.set_sprites", function(orig)
    return function(self, _center, _front)
      local r = orig(self, _center, _front)
      if _center and _center.ddeck_hero then pcall(DDeck.apply_sprite, self) end
      return r
    end
  end)

  wrap("ease_background_colour", function(orig)
    return function(args, ...)
      local s, v = pcall(DDeck.area_colours, args)
      return orig(s and v or args, ...)
    end
  end)

  wrap("Sprite.draw", function(orig)
    return function(self, ...)
      local r = orig(self, ...)
      if G and self == G.SPLASH_BACK and in_run() then guarded("backdrop", DDeck.draw_backdrop) end
      return r
    end
  end)

  wrap("Card.draw", function(orig)
    return function(self, layer, ...)
      local r = orig(self, layer, ...)
      if (layer == nil or layer == "card" or layer == "both") and DDeck.hero_key(self) then
        guarded("hero_bars", DDeck.draw_hero_bars, self)
      end
      return r
    end
  end)

  wrap("Game.draw", function(orig)
    return function(self, ...)
      local r = orig(self, ...)
      guarded("enemy_banner", DDeck.draw_enemy_banner)
      guarded("torchlight", DDeck.draw_torchlight)
      return r
    end
  end)
end

return DDeck
