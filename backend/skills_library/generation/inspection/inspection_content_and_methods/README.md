# 鉴定内容和方法及原始记录一览表生成器

## 📋 功能概述

该 Skill 用于生成房屋危险性鉴定报告的第三章"鉴定内容和方法及原始记录一览表"，包含：

### 章节内容

#### （一）鉴定内容和方法
1. **地基危险性鉴定**
   - 评定鉴定对象地基的危险性状态
   - 通过分析倾斜观测资料和不均匀沉降影响

2. **基础及上部结构危险性鉴定**
   - 基础危险性鉴定
   - 上部结构危险性鉴定
     - 结构布置检查（轴网、层高、构件尺寸等）
     - 完损情况检查（裂缝、变形、拆改等）
     - 围护结构检查
     - PKPM 建模计算分析
     - 危险构件评定

3. **综合评定**
   - 按照 JGJ125-2016 标准进行综合分析评定

#### （二）主要检测仪器设备
包含检测使用的仪器设备信息表格：
- 仪器名称
- 规格型号
- 编号
- 有效截止日期

#### （三）原始记录一览表
包含所有原始检测记录的清单：
- 原始记录名称
- 内部编号

## 🎯 使用方法

### Python 调用

```python
from skills_library.generation.inspection.inspection_content_and_methods.impl import (
    generate_inspection_content_and_methods
)

# 生成章节
result = generate_inspection_content_and_methods(
    project_id="proj-xxx",
    node_id="node-xxx",
    context={
        "chapter_number": "三",
        "report_type": "danger_appraisal"
    }
)

# 输出结果
print(result["chapter_title"])
for section in result["sections"]:
    print(f"\n{section['section_number']} {section['section_title']}")
    if section["type"] == "text":
        print(section["content"])
    elif section["type"] == "table":
        print(f"表格包含 {len(section['table']['rows'])} 行数据")
```

### 异步调用

```python
from skills_library.generation.inspection.inspection_content_and_methods.impl import (
    generate_inspection_content_and_methods_async
)

result = await generate_inspection_content_and_methods_async(
    project_id="proj-xxx",
    node_id="node-xxx"
)
```

## 📁 文件结构

```
inspection_content_and_methods/
├── SKILL.md                      # Skill 定义文档
├── fields.yaml                   # 字段配置和默认数据
├── README.md                     # 本文件
├── DATA_EXTRACTION_GUIDE.md      # 🆕 数据提取逻辑详细说明
├── IMPLEMENTATION_SUMMARY.md     # 🆕 实现总结文档
├── impl/
│   ├── __init__.py              # 模块初始化
│   ├── generate.py              # 生成实现
│   └── extract_utils.py         # 🆕 数据库动态提取工具
├── test_generate.py             # 🆕 静态生成测试
└── test_extract.py              # 🆕 动态提取测试
```

## 🔧 配置说明

### 双模式支持

本 Skill 支持两种数据源模式：

#### 1. 静态数据模式（默认）
使用 `fields.yaml` 中定义的固定数据：
- 默认仪器设备列表
- 默认原始记录列表
- 适用于快速测试和展示

```python
result = generate_inspection_content_and_methods(
    project_id="proj-xxx",
    node_id="node-xxx",
    context={
        "use_dynamic_data": False  # 使用静态数据
    }
)
```

#### 2. 动态数据模式（✅ 已实现）
从数据库 `professional_data` 表动态提取：
- **表格1（主要检测仪器设备）**: 从 `raw_result` 和 `confirmed_result` JSON 字段提取
  - 仪器名称：根据 `test_item` 推断
  - 规格型号：`meta.instrument_model` 字段
  - 编号：`meta.instrument_id` 字段
  
- **表格2（原始记录一览表）**: 从数据库记录自动生成
  - 原始记录名称：根据 `control_id` 或 `test_item` 推断
  - 内部编号：从 `meta.record_no` 提取，支持连续编号合并

```python
result = generate_inspection_content_and_methods(
    project_id="proj-xxx",
    node_id="node-xxx",
    context={
        "use_dynamic_data": True  # 启用动态提取
    }
)
```

详细的数据提取逻辑请参考 [DATA_EXTRACTION_GUIDE.md](./DATA_EXTRACTION_GUIDE.md)

### 容错机制
- 如果动态提取失败或无数据，自动回退到静态数据
- 保证在任何情况下都能生成完整的章节内容

## 📝 输出格式

```json
{
  "chapter_type": "inspection_content_and_methods",
  "chapter_title": "鉴定内容和方法及原始记录一览表",
  "chapter_number": "三",
  "has_data": true,
  "sections": [
    {
      "section_number": "(一)",
      "section_title": "鉴定内容和方法",
      "type": "text",
      "content": "..."
    },
    {
      "section_number": "(二)",
      "section_title": "主要检测仪器设备",
      "type": "table",
      "table": {
        "columns": [...],
        "rows": [...]
      }
    },
    {
      "section_number": "(三)",
      "section_title": "原始记录一览表",
      "type": "table",
      "table": {
        "columns": [...],
        "rows": [...]
      }
    }
  ],
  "generation_metadata": {
    "skill_name": "inspection_content_and_methods",
    "skill_version": "1.0.0",
    "generated_at": "2026-02-15T10:00:00Z"
  }
}
```

## 🧪 测试

### 静态数据测试
```bash
cd backend/skills_library/generation/inspection/inspection_content_and_methods
python test_generate.py
```

### 动态提取测试
```bash
cd backend/skills_library/generation/inspection/inspection_content_and_methods
python test_extract.py
```

测试会验证以下功能：
- ✅ 从数据库提取仪器设备信息
- ✅ 从数据库提取原始记录清单
- ✅ 仪器类型智能推断
- ✅ 记录名称自动映射
- ✅ 连续编号自动合并（如 NO:2500108~2500109）
- ✅ 去重机制
- ✅ 双模式生成对比

## 🔄 版本历史

### v1.1.0 (2026-02-15) 🆕
- ✅ 实现从数据库动态提取数据
- ✅ 添加双模式支持（静态/动态）
- ✅ 实现仪器类型智能推断
- ✅ 实现记录名称自动映射
- ✅ 支持连续记录编号合并
- ✅ 添加完整的测试套件
- ✅ 添加详细的数据提取文档

### v1.0.0 (2026-02-15)
- ✅ 初始版本
- ✅ 静态内容生成
- ✅ 支持三个子章节
- ✅ 包含默认仪器设备和原始记录数据

## 📋 TODO

- [ ] 添加仪器有效期管理（valid_until 字段）
- [ ] 支持从单独的仪器配置表读取
- [ ] 增强记录名称推断算法（机器学习）
- [ ] 支持更多检测项目类型
- [ ] 添加检测方法的详细说明
- [ ] 前端集成显示
- [ ] 支持导出为 Word/PDF 格式
- [ ] 添加数据质量报告
