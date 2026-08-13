#!/usr/bin/env python3
"""Validate structural synchronization for a bilingual GitHub README pair."""

from __future__ import annotations

import argparse
from collections import Counter
import re
import sys
from pathlib import Path


SYNC_RE = re.compile(r"<!--\s*README_SYNC:\s*source=([^;>]+);\s*updated=(\d{4}-\d{2}-\d{2})\s*-->")
FENCE_RE = re.compile(r"```([^\n`]*)\n(.*?)\n```", re.DOTALL)
MD_LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+[^)]*)?\)")
HTML_LINK_RE = re.compile(r"(?:href|src)=[\"']([^\"']+)[\"']", re.IGNORECASE)
TOKEN_RE = re.compile(
    r"(?<![\w/])(?:[A-Z][A-Z0-9_]{2,}|v?\d+\.\d+(?:\.\d+)?|"
    r"[\w.-]+\.(?:md|py|js|ts|tsx|json|ya?ml|toml|sh)|"
    r"localhost:\d+|127\.0\.0\.1:\d+)(?![\w/])"
)
PLACEHOLDER_RE = re.compile(r"\[(?:TODO|TBD|PLACEHOLDER)[^\]]*\]", re.IGNORECASE)


def extract_targets(text: str) -> set[str]:
    targets = set(MD_LINK_RE.findall(text)) | set(HTML_LINK_RE.findall(text))
    return {
        target.removeprefix("./")
        for target in targets
        if not target.startswith("#")
    }


def extract_code_blocks(text: str) -> Counter[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []
    for info, block in FENCE_RE.findall(text):
        language = info.strip().split(maxsplit=1)[0].lower() if info.strip() else ""
        if language in {"mermaid", "text", "plaintext", "ascii"}:
            continue
        blocks.append((language, re.sub(r"\s+", " ", block.strip())))
    return Counter(blocks)


def extract_tokens(text: str) -> set[str]:
    code = "\n".join(block for _, block in FENCE_RE.findall(text))
    return set(TOKEN_RE.findall(code))


def validate(primary: Path, secondary: Path) -> list[str]:
    errors: list[str] = []
    if not primary.is_file():
        errors.append(f"Primary README not found: {primary}")
    if not secondary.is_file():
        errors.append(f"Secondary README not found: {secondary}")
    if errors:
        return errors

    primary_text = primary.read_text(encoding="utf-8")
    secondary_text = secondary.read_text(encoding="utf-8")

    primary_head = primary_text[:2000]
    secondary_head = secondary_text[:2000]
    if secondary.name not in extract_targets(primary_head):
        errors.append(f"{primary.name} does not link to {secondary.name} in its first screen")
    if primary.name not in extract_targets(secondary_head):
        errors.append(f"{secondary.name} does not link to {primary.name} in its first screen")

    primary_sync = SYNC_RE.search(primary_head)
    secondary_sync = SYNC_RE.search(secondary_head)
    if not primary_sync or not secondary_sync:
        errors.append("Both README files must include a README_SYNC marker near the top")
    elif primary_sync.groups() != secondary_sync.groups():
        errors.append("README_SYNC markers do not match")

    primary_code = extract_code_blocks(primary_text)
    secondary_code = extract_code_blocks(secondary_text)
    if primary_code != secondary_code:
        errors.append("Executable fenced code blocks differ between languages")

    primary_links = extract_targets(primary_text) - {secondary.name}
    secondary_links = extract_targets(secondary_text) - {primary.name}
    if primary_links != secondary_links:
        missing_secondary = sorted(primary_links - secondary_links)
        missing_primary = sorted(secondary_links - primary_links)
        if missing_secondary:
            errors.append(f"Targets missing from {secondary.name}: {', '.join(missing_secondary)}")
        if missing_primary:
            errors.append(f"Targets missing from {primary.name}: {', '.join(missing_primary)}")

    primary_tokens = extract_tokens(primary_text)
    secondary_tokens = extract_tokens(secondary_text)
    if primary_tokens != secondary_tokens:
        errors.append("Technical tokens inside code blocks differ between languages")

    for path, text in ((primary, primary_text), (secondary, secondary_text)):
        if PLACEHOLDER_RE.search(text):
            errors.append(f"Placeholder marker found in {path.name}")
        if text.count("```") % 2:
            errors.append(f"Unbalanced fenced code blocks in {path.name}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--primary", type=Path, required=True)
    parser.add_argument("--secondary", type=Path, required=True)
    args = parser.parse_args()

    errors = validate(args.primary, args.secondary)
    if errors:
        print("README pair validation: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("README pair validation: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
