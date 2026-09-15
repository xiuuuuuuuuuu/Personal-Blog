---
title: "Unity TMP 转 Text 迁移工具"
description: "一个把 TextMeshProUGUI 批量迁移为 UnityEngine.UI.Text 的编辑器工具，支持字体映射、参数迁移、右键转换、当前场景批量转换和 Undo"
slug: tmp-to-text-migration-tool
date: 2026-09-16 00:35:00+0800
categories:
    - 技术
tags:
    - unity
    - editor
    - UI
    - TextMeshPro
weight: 19
---

最近写了一个小工具，用来把 Unity UI 里的 `TextMeshProUGUI` 批量转换成旧版 `UnityEngine.UI.Text`。

正常情况下我更推荐新项目继续使用 TMP，因为 TMP 的字体渲染、fallback、材质效果和富文本能力都更完整。但有些项目会遇到比较现实的迁移需求：旧 UI 代码只认 `Text`，目标平台或历史插件对 TMP 支持不好，或者某些资源包需要回退到旧版 UI 文本组件。手动一个个替换很容易漏参数，也很容易把字号、颜色、对齐和射线检测状态弄乱，于是就有了这个编辑器工具。

## 版本更新

### v1.1

1.1 版本在设置窗口里新增了批量转换区域：

```text
转换选中对象及子物体
转换当前场景所有 TMP
```

其中 `转换当前场景所有 TMP` 会扫描当前打开并已加载场景中的所有 `TextMeshProUGUI`，跳过 Project 里的持久化资源，并在正式转换前弹出确认框。它适合在字体映射和转换参数已经确认无误后，对整个场景做一次统一迁移。

### v1.0

1.0 版本提供基础迁移能力：支持选中对象及子物体转换、组件右键转换、菜单栏转换、字体映射、参数迁移和 Undo。这个版本更适合先在小范围 UI 节点上验证转换效果。

## 工具做了什么

这个工具的核心目标很简单：

1. 找到选中对象及其子物体上的 `TextMeshProUGUI`。
2. 记录常用显示参数。
3. 删除 TMP 组件。
4. 在同一个 GameObject 上添加 `UnityEngine.UI.Text`。
5. 把能迁移的参数尽量迁移过去。

当前会迁移的内容包括：

- 文本内容、颜色、字号
- 粗体、斜体
- 水平与垂直对齐
- Geometry Align
- Auto Size 的最小字号与最大字号
- Rich Text 开关
- Horizontal Overflow、Vertical Overflow
- Line Spacing
- Maskable
- Raycast Target
- 字体映射结果

转换操作接入了 Unity Undo，转换后如果发现不合适，可以直接撤销。

## 为什么字体需要单独处理

TMP 的字体类型是 `TMP_FontAsset`，旧版 Text 的字体类型是 `UnityEngine.Font`。这两个资源不能直接互相赋值，所以迁移时最麻烦的不是文本内容，而是字体。

工具里做了一层字体查找优先级：

```text
字体映射 > TMP_FontAsset.sourceFontFile > 默认 Text 字体 > Unity 内置字体
```

最稳的是手动配置字体映射。例如项目里有一个 `NotoSansSC SDF`，它实际来源于 `NotoSansSC.ttf`，那就把这个 TMP 字体资产映射到对应的普通字体文件。批量转换时工具会优先使用这张映射表。

如果 TMP 字体资产还保留着 `sourceFontFile`，工具也可以自动拿它作为兜底字体。这个能力很方便，但不能完全依赖它，因为有些 TMP 字体资产可能已经丢失或没有保存源字体引用。

## 使用方式

把脚本放到项目的 Editor 目录下：

```text
Assets/Editor/TMPToTextMigrationTool.cs
```

等待 Unity 编译完成后，可以从这里打开设置窗口：

```text
Tools > UI > TMP 转 Text 迁移设置
```

首次打开时，工具会自动创建设置资源：

```text
Assets/Editor/TMPToTextMigrationSettings.asset
```

在设置窗口里可以配置默认字体、字体映射、Overflow 行为、是否关闭 Raycast Target、是否保留 Auto Size 等选项。

1.1 版本实际转换有四种入口：

| 入口 | 作用 |
| --- | --- |
| Hierarchy 右击对象，选择 `将 TMP 转换为 Text` | 转换选中对象及所有子物体中的 TMP |
| 设置窗口点击 `转换选中对象及子物体` | 转换当前选中对象范围 |
| 设置窗口点击 `转换当前场景所有 TMP` | 转换当前已加载场景中的所有 TMP，执行前会弹确认框 |
| Inspector 右击 `TextMeshProUGUI` 组件，选择 `转换为旧版 Text` | 只转换当前组件 |
| 菜单栏 `Tools > UI > 将选中 TMP 转换为 Text` | 转换当前选中对象范围 |

## 主要实现思路

转换前，工具会先把 TMP 的关键字段记录到一个快照结构里：

```csharp
TMPTextSnapshot snapshot = TMPTextSnapshot.Capture(tmp, settings);
GameObject gameObject = tmp.gameObject;
```

然后通过 Undo 删除 TMP 组件，再添加旧版 Text：

```csharp
Undo.DestroyObjectImmediate(tmp);
Text text = Undo.AddComponent<Text>(gameObject);
snapshot.ApplyTo(text, settings);
```

这样做的好处是转换过程可以撤销，也不会因为组件删除后引用失效而丢掉原始参数。

对齐方式需要单独转换。TMP 的水平和垂直选项比旧版 Text 更细，工具会把 `HorizontalAlignmentOptions` 和 `VerticalAlignmentOptions` 合并成 `TextAnchor`。例如 Top + Left 会转换为 `UpperLeft`，Bottom + Right 会转换为 `LowerRight`，其余居中情况尽量落到对应的 Center 选项。

字体样式也做了一个简化映射：

```csharp
bool bold = (style & FontStyles.Bold) != 0;
bool italic = (style & FontStyles.Italic) != 0;
```

旧版 Text 只有 `Normal`、`Bold`、`Italic` 和 `BoldAndItalic`，所以 TMP 的更多样式不会完整保留。

## 迁移后的限制

这个工具是“尽量迁移常用 UI 文本参数”，不是把 TMP 的渲染能力完整复刻到旧版 Text。

以下能力无法完美迁移：

- TMP 字体 fallback
- TMP 材质、描边、渐变色
- TMP Sprite Asset 和 `<sprite>` 标签
- TMP 专属富文本标签
- 字距、词距、段距等高级排版参数
- TMP 的部分 Overflow、Masking 和 Linked Text 行为

所以它适合做批量回退和基础 UI 迁移。转换后如果是关键界面，还是需要逐个检查显示效果，尤其是字号、换行、溢出和中文字体。

## 推荐流程

比较稳的使用流程是：

1. 先打开 `Tools > UI > TMP 转 Text 迁移设置`。
2. 设置一个默认 Text 字体。
3. 保持 `使用 TMP 源字体兜底` 开启。
4. 对项目常用 TMP 字体添加字体映射。
5. 根据项目需要设置 Overflow、Maskable 和 Raycast Target。
6. 先在一个测试 Canvas 或单个 prefab 上转换。
7. 确认视觉没问题后，再对更大的 UI 节点批量转换。
8. 使用 1.1 版本时，可以在确认设置无误后点击 `转换当前场景所有 TMP` 做场景级迁移。

纯显示文本一般可以关闭 `Raycast Target`，避免转换后的文字挡住按钮、拖拽或点击事件。如果项目中有依赖文本接收射线的特殊交互，再针对那些对象单独处理。

## 下载

源码和完整使用说明放在下面。源码文件直接放入 Unity 项目的 `Assets/Editor/` 目录即可使用。

### v1.1

推荐使用 1.1 版本。它在 1.0 的基础上增加了设置窗口批量转换入口，并支持将当前场景中的所有 TMP 一次性转换为 Text。

<a href="./TMPToTextMigrationTool-v1.1.cs" download>下载 TMPToTextMigrationTool-v1.1.cs</a>

<a href="./TMP转Text迁移工具使用说明-v1.1.md" download>下载 TMP 转 Text 迁移工具使用说明 v1.1</a>

### v1.0

1.0 版本保留在这里，方便对照或回退。

<a href="./TMPToTextMigrationTool.cs" download>下载 TMPToTextMigrationTool.cs（v1.0）</a>

<a href="./TMP转Text迁移工具使用说明.md" download>下载 TMP 转 Text 迁移工具使用说明（v1.0）</a>
