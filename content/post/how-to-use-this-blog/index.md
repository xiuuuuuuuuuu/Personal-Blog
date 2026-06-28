---
title: 如何使用这个博客
description: 给自己看的博客使用指南
slug: how-to-use-this-blog
date: 2026-06-28 00:00:00+0800
categories:
    - 教程
tags:
    - 入门
weight: 1
---

## 如何发布一篇文章

1. 打开 `E:\MyBlog\content\post` 文件夹
2. 创建一个新文件夹，名字随便取，比如 `my-first-post`
3. 在里面新建一个 `index.md` 文件
4. 用记事本打开，按下面的格式写：

```markdown
---
title: 文章标题
description: 简短描述
date: 2026-06-28 00:00:00+0800
categories:
    - 分类名
tags:
    - 标签名
---

这里写文章正文，支持 Markdown 语法。
```

5. 保存文件
6. 本地预览：打开 PowerShell，运行：

```powershell
cd E:\MyBlog
.\hugo.exe server
```

然后浏览器打开 `http://localhost:1313/Personal-Blog/` 就能看到效果

7. 满意之后，用 SourceTree：
   - **Commit**（提交到本地）
   - **Push**（推送到 GitHub）
   - 等一两分钟，GitHub Actions 自动构建，`https://xiuuuuuuuuuu.github.io/Personal-Blog/` 就会更新

## 添加封面图

在文章文件夹里放一张图片（比如 `cover.jpg`），然后在 `index.md` 的文件头里加一行：

```yaml
image: cover.jpg
```

图片会自动变成文章封面和分享缩略图。

## 修改头像

把新头像图片放到 `E:\MyBlog\assets\img\avatar.png` 覆盖原文件即可。

## 修改网站信息

打开 `E:\MyBlog\config\_default\config.toml`：

- `title` — 网站标题
- `locale` — 语言（`zh-cn` 是中文）

打开 `E:\MyBlog\config\_default\params.toml`：

- `sidebar.subtitle` — 侧边栏个人介绍
- `footer.since` — 建站年份

## 修改主题色

打开 `E:\MyBlog\assets\scss\custom.scss`，添加 CSS 样式即可覆盖主题默认颜色。

## 本地预览 vs 正式发布

| 操作 | 效果 |
|---|---|
| 修改文件 → 浏览器刷新 | 本地预览 `localhost:1313` 即时更新 |
| Commit + Push → 等几分钟 | 正式网站 `xiuuuuuuuuuu.github.io` 更新 |
