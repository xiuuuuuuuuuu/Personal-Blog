---
title: CG语言语法基础
description: 全面介绍CG语言的基础语法，包括数据类型、运算符、流程控制、顶点/片元着色器结构、语义、内置函数与内置文件等
slug: cg-language-basics
date: 2026-07-15 21:18:00+0800
categories:
    - 图形学
tags:
    - cg
    - shader
    - unity
weight: 10
---

## CG 语法写在哪里

### CG 语句写在哪里？

对于顶点/片元着色器来说，CG 语句需要写在 `Pass` 渲染通道语句块中，用 `CGPROGRAM` 和 `ENDCG` 指令包裹：

```glsl
Pass
{
    CGPROGRAM
    // 在这两个指令间写 CG 代码
    ENDCG
}
```

### 指定着色器函数

在书写 CG 代码之前，需要先使用 `#pragma` 声明编译指令来指定顶点/片元着色器的函数名称：

```glsl
#pragma vertex 函数名
#pragma fragment 函数名
```

这两个编译指令将顶点/片元着色器实现定位到两个函数中，之后只需在对应函数中书写 Shader 逻辑即可。

一个完整的 Pass 示例：

```glsl
Pass
{
    CGPROGRAM

    #pragma vertex vert
    #pragma fragment frag
    #pragma multi_compile_fog

    #include "UnityCG.cginc"

    struct appdata
    {
        float4 vertex : POSITION;
        float2 uv     : TEXCOORD0;
    };

    struct v2f
    {
        float2 uv  : TEXCOORD0;
        UNITY_FOG_COORDS(1)
        float4 vertex : SV_POSITION;
    };

    sampler2D _MainTex;
    float4    _MainTex_ST;

    v2f vert(appdata v)
    {
        v2f o;
        o.vertex = UnityObjectToClipPos(v.vertex);
        o.uv     = TRANSFORM_TEX(v.uv, _MainTex);
        UNITY_TRANSFER_FOG(o, o.vertex);
        return o;
    }

    fixed4 frag(v2f i) : SV_Target
    {
        fixed4 col = tex2D(_MainTex, i.uv);
        UNITY_APPLY_FOG(i.fogCoord, col);
        return col;
    }

    ENDCG
}
```

---

## CG 语法基础数据类型

### 基础数据类型

CG 中的基础数据类型与 C# 基本一致，但有几点不同：

1. **多了浮点数类型** `half` 和 `fixed`
2. **多了纹理类型** `sampler`
3. **数组的声明有区别**

| 类型 | 说明 | 符号 |
|------|------|------|
| `uint` | 32 位无符号整型 | u |
| `int` | 32 位整型 | i |
| `float` | 32 位浮点数 | f |
| `half` | 16 位浮点数 | h |
| `fixed` | 12 位浮点数 | — |
| `bool` | 布尔类型 | — |
| `string` | 字符串 | — |

**纹理对象句柄：**

- `sampler` — 通用纹理采样器
- `sampler1D` — 一维纹理，如渐变色
- `sampler2D` — 二维纹理，最常见
- `sampler3D` — 三维纹理，用于体积渲染
- `samplerCUBE` — 立方体纹理，用于环境映射
- `samplerRECT` — 矩形纹理，用于非标准纹理映射

### 复合数据类型

**数组：** 与 C# 类似，但 CG 无法通过 `Length` 获取数组长度，需要手动用变量记录：

```glsl
// 一维数组
int a[4] = {1, 2, 3, 4};
int aLength = 4;

// 二维数组
int b[2][3] = {{1, 2, 3}, {4, 5, 6}};
int bRowsLength = 2;
int bColsLength = 3;

// 遍历一维数组
for (int i = 0; i < aLength; i++)
{
    int value = a[i];
}

// 遍历二维数组
for (int row = 0; row < bRowsLength; row++)
{
    for (int col = 0; col < bColsLength; col++)
    {
        int value = b[row][col];
    }
}
```

**结构体：** 没有访问修饰符，声明结束需要加分号，一般在函数外声明：

```glsl
struct test
{
    int   i;
    float f;
    bool  b;
};
```

### 特殊数据类型

**向量类型** 是 CG 的内置数据类型，最大维度不超过 4 维，数据类型可以是任意数值类型：

```glsl
fixed4 frag(v2f i) : SV_Target
{
    fixed4 col = tex2D(_MainTex, i.uv);

    float2 vec2 = float2(1.0, 2.0);      // 2 维向量
    fixed3 vec3 = fixed3(1, 2, 4);       // 3 维向量
    int4   vec4 = int4(1, 2, 3, 4);      // 4 维向量

    UNITY_APPLY_FOG(i.fogCoord, col);
    return col;
}
```

**矩阵类型** 也是 CG 的内置数据类型，最大行列不大于 4，不小于 1：

```glsl
// 2x3 矩阵
int2x3 mInt2x3 = {1, 2, 3,
                  4, 5, 6};
```

**bool 类型的特殊用法：** bool 同样可以用于向量，存储逻辑判断结果：

```glsl
float3 a = float3(1.1, 4.5, 1.4);
float3 b = float3(1.9, 1.9, 1.8);
bool3  c = a < b;  // 结果: bool3(true, false, true)
```

> 注意：CG 中向量、矩阵和数组是完全不同的概念。向量和矩阵是内置数据类型，而数组是一种数据结构。

---

## Swizzle 操作符

Swizzle 操作符以点号 `.` 形式使用，后面跟所需的分量顺序。对于四维向量，可以通过 `.xyzw` 或 `.rgba` 两种方式表示四个值，分别用于坐标和颜色语境。

```glsl
fixed4 f4 = fixed4(1, 2, 3, 4);

// 提取分量
fixed f = f4.x;   // 1
f = f4.r;         // 1

// 重新排列分量
f4 = f4.yzxw;
f4 = f4.abgr;

// 用高维向量创建低维向量
fixed3 f3 = f4.xyz;
fixed2 f2 = f3.xz;

// 低维创建高维
fixed4 f4_2 = fixed4(f2, 4, 5);
f4_2 = fixed4(f3, f);
```

### 向量和矩阵的更多用法

**用向量声明矩阵：**

```glsl
fixed4x4 f4x4 = {fixed4(1, 2, 3, 4),
                  5, 6, 7, 8,
                  9, 10, 11, 12,
                  13, 14, 15, 16};
```

**获取矩阵中的元素：**

```glsl
f = f4x4[0][0];   // 第一行第一列
```

**用向量存储矩阵中的某一行：**

```glsl
fixed4 row = f4x4[0];
```

**高维转低维：**

```glsl
fixed3   f3   = f4;       // 自动舍弃多余元素
fixed3x3 f3x3 = f4x4;     // 截取前三行三列
```

---

## 运算符

### 比较运算符

CG 的比较运算符与 C# 一致，结果为 `bool`：

```glsl
>   <   >=   <=   ==   !=
```

### 条件运算符（三目运算符）

```glsl
condition ? value_if_true : value_if_false
```

### 逻辑运算符

```glsl
||   逻辑或（有真则真）
&&   逻辑与（有假则假）
!    逻辑非
```

> 注意：CG 中不存在 C# 中的"短路"操作。

### 数学运算符

```glsl
+   -   *   /   %   ++   --
```

> 注意：CG 取余符号只能对整数取余。

---

## 流程控制语句

### 条件分支语句

```glsl
if (condition) { }
switch (value) { case: break; }
```

条件分支语句的使用与 C# 完全一致。

### 循环语句

```glsl
for (init; condition; increment) { }
while (condition) { }
do { } while (condition);
```

**do-while 示例：**

```cpp
int i = 10;
do
{
    Debug.Log(i);
    i++;
} while (i < 5);  // 输出 10，至少执行一次才退出
```

**性能考虑：**

1. 尽量少用循环语句，用则减少次数和复杂度
2. 充分利用 GPU 的**并行性**来替代循环
3. 尽量避免复杂的条件分支

---

## 函数

CG 中的函数声明和使用几乎与 C# 一致，但多了 `in` / `out` 参数修饰符。

### 无返回值的函数

- `void` — 没有返回值
- `in` — 输入参数，由外部传入，内部只读不修改
- `out` — 输出参数，由内部赋值返回给调用者，必须初始化或修改

```glsl
void test(in fixed inF, out fixed outF)
{
    outF = inF + 10;
}

fixed f  = 10;
fixed f2;
test(f, f2);  // f2 == 20
```

### 有返回值的函数

```glsl
float test2(in float inF, out fixed f)
{
    f = inF + 2;
    return inF * 2;
}

float f3 = test2(11, f);  // f == 13, f3 == 22
```

> 注意：虽然有返回值的函数也可使用 `out` 参数，但这并不常见。顶点/片元着色器函数通常只使用单返回值。

---

## 顶点/片元着色器的基本结构

### 标准的空 Shader 文件

```glsl
Shader "Unlit/TestShader"
{
    Properties { }
    SubShader
    {
        Pass
        {
            CGPROGRAM
            ENDCG
        }
    }
}
```

### 顶点着色器的基本结构

```glsl
CGPROGRAM
#pragma vertex myVert

float4 myVert(float4 v : POSITION) : SV_POSITION
{
    return UnityObjectToClipPos(v);
}
ENDCG
```

**语义说明：**
- `POSITION` — 把模型空间的顶点坐标传入参数 `v`
- `SV_POSITION` — 返回值语义，表示裁剪空间的顶点坐标

### 片元着色器的基本结构

```glsl
CGPROGRAM
#pragma fragment myFrags

fixed4 myFrag() : SV_Target
{
    return fixed4(1, 0, 0, 1);
}
ENDCG
```

**语义说明：**
- `SV_Target` — 将输出颜色存储到渲染目标中（默认帧缓存）

### 整体结构

```glsl
Shader "Unlit/TestShader"
{
    Properties { }
    SubShader
    {
        Pass
        {
            CGPROGRAM
            #pragma vertex myVert

            float4 myVert(float4 v : POSITION) : SV_POSITION
            {
                return UnityObjectToClipPos(v);
            }

            #pragma fragment myFrags

            fixed4 myFrag() : SV_Target
            {
                return fixed4(1, 0, 0, 1);
            }
            ENDCG
        }
    }
}
```

---

## 语义（Semantics）

语义是 CG 语言中用于修饰函数传入参数和返回值的特殊关键字，作用是让 Shader 知道从哪里读取数据、把数据输出到哪里。

> Unity 只支持 CG 中的部分语义。

### 应用阶段 → 顶点着色器

| 语义 | 说明 |
|------|------|
| `POSITION` | 模型空间中的顶点位置 |
| `NORMAL` | 顶点法线 |
| `TANGENT` | 顶点切线 |
| `TEXCOORDn` | 顶点纹理坐标（UV 坐标） |
| `COLOR` | 顶点颜色 |

### 顶点着色器 → 片元着色器

| 语义 | 说明 |
|------|------|
| `SV_POSITION` | 裁剪空间中的顶点坐标（必备） |
| `COLOR0` / `COLOR1` | 顶点颜色 |
| `TEXCOORD0~TEXCOORD7` | 纹理坐标 |

### 片元着色器输出

| 语义 | 说明 |
|------|------|
| `SV_Target` | 输出值存储到渲染目标中 |

### 更多语义

[HLSL 语义汇总（Microsoft 官方文档）](https://learn.microsoft.com/zh-cn/windows/win32/direct3dhlsl/dx-graphics-hlsl-semantics?redirectedfrom=MSDN)

CG 语义大部分与 HLSL 相同，在此做了解即可。

---

## 顶点/片元着色器传递更多参数

需要在着色器中获取更多模型信息时，可以使用结构体对数据进行封装，通过对成员变量加语义的方式来定义所需信息。

> 片元着色器中获取的数据基本上都由顶点着色器传递过来，所以封装的结构体还需作为顶点着色器的返回值类型。

```glsl
CGPROGRAM
#pragma vertex vert
#pragma fragment frag

struct a2v
{
    float4 vertex   : POSITION;
    float3 normal   : NORMAL;
    float2 uv       : TEXCOORD0;
};

struct v2f
{
    float4 pos      : SV_POSITION;
    float3 normal   : NORMAL;
    float2 uv       : TEXCOORD1;
};

v2f vert(a2v data)
{
    v2f o;
    o.pos    = UnityObjectToClipPos(data.vertex);
    o.normal = data.normal;
    o.uv     = data.uv;
    return o;
}

fixed4 frag(v2f data) : SV_Target
{
    return fixed4(0, 1, 0, 1);
}
CGEND
```

---

## ShaderLab 属性类型与 CG 变量类型的匹配关系

| ShaderLab 属性类型 | CG 变量类型 |
|---|---|
| Color, Vector | `float4`, `half4`, `fixed4` |
| Range, Float, Int | `float`, `half`, `fixed` |
| 2D | `sampler2D` |
| Cube | `samplerCube` |
| 3D | `sampler3D` |
| 2DArray | `sampler2DArray` |

在 CG 语句块中声明与 ShaderLab 属性中对应类型的**同名变量**即可使用。

---

## CG 内置函数

CG 提供了丰富的内置函数用于图形编程，可直接在 Shader 中使用。

### 数学函数

**三角函数：**
- `sincos(x, out s, out c)` — 同时计算 sin 和 cos
- `sin(x)`, `cos(x)`, `tan(x)` — 正/余/正切
- `sinh(x)`, `cosh(x)`, `tanh(x)` — 双曲正/余/正切
- `asin(x)`, `acos(x)`, `atan(x)`, `atan2(y, x)` — 反三角函数

**向量/矩阵相关：**
- `cross(A, B)` — 叉乘（仅三维向量）
- `dot(A, B)` — 点乘（仅三维向量）
- `mul(M, N)` / `mul(M, v)` / `mul(v, M)` — 矩阵、向量相乘
- `transpose(M)` — 转置矩阵
- `determinant(m)` — 行列式

**数值相关：**
- `abs`, `ceil`, `floor`, `round` — 取整函数
- `clamp`, `saturate` — 夹紧
- `radians` / `degrees` — 角度/弧度互转
- `max`, `min` — 最大/最小值
- `sqrt`, `rsqrt`, `pow` — 幂 & 根
- `lerp(a, b, f)` — 线性插值
- `exp`, `exp2` — 指数
- `fmod`, `frac` — 余数 & 小数部分
- `sign`, `step`, `smoothstep` — 阶跃函数
- `all`, `any` — 逻辑与/或
- `isfinite`, `isinf`, `isnan` — 数值判定

**其他：**
- `lit(NdotL, NdotH, m)` — 光照贡献计算
- `noise(x)` — 噪声函数

### 几何函数
- `length(v)` / `normalize(v)` — 模长与归一化
- `distance(p1, p2)` — 两点距离
- `reflect(I, N)` / `refract(I, N, eta)` — 反射与折射

### 纹理函数
- `tex2D(tex, s)` — 二维纹理查询
- `tex2Dproj(tex, sq)` — 二维投影纹理查询

---

## CG 内置文件

### 位置与作用

**位置：** `Unity安装目录/Editor/Data/CGIncludes/`

**作用：** 后缀为 `.cginc` 的内置文件，包含已封装好的 Shader 逻辑。

| 文件 | 作用 |
|------|------|
| `UnityCG.cginc` | 最常用的帮助函数、宏和结构体 |
| `Lighting.cginc` | 各种内置光照模型 |
| `UnityShaderVariables.cginc` | 内置全局变量 |
| `HLSLSupport.cginc` | 跨平台编译宏和定义 |

### 使用方式

在 CG 语句块中通过编译指令引用：

```glsl
#include "UnityCG.cginc"
```

> 部分常用的函数、宏和变量无需显式引用，Unity 会在编译时自动识别。但为避免报错，建议都显式引用。

### 常用内容

**方法（UnityCG.cginc）：**
- `WorldSpaceViewDir(v)` — 世界空间中的观察方向
- `ObjSpaceViewDir(v)` — 模型空间中的观察方向
- `WorldSpaceLightDir(v)` — 世界空间中的光照方向（前向渲染）
- `ObjSpaceLightDir(v)` — 模型空间中的光照方向（前向渲染）
- `UnityObjectToWorldNormal(norm)` — 法线模型→世界
- `UnityObjectToWorldDir(dir)` / `UnityWorldToObjectDir(dir)` — 方向模型↔世界

**结构体（UnityCG.cginc）：**
- `appdata_base` — 顶点位置 + 法线 + UV
- `appdata_tan` — 顶点位置 + 法线 + 切线 + UV
- `appdata_full` — 顶点位置 + 法线 + 切线 + 多组 UV
- `appdata_img` — 顶点位置 + UV
- `v2f_img` — 裁剪空间位置 + UV

**变换矩阵宏：**
- `UNITY_MATRIX_MVP` — 模型·观察·投影矩阵
- `UNITY_MATRIX_MV`, `UNITY_MATRIX_V`, `UNITY_MATRIX_P`
- `UNITY_MATRIX_VP`, `UNITY_MATRIX_T_MV`, `UNITY_MATRIX_IT_MV`
- `_Object2World` / `unity_ObjectToWorld` — 模型→世界
- `_World2Object` / `unity_WorldToObject` — 世界→模型

**变量：**
- `_Time` — 用于 Shader 动画
- `_LightColor0` — 光的颜色
