#!/usr/bin/env python3
"""Validate conservative WeChat article HTML output."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


FORBIDDEN_TAGS = ("script", "style", "iframe", "form", "input", "video", "audio")
FORBIDDEN_STYLE_PATTERNS = (
    r"position\s*:\s*(?:fixed|absolute|sticky)",
    r"display\s*:\s*grid",
    r"@media",
    r"@keyframes",
    r"var\(--",
    r"url\(\s*https?://",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html_file", type=Path)
    args = parser.parse_args()
    text = args.html_file.read_text(encoding="utf-8")

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
    image_count = len(re.findall(r"<img\b", text, flags=re.I))
    for image in re.findall(r"<img\b[^>]*>", text, flags=re.I):
        if not re.search(r"\balt\s*=\s*[\"'][^\"']*[\"']", image, flags=re.I):
            warnings.append("image without alt")
    report = {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
        "images": image_count,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
