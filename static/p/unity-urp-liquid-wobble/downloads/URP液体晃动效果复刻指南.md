# Unity URP 容器液体晃动效果复刻指南

## 1. 文档目的

本文档用于指导另一个 AI 或开发者在 Unity URP 项目中复刻“杯中液体随容器移动和旋转而晃动”的视觉效果。

该效果不是流体物理模拟。它由以下两部分配合完成：

1. URP Shader 根据世界空间液面裁切一个封闭网格，并绘制液体侧面、顶部、泡沫线和边缘光。
2. C# 脚本计算容器的线速度和角速度，将运动转换为逐渐衰减的液面倾斜参数。

完成后的效果应满足：

- 容器静止时，液面保持世界空间水平。
- 容器移动或旋转时，液面产生有惯性的往复晃动。
- 停止运动后，液面逐渐恢复平静。
- 可调整液位、颜色、泡沫、波纹频率、晃动幅度与恢复速度。
- 多个液体实例之间的动态参数不会互相覆盖。

## 2. 已验证环境

- Unity：`2022.3.62f3c1`
- 渲染管线：Universal Render Pipeline（URP）
- URP 包版本：`14.0.12`
- Shader 类型：手写 URP HLSL，非 Shader Graph

原 Minions Art 教程使用 Built-in Render Pipeline。其旧式 CG Shader 不能直接用于本项目，必须改写为 URP Shader。C# 的速度驱动思路可以保留。

## 3. 当前实现文件

| 文件 | 作用 |
| --- | --- |
| `Assets/LiquidDemo/LiquidURP.shader` | 液位裁切、液体着色、顶部、泡沫、边缘光与动态波纹 |
| `Assets/LiquidDemo/LiquidWobble.cs` | 计算线速度、角速度、衰减振荡并向 Shader 传参 |
| `Assets/LiquidDemo/LiquidDemoMover.cs` | 仅用于演示，自动移动和倾斜杯子 |
| `Assets/LiquidDemo/Liquid.mat` | 液体材质 |
| `Assets/LiquidDemo/Glass.mat` | URP 透明玻璃材质 |
| `Assets/LiquidDemo/Editor/LiquidDemoAutoSetup.cs` | 自动配置演示场景，也提供手动菜单入口 |
| `Assets/Scenes/LiquidDemo.unity` | 已配置好的演示场景 |

若当前工程保留了这些文件，优先复用或检查现有实现，不要重复创建同名脚本和材质。

## 4. 场景对象结构

推荐层级：

```text
Cup                         根对象；容器外观和整体运动对象
└── Liquid                  子对象；封闭的液体体积网格
```

演示场景中两个对象都可以使用 Unity 自带的 Cylinder：

- `Cup`：外层 Cylinder，使用 `Glass.mat`。
- `Liquid`：内层 Cylinder，作为 `Cup` 的子对象，使用 `Liquid.mat`。
- `Liquid.localPosition = (0, 0, 0)`。
- `Liquid.localRotation = (0, 0, 0)`。
- `Liquid.localScale = (0.88, 0.95, 0.88)`，使其位于杯子内部。
- 禁用 `Liquid` 的 Collider；外层杯子的 Collider 可保留。
- `Liquid` 必须是封闭网格，否则无法利用背面伪造液体顶部截面。

正式项目可将 Cylinder 替换成杯子或瓶子模型，但液体仍应是独立、封闭、与容器内腔相匹配的网格。

## 5. 组件配置

### Cup

- `MeshFilter`
- `MeshRenderer`，材质为 `Glass.mat`
- 可选 Collider
- 演示时挂载 `LiquidDemoMover`
- 实际游戏中移除或禁用 `LiquidDemoMover`，改由玩家、动画、Tween 或物理系统移动

`LiquidDemoMover` 默认参数：

| 参数 | 默认值 | 含义 |
| --- | ---: | --- |
| Animate | true | 是否自动演示 |
| Speed | 1.25 | 移动动画速度 |
| Move Distance | 1.15 | 水平移动距离 |
| Tilt Angle | 16 | 最大倾斜角 |

### Liquid

- `MeshFilter`
- `MeshRenderer`，材质为 `Liquid.mat`
- `LiquidWobble`
- Collider 禁用

`LiquidWobble` 默认参数：

| 参数 | 默认值 | 含义 |
| --- | ---: | --- |
| Fill Amount | 0.62 | 归一化液位，范围 0～1 |
| Max Wobble | 0.10 | 最大液面倾斜量 |
| Wobble Speed | 2.2 | 振荡频率 |
| Recovery | 2.0 | 停止运动后的衰减速度 |
| Motion Sensitivity | 0.035 | 对位移和旋转的敏感度 |

## 6. Shader 参数契约

C# 与 Shader 必须使用完全相同的属性名：

| Shader 属性 | 类型 | 设置方 | 作用 |
| --- | --- | --- | --- |
| `_FillPosition` | Vector | C# 每帧设置 | 世界空间液面基准点 |
| `_WobbleX` | Float | C# 每帧设置 | X 方向运动造成的液面倾斜 |
| `_WobbleZ` | Float | C# 每帧设置 | Z 方向运动造成的液面倾斜 |
| `_BaseColor` | Color | 材质 | 液体主体颜色与透明度 |
| `_TopColor` | Color | 材质 | 液面顶部颜色 |
| `_FoamColor` | Color | 材质 | 液面边缘颜色 |
| `_FoamWidth` | Float | 材质 | 泡沫线宽度 |
| `_RimColor` | Color | 材质 | 侧面边缘光颜色和强度 |
| `_RimPower` | Float | 材质 | Fresnel 边缘光指数 |
| `_WaveFrequency` | Float | 材质 | 液面小波纹的空间频率 |
| `_WaveAmplitude` | Float | 材质 | 液面小波纹幅度 |

动态参数必须通过 `MaterialPropertyBlock` 写入 Renderer。不要使用 `renderer.sharedMaterial.SetFloat()`，否则共用同一材质的多个容器会互相覆盖晃动参数，并可能污染材质资源。

## 7. Shader 实现原理

### 7.1 URP Pass 基本要求

SubShader 至少包含：

```hlsl
Tags
{
    "RenderType" = "Transparent"
    "Queue" = "Transparent-10"
    "RenderPipeline" = "UniversalPipeline"
}
```

Pass 使用：

```hlsl
Tags { "LightMode" = "UniversalForward" }
Cull Off
ZWrite On
Blend SrcAlpha OneMinusSrcAlpha
```

需要包含：

```hlsl
#include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
```

使用 URP 提供的转换函数：

- `GetVertexPositionInputs()`：取得裁切空间和世界空间坐标。
- `TransformObjectToWorldNormal()`：将法线转换到世界空间。
- `GetWorldSpaceNormalizeViewDir()`：取得观察方向。
- `ComputeFogFactor()` 与 `MixFog()`：兼容场景雾。

### 7.2 世界空间水平液面

顶点阶段传递每个片元的世界坐标 `positionWS`。

片元阶段先计算相对液面位置：

```hlsl
float3 relativePosition = input.positionWS - _FillPosition.xyz;
```

液面距离公式：

```hlsl
float surfaceDistance = relativePosition.y
                      + relativePosition.x * _WobbleX
                      + relativePosition.z * _WobbleZ
                      + wave;
```

保留液面以下的像素：

```hlsl
clip(-surfaceDistance);
```

因为判断基于世界空间 Y，所以即使容器自身倾斜，静止时液面仍保持世界空间水平。

### 7.3 动态波纹

波纹只在发生晃动时明显出现：

```hlsl
float movement = saturate(abs(_WobbleX) + abs(_WobbleZ));
float wave = sin(
    (relativePosition.x + relativePosition.z) * _WaveFrequency
    + _Time.y * 2.0
) * _WaveAmplitude * movement;
```

### 7.4 泡沫边缘

根据片元到裁切液面的距离形成窄边：

```hlsl
float foam = 1.0 - smoothstep(0.0, _FoamWidth, -surfaceDistance);
half4 sideColor = lerp(_BaseColor, _FoamColor, foam);
```

### 7.5 边缘光

通过世界法线与观察方向计算 Fresnel：

```hlsl
half rim = pow(
    1.0h - saturate(dot(normalDirection, viewDirection)),
    _RimPower
);
sideColor.rgb += _RimColor.rgb * rim * _RimColor.a;
```

### 7.6 顶部截面假象

必须设置 `Cull Off`，并在片元入口读取 `SV_IsFrontFace`：

```hlsl
half4 Frag(Varyings input, bool isFrontFace : SV_IsFrontFace) : SV_Target
```

根据正面或背面选择颜色：

```hlsl
half4 finalColor = isFrontFace
    ? sideColor
    : lerp(_TopColor, _FoamColor, foam * 0.65);
```

这是视觉近似，不会真的生成裁切平面的几何。对于凸形、封闭的杯内液体网格效果最好；复杂凹形容器可能需要额外的顶部网格或更高级的多 Pass 方案。

## 8. C# 晃动算法

### 8.1 每帧运动量

保存上一帧位置和旋转：

```csharp
Vector3 velocity = (transform.position - previousPosition) / deltaTime;
Quaternion delta = currentRotation * Quaternion.Inverse(previousRotation);
```

将旋转差转换为 Angle-Axis，并除以 `deltaTime` 得到角速度。角度超过 180° 时应减去 360°，避免旋转跨界造成突变。

### 8.2 将运动注入晃动

实现使用以下映射：

```csharp
wobbleImpulseX += (-velocity.x + angularVelocity.z * 0.18f)
                  * motionSensitivity;
wobbleImpulseZ += (-velocity.z - angularVelocity.x * 0.18f)
                  * motionSensitivity;
```

然后将两个 impulse 限制在 `[-maxWobble, maxWobble]`。

### 8.3 指数衰减与正弦振荡

```csharp
float damping = Mathf.Exp(-recovery * deltaTime);
wobbleImpulseX *= damping;
wobbleImpulseZ *= damping;

phase += deltaTime * wobbleSpeed * Mathf.PI * 2f;
float pulse = Mathf.Sin(phase);

float wobbleX = wobbleImpulseX * pulse;
float wobbleZ = wobbleImpulseZ * pulse;
```

指数衰减使恢复速度基本不受帧率影响；正弦波产生来回摆动的惯性感。

### 8.4 液位位置

从 `MeshFilter.sharedMesh.bounds` 获取本地 Bounds：

```csharp
Bounds bounds = meshFilter.sharedMesh.bounds;
Vector3 centerWS = transform.TransformPoint(bounds.center);
float worldHeight = bounds.size.y * Mathf.Abs(transform.lossyScale.y);
float heightOffset = Mathf.Lerp(
    -worldHeight * 0.5f,
     worldHeight * 0.5f,
     fillAmount
);
Vector3 fillPosition = centerWS + Vector3.up * heightOffset;
```

将 `fillPosition` 写入 `_FillPosition`。这种实现以 Mesh Bounds 中心为基准，不要求模型 Pivot 位于几何中心。

### 8.5 MaterialPropertyBlock 正确生命周期

不要只依赖非序列化字段的初始化表达式。Unity 编辑器发生 Domain Reload 后，该托管对象可能为空。

正确方式是按需创建：

```csharp
[System.NonSerialized]
private MaterialPropertyBlock properties;

private void EnsurePropertyBlock()
{
    if (properties == null)
        properties = new MaterialPropertyBlock();
}
```

在调用以下 API 前必须先执行 `EnsurePropertyBlock()`：

```csharp
targetRenderer.GetPropertyBlock(properties);
properties.SetVector(FillPositionId, fillPosition);
properties.SetFloat(WobbleXId, wobbleX);
properties.SetFloat(WobbleZId, wobbleZ);
targetRenderer.SetPropertyBlock(properties);
```

若忽略该处理，可能出现：

```text
ArgumentNullException: Value cannot be null.
Parameter name: dest
UnityEngine.Renderer.GetPropertyBlock(...)
```

## 9. 玻璃材质建议

外层容器可使用 `Universal Render Pipeline/Lit`：

- Surface Type：Transparent
- Base Color：浅蓝或白色
- Alpha：约 `0.10～0.25`
- Smoothness：约 `0.85～0.95`
- Metallic：约 `0～0.1`
- Render Queue：`3000`
- 关闭阴影投射

液体材质使用 Render Queue `2990`，使其通常先于玻璃绘制。透明排序仍属于近似方案；若正式模型出现排序问题，应根据相机与模型结构调整 Render Queue，或将玻璃拆成前后两部分。

## 10. 自动配置逻辑

当前工程中的 `LiquidDemoAutoSetup` 会在打开名为 `LiquidDemo` 的场景后执行以下操作：

1. 寻找根级 `Cup`，找不到则寻找根级 `Cylinder`。
2. 在它下面寻找 `Liquid`，找不到则寻找子级 `Cylinder`。
3. 将两个对象重命名为 `Cup` 和 `Liquid`。
4. 调整液体的本地位置、旋转和缩放。
5. 创建或复用 `Glass.mat` 与 `Liquid.mat`。
6. 分配材质并关闭两个 Renderer 的阴影投射。
7. 禁用液体 Collider。
8. 挂载 `LiquidWobble` 和 `LiquidDemoMover`。
9. 保存场景和资源。

也可以手动执行菜单：

```text
Tools > Liquid Demo > Configure Current Scene
```

将该功能移植到正式项目时，自动配置脚本不是运行时必需项，可以删除；运行时只需要液体 Shader、液体材质和 `LiquidWobble`。

## 11. 推荐复刻步骤

另一个 AI 在新 URP 项目中应按以下顺序实施：

1. 确认项目确实使用 URP，并记录 Unity 与 URP 版本。
2. 创建一个独立测试场景，避免影响正式场景。
3. 创建外层容器和内部封闭液体网格，建立 `Cup/Liquid` 层级。
4. 创建透明 URP Lit 玻璃材质并赋给 `Cup`。
5. 创建 URP HLSL 液体 Shader，严格实现第 6、7 节的参数契约与裁切逻辑。
6. 创建液体材质并赋给 `Liquid`。
7. 创建运动脚本，严格实现第 8 节的速度、衰减、振荡和液位计算。
8. 使用 `MaterialPropertyBlock` 动态参数，并实现 Domain Reload 后的按需重建。
9. 创建一个自动移动测试脚本，或在 Play 模式手动移动容器。
10. 按第 12 节验收；确认无误后再接入正式模型和正式运动系统。

## 12. 验收清单

### 编译与资源

- [ ] Console 中没有 C# 编译错误。
- [ ] 液体 Shader 没有编译错误，材质不是粉色。
- [ ] 项目仍绑定 URP Pipeline Asset。
- [ ] `Liquid` 的 Renderer 使用液体材质。
- [ ] `Cup` 的 Renderer 使用透明玻璃材质。

### 静止表现

- [ ] 能看到液体主体。
- [ ] 液位可通过 `Fill Amount` 调整。
- [ ] 静止并倾斜杯子后，液面仍趋向世界空间水平。
- [ ] 能看到液面顶部或顶部截面的视觉假象。
- [ ] 泡沫线紧贴液面边缘。

### 运动表现

- [ ] 杯子水平移动时，液面向反方向产生惯性倾斜。
- [ ] 杯子旋转时，液面产生相应晃动。
- [ ] 停止运动后，振幅逐渐衰减至零。
- [ ] 修改 `Max Wobble`、`Recovery`、`Motion Sensitivity` 后效果符合预期。
- [ ] 暂停时间或编辑器重新加载脚本后，不出现 NaN 或空引用异常。

### 多实例

- [ ] 复制两套杯子后，每个液体实例独立晃动。
- [ ] 一个杯子的晃动不会改变另一个杯子的参数。
- [ ] 材质资源本身不会在 Play 模式被动态参数污染。

## 13. 常见问题

### 材质变成粉色

原因通常是仍在使用 Built-in Shader、URP include 路径错误，或 Shader 编译失败。确认 SubShader 包含 `RenderPipeline = UniversalPipeline`，并检查 Console 的第一条 Shader 错误。

### 整个 Cylinder 都被显示，没有液位裁切

检查：

- `_FillPosition` 是否每帧传入。
- Shader 属性名是否与 C# 完全一致。
- `clip(-surfaceDistance)` 的正负号是否正确。
- `MaterialPropertyBlock` 是否最终通过 `Renderer.SetPropertyBlock()` 写回。

### 液体完全看不见

先将 Fill Amount 设置为 `0.5`，确认液体材质已分配，然后临时把 `_BaseColor.a` 调到 1。若仍不可见，检查裁切方向和网格 Bounds。

### 液面跟着杯子一起倾斜

说明液面判断很可能使用了 Object Space。应使用 `positionWS` 与世界空间 `_FillPosition` 计算高度，而不是直接使用模型本地 Y。

### 晃动太剧烈或穿出杯子

降低：

- `Max Wobble`
- `Motion Sensitivity`
- Shader 的 `_WaveAmplitude`

正式项目还应根据容器宽高限制最大倾斜量。

### 异形杯中液位不准确

当前 `Fill Amount` 按 Mesh Bounds 高度线性映射，不等于真实体积百分比。异形容器若需要体积准确，应预计算“填充高度到体积”的曲线或查找表。

### 顶部截面在复杂模型中破碎

当前方案依赖封闭凸网格的背面显示。对于凹形容器、带把手结构或复杂拓扑，应单独提供简化的液体网格，或实现额外的液面平面/Stencil/多 Pass 方案。

## 14. 当前方案边界

本效果只负责视觉表现，不包含：

- 真实流体碰撞与压力。
- 液体从杯口倒出。
- 飞溅粒子和液滴分裂。
- 多容器之间的液体转移。
- 异形容器中的严格体积守恒。
- 透明物体排序的所有极端情况。

若需求扩展到倒水或流体交互，应将当前 Shader 作为容器内液体的基础表现，再叠加粒子、VFX Graph、液柱网格或专用流体模拟系统。

## 15. 实现原则总结

复刻该效果最重要的五点：

1. 液体使用独立、封闭的内部网格。
2. 液位裁切在世界空间完成，保证静止液面水平。
3. 线速度和角速度只负责驱动晃动，随后通过正弦波和指数衰减模拟惯性。
4. 每个 Renderer 使用 `MaterialPropertyBlock` 保存动态参数。
5. `MaterialPropertyBlock` 必须能在 Unity Domain Reload 后按需重建。

只要严格保持 Shader 属性契约、坐标空间和脚本生命周期处理，即可在其他 Unity URP 项目中复刻同类效果。
