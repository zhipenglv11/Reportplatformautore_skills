# 混凝土链路完整性检查报告

> 检查时间：2025-01-03
> 检查范围：PDF输入 → 表格输出、PDF输入 → 段落输出

---

## 📊 链路1：PDF → 表格（concrete_strength_table）

### ✅ 信息采集阶段

**输入**：PDF/图片文件（回弹法检测表）

**处理流程**：
1. ✅ `upload_file` 接口接收文件
2. ✅ `ParseSkill` 使用 Vision LLM 解析图片
3. ✅ `DEFAULT_PROMPT` 提取字段：
   - 检测部位
   - 设计强度等级
   - 混凝土强度推定值_MPa
   - 碳化深度计算值_mm（数组）
   - 碳化深度平均值_mm
   - 检测日期
4. ✅ `MappingSkill` 映射到 professional_data 表结构
5. ✅ `ValidationSkill` 验证数据
6. ✅ 存入 Supabase `professional_data` 表

**状态**：✅ **已打通**

---

### ✅ 报告生成阶段

**输入**：章节配置（templateStyle = 'concrete_strength_table'）

**处理流程**：
1. ✅ 前端映射：`concrete_strength_table` → `dataset_key = 'concrete_rebound_tests'`
2. ✅ 后端查询：从 Supabase 读取数据（按 project_id、test_item、method_keyword 过滤）
3. ✅ 数据组装：生成表格行数据（序号、抽测部位、设计强度等级、强度推定值、碳化深度、评价）
4. ✅ 输出：返回表格 block（type: "table"）

**状态**：✅ **已打通**

---

## 📝 链路2：PDF → 段落（concrete_strength_desc）

### ✅ 信息采集阶段

**输入**：PDF/图片文件（回弹法检测表）

**处理流程**：
1. ✅ `upload_file` 接口接收文件
2. ✅ `ParseSkill` 使用 Vision LLM 解析图片
3. ✅ `DEFAULT_PROMPT` 提取基础字段（同上）
4. ✅ `MappingSkill` 提取并存储 meta 字段：
   - `raw_result.meta.concrete_type`（混凝土类型）
   - `raw_result.meta.test_method`（检测方法）
   - `raw_result.meta.test_instrument`（检测仪器）
   - `raw_result.casting_date`（浇筑日期）
   - `raw_result.test_date`（检测日期）
5. ✅ `ValidationSkill` 生成 `confirmed_result.meta`：
   - `correction_standard_code`（修正规范编号）
   - `correction_standard_name`（修正规范名称）
   - `correction_ref`（修正规范引用）
   - `strength_correction_factor`（强度修正系数）
   - `result_evaluation_text`（评价结果）
6. ✅ 存入 Supabase `professional_data` 表（包含 raw_result 和 confirmed_result）

**状态**：✅ **已打通**（但部分字段可能需要在 Prompt 中明确要求提取）

---

### ⚠️ 报告生成阶段（已修复）

**输入**：章节配置（templateStyle = 'concrete_strength_desc'）

**处理流程**：
1. ✅ **已修复**：前端映射：`concrete_strength_desc` → `dataset_key = 'concrete_strength_description'`
2. ✅ 后端路由：`dataset_key = 'concrete_strength_description'` → 调用 `_generate_strength_description()`
3. ✅ 数据提取：从数据库读取并提取：
   - A类字段：concrete_type, test_method, test_instrument, casting_date, test_date, design_strength_grade
   - B类字段：strength_estimated_mpa, carbonation_depth_avg_mm
   - C类字段：age_days（计算）, strength_min_mpa（统计）, carbonation_depth_over_6（判断）
   - D类字段：correction_standard_code, strength_correction_factor（从 confirmed_result.meta 读取）
4. ✅ 文本生成：`_build_strength_description_text()` 组装描述文本
5. ✅ 输出：返回文本 block（type: "text"）

**状态**：✅ **已打通**（修复前端映射后）

---

## 🔍 发现的问题

### 1. 前端映射错误（已修复）✅

**问题**：
- `concrete_strength_desc` 被错误映射到 `dataset_key = 'concrete_rebound_tests'`
- 导致后端无法识别需要生成描述文本

**修复**：
- 修改前端映射：`concrete_strength_desc` → `dataset_key = 'concrete_strength_description'`

---

### 2. 信息采集阶段字段提取完整性 ⚠️

**潜在问题**：
- `DEFAULT_PROMPT` 主要关注表格数据字段
- 描述文本需要的部分字段（如 `concrete_type`, `test_instrument`）可能不在 Prompt 中明确要求
- 这些字段依赖 `MappingSkill` 从 `raw_result` 中提取，如果 LLM 没有输出，则无法获取

**建议**：
- 在 `DEFAULT_PROMPT` 中明确要求提取：
  - `concrete_type`（混凝土类型，如"泵送混凝土"）
  - `test_instrument`（检测仪器，如"混凝土回弹仪"）
- 或者：在 `ingest_commit` 阶段，如果这些字段缺失，使用默认值或从上下文推断

---

## ✅ 总结

| 链路 | 信息采集 | 数据存储 | 报告生成 | 总体状态 |
|------|---------|---------|---------|---------|
| **PDF → 表格** | ✅ 已打通 | ✅ 已打通 | ✅ 已打通 | ✅ **完全打通** |
| **PDF → 段落** | ⚠️ 部分字段可能缺失 | ✅ 已打通 | ✅ 已打通（修复后） | ⚠️ **基本打通，需完善字段提取** |

---

## 🎯 下一步建议

### 优先级1：完善字段提取

1. **更新 DEFAULT_PROMPT**：
   - 明确要求提取 `concrete_type`（混凝土类型）
   - 明确要求提取 `test_instrument`（检测仪器）
   - 确保 `test_method` 被正确提取

2. **验证数据完整性**：
   - 检查数据库中是否有 `raw_result.meta.concrete_type` 等字段
   - 如果没有，考虑在 MappingSkill 中添加默认值逻辑

### 优先级2：测试验证

1. **端到端测试**：
   - 上传一个完整的回弹法检测表 PDF
   - 验证表格输出是否正常
   - 验证描述文本输出是否包含所有必要信息

2. **字段完整性测试**：
   - 检查生成的描述文本是否包含所有 A-E 类字段
   - 验证派生字段（age_days, strength_min_mpa）是否正确计算

