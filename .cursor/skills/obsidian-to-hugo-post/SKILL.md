---
name: obsidian-to-hugo-post
description: >-
  Converts Obsidian markdown notes into Hugo blog posts for MyBlog. Handles
  wikilink images, callouts, front matter, and asset copying. Use when importing
  Obsidian notes, converting .md from Obsidian vault, or publishing notes to
  the Hugo blog at E:/MyBlog.
---

# Obsidian → Hugo 文章导入

将 Obsidian 笔记发布到 `E:/MyBlog` 的标准流程。

## 快速导入（推荐）

使用项目脚本：

```bash
python scripts/import_obsidian_article.py "path/to/note.md" \
  --slug post-slug \
  --title "文章标题" \
  --tags unity,csharp \
  --categories 技术 \
  --date "2026-06-29 12:00:00+0800"
```

输出目录：`content/post/<slug>/index.md` + 同目录图片。

### 常用参数

| 参数 | 说明 | 默认 |
|------|------|------|
| `source` | Obsidian `.md` 路径 | 必填 |
| `--slug` | URL slug | 从文件名推导 |
| `--title` | 文章标题 | 文件名 |
| `--tags` | 逗号分隔，需与技能树 slug 一致 | `unity` |
| `--categories` | 分类 | `技术` |
| `--date` | 发布时间 | 当前时间 |
| `--weight` | 排序权重 | `40` |
| `--image` | 封面图文件名 | 无 |

## 脚本自动处理

1. `![[image.png]]` → `![](./sanitized-name.png)` 并复制图片
2. `[[双链]]` / `[[目标|别名]]` → 纯文本（别名优先）
3. `> [!note] 标题` callout → 普通引用块
4. 首行 `# 标题` → `## 标题`（避免与 front matter `title` 重复）
5. `Name:**描述**` 行 → markdown 列表项

## 转换顺序（重要）

必须先处理 `![[...]]` 嵌入，再处理 `[[...]]` 双链，否则图片语法会被破坏。

## 手动检查清单

导入后运行 `.\hugo.exe server` 预览，确认：

- [ ] 图片全部显示（路径 `./xxx.png`，同目录）
- [ ] 无残留 `![[` 或 `[[`
- [ ] `tags` 与 `config/_default/params.toml` 技能树 slug 一致
- [ ] 正文从 `##` 开始，无重复一级标题
- [ ] `.excalidraw` 文件需先导出 PNG 再放入文章目录

## 文章目录结构

```
content/post/my-post/
├── index.md
├── cover.jpg          # 可选封面（front matter: image: cover.jpg）
└── diagram.png        # 文中配图
```

## front matter 模板

```yaml
---
title: "文章标题"
description: 简短描述
slug: my-post
date: 2026-06-29 12:00:00+0800
categories:
    - 技术
tags:
    - unity
weight: 40
---
```

## 技能树 tag 对照

tag 必须匹配 `config/_default/params.toml` 中 `[skillTree]` 的 `slug`，例如：

- `csharp` → 编程语言 / C#
- `unity` → 游戏引擎 / Unity
- `object-pool` → 游戏框架 / 对象池

无文章的 tag 在侧边栏显示为灰色不可点击。

## 发布

```powershell
cd E:\MyBlog
.\hugo.exe server          # 本地预览
# SourceTree Commit + Push  # 线上发布
```

## 示例

```bash
python scripts/import_obsidian_article.py \
  "e:/Obsidian/仓库/First/Unity性能优化.md" \
  --slug unity-performance \
  --title "Unity 性能优化" \
  --tags unity
```

生成：`content/post/unity-performance/index.md`
