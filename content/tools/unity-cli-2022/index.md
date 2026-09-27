---
title: "Unity CLI：Unity 2022 Windows 迁移包与安装说明"
description: "固定版本的 Windows CLI、Unity 2022 Pipeline 适配包，以及跨电脑安装、验证和 AI 调用说明。"
slug: unity-cli-2022
url: /tools/unity-cli-2022/
date: 2026-09-27T23:55:00+08:00
categories:
    - 小工具
tags:
    - Unity
    - CLI
    - Unity2022
toc: true
comments: false
---

这份迁移包包含已在本机验证的 Windows x64 CLI、Unity 2022 Pipeline 适配包、中文说明和文件校验工具。下载后按下文完成目标电脑的安装与连接检查。

## 下载

- [下载完整迁移包（ZIP，约 15.9 MiB）](../../downloads/other/unity-cli-2022/UnityCLI-Windows-2022-2026-09-27.zip)
- [下载独立 Markdown 说明](../../downloads/other/unity-cli-2022/UnityCLI-Windows-2022-Setup.zh-CN.md)
- [查看 SHA-256 校验值](../../downloads/other/unity-cli-2022/SHA256SUMS.txt)

压缩包 SHA-256：

```text
695EB0FA6FD65424458CFA246B61E24506DC27A06C1356C0036CEA30ED39927A
```


整理日期：2026-09-27。适用于把当前已验证的 CLI 与 Pipeline 适配包迁移到另一台 Windows x64 电脑。

## 1. 先了解需要安装什么

这套工具由两部分组成：**CLI 是电脑上的命令行程序，Pipeline 是 Unity 项目内负责接收命令的包。** CLI 每台电脑准备一份；每个需要控制的 Unity 项目安装一份 Pipeline。编辑器打开项目并完成编译后，AI 或 PowerShell 才能通过 CLI 操作它。

本压缩包直接提供 Windows 程序，无需 Ubuntu、WSL、Node.js 或 npm。Unity 编辑器和授权仍需在目标电脑上自行准备；压缩包不包含 Unity 编辑器。

| 内容 | 固定版本与范围 |
| --- | --- |
| CLI | Unity CLI `1.0.0-beta.10`，Windows x64 |
| Pipeline | `0.7.0-exp.1.2022mod.1`，基于官方 `0.7.0-exp.1` 的本地 Unity 2022 适配 |
| 已验证编辑器 | Windows 上的 `2022.3.62f3c1`；已有适配包项目也已在 `2022.3.62f3` 复查通过 |
| tgz 安装验证 | 空白 `2022.3.62f3c1` 项目通过依赖安装和编译 |
| PowerShell | 使用 Windows PowerShell 或 PowerShell 7；文中命令采用 PowerShell 语法 |

适配包不是 Unity 官方面向 2022 发布的版本。不要据此推断其他 2022 小版本、Unity 6、其他系统或全部命令均兼容。公司项目优先在可恢复的项目副本中首次接入。

## 2. 压缩包内容

```text
UnityCLI/
├─ bin/unity.exe
├─ packages/com.unity.pipeline-0.7.0-exp.1.2022mod.1.tgz
├─ unity.ps1
├─ Verify-Files.ps1
├─ manifest.json
├─ README.zh-CN.md
├─ AI-USAGE.zh-CN.md
└─ THIRD-PARTY.zh-CN.md
```

- `bin/unity.exe`：原样复制的 CLI 可执行文件。
- `packages/*.tgz`：通过 Package Manager 安装的 Unity 2022 适配包；内部保留许可证、第三方声明和兼容说明。
- `unity.ps1`：按项目路径调用 CLI，把 CLI 的运行状态放到工具目录下的 `state/`，运行结束后恢复当前进程的环境变量。
- `Verify-Files.ps1`：只读取文件，对照清单校验大小和 SHA-256，不安装组件、不改 PATH、不连接 Unity。
- `manifest.json`：固定版本、文件大小和 SHA-256 清单。
- `AI-USAGE.zh-CN.md`：可以交给公司电脑上的 AI 阅读的调用规范。

包内没有原电脑的 `state/`、登录信息、连接凭据、项目 `Library/`、Unity 日志或业务资源。`state/` 在首次使用辅助脚本时生成。

## 3. 在公司电脑解压并检查

将整个 `UnityCLI` 文件夹解压到自己有写入权限的固定位置，例如：

```text
D:\UnityTools\UnityCLI
```

没有 D 盘时，可以放到 `C:\Tools\UnityCLI` 或用户目录。后续命令中的路径需要相应替换；工具本身不依赖 D 盘。辅助脚本需要能在自己的目录下创建 `state/`。

先核对下载页给出的压缩包 SHA-256：

```powershell
Get-FileHash -LiteralPath 'C:\下载目录\UnityCLI-Windows-2022-2026-09-27.zip' -Algorithm SHA256
```

再校验解压后的文件：

```powershell
& 'D:\UnityTools\UnityCLI\Verify-Files.ps1'
```

应看到 `PASS` 和文件数量。SHA-256 用于检查文件是否与发布包一致，不替代来源信任。也可右键 `bin\unity.exe` → 属性 → 数字签名，查看 Unity Technologies 的签名信息。

如果公司 PowerShell 策略不允许执行 `.ps1`，可以直接执行后文的 `unity.exe` 命令，并手工使用 `Get-FileHash` 校验清单中的哈希；不必为运行 CLI 修改全局执行策略。若公司策略也禁止该程序运行，按公司软件管理流程处理。

检查版本：

```powershell
& 'D:\UnityTools\UnityCLI\bin\unity.exe' --version
```

预期输出：`1.0.0-beta.10`。

## 4. 给 Unity 项目安装 Pipeline

### 4.1 首次在一个新项目使用

1. 用目标 Unity 版本打开项目。建议使用已验证的 `2022.3.62f3`，等待原有代码编译完成。
2. 在项目根目录（与 `Assets`、`Packages`、`ProjectSettings` 同级）创建 `LocalPackages` 文件夹。
3. 把工具包中的 `.tgz` 复制进去，保留原文件名。
4. 在 Unity 打开 **Window → Package Manager**。
5. 点击 **＋ → Add package from tarball…**，选择项目 `LocalPackages` 中的 `.tgz`。
6. 等待依赖安装、代码编译和可能发生的编辑器重载。确保 Console 没有阻止编译的错误。

目录示例：

```text
YourProject/
├─ Assets/
├─ Packages/
├─ ProjectSettings/
└─ LocalPackages/
   └─ com.unity.pipeline-0.7.0-exp.1.2022mod.1.tgz
```

这是 UPM 包，不是 `.unitypackage`，不要把它解压到 `Assets`。安装方法参见 [Unity 2022.3 官方文档](https://docs.unity3d.com/2022.3/Documentation/Manual/upm-ui-tarball.html)。

包显式依赖 `com.unity.inputsystem@1.14.2`，以及 Test Framework、Newtonsoft JSON、Mono.Cecil 和若干内置模块。**本压缩包不是全部依赖的离线镜像**：缺少依赖时，Package Manager 需要访问项目配置的 Unity 包源。若出现输入系统启用或重启提示，应按项目现有输入方案处理，不必为 CLI 改写游戏输入代码。

项目需要共享给其他电脑时，将 `LocalPackages` 中的 tgz、`Packages/manifest.json` 和 `Packages/packages-lock.json` 一起纳入项目版本管理。确认依赖引用使用可迁移的相对路径。对上述目录结构，manifest 中该依赖通常为：

```json
"com.unity.pipeline": "file:../LocalPackages/com.unity.pipeline-0.7.0-exp.1.2022mod.1.tgz"
```

让 Package Manager 生成条目即可，不要把这一个条目覆盖成整个 manifest。

### 4.2 搬的是已经接入的项目

如果项目已经包含适配过的 `Packages/com.unity.pipeline` 嵌入式目录，完整保留它即可，**不要再导入第二份 tgz**。当前 TestMCP 就属于这种情况。

如果已有其他版本的同名包，先确认来源和项目依赖，再迁移。同一项目只应有一份有效的 Pipeline；嵌入式目录会优先于 manifest 中的包引用。

不要使用 `unity pipeline install` 覆盖这份适配包，也不要直接升级到最新官方 Pipeline 来替代它。

## 5. 测试连接与实际执行

下面假设项目在 `D:\Work\YourProject`。每次都换成目标项目根目录。运行命令前，保持 Unity 编辑器打开，并关闭需要人工处理的保存提示等模态弹窗。

### 5.1 查询状态

```powershell
& 'D:\UnityTools\UnityCLI\bin\unity.exe' command editor_status --project-path 'D:\Work\YourProject' --format json --timeout 10
```

检查 JSON 返回：命令成功、状态为 `ready`，项目路径和 Unity 版本与目标一致。仅 `unity --version` 成功不能证明已连接编辑器。

### 5.2 让后台编辑器保持更新

```powershell
& 'D:\UnityTools\UnityCLI\bin\unity.exe' command set_autotick --enable true --project-path 'D:\Work\YourProject' --format json --timeout 10
```

这一步适用于后续 AI 自动操作，减少编辑器不在前台时更新停滞的问题。它不能代替关闭弹窗，也不能解决脚本死循环。

### 5.3 实际执行一条只读 C#

```powershell
& 'D:\UnityTools\UnityCLI\bin\unity.exe' command eval --code 'return UnityEngine.Application.unityVersion;' --project-path 'D:\Work\YourProject' --format json --timeout 15
```

返回当前 Unity 版本且执行结果成功，说明 CLI → Pipeline → 编辑器执行链路可用。应同时检查外层命令结果和内层脚本结果，不要只看进程是否退出。

### 5.4 使用辅助脚本

也可以使用随包的脚本，保持 CLI 状态在工具目录内：

```powershell
& 'D:\UnityTools\UnityCLI\unity.ps1' -ProjectPath 'D:\Work\YourProject' -CliArgs @('command', 'editor_status', '--format', 'json', '--timeout', '10')
```

辅助脚本使用 `-ProjectPath` 指定项目；不要在 `-CliArgs` 中重复传入 `--project-path`。本文使用的是公共目录里的 `unity.ps1`，不是旧项目中可能带有固定安装路径的同名脚本。

## 6. 可选：配置 PATH

完整路径命令已经可以使用。若希望直接输入 `unity`，可在 Windows 的“编辑账户的环境变量”中，把实际 `UnityCLI\bin` 路径加入当前用户的 `Path`，保留原有条目。

修改后重新打开终端；如果终端由 AI 编辑器或其他应用启动，也要重新启动该父应用，以获取新环境变量。

```powershell
Get-Command unity
unity --version
```

确认 `Get-Command` 指向本工具包的 `bin\unity.exe`。遇到同名程序或多个 CLI 版本时，继续使用完整路径最明确。

## 7. 让 AI 使用

把 `AI-USAGE.zh-CN.md` 交给 AI，并提供工具目录、项目根目录、Unity 版本。AI 必须能够在打开 Unity 的电脑上执行本机命令。仅有远程聊天窗口而没有本机执行能力，不能直接调用这里的 exe。

首次使用让 AI 先完成本说明第 5 节的三项检查，再执行具体任务。要求固定项目路径、设置合理超时，并在脚本返回后报告实际结果。

编写多行 C# 时，把脚本放在项目 `Tools/UnityCli/` 等 `Assets` 之外的目录，通过 `run_script --file ... --entry ...` 执行；避免为一次工具调用引入不必要的项目脚本导入。

修改项目 C# 后，需要等待重编译完成再操作。测试或其他长任务优先使用命令自身支持的异步模式和状态查询；不要反复启动同一个任务。

## 8. 常见问题

| 现象 | 检查方式与处理 |
| --- | --- |
| 提示找不到 `unity` | 用完整 exe 路径；或重开终端及父应用加载 PATH。 |
| 能显示 CLI 版本，但找不到编辑器 | 确认 Unity 已打开目标项目、Pipeline 已安装、项目无编译错误、`--project-path` 正确。 |
| 普通终端正常，AI 沙箱找不到实例或访问被拒绝 | Pipeline 的本机连接凭据限制为当前 Windows 用户读取。让 AI 使用获准的本机命令执行环境；不要复制旧连接凭据、放宽凭据文件权限或关闭认证。 |
| `blocked_by_dialog` 或长时间无返回 | 查看 Unity 是否有保存、确认、导入或其他模态弹窗；按真实需要处理后再查状态。 |
| `Main thread operation timed out` | 检查 Unity 主线程是否忙于导入、编译、弹窗或脚本执行；先查 `editor_status` 和 Console，再决定是否重试。 |
| AI 一直显示“处理中”，但 Unity 已完成 | 分别查看命令实际耗时、命令返回值和 AI 任务总耗时。任务总时长还包含思考、读文件与后续验证。 |
| 包依赖下载失败 | 查看 Package Manager 的具体依赖和包源网络错误；本包未携带全部依赖缓存。 |
| 包装脚本被 PowerShell 策略阻止 | 使用 `bin\unity.exe` 的完整路径；遵守公司脚本和程序运行策略。 |
| 另一台没有 D 盘 | 更换解压位置和命令路径，工具支持其他可写目录。 |

`--timeout` 是 CLI 等待时间（秒）；`run_script` 另有 `--timeout_ms`（毫秒）控制服务端等待。超时返回不代表脚本中的所有操作已被撤销或停止，尤其异步入口可能继续运行。先确认项目当前状态，避免重复创建对象或重复写入。

查看命令帮助和错误状态：

```powershell
& 'D:\UnityTools\UnityCLI\bin\unity.exe' command run_script --help
& 'D:\UnityTools\UnityCLI\bin\unity.exe' command console_status --project-path 'D:\Work\YourProject' --format json --timeout 10
```

Console 缓存可能包含历史错误，应结合当前编译状态与时间判断，不要把历史记录直接当作新错误。测试时无须清空用户的日志。

## 9. 已验证范围与维护

原适配实验验证过编辑器连接、命令发现、实时 C#、资源创建和保存、截图、Play/Stop、重编译、重启后的资源与连接恢复。空白项目安装 tgz 的依赖和编译验证通过。之后已有适配项目在 `2022.3.62f3` 上复查了连接、C# 执行、材质读取和截图；2026-09-27 再次确认连接与 C# 执行正常。

这些记录不是对全部命令、所有项目、Player 构建、IL2CPP 或运行时热重载的完整认证。公司电脑尚未实机验证，需要按第 5 节完成接收验收。

版本固定在本说明列出的组合。升级 CLI、Pipeline、Unity 或关键依赖后重新检查，不要依赖“最新版”浮动下载自动保持兼容。

适配主要包含：Unity 2022 的物理材质命名兼容、材质渲染队列读取、DLL 导入元数据转换、Console 计数接口适配，以及停用 Unity 6 专用统计和默认不启用上游内部测试。详细说明与原许可证在 tgz 的 `UNITY-2022-COMPATIBILITY.md`、`LICENSE.md` 和 `Third Party Notices.md` 内。

## 10. 接收验收清单

- [ ] 压缩包 SHA-256 与下载页一致，解压后的 `Verify-Files.ps1` 校验通过。
- [ ] `unity.exe --version` 返回 `1.0.0-beta.10`。
- [ ] 目标项目使用预期 Unity 版本，Pipeline 安装完成且无编译错误。
- [ ] `editor_status` 返回正确项目和 `ready`。
- [ ] `set_autotick` 成功，`eval` 返回当前 Unity 版本。
- [ ] AI 能以相同路径调用，并正确读取返回值。

## 11. 来源

- [Unity 2022 适配思路参考](https://github.com/rocwood/unity-cli-2022-mod)
- [Unity 2022.3：从本地 tarball 安装 UPM 包](https://docs.unity3d.com/2022.3/Documentation/Manual/upm-ui-tarball.html)
- CLI 原文件签名与 SHA-256、适配包 SHA-256 记录在本包 `manifest.json`；本次迁移不重新下载或替换程序版本。
