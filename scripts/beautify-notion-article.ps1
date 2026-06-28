param(
    [string]$Path = "E:\MyBlog\content\post\data-persistence-binary\index.md"
)

$content = Get-Content -Path $Path -Raw -Encoding UTF8

if ($content -notmatch '(?s)\A(---\r?\n.*?\r?\n---\r?\n)(.*)\Z') {
    throw "Front matter not found"
}

$frontmatter = $Matches[1]
$body = $Matches[2]

$lines = $body -split "\r?\n"
$result = New-Object System.Collections.Generic.List[string]
$inCode = $false
$prevBlank = $false

function Add-Line {
    param([string]$Line)
    $isBlank = [string]::IsNullOrWhiteSpace($Line)
    if ($isBlank -and $script:prevBlank) { return }
    $script:prevBlank = $isBlank
    $script:result.Add($Line)
}

foreach ($line in $lines) {
    if ($line -match '^\s*```') {
        $inCode = -not $inCode
        Add-Line $line
        continue
    }

    if ($inCode) {
        Add-Line $line
        continue
    }

    if ($line -match '^\s*---\s*$') { continue }

    $trimmed = $line.TrimStart()
    if ([string]::IsNullOrWhiteSpace($trimmed)) {
        Add-Line ""
        continue
    }

    $indent = $line.Length - $trimmed.Length

    # List item -> heading by indent depth
    if ($trimmed -match '^- (.+)$') {
        $title = $Matches[1].Trim()
        $level = [Math]::Min(6, 4 + [int]($indent / 4))
        Add-Line ("#" * $level + " " + $title)
        continue
    }

    # API / meta lines
    if ($trimmed -match '^(类名|命名空间|方法|特性名|需要引用命名空间|主要方法|主要类|用法|理解|规则一|规则二|规则三|新知识点|参数一|参数二|参数三|参数四)[:：](.*)$') {
        $label = $Matches[1]
        $value = $Matches[2].Trim()
        if ($label -eq '命名空间' -or $label -eq '方法') {
            Add-Line ("**${label}：** " + '``' + $value + '``')
        } else {
            Add-Line "**${label}：** $value"
        }
        continue
    }

    if ($trimmed -match '^说人话[:：](.*)$') {
        Add-Line "> **说人话：**$($Matches[1])"
        continue
    }

    # Plain paragraph: strip Notion indent
    Add-Line $trimmed
}

$body = ($result -join "`n")
$body = $body -replace 'UTF\s*-\s*8', 'UTF-8'
$body = $body -replace '(\r?\n){3,}', "`n`n"

# Manual polish: opening section
$body = $body -replace '(?s)(### 各类型数据转字节数据\r?\n\r?\n)#### 不同变量类型\r?\n\r?\n有符号  sbyte   int   short   long\r?\n\r?\n无符号  byte    uint   ushort   ulong\r?\n\r?\n浮点   float double  decimal\r?\n\r?\n特殊   bool   char   string',
@'
### 各类型数据转字节数据

#### 不同变量类型

- **有符号：** `sbyte`、`int`、`short`、`long`
- **无符号：** `byte`、`uint`、`ushort`、`ulong`
- **浮点：** `float`、`double`、`decimal`
- **特殊：** `bool`、`char`、`string`
'@

# Empty placeholder sections at end
$body = $body -replace '(### 需求分析\r?\n)(### Excel配置表数据功能)', "`$1`n> 本节内容待补充。`n`n`$2"
$body = $body -replace '(### Excel配置表数据功能\r?\n)(### 表加载使用功能)', "`$1`n> 本节内容待补充。`n`n`$2"
$body = $body -replace '(### 表加载使用功能\r?\n)(### 导出通用工具包)', "`$1`n> 本节内容待补充。`n`n`$2"
$body = $body -replace '(### 导出通用工具包)\s*\Z', "`$1`n`n> 本节内容待补充。"

$intro = @"

> 本文整理自 Unity / C# 数据持久化学习笔记，涵盖字节转换、文件与文件夹操作、文件流、序列化与加密等内容。

"@

$body = $body -replace '\A(\r?\n)?(## 基础知识)', ($intro + '## 基础知识')

$utf8NoBom = New-Object System.Text.UTF8Encoding $false
$output = $frontmatter + $body.TrimStart() + [Environment]::NewLine
[System.IO.File]::WriteAllText($Path, $output, $utf8NoBom)
Write-Host "Beautified: $Path"
