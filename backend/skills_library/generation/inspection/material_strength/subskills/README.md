# Material Strength Skills - Sub-Skills README

## 子Skills结构

本目录包含材料强度检测的各个子skills，每个子skill独立负责一种材料类型。

### 已实现
- ✅ **concrete_strength** - 混凝土强度（完整实现）

### 待完善
- ⚠️ **brick_strength** - 砌体砖强度（框架已创建）
- ⚠️ **mortar_strength** - 砂浆强度（框架已创建）

## 如何添加新的子skill

1. 复制 `concrete_strength/` 目录结构
2. 修改 SKILL.md 的 dataset_key 和查询条件
3. 修改 fields.yaml 的字段定义（移除不适用的字段，如碳化深度）
4. 修改 render.md 的描述模板
5. 修改 impl/parse.py 的数据提取逻辑

## 统一规范

所有子skills必须遵循：
- 返回结构包含 `has_data`, `material_type`, `content`, `test_count` 等字段
- 无数据时返回 `has_data=false`
- 使用相同的错误处理策略
