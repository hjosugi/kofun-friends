extends Node2D

const VIEW_SIZE := Vector2(960.0, 540.0)
const PLAYER_SPEED := 260.0
const ENEMY_SPEED := 125.0
const PICKUP_COUNT := 8

var player: Sprite2D
var enemy: Sprite2D
var pickups: Array[Sprite2D] = []
var score := 0
var health := 3
var ended := false
var hit_cooldown := 0.0
var rng := RandomNumberGenerator.new()
var status_label: Label
var message_label: Label


func _ready() -> void:
	rng.seed = 20260725
	_build_world()
	_reset_game()


func _build_world() -> void:
	var background := Sprite2D.new()
	background.texture = load("res://assets/background.png")
	background.centered = false
	background.scale = VIEW_SIZE / Vector2(background.texture.get_size())
	background.modulate = Color(0.55, 0.55, 0.65)
	add_child(background)

	player = _make_sprite("res://assets/kofun.png", Vector2(64.0, 64.0))
	add_child(player)
	enemy = _make_sprite("res://assets/dochicken.png", Vector2(62.0, 62.0))
	add_child(enemy)

	for index in PICKUP_COUNT:
		var pickup := _make_sprite("res://assets/haniwa.png", Vector2(36.0, 36.0))
		pickup.name = "Haniwa%d" % index
		add_child(pickup)
		pickups.append(pickup)

	var hud := CanvasLayer.new()
	add_child(hud)
	status_label = Label.new()
	status_label.position = Vector2(20.0, 16.0)
	status_label.add_theme_font_size_override("font_size", 24)
	status_label.add_theme_color_override("font_color", Color.WHITE)
	status_label.add_theme_color_override("font_shadow_color", Color.BLACK)
	status_label.add_theme_constant_override("shadow_offset_x", 2)
	status_label.add_theme_constant_override("shadow_offset_y", 2)
	hud.add_child(status_label)

	message_label = Label.new()
	message_label.position = Vector2(120.0, 205.0)
	message_label.size = Vector2(720.0, 140.0)
	message_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	message_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	message_label.add_theme_font_size_override("font_size", 34)
	message_label.add_theme_color_override("font_color", Color("#fff2b2"))
	message_label.add_theme_color_override("font_outline_color", Color("#28162f"))
	message_label.add_theme_constant_override("outline_size", 8)
	hud.add_child(message_label)


func _make_sprite(path: String, display_size: Vector2) -> Sprite2D:
	var sprite := Sprite2D.new()
	sprite.texture = load(path)
	sprite.scale = display_size / Vector2(sprite.texture.get_size())
	return sprite


func _reset_game() -> void:
	score = 0
	health = 3
	ended = false
	hit_cooldown = 0.0
	player.position = Vector2(160.0, 270.0)
	player.modulate = Color.WHITE
	enemy.position = Vector2(800.0, 270.0)
	enemy.visible = true
	for pickup in pickups:
		pickup.position = _random_position()
		pickup.visible = true
	message_label.text = "KOFUN COURIER\nCollect every haniwa!"
	get_tree().create_timer(1.7).timeout.connect(_hide_intro)
	_update_hud()


func _hide_intro() -> void:
	if not ended:
		message_label.text = ""


func _process(delta: float) -> void:
	if ended:
		if Input.is_key_pressed(KEY_ENTER):
			_reset_game()
		return

	var movement := Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
	if Input.is_key_pressed(KEY_A):
		movement.x -= 1.0
	if Input.is_key_pressed(KEY_D):
		movement.x += 1.0
	if Input.is_key_pressed(KEY_W):
		movement.y -= 1.0
	if Input.is_key_pressed(KEY_S):
		movement.y += 1.0
	if movement.length_squared() > 1.0:
		movement = movement.normalized()
	player.position += movement * PLAYER_SPEED * delta
	player.position = player.position.clamp(Vector2(34.0, 74.0), VIEW_SIZE - Vector2(34.0, 34.0))

	var chase := player.position - enemy.position
	if chase.length_squared() > 1.0:
		enemy.position += chase.normalized() * ENEMY_SPEED * delta

	for pickup in pickups:
		if pickup.visible and player.position.distance_to(pickup.position) < 47.0:
			pickup.visible = false
			score += 1
			_update_hud()
			if score == PICKUP_COUNT:
				_finish(true)

	hit_cooldown = maxf(0.0, hit_cooldown - delta)
	player.modulate.a = 0.45 if hit_cooldown > 0.0 else 1.0
	if hit_cooldown <= 0.0 and player.position.distance_to(enemy.position) < 58.0:
		health -= 1
		hit_cooldown = 1.2
		var push := (player.position - enemy.position).normalized()
		player.position += push * 70.0
		_update_hud()
		if health <= 0:
			_finish(false)


func _random_position() -> Vector2:
	return Vector2(rng.randf_range(90.0, 870.0), rng.randf_range(105.0, 470.0))


func _update_hud() -> void:
	status_label.text = "HANIWA  %d / %d     HEART  %d" % [score, PICKUP_COUNT, health]


func _finish(won: bool) -> void:
	ended = true
	message_label.text = ("DELIVERY COMPLETE!" if won else "CAUGHT BY DOCHICKEN!") + "\nPress Enter to retry"
