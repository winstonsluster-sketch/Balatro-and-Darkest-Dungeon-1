-- Renders the v0.2 look in real LÖVE 11.5: area background colour, corridor
-- backdrop (synthetic stand-in images we generate here, not game files), hero
-- cards from the atlas, and torchlight at a given party stress.
--   xvfb-run love tests/look <repo root> <ante> <stress>
local function put(path, data) local f = assert(io.open(path, "wb")); f:write(data); f:close() end
function love.load(args)
  local root, ante, stress = args[1], tonumber(args[2] or 1), tonumber(args[3] or 0)
  package.preload["ddeck.data"] = function() return dofile(root .. "/mod/DarkestDeck/ddeck/data.lua") end
  package.preload["ddeck.core"] = function() return dofile(root .. "/mod/DarkestDeck/ddeck/core.lua") end
  local fx = os.getenv("HOME") .. "/ddeck_look_fixture"
  G = { ASSET_ATLAS = {}, GAME = { round_resets = { ante = ante } }, STAGES = { RUN = 2 }, STAGE = 2 }
  local DD = require("ddeck.core")
  local area = DD.current_area()
  -- synthetic "corridor" stand-ins: stone-block pattern, 720x720
  os.execute('mkdir -p "' .. fx .. '/dungeons/' .. area.dd_folder .. '" "' .. fx .. '/heroes/crusader"')
  put(fx .. "/heroes/crusader/crusader.info.darkest", "weapon: .dmg 6 12\n")
  for n = 1, 2 do
    local id = love.image.newImageData(720, 720)
    id:mapPixel(function(x, y)
      local row = math.floor(y / 60); local off = (row % 2) * 45
      local mortar = (y % 60 < 4) or ((x + off) % 90 < 4)
      local v = mortar and 0.08 or (0.28 + 0.05 * math.sin(x * 0.05 + n) + 0.04 * math.cos(y * 0.07))
      local arch = ((x - 360) ^ 2 / 200 ^ 2 + (y - 520) ^ 2 / 330 ^ 2) < 1
      if arch then v = v * 0.25 end
      return v, v * 0.92, v * 0.85, 1
    end)
    put(fx .. "/dungeons/" .. area.dd_folder .. "/" .. area.dd_folder .. ".corridor_wall." .. n .. ".png", id:encode("png"):getString())
  end
  DD.load_companion(true, { fx })
  DD.build_atlas()
  local W, H = 960, 540
  local c = love.graphics.newCanvas(W, H)
  love.graphics.setCanvas(c)
  -- stand-in for Balatro's swirling background: a vertical blend of the area's colours
  local function hx(s) return tonumber(s:sub(2,3),16)/255, tonumber(s:sub(4,5),16)/255, tonumber(s:sub(6,7),16)/255 end
  local r1,g1,b1 = hx(area.colour_light); local r2,g2,b2 = hx(area.colour_dark)
  for y = 0, H - 1 do local t = y / H
    love.graphics.setColor(r1*(1-t)+r2*t, g1*(1-t)+g2*t, b1*(1-t)+b2*t, 1); love.graphics.rectangle("fill", 0, y, W, 1) end
  DD.draw_backdrop()
  -- four hero cards on the "table"
  local A = G.ASSET_ATLAS[DD.ATLAS]
  love.graphics.setColor(1, 1, 1, 1)
  for i = 0, 3 do
    local row = (i == 2 and stress >= 100) and 1 or 0
    local q = love.graphics.newQuad(i * 71, row * 95, 71, 95, A.image:getDimensions())
    love.graphics.draw(A.image, q, 250 + i * 120, 60, 0, 1.4, 1.4)
  end
  love.graphics.setCanvas()
  -- torchlight over the whole frame, like Game.draw's wrapper
  local frame = love.graphics.newCanvas(W, H)
  love.graphics.setCanvas(frame); love.graphics.setColor(1,1,1,1); love.graphics.draw(c)
  DD.load_companion(false)
  local hero = { config = { center = { ddeck_hero = "j_ddeck_crusader" } }, ability = { extra = { stress = stress } } }
  G.jokers = { cards = { hero } }
  DD.draw_torchlight()
  love.graphics.setColor(1,1,1,1); love.graphics.print(area.name .. "  (ante " .. ante .. ", stress " .. stress .. ")  - test render, stand-in art", 10, H - 20)
  love.graphics.setCanvas()
  frame:newImageData():encode("png", "look_" .. area.key .. ".png")
  print("wrote", love.filesystem.getSaveDirectory() .. "/look_" .. area.key .. ".png", "alpha", DD.torch_alpha())
  love.event.quit(0)
end
function love.errorhandler(msg)
  print("ERROR: " .. tostring(msg) .. "\n" .. debug.traceback()); io.stdout:flush()
  love.event.quit(1); return nil
end
