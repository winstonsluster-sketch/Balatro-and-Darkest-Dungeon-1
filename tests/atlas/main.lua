-- Renders the hero atlas in real LÖVE 11.5 (Balatro's engine) from the fixture
-- install, then writes it to <save dir>/atlas.png. Run from the repo root:
--   xvfb-run love tests/atlas <repo root>
local root
function love.load(args)
  root = args[1]
  package.preload["ddeck.data"] = function() return dofile(root .. "/mod/DarkestDeck/ddeck/data.lua") end
  package.preload["ddeck.core"] = function() return dofile(root .. "/mod/DarkestDeck/ddeck/core.lua") end
  local fx = root .. "/tests/fixtures/dd"
  -- a synthetic portrait (our own pixels) for the crusader only, to test both paths
  os.execute('mkdir -p "' .. fx .. '/heroes/crusader/crusader_A"')
  local id = love.image.newImageData(64, 64)
  id:mapPixel(function(x, y) local d = ((x-32)^2 + (y-28)^2) < 300 and 1 or 0
    return 0.2 + 0.6*d, 0.25 + 0.4*d, 0.4 + 0.2*d, 1 end)
  local f = io.open(fx .. "/heroes/crusader/crusader_A/crusader_portrait_roster.png", "wb")
  f:write(id:encode("png"):getString()); f:close()
  G = { ASSET_ATLAS = {} }
  local DD = require("ddeck.core")
  DD.load_companion(true, { fx })
  DD.build_atlas()
  local A = G.ASSET_ATLAS[DD.ATLAS]
  assert(A and A.image, "atlas not built")
  local w, h = A.image:getDimensions()
  print("atlas logical size", w, h, "px/py", A.px, A.py)
  assert(w == 4 * 71 and h == 3 * 95, "unexpected atlas size")
  -- the quad Balatro's Sprite would make for Plague Doctor, afflicted row
  local q = love.graphics.newQuad(2 * A.px, 1 * A.py, A.px, A.py, A.image:getDimensions())
  assert(q)
  -- write the atlas out at full resolution
  local c = love.graphics.newCanvas(w * 2, h * 2)
  love.graphics.setCanvas(c); love.graphics.clear(0.2, 0.2, 0.25, 1)
  love.graphics.draw(A.image, 0, 0, 0, 2, 2); love.graphics.setCanvas()
  c:newImageData():encode("png", "atlas.png")
  print("wrote", love.filesystem.getSaveDirectory() .. "/atlas.png")
  love.event.quit(0)
end
