"""
Material Strength Skill - README
材料强度检测描述生成技能说明文档
"""

# Material Strength Description Skill

## 📋 概述

这是一个**生成类（Generation）**技能，用于根据已采集的材料强度检测数据，生成符合工程技术规范的检测情况描述文字。

### 典型应用场景
- 房屋质量安全鉴定报告
- 建筑结构检测报告
- "检查和检测情况"章节中的"材料强度"小节

---

## 🏗️ 架构设计

### 三层分离结构

```
material_strength/
├── SKILL.md          ← 系统视角：能力定义、边界、失败策略
├── fields.yaml       ← 数据视角：字段契约、数据来源映射
├── render.md         ← 语言视角：写作规范、句式范式
└── impl/
    └── parse.py      ← 实现层：数据获取与转换逻辑
```

**关键设计原则：**
- `fields.yaml` 定义"要什么数据"
- `render.md` 定义"怎么写"
- `parse.py` 实现"怎么取数据"
- **三者完全解耦，可独立演进**

---

## 📊 数据流

```
professional_data 表
        ↓
   parse.py 读取并按 fields.yaml 映射
        ↓
   结构化数据（JSON）
        ↓
   根据 render.md 规则生成文字
        ↓
   报告章节内容
```

---

## 🔌 与现有系统的对接

### 依赖的上游 Skills
- `info_collection/concrete_table_recognition` - 混凝土强度数据采集
- `info_collection/masonry_strength_recognition` - 砌体强度数据采集

### 数据库依赖
从 `professional_data` 表读取：
- `test_item` - 检测项目
- `test_result` - 检测结果
- `strength_estimated_mpa` - 强度推定值
- `confirmed_result` - 确认后的结果（JSONB）
- `evidence_refs` - 证据引用

### 被下游 Skills 引用
- `analysis/risk_analysis` - 分析说明章节
- `conclusion/appraisal_opinion` - 鉴定意见章节

---

## 🚀 使用方法

### 方式1：通过 DeclarativeSkillExecutor 调用

```python
from services.declarative_skills.executor import DeclarativeSkillExecutor

executor = DeclarativeSkillExecutor()

result = await executor.execute(
    skill_name="material_strength_description",
    project_id="proj-12345",
    node_id="node-67890",
    context={
        "report_type": "safety_appraisal",
        "chapter_number": "5.2.1"
    }
)

print(result["content"])
```

### 方式2：直接使用 parse.py（调试用）

```python
from models.db import fetch_professional_data
from skills_library.generation.inspection.material_strength.impl.parse import (
    parse_material_strength,
    validate_parsed_data
)

# 获取数据
records = fetch_professional_data(
    project_id="proj-12345",
    node_id="node-67890"
)

# 解析
parsed = parse_material_strength(records, "proj-12345", "node-67890")

# 验证
validation = validate_parsed_data(parsed)
print(validation)
```

---

## 📝 输出示例

### 示例1：混凝土单一材料

**输入数据：**
- 材料类型：混凝土
- 检测方法：回弹法
- 检测数量：5个构件
- 强度范围：25.8~31.2 MPa
- 平均强度：28.5 MPa
- 设计等级：C25
- 碳化深度：2.3 mm

**输出内容：**
```
采用回弹法对现场混凝土强度进行检测，共检测5个构件。检测结果表明，
混凝土强度推定值在25.8~31.2MPa之间，平均值为28.5MPa，设计强度等级为C25。
碳化深度平均值为2.3mm。相关检测及结果判定依据JGJ/T 23-2011、GB 50010-2010执行。
```

### 示例2：混凝土+砌体砖

**输出内容：**
```
现场材料强度检测采用回弹法，共检测混凝土、砌体砖等材料，合计8个检测点。
混凝土强度检测结果显示，各检测构件强度推定值平均值为28.5MPa。
砌体砖强度检测结果，强度推定值为8.5MPa。
相关检测及结果判定依据JGJ/T 23-2011、GB/T 50315-2011执行。
```

---

## 🔧 自定义与扩展

### 添加新的材料类型

1. **在 `fields.yaml` 中添加枚举值：**
```yaml
material_type:
  enum: [混凝土, 砌体砖, 砌块, 砂浆, 钢材]  # ← 新增钢材
```

2. **在 `parse.py` 中添加识别逻辑：**
```python
elif "钢材" in test_item or "钢筋" in test_item:
    material_type = "钢材"
```

3. **在 `render.md` 中添加描述模板：**
```yaml
steel_template:
  templates:
    default: |
      钢材强度采用{test_method}检测，检测{test_count}个样品，
      抗拉强度为{avg_strength}MPa。
```

### 修改写作风格

只需修改 `render.md` 中的 `sentence_patterns` 和 `templates`，不影响数据逻辑。

---

## ⚠️ 注意事项

### 数据质量要求
- 必须先完成 info_collection skills 的数据采集
- `confirmed_result` 字段必须包含有效的材料类型和强度值
- 推荐进行人工审核确认后再生成报告

### 边界约束
- ❌ 不做安全性判断（"安全"、"危险"）
- ❌ 不做符合性结论（"符合要求"、"不符合要求"）
- ✅ 只做客观陈述和数据呈现

### 性能考虑
- 单次调用约处理 10-50 条检测记录
- 建议对大批量数据进行分页处理

---

## 🧪 测试

### 单元测试
```bash
cd backend
pytest skills_library/generation/inspection/material_strength/impl/test_parse.py
```

### 集成测试
```bash
# 需要有测试数据库
python -m pytest tests/test_material_strength_skill.py
```

---

## 📚 参考规范

- JGJ/T 23-2011《回弹法检测混凝土抗压强度技术规程》
- GB 50010-2010《混凝土结构设计规范》
- GB/T 50315-2011《砌体工程现场检测技术标准》
- GB 50003-2011《砌体结构设计规范》
- JGJ/T 70-2009《建筑砂浆基本性能试验方法标准》

---

## 📖 相关文档

- [Skills架构设计](../../../HOW_DECLARATIVE_SKILLS_EMBEDDED.md)
- [Generation Skills使用指南](../../README.md)
- [Fields.yaml规范](../../../docs/fields_yaml_spec.md)
- [Render.md规范](../../../docs/render_md_spec.md)

---

## 版本历史

- **v1.0.0** (2026-01-28) - 初始版本，支持混凝土和砌体材料

---

## 作者与维护

- **创建**: System (2026-01-28)
- **维护**: Report Generation Team
- **反馈**: 通过 GitHub Issues 提交
