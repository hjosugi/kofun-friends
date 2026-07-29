#include "raylib.h"
#include "raymath.h"

#include <math.h>
#include <stdbool.h>

#define SCREEN_WIDTH 960
#define SCREEN_HEIGHT 540
#define BRICK_ROWS 5
#define BRICK_COLUMNS 10

typedef struct Brick {
    Rectangle bounds;
    bool active;
} Brick;

static void ResetGame(Vector2 *ball_position, Vector2 *ball_velocity,
                      Rectangle *paddle, Brick bricks[BRICK_ROWS][BRICK_COLUMNS],
                      int *score, int *lives, bool *ended, bool *won) {
    *ball_position = (Vector2){SCREEN_WIDTH / 2.0f, 365.0f};
    *ball_velocity = (Vector2){235.0f, -235.0f};
    *paddle = (Rectangle){SCREEN_WIDTH / 2.0f - 62.0f, 475.0f, 124.0f, 24.0f};
    *score = 0;
    *lives = 3;
    *ended = false;
    *won = false;

    for (int row = 0; row < BRICK_ROWS; row++) {
        for (int column = 0; column < BRICK_COLUMNS; column++) {
            bricks[row][column] = (Brick){
                .bounds = (Rectangle){55.0f + column * 86.0f, 82.0f + row * 37.0f,
                                      74.0f, 25.0f},
                .active = true,
            };
        }
    }
}

int main(void) {
    SetConfigFlags(FLAG_VSYNC_HINT);
    InitWindow(SCREEN_WIDTH, SCREEN_HEIGHT, "Mound Breaker - raylib 6.0");
    SetTargetFPS(60);

    Texture2D background = LoadTexture("assets/background.png");
    Texture2D kofun = LoadTexture("assets/kofun.png");
    Vector2 ball_position;
    Vector2 ball_velocity;
    Rectangle paddle;
    Brick bricks[BRICK_ROWS][BRICK_COLUMNS];
    int score;
    int lives;
    bool ended;
    bool won;
    ResetGame(&ball_position, &ball_velocity, &paddle, bricks, &score, &lives,
              &ended, &won);

    while (!WindowShouldClose()) {
        float delta = GetFrameTime();

        if (!ended) {
            float input = 0.0f;
            if (IsKeyDown(KEY_LEFT) || IsKeyDown(KEY_A)) input -= 1.0f;
            if (IsKeyDown(KEY_RIGHT) || IsKeyDown(KEY_D)) input += 1.0f;
            paddle.x += input * 430.0f * delta;
            paddle.x = Clamp(paddle.x, 20.0f, SCREEN_WIDTH - paddle.width - 20.0f);

            ball_position.x += ball_velocity.x * delta;
            ball_position.y += ball_velocity.y * delta;
            if (ball_position.x < 12.0f || ball_position.x > SCREEN_WIDTH - 12.0f) {
                ball_velocity.x *= -1.0f;
                ball_position.x = Clamp(ball_position.x, 12.0f, SCREEN_WIDTH - 12.0f);
            }
            if (ball_position.y < 54.0f) {
                ball_velocity.y = fabsf(ball_velocity.y);
            }

            if (ball_velocity.y > 0.0f &&
                CheckCollisionCircleRec(ball_position, 11.0f, paddle)) {
                float offset = (ball_position.x - (paddle.x + paddle.width / 2.0f)) /
                               (paddle.width / 2.0f);
                ball_velocity.x = offset * 330.0f;
                ball_velocity.y = -fabsf(ball_velocity.y);
                ball_position.y = paddle.y - 12.0f;
            }

            for (int row = 0; row < BRICK_ROWS; row++) {
                for (int column = 0; column < BRICK_COLUMNS; column++) {
                    Brick *brick = &bricks[row][column];
                    if (brick->active &&
                        CheckCollisionCircleRec(ball_position, 11.0f, brick->bounds)) {
                        brick->active = false;
                        ball_velocity.y *= -1.0f;
                        score++;
                    }
                }
            }

            if (ball_position.y > SCREEN_HEIGHT + 16.0f) {
                lives--;
                if (lives <= 0) {
                    ended = true;
                } else {
                    ball_position = (Vector2){SCREEN_WIDTH / 2.0f, 365.0f};
                    ball_velocity = (Vector2){235.0f, -235.0f};
                }
            }
            if (score == BRICK_ROWS * BRICK_COLUMNS) {
                won = true;
                ended = true;
            }
        } else if (IsKeyPressed(KEY_SPACE) || IsKeyPressed(KEY_ENTER)) {
            ResetGame(&ball_position, &ball_velocity, &paddle, bricks, &score,
                      &lives, &ended, &won);
        }

        BeginDrawing();
        ClearBackground((Color){13, 9, 28, 255});
        DrawTexturePro(background,
                       (Rectangle){0, 0, (float)background.width, (float)background.height},
                       (Rectangle){0, 0, SCREEN_WIDTH, SCREEN_HEIGHT},
                       (Vector2){0, 0}, 0.0f, (Color){125, 125, 145, 255});
        DrawRectangle(0, 0, SCREEN_WIDTH, 50, (Color){15, 8, 35, 225});
        DrawText(TextFormat("MOUND BREAKER     SCORE %02d/50     LIVES %d", score, lives),
                 22, 15, 22, RAYWHITE);

        Color row_colors[BRICK_ROWS] = {PINK, ORANGE, GOLD, LIME, SKYBLUE};
        for (int row = 0; row < BRICK_ROWS; row++) {
            for (int column = 0; column < BRICK_COLUMNS; column++) {
                if (bricks[row][column].active) {
                    DrawRectangleRounded(bricks[row][column].bounds, 0.3f, 4,
                                         row_colors[row]);
                    DrawRectangleLinesEx(bricks[row][column].bounds, 2.0f,
                                         (Color){255, 255, 255, 110});
                }
            }
        }

        DrawRectangleRounded(paddle, 0.5f, 6, (Color){56, 31, 72, 255});
        DrawTexturePro(kofun,
                       (Rectangle){0, 0, (float)kofun.width, (float)kofun.height},
                       (Rectangle){paddle.x + paddle.width / 2.0f - 27.0f,
                                   paddle.y - 28.0f, 54.0f, 54.0f},
                       (Vector2){0, 0}, 0.0f, WHITE);
        DrawCircleV(ball_position, 11.0f, (Color){255, 245, 175, 255});

        if (ended) {
            DrawRectangle(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT,
                          (Color){10, 6, 25, 190});
            const char *title = won ? "ALL MOUNDS CLEARED!" : "THE BALL GOT LOST!";
            int width = MeasureText(title, 42);
            DrawText(title, (SCREEN_WIDTH - width) / 2, 218, 42,
                     (Color){255, 232, 130, 255});
            const char *again = "Press Space or Enter to retry";
            DrawText(again, (SCREEN_WIDTH - MeasureText(again, 22)) / 2, 280,
                     22, RAYWHITE);
        }
        EndDrawing();
    }

    UnloadTexture(kofun);
    UnloadTexture(background);
    CloseWindow();
    return 0;
}
