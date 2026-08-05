#!/usr/bin/env python3
"""Verify that prose and original headings survive formatting-only edits."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$")
IMAGE_RE = re.compile(r"^\s*!\[[^\]]*\]\([^)]*\)\s*$")
HTML_COMMENT_RE = re.compile(r"^\s*<!--.*?-->\s*$")
RULE_RE = re.compile(r"^\s{0,3}(?:-{3,}|\*{3,}|_{3,})\s*$")
LIST_PREFIX_RE = re.compile(r"^\s*(?:>\s*)?(?:[-+*]|\d+[.)])\s+")
QUOTE_PREFIX_RE = re.compile(r"^\s*>\s?")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]*)\)")
WHITESPACE_RE = re.compile(r"\s+")


def strip_layout_markup(text: str) -> str:
    text = LINK_RE.sub(r"\1(\2)", text)
    patterns = (
        (re.compile(r"`([^`\n]+)`"), r"\1"),
        (re.compile(r"\*\*([^*\n]+)\*\*"), r"\1"),
        (re.compile(r"(?<!\w)__([^_\n]+)__(?!\w)"), r"\1"),
        (re.compile(r"~~([^~\n]+)~~"), r"\1"),
        (re.compile(r"(?<!\w)\*([^*\n]+)\*(?!\w)"), r"\1"),
        (re.compile(r"(?<!\w)_([^_\n]+)_(?!\w)"), r"\1"),
    )
    for pattern, replacement in patterns:
        text = pattern.sub(replacement, text)
    return text


def extract_prose(markdown: str) -> str:
    prose_lines: list[str] = []
    in_fence = False
    for raw_line in markdown.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith(("```", "~~~")):
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
        prose_lines.append(strip_layout_markup(line))
    return WHITESPACE_RE.sub("", "".join(prose_lines))


def extract_headings(markdown: str) -> list[str]:
    headings: list[str] = []
    in_fence = False
    for raw_line in markdown.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = HEADING_RE.match(raw_line)
        if match:
            headings.append(WHITESPACE_RE.sub("", strip_layout_markup(match.group(1))))
    return headings


def headings_preserved(baseline: list[str], formatted: list[str]) -> tuple[bool, str | None]:
    """Allow new headings, but require every original heading unchanged and in order."""
    position = 0
    for heading in baseline:
        while position < len(formatted) and formatted[position] != heading:
            position += 1
        if position == len(formatted):
            return False, heading
        position += 1
    return True, None


def first_difference(left: str, right: str) -> tuple[int, str, str] | None:
    limit = min(len(left), len(right))
    for index in range(limit):
        if left[index] != right[index]:
            return index, left[index], right[index]
    if len(left) != len(right):
        return limit, left[limit:limit + 1], right[limit:limit + 1]
    return None


def context(text: str, index: int, radius: int = 24) -> str:
    return text[max(0, index - radius):min(len(text), index + radius)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("formatted", type=Path)
    args = parser.parse_args()

    baseline_text = args.baseline.read_text(encoding="utf-8")
    formatted_text = args.formatted.read_text(encoding="utf-8")
    baseline = extract_prose(baseline_text)
    formatted = extract_prose(formatted_text)
    difference = first_difference(baseline, formatted)
    if difference is not None:
        index, before, after = difference
        print("FAIL: prose content changed.", file=sys.stderr)
        print(f"First difference at normalized character {index}.", file=sys.stderr)
        print(f"Baseline character: {before!r}", file=sys.stderr)
        print(f"Formatted character: {after!r}", file=sys.stderr)
        print(f"Baseline context: {context(baseline, index)!r}", file=sys.stderr)
        print(f"Formatted context: {context(formatted, index)!r}", file=sys.stderr)
        print(f"Lengths: baseline={len(baseline)}, formatted={len(formatted)}", file=sys.stderr)
        return 1

    headings_ok, missing = headings_preserved(
        extract_headings(baseline_text), extract_headings(formatted_text)
    )
    if not headings_ok:
        print(f"FAIL: original heading changed, removed, or reordered: {missing!r}", file=sys.stderr)
        return 1

    print(
        "PASS: prose content and original headings preserved "
        f"({len(baseline)} normalized prose characters)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
