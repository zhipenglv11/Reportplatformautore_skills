# 当前前端数据提取链路流程图

## 主流程图

```mermaid
flowchart TD
    A["App<br/>信息采集 Tab"] --> B["DataCollectionEditor<br/>加载节点、上传状态、分析结果"]
    B --> C["GET /api/collection/node-templates"]
    C --> D["templateCategories<br/>后端模板优先，失败则退回 fallback"]
    D --> E["CollectionDetailModal<br/>embedded 采集界面"]

    E --> F["点击 上传文档"]
    F --> G["handleFileUpload<br/>创建 input[type=file]"]
    G --> H["前端创建 local FileItem<br/>status = pending"]
    H --> I["写入 uploadedFiles[nodeId]"]
    I --> J["handleDataAnalysis(nodeId, nodeData, options)"]

    J --> K{"是否手动指定 skill?"}
    K -- "否" --> L["POST /api/skill/orchestrate<br/>files + project_id + node_id<br/>persist_result=false<br/>use_llm_classification=true"]
    K -- "是" --> M["POST /api/skill/{skill_name}/run<br/>file + project_id + node_id<br/>persist_result=false"]

    L --> N["读取 result / classification / data / error"]
    M --> N

    N --> O["映射 nextFiles"]
    O --> P{"result.success ?"}
    P -- "是" --> Q["status = uploaded<br/>写回 skill_result / skill_name / file_type<br/>source_hash / parse_result / confirmed=false"]
    P -- "否" --> R["status = failed<br/>写回 error / file_type / skill_result<br/>confirmed=false"]

    Q --> S["生成 analysisResults[nodeId].jsonData"]
    R --> S

    S --> T["CollectionDetailModal 读取结构化数据"]
    T --> U["真实结果优先级<br/>analysisResults.jsonData[fileId].data<br/>-> file.parse_result<br/>-> file.skill_result.data<br/>-> []"]
    U --> V{"是否存在真实结构化结果?"}

    V -- "是" --> W["右侧展示真实结构化结果"]
    V -- "否" --> X["buildMockOutputPreviewDataByPage()<br/>右侧显示 Mock 预览数据"]

    W --> Y{"点击 确认无误 ?"}
    X --> Z{"点击 确认无误 ?"}

    Y -- "是" --> AA["POST /api/skill/confirm<br/>project_id + node_id + run_id<br/>source_hash + skill_name + records"]
    AA --> AB["确认成功后<br/>selectedFile.confirmed = true"]

    Z -- "是" --> AC["仅前端本地 setSelectedFile(...confirmed=true)<br/>不调用 /api/skill/confirm"]

    Q --> AD["顶部状态标签读取 currentFile.status / currentFile.file_type"]
    R --> AD
    AB --> AD
    AC --> AD
```

## 图例

- `uploadedFiles`
  - 以 `nodeId` 为键保存当前节点下的文件列表。
  - 每个文件项包含 `status`、`error`、`skill_result`、`parse_result`、`file_type`、`confirmed` 等字段。

- `analysisResults`
  - 以 `nodeId` 为键保存整理后的结构化结果。
  - 右侧“输出数据预览”优先读取这里，而不是直接使用接口原始返回。

- `status`
  - 上传后先是 `pending`。
  - 接口返回后在前端被改成 `uploaded` 或 `failed`。
  - 顶部状态标签主要看这个字段，不看 `confirmed`。

- `file_type`
  - 自动编排时来自 `classification.file_type`。
  - 会显示在右侧输出头部，比如 `other`、识别后的业务类型等。

- `confirmed`
  - 表示用户是否做了“确认无误”动作。
  - 它和 `status` 独立。
  - 在 mock 预览场景下，点击确认只会改前端本地 `confirmed=true`，不会触发后端保存。

- 结构化数据优先级
  - `analysisResults.jsonData[fileId].data`
  - `file.parse_result`
  - `file.skill_result.data`
  - `[]`

## 场景覆盖检查

1. 页面初始化加载模板
2. 上传后自动编排
3. 手动指定 skill 执行
4. Mock 预览下点击确认

## 对应代码入口

- `src/app/App.tsx`
- `src/app/components/data-collection-editor.tsx`
- `src/app/components/collection-detail-modal.tsx`
