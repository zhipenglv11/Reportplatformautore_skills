# 后端开发进度检查清单

> 更新时间：2025-01-03
> 最后检查：2025-01-03（章节配置功能完善，报告生成逻辑修复）

---

## ✅ 已完成（前置条件）

### 1. 基础项目结构 ✅

- [X] `backend/main.py` - FastAPI应用入口
- [X] `backend/config.py` - 配置管理（支持OpenAI和硅基流动）
  - ✅ 本地存储路径配置（默认：项目根目录/data）
  - ✅ Poppler bin路径配置支持（可选）
- [X] `backend/api/routes.py` - API路由框架（已实现报告生成路由）
- [X] `backend/requirements.txt` - 依赖定义
- [X] 目录结构已创建（services/, models/, storage/, schemas/, contracts/, database/）

### 2. 数据库 ✅

- [X] `backend/database/init_sqlite.sql` - SQLite表结构定义（Phase 0）
- [X] `backend/database/init_postgres.sql` - PostgreSQL表结构定义（Phase 1+）
- [X] `backend/database/init_db.py` - 数据库初始化脚本
- [X] `backend/phase0.db` - SQLite数据库文件已创建
- [X] `professional_data` 表结构已定义（包含完整字段：raw_result, confirmed_result, result_version等）
- [X] `run_log` 表结构已定义（包含完整字段：stage, prompt_version, schema_version等）

### 3. 配置和Schema ✅

- [X] `backend/schemas/evidence_ref.json` - 证据链Schema
- [X] `backend/schemas/professional_data.json` - 专业数据Schema
- [X] `backend/contracts/data_contract.py` - 数据契约定义
- [X] `.env` 配置示例（需要手动创建并填入API Key）

### 4. LLM Gateway ✅

- [X] `backend/services/llm_gateway/gateway.py` - LLM Gateway实现
- [X] 支持多个LLM Provider：OpenAI、硅基流动（SiliconFlow）、Moonshot、Qwen
- [X] 提供 `chat_completion()` 和 `vision_completion()` 接口
- [X] 默认使用 Qwen 作为 LLM Provider

### 5. CORS配置 ✅

- [X] FastAPI CORS中间件已配置
- [X] 允许前端端口：localhost:5173, localhost:3000

---

## ⚠️ 待完成（核心功能）

### 1. Skills实现（6/6）✅ 核心功能完成，部分流程待打通

- [X] `backend/services/skills/ingest_skill.py` - 文件上传和存储 ✅ **已完成**
- [X] `backend/services/skills/parse_skill.py` - Vision-first解析（PDF/图片） ✅ **已完成**
- [ ] ~~`backend/services/skills/entity_extraction_skill.py`~~ - **已跳过**（根据架构决策，Parse直接输出entities）
- [X] `backend/services/skills/mapping_skill.py` - 数据映射（规则为主） ✅ **已完成**
- [X] `backend/services/skills/validation_skill.py` - 最小验证 ✅ **已完成**
- [X] `backend/services/skills/template_profile_skill.py` - 模板识别 ✅ **已完成（部分）**
  - ✅ 实现表头识别和指纹计算（fingerprint）
  - ✅ 集成到 `upload_file` 接口（返回 template_profile 和 fingerprint）
  - ⚠️ **待打通**：识别到的模板指纹如何自动匹配到 template_id
  - ⚠️ **待打通**：在 `ingest_commit` 流程中自动使用匹配的 template_id，无需用户手动选择
  - 📋 **技术要点**：需要实现 fingerprint → template_id 的自动匹配逻辑（可能通过 template_registry 表查询）
- [X] `backend/services/skills/chapter_generation_skill.py` - 章节生成 ✅ **已完成 (MVP)**
  - ✅ 支持 "回弹法检测混凝土抗压强度" 场景
  - ✅ 支持表格生成、摘要计算
  - ✅ 自动提取证据链
  - ✅ **数据映射问题已修复**：优先从映射字段（`test_result`, `component_type`）读取，支持 `raw_result` 作为fallback
  - ✅ 支持两种数据集：`concrete_rebound_tests`（检测结果汇总）和 `concrete_rebound_record_sheet`（原始记录汇总）
  - ✅ **报告生成逻辑优化**：支持按检测大类（scope_）筛选，当 sourceNodeId 为 scope_ 开头时，查询整个项目数据而非特定节点
  - ✅ **数据流程确认**：报告生成从 Supabase 数据库提取数据，而非直接调用信息采集的临时数据

**架构决策说明：**

- 根据 `ARCHITECTURE_DECISION_ENTITY_EXTRACTION.md`，Phase 0采用Vision-first策略
- Parse Skill直接输出entities，跳过Entity Extraction Skill
- 简化架构：Parse → Mapping → Validation → Professional DB → Chapter Generation

### 2. 数据库模型层（基本完成）✅

- [X] `backend/models/db.py` - 基础数据库操作函数 ✅ **已完成**
  - ✅ `insert_professional_data()` - 插入专业数据函数已实现
  - ✅ `fetch_professional_data()` - 读取专业数据函数已实现（支持JSON自动解析）
  - ✅ `insert_run_log()` - 日志记录函数已实现
  - [ ] 缺少完整的 ProfessionalDB 类封装（Phase 0 可选，函数式够用）

### 3. 存储层（1/1）✅

- [X] `backend/storage/object_storage.py` - 本地文件存储（LocalObjectStorage实现） ✅ **已完成**
  - 注意：文件名是 `object_storage.py`，但实现的是本地存储（符合Phase 0策略）

### 4. API Routes实现（3.5/5）✅ 核心功能完成，模板识别流程待打通

- [X] `POST /api/collection/upload` - 文件上传接口（支持自动Parse + Mapping + Validation） ✅ **已完成**
  - ✅ 集成Mapping Skill（返回mapping_payload）
  - ✅ 集成Validation Skill（返回validation_result）
  - ✅ persist_result默认False（用户确认后才保存）
  - ✅ **集成模板识别**：TemplateProfileSkill 识别表头并计算指纹
  - ✅ **模板解析**：TemplateResolver 根据指纹查询模板
  - ⚠️ **待打通**：识别到的模板如何自动应用到后续 commit 流程
- [X] `POST /api/collection/confirm` - 数据确认接口（用户确认后保存到数据库） ✅ **已完成**
  - ✅ 验证通过后保存到数据库
  - ✅ 记录run_log
- [X] `POST /api/ingest/commit` - 数据提取提交接口 ✅ **已完成（部分）**
  - ✅ 支持根据 template_id 提取数据
  - ⚠️ **待打通**：如何自动使用 upload 阶段识别到的模板，而非手动选择
- [X] `POST /api/report/generate` - 报告生成接口 ✅ **已完成**
  - ✅ 集成 ChapterGenerationSkill
  - ✅ 返回章节内容和证据链
  - ✅ 支持 `sourceNodeId` 字段传递（关联数据节点或检测大类）
  - ✅ **前端自动映射**：根据 `templateStyle` 自动设置 `dataset_key`
  - ✅ **Scope 支持**：支持按检测大类（scope_concrete_strength 等）筛选数据
- [ ] `GET /api/run/{run_id}` - 运行状态查询接口（Stub已存在，待完善查询逻辑）

### 5. Run Log管理（部分完成）🟡

- [X] Run Log记录逻辑（在关键阶段已实现） ✅ **部分完成**
  - ✅ 文件上传接口中记录（stage: "ingest", "parse", "mapping", "validation"）
  - ✅ 确认接口中记录（stage: "confirm", "persist"）
  - ✅ 报告生成中记录（stage: "chapter_generation"）
  - ⚠️ 缺少完整的Run Log查询和管理接口

---

## 📊 进度统计

**总体进度：约 90%**

- ✅ **前置条件**：100% 完成
- ✅ **核心功能**：约 90% 完成
  - Skills：5.5/6 完成（92%）- 核心技能已实现，模板识别功能已完成但流程待打通
  - 存储层：1/1 完成（100%）
  - 数据库模型层：0.9/1 完成（90%）- 基础函数齐备，能跑通业务
  - API Routes：3.5/5 完成（70%）- 核心链路接口全通，模板识别流程待打通
  - Run Log：0.5/1 完成（50%）- 写入已通，查询待做
  - 前端章节配置：1/1 完成（100%）- Scope筛选、联动过滤、UI优化已完成

**关键里程碑：**

- [X] 项目框架搭建
- [X] 数据库设计
- [X] LLM Gateway实现
- [X] 存储层实现（LocalObjectStorage）
- [X] Ingest Skill实现
- [X] Parse Skill实现（Vision-first）
- [X] 架构决策：跳过Entity Extraction Skill
- [X] **文件上传接口实现**（集成Ingest + Parse + Mapping + Validation）
- [X] **数据确认接口实现**（`POST /api/collection/confirm`）
- [X] **LLM Gateway扩展** (Qwen, Moonshot)
- [X] **数据库操作基础函数** (`insert`, `fetch`)
- [X] **Mapping Skill实现**
- [X] **Validation Skill实现**
- [X] **Chapter Generation Skill实现** (MVP)
- [X] **报告生成接口实现** (`POST /api/report/generate`)
- [X] **数据映射问题修复**：ChapterGenerationSkill 优先从映射字段读取数据
- [X] **前端功能增强**：CollectionNode显示简化、ProjectSidebar菜单功能、ReportNodeEditor修复
- [X] **前端UI优化**："专家文档"更名为"适用的原始记录"
- [X] **章节配置功能完善**：
  - ✅ 实现"数据范围筛选 (Scope)"面板，支持按检测大类筛选
  - ✅ 实现"检测大类"与"数据用途"的联动过滤
  - ✅ 集成抓取规则字段预览到 Scope 面板
  - ✅ UI布局优化，界面更加简约统一
- [X] **报告生成逻辑修复**：
  - ✅ 修复 scope_ 开头的 sourceNodeId 查询逻辑（查询整个项目）
  - ✅ 前端根据 templateStyle 自动映射 dataset_key
  - ✅ 确认数据流程：信息采集 → 数据库存储 → 报告生成时从数据库查询

---

## 🐛 已知问题

### 1. 模板识别流程未打通 ⚠️ **高优先级**

**问题描述：**
- `TemplateProfileSkill` 已实现并集成到 `upload_file` 接口，能够识别表头并计算指纹
- 识别到的模板指纹（fingerprint）尚未自动匹配到 `template_id`
- `ingest_commit` 流程中仍需要用户手动选择模板，无法自动使用识别结果

**修复建议：**
- 实现 fingerprint → template_id 的自动匹配逻辑（通过 `template_registry` 表查询）
- 在 `ingest_commit` 接口中，优先使用识别到的模板，无需用户手动选择
- 或者：前端在 upload 阶段获取识别结果，在 commit 时自动传递 template_id
- 确保模板识别 → 模板解析 → 数据提取的完整链路打通

### 2. Run Log 查询接口待完善

**问题描述：**
- `GET /api/run/{run_id}` 接口目前只返回 stub 数据
- 缺少实际的数据库查询逻辑

**修复建议：**
- 实现 `fetch_run_log()` 函数
- 支持按 `run_id` 查询日志记录
- 返回完整的执行步骤和状态信息

---

## 🎯 下一步行动建议

### 优先级1：模板识别流程打通

1. **模板识别到数据提取的自动流转**
   - 在 `upload_file` 接口中，当识别到模板后，将 `resolved_template` 信息保存到临时存储或返回给前端
   - 在 `ingest_commit` 接口中，自动使用识别到的模板，无需用户手动选择
   - 或者：前端在 upload 阶段获取识别结果，在 commit 时自动传递 template_id
   - 确保模板识别 → 模板解析 → 数据提取的完整链路打通

2. **模板匹配优化**
   - 优化 TemplateResolver 的匹配逻辑（指纹匹配、模糊匹配等）
   - 处理未识别到模板的情况（fallback 机制）

### 优先级2：文本生成功能实现

1. **混凝土强度描述生成**
   - 实现"混凝土强度描述"数据提取逻辑（A-E类字段）
   - 从数据库提取描述级事实字段（concrete_type, test_method等）
   - 计算派生/统计字段（age_days, strength_min_mpa等）
   - 集成规则系统提供规范与规则字段（correction_standard_code等）
   - 实现文本生成模板，将字段组装成描述性文本

2. **规则系统集成**
   - 实现规范引用解析（根据reference_spec获取correction_standard_code等）
   - 实现强度修正系数计算逻辑（根据龄期、碳化深度等）

### 优先级2：端到端联调与验证

1. **完整流程验证**
   - 上传 PDF -> 解析 -> 确认数据 -> 生成报告章节（表格 + 描述）
   - 验证不同检测大类的数据筛选是否正确

2. **前端对接优化**
   - 优化报告预览界面，支持表格和描述文本的展示
   - 添加字段映射可视化（显示哪些字段被使用）

### 优先级3：增强与优化

1. **Run Log 查询**
   - 完善 `GET /api/run/{run_id}` 接口
   - 实现 `fetch_run_log()` 数据库查询函数
   - 前端展示任务运行状态

2. **更多章节类型支持**
   - 扩展支持砂浆强度、砖强度、钢材里氏硬度等检测类型
   - 为每种类型定义对应的抓取规则字段

3. **错误处理优化**
   - 统一全局异常处理
   - 完善错误响应格式

4. **性能优化**
   - 批量数据查询优化
   - LLM 调用并发处理

---

## 📝 最近更新记录

### 2025-01-03（下午）

- ✅ **章节配置功能完善**：
  - 实现"数据范围筛选 (Scope)"面板，整合检测大类选择和数据用途选择
  - 实现检测大类与数据用途的联动过滤（选择混凝土检测只显示混凝土相关类型）
  - 集成抓取规则字段预览到 Scope 面板内部，UI更加简约
  - 移除冗余选项（全部项目、具体批次、预留筛选条件）
  - 优化提示文本布局，整合到标题栏
- ✅ **报告生成逻辑修复**：
  - 修复后端查询逻辑：当 sourceNodeId 为 scope_ 开头时，查询整个项目数据而非作为 node_id
  - 前端根据 templateStyle 自动映射 dataset_key，确保后端正确识别数据类型
  - 确认数据流程：信息采集 → 存入 Supabase → 报告生成时从数据库查询（前后端数据独立）
- ✅ **字段定义扩展**：
  - 定义"混凝土强度描述"抓取规则字段（A-E类：描述级事实、表格级事实、派生统计、规范规则、报告引用）
- ⚠️ **模板识别功能状态确认**：
  - TemplateProfileSkill 已实现并集成到 upload_file 接口
  - 识别功能已完成，但流程未打通：识别到的模板指纹尚未自动应用到 ingest_commit 流程
  - 需要实现 fingerprint → template_id 的自动匹配和自动应用逻辑
- 📋 **文档更新**：
  - 更新 BACKEND_PROGRESS.md，准确反映模板识别功能状态（已完成但流程待打通）
  - 将模板识别流程打通列为优先级1任务

### 2025-01-03（上午）

- ✅ **数据映射问题修复**：
  - ChapterGenerationSkill 优先从映射字段（`test_result`, `component_type`）读取数据
  - 支持 `raw_result` 作为 fallback，兼容中文键名
  - 报告生成表格为空问题已解决
- ✅ **前端UI优化**：
  - "专家文档"更名为"适用的原始记录"
  - 优化用户界面术语统一性
- 📋 **文档更新**：
  - 更新 BACKEND_PROGRESS.md，反映数据映射问题已修复
  - 更新进度统计（约90%完成）

### 2025-01-02

- ✅ **前端功能增强**：
  - CollectionNode 显示简化（只显示必要信息）
  - ProjectSidebar 添加项目菜单（置顶、归档、删除功能）
  - ReportNodeEditor 修复白屏问题（添加缺失的 sourceNodeId 状态）
  - 专家文档预览修复中文显示问题（替换问号占位符）
  - 报告生成接口修复（添加 sourceNodeId 字段传递）
- ⚠️ **问题发现**：
  - 报告生成表格为空问题（数据映射不匹配）
  - 创建分析文档：`ANALYSIS_DATA_MAPPING_ISSUE.md`, `ANALYSIS_CARBONATION_FIELD.md`
- 📋 **文档更新**：
  - 更新 BACKEND_PROGRESS.md 进度状态
