#!/usr/bin/env python3
"""Verify that Markdown prose is unchanged after formatting-only edits."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+")
IMAGE_RE = re.compile(r"^\s*!\[[^\]]*\]\([^)]*\)\s*$")
HTML_COMMENT_RE = re.compile(r"^\s*<!--.*?-->\s*$")
RULE_RE = re.compile(r"^\s{0,3}(?:-{3,}|\*{3,}|_{3,})\s*$")
LIST_PREFIX_RE = re.compile(r"^\s*(?:>\s*)?(?:[-+*]|\d+[.)])\s+")
QUOTE_PREFIX_RE = re.compile(r"^\s*>\s?")
LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]*\)")
MARKUP_RE = re.compile(r"(\*\*|__|\*|_|~~|`)")
WHITESPACE_RE = re.compile(r"\s+")


def extract_prose(markdown: str) -> str:
    """Return prose characters while ignoring layout-only Markdown syntax."""
    prose_lines: list[str] = []
    in_fence = False

    for raw_line in markdown.splitlines():
        stripped = raw_line.strip()

        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue

        if in_fence:
            prose_lines.append(raw_line)
            continue

        if (
            not stripped
            or HEADING_RE.match(raw_line)
            or IMAGE_RE.match(raw_line)
            or HTML_COMMENT_RE.match(raw_line)
            or RULE_RE.match(raw_line)
        ):
            continue

        line = LIST_PREFIX_RE.sub("", raw_line)
        line = QUOTE_PREFIX_RE.sub("", line)
        line = LINK_RE.sub(r"\1", line)
        line = MARKUP_RE.sub("", line)
        prose_lines.append(line)

    return WHITESPACE_RE.sub("", "".join(prose_lines))


def first_difference(left: str, right: str) -> tuple[int, str, str] | None:
    limit = min(len(left), len(right))
    for index in range(limit):
        if left[index] != right[index]:
            return index, left[index], right[index]
    if len(left) != len(right):
        return limit, left[limit : limit + 1], right[limit : limit + 1]
    return None


def context(text: str, index: int, radius: int = 24) -> str:
    start = max(0, index - radius)
    end = min(len(text), index + radius)
    return text[start:end]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare Markdown prose while ignoring formatting-only syntax."
    )
    parser.add_argument("baseline", type=Path)
    parser.add_argument("formatted", type=Path)
    args = parser.parse_args()

    baseline = extract_prose(args.baseline.read_text(encoding="utf-8"))
    formatted = extract_prose(args.formatted.read_text(encoding="utf-8"))
    difference = first_difference(baseline, formatted)

    if difference is None:
        print(
            "PASS: prose content preserved "
            f"({len(baseline)} normalized characters)."
        )
        return 0

    index, before, after = difference
    print("FAIL: prose content changed.", file=sys.stderr)
    print(f"First difference at normalized character {index}.", file=sys.stderr)
    print(f"Baseline character: {before!r}", file=sys.stderr)
    print(f"Formatted character: {after!r}", file=sys.stderr)
    print(f"Baseline context: {context(baseline, index)!r}", file=sys.stderr)
    print(f"Formatted context: {context(formatted, index)!r}", file=sys.stderr)
    print(
        f"Lengths: baseline={len(baseline)}, formatted={len(formatted)}",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
