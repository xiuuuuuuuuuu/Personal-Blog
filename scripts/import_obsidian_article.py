#!/usr/bin/env python3
"""Import an Obsidian markdown note into a Hugo post folder."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POST_ROOT = ROOT / "content" / "post"

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp"}


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "post"


def sanitize_image_name(name: str) -> str:
    stem = Path(name).stem
    suffix = Path(name).suffix.lower()
    clean = re.sub(r"[^a-zA-Z0-9._-]+", "-", stem).strip("-").lower()
    clean = re.sub(r"-+", "-", clean)
    return f"{clean or 'image'}{suffix}"


def convert_wikilinks(content: str) -> str:
    def repl(match: re.Match[str]) -> str:
        target = match.group(1)
        alias = match.group(2)
        return alias or target.split("/")[-1]

    return re.sub(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|([^\]]+))?\]\]", repl, content)


def convert_callouts(content: str) -> str:
    def repl(match: re.Match[str]) -> str:
        title = match.group(1).strip()
        body = match.group(2).strip()
        lines = [f"> **{title}**"]
        lines.extend(f"> {line}" for line in body.splitlines() if line.strip())
        return "\n".join(lines) + "\n"

    return re.sub(
        r"(?ms)^>\s*\[!(\w+)\]\s*(.*?)\n((?:>.*(?:\n|$))*)",
        repl,
        content,
    )


def convert_embeds(content: str) -> tuple[str, list[str]]:
    images: list[str] = []

    def repl(match: re.Match[str]) -> str:
        filename = match.group(1).strip()
        images.append(filename)
        clean = sanitize_image_name(filename)
        alt = Path(filename).stem.replace("-", " ").replace("_", " ")
        return f"\n\n![{alt}](./{clean})\n\n"

    content = re.sub(r"!\[\[([^\]]+)\]\]", repl, content)
    return content, images


def normalize_headings(content: str, title: str) -> str:
    lines = content.splitlines()
    if not lines:
        return content

    first = lines[0].strip()
    if first.startswith("# "):
        heading = first[2:].strip()
        if heading == title or heading in title or title in heading:
            lines[0] = f"## {heading}"
        else:
            lines.insert(0, f"## {heading}")
            lines[1] = ""
    return "\n".join(lines)


def format_tool_lines(content: str) -> str:
    """Turn `Name:**desc` lines into markdown list items after imports."""
    out: list[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        match = re.match(r"^([A-Za-z][A-Za-z0-9 ()/.-]+):\*\*(.+)\*\*$", stripped)
        if match:
            name = match.group(1).strip()
            desc = match.group(2).strip().replace(";", "；")
            out.append(f"- **{name}**：{desc}")
            continue
        out.append(line)
    return "\n".join(out)


def build_frontmatter(
    title: str,
    slug: str,
    description: str,
    tags: list[str],
    categories: list[str],
    date: str,
    weight: int | None,
    image: str | None,
) -> str:
    lines = [
        "---",
        f'title: "{title}"',
        f"description: {description}",
        f"slug: {slug}",
        f"date: {date}",
        "categories:",
    ]
    lines.extend(f"    - {cat}" for cat in categories)
    lines.append("tags:")
    lines.extend(f"    - {tag}" for tag in tags)
    if weight is not None:
        lines.append(f"weight: {weight}")
    if image:
        lines.append(f"image: {image}")
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def copy_images(source_dir: Path, dest_dir: Path, referenced: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for original in referenced:
        src = source_dir / original
        if not src.exists():
            alt = source_dir / "attachments" / original
            if alt.exists():
                src = alt
            else:
                print(f"warning: image not found: {original}", file=sys.stderr)
                continue
        clean = sanitize_image_name(original)
        dest = dest_dir / clean
        shutil.copy2(src, dest)
        mapping[original] = clean
        print(f"copied image: {src.name} -> {dest.relative_to(ROOT)}")
    return mapping


def convert_note(body: str, title: str) -> tuple[str, list[str]]:
    body, images = convert_embeds(body)
    body = convert_callouts(body)
    body = convert_wikilinks(body)
    body = normalize_headings(body, title)
    body = format_tool_lines(body)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    return body + "\n", images


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import Obsidian note into Hugo post folder")
    parser.add_argument("source", type=Path, help="Path to Obsidian .md file")
    parser.add_argument("--slug", help="Hugo post slug (default: derived from filename)")
    parser.add_argument("--title", help="Post title (default: filename without extension)")
    parser.add_argument("--description", help="Post description")
    parser.add_argument("--tags", default="unity", help="Comma-separated tags")
    parser.add_argument("--categories", default="技术", help="Comma-separated categories")
    parser.add_argument("--date", help="Publish date, e.g. 2026-06-29 12:00:00+0800")
    parser.add_argument("--weight", type=int, default=40, help="Sort weight")
    parser.add_argument("--image", help="Cover image filename inside post folder")
    parser.add_argument(
        "--output",
        type=Path,
        help="Output post directory (default: content/post/<slug>)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = args.source.resolve()
    if not source.exists():
        raise SystemExit(f"source not found: {source}")

    title = args.title or source.stem
    slug = args.slug or slugify(source.stem) or "post"
    description = args.description or f"{title}学习笔记"
    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    categories = [c.strip() for c in args.categories.split(",") if c.strip()]
    date = args.date or datetime.now().strftime("%Y-%m-%d %H:%M:%S+0800")

    dest_dir = (args.output or POST_ROOT / slug).resolve()
    dest_dir.mkdir(parents=True, exist_ok=True)

    body = source.read_text(encoding="utf-8")
    converted, images = convert_note(body, title)

    copy_images(source.parent, dest_dir, images)

    frontmatter = build_frontmatter(
        title=title,
        slug=slug,
        description=description,
        tags=tags,
        categories=categories,
        date=date,
        weight=args.weight,
        image=args.image,
    )

    post_md = dest_dir / "index.md"
    post_md.write_text(frontmatter + converted, encoding="utf-8")
    print(f"created post: {post_md.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
