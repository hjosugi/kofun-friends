import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GAMES = ROOT / "games"
SYNC_SCRIPT = GAMES / "sync_assets.py"


def load_sync_module():
    spec = importlib.util.spec_from_file_location("sync_assets", SYNC_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load the game asset sync module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GameLabTests(unittest.TestCase):
    def test_all_seven_projects_are_present(self):
        expected = {
            "godot-gdscript": "project.godot",
            "raylib-c": "CMakeLists.txt",
            "defold-lua": "game.project",
            "love2d-lua": "main.lua",
            "phaser-typescript": "package.json",
            "macroquad-rust": "Cargo.toml",
            "ebitengine-go": "go.mod",
        }
        for project, entrypoint in expected.items():
            with self.subTest(project=project):
                self.assertTrue((GAMES / project / entrypoint).is_file())

    def test_every_declared_source_asset_exists(self):
        sync_assets = load_sync_module()
        self.assertEqual(7, len(sync_assets.PROJECT_ASSETS))
        for project, files in sync_assets.PROJECT_ASSETS.items():
            with self.subTest(project=project):
                self.assertTrue(files)
                for source in files.values():
                    self.assertTrue((ROOT / source).is_file(), source)

    def test_generated_assets_are_ignored(self):
        ignore_rules = (GAMES / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("**/assets/*.png", ignore_rules)


if __name__ == "__main__":
    unittest.main()
