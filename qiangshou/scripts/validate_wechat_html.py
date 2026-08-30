#!/usr/bin/env python3
"""Validate conservative WeChat article HTML output."""

from __future__ import annotations

import argparse
import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


FORBIDDEN_TAGS = ("a", "script", "style", "iframe", "form", "input", "video", "audio")
ALLOWED_TAGS = {
    "section", "p", "span", "strong", "em", "del", "blockquote", "ul", "ol", "li",
    "pre", "code", "img", "hr", "table", "thead", "tbody", "tr", "th", "td", "h2", "h3",
}
VOID_TAGS = {"img", "hr"}
GLOBAL_ATTRIBUTES = {"style"}
TAG_ATTRIBUTES = {
    "section": {"data-tool"},
    "img": {"src", "alt"},
}
FORBIDDEN_STYLE_PATTERNS = (
    r"position\s*:\s*(?:fixed|absolute|sticky)",
    r"display\s*:\s*grid",
    r"@media",
    r"@keyframes",
    r"var\(--",
    r"url\(\s*https?://",
)


def is_portable_image_source(source: str) -> bool:
    value = html.unescape(source).strip()
    parsed = urlparse(value)
    if parsed.scheme == "https":
        return True
    return bool(
        parsed.scheme == "data"
        and re.match(r"^data:image/(?:png|jpe?g|gif|webp);", value, flags=re.I)
    )


class FragmentValidator(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.images = 0
        self.stack: list[str] = []

    def validate_tag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag not in ALLOWED_TAGS:
            self.errors.append(f"unsupported tag: <{tag}>")
            return
        seen: set[str] = set()
        values: dict[str, str] = {}
        allowed = GLOBAL_ATTRIBUTES | TAG_ATTRIBUTES.get(tag, set())
        for raw_name, raw_value in attrs:
            name = raw_name.lower()
            if name in seen:
                self.errors.append(f"duplicate attribute on <{tag}>: {name}")
                continue
            seen.add(name)
            if name.startswith("on"):
                self.errors.append(f"event handler attribute on <{tag}>: {name}")
                continue
            if name not in allowed:
                self.errors.append(f"unsupported attribute on <{tag}>: {name}")
                continue
            if raw_value is None:
                self.errors.append(f"attribute without value on <{tag}>: {name}")
                continue
            values[name] = raw_value
        if tag == "img":
            self.images += 1
            if "alt" not in values:
                self.warnings.append("image without alt")
            if "src" not in values:
                self.errors.append("image without src")
            elif not is_portable_image_source(values["src"]):
                self.errors.append(f"non-portable image src: {values['src']}")

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized = tag.lower()
        self.validate_tag(normalized, attrs)
        if normalized in ALLOWED_TAGS and normalized not in VOID_TAGS:
            self.stack.append(normalized)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.validate_tag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        normalized = tag.lower()
        if normalized in VOID_TAGS:
            self.errors.append(f"unexpected closing tag: </{normalized}>")
        elif normalized not in ALLOWED_TAGS:
            self.errors.append(f"unsupported closing tag: </{normalized}>")
        elif not self.stack or self.stack[-1] != normalized:
            self.errors.append(f"mismatched closing tag: </{normalized}>")
        else:
            self.stack.pop()

    def handle_decl(self, decl: str) -> None:
        self.errors.append(f"unsupported declaration: <!{decl}>")

    def unknown_decl(self, data: str) -> None:
        self.errors.append("unsupported declaration")

    def finish(self) -> None:
        if self.stack:
            self.errors.append(f"unclosed tags: {', '.join(self.stack)}")


def validate_html(text: str) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    for tag in FORBIDDEN_TAGS:
        if re.search(fr"<\s*{tag}\b", text, flags=re.I):
            errors.append(f"forbidden tag: <{tag}>")
    for pattern in FORBIDDEN_STYLE_PATTERNS:
        if re.search(pattern, text, flags=re.I):
            errors.append(f"forbidden style: {pattern}")
    parser = FragmentValidator()
    try:
        parser.feed(text)
        parser.close()
        parser.finish()
    except ValueError as error:
        errors.append(f"invalid HTML: {error}")
    errors.extend(parser.errors)
    warnings.extend(parser.warnings)

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
        "images": parser.images,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html_file", type=Path)
    args = parser.parse_args()
    report = validate_html(args.html_file.read_text(encoding="utf-8"))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
