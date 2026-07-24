use macroquad::prelude::*;
use macroquad::rand::gen_range;

const ROUND_SECONDS: f32 = 30.0;

struct Bullet {
    position: Vec2,
    velocity: Vec2,
}

struct Enemy {
    position: Vec2,
    speed: f32,
}

struct Game {
    player: Vec2,
    bullets: Vec<Bullet>,
    enemies: Vec<Enemy>,
    spawn_timer: f32,
    shot_timer: f32,
    elapsed: f32,
    score: u32,
    health: i32,
    ended: bool,
    won: bool,
}

impl Game {
    fn new() -> Self {
        Self {
            player: vec2(screen_width() / 2.0, screen_height() / 2.0),
            bullets: Vec::new(),
            enemies: Vec::new(),
            spawn_timer: 0.7,
            shot_timer: 0.0,
            elapsed: 0.0,
            score: 0,
            health: 3,
            ended: false,
            won: false,
        }
    }

    fn spawn_enemy(&mut self) {
        let side = gen_range(0, 4);
        let margin = 55.0;
        let position = match side {
            0 => vec2(-margin, gen_range(70.0, screen_height() - margin)),
            1 => vec2(screen_width() + margin, gen_range(70.0, screen_height() - margin)),
            2 => vec2(gen_range(margin, screen_width() - margin), -margin),
            _ => vec2(
                gen_range(margin, screen_width() - margin),
                screen_height() + margin,
            ),
        };
        self.enemies.push(Enemy {
            position,
            speed: gen_range(72.0, 112.0) + self.elapsed * 1.4,
        });
    }

    fn shoot(&mut self) {
        if self.shot_timer > 0.0 {
            return;
        }
        let target = self
            .enemies
            .iter()
            .min_by(|a, b| {
                a.position
                    .distance_squared(self.player)
                    .total_cmp(&b.position.distance_squared(self.player))
            })
            .map(|enemy| enemy.position)
            .unwrap_or_else(|| self.player + vec2(1.0, 0.0));
        let direction = (target - self.player).normalize_or_zero();
        self.bullets.push(Bullet {
            position: self.player,
            velocity: direction * 520.0,
        });
        self.shot_timer = 0.22;
    }

    fn update(&mut self, dt: f32) {
        if self.ended {
            return;
        }
        self.elapsed += dt;
        self.spawn_timer -= dt;
        self.shot_timer = (self.shot_timer - dt).max(0.0);

        let mut movement = Vec2::ZERO;
        if is_key_down(KeyCode::Left) || is_key_down(KeyCode::A) {
            movement.x -= 1.0;
        }
        if is_key_down(KeyCode::Right) || is_key_down(KeyCode::D) {
            movement.x += 1.0;
        }
        if is_key_down(KeyCode::Up) || is_key_down(KeyCode::W) {
            movement.y -= 1.0;
        }
        if is_key_down(KeyCode::Down) || is_key_down(KeyCode::S) {
            movement.y += 1.0;
        }
        self.player += movement.normalize_or_zero() * 265.0 * dt;
        self.player.x = self.player.x.clamp(34.0, screen_width() - 34.0);
        self.player.y = self.player.y.clamp(74.0, screen_height() - 34.0);

        if is_key_down(KeyCode::Space) {
            self.shoot();
        }
        if self.spawn_timer <= 0.0 {
            self.spawn_enemy();
            self.spawn_timer = (0.8 - self.elapsed * 0.012).max(0.35);
        }

        for bullet in &mut self.bullets {
            bullet.position += bullet.velocity * dt;
        }
        for enemy in &mut self.enemies {
            let direction = (self.player - enemy.position).normalize_or_zero();
            enemy.position += direction * enemy.speed * dt;
        }

        let mut bullet_alive = vec![true; self.bullets.len()];
        let mut enemy_alive = vec![true; self.enemies.len()];
        for (bullet_index, bullet) in self.bullets.iter().enumerate() {
            for (enemy_index, enemy) in self.enemies.iter().enumerate() {
                if bullet_alive[bullet_index]
                    && enemy_alive[enemy_index]
                    && bullet.position.distance_squared(enemy.position) < 30.0 * 30.0
                {
                    bullet_alive[bullet_index] = false;
                    enemy_alive[enemy_index] = false;
                    self.score += 1;
                }
            }
        }

        for (index, enemy) in self.enemies.iter().enumerate() {
            if enemy_alive[index]
                && enemy.position.distance_squared(self.player) < 47.0 * 47.0
            {
                enemy_alive[index] = false;
                self.health -= 1;
            }
        }
        self.bullets = self
            .bullets
            .drain(..)
            .enumerate()
            .filter_map(|(index, bullet)| {
                let on_screen = bullet.position.x > -20.0
                    && bullet.position.x < screen_width() + 20.0
                    && bullet.position.y > -20.0
                    && bullet.position.y < screen_height() + 20.0;
                (bullet_alive[index] && on_screen).then_some(bullet)
            })
            .collect();
        self.enemies = self
            .enemies
            .drain(..)
            .enumerate()
            .filter_map(|(index, enemy)| enemy_alive[index].then_some(enemy))
            .collect();

        if self.health <= 0 {
            self.ended = true;
        } else if self.elapsed >= ROUND_SECONDS {
            self.won = true;
            self.ended = true;
        }
    }
}

fn window_conf() -> Conf {
    Conf {
        window_title: "Kofun Orbit".to_owned(),
        window_width: 960,
        window_height: 540,
        window_resizable: true,
        high_dpi: false,
        ..Default::default()
    }
}

#[macroquad::main(window_conf)]
async fn main() {
    let background = load_texture("assets/background.png").await.unwrap();
    let kofun = load_texture("assets/kofun.png").await.unwrap();
    let dochicken = load_texture("assets/dochicken.png").await.unwrap();
    background.set_filter(FilterMode::Nearest);
    kofun.set_filter(FilterMode::Nearest);
    dochicken.set_filter(FilterMode::Nearest);

    let mut game = Game::new();
    loop {
        let dt = get_frame_time().min(0.05);
        if game.ended && is_key_pressed(KeyCode::Enter) {
            game = Game::new();
        }
        game.update(dt);

        clear_background(Color::from_rgba(8, 5, 20, 255));
        draw_texture_ex(
            &background,
            0.0,
            0.0,
            Color::from_rgba(145, 145, 160, 255),
            DrawTextureParams {
                dest_size: Some(vec2(screen_width(), screen_height())),
                ..Default::default()
            },
        );
        draw_rectangle(0.0, 0.0, screen_width(), 58.0, Color::from_rgba(8, 4, 22, 225));

        for bullet in &game.bullets {
            draw_circle(bullet.position.x, bullet.position.y, 6.0, GOLD);
            draw_circle_lines(bullet.position.x, bullet.position.y, 9.0, 2.0, WHITE);
        }
        for enemy in &game.enemies {
            draw_texture_ex(
                &dochicken,
                enemy.position.x - 30.0,
                enemy.position.y - 30.0,
                WHITE,
                DrawTextureParams {
                    dest_size: Some(vec2(60.0, 60.0)),
                    ..Default::default()
                },
            );
        }
        draw_texture_ex(
            &kofun,
            game.player.x - 34.0,
            game.player.y - 34.0,
            WHITE,
            DrawTextureParams {
                dest_size: Some(vec2(68.0, 68.0)),
                ..Default::default()
            },
        );

        let remaining = (ROUND_SECONDS - game.elapsed).max(0.0);
        draw_text(
            &format!(
                "KOFUN ORBIT     SCORE {:03}     HEART {}     TIME {:04.1}",
                game.score, game.health, remaining
            ),
            20.0,
            37.0,
            25.0,
            WHITE,
        );
        draw_text(
            "Move: WASD / Arrows    Auto-aim shot: Space",
            20.0,
            screen_height() - 18.0,
            20.0,
            LIGHTGRAY,
        );

        if game.ended {
            draw_rectangle(
                0.0,
                0.0,
                screen_width(),
                screen_height(),
                Color::from_rgba(8, 4, 22, 205),
            );
            let title = if game.won {
                "ORBIT DEFENDED!"
            } else {
                "THE ORBIT FELL!"
            };
            let title_size = measure_text(title, None, 44, 1.0);
            draw_text(
                title,
                (screen_width() - title_size.width) / 2.0,
                screen_height() / 2.0 - 12.0,
                44.0,
                GOLD,
            );
            let help = "Press Enter to retry";
            let help_size = measure_text(help, None, 25, 1.0);
            draw_text(
                help,
                (screen_width() - help_size.width) / 2.0,
                screen_height() / 2.0 + 40.0,
                25.0,
                WHITE,
            );
        }
        next_frame().await;
    }
}
