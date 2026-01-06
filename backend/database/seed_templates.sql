-- backend/database/seed_templates.sql
-- Fill fingerprint and prompt content before running.

-- Template: concrete strength result table (existing)
insert into template_registry (
    template_id,
    dataset_key,
    fingerprint,
    schema_version,
    prompt_version,
    prompt,
    mapping_rules,
    validation_rules,
    status
) values (
    'concrete_strength_v1',
    'concrete_strength',
    'REPLACE_WITH_FINGERPRINT',
    'v1',
    'v1',
    $prompt$
# 回弹法检测表结构化抽取 Skill Prompt（稳定性优先）

## 角色
你是建筑工程质量检测领域的专业抽取引擎，熟悉 JGJ/T 23-2011。
你的首要目标是输出可靠数据，而不是尽量多输出。
不确定时允许输出 null，禁止猜测。

## 输入
输入为一张或多张《回弹法检测混凝土强度原始记录表》扫描图片。
图片可能存在模糊、倾斜、曝光不均或手写干扰。

## 任务
对每一张检测表独立完成字段抽取、校验、计算，并输出 JSON。
任一步失败，不得强行推断。

## 必须输出字段
- 记录编号(record_code)
- 检测部位
- 检测日期
- 设计强度等级
- 混凝土强度推定值_MPa
- 碳化深度计算值_mm（数组）
- 碳化深度平均值_mm

## 输出格式
- 仅输出 JSON
- 多张表输出为 JSON 数组
- 单张表输出为一个对象
$prompt$,
    '{}'::jsonb,
    '{
      "rule_set": {
        "id": "concrete_strength_v1",
        "ruleset": "GB50292-2015-appendix-K",
        "global_rules": {
          "required_fields": ["test_item", "test_result", "test_unit", "evidence_refs"],
          "field_types": {
            "test_item": "string",
            "test_result": "number",
            "test_unit": "string",
            "evidence_refs": "array"
          },
          "evidence_rules": {"min_count": 1}
        },
        "skill_rules": {
          "test_item_whitelist_mode": "warning",
          "test_item_whitelist": ["混凝土抗压强度", "混凝土立方体抗压强度", "concrete_compressive_strength"],
          "unit_rules": {"allowed_units": ["MPa", "N/mm2"], "normalize_map": {"N/mm²": "N/mm2"}}
        },
        "output_policy": {"on_error": "block_write", "on_warning": "allow_write_with_flag"}
      }
    }'::jsonb,
    'active'
)
on conflict (template_id) do update set
  dataset_key      = excluded.dataset_key,
  fingerprint      = excluded.fingerprint,
  schema_version   = excluded.schema_version,
  prompt_version   = excluded.prompt_version,
  prompt           = excluded.prompt,
  mapping_rules    = excluded.mapping_rules,
  validation_rules = excluded.validation_rules,
  status           = excluded.status,
  updated_at       = now();


-- Template: rebound record sheet (header + detail)
insert into template_registry (
    template_id,
    dataset_key,
    fingerprint,
    schema_version,
    prompt_version,
    prompt,
    mapping_rules,
    validation_rules,
    status
) values (
    'rebound_record_v1',
    'concrete_rebound_record_sheet',
    'REPLACE_WITH_FINGERPRINT_2',
    'v1',
    'v1',
    $prompt$
你是建筑检测表格结构化抽取引擎，只输出 JSON。
目标：抽取“回弹原始记录表”的表头与明细。

输出结构：
{
  "header": {
    "test_date_raw": "...",
    "test_date": "...",
    "assessment_type": "...",
    "method": "回弹法",
    "test_method": "回弹法",
    "test_instrument": "混凝土回弹仪",
    "concrete_type": "泵送混凝土"
  },
  "rows": [
    {
      "position": "...",
      "surface_state": "...",
      "design_grade": "C30",
      "construction_date_raw": "...",
      "construction_date": "YYYY-MM-DD",
      "assessment_type": "..."
    }
  ]
}

要求：
- 仅输出 JSON
- 如果缺失填 null
$prompt$,
    '{}'::jsonb,
    '{
      "rule_set": {
        "id": "rebound_record_v1",
        "global_rules": {
          "required_fields": ["test_item", "test_unit", "evidence_refs"],
          "field_types": {
            "test_item": "string",
            "test_unit": "string",
            "evidence_refs": "array"
          },
          "evidence_rules": {"min_count": 1}
        },
        "skill_rules": {
          "test_item_whitelist_mode": "warning",
          "test_item_whitelist": ["混凝土回弹检测-元信息", "混凝土回弹检测-原始记录"]
        },
        "output_policy": {"on_error": "block_write", "on_warning": "allow_write_with_flag"}
      }
    }'::jsonb,
    'active'
)
on conflict (template_id) do update set
  dataset_key      = excluded.dataset_key,
  fingerprint      = excluded.fingerprint,
  schema_version   = excluded.schema_version,
  prompt_version   = excluded.prompt_version,
  prompt           = excluded.prompt,
  mapping_rules    = excluded.mapping_rules,
  validation_rules = excluded.validation_rules,
  status           = excluded.status,
  updated_at       = now();
