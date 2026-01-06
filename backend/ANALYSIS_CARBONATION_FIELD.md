# 碳化深度字段存储方案分析

## 问题
是否应该将碳化深度从 `raw_result` JSON 中提取出来，单独存储为数据库字段（类似 `test_result` 和 `component_type`）？

## 当前方案：从 raw_result 中读取

### 数据结构
- `raw_result` (JSON/TEXT): 存储完整的原始解析数据
  - 包含中文键名：`"碳化深度平均值_mm"`, `"碳化深度计算值_mm"` 等
  - 代码已经支持从 `raw_result` 中读取（第162-166行）

### 优点
1. ✅ **不需要修改数据库schema**
   - 当前表结构已经足够
   - 不需要数据迁移
   
2. ✅ **灵活性高**
   - 可以存储多个相关字段（平均值、计算值数组等）
   - 不同检测项目可能有不同的碳化深度数据结构
   
3. ✅ **已实现**
   - 代码已经支持中文键名作为fallback
   - 可以正常工作

### 缺点
1. ⚠️ **性能稍差**
   - 每次查询需要解析JSON
   - 但如果数据量不大（Phase 0），影响可忽略
   
2. ⚠️ **查询不便**
   - 无法直接在SQL中按碳化深度过滤/排序
   - 但当前需求不需要这种查询

## 方案B：映射到单独字段

### 数据结构
需要在数据库中添加：
```sql
carbonation_depth_avg REAL,  -- 碳化深度平均值(mm)
carbonation_depth_values TEXT,  -- 碳化深度计算值数组(JSON)
```

### 优点
1. ✅ **查询性能更好**
   - 可以直接在SQL中过滤/排序
   - 不需要解析JSON
   
2. ✅ **数据结构更清晰**
   - 与 `test_result`, `component_type` 保持一致
   - 明确的字段定义

3. ✅ **类型安全**
   - 数据库可以约束数据类型（REAL）
   - 减少类型转换错误

### 缺点
1. ❌ **需要数据库迁移**
   - 修改 `init_sqlite.sql` 和 `init_postgres.sql`
   - 现有数据需要迁移（或新字段可为NULL）
   
2. ❌ **需要修改MappingSkill**
   - 需要在映射规则中添加碳化深度字段
   - 需要修改 `concrete_strength.yaml` 配置
   
3. ❌ **灵活性降低**
   - 固定的字段结构
   - 不同检测项目可能需要不同的字段

## 推荐方案

### Phase 0（当前阶段）：继续使用 raw_result ✅

**理由：**
1. **已可工作**：代码已经支持从 `raw_result` 中读取，支持中文键名
2. **不需要迁移**：现有数据可以继续使用
3. **快速迭代**：不需要修改数据库schema和MappingSkill
4. **需求不明确**：碳化深度可能不是所有检测项目的必需字段

### Phase 1+（未来优化）：考虑单独字段

**条件：**
- 如果发现性能瓶颈（数据量大）
- 如果需要基于碳化深度进行复杂查询
- 如果多个检测项目都需要碳化深度字段

## 当前代码实现（已支持）

```python
# chapter_generation_skill.py 第162-166行
carbonation = (
    self._as_number(raw_result.get("carbonation_depth_avg_mm"))  # 英文键名
    or self._as_number(raw_result.get("碳化深度平均值_mm"))      # 中文键名（fallback）
    or self._as_number(raw_result.get("碳化深度平均值"))          # 简化中文键名（fallback）
)
```

**结论：当前方案已经足够，不需要单独字段。** ✅

## 如果未来需要优化，修改步骤

1. **数据库迁移**
   ```sql
   ALTER TABLE professional_data 
   ADD COLUMN carbonation_depth_avg REAL;
   ```

2. **修改MappingSkill**
   - 在映射配置中添加碳化深度字段
   - 在 `_apply_mapping` 中提取碳化深度值

3. **修改ChapterGenerationSkill**
   - 优先从 `record.get("carbonation_depth_avg")` 读取
   - `raw_result` 作为fallback

4. **数据迁移脚本**
   - 从现有记录的 `raw_result` 中提取碳化深度
   - 填充到新字段
