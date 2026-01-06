# 前端交互与后端接口映射指南

> 创建时间：2024-12-30

---

## ❓ 核心问题

**是不是前端每个点击/交互都需要对应的后端接口？**

**答案：不是！** 只有**需要后端处理**的交互才需要接口。

---

## 📊 前端交互点分类

### 分类标准

| 分类 | 是否需要后端接口 | 说明 | 示例 |
|------|----------------|------|------|
| **纯UI交互** | ❌ 不需要 | 只改变前端状态，不涉及数据持久化或后端处理 | 打开/关闭弹窗、切换标签页 |
| **本地状态管理** | ❌ 不需要 | 前端组件内部状态变化 | 节点选择、展开/折叠 |
| **数据持久化** | ✅ 需要 | 需要保存到数据库或文件系统 | 保存节点配置、保存项目数据 |
| **后端服务调用** | ✅ 需要 | 需要调用后端Skill或服务 | 文件上传、数据分析、报告生成 |
| **数据查询** | ✅ 需要 | 需要从后端获取数据 | 查询项目列表、查询运行状态 |

---

## 🔍 前端交互点清单

### 一、数据采集模块（Collection）

#### 1. 节点操作

| 交互点 | 位置 | 当前状态 | 是否需要接口 | 接口路径（如需要） |
|--------|------|---------|-------------|------------------|
| **添加节点** | `node-sidebar.tsx` | 前端本地 | ❌ **不需要** | - |
| **删除节点** | `data-collection-editor.tsx` | 前端本地 | ❌ **不需要** | - |
| **编辑节点** | `collection-detail-modal.tsx` | 前端本地 | ❌ **不需要** | - |
| **选择节点** | `data-collection-editor.tsx` | 前端本地 | ❌ **不需要** | - |
| **双击打开详情** | `data-collection-editor.tsx` | 前端本地 | ❌ **不需要** | - |

**说明：** 节点操作是前端ReactFlow的本地状态管理，数据保存在localStorage，**不需要后端接口**。

---

#### 2. 文件操作

| 交互点 | 位置 | 当前状态 | 是否需要接口 | 接口路径 |
|--------|------|---------|-------------|---------|
| **选择文件** | `collection-detail-modal.tsx` 第332行 | ✅ **已实现** | ✅ **需要** | `POST /api/collection/upload` |
| **删除文件** | `data-collection-editor.tsx` 第227行 | 前端本地 | ⚠️ **可选** | `DELETE /api/collection/file/{file_id}` |
| **下载文件** | - | 未实现 | ⚠️ **可选** | `GET /api/collection/file/{file_id}` |

**说明：**
- **文件上传**：✅ 必须（需要保存到后端存储）
- **文件删除**：⚠️ 可选（Phase 0可以先只做前端删除，Phase 1再做后端删除）
- **文件下载**：⚠️ 可选（Phase 0可能不需要）

---

#### 3. 数据分析

| 交互点 | 位置 | 当前状态 | 是否需要接口 | 接口路径 |
|--------|------|---------|-------------|---------|
| **开始数据分析** | `collection-detail-modal.tsx` 第360行 | ❌ **Mock数据** | ✅ **需要** | `POST /api/collection/analyze` |

**当前实现（Mock）：**
```typescript
// data-collection-editor.tsx 第183-225行
const handleDataAnalysis = useCallback((nodeId: string, nodeData: any) => {
  // ❌ 当前只是生成Mock数据，没有调用后端
  const mockAnalysisResult = {
    // ... 模拟数据
  };
  setAnalysisResults(prev => ({
    ...prev,
    [nodeId]: mockAnalysisResult
  }));
}, [uploadedFiles]);
```

**需要实现：**
```typescript
const handleDataAnalysis = useCallback(async (nodeId: string, nodeData: any) => {
  const files = uploadedFiles[nodeId] || [];
  if (files.length === 0) return;
  
  // ✅ 调用后端接口
  const response = await fetch('/api/collection/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      project_id: projectId,
      node_id: nodeId,
      files: files.map(f => ({
        object_key: f.object_key,
        source_hash: f.source_hash
      }))
    })
  });
  
  const result = await response.json();
  setAnalysisResults(prev => ({
    ...prev,
    [nodeId]: result
  }));
}, [uploadedFiles, projectId]);
```

---

#### 4. 数据保存

| 交互点 | 位置 | 当前状态 | 是否需要接口 | 接口路径 |
|--------|------|---------|-------------|---------|
| **保存节点数据** | - | 未实现 | ✅ **需要** | `POST /api/collection/save` |

**说明：** 用户填写完数据字段后，需要保存到专业数据库。

---

### 二、报告生成模块（Report）

#### 1. 报告操作

| 交互点 | 位置 | 当前状态 | 是否需要接口 | 接口路径 |
|--------|------|---------|-------------|---------|
| **生成报告** | `node-sidebar.tsx` 第852行 | ❌ **Mock** | ✅ **需要** | `POST /api/report/generate` |
| **停止生成** | `node-sidebar.tsx` 第844行 | ❌ **未实现** | ✅ **需要** | `POST /api/report/stop/{run_id}` |
| **查询运行状态** | - | ❌ **未实现** | ✅ **需要** | `GET /api/run/{run_id}` |

**当前实现（Mock）：**
```typescript
// node-sidebar.tsx 第852行
<button onClick={() => {
  setIsGenerateReportClicked(true);
  onGenerateReport();  // ❌ 当前只是调用父组件的函数，没有后端调用
}}>
```

---

### 三、其他交互

#### 1. 项目操作

| 交互点 | 位置 | 当前状态 | 是否需要接口 | 接口路径 |
|--------|------|---------|-------------|---------|
| **创建项目** | `project-sidebar.tsx` | 前端localStorage | ⚠️ **可选** | `POST /api/project/create` |
| **切换项目** | `project-sidebar.tsx` | 前端localStorage | ❌ **不需要** | - |
| **删除项目** | `project-sidebar.tsx` | 前端localStorage | ⚠️ **可选** | `DELETE /api/project/{id}` |

**说明：** Phase 0使用localStorage，**不需要后端接口**。Phase 1+需要持久化到数据库时再实现。

---

#### 2. UI交互（不需要接口）

| 交互点 | 位置 | 说明 |
|--------|------|------|
| 打开/关闭弹窗 | `collection-detail-modal.tsx` | 纯UI状态 |
| 切换标签页 | `App.tsx` | 纯UI状态 |
| 展开/折叠侧边栏 | `node-sidebar.tsx` | 纯UI状态 |
| 搜索节点 | `node-sidebar.tsx` | 前端过滤 |
| 调整面板大小 | `collection-detail-modal.tsx` | 纯UI状态 |

---

## 🎯 需要后端接口的交互清单

### Phase 0 必须实现的接口

| 序号 | 交互点 | 接口路径 | 优先级 | 状态 |
|------|--------|---------|--------|------|
| 1 | 文件上传 | `POST /api/collection/upload` | ✅ **P0** | ✅ **已实现** |
| 2 | 数据分析 | `POST /api/collection/analyze` | ✅ **P0** | ❌ **待实现** |
| 3 | 数据保存 | `POST /api/collection/save` | ✅ **P0** | ❌ **待实现** |
| 4 | 报告生成 | `POST /api/report/generate` | ✅ **P0** | ❌ **待实现** |
| 5 | 运行状态查询 | `GET /api/run/{run_id}` | ✅ **P0** | ❌ **待实现** |

### Phase 1+ 可选接口

| 序号 | 交互点 | 接口路径 | 优先级 |
|------|--------|---------|--------|
| 6 | 文件删除 | `DELETE /api/collection/file/{file_id}` | P1 |
| 7 | 文件下载 | `GET /api/collection/file/{file_id}` | P1 |
| 8 | 停止生成 | `POST /api/report/stop/{run_id}` | P1 |
| 9 | 项目创建 | `POST /api/project/create` | P2 |
| 10 | 项目列表 | `GET /api/project/list` | P2 |

---

## 📐 接口设计模式

### 模式1：按功能模块组织（推荐）

```
/api/collection/     # 数据采集模块
  ├── upload         # 文件上传
  ├── analyze        # 数据分析
  └── save           # 数据保存

/api/report/         # 报告生成模块
  ├── generate       # 生成报告
  └── stop/{run_id}  # 停止生成

/api/run/            # 运行管理
  └── {run_id}       # 查询运行状态
```

**优点：**
- ✅ 结构清晰，按前端功能模块组织
- ✅ 易于维护和扩展
- ✅ 符合RESTful设计

### 模式2：按资源组织（备选）

```
/api/files/          # 文件资源
  ├── upload
  ├── {file_id}
  └── {file_id}/download

/api/nodes/          # 节点资源
  ├── {node_id}/analyze
  └── {node_id}/save
```

**当前推荐：模式1（按功能模块组织）**

---

## 🔄 接口调用模式

### 统一的前端调用方式

**建议：** 继续使用 `fetch`，保持简单（Phase 0）

**示例模板：**

```typescript
// 通用API调用模板
async function callAPI(endpoint: string, method: string, data?: any) {
  const options: RequestInit = {
    method,
    headers: {
      'Content-Type': 'application/json',
    },
  };
  
  if (data && method !== 'GET') {
    options.body = JSON.stringify(data);
  }
  
  const response = await fetch(`/api${endpoint}`, options);
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: response.statusText }));
    throw new Error(error.message || `请求失败: ${response.statusText}`);
  }
  
  return response.json();
}

// 使用示例
const result = await callAPI('/collection/analyze', 'POST', {
  project_id: projectId,
  node_id: nodeId,
  files: [...]
});
```

---

## 📋 判断是否需要接口的决策树

```
前端交互
  ↓
是否需要持久化数据？
  ├─ 否 → ❌ 不需要接口（纯UI交互）
  └─ 是 → 是否需要后端处理？
      ├─ 否 → ❌ 不需要接口（前端localStorage即可）
      └─ 是 → ✅ 需要接口
          ├─ 文件操作 → /api/collection/upload
          ├─ 数据分析 → /api/collection/analyze
          ├─ 数据保存 → /api/collection/save
          └─ 报告生成 → /api/report/generate
```

---

## 🎯 总结

### 核心原则

1. **不是所有交互都需要接口**
   - 纯UI交互：❌ 不需要
   - 本地状态管理：❌ 不需要
   - 需要后端处理：✅ 需要

2. **接口按功能模块组织**
   - `/api/collection/*` - 数据采集
   - `/api/report/*` - 报告生成
   - `/api/run/*` - 运行管理

3. **Phase 0只需要5个核心接口**
   - ✅ 文件上传（已实现）
   - ❌ 数据分析（待实现）
   - ❌ 数据保存（待实现）
   - ❌ 报告生成（待实现）
   - ❌ 运行状态查询（待实现）

4. **前端调用方式**
   - 继续使用 `fetch` API
   - 保持简单，无需复杂封装（Phase 0）

---

## 📝 下一步行动

### 优先级1：实现数据分析接口

**接口：** `POST /api/collection/analyze`

**功能：** 调用Parse Skill + Entity Extraction（如果需要）

**前端修改：** `data-collection-editor.tsx` 第183行

### 优先级2：实现数据保存接口

**接口：** `POST /api/collection/save`

**功能：** 保存节点数据到专业数据库

### 优先级3：实现报告生成接口

**接口：** `POST /api/report/generate`

**功能：** 调用完整的Skill链生成报告

---

## 🔗 相关文档

- API接口文档：`backend/API_DOCUMENTATION.md`
- 前端后端对接指南：`backend/FRONTEND_BACKEND_INTEGRATION_GUIDE.md`
- 后端进度：`backend/BACKEND_PROGRESS.md`

