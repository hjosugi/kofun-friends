package main

import (
	"bytes"
	"embed"
	"fmt"
	"image/color"
	"image/png"
	"log"
	"math/rand"

	"github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/ebitenutil"
	"github.com/hajimehoshi/ebiten/v2/inpututil"
	"github.com/hajimehoshi/ebiten/v2/vector"
)

const (
	screenWidth  = 800
	screenHeight = 600
	cellSize     = 28
	gridWidth    = 25
	gridHeight   = 16
	gridLeft     = 50
	gridTop      = 88
	targetScore  = 15
)

//go:embed assets/kofun.png assets/haniwa.png
var assetFiles embed.FS

type Point struct {
	X int
	Y int
}

type Game struct {
	snake         []Point
	direction     Point
	nextDirection Point
	food          Point
	frame         int
	score         int
	ended         bool
	won           bool
	kofun         *ebiten.Image
	haniwa        *ebiten.Image
}

func loadImage(path string) (*ebiten.Image, error) {
	data, err := assetFiles.ReadFile(path)
	if err != nil {
		return nil, err
	}
	decoded, err := png.Decode(bytes.NewReader(data))
	if err != nil {
		return nil, err
	}
	return ebiten.NewImageFromImage(decoded), nil
}

func NewGame(kofun, haniwa *ebiten.Image) *Game {
	game := &Game{kofun: kofun, haniwa: haniwa}
	game.reset()
	return game
}

func (g *Game) reset() {
	g.snake = []Point{{8, 8}, {7, 8}, {6, 8}}
	g.direction = Point{1, 0}
	g.nextDirection = g.direction
	g.frame = 0
	g.score = 0
	g.ended = false
	g.won = false
	g.placeFood()
}

func (g *Game) placeFood() {
	for {
		candidate := Point{rand.Intn(gridWidth), rand.Intn(gridHeight)}
		occupied := false
		for _, part := range g.snake {
			if part == candidate {
				occupied = true
				break
			}
		}
		if !occupied {
			g.food = candidate
			return
		}
	}
}

func (g *Game) Update() error {
	if g.ended {
		if inpututil.IsKeyJustPressed(ebiten.KeyEnter) {
			g.reset()
		}
		return nil
	}

	switch {
	case ebiten.IsKeyPressed(ebiten.KeyArrowUp) || ebiten.IsKeyPressed(ebiten.KeyW):
		if g.direction.Y == 0 {
			g.nextDirection = Point{0, -1}
		}
	case ebiten.IsKeyPressed(ebiten.KeyArrowDown) || ebiten.IsKeyPressed(ebiten.KeyS):
		if g.direction.Y == 0 {
			g.nextDirection = Point{0, 1}
		}
	case ebiten.IsKeyPressed(ebiten.KeyArrowLeft) || ebiten.IsKeyPressed(ebiten.KeyA):
		if g.direction.X == 0 {
			g.nextDirection = Point{-1, 0}
		}
	case ebiten.IsKeyPressed(ebiten.KeyArrowRight) || ebiten.IsKeyPressed(ebiten.KeyD):
		if g.direction.X == 0 {
			g.nextDirection = Point{1, 0}
		}
	}

	g.frame++
	speed := 9
	if g.score >= 8 {
		speed = 7
	}
	if g.frame < speed {
		return nil
	}
	g.frame = 0
	g.direction = g.nextDirection
	head := Point{
		X: g.snake[0].X + g.direction.X,
		Y: g.snake[0].Y + g.direction.Y,
	}
	if head.X < 0 || head.X >= gridWidth || head.Y < 0 || head.Y >= gridHeight {
		g.ended = true
		return nil
	}
	for _, part := range g.snake {
		if head == part {
			g.ended = true
			return nil
		}
	}

	g.snake = append([]Point{head}, g.snake...)
	if head == g.food {
		g.score++
		if g.score >= targetScore {
			g.won = true
			g.ended = true
		} else {
			g.placeFood()
		}
	} else {
		g.snake = g.snake[:len(g.snake)-1]
	}
	return nil
}

func cellPosition(point Point) (float64, float64) {
	return float64(gridLeft + point.X*cellSize), float64(gridTop + point.Y*cellSize)
}

func drawSprite(screen, sprite *ebiten.Image, point Point, padding float64) {
	x, y := cellPosition(point)
	bounds := sprite.Bounds()
	target := float64(cellSize) - padding*2
	options := &ebiten.DrawImageOptions{}
	options.Filter = ebiten.FilterNearest
	options.GeoM.Scale(target/float64(bounds.Dx()), target/float64(bounds.Dy()))
	options.GeoM.Translate(x+padding, y+padding)
	screen.DrawImage(sprite, options)
}

func (g *Game) Draw(screen *ebiten.Image) {
	screen.Fill(color.RGBA{8, 5, 20, 255})
	for y := 0; y < gridHeight; y++ {
		for x := 0; x < gridWidth; x++ {
			tint := color.RGBA{24, 15, 42, 255}
			if (x+y)%2 == 0 {
				tint = color.RGBA{29, 18, 50, 255}
			}
			vector.DrawFilledRect(screen,
				float32(gridLeft+x*cellSize), float32(gridTop+y*cellSize),
				cellSize-1, cellSize-1, tint, false)
		}
	}

	for index, part := range g.snake {
		x, y := cellPosition(part)
		tint := color.RGBA{141, 91, 187, 255}
		if index%2 == 0 {
			tint = color.RGBA{174, 111, 214, 255}
		}
		vector.DrawFilledRect(screen, float32(x+3), float32(y+3),
			cellSize-6, cellSize-6, tint, false)
	}
	drawSprite(screen, g.kofun, g.snake[0], 1)
	drawSprite(screen, g.haniwa, g.food, 2)

	ebitenutil.DebugPrintAt(screen, "KOFUN SNAKE", 20, 18)
	ebitenutil.DebugPrintAt(screen,
		fmt.Sprintf("HANIWA %02d / %02d", g.score, targetScore), 20, 44)
	ebitenutil.DebugPrintAt(screen, "MOVE: WASD / ARROWS", 560, 44)

	if g.ended {
		vector.DrawFilledRect(screen, 115, 235, 570, 130,
			color.RGBA{12, 6, 28, 235}, false)
		message := "THE TRAIL BROKE!"
		if g.won {
			message = "HANIWA FEAST COMPLETE!"
		}
		ebitenutil.DebugPrintAt(screen, message, 300, 270)
		ebitenutil.DebugPrintAt(screen, "Press Enter to retry", 305, 315)
	}
}

func (g *Game) Layout(_, _ int) (int, int) {
	return screenWidth, screenHeight
}

func main() {
	kofun, err := loadImage("assets/kofun.png")
	if err != nil {
		log.Fatal(err)
	}
	haniwa, err := loadImage("assets/haniwa.png")
	if err != nil {
		log.Fatal(err)
	}

	ebiten.SetWindowSize(screenWidth, screenHeight)
	ebiten.SetWindowTitle("Kofun Snake")
	ebiten.SetWindowResizingMode(ebiten.WindowResizingModeEnabled)
	if err := ebiten.RunGame(NewGame(kofun, haniwa)); err != nil {
		log.Fatal(err)
	}
}
