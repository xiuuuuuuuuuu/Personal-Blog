# TMP 转 Text 迁移工具使用说明

版本：1.0

## 工具用途

这个工具用于把 UI 中的 `TextMeshProUGUI` 组件迁移为旧版 `UnityEngine.UI.Text` 组件。

它适合处理需要从 TMP 回退到旧版 Text 的项目，例如目标平台、旧 UI 系统、第三方插件或现有代码只支持 `Text` 的情况。

工具会尽量迁移 TMP 的常用显示参数，包括文字内容、颜色、字号、字体样式、对齐、自动字号、Rich Text、Overflow、Maskable 和 Raycast Target 等。但旧版 Text 和 TMP 的功能不是完全等价的，TMP 的材质、描边、fallback、sprite 标签和部分 TMP 专属富文本效果无法完美迁移。

## 安装方式

将脚本文件放到项目的 `Assets/Editor/` 目录下：

```text
Assets/Editor/TMPToTextMigrationTool.cs
```

如果项目中没有 `Editor` 文件夹，可以手动创建。

放入后等待 Unity 编译完成即可使用。目标项目需要安装 TextMesh Pro 包，因为工具依赖 `TMPro.TextMeshProUGUI` 和 `TMPro.TMP_FontAsset`。

## 打开设置界面

菜单路径：

```text
Tools > UI > TMP 转 Text 迁移设置
```

打开后会显示迁移设置窗口。首次打开时，工具会自动创建设置文件：

```text
Assets/Editor/TMPToTextMigrationSettings.asset
```

这个设置文件会保存字体映射和转换参数。

## 转换方式

### 方式一：右击对象转换

在 Hierarchy 中选中包含 TMP 文本的对象，右击对象，选择：

```text
将 TMP 转换为 Text
```

工具会转换当前选中对象及其所有子物体中的 `TextMeshProUGUI`。

### 方式二：组件右键转换

在 Inspector 中右击 `TextMeshProUGUI` 组件，选择：

```text
转换为旧版 Text
```

这种方式只转换当前这个 TMP 组件。

### 方式三：菜单栏转换

选中对象后，也可以使用：

```text
Tools > UI > 将选中 TMP 转换为 Text
```

## 参数说明

### 默认 Text 字体

当工具无法从字体映射或 TMP 源字体中找到可用字体时，会使用这里设置的字体。

旧版 `Text.font` 使用的是 `UnityEngine.Font`，而 TMP 使用的是 `TMP_FontAsset`，二者不能直接互相赋值。

### 使用 TMP 源字体兜底

如果开启，工具会尝试使用 `TMP_FontAsset.sourceFontFile` 作为转换后的 `Text.font`。

例如某个 TMP 字体资产是由 `NotoSansSC.ttf` 生成的，只要 TMP 资产里还保留这个源字体引用，工具就可以直接把 `NotoSansSC.ttf` 赋给旧版 Text。

建议保持开启。

### 关闭射线检测

如果开启，转换后的 `Text.raycastTarget` 会被设置为 `false`。

这可以避免文字挡住按钮、拖拽、点击等 UI 事件。一般情况下，纯显示文本建议关闭射线检测。

### 启用 Maskable

控制转换后的 `Text.maskable`。

如果开启，Text 会受到父级 `Mask` 或 `RectMask2D` 的裁剪影响。

如果关闭，Text 不参与 UI Mask 裁剪。需要注意，具体显示效果还会受到 Canvas、父级组件和材质等因素影响。

### 迁移 TMP Auto Size

如果开启，并且原 TMP 开启了 Auto Size，工具会给转换后的 Text 开启：

```csharp
resizeTextForBestFit = true
```

同时迁移 TMP 的最小字号和最大字号。

旧版 Text 的自动字号算法和 TMP 不完全一样，所以转换后可能仍需要手动微调字号或文本框尺寸。

### 启用 Rich Text

如果开启，转换后的 `Text.supportRichText` 会根据原 TMP 的 Rich Text 状态启用。

旧版 Text 支持部分基础富文本标签，例如：

```text
<b>
<i>
<color>
<size>
```

但不支持 TMP 专属标签，例如：

```text
<sprite>
部分 TMP 材质、描边、字重、样式标签
```

### 水平 Overflow

控制转换后的 `Text.horizontalOverflow`。

可选值通常包括：

```text
Wrap
Overflow
```

`Wrap` 表示超出宽度时自动换行。

`Overflow` 表示允许文字横向超出 RectTransform 继续显示。

如果你遇到“TMP 能显示，转成 Text 后同样框里显示不出来”的情况，通常建议设置为 `Overflow`。

### 垂直 Overflow

控制转换后的 `Text.verticalOverflow`。

可选值通常包括：

```text
Truncate
Overflow
```

`Truncate` 表示超出高度的部分会被截断。

`Overflow` 表示允许文字纵向超出 RectTransform 继续显示。

如果希望更接近 TMP 超框仍可见的表现，建议设置为 `Overflow`。

### 字体映射

字体映射是一张对照表，用来告诉工具：

```text
某个 TMP_FontAsset 转成 Text 时，应该使用哪个 UnityEngine.Font
```

例如：

```text
LiberationSans SDF -> LiberationSans
NotoSansSC SDF -> NotoSansSC.ttf
TitleFont SDF -> TitleFont.ttf
```

转换时，字体查找优先级如下：

```text
字体映射 > TMP_FontAsset.sourceFontFile > 默认 Text 字体 > Unity 内置字体
```

字体映射优先级最高，因为它是人工指定的结果，最明确、最可靠。

### 添加选中 TMP 字体

先在 Hierarchy 中选中一个带 `TextMeshProUGUI` 的对象，再点击这个按钮。

工具会读取该对象当前使用的 TMP 字体，并自动添加一条字体映射。

如果该 TMP 字体有 `sourceFontFile`，会自动填入对应的 Text 字体。否则需要手动指定 `Text 字体`。

### 保存设置

保存当前设置到：

```text
Assets/Editor/TMPToTextMigrationSettings.asset
```

建议修改字体映射或转换参数后点击一次保存。

## 转换后会迁移的内容

工具会尽量迁移以下内容：

- 文本内容
- 文本颜色
- 字体
- 字号
- 最小字号
- 最大字号
- 粗体和斜体
- 水平和垂直对齐
- Geometry Align
- Auto Size
- Rich Text
- Horizontal Overflow
- Vertical Overflow
- Line Spacing
- Maskable
- Raycast Target

## 无法完美迁移的内容

以下 TMP 能力无法完整迁移到旧版 Text：

- TMP 字体资产本身
- TMP 字体 fallback
- TMP 材质
- TMP 描边
- TMP 渐变色
- TMP Sprite Asset 和 `<sprite>` 标签
- TMP 部分富文本标签
- 字距、词距、段距等高级排版参数
- TMP 的 Overflow、Masking、Linked Text 等高级模式

转换后如果视觉要求很高，仍建议逐个检查重点 UI。

## 推荐使用流程

1. 打开 `Tools > UI > TMP 转 Text 迁移设置`。
2. 设置一个默认 Text 字体。
3. 勾选 `使用 TMP 源字体兜底`。
4. 根据项目需求设置 `关闭射线检测`、`启用 Maskable` 和 Overflow。
5. 对常用 TMP 字体配置字体映射。
6. 在 Hierarchy 中右击对象，选择 `将 TMP 转换为 Text`。
7. 检查转换后的 UI 显示效果。

## 常见问题

### 为什么 TMP 字体不能直接赋给 Text？

因为 TMP 使用的是 `TMP_FontAsset`，旧版 Text 使用的是 `UnityEngine.Font`。

它们是两种不同类型的资源，所以需要通过字体映射或 TMP 源字体找到对应的普通字体。

### 为什么转换后文字位置或大小和 TMP 不完全一样？

TMP 和旧版 Text 的排版系统不同，字号计算、行距、对齐、字形度量和自动字号算法都不完全一致。

工具只能尽量迁移常用参数，无法保证像素级一致。

### 为什么设置了 Overflow 还是被裁剪？

`Text.horizontalOverflow` 和 `Text.verticalOverflow` 只控制 Text 自身的超框行为。

如果父级对象有 `Mask`、`RectMask2D` 或其他裁剪逻辑，文字仍可能被父级裁掉。

### 这个工具会删除原 TMP 组件吗？

会。

转换时工具会先记录 TMP 的常用参数，然后删除 `TextMeshProUGUI`，再在同一个 GameObject 上添加 `UnityEngine.UI.Text`。

操作支持 Unity Undo，可以使用撤销恢复。
