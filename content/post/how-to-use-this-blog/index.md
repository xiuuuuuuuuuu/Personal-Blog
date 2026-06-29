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

## 文章放哪里

所有文章统一放在 `E:\MyBlog\content\post\` 下，推荐用**文件夹 + index.md** 的结构（和现有文章一致）：

```
content/post/
└── my-unity-note/          ← 文件夹名随意，建议英文或拼音
    ├── index.md            ← 正文
    ├── cover.jpg           ← 可选：封面
    └── diagram.png         ← 可选：文中配图
```

如果你已经有一个 `.md` 文件，把它复制到新文件夹里的 `index.md`，再在文件最顶部补上 YAML 头（见下文）即可。

---

## 如何发布一篇文章

1. 打开 `E:\MyBlog\content\post` 文件夹
2. 创建一个新文件夹，比如 `my-first-post`
3. 在里面新建 `index.md`，按下面的格式写
4. 保存文件
5. 本地预览（见「本地预览 vs 正式发布」）
6. 满意之后，用 SourceTree **Commit** → **Push**，等 GitHub Actions 构建完成

### 基本模板

```markdown
---
title: 文章标题
description: 简短描述，会显示在摘要和分享卡片里
slug: my-first-post
date: 2026-06-28 00:00:00+0800
categories:
    - 分类名
tags:
    - 标签名
weight: 10
---

这里写文章正文，支持 Markdown 语法。
```

### 完整示例

```markdown
---
title: Unity 对象池实现
description: 简单实现一个通用对象池，支持预加载和回收
slug: unity-object-pool
date: 2026-06-29 10:00:00+0800
categories:
    - 技术
tags:
    - unity
    - object-pool
weight: 20
image: cover.jpg
---

## 为什么需要对象池

正文内容……
```

---

## 文件头字段说明

文件最顶部、被 `---` 包裹的部分叫 **front matter**，用来控制文章的元信息。

| 字段 | 是否必填 | 作用 |
|------|----------|------|
| `title` | 必填 | 文章标题 |
| `description` | 建议填 | 摘要，用于 SEO 和分享卡片 |
| `slug` | 建议填 | 文章 URL，如 `unity-object-pool` → `/post/unity-object-pool/` |
| `date` | 必填 | 创建 / 发布时间，**可以手动指定任意日期** |
| `categories` | 可选 | 分类，出现在侧边栏「分类」里 |
| `tags` | 可选 | 标签，关联技能树和标签筛选页 |
| `weight` | 可选 | 排序权重，**数字越小越靠前** |
| `image` | 可选 | 封面图文件名（放在同目录下） |

### 关于发布时间 `date`

你可以自己规定文章的创建时间，博客会按这个时间显示和排序：

```yaml
date: 2026-06-29 14:30:00+0800   # 2026年6月29日 14:30（东八区）
date: 2025-03-15 00:00:00+0800   # 也可以写成过去的日期
```

格式固定为：`年-月-日 时:分:秒+0800`（`+0800` 表示中国时区）。

### 关于排序 `weight`

首页和列表页的排序受 `weight` 影响，数字越小越靠前。例如 `weight: 1` 会比 `weight: 99` 更靠前。

---

## 标签与技能树

侧边栏的**技能树**三级节点，会链接到对应 **tag** 的筛选页。  
只有文章 front matter 里写了对应 tag，该技能才会变成可点击链接。

技能树配置在 `E:\MyBlog\config\_default\params.toml` 的 `[skillTree]` 段，例如：

```toml
{ name = "C#",  slug = "csharp" }
{ name = "对象池", slug = "object-pool" }
```

文章里的 `tags` 必须和配置里的 `slug` **完全一致**：

```yaml
tags:
    - csharp        # 对应技能树「编程语言 → C#」
    - object-pool   # 对应技能树「游戏框架 → 对象池」
```

一篇可以有多个 tag：

```yaml
tags:
    - unity
    - csharp
    - object-pool
```

还没有任何文章使用的 tag，在技能树里会显示为**灰色不可点击**（悬停提示「暂无文章」）。写了文章并加上对应 tag 后，会自动变为可点击。

---

## 添加封面图

在文章文件夹里放一张图片（比如 `cover.jpg`），然后在 front matter 里加一行：

```yaml
image: cover.jpg
```

图片会自动变成文章封面和分享缩略图。

## 添加文中配图

把图片放在文章同目录下，在正文里用相对路径引用：

```markdown
![对象池结构](./pool-diagram.png)
```

---

## 本地预览

打开 PowerShell，运行：

```powershell
cd E:\MyBlog
.\hugo.exe server
```

然后浏览器打开 `http://localhost:1313/Personal-Blog/`，改完 md 保存后刷新即可看到效果。

---

## 发布到线上

1. 用 SourceTree **Commit**（把新文件夹和 md 加进去）
2. **Push** 到 GitHub
3. 等一两分钟，GitHub Actions 自动构建
4. 正式网站：`https://xiuuuuuuuuuu.github.io/Personal-Blog/`

---

## 修改头像

把新头像图片放到 `E:\MyBlog\assets\img\avatar.png` 覆盖原文件即可。

## 修改网站信息

打开 `E:\MyBlog\config\_default\config.toml`：

- `title` — 网站标题
- `locale` — 语言（`zh-cn` 是中文）

打开 `E:\MyBlog\config\_default\params.toml`：

- `sidebar.subtitle` — 侧边栏个人介绍
- `footer.since` — 建站年份
- `[skillTree]` — 侧边栏技能树结构

## 修改主题色

打开 `E:\MyBlog\assets\scss\custom.scss`，添加 CSS 样式即可覆盖主题默认颜色。

---

## 本地预览 vs 正式发布

| 操作 | 效果 |
|---|---|
| 修改文件 → 浏览器刷新 | 本地预览 `localhost:1313` 即时更新 |
| Commit + Push → 等几分钟 | 正式网站 `xiuuuuuuuuuu.github.io` 更新 |

---

## 快速对照

| 你想控制 | 填哪个字段 |
|----------|------------|
| 创建 / 发布时间 | `date` |
| 出现在哪个技能下 | `tags`（与技能树 slug 一致） |
| 文章分类 | `categories` |
| 首页排序 | `weight`（越小越靠前） |
| URL 地址 | `slug` |
| 封面图 | `image` + 同目录放图片 |
