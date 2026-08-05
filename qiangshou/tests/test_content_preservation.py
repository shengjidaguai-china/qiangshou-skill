from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "verify_content_preservation.py"
SPEC = importlib.util.spec_from_file_location("verify_content_preservation", SCRIPT)
assert SPEC and SPEC.loader
preserve = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preserve)


class ContentPreservationTests(unittest.TestCase):
    def test_layout_markup_does_not_change_prose(self) -> None:
        self.assertEqual(preserve.extract_prose("正文原样"), preserve.extract_prose("**正文原样**"))

    def test_literal_underscore_change_is_detected(self) -> None:
        self.assertNotEqual(preserve.extract_prose("变量 foo_bar"), preserve.extract_prose("变量 foobar"))

    def test_link_target_change_is_detected(self) -> None:
        self.assertNotEqual(
            preserve.extract_prose("[项目](https://one.example)"),
            preserve.extract_prose("[项目](https://two.example)"),
        )

    def test_new_headings_are_allowed(self) -> None:
        baseline = preserve.extract_headings("# 原标题\n正文")
        formatted = preserve.extract_headings("# 原标题\n## 新导航\n正文")
        self.assertEqual((True, None), preserve.headings_preserved(baseline, formatted))

    def test_original_heading_change_is_rejected(self) -> None:
        baseline = preserve.extract_headings("# 原标题\n正文")
        formatted = preserve.extract_headings("# 新标题\n正文")
        self.assertEqual((False, "原标题"), preserve.headings_preserved(baseline, formatted))


if __name__ == "__main__":
    unittest.main()
