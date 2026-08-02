#!/usr/bin/env python3
"""Render a conservative Markdown subset to WeChat-friendly inline HTML."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path


COLORS = {
    "ink": "#202124",
    "muted": "#6B7280",
    "blue": "#315EFB",
    "blue_soft": "#EEF3FF",
    "orange": "#F27A24",
    "orange_soft": "#FFF4EA",
    "line": "#E5E7EB",
    "paper": "#FFFDFC",
}

P_STYLE = (
    "margin:0 0 18px;color:#202124;font-size:16px;line-height:1.9;"
    "letter-spacing:0.03em;text-align:justify;"
)


def inline_markup(text: str) -> str:
    """Escape text and render a deliberately small inline Markdown subset."""
    placeholders: list[str] = []

    def hold(value: str) -> str:
        placeholders.append(value)
        return f"\x00{len(placeholders) - 1}\x00"

    def image_repl(match: re.Match[str]) -> str:
        alt = html.escape(match.group(1), quote=True)
        src = html.escape(match.group(2), quote=True)
        return hold(
            f'<img src="{src}" alt="{alt}" '
            'style="display:block;width:100%;height:auto;margin:24px auto 8px;'
            'border-radius:12px;border:0;" />'
        )

    def link_repl(match: re.Match[str]) -> str:
        label = html.escape(match.group(1))
        href = html.escape(match.group(2), quote=True)
        return hold(
            f'<a href="{href}" style="color:{COLORS["blue"]};'
            'text-decoration:underline;text-underline-offset:3px;">'
            f"<span>{label}</span></a>"
        )

    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", image_repl, text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link_repl, text)
    escaped = html.escape(text, quote=False)
    escaped = re.sub(
        r"`([^`]+)`",
        lambda m: (
            '<code style="font-family:Menlo,Consolas,monospace;font-size:0.9em;'
            'color:#B45309;background:#FFF7ED;padding:2px 5px;border-radius:4px;">'
            f"{m.group(1)}</code>"
        ),
        escaped,
    )
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", escaped)
    escaped = re.sub(r"~~([^~]+)~~", r"<del>\1</del>", escaped)
    escaped = escaped.replace("  \n", "<br />")

    for index, value in enumerate(placeholders):
        escaped = escaped.replace(html.escape(f"\x00{index}\x00"), value)
        escaped = escaped.replace(f"\x00{index}\x00", value)
    return escaped


def paragraph(text: str) -> str:
    rendered = inline_markup(text.strip())
    if rendered.startswith("<img ") and rendered.endswith("/>"):
        return rendered
    return f'<p style="{P_STYLE}"><span>{rendered}</span></p>'


def heading(level: int, text: str, chapter_index: int) -> str:
    rendered = inline_markup(text.strip())
    if level == 1:
        return ""
    if level == 2:
        number = f"{chapter_index:02d}"
        return (
            '<section style="margin:42px 0 22px;padding-top:8px;">'
            f'<p style="margin:0 0 7px;color:{COLORS["orange"]};font-size:13px;'
            'font-weight:700;letter-spacing:0.18em;"><span>CHAPTER '
            f"{number}</span></p>"
            f'<h2 style="margin:0;color:{COLORS["ink"]};font-size:23px;'
            'line-height:1.45;font-weight:800;letter-spacing:0.02em;">'
            f"<span>{rendered}</span></h2>"
            f'<p style="margin:13px 0 0;width:44px;height:4px;background:{COLORS["blue"]};'
            'border-radius:4px;"><span>&nbsp;</span></p></section>'
        )
    return (
        f'<h3 style="margin:30px 0 15px;padding-left:12px;border-left:4px solid '
        f'{COLORS["blue"]};color:{COLORS["ink"]};font-size:18px;line-height:1.55;'
        f'font-weight:750;"><span>{rendered}</span></h3>'
    )


def render_markdown(source: str) -> tuple[str, dict[str, int | str]]:
    lines = source.splitlines()
    output: list[str] = [
        f'<section data-tool="qiangshou" style="margin:0 auto;padding:0 8px;'
        f'color:{COLORS["ink"]};background:{COLORS["paper"]};font-family:'
        '-apple-system,BlinkMacSystemFont,&quot;PingFang SC&quot;,&quot;Microsoft YaHei&quot;,sans-serif;">'
    ]
    counts = {"h2": 0, "h3": 0, "paragraphs": 0, "images": 0, "quotes": 0, "lists": 0, "code_blocks": 0}
    title = ""
    paragraph_lines: list[str] = []
    quote_lines: list[str] = []
    list_items: list[tuple[str, str]] = []
    code_lines: list[str] = []
    code_lang = ""
    in_code = False
    chapter_index = 0

    def flush_paragraph() -> None:
        if paragraph_lines:
            text = "\n".join(paragraph_lines).strip()
            if text:
                output.append(paragraph(text))
                counts["paragraphs"] += 1
                counts["images"] += len(re.findall(r"!\[[^\]]*\]\([^)]+\)", text))
            paragraph_lines.clear()

    def flush_quote() -> None:
        if quote_lines:
            body = "<br />".join(inline_markup(x.strip()) for x in quote_lines)
            output.append(
                f'<blockquote style="margin:22px 0;padding:18px 18px 16px;'
                f'border:0;border-left:4px solid {COLORS["orange"]};'
                f'background:{COLORS["orange_soft"]};border-radius:0 10px 10px 0;">'
                f'<p style="margin:0;color:#4B5563;font-size:15px;line-height:1.85;">'
                f"<span>{body}</span></p></blockquote>"
            )
            counts["quotes"] += 1
            quote_lines.clear()

    def flush_list() -> None:
        if not list_items:
            return
        ordered = list_items[0][0] == "ol"
        tag = "ol" if ordered else "ul"
        output.append(
            f'<{tag} style="margin:10px 0 22px;padding-left:1.5em;color:{COLORS["ink"]};">'
        )
        for _, item in list_items:
            output.append(
                '<li style="margin:8px 0;font-size:16px;line-height:1.8;">'
                f"<span>{inline_markup(item)}</span></li>"
            )
        output.append(f"</{tag}>")
        counts["lists"] += 1
        list_items.clear()

    for raw in lines + [""]:
        stripped = raw.strip()
        if in_code:
            if stripped.startswith("```"):
                code = html.escape("\n".join(code_lines))
                lang_badge = (
                    f'<p style="margin:0 0 10px;color:#94A3B8;font-size:12px;">'
                    f"<span>{html.escape(code_lang)}</span></p>"
                    if code_lang
                    else ""
                )
                output.append(
                    '<section style="margin:22px 0;padding:16px 18px;background:#111827;'
                    f'border-radius:10px;overflow-x:auto;">{lang_badge}'
                    '<pre style="margin:0;color:#E5E7EB;font-size:13px;line-height:1.7;'
                    'font-family:Menlo,Consolas,monospace;white-space:pre-wrap;word-break:break-word;">'
                    f"<code>{code}</code></pre></section>"
                )
                counts["code_blocks"] += 1
                code_lines.clear()
                code_lang = ""
                in_code = False
            else:
                code_lines.append(raw)
            continue

        if stripped.startswith("```"):
            flush_paragraph()
            flush_quote()
            flush_list()
            in_code = True
            code_lang = stripped[3:].strip()
            continue

        heading_match = re.match(r"^(#{1,3})\s+(.+)$", stripped)
        if heading_match:
            flush_paragraph()
            flush_quote()
            flush_list()
            level = len(heading_match.group(1))
            text = heading_match.group(2)
            if level == 1:
                title = re.sub(r"\*\*|`", "", text)
            elif level == 2:
                chapter_index += 1
                counts["h2"] += 1
                output.append(heading(level, text, chapter_index))
            else:
                counts["h3"] += 1
                output.append(heading(level, text, chapter_index))
            continue

        if stripped.startswith(">"):
            flush_paragraph()
            flush_list()
            quote_lines.append(stripped[1:].lstrip())
            continue
        flush_quote()

        list_match = re.match(r"^[-*]\s+(.+)$", stripped)
        ordered_match = re.match(r"^\d+[.)]\s+(.+)$", stripped)
        if list_match or ordered_match:
            flush_paragraph()
            kind = "ul" if list_match else "ol"
            if list_items and list_items[0][0] != kind:
                flush_list()
            list_items.append((kind, (list_match or ordered_match).group(1)))
            continue
        flush_list()

        if stripped in {"---", "***", "___"}:
            flush_paragraph()
            output.append(
                f'<hr style="margin:34px auto;border:0;border-top:1px solid {COLORS["line"]};width:44%;" />'
            )
            continue

        if not stripped:
            flush_paragraph()
            continue
        paragraph_lines.append(raw)

    if in_code:
        raise ValueError("Unclosed fenced code block")
    output.append("</section>")
    counts["title"] = title
    return "\n".join(output), counts


def preview_document(title: str, fragment: str) -> str:
    safe_title = html.escape(title or "公众号排版预览")
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>{safe_title}</title>
<style>
body {{ margin:0; background:#eef1f5; color:#202124; }}
.toolbar {{ position:sticky; top:0; z-index:10; display:flex; justify-content:center; gap:12px;
  padding:12px; background:rgba(255,255,255,.96); border-bottom:1px solid #e5e7eb; }}
button {{ appearance:none; border:0; border-radius:8px; padding:10px 18px; color:white;
  background:#315EFB; font-size:14px; font-weight:700; cursor:pointer; }}
.hint {{ align-self:center; color:#6b7280; font:13px/1.4 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif; }}
#article {{ max-width:677px; margin:24px auto; padding:32px 26px 60px; background:#fffdfc;
  box-shadow:0 10px 32px rgba(15,23,42,.08); }}
@media (max-width:720px) {{ #article {{ margin:0; padding:24px 18px 48px; box-shadow:none; }} }}
</style>
</head>
<body>
<div class="toolbar"><button id="copy">复制富文本正文</button><span class="hint" id="status">复制后粘贴到公众号编辑器</span></div>
<main id="article">{fragment}</main>
<script>
document.getElementById('copy').addEventListener('click', async () => {{
  const article = document.querySelector('#article > section');
  const status = document.getElementById('status');
  try {{
    const blob = new Blob([article.outerHTML], {{type:'text/html'}});
    const plain = new Blob([article.innerText], {{type:'text/plain'}});
    await navigator.clipboard.write([new ClipboardItem({{'text/html':blob,'text/plain':plain}})]);
    status.textContent = '已复制富文本正文';
  }} catch (error) {{
    const range = document.createRange();
    range.selectNode(article);
    const selection = window.getSelection();
    selection.removeAllRanges(); selection.addRange(range);
    document.execCommand('copy'); selection.removeAllRanges();
    status.textContent = '已复制（兼容模式）';
  }}
}});
</script>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("markdown", type=Path)
    parser.add_argument("--fragment", type=Path, required=True)
    parser.add_argument("--preview", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    source = args.markdown.read_text(encoding="utf-8")
    fragment, report = render_markdown(source)
    args.fragment.parent.mkdir(parents=True, exist_ok=True)
    args.preview.parent.mkdir(parents=True, exist_ok=True)
    args.fragment.write_text(fragment + "\n", encoding="utf-8")
    args.preview.write_text(preview_document(str(report["title"]), fragment), encoding="utf-8")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
