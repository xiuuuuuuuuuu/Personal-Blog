#!/usr/bin/env python3
"""Import Notion markdown export into Hugo post folder."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTION_MD = ROOT.parent / "Notion/导出/ExportBlock-a13874af-6b52-40d3-8751-24f40fa55299-Part-1/数据持久化——二进制文件 13544433cc3c802eb88fc19be7e9adc1.md"
POST_MD = ROOT / "content/post/data-persistence-binary/index.md"
BEAUTIFY = ROOT / "scripts/beautify_notion_article.py"

FRONTMATTER = """---
title: "数据持久化——二进制文件"
description: 数据持久化——二进制文件学习笔记
slug: data-persistence-binary
date: 2026-06-28 00:00:00+0800
categories:
    - 编程
tags:
    - data-persistence
    - csharp
weight: 50
---
"""


def convert_images(content: str) -> str:
    content = re.sub(
        r"!\[([^\]]*)\]\([^)]*?/image(?:%20| )?(\d*)\.png\)",
        lambda m: f"![{m.group(1)}](image-{m.group(2)}.png)" if m.group(2) else f"![{m.group(1)}](image.png)",
        content,
    )
    return content


def strip_notion_header(content: str) -> str:
    return re.sub(
        r"(?s)^#\s*数据持久化——二进制文件\s*\r?\n\r?\nCreated:.*?\r?\n\r?\n",
        "",
        content,
        count=1,
    )


def main() -> None:
    notion = Path(sys.argv[1]) if len(sys.argv) > 1 else NOTION_MD
    body = strip_notion_header(notion.read_text(encoding="utf-8"))
    body = convert_images(body)
    POST_MD.write_text(FRONTMATTER + body.strip() + "\n", encoding="utf-8")
    subprocess.run([sys.executable, str(BEAUTIFY), str(POST_MD)], check=True)
    print(f"Imported and beautified: {POST_MD}")


if __name__ == "__main__":
    main()
