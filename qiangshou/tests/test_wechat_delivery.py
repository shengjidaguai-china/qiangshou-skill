from __future__ import annotations

import importlib.util
import struct
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


render = load("render_wechat_html", ROOT / "scripts" / "render_wechat_html.py")
validate_html = load("validate_wechat_html", ROOT / "scripts" / "validate_wechat_html.py")
validate_images = load("validate_wechat_images", ROOT / "scripts" / "validate_wechat_images.py")


class WechatRenderTests(unittest.TestCase):
    def test_links_become_plain_visible_text(self) -> None:
        fragment, _ = render.render_markdown("正文见[项目地址](https://example.com)")
        self.assertNotIn("<a", fragment)
        self.assertNotIn("href=", fragment)
        self.assertIn("项目地址", fragment)
        self.assertIn("https://example.com", fragment)

    def test_markdown_table_renders_as_inline_table(self) -> None:
        fragment, report = render.render_markdown(
            "| 方案 | 结果 |\n| --- | --- |\n| A | 通过 |"
        )
        self.assertIn("<table", fragment)
        self.assertIn("<th", fragment)
        self.assertIn("<td", fragment)
        self.assertEqual(1, report["tables"])

    def test_html_validator_rejects_links_and_local_images(self) -> None:
        report = validate_html.validate_html('<a href="https://example.com">x</a><img src="./a.png" alt="a" />')
        self.assertEqual("FAIL", report["status"])
        self.assertTrue(any("forbidden tag" in error for error in report["errors"]))
        self.assertTrue(any("non-portable image" in error for error in report["errors"]))

    def test_html_validator_accepts_portable_image_and_table(self) -> None:
        report = validate_html.validate_html(
            '<table><tbody><tr><td>x</td></tr></tbody></table>'
            '<img src="https://example.com/a.png" alt="a" />'
        )
        self.assertEqual("PASS", report["status"])

    def test_rendered_fragment_passes_validator_end_to_end(self) -> None:
        fragment, _ = render.render_markdown(
            "[项目](https://example.com)\n\n"
            "| 方案 | 结果 |\n| --- | --- |\n| A | 通过 |\n\n"
            "![证据](https://example.com/a.png)"
        )
        self.assertEqual("PASS", validate_html.validate_html(fragment)["status"])


class WechatImageTests(unittest.TestCase):
    @staticmethod
    def png_header(width: int, height: int) -> bytes:
        return b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + struct.pack(">II", width, height)

    def test_dimension_validator_enforces_2000px(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "ok.png").write_bytes(self.png_header(2000, 1200))
            (root / "large.png").write_bytes(self.png_header(2001, 1200))
            markdown = root / "article.md"
            markdown.write_text("![ok](ok.png)\n![large](large.png)\n", encoding="utf-8")
            report = validate_images.validate_markdown_images(markdown)
            self.assertEqual("FAIL", report["status"])
            self.assertTrue(any("2001x1200" in error for error in report["errors"]))


if __name__ == "__main__":
    unittest.main()
