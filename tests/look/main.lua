-- Renders a battle frame and a shop frame in real LÖVE 11.5 with the mod's own
-- drawing code: per-blind backdrop, Hamlet, hero cards with HP/Stress bars,
-- enemy banner and torchlight. All art here is synthetic stand-ins we generate.
--   xvfb-run love tests/look <repo root>
local function put(path, data) local f = assert(io.open(path, "wb")); f:write(data); f:close() end
local function stone(w, h, tint, arch)
  local id = love.image.newImageData(w, h)
  id:mapPixel(function(x, y)
    local row = math.floor(y / 60); local off = (row % 2) * 45
    local mortar = (y % 60 < 4) or ((x + off) % 90 < 4)
    local v = mortar and 0.08 or (0.3 + 0.05 * math.sin(x * 0.05) + 0.04 * math.cos(y * 0.07))
    if arch and ((x - w / 2) ^ 2 / (w * 0.28) ^ 2 + (y - h * 0.75) ^ 2 / (h * 0.5) ^ 2) < 1 then v = v * 0.25 end
    return v * tint[1], v * tint[2], v * tint[3], 1
  end)
  return id:encode("png"):getString()
end
function love.load(args)
  local root = args[1]
  for _, m in ipairs({ "data", "core", "battle", "look" }) do
    package.preload["ddeck." .. m] = function() return dofile(root .. "/mod/DarkestDeck/ddeck/" .. m .. ".lua") end
  end
  local fx = os.getenv("HOME") .. "/ddeck_look_fixture2"
  os.execute('rm -rf "' .. fx .. '"; mkdir -p "' .. fx .. '/heroes/crusader" "' .. fx .. '/dungeons/crypts" "' .. fx .. '/campaign/town"')
  put(fx .. "/heroes/crusader/crusader.info.darkest", "weapon: .dmg 6 12\narmour: .hp 33\n")
  put(fx .. "/dungeons/crypts/crypts.corridor_wall.1.png", stone(720, 720, { 1, 0.95, 0.9 }, true))
  put(fx .. "/dungeons/crypts/crypts.corridor_wall.2.png", stone(720, 720, { 0.9, 0.95, 1 }, false))
  put(fx .. "/campaign/town/town_bg.png", stone(1920, 720, { 1.2, 0.9, 0.6 }, false))
  function pseudorandom() return 0.3 end
  G = { ASSET_ATLAS = {}, GAME = { round_resets = { ante = 1 }, chips = 120, blind = { chips = 300 } },
        STATES = { SELECTING_HAND = 1, SHOP = 5 }, STAGES = { RUN = 2 }, STAGE = 2, STATE = 1,
        TILESCALE = 1, TILESIZE = 60, C = {} }
  local DD = require("ddeck.core")
  require("ddeck.battle"); require("ddeck.look")
  DD.load_companion(true, { fx })
  DD.build_atlas()
  G.GAME.ddeck = { area = "ruins", blind_kind = "big", blind_index = 2,
    enemies = { { name = "Bone Soldier", alive = false, dies_at = 0.3, dmg_min = 3, dmg_max = 8, stress = 2 },
                { name = "Bone Arbalist", alive = true, dies_at = 0.65, dmg_min = 4, dmg_max = 9, stress = 2 },
                { name = "Madman", alive = true, dies_at = 1, dmg_min = 1, dmg_max = 3, stress = 8 } } }
  DD.pick_backdrop()
  local A = G.ASSET_ATLAS[DD.ATLAS]
  local keys = { "j_ddeck_crusader", "j_ddeck_highwayman", "j_ddeck_plague_doctor", "j_ddeck_vestal" }
  local cards = {}
  G.jokers = { cards = cards }
  for i, k in ipairs(keys) do
    cards[i] = { config = { center = { ddeck_hero = k, pos = { x = DD.D.heroes[k].atlas_x } } },
      ability = { extra = { stress = ({ 20, 60, 110, 5 })[i], hp = ({ 33, 9, 0, 20 })[i],
                            state = i == 3 and "abusive" or nil } },
      area = G.jokers, VT = { x = 4 + i * 2.6, y = 0.6, w = 2.37, h = 3.17 } }
  end
  local W, H = 960, 540
  for _, frame in ipairs({ "battle", "shop" }) do
    G.STATE = frame == "shop" and 5 or 1
    local c = love.graphics.newCanvas(W, H)
    love.graphics.setCanvas(c); love.graphics.clear(0.1, 0.1, 0.12, 1)
    DD.draw_backdrop()
    for i, card in ipairs(cards) do
      local row = DD.ROW[DD.state_kind(card)]
      local q = love.graphics.newQuad(card.config.center.pos.x * 71, row * 95, 71, 95, A.image:getDimensions())
      love.graphics.setColor(1, 1, 1, 1)
      love.graphics.draw(A.image, q, card.VT.x * 60, card.VT.y * 60, 0, card.VT.w * 60 / 71, card.VT.h * 60 / 95)
      DD.draw_hero_bars(card)
    end
    love.graphics.setCanvas()
    local out = love.graphics.newCanvas(W, H)
    love.graphics.setCanvas(out); love.graphics.setColor(1, 1, 1, 1); love.graphics.draw(c)
    DD.draw_enemy_banner()
    DD.draw_torchlight()
    love.graphics.setColor(1, 1, 1, 1)
    love.graphics.print(frame .. " frame - test render, synthetic stand-in art", 10, H - 20)
    love.graphics.setCanvas()
    out:newImageData():encode("png", frame .. ".png")
    print("wrote", love.filesystem.getSaveDirectory() .. "/" .. frame .. ".png")
  end
  love.event.quit(0)
end
function love.errorhandler(msg)
  print("ERROR: " .. tostring(msg) .. "\n" .. debug.traceback()); io.stdout:flush()
  love.event.quit(1); return nil
end
