$ErrorActionPreference = 'Stop'

$noteRoot = 'E:\笔记\Obsidian\仓库\First\笔记\Unity'
$blogRoot = 'E:\MyBlog\content\post'

$articles = @(
    @{
        Stem = '动画系统——Animation'
        Items = @(
            ,@('animation-system-animation', 'animation-window-overview.png', '## 4. Animation 窗口结构', '![Animation 窗口整体结构](动画系统——Animation.assets/animation-window-overview.png)')
            ,@('animation-system-animation', 'dopesheet-overview.png', '## 7. 在 Dopesheet 模式编辑动画', '![Dopesheet 模式下的属性轨道和时间轴](动画系统——Animation.assets/dopesheet-overview.png)')
            ,@('animation-system-animation', 'curves-overview.png', '## 8. 在 Curves 模式编辑动画', '![Curves 模式下的动画曲线](动画系统——Animation.assets/curves-overview.png)')
            ,@('animation-system-animation', 'keyframe-tangent-menu.png', '## 9. 关键帧右键菜单和切线模式', '![关键帧右键菜单和切线选项](动画系统——Animation.assets/keyframe-tangent-menu.png)')
            ,@('animation-system-animation', 'animationclip-inspector.png', '## 10. AnimationClip 参数', '![AnimationClip 常用参数](动画系统——Animation.assets/animationclip-inspector.png)')
            ,@('animation-system-animation', 'animationclip-debug-settings.png', '### 10.2 Debug 模式常见参数', '![Debug 模式下的 Sample Rate 和 Wrap Mode](动画系统——Animation.assets/animationclip-debug-settings.png)')
        )
    }
    @{
        Stem = '动画系统——Animator'
        Items = @(
            ,@('animation-system-animator', 'animator-window-overview.png', '## 5. Animator 窗口结构', '![Animator 窗口整体结构](动画系统——Animator.assets/animator-window-overview.png)')
            ,@('animation-system-animator', 'animator-parameters-panel.png', '### 5.1 左侧面板', '![Parameters 面板中的四种参数类型](动画系统——Animator.assets/animator-parameters-panel.png)')
            ,@('animation-system-animator', 'create-state-menu.png', '### 6.3 手动创建状态', '![右键创建动画状态菜单](动画系统——Animator.assets/create-state-menu.png)')
            ,@('animation-system-animator', 'transition-overview.png', '## 8. 添加状态过渡', '![两个状态之间的过渡连线](动画系统——Animator.assets/transition-overview.png)')
            ,@('animation-system-animator', 'transition-conditions-inspector.png', '## 10. Transition 过渡参数', '![Transition 参数和 Conditions 设置](动画系统——Animator.assets/transition-conditions-inspector.png)')
            ,@('animation-system-animator', 'animator-component-inspector.png', '## 12. Animator 组件参数', '![Animator 组件 Inspector 参数](动画系统——Animator.assets/animator-component-inspector.png)')
        )
    }
)

foreach ($article in $articles) {
    $assetDir = Join-Path $noteRoot ($article.Stem + '.assets')
    New-Item -ItemType Directory -Path $assetDir -Force | Out-Null

    $notePath = Join-Path $noteRoot ($article.Stem + '.md')
    $content = [System.IO.File]::ReadAllText($notePath)

    foreach ($item in $article.Items) {
        $sourcePath = Join-Path (Join-Path $blogRoot $item[0]) $item[1]
        $targetPath = Join-Path $assetDir $item[1]
        Copy-Item -LiteralPath $sourcePath -Destination $targetPath -Force

        $heading = $item[2]
        $imageLine = $item[3]
        if (-not $content.Contains($imageLine)) {
            if ($content -notmatch [regex]::Escape($heading)) {
                throw "Missing heading: $heading"
            }
            $content = [regex]::Replace(
                $content,
                [regex]::Escape($heading) + "\r?\n\r?\n",
                $heading + "`r`n`r`n" + $imageLine + "`r`n`r`n",
                1
            )
        }
    }

    [System.IO.File]::WriteAllText($notePath, $content, [System.Text.UTF8Encoding]::new($false))
    $imageCount = ([regex]::Matches($content, '!\[')).Count
    $assetCount = (Get-ChildItem -LiteralPath $assetDir -Filter '*.png' -File).Count
    Write-Output "$($article.Stem): references=$imageCount assets=$assetCount"
}
