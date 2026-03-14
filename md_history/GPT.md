太好了，那我就**直接给你一套“可复制、可批量扩展”的标准样例**。
我们就拿你最核心、也最容易被审计卡住的一个章节来做——

> **inspection / material_strength（材料强度）**

你可以把这套结构 **原封不动复制** 到其他章节（倾斜、钢筋、墙体高厚比等）。

---

# 一、目录结构（最终推荐版）

```text
inspection/material_strength/
├── SKILL.md              # 能力定义（系统视角）
├── fields.yaml           # 字段契约（数据视角）
├── render.md             # 生成规范（语言视角）
└── impl/
    ├── parse.py          # 从 professional_data 取数
    ├── calculate.py      # 可选：换算/统计
    └── validate.py       # 可选：校验规则
```

---

# 二、SKILL.md（能力定义｜系统级）

```md
# Skill: material_strength_description

## Purpose
生成“材料强度检测情况”章节文字，用于结构安全鉴定报告中
【检查和检测情况 → 检测情况 → 材料强度】小节。

## Scope
- 适用于砌体结构、混凝土结构的材料强度检测描述
- 不做安全等级或危险性结论
- 不替代分析说明或鉴定意见章节

## Inputs
- 数据来源：professional_data
- dataset_key:
  - masonry_strength
  - concrete_strength
  - mortar_strength（可选）

## Outputs
- 一段结构化、专业、可审计的中文描述性文字
- 可被 analysis / opinion 类 skills 引用

## Constraints
- 不得猜测缺失数据
- 不得下“安全 / 危险 / 不符合要求”等结论性判断
- 数值保留位数须符合 fields.yaml 定义

## Failure Strategy
- 若无有效检测数据：
  - 输出“未进行××材料强度检测”的说明性文字
- 不抛异常，不中断报告生成流程
```

> 💡 这个文件是给 **系统 / orchestration / 审核人**看的，不是给大模型“写作”的。

---

# 三、fields.yaml（字段契约｜你系统的“灵魂”）

```yaml
skill: material_strength_description

fields:
  material_type:
    type: enum
    enum: [混凝土, 砌体砖, 砂浆]
    required: true
    source:
      - dataset_key: masonry_strength
        path: raw_result.material_type
      - dataset_key: concrete_strength
        path: raw_result.material_type
    priority: 1

  strength_value:
    type: number
    unit: MPa
    precision: 1
    required: true
    source:
      - dataset_key: masonry_strength
        path: confirmed_result.strength_estimated
      - dataset_key: concrete_strength
        path: confirmed_result.rebound_strength
    priority: 1

  strength_grade:
    type: string
    required: false
    source:
      - dataset_key: masonry_strength
        path: confirmed_result.strength_grade
    priority: 2

  test_method:
    type: string
    required: false
    default: 回弹法
    source:
      - dataset_key: concrete_strength
        path: raw_result.test_method

  test_date:
    type: date
    required: false
    source:
      - dataset_key: masonry_strength
        path: raw_result.test_date
      - dataset_key: concrete_strength
        path: raw_result.test_date

  code_reference:
    type: list
    default:
      - JGJ/T 23-2011
      - GB 50010-2010
```

> 🔑 **重点**

* `source + priority` = 你后面支持多模板、多结构的关键
* fields.yaml **永远不写“语言”**

---

# 四、render.md（生成规范｜只管“怎么写”）

```md
# Render Spec: 材料强度检测描述

## Writing Style
- 工程技术报告语体
- 客观、陈述式
- 不使用评价性或结论性措辞

## Structure
1. 检测对象与方法说明
2. 检测结果描述（数值 + 等级，如有）
3. 规范依据说明（如适用）

## Conditional Rules
- 若存在 strength_grade：
  - 同时描述“强度推定值 + 强度等级”
- 若 test_date 缺失：
  - 不单独说明检测日期
- 若无检测数据：
  - 输出“本次检测未对××材料进行强度检测”

## Example Sentence Patterns
- “采用{test_method}对{material_type}强度进行检测……”
- “检测结果表明，其强度推定值为{strength_value}MPa……”
- “相关检测及结果判定依据{code_reference}执行。”
```

> ⚠️ 注意：
> 这里 **没有模板变量占位符**，只有规则与范式
> 真正拼句由模型完成

---

# 五、impl/parse.py（取数逻辑骨架）

```python
def parse_material_strength(records):
    """
    records: List[professional_data rows]
    return: dict matching fields.yaml
    """
    result = {}

    # 示例：取最高优先级的强度值
    strength_values = [
        r["confirmed_result"].get("strength_estimated")
        for r in records
        if r.get("confirmed_result")
    ]

    if strength_values:
        result["strength_value"] = round(sum(strength_values) / len(strength_values), 1)

    # 其他字段按 fields.yaml 映射
    return result
```

> 你后面可以把 `fields.yaml` 自动加载成 mapping 规则，这一步你已经在做了 👍

---

# 六、为什么这一套“非常适合你现在的系统”

✔ 和你现在的 **professional_data + dataset_key** 完全对齐
✔ 支持字段缺失 / 多来源 / 多模板
✔ 支持 **analysis / opinion** 引用
✔ 审核、回溯、debug 都非常友好
✔ 能被 Claude skills / MCP / 自研 agent 统一调用

---

## 下一步我建议你这样走（很具体）

1️⃣ 你先 **按这个样例复制出 2 个章节**

* `building_inclination`
* `wall_ratio_check`

2️⃣ 等你写到第 3 个，你会发现：

> 90% 的结构可以复用
> 真正变的只有 fields.yaml

---

如果你愿意，下一步我可以继续 **手把手帮你做第二个章节（比如倾斜或墙体高厚比）**，或者直接帮你设计一个 **skills 自动加载/注册机制**（非常适合你现在这个目录结构）。
