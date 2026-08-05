#!/usr/bin/env python3
"""Validate conservative WeChat article HTML output."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from urllib.parse import urlparse


FORBIDDEN_TAGS = ("a", "script", "style", "iframe", "form", "input", "video", "audio")
FORBIDDEN_STYLE_PATTERNS = (
    r"position\s*:\s*(?:fixed|absolute|sticky)",
    r"display\s*:\s*grid",
    r"@media",
    r"@keyframes",
    r"var\(--",
    r"url\(\s*https?://",
)


def is_portable_image_source(source: str) -> bool:
    parsed = urlparse(html.unescape(source).strip())
    return parsed.scheme in {"https", "data"}


def validate_html(text: str) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    for tag in FORBIDDEN_TAGS:
        if re.search(fr"<\s*{tag}\b", text, flags=re.I):
            errors.append(f"forbidden tag: <{tag}>")
    for pattern in FORBIDDEN_STYLE_PATTERNS:
        if re.search(pattern, text, flags=re.I):
            errors.append(f"forbidden style: {pattern}")
    if re.search(r"\bclass\s*=", text, flags=re.I):
        warnings.append("class attribute found; fragment should not rely on classes")
    if re.search(r"\bid\s*=", text, flags=re.I):
        warnings.append("id attribute found; fragment should not rely on ids")

    images = re.findall(r"<img\b[^>]*>", text, flags=re.I)
    for image in images:
        if not re.search(r"\balt\s*=\s*[\"'][^\"']*[\"']", image, flags=re.I):
            warnings.append("image without alt")
        source_match = re.search(r"\bsrc\s*=\s*[\"']([^\"']+)[\"']", image, flags=re.I)
        if not source_match:
            errors.append("image without src")
        elif not is_portable_image_source(source_match.group(1)):
            errors.append(f"non-portable image src: {source_match.group(1)}")

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
        "images": len(images),
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
