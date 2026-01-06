# 数据映射问题分析报告

## 问题描述
生成报告时表格为空，但数据库中确实有数据。

## 数据库实际数据结构

根据用户提供的数据库截图，实际数据如下：

### 1. `test_result` 字段（numeric）
- 存储值：34.1, 33.9, 35.9, 33.7 等（13条记录）
- **这是实际的混凝土强度值**

### 2. `test_item` 字段（text）
- 存储值：混合的 "混凝土强度" 和 "混凝土抗压强度"（13条记录）
- 查询条件需要匹配这两个值

### 3. `component_type` 字段（text）
- 存储值：全部是 "C30"（13条记录）
- **这是设计强度等级**

### 4. `location` 字段（jsonb）
- 存储值：JSON格式的位置信息，如 `"屋面梁3/D-G"`, `"二层柱5/C"` 等
- 结构：可能是字符串或JSON对象

### 5. `raw_result` 字段（jsonb）
- 存储值：LLM解析的原始JSON，使用**中文键名**
- 包含字段：
  - `"检测部位"`: 位置信息
  - `"设计强度等级"`: "C30"
  - `"碳化深度平均值_mm"`: 6
  - `"碳化深度计算值_mm"`: [6,6,6,6,...]
  - **可能包含 `"混凝土强度推定值_MPa"` 或类似字段，但不是 `"strength_estimated_mpa"`**

## 代码期望的数据结构

### ChapterGenerationSkill.execute() 方法（第145-147行）

```python
design_grade = test_value_json.get("design_grade") or raw_result.get("design_grade")
strength = self._as_number(raw_result.get("strength_estimated_mpa"))
carbonation = self._as_number(raw_result.get("carbonation_depth_avg_mm"))
```

**期望：**
- `strength_estimated_mpa` 从 `raw_result` 中获取（使用**英文键名**）
- `design_grade` 从 `test_value_json` 或 `raw_result` 中获取
- `carbonation_depth_avg_mm` 从 `raw_result` 中获取（使用**英文键名**）

## 问题根源

### 1. **字段名不匹配（键名问题）**

- **代码期望**：`raw_result.get("strength_estimated_mpa")`（英文键名）
- **实际数据**：`raw_result` 中使用中文键名，如 `"混凝土强度推定值_MPa"` 或可能没有该字段
- **实际值位置**：强度值已经被映射到 `test_result` 字段中

### 2. **数据已被映射但代码仍从原始数据读取**

- MappingSkill 已经将强度值提取并保存到 `test_result` 字段
- 但 ChapterGenerationSkill 仍试图从 `raw_result` 中读取（使用错误的键名）

### 3. **查询条件问题**

- 代码查询 `test_item = "混凝土抗压强度"`（第118行，dataset["test_item"]）
- 但数据库中 `test_item` 字段混合了 "混凝土强度" 和 "混凝土抗压强度"
- 需要支持模糊匹配或使用 IN 查询

## 解决方案

### 方案1：修改 ChapterGenerationSkill 使用映射后的字段（推荐）

**优点：**
- 利用 MappingSkill 已经完成的数据映射工作
- 代码更简洁，性能更好
- 符合数据流设计

**修改点：**

1. **强度值**：优先从 `record.get("test_result")` 获取，如果没有再从 `raw_result` 中查找（支持中文键名）
2. **设计强度等级**：优先从 `record.get("component_type")` 获取，如果没有再从 `raw_result` 中查找
3. **位置信息**：`record.get("location")` 已经是正确的（但需要处理JSON格式）
4. **碳化深度**：从 `raw_result` 中查找（支持中文键名 `"碳化深度平均值_mm"`）

### 方案2：修改 MappingSkill 在 raw_result 中保存英文键名

**缺点：**
- 需要修改 MappingSkill，影响已保存的数据
- 不够灵活，如果以后有其他映射规则会冲突

## 推荐修复代码

```python
# 在 ChapterGenerationSkill.execute() 中

for record in records:
    test_value_json = record.get("test_value_json") or {}
    raw_result = record.get("raw_result") or {}
    
    # 位置信息：优先从 location 字段获取
    location = record.get("location") or {}
    if isinstance(location, str):
        # 如果 location 是字符串，转换为 JSON 格式
        try:
            location = json.loads(location) if location else {}
        except:
            location = {"display": location} if location else {}
    
    # 设计强度等级：优先从 component_type 字段获取，再从 raw_result 中查找
    design_grade = (
        record.get("component_type") or  # 优先：映射后的字段
        test_value_json.get("design_grade") or
        raw_result.get("设计强度等级") or  # 中文键名
        raw_result.get("design_grade")
    )
    
    # 强度值：优先从 test_result 字段获取，再从 raw_result 中查找（支持中文键名）
    strength = (
        record.get("test_result") or  # 优先：映射后的字段
        self._as_number(raw_result.get("混凝土强度推定值_MPa")) or
        self._as_number(raw_result.get("混凝土强度推定值（MPa）")) or
        self._as_number(raw_result.get("strength_estimated_mpa"))
    )
    
    # 碳化深度：从 raw_result 中查找（支持中文键名）
    carbonation = (
        self._as_number(raw_result.get("碳化深度平均值_mm")) or
        self._as_number(raw_result.get("carbonation_depth_avg_mm"))
    )
    
    # 评价：从 raw_result 中查找
    evaluation = raw_result.get("evaluation") or raw_result.get("评价")
```

## 查询条件优化

对于 `test_item` 查询，建议：

```python
# 如果指定了源节点，不再强制过滤 test_item
query_test_item = None if source_node_id else dataset["test_item"]

# 或者支持模糊匹配（如果数据库支持）
# 但这需要修改 fetch_professional_data 函数
```

## 总结

**核心问题：**
1. ChapterGenerationSkill 使用了错误的字段名（英文键名 vs 中文键名）
2. ChapterGenerationSkill 没有利用 MappingSkill 已经映射好的数据（test_result, component_type）
3. 查询条件可能需要更灵活

**推荐修复：**
- 优先使用映射后的字段（test_result, component_type）
- 如果映射字段为空，再从 raw_result 中查找（支持中文键名作为fallback）
