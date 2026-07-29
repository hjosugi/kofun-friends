local game = {}
local images = {}
local font
local title_font

local function resetGame()
    game.player = { x = 135, y = 220, vy = 0, size = 62 }
    game.obstacles = {}
    game.spawnTimer = 0
    game.score = 0
    game.alive = true
    game.started = false
end

local function flap()
    if not game.alive then
        resetGame()
    end
    game.started = true
    game.player.vy = -345
end

local function overlaps(a, b)
    return a.x < b.x + b.w and b.x < a.x + a.w
        and a.y < b.y + b.h and b.y < a.y + a.h
end

function love.load()
    love.graphics.setDefaultFilter("nearest", "nearest")
    images.background = love.graphics.newImage("assets/background.png")
    images.kofun = love.graphics.newImage("assets/kofun.png")
    images.dochicken = love.graphics.newImage("assets/dochicken.png")
    font = love.graphics.newFont(22)
    title_font = love.graphics.newFont(38)
    resetGame()
end

function love.resize()
    -- The virtual canvas is scaled in love.draw.
end

function love.keypressed(key)
    if key == "space" or key == "up" or key == "w" then
        flap()
    elseif key == "return" and not game.alive then
        resetGame()
    end
end

function love.mousepressed(_, _, button)
    if button == 1 then
        flap()
    end
end

function love.touchpressed()
    flap()
end

function love.update(dt)
    if not game.alive or not game.started then
        return
    end

    game.player.vy = game.player.vy + 920 * dt
    game.player.y = game.player.y + game.player.vy * dt
    game.spawnTimer = game.spawnTimer - dt

    if game.spawnTimer <= 0 then
        local gapY = love.math.random(155, 385)
        table.insert(game.obstacles, {
            x = 1000,
            gapY = gapY,
            gap = 178,
            width = 76,
            counted = false,
        })
        game.spawnTimer = math.max(0.9, 1.5 - game.score * 0.018)
    end

    local playerBox = {
        x = game.player.x + 8,
        y = game.player.y + 8,
        w = game.player.size - 16,
        h = game.player.size - 16,
    }

    for index = #game.obstacles, 1, -1 do
        local obstacle = game.obstacles[index]
        obstacle.x = obstacle.x - (235 + game.score * 2.5) * dt
        local top = { x = obstacle.x, y = 0, w = obstacle.width,
            h = obstacle.gapY - obstacle.gap / 2 }
        local bottomY = obstacle.gapY + obstacle.gap / 2
        local bottom = { x = obstacle.x, y = bottomY, w = obstacle.width,
            h = 540 - bottomY }
        if overlaps(playerBox, top) or overlaps(playerBox, bottom) then
            game.alive = false
        end
        if not obstacle.counted and obstacle.x + obstacle.width < game.player.x then
            obstacle.counted = true
            game.score = game.score + 1
        end
        if obstacle.x < -obstacle.width then
            table.remove(game.obstacles, index)
        end
    end

    if game.player.y < -8 or game.player.y + game.player.size > 540 then
        game.alive = false
    end
end

local function drawGame()
    local bg = images.background
    love.graphics.setColor(0.58, 0.58, 0.68)
    love.graphics.draw(bg, 0, 0, 0, 960 / bg:getWidth(), 540 / bg:getHeight())

    for _, obstacle in ipairs(game.obstacles) do
        love.graphics.setColor(0.17, 0.08, 0.28, 0.98)
        love.graphics.rectangle("fill", obstacle.x, 0, obstacle.width,
            obstacle.gapY - obstacle.gap / 2, 9, 9)
        local bottomY = obstacle.gapY + obstacle.gap / 2
        love.graphics.rectangle("fill", obstacle.x, bottomY, obstacle.width,
            540 - bottomY, 9, 9)
        love.graphics.setColor(1, 0.45, 0.66)
        love.graphics.rectangle("line", obstacle.x, 0, obstacle.width,
            obstacle.gapY - obstacle.gap / 2, 9, 9)
        love.graphics.rectangle("line", obstacle.x, bottomY, obstacle.width,
            540 - bottomY, 9, 9)
        love.graphics.setColor(1, 1, 1)
        local image = images.dochicken
        love.graphics.draw(image, obstacle.x + obstacle.width / 2,
            obstacle.gapY, 0, 0.42, 0.42, image:getWidth() / 2,
            image:getHeight() / 2)
    end

    love.graphics.setColor(1, 1, 1)
    love.graphics.draw(images.kofun, game.player.x, game.player.y, 0,
        game.player.size / images.kofun:getWidth(),
        game.player.size / images.kofun:getHeight())

    love.graphics.setColor(0.04, 0.02, 0.09, 0.88)
    love.graphics.rectangle("fill", 0, 0, 960, 56)
    love.graphics.setFont(font)
    love.graphics.setColor(1, 1, 1)
    love.graphics.print(string.format("DOCHICKEN SKY DODGE     SCORE %03d", game.score),
        22, 16)

    if not game.started or not game.alive then
        love.graphics.setColor(0.03, 0.015, 0.08, 0.8)
        love.graphics.rectangle("fill", 110, 176, 740, 188, 18, 18)
        love.graphics.setFont(title_font)
        love.graphics.setColor(1, 0.92, 0.55)
        local message = game.alive and "READY TO FLY?" or "FLIGHT OVER!"
        love.graphics.printf(message, 110, 205, 740, "center")
        love.graphics.setFont(font)
        love.graphics.setColor(1, 1, 1)
        local help = game.alive and "Space / Up / Click to flap"
            or "Space, Click, or Enter to retry"
        love.graphics.printf(help, 110, 276, 740, "center")
    end
end

function love.draw()
    local width, height = love.graphics.getDimensions()
    local scale = math.min(width / 960, height / 540)
    local offsetX = (width - 960 * scale) / 2
    local offsetY = (height - 540 * scale) / 2
    love.graphics.push()
    love.graphics.translate(offsetX, offsetY)
    love.graphics.scale(scale, scale)
    drawGame()
    love.graphics.pop()
end
