# 架构推荐方案：Skills-first + Orchestrator（弱智能编排）

## 📊 您的当前流程分析

```
用户输入（文本/PDF/图片）
    ↓
解析提取（通用数据提取）
    ↓
存入通用数据库
    ↓
结合项目情况提取
    ↓
存入专业数据库
    ↓
报告生成（从专业数据库读取）
```

### 流程特点

- ✅ **线性流程**：步骤顺序明确，依赖关系清晰
- ✅ **确定性操作**：每个步骤的输入输出相对固定
- ✅ **数据存储需求**：需要持久化到数据库
- ✅ **标准化处理**：处理逻辑相对标准化

---

## 🎯 核心架构：Skills-first + Orchestrator（弱智能编排）

### 架构理念

**将"Agent"拆开看成两层：**

1. **技能层（Skills）**：每个小模块做得极强、极稳、输入输出规范化

   - 单一职责，可独立测试
   - 输入输出严格定义
   - 内部可使用Tools（PDF解析、OCR等）或通过LLM Gateway调用LLM
   - **⚠️ 每个Skill输出都自带追溯信息**（evidence_refs, confidence, source_hash等）
2. **编排层（Orchestrator）**：由两部分组成

   - **执行引擎（Execution Engine）**：负责顺序、依赖、校验、重试、记录审计
   - **策略/路由层（Policy/Router）**：决定用哪个Skill版本、哪个模型、是否重试、是否追问
   - 弱智能：流程可提前定义，但策略层可动态决策
   - **⚠️ 重要：策略层预留Agent升级插槽**，未来如需智能决策，只需升级策略层，无需推翻重来
3. **Agent（强智能编排）**：只有当"编排逻辑无法提前写死"时再上

   - 当前阶段不需要
   - 未来如需动态决策，将策略层升级为Agent即可

### 关键架构边界点

#### A. 模型选择机制

**✅ 默认策略：用户不选模型（强烈建议）**

**理由**：
- **成本可控**：可以做套餐/限额管理
- **质量可控**：能按任务匹配最合适模型
- **工程风险小**：不会因为用户误选导致全链路崩溃

**后端职责**（Orchestrator策略层 + Skills）：

- ✅ **根据任务需求自动选择模型**（根据Skill类型、复杂度、能力要求等）
- ✅ **模型能力匹配**（根据任务需求选择合适模型）
- ✅ **Fallback策略**（如果首选模型不支持，自动降级到兼容模型）
- ✅ **成本/限流控制**（根据成本预算选择合适模型）
- ✅ **动态模型选择**（在不同的Skills、报告生成等环节中，根据实际情况选择不同模型）

**⚠️ 管理员/企业版开关（保留但不暴露给普通用户）**

不是给普通用户，而是给：
- 自己测试
- B端客户有合规要求（例如只能用国产模型）
- 需要做A/B评测

**做法**：用户不可见，在项目级配置里（Project Settings）由管理员设定即可。

**示例场景**：

```
Entity Extraction Skill需要JSON输出
策略层决策：根据能力要求选择支持JSON模式的模型（如claude-3-5-sonnet）
如果首选模型不可用，自动fallback到其他支持JSON的模型（如gpt-4o）

管理员配置：项目A要求只使用国产模型（Qwen/Kimi）
策略层决策：在国产模型范围内选择支持JSON模式的模型
```

#### B. Orchestrator的策略/路由插槽

**当前阶段**（规则驱动）：

- 策略层使用规则引擎
- 基于配置和规则做决策
- 例如：质量差 → 走加强解析路线

**未来扩展**（可升级为Agent）：

- 策略层升级为Agent智能决策
- 执行引擎保持不变
- 例如：Agent分析数据质量，动态选择处理路径

**常见策略场景**：

- 输入质量差 → 走"加强解析路线"（多模型交叉验证）
- Validation发现缺字段 → "追问/补全/降级生成"
- 不同项目模板 → 动态挑选Chapter Skill版本
- 成本控制 → 根据任务复杂度选择合适模型

### 架构设计图

```
┌─────────────────────────────────────────┐
│          前端 UI 层                      │
│  (DataCollectionEditor/ReportEditor)    │
│  - 数据采集节点操作                      │
│  - 报告生成配置                          │
│  - 查看处理结果                          │
│  - 质量反馈入口（某章不对、证据链不可信）│
│  - 证据链可视化（点击展开来源）          │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│        API 服务层                        │
│  (FastAPI / Express)                    │
│  - 接收用户操作请求                      │
│  - 创建Job并提交到队列                   │
│  - 返回job_id和run_id                    │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│   Job Queue (异步任务队列)               │
│   (Redis Queue / Celery / BullMQ)       │
│  - Job状态机（PENDING/RUNNING/SUCCESS/  │
│    FAILED）                              │
│  - 任务调度与重试                        │
│  - UI轮询/WebSocket/SSE更新进度         │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│   LLM Gateway (全局基础设施)             │
│   (Multi-Provider统一抽象层)             │
│  ⚠️ Phase 0只接1-2个Provider            │
│  - OpenAI / 硅基流动（MVP阶段）         │
│  - Phase 2扩展：Anthropic/DeepSeek/     │
│    Qwen/Kimi                            │
│  - 统一结构化输出约束（JSON Schema）     │
│  - 统一重试/退避/超时                   │
│  - 统一token/cost计费与审计             │
│  - 统一模型能力标签                     │
│    (支持function call? JSON mode? 等)   │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      Orchestrator (工作流编排器)         │
│  ┌──────────────────────────────────┐   │
│  │  Skill Registry (技能注册表)     │   │
│  │  - Skill名称/版本                │   │
│  │  - input/output schema           │   │
│  │  - required_capabilities         │   │
│  │  - cost_class / timeout / retry  │   │
│  └──────────────────────────────────┘   │
│  ┌──────────────────────────────────┐   │
│  │  策略/路由层 (Policy/Router)     │   │
│  │  - 决定用哪个Skill版本           │   │
│  │  - 决定用哪个模型（带fallback）  │   │
│  │  - 决定是否重试/追问/降级        │   │
│  │  - 成本/限流策略                 │   │
│  │  ⚠️ 未来可升级为Agent智能决策     │   │
│  └──────────────────────────────────┘   │
│  ┌──────────────────────────────────┐   │
│  │  执行引擎 (Execution Engine)     │   │
│  │  - DAG/顺序执行                  │   │
│  │  - 依赖管理                      │   │
│  │  - 错误处理与重试                │   │
│  │  - 审计日志                      │   │
│  └──────────────────────────────────┘   │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
┌───▼─────────────────────▼──────────────────┐
│         Skills 层（8个核心技能）           │
│  ⚠️ 每个Skill输出都自带追溯信息            │
│     (evidence_refs, confidence, source)   │
│                                            │
│  1. Ingest Skill      (数据上传与元数据)   │
│  2. Parse Skill       (文件解析)           │
│  3. Normalize Skill   (数据标准化)         │
│  4. Entity Extraction (实体抽取)           │
│  5. Mapping Skill     (通用库→专业库)      │
│  6. Validation Skill  (数据验证)           │
│  7. Chapter Generation (章节生成)          │
│  8. Traceability Skill (证据链汇总)        │
│                                            │
│  ┌────────────────────────────────────┐   │
│  │  Tools (内部工具)                  │   │
│  │  - PDF解析 (pdfplumber)            │   │
│  │  - OCR (PaddleOCR/Tesseract)       │   │
│  │  - Excel解析 (pandas)              │   │
│  │  - 数据验证规则引擎                │   │
│  └────────────────────────────────────┘   │
└──────────────┬─────────────────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
┌───▼─────────┐  ┌────────▼────────┐
│  数据库层    │  │  对象存储层      │
│             │  │  (S3/OSS/MinIO) │
│ - 通用数据库 │  │                 │
│ - 专业数据库 │  │ - 原始文件       │
│ - 索引       │  │   (PDF/图片/    │
│ - metadata  │  │    Excel)       │
│ - hash      │  │ - 解析结果文件   │
└─────────────┘  └─────────────────┘
```

---

## 🔧 Skills 模块详解（8个核心技能）

### 1. Ingest Skill（数据采集技能）

**职责**：

- 统一处理文件上传（PDF、图片、Excel、文本）
- 生成统一元数据格式
- 记录采集来源和上下文
- 存储原始文件到对象存储

**输入**：

```json
{
  "file": File,
  "node_id": "collection-xxx",
  "project_id": "project-xxx",
  "data_type": "concrete-strength",
  "uploader": "user-id"
}
```

**输出**：

```json
{
  "ingest_id": "ingest-xxx",
  "metadata": {
    "source": "file-upload",
    "timestamp": "2024-12-30T10:00:00Z",
    "collector": "user-id",
    "project_id": "project-xxx",
    "data_type": "concrete-strength",
    "version": "1.0",
    "file_info": {
      "name": "检测报告.pdf",
      "size": 1024000,
      "type": "application/pdf"
    }
  },
  "object_key": "ingest/ingest-xxx/original.pdf",  // 对象存储key
  "file_hash": "sha256:abc123...",  // 文件hash
  "evidence_refs": []  // 初始为空
}
```

**实现方式**：

- Tools：文件存储到对象存储、元数据生成、hash计算
- 无LLM调用

---

### 2. Parse Skill（解析技能）

**职责**：

- PDF/图片/文本 → 结构化JSON
- 提取原始文本、表格、图片
- 标注置信度
- 保存解析结果到对象存储

**输入**：

```json
{
  "ingest_id": "ingest-xxx",
  "object_key": "ingest/ingest-xxx/original.pdf",
  "file_type": "pdf",
  "evidence_refs": [
    {
      "type": "ingest",
      "id": "ingest-xxx",
      "object_key": "ingest/ingest-xxx/original.pdf"
    }
  ]
}
```

**输出**：

```json
{
  "parse_id": "parse-xxx",
  "raw_text": "检测结果：混凝土强度为30.5MPa...",
  "structured_data": {
    "tables": [
      {
        "page": 1,
        "table": [[...]],
        "confidence": 0.95
      }
    ],
    "images": [
      {
        "page": 1,
        "object_key": "parse/parse-xxx/images/image-1.png",
        "description": "检测现场照片"
      }
    ]
  },
  "confidence_score": 0.92,
  "object_keys": {
    "raw_text": "parse/parse-xxx/raw_text.json",
    "tables": "parse/parse-xxx/tables.json",
    "images": "parse/parse-xxx/images/"
  },
  "evidence_refs": [
    {
      "type": "ingest",
      "id": "ingest-xxx",
      "object_key": "ingest/ingest-xxx/original.pdf",
      "page": null
    }
  ],
  "source_hash": "sha256:def456...",
  "parse_metadata": {
    "parser_version": "1.0",
    "parse_time": "2024-12-30T10:01:00Z"
  }
}
```

**实现方式**：

- **工具优先**：PDF解析（pdfplumber）、OCR（PaddleOCR/Tesseract）、Excel解析（pandas）
- **⚠️ 风险B应对**：质量差时，Policy/Router决策进入enhanced_parse（LLM辅助结构化/纠错）
- 对结构化表格类PDF：纯工具即可
- 对图文混排/扫描件/低质量PDF：LLM增强解析

---

### 3. Normalize Skill（标准化技能）

**职责**：

- 单位统一转换（MPa、kPa、Pa等）
- 术语标准化（强度等级、构件名称）
- 编码标准化（国标编码、企业编码）
- 枚举值规范化

**输入**：

```json
{
  "parse_id": "parse-xxx",
  "structured_data": {
    "strength": "30.5",
    "unit": "Mpa",  // 需要标准化
    "grade": "C30", // 需要验证
    "component": "梁" // 需要标准化为统一术语
  },
  "evidence_refs": [
    {
      "type": "parse",
      "id": "parse-xxx",
      "object_key": "parse/parse-xxx/raw_text.json",
      "page": 2
    }
  ]
}
```

**输出**：

```json
{
  "normalize_id": "normalize-xxx",
  "normalized_data": {
    "strength": 30.5,
    "unit": "MPa",  // 已标准化
    "grade": "C30",
    "component": "beam",  // 已标准化为英文术语
    "component_cn": "梁"
  },
  "normalization_rules_applied": [
    "unit_standardization",
    "component_name_mapping"
  ],
  "evidence_refs": [
    {
      "type": "parse",
      "id": "parse-xxx",
      "object_key": "parse/parse-xxx/raw_text.json",
      "page": 2,
      "bbox": [100, 200, 300, 250]  // 文本位置
    }
  ],
  "confidence": 0.95,
  "source_hash": "sha256:ghi789..."
}
```

**实现方式**：

- Tools：规则引擎、查找表、单位转换库
- 可选LLM：处理特殊情况（非标准术语识别）

---

### 4. Entity Extraction Skill（实体抽取技能）

**职责**：

- 从文本中抽取结构化实体
- 构件识别（构造柱、圈梁、框架梁等）
- 位置信息提取
- 缺陷类型识别
- 检测项目识别

**输入**：

```json
{
  "normalize_id": "normalize-xxx",
  "text": "一层框架柱KZ1，混凝土强度检测结果为30.5MPa，位置：A轴与1轴交点",
  "extraction_schema": {
    "entities": [
      {"name": "component", "type": "构件", "values": ["构造柱", "圈梁", "框架柱"]},
      {"name": "location", "type": "位置"},
      {"name": "strength", "type": "数值", "unit": "MPa"}
    ]
  },
  "llm_provider": "anthropic",  // 由策略层决定
  "llm_model": "claude-3-5-sonnet-20241022",
  "evidence_refs": [
    {
      "type": "normalize",
      "id": "normalize-xxx",
      "object_key": "normalize/normalize-xxx/data.json"
    }
  ]
}
```

**输出**：

```json
{
  "extraction_id": "extract-xxx",
  "entities": {
    "component": {
      "value": "框架柱",
      "code": "KZ1",
      "confidence": 0.95
    },
    "location": {
      "axis": "A轴与1轴交点",
      "floor": "一层",
      "confidence": 0.90
    },
    "strength": {
      "value": 30.5,
      "unit": "MPa",
      "confidence": 0.98
    }
  },
  "evidence_refs": [
    {
      "type": "normalize",
      "id": "normalize-xxx",
      "object_key": "normalize/normalize-xxx/data.json",
      "page": 2,
      "bbox": [100, 200, 300, 250]
    }
  ],
  "confidence": 0.94,
  "source_hash": "sha256:jkl012...",
  "extraction_metadata": {
    "model_used": "claude-3-5-sonnet-20241022",
    "extraction_time": "2024-12-30T10:02:00Z",
    "cost": 0.003  // LLM调用成本
  }
}
```

**实现方式**：

- LLM Gateway调用：结构化输出（多模型支持，由策略层决定模型）
- Tools：实体验证、置信度计算

---

### 5. Mapping Skill（映射技能）- 核心壁垒

**职责**：

- 通用数据库 → 专业数据库的字段映射
- 业务规则落库
- 数据转换和关联
- 这是您系统的核心价值

**输入**：

```json
{
  "extraction_id": "extract-xxx",
  "generic_data": {
    "entities": {...},
    "raw_text": "..."
  },
  "project_context": {
    "project_id": "project-xxx",
    "project_type": "民标安全性",
    "building_type": "框架结构"
  },
  "mapping_rules": {
    "field_mappings": {...},
    "business_rules": {...}
  },
  "llm_provider": "anthropic",  // 由策略层决定
  "llm_model": "claude-3-5-sonnet-20241022",
  "evidence_refs": [
    {
      "type": "extract",
      "id": "extract-xxx",
      "object_key": "extract/extract-xxx/entities.json"
    }
  ]
}
```

**输出**：

```json
{
  "mapping_id": "mapping-xxx",
  "professional_data": {
    "test_item": "混凝土抗压强度",
    "test_result": 30.5,
    "test_unit": "MPa",
    "test_standard": "GB/T 50081-2019",
    "test_date": "2024-12-30",
    "component_type": "框架柱",
    "component_code": "KZ1",
    "location": {
      "floor": "一层",
      "axis": "A轴与1轴交点"
    },
    "project_id": "project-xxx",
    "data_source": {
      "ingest_id": "ingest-xxx",
      "parse_id": "parse-xxx"
    }
  },
  "object_key": "professional/project-xxx/mapping-xxx.json",  // 对象存储key
  "evidence_refs": [
    {
      "type": "extract",
      "id": "extract-xxx",
      "object_key": "extract/extract-xxx/entities.json"
    }
  ],
  "confidence": 0.92,
  "source_hash": "sha256:mno345...",
  "mapping_metadata": {
    "mapping_version": "1.0",
    "mapped_time": "2024-12-30T10:03:00Z",
    "model_used": "claude-3-5-sonnet-20241022",
    "cost": 0.005
  }
}
```

**实现方式**：

- **⚠️ 风险C应对：规则为主、LLM为辅**
  - 先做字段映射表 + 规则引擎（可解释、确定性）
  - LLM只处理"非标准表达/缺省补全/候选建议"
  - 输出必须过schema校验 + evidence约束
- **⚠️ 风险C应对：规则为主、LLM为辅**
  - 先做字段映射表 + 规则引擎（可解释、确定性）
  - LLM只处理"非标准表达/缺省补全/候选建议"
  - 输出必须过schema校验 + evidence约束
- LLM Gateway调用：智能映射（根据项目上下文，由策略层决定模型）
- Tools：规则引擎、字段映射表、业务规则校验

---

### 6. Validation Skill（验证技能）

**职责**：

- 数据完整性校验
- 冲突检测（同一构件多次检测结果是否一致）
- 缺失项清单生成
- 数据质量评分

**输入**：

```json
{
  "mapping_id": "mapping-xxx",
  "professional_data": {...},
  "validation_rules": {
    "required_fields": ["test_item", "test_result", "test_date"],
    "value_ranges": {
      "strength": {"min": 0, "max": 100}
    }
  },
  "evidence_refs": [
    {
      "type": "mapping",
      "id": "mapping-xxx",
      "object_key": "professional/project-xxx/mapping-xxx.json"
    }
  ]
}
```

**输出**：

```json
{
  "validation_id": "validate-xxx",
  "validation_result": {
    "is_valid": true,
    "completeness_score": 0.95,
    "conflicts": [],
    "missing_fields": [],
    "warnings": [
      {
        "field": "test_standard",
        "message": "检测标准未明确指定，使用默认标准"
      }
    ]
  },
  "quality_score": 0.92,
  "evidence_refs": [
    {
      "type": "mapping",
      "id": "mapping-xxx",
      "object_key": "professional/project-xxx/mapping-xxx.json"
    }
  ],
  "confidence": 0.92
}
```

**实现方式**：

- Tools：规则引擎、完整性检查、冲突检测算法
- 可选LLM：复杂业务规则验证

---

### 7. Chapter Generation Skill（章节生成技能）

**职责**：

- 从专业数据库读取数据（⚠️ 风险E：必须先定死专业库schema）
- 严格按照模板生成报告章节
- 支持多模型（每个章节可使用不同模型，由后端策略层根据章节类型和复杂度自动选择）

**输入**：

```json
{
  "chapter_config": {
    "chapter_id": "chapter-xxx",
    "title": "混凝土强度检测",
    "chapter_number": "3.1",
    "prompt": "请详细描述混凝土强度检测结果...",
    // 注意：llm_provider和llm_model由后端策略层根据章节类型、复杂度等自动选择
    "template": "template-id",
    "references": ["GB 50010-2010"]
  },
  "professional_data": {
    "test_results": [...],
    "statistics": {...}
  },
  "project_context": {...},
  "evidence_refs": [
    {
      "type": "professional",
      "id": "prof-data-1",
      "object_key": "professional/project-xxx/prof-data-1.json"
    }
  ]
}
```

**输出**：

```json
{
  "generation_id": "generate-xxx",
  "chapter_content": "3.1 混凝土强度检测\n\n根据检测结果，本项目...",
  "object_key": "chapters/chapter-xxx/content.md",  // 对象存储key
  "evidence_refs": [
    {
      "type": "professional",
      "id": "prof-data-1",
      "object_key": "professional/project-xxx/prof-data-1.json"
    }
  ],
  "confidence": 0.90,
  "generation_metadata": {
    "model_used": "gpt-4o",  // 实际使用的模型（可能被策略层fallback）
    "generation_time": "2024-12-30T10:05:00Z",
    "token_usage": {
      "input_tokens": 1500,
      "output_tokens": 800
    },
    "cost": 0.015
  }
}
```

**实现方式**：

- LLM Gateway调用：内容生成（多模型支持，由后端策略层根据章节类型和复杂度自动选择）
- Tools：模板引擎、内容格式化

**⚠️ 风险E应对**：
- 先选一个最常做、最有商业价值的报告类型
- 先把它的专业库schema定死（10-30个关键字段就够）
- 等这个类型跑通后，再扩展其他报告类型

---

### 8. Traceability Skill（证据链汇总技能）

**职责**：

- **汇总**各Skill输出的追溯信息
- 生成完整的证据链文档
- 生成审计轨迹报告

**⚠️ 重要**：Traceability不是只在最后做，而是贯穿全链路

**每个Skill的输出都应该包含追溯信息**：

```json
{
  "skill_output": {
    // ... 业务数据
    "evidence_refs": [
      {
        "type": "ingest",
        "id": "ingest-xxx",
        "object_key": "ingest/ingest-xxx/original.pdf",
        "page": 2,
        "bbox": [100, 200, 300, 400]  // 页面位置
      }
    ],
    "confidence": 0.95,
    "source_hash": "sha256:abc123...",
    "doc_id": "doc-xxx",
    "metadata": {
      "skill_version": "1.0",
      "execution_time": "2024-12-30T10:00:00Z"
    }
  }
}
```

**Traceability Skill的输入**：

```json
{
  "chapter_id": "chapter-xxx",
  "generation_id": "generate-xxx",
  "skill_outputs": [
    {
      "skill": "ingest",
      "id": "ingest-xxx",
      "evidence_refs": [...],
      "confidence": 1.0
    },
    {
      "skill": "parse",
      "id": "parse-xxx",
      "evidence_refs": [...],
      "confidence": 0.92
    },
    // ... 所有相关Skill的输出
  ]
}
```

**Traceability Skill的输出**：

```json
{
  "traceability_id": "trace-xxx",
  "evidence_chain": [
    {
      "claim": "混凝土强度为30.5MPa",
      "evidence_path": [
        {"skill": "ingest", "id": "ingest-xxx"},
        {"skill": "parse", "id": "parse-xxx"},
        {"skill": "entity_extraction", "id": "extract-xxx"}
      ],
      "source": {
        "type": "file",
        "object_key": "ingest/ingest-xxx/original.pdf",
        "page": 2,
        "bbox": [100, 200, 300, 400]
      },
      "confidence": 0.95
    }
  ],
  "audit_trail": [
    {
      "timestamp": "2024-12-30T10:00:00Z",
      "skill": "ingest",
      "action": "file_upload",
      "actor": "user-id",
      "resource_id": "ingest-xxx",
      "object_key": "ingest/ingest-xxx/original.pdf"
    },
    // ... 完整的操作链
  ],
  "object_key": "traceability/trace-xxx/evidence_chain.json"
}
```

**实现方式**：

- Tools：证据链汇总、审计日志记录、对象存储查询
- 可选LLM：智能证据匹配和关联

---

## ⚠️ 三个"防翻车"设计约束（强烈建议）

### 1. Event Bus / Job Queue（异步任务队列）

**为什么必须要有？**

Parse/OCR/LLM调用都是长耗时任务。如果都走同步HTTP，会遇到：
- 超时问题
- 重试重复执行
- 并发上来后API被拖死

**✅ 最小实现要求：**

1. **Job Queue**（例如Redis Queue / Celery / BullMQ）
   - 异步任务提交和执行
   - 任务持久化和可靠性保证

2. **Job状态机**（PENDING/RUNNING/SUCCEEDED/FAILED）
   - 明确的状态转换
   - 状态查询接口

3. **UI进度更新**（轮询或WebSocket/SSE）
   - 实时显示任务进度
   - 用户友好的等待体验

**实现示例：**

```python
# 任务提交
@app.post("/api/report/generate")
async def generate_report(request: GenerateReportRequest):
    # 创建run_id
    run_id = generate_run_id()
    
    # 创建job并提交到队列
    job = await job_queue.enqueue(
        "generate_report_task",
        run_id=run_id,
        project_id=request.project_id,
        chapter_configs=request.chapters
    )
    
    return {
        "job_id": job.id,
        "run_id": run_id,
        "status": "PENDING"
    }

# 任务执行
@job_queue.task("generate_report_task")
async def generate_report_task(run_id: str, project_id: str, chapter_configs: list):
    # 创建Run Log
    run_log = RunLog.create(run_id, project_id)
    
    try:
        # 执行Orchestrator
        orchestrator = Orchestrator(run_log=run_log)
        result = await orchestrator.execute_workflow(...)
        
        # 更新Run Log
        run_log.mark_completed(result)
        return result
    except Exception as e:
        run_log.mark_failed(str(e))
        raise
```

**这不是"优化"，而是"能不能稳定跑"的分水岭。**

---

### 2. 统一Run Log（一次运行的全链路审计实体）

**核心对象：run_id（或execution_id）**

每次用户点击"生成报告/重跑章节"，都生成一个run。

**Run Log包含：**

```python
class RunLog:
    """一次运行的全链路审计实体"""
    
    run_id: str                    # 唯一标识
    project_id: str                # 项目ID
    user_id: str                   # 用户ID
    run_type: str                  # "report_generation" | "data_collection"
    status: str                    # PENDING | RUNNING | SUCCEEDED | FAILED
    
    # 输入
    inputs: dict                   # 文件hash列表、配置等
    input_files_hash: list[str]    # 输入文件hash列表
    
    # Skill执行列表
    skill_executions: list[dict]   # [
        #   {
        #     "skill_name": "entity_extraction",
        #     "skill_version": "1.0",
        #     "start_time": "2024-12-30T10:00:00Z",
        #     "end_time": "2024-12-30T10:02:00Z",
        #     "status": "SUCCEEDED",
        #     "execution_time_ms": 2000
        #   }
        # ]
    
    # LLM调用记录
    llm_calls: list[dict]          # [
        #   {
        #     "skill_name": "entity_extraction",
        #     "provider": "anthropic",
        #     "model": "claude-3-5-sonnet",
        #     "input_tokens": 1500,
        #     "output_tokens": 800,
        #     "cost": 0.003,
        #     "latency_ms": 1500
        #   }
        # ]
    
    # 输出产物索引
    outputs: dict                  # {
        #   "chapter_contents": ["chapter-1.md", "chapter-2.md"],
        #   "structured_data": ["prof-data-1.json"],
        #   "evidence_chains": ["trace-xxx.json"]
        # }
    
    # 元数据
    created_at: datetime
    completed_at: datetime
    total_cost: float
    total_execution_time_ms: int
```

**好处：**

- ✅ **任何结果可复现**：通过run_id可以回溯完整执行链路
- ✅ **质量反馈能精确对应到某次运行**：用户反馈时可以关联到具体的run_id
- ✅ **成本分析**：可以统计每次运行的cost，做成本优化
- ✅ **A/B测试**：可以对比不同run的结果

**使用示例：**

```python
# 创建Run Log
run_log = RunLog.create(
    run_id=run_id,
    project_id=project_id,
    user_id=user_id,
    run_type="report_generation"
)

# 在执行过程中记录
run_log.record_skill_execution(
    skill_name="entity_extraction",
    skill_version="1.0",
    start_time=start_time,
    end_time=end_time,
    status="SUCCEEDED"
)

run_log.record_llm_call(
    skill_name="entity_extraction",
    provider="anthropic",
    model="claude-3-5-sonnet",
    tokens={"input": 1500, "output": 800},
    cost=0.003,
    latency_ms=1500
)

# 查询Run Log
run_log = RunLog.get(run_id)
print(f"总成本: {run_log.total_cost}")
print(f"执行时间: {run_log.total_execution_time_ms}ms")
```

---

### 3. Data Contract的硬规则（防"越权读取"）

**⚠️ 强约束规则：**

1. **Chapter Generation只能读专业库**（不能读Parse输出原文）
   - 违反此规则会抛出PermissionError
   - 确保数据经过Mapping Skill的标准化处理

2. **Mapping是唯一写专业库入口**
   - 所有写入专业库的操作必须经过Mapping Skill
   - 其他Skill无法直接写入专业库

3. **任何写入必须携带evidence_refs + source_hash**
   - 写入时必须包含完整的追溯信息
   - source_hash用于数据完整性校验

4. **Validation是gating：不通过就降级/追问/拒绝生成**
   - Validation失败时，不能继续后续流程
   - 必须根据策略决定：降级、追问用户、或拒绝生成

**实现示例：**

```python
# Data Contract验证器
class DataContractValidator:
    """数据契约硬规则验证器"""
    
    def validate_read_access(self, skill_name: str, data_source: str):
        """验证读权限"""
        if skill_name == "chapter_generation":
            if data_source != "professional_db":
                raise PermissionError(
                    f"Chapter Generation Skill只能读professional_db，"
                    f"不能读{data_source}"
                )
    
    def validate_write_access(self, skill_name: str, data_source: str):
        """验证写权限"""
        if data_source == "professional_db":
            if skill_name != "mapping":
                raise PermissionError(
                    f"只有Mapping Skill能写professional_db，"
                    f"{skill_name}无权写入"
                )
    
    def validate_write_data(self, output: dict):
        """验证写入数据必须包含evidence_refs和source_hash"""
        if "evidence_refs" not in output or not output["evidence_refs"]:
            raise ValueError("写入数据必须包含evidence_refs")
        
        if "source_hash" not in output:
            raise ValueError("写入数据必须包含source_hash")

# Mapping Skill使用
class MappingSkill:
    async def execute(self, input_data: dict) -> dict:
        # 验证写权限
        self.data_contract_validator.validate_write_access(
            skill_name="mapping",
            data_source="professional_db"
        )
        
        # 执行映射
        professional_data = await self._map_data(input_data)
        
        # 验证写入数据
        self.data_contract_validator.validate_write_data(professional_data)
        
        # 写入专业库
        result = await self.professional_db.insert(professional_data)
        return result

# Chapter Generation Skill使用
class ChapterGenerationSkill:
    async def execute(self, input_data: dict) -> dict:
        # 验证读权限（只能读专业库）
        self.data_contract_validator.validate_read_access(
            skill_name="chapter_generation",
            data_source="professional_db"
        )
        
        # 从专业库读取
        professional_data = await self.professional_db.get(input_data["data_ids"])
        
        # 生成章节
        content = await self._generate_content(professional_data)
        return content

# Validation Skill作为gating
class ValidationSkill:
    async def execute(self, input_data: dict) -> dict:
        validation_result = await self._validate(input_data)
        
        if not validation_result["is_valid"]:
            # gating：不通过就降级/追问/拒绝生成
            if validation_result["severity"] == "error":
                # 拒绝生成
                raise ValidationError("数据验证失败，无法继续")
            elif validation_result["severity"] == "warning":
                # 降级生成或追问用户
                return {
                    "status": "warning",
                    "message": "数据质量警告，建议补充信息",
                    "requires_user_input": True
                }
        
        return validation_result
```

**这条约束会极大提升系统的可信度与工程一致性。**

---

## 🔄 Orchestrator（编排层）

Orchestrator由三部分组成：**Skill Registry** + **策略/路由层** + **执行引擎**

### 1. 策略/路由层（Policy/Router）

**职责**：

- 决定用哪个Skill版本
- 决定用哪个模型（带fallback策略）
- 决定是否重试/追问/降级
- 成本/限流策略
- 模型能力匹配

**关键策略场景**：

```python
# 策略示例
policies = {
    "model_selection": {
        "rule": "根据任务需求选择模型",
        "checks": [
            "是否支持JSON模式",
            "是否支持function calling",
            "token限制",
            "成本预算"
        ],
        "fallback": "自动降级到兼容模型"
    },
    "quality_routing": {
        "input_quality_poor": "加强解析路线（多模型交叉验证）",
        "validation_failed": "追问/补全/降级生成",
        "missing_fields": "触发补全流程"
    },
    "cost_control": {
        "budget_limit": 100,  # 每任务成本上限
        "prefer_cheaper_model": True,
        "fallback_to_cheaper": True
    },
    "template_routing": {
        "project_type_A": "使用Chapter Skill v1",
        "project_type_B": "使用Chapter Skill v2"
    },
    "model_selection_rules": {
        "entity_extraction": {
            "preferred": ["claude-3-5-sonnet", "gpt-4o"],  # 根据能力要求选择
            "required_capabilities": ["json_mode"],
            "fallback": "自动选择支持JSON模式的模型"
        },
        "chapter_generation": {
            "preferred": ["gpt-4o", "claude-3-5-sonnet"],  # 根据章节复杂度选择
            "fallback": "根据成本预算选择合适模型"
        }
    }
}
```

**⚠️ 未来升级路径**：

- 当前：规则引擎驱动策略
- 未来：策略层可升级为Agent智能决策
- 执行引擎保持不变，只需升级策略层

### 2. 执行引擎（Execution Engine）

**职责**：

1. **顺序控制**

   - 按照DAG/顺序执行Skills
   - 处理依赖关系
2. **依赖管理**

   - 确保前置Skill完成后再执行后续Skill
   - 数据传递和状态管理
3. **错误处理和重试**

   - 失败重试机制（基于策略层决策）
   - 降级策略（基于策略层决策）
4. **审计日志**

   - 记录每个Skill的执行状态
   - 性能监控
   - 完整的操作链记录
5. **数据流管理**

   - 在Skills之间传递数据
   - 状态持久化

### 工作流示例

```python
# Orchestrator 工作流定义
workflow = {
    "data_collection": [
        {
            "skill": "ingest",
            "retry": 3,
            "policy": "standard"  # 使用标准策略
        },
        {
            "skill": "parse",
            "depends_on": ["ingest"],
            "policy": "quality_based",  # 基于质量的策略
            "routing": {
                "quality_poor": "enhanced_parse",
                "quality_good": "standard_parse"
            }
        },
        {
            "skill": "normalize",
            "depends_on": ["parse"]
        },
        {
            "skill": "entity_extraction",
            "depends_on": ["normalize"],
            "model_selection": {
                "preferred": ["claude-3-5-sonnet", "gpt-4o"],  # 策略层根据能力要求选择
                "required_capabilities": ["json_mode"],  # 策略层检查能力
                "fallback": "自动选择支持JSON模式的模型"  # 策略层fallback
            }
        },
        {
            "skill": "mapping",
            "depends_on": ["entity_extraction"]
        },
        {
            "skill": "validation",
            "depends_on": ["mapping"],
            "on_failure": "trigger_completion"  # 失败时触发补全
        }
    ],
    "report_generation": [
        {
            "skill": "chapter_generation",
            "parallel": True,
            "template_routing": "project_type_based",
            "model_selection": {
                "preferred": ["gpt-4o", "claude-3-5-sonnet"],  # 策略层根据章节复杂度选择
                "required_capabilities": [],  # 策略层检查
                "fallback": "根据成本预算选择合适模型"  # 策略层fallback
            }
        },
        {
            "skill": "traceability",
            "depends_on": ["chapter_generation"]
        }
    ]
}
```

### 实现方式

- **策略/路由层**：规则引擎（当前）→ 可升级为Agent（未来）
- **执行引擎**：基于规则和配置，使用工作流引擎（如Airflow、Temporal、或自定义）

---

## 🤖 何时需要Agent（强智能编排）？

### 当前阶段：不需要Agent

您的流程是线性的，步骤固定，使用Orchestrator（弱智能）即可。

### 未来可能需要Agent的场景

1. **智能数据关联**

   - 需要根据数据内容动态判断哪些数据应该关联
   - 自动建立复杂的数据关系
2. **报告结构规划**

   - 根据采集的数据自动规划报告章节结构
   - 动态调整章节顺序和内容
3. **异常处理决策**

   - 当数据质量异常时，智能决策修复策略
   - 动态选择备用数据源
4. **多路径工作流**

   - 根据数据特征选择不同的处理路径
   - 无法提前确定执行顺序

---

## 📋 实施建议

### 当前阶段（立即实施）

1. **实现架构组件**

   ```
   backend/
   ├── services/
   │   ├── llm_gateway/          # ⚠️ 全局基础设施
   │   │   ├── gateway.py        # LLM Gateway主类
   │   │   ├── capability_registry.py  # 模型能力注册表
   │   │   ├── cost_tracker.py   # 成本追踪
   │   │   ├── retry_manager.py  # 重试管理
   │   │   └── providers/        # 各Provider适配器
   │   │       ├── openai_provider.py
   │   │       ├── anthropic_provider.py
   │   │       ├── deepseek_provider.py
   │   │       └── ...
   │   ├── orchestrator/
   │   │   ├── skill_registry.py     # ⚠️ Skill注册表
   │   │   ├── execution_engine.py   # 执行引擎
   │   │   ├── policy_router.py      # ⚠️ 策略/路由层
   │   │   ├── workflow_definitions.py
   │   │   └── fallback_strategies.py
   │   ├── data_contract/            # ⚠️ 数据契约
   │   │   ├── contract.py           # Data Contract定义
   │   │   └── validators.py         # 契约验证器
   │   ├── skills/
   │   │   ├── ingest_skill.py
   │   │   ├── parse_skill.py
   │   │   ├── normalize_skill.py
   │   │   ├── entity_extraction_skill.py
   │   │   ├── mapping_skill.py
   │   │   ├── validation_skill.py
   │   │   ├── chapter_generation_skill.py
   │   │   └── traceability_skill.py
   │   └── tools/            # Tools被Skills内部使用
   │       ├── pdf_parser.py
   │       ├── ocr_tool.py
   │       └── ...
   ├── storage/
   │   ├── object_storage.py  # ⚠️ 对象存储客户端
   │   └── storage_config.py
   ├── models/               # 数据模型
   │   ├── generic_db.py
   │   ├── professional_db.py
   │   └── evidence_index.py  # ⚠️ 证据链索引
   └── api/
       ├── routes.py
       └── policy_validator.py  # ⚠️ 配置Policy校验
   ```
2. **Skills设计原则**

   - ✅ **单一职责**：每个Skill只做一件事
   - ✅ **输入输出规范化**：标准化的接口定义（通过Skill Registry注册）
   - ✅ **可独立测试**：每个Skill可以单独测试
   - ✅ **可组合**：Skills之间可以组合使用
   - ✅ **内部可包含Tools和LLM Gateway调用**
   - ✅ **输出包含追溯信息**：evidence_refs, confidence, source_hash
   - ✅ **遵守Data Contract**：遵守数据访问权限和证据链要求
3. **数据库和存储设计**

**⚠️ 增强3：数据库层补充对象存储**

```sql
-- 通用数据库（只存metadata和索引）
CREATE TABLE generic_data (
    id UUID PRIMARY KEY,
    ingest_id UUID,
    parse_id UUID,
    raw_text_hash VARCHAR(64),  -- SHA256 hash
    object_key VARCHAR,  -- 对象存储key（如：generic/parse-xxx/raw_text.json）
    structured_data_hash VARCHAR(64),
    structured_data_key VARCHAR,
    created_at TIMESTAMP,
    INDEX idx_ingest_id (ingest_id),
    INDEX idx_hash (raw_text_hash)
);

-- 专业数据库
CREATE TABLE professional_data (
    id UUID PRIMARY KEY,
    project_id VARCHAR,
    mapping_id UUID,
    data_type VARCHAR,
    data_content_hash VARCHAR(64),
    data_content_key VARCHAR,  -- 对象存储key
    created_at TIMESTAMP,
    INDEX idx_project_id (project_id),
    INDEX idx_data_type (data_type)
);

-- 审计日志
CREATE TABLE audit_trail (
    id UUID PRIMARY KEY,
    workflow_id UUID,
    skill_name VARCHAR,
    skill_version VARCHAR,
    input_hash VARCHAR(64),
    input_key VARCHAR,  -- 对象存储key
    output_hash VARCHAR(64),
    output_key VARCHAR,
    status VARCHAR,
    error_message TEXT,
    execution_time INTEGER,
    cost DECIMAL(10, 4),  -- 本次执行成本
    model_used VARCHAR,
    created_at TIMESTAMP,
    INDEX idx_workflow_id (workflow_id),
    INDEX idx_skill_name (skill_name)
);

-- 证据链索引
CREATE TABLE evidence_index (
    id UUID PRIMARY KEY,
    skill_output_id UUID,
    evidence_type VARCHAR,  -- ingest, parse, extract, etc.
    evidence_id UUID,
    object_key VARCHAR,  -- 对象存储key
    page_number INTEGER,
    bbox JSONB,  -- 页面位置 [x, y, width, height]（⚠️ 风险D：Phase 0只做page级，V2再做bbox）
    confidence DECIMAL(3, 2),
    created_at TIMESTAMP,
    INDEX idx_skill_output_id (skill_output_id),
    INDEX idx_evidence_id (evidence_id)
);

-- Run Log（运行日志）- ⚠️ 防翻车关键表
CREATE TABLE run_log (
    run_id UUID PRIMARY KEY,
    project_id VARCHAR,
    user_id VARCHAR,
    run_type VARCHAR,  -- report_generation, data_collection
    status VARCHAR,    -- PENDING, RUNNING, SUCCEEDED, FAILED
    inputs JSONB,      -- 输入配置
    input_files_hash JSONB,  -- 输入文件hash列表
    skill_executions JSONB,  -- Skill执行列表
    llm_calls JSONB,   -- LLM调用记录
    outputs JSONB,     -- 输出产物索引
    total_cost DECIMAL(10, 4),
    total_execution_time_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMP,
    completed_at TIMESTAMP,
    INDEX idx_project_id (project_id),
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);

-- Job Queue表（如果使用数据库作为队列后端）
CREATE TABLE job_queue (
    job_id UUID PRIMARY KEY,
    run_id UUID,
    job_type VARCHAR,
    status VARCHAR,  -- PENDING, RUNNING, SUCCEEDED, FAILED
    payload JSONB,
    result JSONB,
    error_message TEXT,
    created_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    INDEX idx_run_id (run_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);
```

**对象存储结构**：

```
对象存储 (S3/OSS/MinIO)
├── ingest/
│   └── {ingest_id}/
│       └── original.pdf
├── parse/
│   └── {parse_id}/
│       ├── raw_text.json
│       ├── tables.json
│       └── images/
│           └── image-1.png
├── generic/
│   └── {generic_data_id}/
│       └── structured_data.json
└── professional/
    └── {project_id}/
        └── {professional_data_id}.json
```

**好处**：

- ✅ 审计与追溯更靠谱（原始文件永久保存）
- ✅ 后期重跑解析/更新模型不会丢原始证据
- ✅ 数据库只存metadata，查询更快
- ✅ 可以版本化管理（同一文件的不同解析版本）

---

## 💡 关键技术点

### 1. LLM Gateway（全局基础设施）

**⚠️ 增强1：LLM Gateway作为共享基础设施，而非Skills内部组件**

LLM Gateway是全局基础设施，Skills通过Gateway调用LLM，就像调用数据库、对象存储一样。

**LLM Gateway职责**：

```python
class LLMGateway:
    """全局LLM Gateway，提供统一接口"""
  
    def __init__(self):
        self.providers = {...}  # 多提供商适配器
        self.capability_registry = {}  # 模型能力注册表
        self.cost_tracker = CostTracker()  # 成本追踪
        self.retry_manager = RetryManager()  # 重试管理
  
    async def chat_completion(
        self,
        provider: str,
        model: str,
        messages: list[dict],
        required_capabilities: list[str] = None,  # 如：["json_mode", "function_calling"]
        **kwargs
    ) -> dict:
        """
        统一的LLM调用接口
      
        功能：
        - 能力检查（模型是否支持required_capabilities）
        - 统一结构化输出约束（JSON Schema验证）
        - 统一重试/退避/超时策略
        - 统一token/cost计费与审计
        - Fallback策略
        """
        # 1. 能力检查
        if required_capabilities:
            if not self.check_capabilities(provider, model, required_capabilities):
                # 自动fallback到支持该能力的模型
                model = self.find_compatible_model(provider, required_capabilities)
      
        # 2. 成本检查
        if not self.cost_tracker.check_budget(model, kwargs.get('max_tokens', 4096)):
            raise BudgetExceededError("成本预算超限")
      
        # 3. 调用LLM（带重试）
        response = await self.retry_manager.execute_with_retry(
            lambda: self._call_llm(provider, model, messages, **kwargs)
        )
      
        # 4. 统一输出验证（JSON Schema）
        if kwargs.get('response_format') == {'type': 'json_object'}:
            response['content'] = self.validate_json_schema(
                response['content'],
                kwargs.get('json_schema')
            )
      
        # 5. 成本记录
        self.cost_tracker.record_usage(provider, model, response['usage'])
      
        return response
  
    def get_model_capabilities(self, provider: str, model: str) -> dict:
        """获取模型能力标签"""
        return self.capability_registry.get(f"{provider}:{model}", {
            "json_mode": False,
            "function_calling": False,
            "max_tokens": 4096,
            "cost_per_1k_tokens": 0.01
        })
```

**模型能力注册表示例**：

```python
CAPABILITY_REGISTRY = {
    "openai:gpt-4o": {
        "json_mode": True,
        "function_calling": True,
        "max_tokens": 16384,
        "cost_per_1k_input": 0.005,
        "cost_per_1k_output": 0.015
    },
    "anthropic:claude-3-5-sonnet-20241022": {
        "json_mode": True,
        "function_calling": True,
        "max_tokens": 8192,
        "cost_per_1k_input": 0.003,
        "cost_per_1k_output": 0.015
    },
    "deepseek:deepseek-chat": {
        "json_mode": True,
        "function_calling": True,
        "max_tokens": 16384,
        "cost_per_1k_input": 0.0001,
        "cost_per_1k_output": 0.0002
    },
    # ... 其他模型
}
```

### 2. Skills内部架构

每个Skill通过LLM Gateway调用LLM，并自带追溯信息：

```python
class EntityExtractionSkill:
    """实体抽取Skill"""
  
    def __init__(self, llm_gateway: LLMGateway, model_selector: ModelSelector, tools: dict):
        self.llm_gateway = llm_gateway  # 通过Gateway调用LLM
        self.model_selector = model_selector  # 模型选择器
        self.validator = tools['validator']  # Tools
  
    async def execute(self, input_data: dict) -> dict:
        # 1. 使用Tools预处理
        preprocessed = self.validator.validate_input(input_data)
      
        # 2. 通过LLM Gateway调用LLM
        # Gateway会自动处理能力检查、成本控制、重试等
        entities_response = await self.llm_gateway.chat_completion(
            provider=input_data.get('llm_provider', 'anthropic'),
            model=input_data.get('llm_model', 'claude-3-5-sonnet-20241022'),
            messages=[{"role": "user", "content": self._build_prompt(preprocessed)}],
            required_capabilities=["json_mode"],  # Gateway会确保模型支持
            response_format={"type": "json_object"},
            json_schema=self._get_extraction_schema()
        )
      
        entities = json.loads(entities_response['content'])
      
        # 3. 使用Tools后处理
        validated_entities = self.validator.validate_entities(entities)
      
        # 4. 构建输出（包含追溯信息）
        return {
            "entities": validated_entities,
            # ⚠️ 追溯信息：每个Skill输出都包含
            "evidence_refs": input_data.get('evidence_refs', []),  # 继承上游
            "confidence": self._calculate_confidence(validated_entities),
            "source_hash": self._calculate_hash(input_data),
            "metadata": {
                "skill_version": "1.0",
                "execution_time": datetime.now().isoformat(),
                "model_used": entities_response.get('model'),
                "cost": entities_response.get('usage', {}).get('cost', 0)
            }
        }
```

### 3. 模型选择器（ModelSelector）

```python
# services/orchestrator/model_selector.py
class ModelSelector:
    """模型选择器 - 根据任务需求自动选择模型"""
    
    def __init__(self, llm_gateway: LLMGateway):
        self.llm_gateway = llm_gateway
    
    def select_model(
        self,
        skill_name: str,
        required_capabilities: list[str],
        task_complexity: str = "medium",  # simple, medium, complex
        cost_budget: float = None
    ) -> dict:
        """
        根据任务需求自动选择模型
        
        返回：
        {
            "provider": str,  # 选择的provider
            "model": str,     # 选择的model
            "capabilities": dict,  # 模型能力
            "cost_per_1k_tokens": float  # 成本
        }
        """
        # 1. 根据能力要求筛选候选模型
        candidates = self.llm_gateway.find_models_with_capabilities(
            required_capabilities
        )
        
        # 2. 根据任务复杂度过滤
        if task_complexity == "simple":
            # 简单任务优先选择成本低的模型
            candidates = sorted(candidates, key=lambda x: x["cost_per_1k_tokens"])
        elif task_complexity == "complex":
            # 复杂任务优先选择能力强的模型
            candidates = sorted(candidates, key=lambda x: -x["max_tokens"])
        
        # 3. 根据成本预算过滤
        if cost_budget:
            candidates = [c for c in candidates if c["cost_per_1k_tokens"] <= cost_budget]
        
        # 4. 选择第一个候选模型
        selected = candidates[0] if candidates else None
        
        if not selected:
            # 如果找不到合适模型，使用fallback
            selected = self.llm_gateway.get_default_model(required_capabilities)
        
        return {
            "provider": selected["provider"],
            "model": selected["model"],
            "capabilities": selected["capabilities"],
            "cost_per_1k_tokens": selected["cost_per_1k_tokens"]
        }
```

---

## 🎯 总结建议

### ✅ 当前阶段（推荐）

- **Skills-first架构**：8个核心Skills模块
- **Orchestrator（弱智能）**：策略/路由层 + 执行引擎
- **LLM Gateway**：全局基础设施，统一管理多模型
- **对象存储 + 数据库**：原始文件存对象存储，数据库存metadata
- **Traceability贯穿全链路**：每个Skill输出包含追溯信息
- **后端自动模型选择**：在Skills执行和报告生成时，后端策略层根据任务需求自动选择合适模型

### 🔄 未来演进

- 当需要动态决策、复杂推理时，将策略层升级为Agent智能决策
- 执行引擎保持不变，只需升级策略层

### 📊 Skills vs Agent对比

| 特性               | Skills + Orchestrator | Agent（强智能）    |
| ------------------ | --------------------- | ------------------ |
| **适用场景** | 线性流程、固定步骤    | 动态决策、复杂推理 |
| **编排方式** | 规则和配置            | LLM规划            |
| **成本**     | 低（单次LLM调用）     | 高（多次LLM调用）  |
| **可预测性** | 高                    | 中等               |
| **可维护性** | 高                    | 中等               |
| **性能**     | 快                    | 相对慢             |

**结论：当前阶段，Skills-first + Orchestrator 更适合您的需求！**

---

## 🚀 下一步行动

1. ✅ 确认架构方案（Skills-first + Orchestrator + Policy/Router）
2. ✅ 实现LLM Gateway（全局基础设施）
   - 模型能力注册表
   - 成本追踪
   - 重试管理
   - 能力检查和Fallback
3. ✅ 实现Skill Registry
   - Skill注册机制
   - Schema定义
   - 版本管理
   - 能力标签
4. ✅ 实现Data Contract
   - 数据访问权限定义
   - 只读专业库原则
   - 证据链验证
   - 审计日志
5. ✅ 实现Orchestrator策略/路由层
   - Policy校验规则
   - 模型选择策略（默认用户不选，保留管理员开关）
   - Fallback策略
   - 成本控制策略
6. ✅ 实现Orchestrator执行引擎
   - DAG执行
   - 依赖管理
   - 错误处理
7. ✅ 设计8个Skills模块的接口规范（包含追溯信息）
   - 在Skill Registry中注册
   - 定义input/output schema
   - 定义required_capabilities
8. ✅ 实现对象存储集成（S3/OSS/MinIO）
9. ✅ 实现基础Tools（PDF解析、OCR等）
10. ✅ 实现核心Skills（从Ingest开始）
   - 每个Skill输出包含evidence_refs、confidence、source_hash
   - 遵守Data Contract
11. ✅ 实现前端UI关键功能
   - 质量反馈入口（某章不对、证据链不可信）
   - 证据链可视化（点击展开来源）
12. ✅ 测试和优化

## 📝 架构边界点总结

### A. 模型选择机制

- **后端策略层**：根据任务需求、能力要求、成本预算等自动选择模型
- **Skills和报告生成**：在执行时根据实际情况选择合适模型
- **Fallback机制**：如果首选模型不可用，自动降级到兼容模型
- **结果**：确保模型支持所需能力，控制成本，避免链路崩溃

### B. Orchestrator策略/路由插槽

- **当前**：规则引擎驱动的策略层
- **未来**：策略层可升级为Agent智能决策
- **执行引擎**：保持不变，只需升级策略层

### C. 三大增强

1. **LLM Gateway作为全局基础设施**：统一管理、成本控制、能力检查
2. **Traceability贯穿全链路**：每个Skill输出都包含追溯信息
3. **对象存储 + 数据库**：原始文件存对象存储，数据库只存metadata和索引

### D. 两个落地必备开关

1. **Skill Registry（技能注册表）**
   - Skill名称/版本、input/output schema
   - required_capabilities、cost_class、timeout、retry policy
   - 支持版本灰度发布、动态Skill选择

2. **Data Contract（数据契约）+ "只读专业库"原则**
   - Chapter Generation Skill只能读专业库
   - Mapping Skill是唯一能写专业库的入口（加审计）
   - 所有输出必须可追溯到evidence_refs

### E. 三个"防翻车"设计约束（强烈建议）

1. **Event Bus / Job Queue（异步任务队列）**
   - Parse/OCR/LLM调用都是长耗时任务，必须异步化
   - Job Queue（Redis Queue / Celery / BullMQ）
   - Job状态机（PENDING/RUNNING/SUCCEEDED/FAILED）
   - UI轮询或WebSocket/SSE更新进度
   - **这不是"优化"，而是"能不能稳定跑"的分水岭**

2. **统一Run Log（一次运行的全链路审计实体）**
   - 核心对象：run_id（或execution_id）
   - 记录：inputs、skill执行列表、LLM调用记录、输出产物索引
   - 好处：任何结果可复现、质量反馈能精确对应、成本分析、A/B测试

3. **Data Contract的硬规则（防"越权读取"）**
   - Chapter Generation只能读专业库（硬约束，违反抛出PermissionError）
   - Mapping是唯一写专业库入口（硬约束）
   - 任何写入必须携带evidence_refs + source_hash（硬约束）
   - Validation是gating：不通过就降级/追问/拒绝生成（硬约束）
   - **这条约束会极大提升系统的可信度与工程一致性**

---

## ⚠️ 需要特别注意的5个风险点（否则容易做着做着变重）

### 风险A：过早做"多Provider + 动态选模"

**问题**：
文档把LLM Gateway写得很完整，但早期如果同时接OpenAI/Anthropic/DeepSeek/Qwen/Kimi…会明显拖慢交付。

**建议**：
- ✅ **MVP阶段只接1-2个模型**
- ✅ capability registry / fallback先做"框架"，但别把provider接满
- ✅ 例如只选择：**OpenAI + 硅基流动**（一个国外主流，一个国产）
- ✅ 等Phase 2再扩展多Provider

**实施**：
```python
# MVP阶段：只初始化2个Provider
if PHASE == "MVP":
    providers = ["openai", "siliconflow"]
else:
    providers = ["openai", "anthropic", "deepseek", "qwen", "kimi", "siliconflow"]
```

---

### 风险B：Parse Skill"完全不走LLM"在真实PDF上可能不够

**问题**：
文档建议Parse纯工具（pdfplumber/OCR），这对结构化表格类PDF很好；但很多检测报告是"图文混排 + 扫描件 + 低质量"，纯工具会丢语义。

**建议**：
- ✅ Parse保持"工具优先"
- ✅ 但给Policy/Router留一个开关：质量差时进入enhanced_parse（LLM辅助结构化/纠错）

**实施**：
```python
class ParseSkill:
    async def execute(self, input_data: dict) -> dict:
        # 1. 先用工具解析
        result = await self.tool_parse(input_data)
        
        # 2. 评估质量
        quality_score = self._assess_quality(result)
        
        # 3. 如果质量差，使用LLM增强
        if quality_score < 0.7:
            # Policy/Router决策：进入enhanced_parse
            enhanced_result = await self.llm_enhanced_parse(result)
            return enhanced_result
        
        return result
```

---

### 风险C：Mapping Skill既要"智能"又要"可控"——最难

**问题**：
文档把Mapping定位为核心壁垒非常准确。但Mapping如果全靠LLM，会出现"同一输入，多次映射不一致"。

**建议**：
- ✅ **Mapping必须"规则为主、LLM为辅"**：
  - 先做字段映射表 + 规则引擎（可解释）
  - LLM只处理"非标准表达/缺省补全/候选建议"
  - 并且输出必须过schema校验 + evidence约束

**实施**：
```python
class MappingSkill:
    async def execute(self, input_data: dict) -> dict:
        # 1. 规则引擎映射（确定性字段）
        rule_mapped = self.rule_engine.map(input_data)
        
        # 2. LLM处理非标准表达（不确定性字段）
        llm_mapped = await self.llm_map_non_standard_fields(
            input_data,
            rule_mapped
        )
        
        # 3. 合并结果
        merged = self._merge_mappings(rule_mapped, llm_mapped)
        
        # 4. Schema校验（硬约束）
        validated = self.schema_validator.validate(merged)
        
        # 5. Evidence约束（硬约束）
        if not validated.get("evidence_refs"):
            raise ValueError("Mapping输出必须包含evidence_refs")
        
        return validated
```

---

### 风险D：证据链做到bbox级别会很耗工

**问题**：
bbox/页码级溯源非常值钱，但实现成本也高（尤其OCR后的文字定位）。

**建议**：
- ✅ **分两级落地**：
  - **MVP**：page级引用（page + object_key + snippet）
  - **V2**：再做bbox（重点章节、重点结论优先）

**实施**：
```python
# MVP阶段：page级证据链
evidence_ref = {
    "type": "parse",
    "id": "parse-xxx",
    "object_key": "parse/parse-xxx/raw_text.json",
    "page": 2,  # 只到page级别
    "snippet": "检测结果：混凝土强度为30.5MPa"  # 文本片段
}

# V2阶段：bbox级证据链（重点章节优先）
evidence_ref = {
    "type": "parse",
    "id": "parse-xxx",
    "object_key": "parse/parse-xxx/raw_text.json",
    "page": 2,
    "bbox": [100, 200, 300, 250],  # 精确位置
    "snippet": "检测结果：混凝土强度为30.5MPa"
}
```

---

### 风险E：Chapter Generation"只能读专业库"是对的，但会逼你先把专业库设计好

**问题**：
文档的硬规则很正确。但现实：专业库schema没定好，章节生成就会反复返工。

**建议**：
- ✅ **先选一个你最常做、最有商业价值的报告类型**
- ✅ 先把它的专业库schema定死（10-30个关键字段就够）
- ✅ 等这个类型跑通后，再扩展其他报告类型

**实施**：
```python
# 先定义核心报告类型的专业库schema
PROFESSIONAL_DB_SCHEMA = {
    "民标安全性": {
        "test_item": str,           # 检测项目
        "test_result": float,       # 检测结果
        "test_unit": str,           # 单位
        "test_standard": str,       # 检测标准
        "test_date": datetime,      # 检测日期
        "component_type": str,      # 构件类型
        "component_code": str,      # 构件编号
        "location": dict,           # 位置信息
        "project_id": str,          # 项目ID
        # ... 10-30个关键字段
    }
}
```

---

## 🚀 AutoRe开发路径（最省时间、最容易出Demo/签单）

**核心策略：先做"一个报告类型闭环"，不要一上来做平台。**

### Phase 0（1个闭环：最小可卖Demo）

**目标**：能跑通"上传→专业库→生成1-2个关键章节→证据链→可下载"

**必做**：

1. ✅ **Ingest + Object Storage + Hash**（证据保全）
2. ✅ **Parse**（工具优先，质量差时LLM增强）
3. ✅ **Entity Extraction**（JSON schema输出，只接1-2个模型）
4. ✅ **Mapping**（先规则后智能，schema定死）
5. ✅ **Chapter Generation**（只读专业库，生成1-2个关键章节）
6. ✅ **Run Log**（最简字段也要有：run_id, status, cost）
7. ✅ **UI**：结果展示 + 反馈入口（先不做复杂编辑器）

**先别做**：
- ❌ 多模板
- ❌ 多provider（只接1-2个）
- ❌ 复杂DAG
- ❌ bbox级证据链（只做page级）
- ❌ Skill Registry完整版（先写死调用）
- ❌ Validation完整版（先简单校验）

**时间估算**：2-4周

---

### Phase 1（可交付版本：稳定 + 可审计）

**目标**：稳定运行，可审计，可交付给客户

**新增**：

1. ✅ **Job Queue**（异步化，避免超时）
2. ✅ **Validation gating**（缺失/冲突→追问/降级/拒绝）
3. ✅ **Traceability汇总**（page级证据链）
4. ✅ **Skill Registry**（版本管理 + schema）
5. ✅ **Data Contract硬规则**（防越权读取）
6. ✅ **UI**：证据链可视化（page级）

**时间估算**：4-6周

---

### Phase 2（平台化：多报告类型、多项目、多团队）

**目标**：支持多报告类型，多项目并行，团队协作

**新增**：

1. ✅ **LLM Gateway完整化**（capability registry、fallback、成本策略）
2. ✅ **多Provider支持**（OpenAI/Anthropic/DeepSeek/Qwen/Kimi/硅基流动）
3. ✅ **多模板、多章节并行生成**（parallel）
4. ✅ **管理员策略**（国产模型限定、A/B测试）
5. ✅ **多报告类型支持**（扩展专业库schema）
6. ✅ **bbox级证据链**（重点章节优先）

**时间估算**：8-12周

---

### Phase 3（再考虑Agent）

**目标**：智能决策、动态规划

**何时引入**：
- 只有当出现"动态章节规划、多路径决策、复杂异常修复"等真实需求时
- 再把Policy/Router升级为Agent

**时间估算**：根据实际需求

---

## 📋 分阶段实施建议

### Phase 0 实施清单（最小可卖Demo）

```
backend/
├── services/
│   ├── skills/
│   │   ├── ingest_skill.py          ✅ 必做
│   │   ├── parse_skill.py           ✅ 必做（工具优先）
│   │   ├── entity_extraction_skill.py  ✅ 必做（只接1-2个模型）
│   │   ├── mapping_skill.py         ✅ 必做（规则为主）
│   │   └── chapter_generation_skill.py  ✅ 必做（只读专业库）
│   ├── llm_gateway/                 ⚠️ 简化版（只接1-2个Provider）
│   │   └── gateway.py
│   └── tools/
│       ├── pdf_parser.py            ✅ 必做
│       └── ocr_tool.py              ✅ 必做
├── storage/
│   └── object_storage.py            ✅ 必做
├── models/
│   └── professional_db.py           ✅ 必做（先定死一个报告类型schema）
└── api/
    └── routes.py                    ✅ 必做
```

**数据库（Phase 0最小集）**：

```sql
-- 专业数据库（先定死一个报告类型）
CREATE TABLE professional_data (
    id UUID PRIMARY KEY,
    project_id VARCHAR,
    test_item VARCHAR,              -- 检测项目
    test_result DECIMAL(10, 2),      -- 检测结果
    test_unit VARCHAR,               -- 单位
    component_type VARCHAR,          -- 构件类型
    location JSONB,                 -- 位置信息
    evidence_refs JSONB,            -- 证据链（page级）
    created_at TIMESTAMP
);

-- Run Log（最简版）
CREATE TABLE run_log (
    run_id UUID PRIMARY KEY,
    project_id VARCHAR,
    status VARCHAR,
    total_cost DECIMAL(10, 4),
    created_at TIMESTAMP
);
```

---

### Phase 1 实施清单（可交付版本）

在Phase 0基础上新增：

```
backend/
├── services/
│   ├── job_queue/                  ✅ 新增
│   │   └── queue.py
│   ├── orchestrator/
│   │   ├── skill_registry.py       ✅ 新增
│   │   └── execution_engine.py   ✅ 新增
│   ├── data_contract/              ✅ 新增
│   │   └── validators.py
│   ├── skills/
│   │   ├── validation_skill.py     ✅ 新增（gating）
│   │   └── traceability_skill.py  ✅ 新增（汇总）
```

---

### Phase 2 实施清单（平台化）

在Phase 1基础上新增：

```
backend/
├── services/
│   ├── llm_gateway/                ✅ 完整化
│   │   ├── capability_registry.py
│   │   ├── cost_tracker.py
│   │   └── providers/              ✅ 扩展多Provider
│   ├── orchestrator/
│   │   └── policy_router.py       ✅ 完整化（管理员策略）
```

---

## 🎯 关键决策点

### 何时扩展多Provider？

- ✅ Phase 0：只接1-2个（OpenAI + 硅基流动）
- ✅ Phase 1：保持1-2个，完善框架
- ✅ Phase 2：扩展到6个Provider

### 何时做bbox级证据链？

- ✅ Phase 0：只做page级
- ✅ Phase 1：保持page级
- ✅ Phase 2：重点章节做bbox级

### 何时引入Agent？

- ✅ Phase 0-2：不需要
- ✅ Phase 3：根据实际需求再引入

需要我帮您实现具体的某个模块吗？
