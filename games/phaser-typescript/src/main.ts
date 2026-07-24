import Phaser from "phaser";

const WIDTH = 960;
const HEIGHT = 540;
const GOAL_SECONDS = 30;

class DashScene extends Phaser.Scene {
  private player!: Phaser.Physics.Arcade.Sprite;
  private obstacles!: Phaser.Physics.Arcade.Group;
  private cursors!: Phaser.Types.Input.Keyboard.CursorKeys;
  private jumpKey!: Phaser.Input.Keyboard.Key;
  private restartKey!: Phaser.Input.Keyboard.Key;
  private statusText!: Phaser.GameObjects.Text;
  private messageText!: Phaser.GameObjects.Text;
  private elapsed = 0;
  private ended = false;
  private spawnTimer?: Phaser.Time.TimerEvent;

  constructor() {
    super("dash");
  }

  preload(): void {
    this.load.image("background", "/assets/background.png");
    this.load.image("kofun", "/assets/kofun.png");
    this.load.image("dochicken", "/assets/dochicken.png");
  }

  create(): void {
    this.elapsed = 0;
    this.ended = false;

    this.add
      .image(WIDTH / 2, HEIGHT / 2, "background")
      .setDisplaySize(WIDTH, HEIGHT)
      .setTint(0x9999aa);
    this.add.rectangle(WIDTH / 2, 510, WIDTH, 60, 0x120827, 0.96);
    this.add.rectangle(WIDTH / 2, 482, WIDTH, 4, 0xff6fbb, 0.8);

    const ground = this.add.rectangle(WIDTH / 2, 510, WIDTH, 60, 0, 0);
    this.physics.add.existing(ground, true);

    this.player = this.physics.add.sprite(145, 430, "kofun");
    this.player.setDisplaySize(70, 70);
    this.player.setCollideWorldBounds(true);
    this.player.setGravityY(1100);
    this.player.setDepth(2);
    const playerBody = this.player.body as Phaser.Physics.Arcade.Body;
    playerBody.setSize(58, 64).setOffset(19, 18);
    this.physics.add.collider(this.player, ground);

    this.obstacles = this.physics.add.group({
      allowGravity: false,
      immovable: true,
    });
    this.physics.add.overlap(
      this.player,
      this.obstacles,
      () => this.finish(false),
      undefined,
      this,
    );

    this.add.rectangle(WIDTH / 2, 28, WIDTH, 56, 0x0b0618, 0.92);
    this.statusText = this.add.text(22, 14, "", {
      color: "#ffffff",
      fontFamily: "monospace",
      fontSize: "22px",
    });
    this.messageText = this.add
      .text(WIDTH / 2, 225, "NEON KOFUN DASH\nSurvive for 30 seconds!", {
        align: "center",
        color: "#fff0a3",
        fontFamily: "monospace",
        fontSize: "34px",
        stroke: "#240d39",
        strokeThickness: 8,
      })
      .setOrigin(0.5);

    this.cursors = this.input.keyboard!.createCursorKeys();
    this.jumpKey = this.input.keyboard!.addKey(Phaser.Input.Keyboard.KeyCodes.W);
    this.restartKey = this.input.keyboard!.addKey(
      Phaser.Input.Keyboard.KeyCodes.ENTER,
    );
    this.input.on("pointerdown", () => {
      if (this.ended) {
        this.scene.restart();
      } else {
        this.jump();
      }
    });

    this.spawnTimer = this.time.addEvent({
      delay: 1250,
      loop: true,
      callback: () => this.spawnObstacle(),
    });
    this.time.delayedCall(1600, () => {
      if (!this.ended) this.messageText.setText("");
    });
    this.updateStatus();
  }

  update(_time: number, delta: number): void {
    if (this.ended) {
      if (Phaser.Input.Keyboard.JustDown(this.restartKey)) {
        this.scene.restart();
      }
      return;
    }

    if (
      Phaser.Input.Keyboard.JustDown(this.cursors.space!) ||
      Phaser.Input.Keyboard.JustDown(this.cursors.up!) ||
      Phaser.Input.Keyboard.JustDown(this.jumpKey)
    ) {
      this.jump();
    }

    this.elapsed += delta / 1000;
    const speed = 285 + this.elapsed * 7;
    this.obstacles.children.each((child) => {
      const obstacle = child as Phaser.Physics.Arcade.Sprite;
      obstacle.setVelocityX(-speed);
      if (obstacle.x < -80) obstacle.destroy();
      return true;
    });
    this.updateStatus();

    if (this.elapsed >= GOAL_SECONDS) {
      this.finish(true);
    }
  }

  private jump(): void {
    const body = this.player.body as Phaser.Physics.Arcade.Body;
    if (body.blocked.down || body.touching.down) {
      this.player.setVelocityY(-510);
    }
  }

  private spawnObstacle(): void {
    if (this.ended) return;
    const obstacle = this.obstacles.create(
      WIDTH + 70,
      446,
      "dochicken",
    ) as Phaser.Physics.Arcade.Sprite;
    obstacle.setDisplaySize(68, 68);
    const body = obstacle.body as Phaser.Physics.Arcade.Body;
    body.setSize(64, 70).setOffset(16, 16);
    obstacle.setDepth(2);
  }

  private updateStatus(): void {
    this.statusText.setText(
      `NEON KOFUN DASH     TIME ${Math.min(this.elapsed, GOAL_SECONDS)
        .toFixed(1)
        .padStart(4, "0")} / ${GOAL_SECONDS}.0`,
    );
  }

  private finish(won: boolean): void {
    if (this.ended) return;
    this.ended = true;
    this.spawnTimer?.remove(false);
    this.physics.pause();
    this.player.setTint(won ? 0xfff0a3 : 0xff83a8);
    this.messageText.setText(
      `${won ? "ROOFTOP CLEARED!" : "DOCHICKEN COLLISION!"}\nPress Enter or click to retry`,
    );
  }
}

new Phaser.Game({
  type: Phaser.AUTO,
  parent: "game",
  width: WIDTH,
  height: HEIGHT,
  backgroundColor: "#090512",
  pixelArt: true,
  physics: {
    default: "arcade",
    arcade: {
      debug: false,
      gravity: { x: 0, y: 0 },
    },
  },
  scale: {
    mode: Phaser.Scale.FIT,
    autoCenter: Phaser.Scale.CENTER_BOTH,
  },
  scene: DashScene,
});
