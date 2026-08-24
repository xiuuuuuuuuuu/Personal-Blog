---
title: "Unity 简易音频管理器：ScriptableObject 驱动的 BGM/SFX 管理"
description: "一个轻量的 Unity 音频管理器，用 ScriptableObject 做配置，支持 ID 播放、BGM 淡入淡出、SFX 对象池、2D/3D 音效和音量持久化"
slug: simple-so-audio
date: 2026-08-24 23:00:00+0800
categories:
    - 技术
tags:
    - unity
    - 音频
    - ScriptableObject
weight: 20
---

最近整理了一个轻量级的 Unity 音频管理器 SimpleSOAudio。它不依赖 AudioMixer，也不需要复杂的接入流程，用三个脚本就能把项目里的 BGM、SFX 统一管起来：音频条目通过 ScriptableObject 配置，代码里只按 `id` 播放，音量、对象池和 3D 音效参数都可以在 Inspector 中调整。

## 为什么需要音频管理器

项目里音效多了以后，常见问题是这样：

- 每个地方都直接挂 `AudioSource`，音量要改就得满项目找
- 同一个短音效频繁播放时反复创建 `AudioSource`，产生不必要的开销
- 音频资源直接写在代码里，策划想换一个音效也要动代码
- BGM 切换、暂停、淡入淡出很难统一处理

SimpleSOAudio 用 ScriptableObject 承载配置，把“放什么音频”和“怎么播放”拆开：音频表只管 ID 与资源的对应关系，管理器负责播放、池化、淡化和音量，业务代码只认识 `id`。

## 文件结构与职责

| 文件 | 职责 |
| --- | --- |
| `SimpleSOAudioLibrary.cs` | 定义音频条目 `SimpleSOAudioEntry`，用字典维护 `id -> AudioClip` 映射 |
| `SimpleSOAudioSettings.cs` | 音量、SFX 池大小、3D 音效衰减等配置 |
| `SimpleSOAudioManager.cs` | 全局单例，负责 BGM、SFX 播放和音量持久化 |

Library 中的 `SimpleSOAudioEntry` 包含 `id`、`clip`、`type`、`volume` 和 `pitch_range`：

```csharp
[Serializable]
public sealed class SimpleSOAudioEntry
{
    public string id;
    public AudioClip clip;
    public SimpleSOAudioType type = SimpleSOAudioType.SFX;
    [Range(0f, 1f)] public float volume = 1f;
    public Vector2 pitch_range = Vector2.one;
}
```

`type` 只是标记，实际播放还是走管理器的 BGM / SFX 两个入口；`pitch_range` 让同一段音效每次播放可以有不同的音调，避免重复听感太机械。

## 核心设计

### ID 驱动的音频库

Library 是 `ScriptableObject`，在 Project 窗口里创建资源后，用 Inspector 添加条目即可：

| 字段 | 说明 |
| --- | --- |
| `id` | 播放时使用的唯一标识，例如 `bgm_main`、`sfx_click` |
| `clip` | 对应的音频资源 |
| `type` | BGM 或 SFX |
| `volume` | 该条目的音量倍率，最终和总音量相乘 |
| `pitch_range` | 随机音调范围，x 与 y 相等时为固定音调 |

查找时字典会延迟构建，第一次 `TryGet` 时建立映射；在编辑器中修改列表后 `OnValidate` 会让缓存失效，下次播放自动重建。

### 音量与持久化

Settings 中把音量分成 Master、BGM、SFX 三档，最终音量是 `master_volume * bgm_volume` 或 `master_volume * sfx_volume`：

```csharp
public float BgmFinalVolume => master_volume * bgm_volume;
public float SfxFinalVolume => master_volume * sfx_volume;
```

管理器把音量写入 PlayerPrefs，场景切换后仍能恢复，适合接设置界面。

### BGM 淡入淡出

`PlayBGM` 支持传入 `fade_time`：先让当前 BGM 淡出，再淡入新 BGM；`StopBGM` 也可以只做淡出。淡入淡出使用 `Time.unscaledDeltaTime` 计时，游戏暂停或减速时音乐过渡不会跟着卡住。

### SFX 对象池

管理器启动时按 `initial_sfx_sources` 创建一批 `AudioSource`，空闲时复用；全部忙时如果允许扩容且未达到上限就新建，达到上限后按顺序回收最旧的源。`PlaySFXAtPosition` 会把 `spatialBlend` 设为 1，让音效随位置衰减。

### 单例与跨场景

管理器在 `Awake` 中保证全局唯一，并调用 `DontDestroyOnLoad`，让它跨场景存活。第一次访问 `Instance` 时如果场景里没有实例，会自动创建一个 `[SimpleSOAudioManager]` GameObject。代码用 `UNITY_2023_1_OR_NEWER` 区分 `FindFirstObjectByType` 和旧版 `FindObjectOfType`，兼容 Unity 2023 前后的版本。

## 快速使用

### 1. 创建资源

在 Project 窗口右键选择：

- `Create -> Simple Audio -> Settings`
- `Create -> Simple Audio -> Library`

把资源文件分别命名为 `SimpleAudioSettings` 和 `SimpleAudioLibrary`，并放到任意 `Resources` 文件夹下，管理器启动时会自动 `Resources.Load`。如果已经手动把资源拖到管理器上，放哪里都行。

### 2. 配置 Library

打开 Library 资源，添加条目，例如：

- `id = bgm_main`，`clip = 主城音乐`，`type = BGM`
- `id = sfx_click`，`clip = 点击音效`，`type = SFX`
- `id = sfx_explosion`，`clip = 爆炸音效`，`type = SFX`

### 3. 在代码里播放

```csharp
// 播放 BGM，1.5 秒淡入
SimpleSOAudioManager.Instance.PlayBGM("bgm_main", fade_time: 1.5f);

// 2D 音效
SimpleSOAudioManager.Instance.PlaySFX("sfx_click");

// 世界空间 3D 音效
SimpleSOAudioManager.Instance.PlaySFXAtPosition("sfx_explosion", transform.position);

// 调整音量并自动保存
SimpleSOAudioManager.Instance.SetSFXVolume(0.8f);

// 淡出 BGM
SimpleSOAudioManager.Instance.StopBGM(fade_time: 0.5f);
```

## API 一览

| 方法 | 说明 |
| --- | --- |
| `PlayBGM(id / clip, loop, fade_time)` | 播放 BGM，支持淡入淡出 |
| `StopBGM(fade_time)` | 停止 BGM，可淡出 |
| `PauseBGM()` / `ResumeBGM()` | 暂停 / 恢复 BGM |
| `PlaySFX(id / clip)` | 播放 2D 音效 |
| `PlaySFXAtPosition(id / clip, position)` | 在世界坐标播放 3D 音效 |
| `SetMasterVolume / SetBGMVolume / SetSFXVolume` | 修改音量并持久化 |
| `StopAllSFX()` / `StopAll()` | 停止音效或全部音频 |
| `SaveVolumes()` / `LoadVolumes()` | 手动保存 / 恢复音量 |

## 注意事项

- 自动加载依赖 Resources 路径，资源文件名必须保持 `SimpleAudioSettings` 和 `SimpleAudioLibrary`；不想放在 Resources 就手动拖给 Manager。
- 播放不存在的 `id` 或缺失 `clip` 的条目时，管理器只输出 Warning，不会抛异常。
- 音量始终限制在 `[0, 1]`，设置时会自动 Clamp。
- 对象池回收的是最旧未停止的源，密集播放时偶尔会打断上一个音效，这是池子上限的预期行为。

## 下载源码

完整源码已经打包好了，包含 `SimpleSOAudioLibrary.cs`、`SimpleSOAudioManager.cs`、`SimpleSOAudioSettings.cs` 和一份使用说明：

[下载 SimpleSOAudio.zip](./SimpleSOAudio.zip)

解压后把三个 `.cs` 文件放进项目的 `Assets` 目录，再按上面的步骤创建 Settings 和 Library 资源即可使用。原项目以 MIT License 开源。
