#!/usr/bin/env python3
"""Deterministic attribution and preference-state helpers for qiangshou."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import tempfile
from difflib import SequenceMatcher
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).parents[1]
FINAL_DELIVERABLES = frozenset({"visuals", "wechat_copyable_html"})
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+")
IMAGE_ONLY_RE = re.compile(r"^\s*(?:!\[[^\]]*\]\([^)]*\)|<img\b[^>]*>)\s*$", re.I)
INLINE_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
HTML_COMMENT_RE = re.compile(r"^\s*<!--.*?-->\s*$")
RULE_RE = re.compile(r"^\s{0,3}(?:-{3,}|\*{3,}|_{3,})\s*$")
LIST_PREFIX_RE = re.compile(r"^\s*(?:>\s*)?(?:[-+*]|\d+[.)])\s+")
QUOTE_PREFIX_RE = re.compile(r"^\s*>\s?")
LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]*\)")
OPAQUE_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
MAX_ACTIVE_RULES = 15
REWRITE_THRESHOLD = 0.45


def strip_inline_markup(text: str) -> str:
    """Remove layout-only Markdown while preserving literal punctuation in prose/code."""
    text = INLINE_IMAGE_RE.sub("", text)
    text = LINK_RE.sub(r"\1", text)
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
    return re.sub(r"\s+", " ", text).strip()


def _text_lines(text: str) -> list[str]:
    normalized: list[str] = []
    in_fence = False
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped.startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if not in_fence and (
            not stripped
            or HEADING_RE.match(raw)
            or IMAGE_ONLY_RE.match(raw)
            or HTML_COMMENT_RE.match(raw)
            or RULE_RE.match(raw)
        ):
            continue
        line = raw if in_fence else LIST_PREFIX_RE.sub("", QUOTE_PREFIX_RE.sub("", raw))
        line = strip_inline_markup(line)
        if line:
            normalized.append(line)
    return normalized


def _visual_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if IMAGE_ONLY_RE.match(line)]


def _lines(text: str, domain: str) -> list[str]:
    if domain == "text":
        return _text_lines(text)
    if domain == "visual":
        return _visual_lines(text)
    raise ValueError(f"unsupported domain: {domain}")


def _excerpt(lines: list[str], limit: int = 160) -> str:
    value = "\n".join(lines).strip()
    return value if len(value) <= limit else value[: limit - 1] + "…"


def _change(kind: str, before: list[str], after: list[str]) -> dict[str, object]:
    unchanged = kind == "unchanged"
    return {
        "kind": kind,
        "attribution": "assistant" if unchanged else "user",
        "learning_eligible": not unchanged,
        "draft_lines": len(before),
        "final_lines": len(after),
        "draft_excerpt": _excerpt(before),
        "final_excerpt": _excerpt(after),
    }


def _aligned_replacements(before: list[str], after: list[str]) -> list[dict[str, object]]:
    """Split a replace block into ordered rewrites, deletions, and additions."""
    rows, cols = len(before), len(after)
    scores = [[0.0] * (cols + 1) for _ in range(rows + 1)]
    similarities = [
        [SequenceMatcher(a=before[i], b=after[j], autojunk=False).ratio() for j in range(cols)]
        for i in range(rows)
    ]
    for i in range(rows - 1, -1, -1):
        for j in range(cols - 1, -1, -1):
            match = -1.0
            if similarities[i][j] >= REWRITE_THRESHOLD:
                match = similarities[i][j] + scores[i + 1][j + 1]
            scores[i][j] = max(match, scores[i + 1][j], scores[i][j + 1])

    pairs: list[tuple[int, int]] = []
    i = j = 0
    while i < rows and j < cols:
        match = -1.0
        if similarities[i][j] >= REWRITE_THRESHOLD:
            match = similarities[i][j] + scores[i + 1][j + 1]
        if match >= scores[i + 1][j] and match >= scores[i][j + 1]:
            pairs.append((i, j))
            i += 1
            j += 1
        elif scores[i + 1][j] >= scores[i][j + 1]:
            i += 1
        else:
            j += 1

    changes: list[dict[str, object]] = []
    before_pos = after_pos = 0
    for before_index, after_index in pairs:
        for line in before[before_pos:before_index]:
            changes.append(_change("deleted", [line], []))
        for line in after[after_pos:after_index]:
            changes.append(_change("added", [], [line]))
        changes.append(_change("rewritten", [before[before_index]], [after[after_index]]))
        before_pos = before_index + 1
        after_pos = after_index + 1
    for line in before[before_pos:]:
        changes.append(_change("deleted", [line], []))
    for line in after[after_pos:]:
        changes.append(_change("added", [], [line]))
    return changes


def classify_revision(draft: str, final: str, domain: str = "text") -> list[dict[str, object]]:
    """Classify normalized changes without crediting retained assistant text to the user."""
    before = _lines(draft, domain)
    after = _lines(final, domain)
    matcher = SequenceMatcher(a=before, b=after, autojunk=False)
    changes: list[dict[str, object]] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        left, right = before[i1:i2], after[j1:j2]
        if tag == "equal":
            changes.append(_change("unchanged", left, right))
        elif tag == "delete":
            changes.extend(_change("deleted", [line], []) for line in left)
        elif tag == "insert":
            changes.extend(_change("added", [], [line]) for line in right)
        else:
            changes.extend(_aligned_replacements(left, right))
    return changes


def is_final_delivery(deliverables: Iterable[str], explicit_final: bool = False) -> bool:
    return explicit_final or FINAL_DELIVERABLES.issubset(set(deliverables))


def should_promote(source_ids: Iterable[str], explicit: bool = False) -> bool:
    return explicit or len({source for source in source_ids if source}) >= 2


def source_id_for_final(final: str, domain: str = "text") -> str:
    """Hash normalized content so formatting-only changes do not duplicate a final."""
    normalized = "\n".join(_lines(final, domain)).encode("utf-8")
    digest = hashlib.sha256(normalized).hexdigest()[:16]
    return f"final-{domain}-{digest}"


def new_state(history_final_count: int = 0) -> dict[str, object]:
    return {"version": 1, "revision": 0, "history_final_count": history_final_count, "rules": {}}


def record_preference(
    state: dict[str, object],
    *,
    key: str,
    rule: str,
    source_id: str,
    explicit: bool = False,
    supersedes: Iterable[str] = (),
) -> dict[str, object]:
    """Record one abstract signal; explicit rules win and inferred rules need two sources."""
    supersedes = tuple(supersedes)
    if not OPAQUE_ID_RE.fullmatch(key) or not OPAQUE_ID_RE.fullmatch(source_id):
        raise ValueError("key and source_id must be opaque IDs using letters, digits, dot, dash, or underscore")
    if supersedes and not explicit:
        raise ValueError("only an explicit instruction may supersede existing keys")
    rule = rule.strip()
    if not rule or "\n" in rule or len(rule) > 300:
        raise ValueError("rule must be one abstract line of at most 300 characters")

    snapshot = copy.deepcopy(state)
    rules = state.setdefault("rules", {})
    if not isinstance(rules, dict):
        raise ValueError("invalid state: rules must be an object")
    for old_key in supersedes:
        if old_key != key:
            rules.pop(old_key, None)

    current = rules.get(key)
    if isinstance(current, dict) and current.get("explicit") and not explicit:
        return {"status": "ignored", "reason": "explicit_rule_has_priority", "entry": current}

    revision = int(state.get("revision", 0)) + 1
    state["revision"] = revision
    if explicit:
        sources = [source_id]
    elif isinstance(current, dict) and current.get("rule") == rule and not current.get("explicit"):
        sources = sorted({*current.get("sources", []), source_id})
    else:
        sources = [source_id]

    entry: dict[str, object] = {
        "rule": rule,
        "explicit": explicit,
        "revision": revision,
        "sources": sources,
        "status": "effective" if should_promote(sources, explicit) else "pending",
    }
    rules[key] = entry
    active = sum(1 for value in rules.values() if isinstance(value, dict) and value.get("status") == "effective")
    if active > MAX_ACTIVE_RULES:
        state.clear()
        state.update(snapshot)
        raise ValueError(f"active rule limit exceeded ({MAX_ACTIVE_RULES})")
    return {"status": "recorded", "entry": entry}


def render_memory(domain: str, state: dict[str, object]) -> str:
    rules = state.get("rules", {})
    if not isinstance(rules, dict):
        raise ValueError("invalid state: rules must be an object")
    ordered = sorted(
        ((key, value) for key, value in rules.items() if isinstance(value, dict)),
        key=lambda item: int(item[1].get("revision", 0)),
    )
    active = [(key, value) for key, value in ordered if value.get("status") == "effective"]
    pending = [(key, value) for key, value in ordered if value.get("status") == "pending"]

    if domain == "text":
        title = "作者文风记忆"
        intro = (
            "这是“枪手”的动态文字记忆，只保存可跨文章复用的文案、句长、口语、删减、列表和 AI 味偏好，"
            "最多 15 条有效规则。视觉偏好只写入 `visual-preferences.md`。不保存终稿正文或片段、文章事实、"
            "数字、观点、人物、项目、奖项、私人内容、文件路径、临时结构或差异报告。"
        )
        boundary = (
            "- 历史基线已覆盖三篇用户确认手改终稿；有可靠前稿的才参与删改归因，没有前稿的只承接用户明确指令。\n"
            "- 用户最新明确指令可以立即修正规则，并覆盖较早终稿推断。"
        )
    elif domain == "visual":
        title = "视觉审美记忆"
        intro = (
            "这是“枪手”的动态视觉记忆，只保存可跨文章复用的配图类型、裁剪、拼图、封面构图和排版偏好，"
            "最多 15 条有效规则。文案偏好只写入 `author-voice.md`。不保存图片、终稿正文、项目事实、私人内容、"
            "文件路径或临时差异报告。"
        )
        boundary = (
            "- 用户明确视觉指令立即生效；最新明确指令覆盖旧终稿推断。\n"
            "- 没有用户修改前后的视觉对照时，只记录明确指令，不从单篇成稿反推审美。"
        )
    else:
        raise ValueError(f"unsupported domain: {domain}")

    active_lines = [f"{index}. {entry['rule']}" for index, (_, entry) in enumerate(active, 1)] or ["- 暂无。"]
    pending_lines = [
        f"- {entry['rule']}（匿名样本数：{len(set(entry.get('sources', [])))}；key：`{key}`）"
        for key, entry in pending
    ] or ["- 暂无。"]
    return (
        f"# {title}\n\n{intro}\n\n## 当前有效规则\n\n"
        + "\n".join(active_lines)
        + "\n\n## 待观察（不是有效规则）\n\n"
        + "\n".join(pending_lines)
        + f"\n\n## 来源边界\n\n{boundary}\n"
    )


def load_state(path: Path) -> dict[str, object]:
    if not path.exists():
        return new_state()
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("state file must contain a JSON object")
    return value


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(text)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def default_paths(domain: str) -> tuple[Path, Path]:
    if domain == "text":
        return ROOT / "references/author-voice-signals.json", ROOT / "references/author-voice.md"
    if domain == "visual":
        return ROOT / "references/visual-preference-signals.json", ROOT / "references/visual-preferences.md"
    raise ValueError(f"unsupported domain: {domain}")


def _diff_command(args: argparse.Namespace) -> int:
    changes = classify_revision(
        args.draft.read_text(encoding="utf-8"),
        args.final.read_text(encoding="utf-8"),
        args.domain,
    )
    summary: dict[str, int] = {}
    for change in changes:
        kind = str(change["kind"])
        summary[kind] = summary.get(kind, 0) + 1
    print(json.dumps({"domain": args.domain, "summary": summary, "changes": changes}, ensure_ascii=False, indent=2))
    return 0


def _trigger_command(args: argparse.Namespace) -> int:
    triggered = is_final_delivery(args.deliverable, explicit_final=args.explicit_final)
    print(json.dumps({"final": triggered}, ensure_ascii=False))
    return 0 if triggered else 1


def _source_id_command(args: argparse.Namespace) -> int:
    print(source_id_for_final(args.final.read_text(encoding="utf-8"), args.domain))
    return 0


def _record_command(args: argparse.Namespace) -> int:
    default_state, default_memory = default_paths(args.domain)
    state_path = args.state_file or default_state
    memory_path = args.memory_file or default_memory
    state = load_state(state_path)
    result = record_preference(
        state,
        key=args.key,
        rule=args.rule,
        source_id=args.source_id,
        explicit=args.explicit,
        supersedes=args.supersedes,
    )
    if result["status"] == "recorded":
        atomic_write(state_path, json.dumps(state, ensure_ascii=False, indent=2) + "\n")
        atomic_write(memory_path, render_memory(args.domain, state))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    diff_parser = subparsers.add_parser("diff", help="classify a normalized draft/final revision")
    diff_parser.add_argument("draft", type=Path)
    diff_parser.add_argument("final", type=Path)
    diff_parser.add_argument("--domain", choices=("text", "visual"), default="text")
    diff_parser.set_defaults(func=_diff_command)

    trigger_parser = subparsers.add_parser("trigger", help="check whether delivery is a final")
    trigger_parser.add_argument("--deliverable", action="append", default=[])
    trigger_parser.add_argument("--explicit-final", action="store_true")
    trigger_parser.set_defaults(func=_trigger_command)

    source_parser = subparsers.add_parser("source-id", help="derive an opaque stable final ID")
    source_parser.add_argument("final", type=Path)
    source_parser.add_argument("--domain", choices=("text", "visual"), default="text")
    source_parser.set_defaults(func=_source_id_command)

    record_parser = subparsers.add_parser("record", help="persist one abstract preference signal")
    record_parser.add_argument("--domain", choices=("text", "visual"), required=True)
    record_parser.add_argument("--key", required=True)
    record_parser.add_argument("--rule", required=True)
    record_parser.add_argument("--source-id", required=True)
    record_parser.add_argument("--explicit", action="store_true")
    record_parser.add_argument("--supersedes", action="append", default=[])
    record_parser.add_argument("--state-file", type=Path)
    record_parser.add_argument("--memory-file", type=Path)
    record_parser.set_defaults(func=_record_command)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
