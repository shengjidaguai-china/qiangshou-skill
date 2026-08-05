#!/usr/bin/env python3
"""Validate local Markdown image dimensions before WeChat rendering."""

from __future__ import annotations

import argparse
import json
import re
import struct
from pathlib import Path
from urllib.parse import urlparse


IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
MAX_SIDE = 2000
JPEG_SOF = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}


def image_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        return struct.unpack(">II", data[16:24])
    if data[:6] in {b"GIF87a", b"GIF89a"} and len(data) >= 10:
        return struct.unpack("<HH", data[6:10])
    if data.startswith(b"\xff\xd8"):
        index = 2
        while index + 9 < len(data):
            if data[index] != 0xFF:
                index += 1
                continue
            marker = data[index + 1]
            index += 2
            if marker in {0xD8, 0xD9}:
                continue
            if index + 2 > len(data):
                break
            length = struct.unpack(">H", data[index:index + 2])[0]
            if marker in JPEG_SOF and index + 7 <= len(data):
                height, width = struct.unpack(">HH", data[index + 3:index + 7])
                return width, height
            index += length
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP" and len(data) >= 30:
        chunk = data[12:16]
        if chunk == b"VP8X":
            width = 1 + int.from_bytes(data[24:27], "little")
            height = 1 + int.from_bytes(data[27:30], "little")
            return width, height
        if chunk == b"VP8L" and data[20] == 0x2F:
            bits = int.from_bytes(data[21:25], "little")
            return 1 + (bits & 0x3FFF), 1 + ((bits >> 14) & 0x3FFF)
        if chunk == b"VP8 ":
            start = data.find(b"\x9d\x01\x2a", 20)
            if start >= 0 and start + 7 <= len(data):
                width, height = struct.unpack("<HH", data[start + 3:start + 7])
                return width & 0x3FFF, height & 0x3FFF
    raise ValueError("unsupported or invalid raster image")


def validate_markdown_images(markdown: Path, max_side: int = MAX_SIDE) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    checked: list[dict[str, object]] = []
    source = markdown.read_text(encoding="utf-8")
    for raw_source in IMAGE_RE.findall(source):
        value = raw_source.strip().strip("<>")
        parsed = urlparse(value)
        if parsed.scheme in {"http", "https", "data"}:
            warnings.append(f"remote image dimensions not inspected: {value}")
            continue
        image_path = Path(value)
        if not image_path.is_absolute():
            image_path = (markdown.parent / image_path).resolve()
        if not image_path.exists():
            errors.append(f"missing local image: {value}")
            continue
        try:
            width, height = image_dimensions(image_path)
        except ValueError as error:
            errors.append(f"cannot inspect image {value}: {error}")
            continue
        checked.append({"source": value, "width": width, "height": height})
        if width > max_side or height > max_side:
            errors.append(f"image exceeds {max_side}px: {value} ({width}x{height})")
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
        "checked": checked,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("markdown", type=Path)
    parser.add_argument("--max-side", type=int, default=MAX_SIDE)
    args = parser.parse_args()
    report = validate_markdown_images(args.markdown, args.max_side)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
