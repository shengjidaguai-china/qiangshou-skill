from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts" / "validate_readme_pair.py"
SPEC = importlib.util.spec_from_file_location("validate_readme_pair", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ReadmePairTests(unittest.TestCase):
    def write_pair(self, root: Path, primary: str, secondary: str) -> tuple[Path, Path]:
        primary_path = root / "README.md"
        secondary_path = root / "README_EN.md"
        primary_path.write_text(primary, encoding="utf-8")
        secondary_path.write_text(secondary, encoding="utf-8")
        return primary_path, secondary_path

    def test_valid_pair_passes(self) -> None:
        marker = "<!-- README_SYNC: source=working-tree; updated=2026-08-13 -->\n"
        shared = "[Demo](./demo.gif)\n\n```bash\napp --version\n```\n"
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "demo.gif").write_bytes(b"GIF89a")
            pair = self.write_pair(
                root,
                marker + "[English](./README_EN.md)\n\n# 项目\n" + shared,
                marker + "[简体中文](./README.md)\n\n# Project\n" + shared,
            )
            self.assertEqual(MODULE.validate(*pair), [])

    def test_missing_back_link_and_code_drift_fail(self) -> None:
        marker = "<!-- README_SYNC: source=working-tree; updated=2026-08-13 -->\n"
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            pair = self.write_pair(
                root,
                marker + "[English](./README_EN.md)\n```bash\napp run\n```\n",
                marker + "# Project\n```bash\napp start\n```\n",
            )
            errors = MODULE.validate(*pair)
            self.assertTrue(any("does not link" in error for error in errors))
            self.assertTrue(any("code blocks differ" in error for error in errors))

    def test_tilde_fenced_code_drift_fails(self) -> None:
        marker = "<!-- README_SYNC: source=working-tree; updated=2026-08-13 -->\n"
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            pair = self.write_pair(
                root,
                marker + "[English](./README_EN.md)\n~~~bash\napp run\n~~~\n",
                marker + "[简体中文](./README.md)\n~~~bash\napp delete\n~~~\n",
            )
            errors = MODULE.validate(*pair)
            self.assertTrue(any("code blocks differ" in error for error in errors))

    def test_shared_missing_local_target_fails(self) -> None:
        marker = "<!-- README_SYNC: source=working-tree; updated=2026-08-13 -->\n"
        shared = "[Missing](./missing.md)\n"
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            pair = self.write_pair(
                root,
                marker + "[English](./README_EN.md)\n" + shared,
                marker + "[简体中文](./README.md)\n" + shared,
            )
            errors = MODULE.validate(*pair)
            self.assertTrue(any("Missing local targets" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
