---
title: "动画系统：Animator"
description: "Unity Animator 学习笔记：有限状态机、Animator Controller、状态、过渡、参数、Layer、Animator 组件参数与代码控制"
slug: animation-system-animator
date: 2026-09-02 22:20:00+0800
categories:
    - 技术
tags:
    - unity
    - animation
weight: 34
---

## Animator 是什么

`Animator` 是 Unity 新动画系统中的动画器组件，负责根据 `Animator Controller` 播放和切换动画状态。`Animation` 窗口主要编辑单个动画片段，而 `Animator` 关注的是多个动画片段之间如何组织、如何切换、如何由参数驱动。

可以把它理解成：

- `AnimationClip`：一个具体动作，例如 Idle、Run、Attack。
- `Animator Controller`：动画状态机资源，描述有哪些状态、状态之间如何切换。
- `Animator` 组件：挂在 GameObject 上，运行时读取 Animator Controller 并真正播放动画。

## 有限状态机

有限状态机（Finite State Machine，FSM）是一种用有限个状态、状态之间的转移条件和转移动作描述行为逻辑的模型。

在游戏里，角色通常会有这些状态：

- 站立
- 走路
- 跑步
- 跳跃
- 攻击
- 防守
- 死亡

这些状态数量是有限的，角色在同一时刻通常处于其中某一个状态。当条件满足时，角色从一个状态切换到另一个状态，例如“速度大于 0”时从 Idle 切到 Walk，“按下攻击键”时从 Idle 或 Run 切到 Attack。

Animator Controller 本质上就是 Unity 为动画播放提供的一套可视化有限状态机。

## Animator Controller

`Animator Controller` 是一个动画控制器资源。它保存状态机数据，包括：

- 有哪些动画状态。
- 每个状态播放哪个 Motion，通常是 AnimationClip。
- 哪个状态是默认状态。
- 状态之间有哪些过渡。
- 过渡需要满足哪些条件。
- 使用哪些参数控制状态切换。
- 是否使用动画层、Avatar Mask、IK 等高级功能。

Animator Controller 必须通过 `Animator` 组件挂到对象上，才能驱动该对象播放动画。

## 打开 Animator 窗口

菜单路径：

```text
Window > Animation > Animator
```

常用方式：

- 双击 `Animator Controller` 资源打开。
- 选中带有 `Animator` 组件的对象，再打开 Animator 窗口查看当前控制器。

## Animator 窗口结构

### 左侧面板

左侧面板主要有两个页签。

| 页签 | 作用 |
| --- | --- |
| Layers | 动画层。用于把动画分层播放，不同层可以有不同权重和遮罩。 |
| Parameters | 参数列表。用于创建控制状态切换的参数，例如 Float、Int、Bool、Trigger。 |

其他控件：

- `+`：添加 Layer 或 Parameter。
- 齿轮按钮：设置当前 Layer。
- 眼睛图标：显示或隐藏左侧面板。

### 右侧状态机编辑区

右侧网格区域用于编辑状态和状态之间的过渡。

常见元素：

| 元素 | 含义 |
| --- | --- |
| Entry | 状态机入口。进入该层状态机时，从 Entry 指向的默认状态开始播放。 |
| Exit | 状态机出口。常用于子状态机或需要退出当前状态机流程的情况。 |
| Any State | 任意状态。表示可以从当前层任意状态切换到目标状态。 |
| 橙色状态 | 默认状态。进入状态机后首先播放。 |
| 灰色状态 | 普通动画状态。 |
| 箭头连线 | Transition，表示两个状态之间可以切换。 |

状态矩形的名称可以自由修改。默认情况下，拖入 AnimationClip 创建状态时，状态名通常和动画文件名一致，但它们不是同一个东西：状态名可以改，AnimationClip 文件名也可以改，二者不必完全相同。

## 添加动画状态

### 自动添加

通过 Animation 窗口给对象创建新的动画片段时，Unity 通常会自动创建或更新 Animator Controller，并把新动画片段添加为一个状态。

适合刚开始给对象制作动画时使用。

### 拖入 AnimationClip

可以直接把 `.anim` 动画片段拖进 Animator 窗口。Unity 会自动创建一个播放该片段的状态。

注意：

- 新动画系统使用的是 Animator + Animator Controller。
- 老动画系统的 Animation 资源拖入时可能会出现兼容性警告。

### 手动创建状态

也可以在 Animator 窗口中右键创建状态，再在 Inspector 中给状态关联 Motion。

常见方式：

| 操作 | 作用 |
| --- | --- |
| Create State > Empty | 创建空状态，之后手动指定 Motion。 |
| Create State > From New Blend Tree | 创建 Blend Tree 状态。 |
| 拖入 AnimationClip | 快速创建一个已绑定动画片段的状态。 |

## 设置默认状态

默认状态是进入该层状态机后首先播放的状态。它通常显示为橙色，并由 `Entry` 指向。

设置方法：

1. 在 Animator 窗口中右键某个状态。
2. 选择 `Set as Layer Default State`。

常见默认状态：

- 角色：Idle。
- UI：Normal 或 Hidden。
- 机关：Closed 或 Off。

## 添加状态过渡

状态之间必须有过渡连线，Unity 才知道它们可以切换。

创建过渡：

1. 右键起始状态。
2. 选择 `Make Transition`。
3. 点击目标状态完成连接。
4. 选中过渡连线，在 Inspector 中设置过渡参数和切换条件。

没有连线的两个状态默认不会互相切换，除非代码直接调用 `Animator.Play`、`CrossFade` 等 API。

## Animator Parameters

`Parameters` 是 Animator Controller 中用于驱动状态切换的参数。代码可以修改这些参数，Transition 根据参数条件判断是否切换状态。

参数类型：

| 类型 | 含义 | 常见用途 |
| --- | --- | --- |
| Float | 浮点数，可以与阈值做大于或小于比较。 | 速度、方向、混合值。 |
| Int | 整数，可以做大于、小于、等于、不等于比较。 | 武器编号、状态编号、连招段数。 |
| Bool | 布尔值，只有 true / false。 | 是否移动、是否在地面、是否瞄准。 |
| Trigger | 触发器。被触发并用于切换后，通常会自动重置。 | 攻击、跳跃、受击、死亡等一次性动作。 |

多个条件写在同一条 Transition 上时，需要同时满足才会发生切换。

## Transition 过渡参数

选中两个状态之间的过渡线后，可以在 Inspector 中设置过渡参数。它们决定什么时候切换、切换多久、是否允许被其他过渡打断。

| 参数 | 作用 |
| --- | --- |
| Has Exit Time | 是否等待源状态播放到指定退出时间后再允许切换。开启后，即使条件已经满足，也要等到 Exit Time。 |
| Exit Time | 退出时间。通常按源动画的归一化时间理解，`1` 表示播放完一轮，`0.5` 表示播放到一半。 |
| Fixed Duration | 决定 Transition Duration 使用秒还是归一化比例。开启时按秒计算，关闭时按源状态时长比例计算。 |
| Transition Duration | 过渡混合时长。值越大，两个动画混合越久；值越小，切换越干脆。 |
| Transition Offset | 目标状态从哪个时间点开始播放。常用于让切入目标动画时跳过开头一段。 |
| Interruption Source | 当前过渡是否能被其他过渡打断，以及允许哪些来源打断。 |
| Ordered Interruption | 开启后，打断会按过渡列表顺序判断；关闭后更宽松。 |
| Conditions | 切换条件列表。由 Parameters 中的参数组成。 |

如果动画切换感觉有延迟，优先检查：

- 是否勾选了 `Has Exit Time`。
- `Exit Time` 是否太靠后。
- `Transition Duration` 是否太长。
- Conditions 是否没有及时满足。

## Layer 动画层

`Layers` 用于让一个 Animator Controller 分层播放动画。上层动画可以覆盖或叠加下层动画。

常见用途：

- 下半身播放跑步，上半身播放攻击。
- 基础层播放角色移动，额外层播放受击、瞄准、持枪。
- UI 基础状态和局部特效分层控制。

常见 Layer 参数：

| 参数 | 作用 |
| --- | --- |
| Weight | 当前层权重。权重越高，对最终动画结果影响越大。 |
| Mask | Avatar Mask。限制该层影响哪些身体部位或 Transform。 |
| Blending | 混合模式。常见为 Override 和 Additive。 |
| Sync | 同步其他层的状态机结构。 |
| IK Pass | 是否让该层参与 IK 计算。 |

基础层通常叫 `Base Layer`，权重固定为 1。添加新层后，如果想让它真正影响动画，需要注意权重、Mask 和 Blending 设置。

## Animator 组件参数

`Animator` 组件挂在 GameObject 上，负责运行 Animator Controller。

| 参数 | 作用 |
| --- | --- |
| Controller | 绑定的 Animator Controller。没有控制器时，Animator 不知道要播放哪套状态机。 |
| Avatar | 角色骨骼映射信息。Humanoid 角色通常需要 Avatar；普通物体动画可以不关注。 |
| Apply Root Motion | 是否应用动画中的根运动。开启后，角色位移和旋转可以由动画本身驱动。 |
| Update Mode | Animator 更新模式。 |
| Culling Mode | Animator 剔除模式，用于控制对象不可见时是否继续更新动画。 |

### Update Mode

| 模式 | 作用 |
| --- | --- |
| Normal | 正常更新，跟随游戏时间。大多数情况使用它。 |
| Animate Physics | 配合物理更新，适合动画影响刚体或需要和物理更同步的情况。 |
| Unscaled Time | 使用不受 `Time.timeScale` 影响的时间，适合暂停菜单、UI 动画等。 |

### Culling Mode

| 模式 | 作用 |
| --- | --- |
| Always Animate | 始终更新动画，即使对象不在摄像机视野内。最稳定，但开销较高。 |
| Cull Update Transforms | 不可见时停止写入 Transform、IK 等结果，但仍保留部分 Animator 更新。 |
| Cull Completely | 不可见时完全停止动画更新。性能最好，但再次可见时要注意状态连续性。 |

## 用代码控制 Animator

代码控制状态机的核心思路是：先拿到 `Animator` 组件，再修改 Parameters 中定义好的参数，让 Transition 根据条件完成切换。

```csharp
using UnityEngine;

public class PlayerAnimation : MonoBehaviour
{
    private Animator animator;

    private void Awake()
    {
        animator = GetComponent<Animator>();
    }
}
```

### 设置参数

```csharp
animator.SetFloat("Speed", 3.5f);
animator.SetInteger("WeaponId", 1);
animator.SetBool("IsGrounded", true);
animator.SetTrigger("Attack");
```

### 读取参数

```csharp
float speed = animator.GetFloat("Speed");
int weaponId = animator.GetInteger("WeaponId");
bool isGrounded = animator.GetBool("IsGrounded");
```

### 重置 Trigger

Trigger 常用于一次性动作，但有时为了避免残留触发，可以手动重置。

```csharp
animator.ResetTrigger("Attack");
```

### 直接播放状态

```csharp
animator.Play("Idle");
```

`Play` 会按状态名直接播放动画状态。它绕过了参数和 Transition 条件，除非有明确需求，否则一般优先使用参数驱动状态机。

需要注意：状态名不一定等于动画文件名。AnimationClip 拖进 Animator 时，状态名默认和动画名一致，但后续可以单独修改。

## 常用流程总结

制作一个简单 Animator 状态机：

1. 准备多个 AnimationClip，例如 Idle、Run、Attack。
2. 创建或打开 Animator Controller。
3. 将 AnimationClip 拖入 Animator 窗口，生成动画状态。
4. 设置默认状态，例如 Idle。
5. 创建状态之间的 Transition。
6. 在 Parameters 中添加控制参数。
7. 给 Transition 添加 Conditions。
8. 根据需要调整 Has Exit Time、Transition Duration 等过渡参数。
9. 将 Animator Controller 绑定到对象的 Animator 组件上。
10. 在代码中调用 SetFloat、SetBool、SetTrigger 等方法驱动切换。

## 易错点

- 把 Animator 和 Animation 混为一谈：Animation 编辑动画片段，Animator 管理动画状态机。
- 状态名和动画文件名混淆：代码里 `Animator.Play` 用的是状态名，不是一定用动画文件名。
- Trigger 当 Bool 用：Trigger 适合一次性触发，持续状态更适合 Bool。
- 条件加太多：同一条 Transition 上的条件必须同时满足。
- 切换有延迟：常见原因是 `Has Exit Time` 开启、`Exit Time` 太靠后或 `Transition Duration` 太长。
- 忘记设置默认状态：Entry 必须指向一个合理的默认状态。
- 新 Layer 没效果：检查 Layer Weight、Avatar Mask、Blending 是否设置正确。
- Root Motion 误开：如果角色移动由代码控制，开启 Apply Root Motion 可能导致位移结果和代码冲突。
