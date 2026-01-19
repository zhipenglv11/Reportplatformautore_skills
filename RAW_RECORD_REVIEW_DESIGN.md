# 原始记录与报告审核模块设计方案

## 1. 需求背景
在现有的"在线审核"流程后，增加"原始记录审核"环节。该环节用于验证原始记录的合规性、鉴定报告的正确性，以及两者的一致性。

## 2. 核心业务逻辑
系统需根据用户上传的文件类型组合，自动触发不同的审核技能（Skills）：

| 场景 | 上传内容 | 触发技能 | 备注 |
| :--- | :--- | :--- | :--- |
| **场景 A** | 仅上传 **原始记录** | `RawRecordAuditSkill` (原始记录审核) | 检查计算逻辑、数据完整性 |
| **场景 B** | 仅上传 **鉴定报告** | `ReportAuditSkill` (鉴定报告审核) | 检查报告格式、结论合规性 |
| **场景 C** | 上传 **原始记录** + **鉴定报告** | `CrossCheckSkill` (一致性比对) | 包含上述两项检查，并比对数据一致性 |

## 3. 系统架构设计

### 3.1 前端设计 (Frontend)
- **入口位置**：在 `在线审核` 之后新增 `原始记录审核` 页面/Tab。
- **UI 交互**：
    - 分离的上传区域：
        - 区域 A：**原始记录上传** (Drag & Drop) -> 标记文件类型为 `raw_record`
        - 区域 B：**鉴定报告上传** (Drag & Drop) -> 标记文件类型为 `inspection_report`
    - **开始审核** 按钮：用户上传完毕后点击，触发后端编排接口。
    - **审核结果展示**：分栏展示（原始记录问题、报告问题、一致性问题）。

### 3.2 后端设计 (Backend)

#### A. 文件模型扩展
现有的文件分类（concrete, mortar 等）主要基于内容识别。为了支持本功能，我们需要明确的**业务用途分类**。
- 方案：在上传时通过前端参数 `category` 明确指定，或者在 `SkillOrchestrator` 的识别 Prompt 中增加这两个大类。
- 建议：采用**前端指定 + 后端校验**的方式。API 接收文件时增加 `file_category` 字段。

#### B. 技能编排器升级 (ReviewOrchestrator)
现有的 `SkillOrchestrator` 主要是 `File -> Skill` 的一对一模式。
我们需要一个新的 **ReviewOrchestrator** (审核编排器)，支持 `List<File> -> Workflow` 的模式。

**处理流程：**
1. 接收文件列表（或 Collection ID）。
2. **分组**：将文件分为 `raw_files` 列表和 `report_files` 列表。
3. **路由判断**：
    ```python
    if raw_files and report_files:
        execute_skill("CrossCheckSkill", input={raw: raw_files, report: report_files})
    elif raw_files:
        execute_skill("RawRecordAuditSkill", input={raw: raw_files})
    elif report_files:
        execute_skill("ReportAuditSkill", input={report: report_files})
    ```

#### C. 新增 Skills 定义 (Stub)
需要在 `backend/services/skills/` 下新建对应技能类：
1. `raw_record_audit.py`: 实现原始记录检查逻辑。
2. `report_audit.py`: 实现报告检查逻辑。
3. `cross_check_audit.py`: 实现比对逻辑。

## 4. 实施步骤

1.  **API 接口定义**：
    - 新增 `POST /api/orchestrator/review` 接口，接收文件 ID 列表及对应的分类标签。
2.  **后端逻辑实现**：
    - 创建 `ReviewOrchestrator` 类。
    - 实现三种新的 Skill 框架（暂时留空具体算法，搭建输入输出结构）。
3.  **前端页面开发**：
    - 新建 `RawRecordReview` 页面。
    - 实现双上传组件。
    - 对接后端接口并渲染结果。

## 5. 待确认问题
- **Skill 独立性设计**：
    - 已确认：`CrossCheckSkill` 将作为一个**完全独立**的 Skill 实现，不直接调用 `RawRecordAuditSkill` 或 `ReportAuditSkill`。
    - 原因：交叉比对时，对原始记录的检查标准往往依赖于报告中的声明（例如报告称依据标准 A，则原始记录必须符合标准 A），这种上下文强相关的检查逻辑难以通过简单的 Skill 组合实现。
    - 复用策略：将通用的原子检查逻辑（如“数值提取”、“日期格式校验”）抽取为公共工具函数（Shared Utilities/Tools），供三个 Skill 共同调用，避免代码冗余。
