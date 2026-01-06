# 架构决策：Entity Extraction Skill 是否必要？

> 讨论时间：2024-12-30

---

## ❓ 问题

**为什么需要Entity Extraction Skill？不是可以直接从Parse到Mapping吗？**

---

## 📊 分析

### 当前架构（Vision-first策略）

```
Parse Skill (Vision-first)
  ↓
  多模态LLM直接输出结构化数据
  ↓
  structured_data: {
    entities: [...],  // 已经包含实体
    tables: [...],
    text: "..."
  }
  ↓
  ?
  ↓
Mapping Skill
```

### 两种可能的架构

#### 架构A：Parse → Entity Extraction → Mapping

```
Parse Skill
  ↓ (输出结构化数据，可能包含entities)
Entity Extraction Skill
  ↓ (进一步提取/标准化entities)
Mapping Skill
  ↓ (映射到专业库schema)
Professional DB
```

**适用场景：**
- Parse只做了基础结构化（提取表格、文本块）
- 需要进一步提取业务实体（构件类型、位置、检测项目）
- 需要合并多页数据
- 需要实体标准化

#### 架构B：Parse → Mapping（跳过Entity Extraction）

```
Parse Skill
  ↓ (直接输出entities，已足够结构化)
Mapping Skill
  ↓ (映射到专业库schema)
Professional DB
```

**适用场景：**
- Parse已经用Vision-first输出完整的entities
- 多模态LLM已经理解了文档结构并提取了实体
- Parse的输出格式已经符合Mapping的输入要求

---

## ✅ 建议（针对Phase 0 + Vision-first）

### **推荐方案：跳过Entity Extraction Skill**

**理由：**

1. **Vision-first策略下，Parse已经足够强**
   - 多模态LLM（GPT-4V/Claude-3.5-Sonnet）可以直接理解文档结构
   - 可以直接输出结构化entities（构件、位置、检测结果等）
   - 不需要额外的实体提取步骤

2. **简化架构，减少调用链**
   - Phase 0目标是"最小可卖Demo"
   - 减少一个Skill = 减少一次LLM调用 = 降低成本和复杂度
   - 更容易调试和维护

3. **文档中已有说明**
   - `PHASE0_PRIORITY_TASKS.md` 明确提到："如果Parse Skill已经用Vision-first输出结构化数据，这一步可以简化或合并"
   - 给出了选项B："合并Parse和Entity Extraction（Parse直接输出entities）"

---

## 🔄 推荐的Phase 0架构

### 简化后的Skill链

```
1. Ingest Skill
   ↓ (文件上传、hash、存储)

2. Parse Skill (Vision-first)
   ↓ (PDF/图片 → 多模态LLM → 结构化entities)
   输出: {
     entities: [
       {component_type: "框架柱", location: "A轴", strength: 30.5, unit: "MPa"},
       ...
     ],
     evidence_refs: [...]
   }

3. Mapping Skill
   ↓ (entities → 专业库schema)
   输入: Parse输出的entities
   输出: professional_data (符合专业库schema)

4. Validation Skill
   ↓ (验证数据完整性)

5. Professional DB
   ↓ (写入专业库)

6. Chapter Generation Skill
   ↓ (从专业库读取，生成章节)
```

### Parse Skill的输出格式

```python
# Parse Skill应该直接输出entities
{
    "parse_id": "parse-xxx",
    "file_category": "pdf",  # 或 "image"
    "page_images": [...],
    "structured_data": {
        # ⚠️ 关键：直接输出entities，而不是原始文本
        "entities": [
            {
                "component_type": "框架柱",
                "component_id": "KZ1",
                "location": {"axis_x": "A", "axis_y": "1"},
                "test_item": "混凝土强度",
                "test_result": 30.5,
                "test_unit": "MPa",
                "page": 2
            },
            # ... 更多实体
        ]
    },
    "evidence_refs": [
        {
            "object_key": "/data/autore/uploads/...",
            "type": "pdf",
            "page": 2,
            "snippet": "框架柱KZ1，混凝土强度30.5MPa",
            "source_hash": "..."
        }
    ]
}
```

### Mapping Skill的输入格式

```python
# Mapping Skill直接从Parse Skill接收entities
async def execute(self, parse_result: dict, project_context: dict) -> dict:
    entities = parse_result["structured_data"]["entities"]
    
    # 规则引擎映射
    rule_mapped = self.rule_engine.map(entities, project_context)
    
    # LLM处理非标准表达
    llm_mapped = await self._llm_map_non_standard_fields(entities, rule_mapped)
    
    # 合并并验证
    professional_data = self._merge_mappings(rule_mapped, llm_mapped)
    
    return {
        "professional_data": professional_data,
        "evidence_refs": parse_result["evidence_refs"]
    }
```

---

## 📝 实现建议

### Phase 0实现方案

1. **Parse Skill增强**
   - 在Vision-first的prompt中明确要求输出entities
   - 定义entities的JSON Schema，让LLM直接输出结构化实体
   - 确保输出格式符合Mapping Skill的输入要求

2. **跳过Entity Extraction Skill**
   - 不在Phase 0实现Entity Extraction Skill
   - Parse Skill直接输出entities给Mapping Skill

3. **如果未来需要Entity Extraction**
   - 可以在Phase 1/2再添加
   - 或者作为Parse Skill的内部优化（如果Parse的输出不够好）

---

## 🎯 结论

**对于Phase 0 + Vision-first策略：**

✅ **不需要单独的Entity Extraction Skill**

✅ **Parse Skill应该直接输出entities**

✅ **架构简化为：Parse → Mapping → Validation → Professional DB → Chapter Generation**

**原因：**
- Vision-first的多模态LLM已经足够强大
- 可以减少LLM调用，降低成本和复杂度
- 符合Phase 0"最小可卖Demo"的目标
- 文档中已有相关说明和建议

---

## 📚 参考

- `PHASE0_PRIORITY_TASKS.md` 第1088-1144行
- "⚠️ Phase 0简化建议"部分

