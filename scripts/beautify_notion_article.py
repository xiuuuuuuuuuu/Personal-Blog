#!/usr/bin/env python3
"""Beautify Notion-exported markdown for Hugo."""

from __future__ import annotations

import re
import sys
from pathlib import Path

META_LABELS = (
    "类名",
    "命名空间",
    "方法",
    "特性名",
    "需要引用命名空间",
    "主要方法",
    "主要类",
    "用法",
    "理解",
    "规则一",
    "规则二",
    "规则三",
    "新知识点",
    "参数一",
    "参数二",
    "参数三",
    "参数四",
)


def dedent_fenced_code(body: str) -> str:
    out: list[str] = []
    in_fence = False
    indent = ""
    for line in body.splitlines():
        m = re.match(r"^(\s*)(```)(.*)$", line)
        if m:
            if not in_fence:
                in_fence = True
                indent = m.group(1)
                out.append(m.group(2) + m.group(3))
            else:
                in_fence = False
                indent = ""
                out.append("```" + m.group(3))
            continue
        if in_fence and indent and line.startswith(indent):
            out.append(line[len(indent) :] if line.strip() else "")
        else:
            out.append(line)
    return "\n".join(out)


def is_special_line(line: str) -> bool:
    s = line.strip()
    if not s:
        return True
    if s.startswith("#"):
        return True
    if s.startswith(">"):
        return True
    if s.startswith("|"):
        return True
    if s.startswith("!["):
        return True
    if s.startswith("```"):
        return True
    if s.startswith("**"):
        return True
    if re.match(r"^\[?\d", s):
        return True
    if re.match(r"^[-*]\s", s):
        return True
    return False


def merge_plain_paragraphs(body: str) -> str:
    lines = body.splitlines()
    lines = remove_soft_blank_lines(lines)
    out: list[str] = []
    buffer: list[str] = []
    in_fence = False

    def flush() -> None:
        nonlocal buffer
        if not buffer:
            return
        if len(buffer) == 1 and buffer[0].strip() == "说人话":
            out.append("> **说人话**")
        elif len(buffer) > 1 and buffer[0].strip() == "说人话":
            out.append("> **说人话**" + "".join(buffer[1:]))
        else:
            out.append("\n".join(buffer))
        buffer = []

    for line in lines:
        if re.match(r"^\s*```", line):
            flush()
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue
        if not line.strip():
            flush()
            out.append("")
            continue
        if is_special_line(line):
            flush()
            out.append(line)
            continue
        buffer.append(line.strip())

    flush()
    return "\n".join(out)


def remove_soft_blank_lines(lines: list[str]) -> list[str]:
    out: list[str] = []
    i = 0
    while i < len(lines):
        if (
            i + 2 < len(lines)
            and lines[i].strip()
            and not lines[i + 1].strip()
            and lines[i + 2].strip()
            and not is_special_line(lines[i])
            and not is_special_line(lines[i + 2])
        ):
            out.append(lines[i])
            i += 2
            continue
        out.append(lines[i])
        i += 1
    return out


def split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---"):
        raise ValueError("Front matter not found")
    end = text.find("\n---", 3)
    if end == -1:
        raise ValueError("Front matter not closed")
    split_at = end + len("\n---\n")
    return text[:split_at], text[split_at:]


def beautify_body(body: str) -> str:
    lines = body.splitlines()
    out: list[str] = []
    in_code = False
    prev_blank = False

    def add(line: str) -> None:
        nonlocal prev_blank
        blank = not line.strip()
        if blank and prev_blank:
            return
        prev_blank = blank
        out.append(line)

    meta_re = re.compile(rf"^({'|'.join(META_LABELS)})[:：](.*)$")

    for raw in lines:
        if re.match(r"^\s*```", raw):
            in_code = not in_code
            add(raw)
            continue
        if in_code:
            add(raw)
            continue
        if re.match(r"^\s*---\s*$", raw):
            continue

        trimmed = raw.lstrip()
        if not trimmed:
            add("")
            continue

        indent = len(raw) - len(trimmed)

        m = re.match(r"^- (.+)$", trimmed)
        if m:
            level = min(6, 4 + indent // 4)
            add("#" * level + " " + m.group(1).strip())
            continue

        m = meta_re.match(trimmed)
        if m:
            label, value = m.group(1), m.group(2).strip()
            if label in ("命名空间", "方法"):
                add(f"**{label}：** `{value}`")
            else:
                add(f"**{label}：** {value}")
            continue

        m = re.match(r"^说人话[:：](.*)$", trimmed)
        if m:
            add(f"> **说人话：**{m.group(1)}")
            continue

        add(trimmed)

    body = "\n".join(out)
    body = re.sub(r"UTF\s*-\s*8", "UTF-8", body)

    body = re.sub(
        r"### 各类型数据转字节数据\n\n#### 不同变量类型\n\n[^\n#]+",
        "### 各类型数据转字节数据\n\n"
        "#### 不同变量类型\n\n"
        "- **有符号：** `sbyte`、`int`、`short`、`long`\n"
        "- **无符号：** `byte`、`uint`、`ushort`、`ulong`\n"
        "- **浮点：** `float`、`double`、`decimal`\n"
        "- **特殊：** `bool`、`char`、`string`",
        body,
        count=1,
    )

    body = re.sub(
        r"(- \*\*特殊：\*\*[^\n]+\n)\n(?:无符号|浮点|特殊).+\n(?:浮点|特殊).+\n(?:特殊).+\n",
        r"\1\n",
        body,
        count=1,
    )

    body = dedent_fenced_code(body)
    body = merge_plain_paragraphs(body)
    body = re.sub(r"\n{3,}", "\n\n", body)

    body = re.sub(
        r"(### 各类型数据转字节数据\n\n)#### 不同变量类型\n\n"
        r"有符号  sbyte   int   short   long\n\n"
        r"无符号  byte    uint   ushort   ulong\n\n"
        r"浮点   float double  decimal\n\n"
        r"特殊   bool   char   string",
        "### 各类型数据转字节数据\n\n"
        "#### 不同变量类型\n\n"
        "- **有符号：** `sbyte`、`int`、`short`、`long`\n"
        "- **无符号：** `byte`、`uint`、`ushort`、`ulong`\n"
        "- **浮点：** `float`、`double`、`decimal`\n"
        "- **特殊：** `bool`、`char`、`string`",
        body,
        count=1,
    )

    intro = (
        "\n> 本文整理自 Unity / C# 数据持久化学习笔记，涵盖字节转换、"
        "文件与文件夹操作、文件流、序列化与加密等内容。\n\n"
    )
    body = re.sub(r"^\s*(## 基础知识)", intro + r"\1", body, count=1)

    placeholders = [
        ("### 需求分析", "### Excel配置表数据功能"),
        ("### Excel配置表数据功能", "### 表加载使用功能"),
        ("### 表加载使用功能", "### 导出通用工具包"),
    ]
    for a, b in placeholders:
        body = body.replace(f"{a}\n{b}", f"{a}\n\n> 本节内容待补充。\n\n{b}", 1)

    if body.rstrip().endswith("### 导出通用工具包"):
        body = body.rstrip() + "\n\n> 本节内容待补充。\n"

    return body


def main() -> None:
    article = Path(__file__).resolve().parents[1] / "content/post/data-persistence-binary/index.md"
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else article
    text = path.read_text(encoding="utf-8")
    frontmatter, body = split_frontmatter(text)
    path.write_text(frontmatter + beautify_body(body).lstrip("\n"), encoding="utf-8")
    print(f"Beautified: {path}")


if __name__ == "__main__":
    main()
