# 银行 Demo：顾客寻路与移动手感复刻指南

版本：1.0  
整理日期：2026-09-20  
源码基线：当前 BankDemo / ThreeBanks 工程  
工程 Unity 版本：2022.3.62f3c1，见 `ProjectSettings/ProjectVersion.txt:1`。  
用途：带到公司电脑，供开发人员或 AI 对照现有项目，复刻此 Demo 的顾客移动、跟随、排队补位和站位停止效果。

本文可以独立阅读。关键源码已经内嵌，不依赖当前电脑的绝对路径。源码索引使用“工程相对路径:行号”，行号对应整理时版本；后续文件修改后请优先按类名、方法名定位。

本文区分三种内容：

- **Demo 实际实现**：能在当前源码或序列化资源中直接核对的行为。
- **复刻接入建议**：为了迁移清晰而提供的等效配置或适配方式，不代表 Demo 已有同名代码。
- **正式项目补强**：对象池、复杂动画、失败恢复等额外能力，不应被当成已经验证的 Demo 功能。

## 1. 先明确要复刻什么

### 1.1 核心结论

Demo 采用 Unity 内置 `UnityEngine.AI.NavMeshAgent` 负责寻路、运动和局部避障，**同样有加速度**，并不是通过匀速直线插值让角色移动。

它看起来停得比较干脆，是以下条件共同作用：

1. 顾客最大速度为 `3.8`，加速度为 `25`，开启自动制动。
2. `stoppingDistance = 0.12`，业务到达判定额外容许 `0.07`。
3. 到达检测不要求先降到零速，而是在完整路径的剩余距离不超过 `0.19` 时提交到达。
4. 业务层确认到达后，如果顾客应当停留，则表现层设置 `Agent.isStopped = true`。
5. 等待或服务期间不继续向 Agent 下发目的地；收到新任务后才恢复移动。
6. 根节点只由 Agent 运动。没有 Rigidbody 惯性、根运动动画或另一个位移脚本继续推动。
7. 跟随目标的更新有距离阈值和时间节流；固定站位不每帧无条件重新寻路。
8. 站位在柜台前的可行走位置，不是柜台模型中心；每个顾客有自己的逻辑预约。

因此，要复刻的是“导航参数 + 到达契约 + 任务生命周期 + 唯一运动驱动 + 合理场景尺寸”，而不是只改一个 Acceleration。

### 1.2 效果边界

Demo 不是精确对齐系统，也不是经过形式证明的“任何帧率下绝不冲过头”的运动算法：

- 它允许停在目标附近，不承诺脚底精确落在 Transform 坐标。
- 进入容差后可以由业务层提前收住；不保证刹车全过程完全自然。
- 基础胶囊没有跑步、脚步和停步动画，轻微速度突变比真人模型更不显眼。
- 拥挤、急转弯、低帧率、高时间倍率、多层场景仍需要实测。
- 现有业务单元测试验证状态和预约，不等于验证了 NavMesh 的逐帧运动质量。

本文没有把当前工程改成另一套移动方案，所有“增强方案”均与原版分开说明。

## 2. 源码定位表

| 路径及起始行 | 类、方法或资源 | 需要参考的内容 |
| --- | --- | --- |
| `Assets/BankDemo/Runtime/BankActorView.cs:7` | `BankActorView` | 顾客导航表现适配器 |
| `Assets/BankDemo/Runtime/BankActorView.cs:20` | `Initialize` | 顾客身份、Agent 和外观绑定 |
| `Assets/BankDemo/Runtime/BankActorView.cs:32` | `Render` | 停止条件、任务版本、目标提交、服务动画 |
| `Assets/BankDemo/Runtime/BankActorView.cs:60` | `ReportArrival` | 完整路径、距离与身份检查 |
| `Assets/BankDemo/Prefabs/Customer.prefab:38` | `NavMeshAgent` 序列化段 | 实际顾客参数，包含自动制动等默认值 |
| `Assets/BankDemo/Editor/BankDemoSceneBuilder.cs:149` | `Actor` | 顾客/玩家构造、根节点、胶囊尺寸、移除碰撞体 |
| `Assets/BankDemo/Editor/BankDemoSceneBuilder.cs:122` | `Desk` | 柜台前服务站位，不是柜台中心 |
| `Assets/BankDemo/Runtime/BankDemoController.cs:56` | `BuildNavigation` | 单银行运行时构建 NavMesh |
| `Assets/BankDemo/Runtime/BankDemoController.cs:92` | `Tick` | 到达反馈、业务推进、表现同步顺序 |
| `Assets/BankDemo/Runtime/BankDemoController.cs:143` | `SpawnOne` | 在生成点实例化、设置银行导航掩码 |
| `Assets/BankDemo/Runtime/BankDemoController.cs:155` | `Destination` | 根据业务状态选择移动目标 |
| `Assets/BankDemo/Runtime/BankPlayerMotor.cs:11` | `FollowPoint` | 玩家身后一单位的跟随点 |
| `Assets/BankDemo/Runtime/BankPlayerMotor.cs:12` | `GoTo` | 玩家移动入口，与顾客入口不同 |
| `Assets/BankDemo/Runtime/BankWorldController.cs:26` | `Awake` | 三银行共享 NavMesh 构建 |
| `Assets/BankDemo/Editor/BankWorldSceneBuilder.cs:54` | `navigationArea` 赋值 | 三银行分别使用 Area 3、4、5 |
| `Assets/BankDemo/Core/BankModel.cs:60` | `ArrivalTicket` | 银行、顾客、任务版本 |
| `Assets/BankDemo/Core/BankModel.cs:188` | `Arrive` | 接受有效到达、开始业务或进入等待 |
| `Assets/BankDemo/Core/BankModel.cs:339` | `MoveTo` | 预约目标后更换任务 |
| `Assets/BankDemo/Core/BankModel.cs:360` | `RemoveOutside` | 室外队列前移使旧到达失效 |
| `Assets/BankDemo/Core/BankModel.cs:373` | `Change` | 修改状态、增加版本、更新到达标记 |

## 3. 完整参数清单

### 3.1 顾客 NavMeshAgent

下表取自 `Customer.prefab`，不只取自场景生成脚本。生成脚本未显式设置的部分属性，已经保存在 Prefab 中。

| 属性 | 当前值 | 复刻意义 |
| --- | --- | --- |
| `agentTypeID` | `0` | 与本 Demo 构建使用的 Agent Type 一致 |
| `speed` | `3.8` | 最大速度，单位为世界单位/秒 |
| `acceleration` | `25` | 最大加速度，单位为世界单位/秒平方 |
| `angularSpeed` | `540` | 最大转向速度，度/秒 |
| `stoppingDistance` | `0.12` | 允许在目标附近停止的距离，不是开始刹车的距离 |
| `autoBraking` | `true` | 接近终点时自动减速 |
| `radius` | `0.28` | 运行时 Agent 半径 |
| `height` | `1.4` | 运行时 Agent 高度 |
| `baseOffset` | `0` | 根节点贴合导航面 |
| `avoidancePriority` | `50` | 所有顾客相同，不靠它实现业务插队或预约 |
| `obstacleAvoidanceType` | 序列化值 `4` | 对应高质量避障 `HighQualityObstacleAvoidance` |
| `autoRepath` | `true` | 开启自动重寻路 |
| `autoTraverseOffMeshLink` | `true` | 开启自动通过 OffMeshLink；本 Demo 没有专门设计此类跳跃流程 |
| Prefab `areaMask` | 全区域 | 三银行模式生成后被覆盖为本银行单一区域 |

当前代码没有关闭 Agent 的 `updatePosition` 和 `updateRotation`，使用 Agent 默认的位置和旋转更新方式。移植时建议显式设为 `true`，但先确认公司项目是否采用“动画驱动根节点”的另一种架构。

Unity 对 `autoBraking` 的定义就是自动制动以避免越过终点；这不等于所有自定义动画或物理位移也会一起停止。[Unity：autoBraking](https://docs.unity3d.com/ScriptReference/AI.NavMeshAgent-autoBraking.html)

### 3.2 导航适配层的硬编码常量

| 位置 | 当前值 | 实际含义 |
| --- | --- | --- |
| `Render` 目标变化阈值 | `> 0.15` | 原始目标距上次已接受的原始目标超过此距离才尝试更新 |
| `Render` 请求间隔 | `0.15` 秒 | 使用 `Time.time`，只限制目的地提交，不限制 Agent 自身每帧运动 |
| 顾客 `SamplePosition` 范围 | `0.8` | 将业务站位映射到允许区域内附近 NavMesh 点 |
| 到达额外容差 | `0.07` | 与 `stoppingDistance` 相加 |
| 当前业务到达阈值 | `0.19` | `0.12 + 0.07`，测量的是剩余路径长度 |
| 跟随距离 | `1.0` | 玩家位置减去朝向向量的一单位 |
| 玩家最大速度 | `6` | 顾客只有 `3.8`，玩家一直全速走时顾客可能落后 |
| 玩家 `SamplePosition` 范围 | `1.5` | 玩家使用全区域，与顾客的 `0.8` 和单银行掩码不同 |

`0.15` 距离阈值与 `0.15` 秒间隔只是数值恰好相同，不是同一个物理量。

普通连续目标更新最多约每秒 6.67 次，但任务版本改变会重置提交时机，不受上一任务剩余节流时间限制。不能把整个 `Render` 或 Agent 更新降到每 0.15 秒一次，那样会改变停止响应。

### 3.3 几何尺寸和空间

| 项目 | 当前值或做法 |
| --- | --- |
| 根节点 | 空 GameObject，上面挂 Agent 与 `BankActorView` |
| 可见身体 | 子节点 `Body`，Unity Capsule |
| `Body.localPosition` | `(0, 0.68, 0)`，服务时叠加上下摆动 |
| `Body.localScale` | `(0.6, 0.65, 0.6)` |
| 顾客碰撞体 | 创建后移除 Capsule 自带 Collider |
| Rigidbody | 没有 |
| Animator / Root Motion | 没有 |
| 室外队列间距 | `1.65` |
| 每张中转柜台的等待位间距 | `1.35` |
| 室内等待位间距 | `1.7` |
| 柜台本体尺寸 | `(2.3, 1, 1.05)` |
| 服务站位 | 柜台基点向世界 `+Z` 偏移 `1.35` |
| 服务站位 Pad | 宽 `0.85`，中心在地面上方 `0.025` |

间距明显大于顾客直径 `0.56`，因此普通排队时不需要持续挤压邻居。业务资源预约避免两个顾客同时被分配到同一个站位，但不是物理碰撞系统。

如果公司场景按另一种世界比例制作，应整体换算距离、速度、加速度、半径、导航采样范围和站位间距。若所有长度扩大 `k` 倍而保持相同经过时间，则速度和加速度也乘以 `k`；时间间隔与角速度不随长度比例改变。不要只缩放模型。

## 4. 原版 BankActorView 完整源码

下面是整理时 `Assets/BankDemo/Runtime/BankActorView.cs` 的完整源码快照，未将建议方案混入原版。

它依赖 `BankDemo.Core` 的 `Customer`、`CustomerState`、`Business`、`ArrivalTicket` 和 `BankModel`。公司项目没有这些类型时，需要按第 11 节映射接口，不能只复制这个文件就认为可独立编译。`body` 和 `bodyRenderer` 也必须绑定。

```csharp
using BankDemo.Core;
using UnityEngine;
using UnityEngine.AI;

namespace BankDemo
{
    [RequireComponent(typeof(NavMeshAgent))]
    public sealed class BankActorView : MonoBehaviour
    {
        public Transform body;
        public Renderer bodyRenderer;
        public int CustomerId { get; private set; }
        public string BankId { get; private set; }
        public NavMeshAgent Agent { get; private set; }
        int revision = -1;
        bool destinationAccepted;
        float retryAt;
        Vector3 lastDestination = Vector3.positiveInfinity;

        public void Initialize(Customer customer)
        {
            CustomerId = customer.Id;
            BankId = customer.BankId;
            Agent = GetComponent<NavMeshAgent>();
            var block = new MaterialPropertyBlock();
            var color = customer.Business == Business.A ? new Color(.08f, .7f, .76f) : new Color(.88f, .32f, .5f);
            block.SetColor("_BaseColor", color);
            block.SetColor("_Color", color);
            bodyRenderer.SetPropertyBlock(block);
        }

        public void Render(Customer customer, Vector3 destination)
        {
            bool following = customer.State == CustomerState.FollowTransit || customer.State == CustomerState.FollowFinal;
            bool stationary = customer.Arrived && !following;
            if (revision != customer.Revision)
            {
                revision = customer.Revision;
                destinationAccepted = false;
                retryAt = 0;
            }
            if (Agent.isOnNavMesh)
            {
                Agent.isStopped = stationary;
                if (!stationary && (Vector3.Distance(destination, lastDestination) > .15f || !destinationAccepted) && Time.time >= retryAt)
                {
                    NavMeshHit hit;
                    destinationAccepted = NavMesh.SamplePosition(destination, out hit, .8f, Agent.areaMask) && Agent.SetDestination(hit.position);
                    if (destinationAccepted) lastDestination = destination;
                    retryAt = Time.time + .15f;
                }
                if (!stationary && !Agent.pathPending && Agent.pathStatus == NavMeshPathStatus.PathInvalid)
                    destinationAccepted = false;
            }
            bool working = customer.State == CustomerState.TransitService || customer.State == CustomerState.FinalService;
            body.localPosition = new Vector3(0, .68f + (working ? Mathf.Sin(Time.time * 7) * .07f : 0), 0);
            body.localRotation = Quaternion.Euler(working ? Mathf.Sin(Time.time * 5) * 9 : 0, 0, 0);
        }

        public void ReportArrival(BankModel model)
        {
            if (model.BankId != BankId) return;
            var c = model.GetCustomer(CustomerId);
            if (c == null || c.Revision != revision || c.Arrived || !destinationAccepted || !Agent.isOnNavMesh || Agent.pathPending) return;
            if (c.State == CustomerState.FollowTransit || c.State == CustomerState.FollowFinal) return;
            if (Agent.pathStatus == NavMeshPathStatus.PathComplete && Agent.remainingDistance <= Agent.stoppingDistance + .07f)
                model.Arrive(new ArrivalTicket(BankId, CustomerId, revision));
        }
    }
}
```

## 5. 逐步解释目标提交

### 5.1 任务版本改变

```csharp
if (revision != customer.Revision)
{
    revision = customer.Revision;
    destinationAccepted = false;
    retryAt = 0;
}
```

新任务必须重新确认导航目标。即使新目标与旧目标相同或相距不足 `0.15`，`!destinationAccepted` 仍能触发新请求。

这里没有重置 `lastDestination`，因为“尚未接受当前任务目标”已经足以强制重新提交。不能删掉这个状态，只保留距离阈值，否则相邻站位、小距离补位或同坐标新业务可能被忽略。

### 5.2 停止由业务状态决定

```csharp
bool following = customer.State == CustomerState.FollowTransit
              || customer.State == CustomerState.FollowFinal;
bool stationary = customer.Arrived && !following;
Agent.isStopped = stationary;
```

“业务已到达且不是跟随”才停。跟随是持续追踪移动目标，不能因为某一帧接近玩家就永久标成到达。

`isStopped` 在每次表现同步都重新取值，新任务清除 `Arrived` 后会恢复移动。原版没有在到达时反复 `ResetPath()`，也没有关闭 Agent。

### 5.3 请求的两个门槛

```text
业务允许移动
AND (目标变化超过 0.15 OR 当前任务目标尚未被接受)
AND 当前缩放时间 >= 下一次可提交时间
```

这不是每 0.15 秒必定重算一条路径。固定目标提交成功后，没有变化就不会持续提交。

它也不是平滑插值：`lastDestination` 保存的是上一次成功提交时的原始业务目标，不是经过 Lerp 的点，更不是角色当前坐标。

### 5.4 目标先映射到导航面

```csharp
NavMesh.SamplePosition(destination, out hit, .8f, Agent.areaMask)
    && Agent.SetDestination(hit.position);
```

两者都成功才令 `destinationAccepted = true`。如果失败，仍经过 `0.15` 秒节流后重试。

需要区分三个事实：

- 找到附近 NavMesh 点，不代表从当前角色位置可以走到。
- `SetDestination` 返回成功，表示目标请求成功，不代表路径计算已经完成。
- `PathComplete` 才是本 Demo 上报到达的必要条件。

Unity 明确说明 `SetDestination` 会触发路径计算，结果可能在后续帧才可用，所以必须检查 `pathPending`。[Unity：SetDestination](https://docs.unity3d.com/ScriptReference/AI.NavMeshAgent.SetDestination.html)

`SamplePosition` 不检查墙体阻隔，也可能采到另一层的导航面；公司的多层银行应额外限制楼层、Agent Type 和投影距离，不能认为 `0.8` 米采样天然保证目标正确。[Unity：SamplePosition](https://docs.unity3d.com/ScriptReference/AI.NavMesh.SamplePosition.html)

### 5.5 无效路径的处理范围

原版在路径计算结束且 `PathInvalid` 时，把 `destinationAccepted` 设回 `false`，使后续能够重试。

原版没有完整实现以下恢复：

- `PathPartial` 长期不完整的主动改派。
- 路径完整但因拥堵持续不前进的超时处理。
- Agent 脱离 NavMesh 后的重新落点与恢复。
- 请求失败时强制清除旧路径，或把当前顾客转入正式的导航失败状态。

特别注意：原版任务切换或采样失败时没有统一 `ResetPath()`，旧路径可能短暂保留。不要把当前实现理解为“任何失败都会立即停在原地”。这些属于正式接入时需要补强的边界，不影响对当前正常场景手感的说明。

## 6. 到达与停止为什么配合有效

### 6.1 到达前置条件

原版 `ReportArrival` 依次确认：

1. 回报目标模型的 `BankId` 与此视图一致。
2. 顾客还存在。
3. 模型任务版本与视图已经下发过的版本一致。
4. 当前任务尚未被模型标记到达。
5. 此任务目标已经被 Agent 接受。
6. Agent 在 NavMesh 上。
7. 路径不在计算中。
8. 顾客不是持续跟随状态。
9. 路径状态为 `PathComplete`。
10. `remainingDistance <= stoppingDistance + 0.07`。

原版没有 `velocity.sqrMagnitude < 某值`，没有要求 `remainingDistance == 0`，也没有把“当前没有路径”直接视为到达。

### 6.2 原版的停止是“自然减速 + 业务收住”

```text
接近导航终点
    -> Agent 自动减速
    -> 到达检测看见剩余距离 <= 0.19
    -> 提交带身份、版本的 ArrivalTicket
    -> 模型标记到达，进入服务或等待
    -> 本次 Tick 的 Render 读取最新状态
    -> 如果仍应停留，isStopped = true
```

因此顾客并不需要先把速度自然降到零，业务才宣布到达。这个设计对经营类柜台站位比较利落，但真人动画可能需要额外处理停步混合。

如果同一次业务调度立刻分配了下一目标，例如室内等待中的顾客获得最终柜台，则 Render 看到的是新任务，会继续走。不要人为强制它一定原地停一帧。

### 6.3 容差不是对原始业务坐标的严格保证

`remainingDistance` 对应提交给 Agent 的 `hit.position`，而不是未经投影的 `destination`。

原始站位与 `hit.position` 最多可能有接近采样半径的偏移；若站位摆在墙里，即使导航到达检测正确，人物也可能停在不合适的位置。正确做法是修正站位和烘焙，而不是不断增大 `SamplePosition` 范围。

### 6.4 不要把速度门槛误认为原版的一部分

有些项目会添加：

```csharp
agent.velocity.sqrMagnitude < 0.01f
```

这可以是另一种到达契约，但会改变 Demo 效果。若公司的自定义移动必须先收到“到达”事件才减速，又要求先停下来才发“到达”，两者可能互相等待。

先复刻原版的距离到达契约，再单独设计自然停步版。不要一边要求与 Demo 一致，一边无说明地加入零速、精确坐标或最后一步 Tween。

## 7. 模型、导航和动画的调用顺序

### 7.1 单个银行的每帧流程

源码：`BankDemoController.Tick`。

```text
处理购买命令；若暂停则不继续推进
    -> 所有顾客 ReportArrival(Model)
    -> 采集玩家接待、交接等输入
    -> Model.Advance(delta)
    -> 到期生成顾客
    -> 删除已离场顾客的视图
    -> 对每位顾客计算 Destination
    -> BankActorView.Render(customer, destination)
    -> 更新柜台、UI 和不变量检查
```

复刻时保留“先接收上一段导航结果，再推进业务，最后把最新任务下发给导航”的数据流。不要让多个脚本各自在 Update 里随意改顾客状态和目标。

这是本 Demo 自己的调用顺序，不是在声明 Unity 内部 NavMesh 求解一定发生于 Update 的某个固定位置。到达检测是每次 Tick 采样，并非连续数学检测。

### 7.2 任务身份

源码：`BankModel.cs:60`。

```csharp
public readonly struct ArrivalTicket
{
    public readonly string BankId;
    public readonly int CustomerId;
    public readonly int Revision;
    public ArrivalTicket(string bankId, int customerId, int revision)
    { BankId = bankId; CustomerId = customerId; Revision = revision; }
}
```

源码：`BankModel.cs:373`。

```csharp
void Change(Customer c, CustomerState state, bool arrived = false)
{
    c.State = state;
    c.Revision++;
    c.Arrived = arrived;
    Log(c, state.ToString());
}
```

“移动完成”事件不能只带一个顾客引用。某位顾客的目标从等待位变成柜台后，旧等待位的迟到通知不能启动柜台服务。

### 7.3 模型接受到达的原版源码

源码：`BankModel.cs:188`。

```csharp
public bool Arrive(ArrivalTicket ticket) => ticket.BankId == BankId && Arrive(ticket.CustomerId, ticket.Revision);

public bool Arrive(int id, int revision)
{
    var c = GetCustomer(id);
    if (c == null || c.Revision != revision || c.Arrived) return false;
    if (c.State == CustomerState.FollowTransit || c.State == CustomerState.FollowFinal) return false;
    c.Arrived = true;
    var slot = c.SlotId == null ? null : GetSlot(c.SlotId);
    if (slot != null) slot.Occupied = true;
    switch (c.State)
    {
        case CustomerState.ToTransit:
            Change(c, CustomerState.TransitService, true);
            c.Remaining = settings.transitSeconds;
            break;
        case CustomerState.ToTransitQueue: Change(c, CustomerState.TransitQueue, true); break;
        case CustomerState.ToIndoor: Change(c, CustomerState.Indoor, true); break;
        case CustomerState.ToFinal:
            Change(c, CustomerState.FinalService, true);
            c.Remaining = settings.finalSeconds;
            break;
        case CustomerState.Leaving:
            customers.Remove(c);
            break;
    }
    return true;
}
```

导航负责报告，模型决定是否接受。动画不直接开始或结束业务，寻路层也不直接释放柜台。

## 8. 各状态到底往哪里走

源码：`BankDemoController.cs:155`，下列为原版方法。

```csharp
Vector3 Destination(Customer c)
{
    if (c.State == CustomerState.FollowTransit || c.State == CustomerState.FollowFinal)
        return world == null ? player.FollowPoint : AreaBounds.ClosestPoint(player.FollowPoint);
    if (c.State == CustomerState.Leaving) return exit.position;
    if (c.State == CustomerState.Outside)
    {
        for (int i = 0; i < Model.Outside.Count; i++)
            if (Model.Outside[i] == c.Id) return outsidePositions[i].position;
    }
    return c.SlotId == null ? spawn.position : slots[c.SlotId].destination.position;
}
```

| 状态 | 目标 | 是否向模型报告到达 |
| --- | --- | --- |
| `Outside` | 室外队列中本人当前序号对应站位 | 是，到达后原地等 |
| `FollowTransit` / `FollowFinal` | 玩家身后跟随点 | 否，持续更新 |
| `ToTransit` | 已预约中转柜台的服务站位 | 是，开始中转服务 |
| `ToTransitQueue` | 已预约的中转等待位 | 是，进入等待 |
| `ToIndoor` | 已预约的室内等待位 | 是，进入等待 |
| `ToFinal` | 已预约最终柜台的服务站位 | 是，开始最终服务 |
| 已到达的等待/服务状态 | 保留对应站位，但 Agent 停止 | 不重复报告 |
| `Leaving` | 本银行出口点 | 是，随后模型移除顾客、运行时销毁视图 |

最后的 `spawn.position` 是原版兜底，不是建议所有异常任务都返回出生点。正式项目应记录缺失站位或非法状态，避免用这个兜底掩盖业务错误。

### 8.1 跟随目标

源码：`BankPlayerMotor.cs:11`。

```csharp
public Vector3 FollowPoint => transform.position - transform.forward * 1.0f;
```

顾客走的是“当前玩家朝向后方的一单位位置”，不是玩家历史轨迹，也没有拷贝玩家路径。因此急转弯时顾客会自己选路径，可能切弯。

原版跟随也保持 `autoBraking = true` 和 `stoppingDistance = 0.12`。没有根据离玩家距离加速追赶，没有在跟随时关闭制动，也没有专用跟随停止半径。

玩家速度 `6` 大于顾客 `3.8`，长距离连续全速行走不能保证固定一单位间隔。公司要增加追赶速度或轨迹跟随时，应明确它属于新需求，不是照搬原版。

### 8.2 排队补位

队首离开后，模型把后续顾客对应的队列索引前移，并使其任务版本更新：

```csharp
for (int i = index; i < outside.Count; i++)
{
    var c = GetCustomer(outside[i]);
    c.Revision++;
    c.Arrived = false;
}
```

视图下一次同步会恢复 `isStopped = false`，提交新站位。到达后重新停下。没有用 Tween 把整列顾客推过去。

### 8.3 柜台目标点

源码：`BankDemoSceneBuilder.Desk`：

```csharp
view.destination = Pad(id + " service",
    position + Vector3.forward * 1.35f,
    white, root.transform, .85f);
```

顾客目标在柜台前，不能把它替换为柜台模型中心。公司柜台如果有不同旋转，应使用柜台局部朝向或专门的服务锚点；原版统一朝向布局采用世界 `+Z`，不应机械套到所有旋转柜台。

## 9. NavMesh 构建与银行隔离

### 9.1 单银行构建源码

源码：`BankDemoController.cs:56`。

```csharp
void BuildNavigation()
{
    var sources = new List<NavMeshBuildSource>();
    foreach (var box in navigationGeometry)
        sources.Add(new NavMeshBuildSource
        {
            shape = NavMeshBuildSourceShape.Box,
            transform = box.transform.localToWorldMatrix * Matrix4x4.Translate(box.center),
            size = box.size,
            area = 0
        });
    var buildSettings = NavMesh.GetSettingsByID(0);
    buildSettings.agentRadius = .3f;
    buildSettings.agentHeight = 1.5f;
    navData = NavMeshBuilder.BuildNavMeshData(buildSettings, sources,
        new Bounds(Vector3.zero, new Vector3(32, 8, 28)), Vector3.zero, Quaternion.identity);
    if (navData == null) throw new System.InvalidOperationException("Bank NavMesh build failed");
    navInstance = NavMesh.AddNavMeshData(navData);
}
```

复刻不要求公司放弃现有烘焙流程。可以继续用现有 NavMeshSurface 或编辑器烘焙，只要最终可行走区域、Agent Type、角色尺度、障碍和站位关系一致。

### 9.2 烘焙参数不是 Agent Inspector 参数的同义词

| 设置层 | 当前值 |
| --- | --- |
| 运行时构建 Agent Type | `GetSettingsByID(0)` |
| 构建半径 | 覆盖为 `0.3` |
| 构建高度 | 覆盖为 `1.5` |
| 运行时顾客半径/高度 | `0.28` / `1.4` |
| 项目 Agent Type 坡度 | `45`，见 `ProjectSettings/NavMeshAreas.asset` |
| 项目 Agent Type 台阶高度 | `0.75`，见同文件 |
| 项目体素/Tile 配置 | `manualCellSize = 0`、`manualTileSize = 0`，使用自动配置 |

项目文件还存有 `cellSize = 0.16666667` 与 `tileSize = 256`，但在自动配置下，不能仅凭这些序列化字段推断最终构建分辨率已经被手工固定。

构建半径决定哪些几何空间可行走；运行时 Agent 半径影响移动中的空间避让。只改 Inspector 的 Radius，不能修正一个烘焙时就错误放开的狭窄通道。

### 9.3 三银行世界

`BankWorldController.Awake` 把三家银行与公共走廊合并构建进同一份 NavMeshData：

- Bank-AB 使用导航 Area `3`。
- Bank-AA 使用导航 Area `4`。
- Bank-BB 使用导航 Area `5`。
- 公共走廊使用 Area `0`。
- 世界构建范围中心为 `(32, 0, -2)`，尺寸为 `(100, 8, 32)`。

顾客生成后执行：

```csharp
if (world != null) actor.Agent.areaMask = 1 << navigationArea;
```

位掩码分别是 `8`、`16`、`32`，不是直接赋值 `3`、`4`、`5`。公司项目的 Area 索引可能已被占用，必须重新映射配置，不能覆盖现有区域定义。

顾客采样也使用 `Agent.areaMask`，因此路径和目标采样都限定在所属银行。玩家使用全区域，能够经过公共走廊。

跟随目标在三银行模式下还会被 `AreaBounds.ClosestPoint` 限制到本行包围盒内。包围盒只能限制几何范围，不能替代 NavMesh 连通性检查或业务 BankId 校验。

### 9.4 几何简化的已知边界

原版把选中的 BoxCollider 作为构建几何，地板、柜台、墙体等通过同一种源收集方式参与构建；并没有完整的楼层管理或逐表面不可行走配置。

公司有低矮墙、可踏上柜面、多层结构时，应检查坡度和台阶高度，并将不应该行走的表面明确设为不可行走。尤其不能因为本 Demo 的布局可用，就认为相同参数适合公司全部模型。

## 10. 动画与移动不能争抢根节点

### 10.1 原版服务表现

原版只在中转/最终服务期间改变 `Body` 子节点的局部高度和局部 X 轴摆动：

```csharp
bool working = customer.State == CustomerState.TransitService
            || customer.State == CustomerState.FinalService;
body.localPosition = new Vector3(0,
    .68f + (working ? Mathf.Sin(Time.time * 7) * .07f : 0), 0);
body.localRotation = Quaternion.Euler(
    working ? Mathf.Sin(Time.time * 5) * 9 : 0, 0, 0);
```

参数 `7` 和 `5` 是正弦相位随时间增长的系数，不是“每秒振动 7 次/5 次”。振幅分别是 `0.07` 世界单位对应的局部偏移和 `9` 度。

这些代码不移动顾客根节点，不产生向前位移。原版也没有到柜台后自动转向柜台的专门对齐逻辑，Agent 停止时的朝向主要来自到达前的运动。

### 10.2 公司真人模型的等效接法

若目标是尽量接近 Demo，建议先采用 Agent 驱动根节点，动画只表现：

```text
CustomerRoot
    NavMeshAgent：唯一的根节点移动驱动
    NavigationAdapter：任务下发、停止、版本化到达
    VisualRoot
        Animator：原地行走、待机、服务动画
```

接入建议：先关闭 Animator 根运动，使用 Agent 实际速度驱动走路混合参数。停止后可以平滑降低动画权重，但动画不能继续把根节点向前拖动。服务对齐只旋转或调整表现层时，也应检查脚底是否明显滑动。

如果项目必须 Root Motion 驱动根节点，就需要另一套明确的 Agent/动画位置同步设计。不能同时让 Agent 默认更新位置，又让 `OnAnimatorMove` 无条件叠加位移。Unity 的 Agent API 提供 `updatePosition`、`nextPosition` 等同步入口；具体接法应按公司动画架构设计，而不是把这些属性随意开关。[Unity 官方 Agent 源码声明](https://github.com/Unity-Technologies/UnityCsReference/blob/master/Modules/AI/Components/NavMeshAgent.bindings.cs)

### 10.3 到达后仍向前滑的定位顺序

1. 观察根节点、`Agent.nextPosition` 和可见模型，而不只看网格。
2. 根节点已经停下，但可见模型继续偏移：查根运动、骨骼动画、VisualRoot 平滑和 Tween。
3. 根节点继续移动且 `isStopped = false`：查到达检测、版本、状态重置、其他脚本恢复 Agent。
4. 根节点继续移动但 `isStopped = true`：查 Rigidbody、CharacterController、Transform、Tween 或动画写位置。
5. Agent 持续运动且目标也一直变：查跟随目标、队列索引和多个命令来源。

这些是排查分支，不是对尚未提供的公司代码作出原因判定。

## 11. 公司项目的复刻接入步骤

### 11.1 第一步：建立可比较基线

先建立一个平地和单个胶囊的测试场景，禁用该测试角色身上其他位移、动画根运动和动态物理驱动。不要一开始就在拥挤银行里同时调所有系统。

复刻测试使用正常时间倍率 `1`。模型和祖先节点保持预期比例，确认生成点、固定目标和转弯通道都在同一个正确 Agent Type 的 NavMesh 上。

### 11.2 第二步：显式配置

下面是为了公司接入整理的配置函数，不是 Demo 原文件中已有的方法。将 Area 掩码作为参数传入，避免把当前项目的 Area 编号写死到公司工程。

```csharp
static void ConfigureDemoLikeCustomer(NavMeshAgent agent, int allowedAreaMask)
{
    agent.speed = 3.8f;
    agent.acceleration = 25f;
    agent.angularSpeed = 540f;
    agent.stoppingDistance = 0.12f;
    agent.autoBraking = true;
    agent.radius = 0.28f;
    agent.height = 1.4f;
    agent.baseOffset = 0f;
    agent.avoidancePriority = 50;
    agent.obstacleAvoidanceType = ObstacleAvoidanceType.HighQualityObstacleAvoidance;
    agent.autoRepath = true;
    agent.autoTraverseOffMeshLink = true;
    agent.updatePosition = true;
    agent.updateRotation = true;
    agent.areaMask = allowedAreaMask;
}
```

前提是 Agent Type 已在 Prefab 与 NavMesh 构建配置中匹配。不要在场景运行中随意切换 Type 来补救不匹配。

### 11.3 第三步：映射数据契约

| Demo 字段/概念 | 公司适配层至少需要的等效信息 |
| --- | --- |
| `BankId` | 导航任务所属区域或业务域 |
| `CustomerId` | 当前顾客身份 |
| `Revision` | 每次新移动任务或目标身份改变递增的序号 |
| `State` | 至少能区分持续跟随、固定目标移动和到达后停留 |
| `Arrived` | 当前任务是否由业务确认到达 |
| `Destination` | 由业务计算的目标点，不由动画决定 |
| `ArrivalTicket` | 到达回调携带上述身份与版本 |
| `Model.Arrive` | 验证回调并决定后续状态的唯一入口 |

逻辑模型不依赖 `Transform`、`NavMeshAgent` 或 Animator。适配层读取模型命令并调用导航；到达后再向模型反馈。

### 11.4 第四步：移植原版运动循环

以第 4 节源码为基线迁移 `Render` 和 `ReportArrival` 的语义：

- 保留任务版本改变时重置提交状态。
- 保留 `0.15` 距离阈值和 `0.15` 秒目标提交间隔。
- 保留 `0.8` 采样范围和本区域掩码。
- 保留路径完整检查与 `0.07` 到达容差。
- 保留跟随状态不发送一次性到达回调。
- 保留模型确认后的 `isStopped` 控制。
- 每个角色每次逻辑 Tick 只执行一套导航适配流程。

不需要把银行业务模型、资金、购买和 UI 全部移植过来，才能复刻导航；但不能省掉任务身份和业务确认这两项必要契约。

### 11.5 第五步：接回正式动画

先保持 Agent 驱动，逐项接回原地走路、待机、服务动画，再接回外观平滑。每接回一项都重复固定目标测试，以找到是哪一层重新引入冲过头。

若公司现有实现是自研路径移动或其他寻路库，不要直接宣称同名参数数值可等效。至少要映射最大速度、加减速策略、转向、到达容差、移动停止指令和位置所有权；无法映射时先使用 NavMeshAgent 做对照组。

## 12. 参数怎么调，哪些不能混为一谈

### 12.1 自动制动、到达距离与停止指令

| 机制 | 解决的问题 | 不保证什么 |
| --- | --- | --- |
| `autoBraking` | 沿路径接近目标时减速 | 不会停止其他脚本或根运动 |
| `stoppingDistance` | 给导航一个可接受的终点范围 | 不是单独指定减速起点 |
| 额外 `0.07` 容差 | 业务不必追到精确坐标 | 不保证脚底严格对齐 |
| `isStopped` | 业务停留期间暂停 Agent 沿路径移动 | 不是冻结所有物理和动画系统 |
| `Revision` | 新旧任务与回调隔离 | 不是运动平滑算法 |
| 预约 | 防止两个顾客抢同一业务站位 | 不保证路径上不发生拥堵 |

不要把到达容差调到很大来掩盖冲过头，这可能让顾客没到柜台就开始服务。也不要用无限大的加速度掩盖多个组件争抢位置。

### 12.2 加速度的直观理解

理想恒定加速度、忽略转向与避障时，从零达到 `3.8` 的时间约为：

```text
t = v / a = 3.8 / 25 = 0.152 秒
```

若假设减速度同样恒为 `25`，理论刹车距离约为：

```text
d = v² / (2a) = 3.8² / (2 × 25) ≈ 0.289 世界单位
```

这是物理直觉示例，不是对 Unity 内部制动实现的反推，也不表示 Demo 应把 stoppingDistance 改成 `0.289`。自动制动可以在进入停止半径前开始减速。

### 12.3 自定义惯性移动的额外问题

如果公司自己对速度做加速积分，需要明确提前减速策略，而不是一直向目标加速，等足够近才把目标方向反过来。

可考虑用“剩余可制动距离”限制期望速度的思路：`v <= sqrt(2 × deceleration × distance)`，但这只是设计参考。最终还必须考虑离散时间步、转弯、碰撞和允许的到达半径。该公式不属于本 Demo 代码，不应作为已经测试过的替换实现直接发布。

### 12.4 固定目标和跟随目标分开验收

固定站位可以在业务确认到达后停止；跟随目标持续移动，不应该使用同一套“一次到达就停住不再更新”的逻辑。

追求更自然跟随时可以研究追赶速度、专用跟随半径和滞回，但这些都会改变当前体验，应在原版复刻达标后单独迭代。

## 13. 最小复现与验收方案

以下是给公司项目执行的测试方案，不是声称已经在公司环境或全部帧率下验证通过。

### 13.1 最小场景

1. 一块平地，烘焙正确 Agent Type 的导航面，构建半径 `0.3`、高度 `1.5`。
2. 一个根节点挂 Agent 的胶囊角色，采用本文参数，无 Rigidbody、Root Motion 或其他位移脚本。
3. 放置相距约 `8` 单位的两个固定目标，另设约 `1` 单位的近距离目标。
4. 用最小业务模型创建一次固定目标任务，递增 Revision、清空 Arrived。
5. 每帧先处理到达，再同步任务；接受到达后保留停留状态，不立刻发下一目标。
6. 胶囊基线通过后增加直角障碍、第二位顾客、队列，最后接回正式模型。

没有银行完整工程时，最小业务模型只需身份、版本、目标、是否跟随、是否到达以及一次性到达入口。先明确这些字段，不要把原版 BankActorView 当成没有依赖的通用组件。

### 13.2 验收矩阵

| 用例 | 操作 | 期望行为 |
| --- | --- | --- |
| 长直线到点 | 走约 8 单位后等待 5 秒 | 到达后停止，不反复绕目标或重新启动 |
| 短距离任务 | 从静止走约 1 单位 | 不要求先达到最大速度再停 |
| 极近新任务 | 新任务目标变化不足 0.15 | 因 Revision 改变仍能提交和完成 |
| 直角绕障 | 绕柜台到前方服务点 | 完整路径到达，不穿过柜台中心 |
| 队列前移 | 队首离开，后方顾客补位 | 清 Arrived、换版本、移动、再停 |
| 两顾客相邻站位 | 采用原版间距 | 各自到预约位，不长期挤同一个点 |
| 跟随急停 | 玩家移动后停止 | 顾客追向跟随点，不把自己永久锁为到达 |
| 跟随转弯 | 玩家转向 90 度或 180 度 | 目标按阈值更新；允许重新选路，不要求沿玩家足迹 |
| 跟随转固定任务 | 玩家交接到中转 | 旧跟随任务不能回报新站位到达 |
| 到达后立即获新任务 | 等待位同 Tick 转柜台 | 执行新任务，不误停在旧位置 |
| 暂停恢复 | `timeScale` 从 1 到 0 再到 1 | 业务与运动同时暂停/恢复，避免导航继续而业务停住 |
| 银行隔离 | 玩家试图带顾客跨行 | 导航掩码和业务归属都不跨行 |
| 目标不在导航面 | 故意把站位移出有效范围 | 不误报到达，能记录失败；正式版本按恢复策略处理 |
| 不完整路径 | 目标在不连通可走岛 | 不以 PathPartial 当作成功 |
| 旧回调 | 新任务开始后提交旧 Ticket | 模型拒绝旧版本，不启动错误业务 |
| 模型换回真人 | 重新启用动画表现 | 停止后无额外根位移；与胶囊基线对比 |

在公司目标平台上分别测正常、高负载和低帧率，再测试游戏实际支持的时间倍率。可以选 30/60/120 FPS 和 1x/2x/4x 作为测试组合，但编辑器帧率限制可能受 VSync 影响，需要记录实际 `deltaTime`。

### 13.3 记录哪些数据

建议在任务提交、路径状态变化、到达上报、模型接受到达和停止时记录事件；到点前后短时间采集逐帧数据，避免全场所有顾客永久刷日志。

```text
frame, scaledTime, unscaledTime, deltaTime, timeScale
bankId, customerId, revision, state, arrived
rawDestination, sampledDestination, agent.destination
rootPosition, agent.nextPosition, visualPosition
agent.velocity, agent.desiredVelocity
isStopped, isOnNavMesh, pathPending, pathStatus, hasPath
remainingDistance, stoppingDistance, destinationAccepted
arrivalReported, arrivalAccepted, targetCommandSource
```

Demo 只缓存原始 `lastDestination`，并未持久保存采样点供日志使用。记录 `sampledDestination` 需要公司在采样成功时额外保存，这属于诊断增强。

验收至少核对：有效 Ticket 只产生一次业务到达；接受到达后若没有新任务则进入停止；固定站位停止后没有持续漂移。最后停点与原始站位的误差需区分采样偏移和移动误差，不要只拿一个总距离下结论。

## 14. 冲过头排查表

| 现象 | 优先核查 | 不建议直接做 |
| --- | --- | --- |
| 越过目标后掉头反复调整 | 自动制动、到达阈值、自定义减速逻辑、目的地是否抖动 | 单纯无限提高加速度 |
| 距离很近但始终不算到达 | pathPending、PathPartial、版本不同、目标未接受 | 直接取消全部到达前置检查 |
| 逻辑到达但模型还滑动 | 根运动、模型局部位移、Tween、动态刚体 | 每帧把模型强行传送回去 |
| 到达后走走停停 | Arrived 被重置、多个目标命令来源、跟随误分类 | 无限制增加等待时间 |
| 停在墙边而非服务位 | 原始目标与采样点、柜台目标是否在障碍里 | 放大采样半径直到“不报错” |
| 拥挤时距离站位还有一截 | 站位预约、Agent 半径、间距和路径阻塞 | 把远处停住一律认作到达 |
| 顾客切弯、不沿玩家脚印 | 原版跟随只追当前后方点，这是设计结果 | 当成固定目标到达 Bug 修 |
| 换银行后路径出界 | Area 掩码、采样区域、BankId 与目标来源 | 全部改成 NavMesh.AllAreas |
| 低帧率才明显越过 | 实际时间步、倍率、位移驱动、容差与速度 | 宣称一组参数适配所有帧率 |

## 15. 正式项目必须另外考虑的能力

### 15.1 对象池生命周期

原版顾客是 Instantiate / Destroy，不是对象池。`Initialize` 没有完整重置旧路径、旧目标缓存和所有任务字段。

对象池复用时必须重置视图缓存、运动状态与身份，并给生命周期增加 Generation 或新的唯一任务身份，避免上一位顾客的回调命中新复用对象。必要的路径清理只能在 Agent 合法、启用且在导航面时执行；不要直接在 OnDisable 中盲目调用 Agent API。

### 15.2 导航失败与预约

导航层应报告失败，由业务层决定保留预约等待重试、取消任务、改派或回收顾客。不要让导航脚本直接释放业务资源，否则会重新引入“人物还在走，位置已经分给别人”的冲突。

生产版本需要覆盖请求失败、不完整路径、长期无进展和脱离导航面。可以记录当前任务起始时间与进展距离，采用有上限的重试策略，而不是永久每 0.15 秒请求。

### 15.3 精准对齐柜台

原版没有最后一步吸附、插值对齐或转向柜台。如果公司需要脚底精确站点并面对柜台，可以设计独立的对齐阶段，但要明确：

- 导航抵近后，谁接管位置与旋转。
- 对齐期间如何暂停 Agent 对同一坐标的写入。
- 对齐结束才开始服务，还是抵近后就开始服务。
- 中断、取消和新任务如何退出对齐。
- 不得同时对根节点执行 Agent 移动和 Tween。

这属于新的到达契约，不应混写成 Demo 原有功能。

### 15.4 物理离位和逻辑释放

原版在预约迁移时释放旧资源，并不等待身体完全离开旧站位。局部避障负责路径上的空间协调。

如果公司柜台过窄，必须等上一位身体离开才能进下一位，可以新增“正在离位”的资源状态；这会影响调度和吞吐量，不是只调 stoppingDistance 能解决的问题。

## 16. 给公司 AI 的执行要求

请先阅读项目现有顾客移动、动画、任务状态、排队和到达检测代码，再进行改造。目标是复刻本文明确描述的行为，不是未经分析就替换整套银行业务系统。

建议按以下顺序交付：

1. 列出现有根节点位置/旋转的所有写入者，确认移动由 Agent 还是动画/自研控制器驱动。
2. 给出当前参数与本文基线参数的对照表，区分场景尺寸差异。
3. 建立单胶囊对照场景，验证导航、到达容差和停止契约。
4. 接入任务版本和到达回调校验，再接回排队、跟随与柜台状态。
5. 接回正式动画，定位并消除额外根位移。
6. 补充失败、对象池、多区域等公司已有功能需要的适配。
7. 提交实际测试记录，说明帧率、倍率、场景规模和仍未覆盖的边界。

禁止把“调了参数”当成已经复刻成功，也不要用每帧 Warp、无条件清零速度、反复 ResetPath 或随意延迟来掩盖系统间争抢移动控制的问题。

**最终验收目标：同一任务只有一个运动控制来源；固定目标的顾客能稳定抵近、有效上报并停止；跟随和新任务可以正常恢复移动；旧任务不会误触发当前业务；正式模型不会在 Agent 停下后继续向前滑。**
