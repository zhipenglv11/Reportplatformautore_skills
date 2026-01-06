# 前端上传对接后端 Ingest/Parse 详细指南

> 创建时间：2024-12-30

---

## 📍 一、前端上传入口位置

### 1.1 主要上传逻辑

**文件路径：** `src/app/components/data-collection-editor.tsx`

**函数名：** `handleFileUpload`

**代码位置：** 第 121-180 行

**函数签名：**
```typescript
const handleFileUpload = useCallback(async (nodeId: string, nodeLabel: string) => {
  // ... 上传逻辑
}, [projectId]);
```

### 1.2 触发按钮位置

**文件路径：** `src/app/components/collection-detail-modal.tsx`

**按钮位置：** 第 332-338 行

**按钮代码：**
```tsx
<button
  onClick={handleUploadClick}
  className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-xs font-medium inline-flex items-center gap-2"
>
  <Upload className="w-3.5 h-3.5" />
  选择文件
</button>
```

**触发函数：** `handleUploadClick()` (第 86-88 行)
```tsx
const handleUploadClick = () => {
  onUpload(node.id, node.data.label);  // 调用父组件的handleFileUpload
};
```

### 1.3 组件调用链

```
CollectionDetailModal (collection-detail-modal.tsx)
  ↓ onUpload prop
DataCollectionEditor (data-collection-editor.tsx)
  ↓ handleFileUpload function
  ↓ fetch('/api/collection/upload')
后端 API
```

---

## 📂 二、具体文件/组件路径

### 前端文件

| 文件路径 | 说明 | 关键代码行 |
|---------|------|-----------|
| `src/app/components/data-collection-editor.tsx` | 主要上传逻辑 | 121-180行 |
| `src/app/components/collection-detail-modal.tsx` | 上传按钮UI | 86-88行, 332-338行 |
| `src/app/App.tsx` | 传递projectId | 241-247行 |

### 后端文件

| 文件路径 | 说明 | 关键代码行 |
|---------|------|-----------|
| `backend/api/collection_routes.py` | 上传接口路由 | 12-56行 |
| `backend/services/skills/ingest_skill.py` | Ingest Skill | 16-23行 |
| `backend/services/skills/parse_skill.py` | Parse Skill | 22-92行 |
| `backend/storage/object_storage.py` | 文件存储 | 19-42行 |

---

## ✅ 三、目前是否已有上传逻辑

### 当前状态：**已实现基础上传功能**

**已实现的功能：**
- ✅ 文件选择（多文件支持）
- ✅ 文件上传到后端（使用fetch）
- ✅ 调用IngestSkill保存文件
- ✅ 返回文件元数据（object_key, source_hash等）
- ✅ 错误处理

**未实现的功能：**
- ❌ **上传后自动调用Parse**
- ❌ 上传进度显示
- ❌ 文件大小限制检查（前端）

**当前上传逻辑代码（data-collection-editor.tsx 121-180行）：**

```typescript
const handleFileUpload = useCallback(async (nodeId: string, nodeLabel: string) => {
  const input = document.createElement('input');
  input.type = 'file';
  input.multiple = true;
  input.accept = 'image/*,.pdf,.doc,.docx,.xls,.xlsx';
  
  input.onchange = async (e: any) => {
    const files = Array.from(e.target.files || []) as File[];
    
    // 上传文件到后端
    const uploadPromises = files.map(async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('project_id', projectId);
      formData.append('node_id', nodeId);
      
      try {
        const response = await fetch('/api/collection/upload', {
          method: 'POST',
          body: formData,
        });
        
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ message: response.statusText }));
          throw new Error(errorData.message || `上传失败: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        return {
          id: `${nodeId}-file-${Date.now()}-${Math.random()}`,
          name: result.filename,
          type: file.type,
          size: file.size,
          url: result.object_key,
          uploadDate: new Date().toLocaleString('zh-CN'),
          object_key: result.object_key,
          source_hash: result.source_hash,
          file_type: result.file_type,
        };
      } catch (error: any) {
        console.error('文件上传失败:', error);
        alert(`文件 ${file.name} 上传失败: ${error.message}`);
        return null;
      }
    });
    
    const uploadResults = await Promise.all(uploadPromises);
    const successfulUploads = uploadResults.filter(result => result !== null);
    
    if (successfulUploads.length > 0) {
      setUploadedFiles(prev => ({
        ...prev,
        [nodeId]: [...(prev[nodeId] || []), ...successfulUploads]
      }));
    }
  };
  
  input.click();
}, [projectId]);
```

---

## 🔧 四、前端调用方式预期

### 4.1 当前使用方式：**直接使用 fetch**

**当前实现：** 直接在 `handleFileUpload` 函数中使用 `fetch` API

**代码位置：** `src/app/components/data-collection-editor.tsx` 第 138-141 行

```typescript
const response = await fetch('/api/collection/upload', {
  method: 'POST',
  body: formData,
});
```

### 4.2 是否有API封装：**目前没有**

**检查结果：**
- ❌ 没有 `src/lib/api/` 目录
- ❌ 没有 `src/api.ts` 或 `src/api.js` 文件
- ✅ **当前直接使用 fetch**

### 4.3 建议

**方案A：继续使用fetch（当前方案）**
- ✅ 简单直接
- ✅ 无需额外封装
- ✅ 适合Phase 0快速开发

**方案B：创建API封装（未来扩展）**
- 可创建 `src/lib/api/collection.ts` 封装上传函数
- 便于统一错误处理、请求拦截等
- 当前**不建议**，保持简单

**推荐：** 继续使用fetch，保持当前实现方式

---

## 📤 五、上传时的字段名

### 5.1 FormData字段

| 字段名 | 类型 | 必填 | 说明 | 当前实现 |
|--------|------|------|------|---------|
| `file` | File | ✅ 是 | 上传的文件对象 | ✅ 已使用 |
| `project_id` | string | ✅ 是 | 项目ID | ✅ 已使用 |
| `node_id` | string | ✅ 是 | 节点ID（如："concrete-strength"） | ✅ 已使用 |

### 5.2 当前实现代码

```typescript
const formData = new FormData();
formData.append('file', file);                    // 字段名：file
formData.append('project_id', projectId);         // 字段名：project_id
formData.append('node_id', nodeId);               // 字段名：node_id
```

### 5.3 后端接收（collection_routes.py）

```python
@router.post("/collection/upload")
async def upload_file(
    file: UploadFile = File(...),           # 对应：file
    project_id: str = Form(...),            # 对应：project_id
    node_id: str = Form(...)                # 对应：node_id
):
```

**✅ 字段名已匹配，无需修改**

---

## 🔌 六、后端接口约定

### 6.1 当前接口路径

**接口路径：** `POST /api/collection/upload`

**完整URL（开发环境）：** `http://localhost:8000/api/collection/upload`

**实现位置：** `backend/api/collection_routes.py` 第 12 行

### 6.2 接口响应格式

**成功响应（HTTP 200）：**

```json
{
  "project_id": "1",
  "node_id": "concrete-strength",
  "object_key": "/data/autore/uploads/1/test.pdf",
  "source_hash": "a1b2c3d4e5f6...",
  "filename": "test.pdf",
  "file_type": "pdf",
  "file_size": 1024000,
  "upload_date": "2024-12-30T10:00:00.000Z"
}
```

**错误响应（HTTP 400/500）：**

```json
{
  "detail": "文件上传失败: 错误信息"
}
```

### 6.3 当前接口实现（仅Ingest）

**当前实现：** 只调用 `IngestSkill`，**不调用Parse**

```python
@router.post("/collection/upload")
async def upload_file(...):
    ingest_skill = IngestSkill()
    result = await ingest_skill.execute(file, project_id)
    # ❌ 当前没有调用Parse
    return {...}
```

---

## 🤔 七、是否"上传后立即 Parse"

### 7.1 当前实现：**分离式（先上传，后Parse）**

**当前流程：**
```
上传文件 → Ingest Skill → 返回文件信息 → 前端存储
```

**Parse调用：** ❌ 当前**未实现**

### 7.2 两种方案对比

#### 方案A：上传后立即Parse（推荐）

**流程：**
```
上传文件 → Ingest Skill → Parse Skill → 返回文件信息+解析结果
```

**优点：**
- ✅ 用户体验好（上传后立即看到解析结果）
- ✅ 减少前端请求次数
- ✅ 后端可以统一处理错误

**缺点：**
- ⚠️ 上传响应时间较长（需要等待Parse完成）
- ⚠️ 如果Parse失败，需要回滚或标记状态

**实现方式：**
```python
@router.post("/collection/upload")
async def upload_file(...):
    # 1. Ingest
    ingest_skill = IngestSkill()
    ingest_result = await ingest_skill.execute(file, project_id)
    
    # 2. Parse（立即执行）
    parse_skill = ParseSkill(llm_gateway=llm_gateway)
    parse_result = await parse_skill.execute(
        ingest_result,
        use_llm=True,  # 是否调用LLM
        prompt="提取混凝土强度检测数据..."
    )
    
    return {
        "project_id": project_id,
        "node_id": node_id,
        "object_key": ingest_result["object_key"],
        "source_hash": ingest_result["source_hash"],
        "filename": result["filename"],
        "file_type": file_type,
        "parse_result": parse_result  # 包含解析结果
    }
```

#### 方案B：分离式（当前方案 + 单独Parse接口）

**流程：**
```
上传文件 → Ingest Skill → 返回文件信息
         ↓
用户点击"分析" → 调用Parse接口 → 返回解析结果
```

**优点：**
- ✅ 上传响应快
- ✅ 用户可以选择是否解析
- ✅ 可以多次解析（使用不同参数）

**缺点：**
- ❌ 需要两次请求
- ❌ 前端需要管理解析状态

**实现方式：**
```python
# 接口1：上传（已实现）
@router.post("/collection/upload")
async def upload_file(...):
    # 只做Ingest，不Parse
    ...

# 接口2：Parse（待实现）
@router.post("/collection/parse")
async def parse_file(
    object_key: str = Form(...),
    use_llm: bool = Form(False),
    prompt: str = Form(None)
):
    # 调用Parse Skill
    ...
```

### 7.3 推荐方案

**推荐：方案A（上传后立即Parse）**

**理由：**
1. 用户体验更好（上传后立即看到结果）
2. 符合Phase 0"最小可卖Demo"的目标
3. 前端逻辑更简单

**实现建议：**
- 添加可选参数 `auto_parse: bool = True`
- 如果 `auto_parse=True`，上传后立即Parse
- 如果 `auto_parse=False`，只上传，不Parse（为未来扩展预留）

---

## 📎 八、文件类型与约束

### 8.1 允许的文件类型

**当前前端限制（data-collection-editor.tsx 第 125 行）：**

```typescript
input.accept = 'image/*,.pdf,.doc,.docx,.xls,.xlsx';
```

**实际支持的文件类型（Phase 0）：**

| 文件类型 | 扩展名 | 前端accept | 后端支持 | Parse支持 |
|---------|--------|-----------|---------|-----------|
| PDF | `.pdf` | ✅ | ✅ | ✅ (Vision-first) |
| 图片 | `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`, `.webp` | ✅ | ✅ | ✅ (Vision-first) |
| Word | `.doc`, `.docx` | ✅ | ⚠️ 部分 | ❌ Phase 0不支持 |
| Excel | `.xls`, `.xlsx` | ✅ | ⚠️ 部分 | ❌ Phase 0不支持 |

**注意：**
- 前端accept包含了Word和Excel，但**后端Parse Skill目前不支持**
- Phase 0主要支持**PDF和图片**
- Word和Excel可以后续支持

### 8.2 文件大小限制

**当前实现：**
- ❌ **前端：无大小限制检查**
- ❌ **后端：无大小限制检查**

**建议限制：**

| 文件类型 | 建议大小限制 | 理由 |
|---------|-------------|------|
| PDF | 50MB | 大PDF转换图片耗时 |
| 图片 | 20MB | 图片处理内存占用 |
| 总体 | 50MB | 上传和Parse性能 |

**实现建议：**

**前端检查（data-collection-editor.tsx）：**
```typescript
const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

input.onchange = async (e: any) => {
  const files = Array.from(e.target.files || []) as File[];
  
  // 检查文件大小
  const oversizedFiles = files.filter(file => file.size > MAX_FILE_SIZE);
  if (oversizedFiles.length > 0) {
    alert(`以下文件超过50MB限制：${oversizedFiles.map(f => f.name).join(', ')}`);
    return;
  }
  
  // ... 上传逻辑
};
```

**后端检查（collection_routes.py）：**
```python
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

@router.post("/collection/upload")
async def upload_file(file: UploadFile = File(...), ...):
    # 检查文件大小
    file_size = 0
    content = await file.read()
    file_size = len(content)
    await file.seek(0)  # 重置文件指针
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"文件大小超过限制（最大50MB）"
        )
    
    # ... 继续处理
```

### 8.3 文件类型验证

**后端验证（collection_routes.py）：**

```python
ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'image/jpeg', 'image/jpg', 'image/png',
    'image/bmp', 'image/tiff', 'image/webp'
}

@router.post("/collection/upload")
async def upload_file(file: UploadFile = File(...), ...):
    # 验证文件类型
    if file.filename:
        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=415,
                detail=f"不支持的文件类型：{ext}，仅支持PDF和图片文件"
            )
    
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"不支持的文件类型：{file.content_type}"
        )
    
    # ... 继续处理
```

---

## 📋 九、对接Parse的完整实现建议

### 9.1 修改后端接口（上传后立即Parse）

**文件：** `backend/api/collection_routes.py`

**修改建议：**

```python
from services.skills.parse_skill import ParseSkill
from services.llm_gateway.gateway import LLMGateway

router = APIRouter()

@router.post("/collection/upload")
async def upload_file(
    file: UploadFile = File(...),
    project_id: str = Form(...),
    node_id: str = Form(...),
    auto_parse: bool = Form(True),  # 新增：是否自动Parse
    use_llm: bool = Form(True),      # 新增：是否使用LLM
):
    """
    文件上传接口（支持自动Parse）
    """
    try:
        # 1. Ingest
        ingest_skill = IngestSkill()
        ingest_result = await ingest_skill.execute(file, project_id)
        
        result = {
            "project_id": project_id,
            "node_id": node_id,
            "object_key": ingest_result["object_key"],
            "source_hash": ingest_result["source_hash"],
            "filename": ingest_result["filename"],
            "file_type": file_type,
            "file_size": file.size if hasattr(file, 'size') else 0,
            "upload_date": datetime.now().isoformat()
        }
        
        # 2. Parse（如果auto_parse=True）
        if auto_parse:
            llm_gateway = LLMGateway()
            parse_skill = ParseSkill(llm_gateway=llm_gateway)
            
            # 构建Parse输入（Ingest的输出）
            parse_input = {
                "object_key": ingest_result["object_key"],
                "source_hash": ingest_result["source_hash"],
                "filename": ingest_result["filename"]
            }
            
            parse_result = await parse_skill.execute(
                ingest_result=parse_input,
                use_llm=use_llm,
                prompt=f"从文档中提取{node_id}相关的结构化数据"
            )
            
            result["parse_result"] = {
                "parse_id": parse_result["parse_id"],
                "structured_data": parse_result.get("structured_data", {}),
                "evidence_refs": parse_result.get("evidence_refs", []),
                "page_images_count": len(parse_result.get("page_images", [])),
            }
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")
```

### 9.2 前端处理Parse结果（可选）

**如果后端返回parse_result，前端可以：**

```typescript
const result = await response.json();

if (result.parse_result) {
  // 解析成功，可以显示解析结果
  console.log('解析结果:', result.parse_result.structured_data);
  // 可以更新UI显示解析结果
}
```

---

## 📝 十、总结

### 当前状态

| 项目 | 状态 | 说明 |
|------|------|------|
| 前端上传逻辑 | ✅ 已实现 | data-collection-editor.tsx |
| Ingest接口 | ✅ 已实现 | POST /api/collection/upload |
| Parse接口 | ❌ 未实现 | 需要添加 |
| 上传后Parse | ❌ 未实现 | 需要修改接口 |
| 文件大小限制 | ❌ 未实现 | 建议添加 |
| 文件类型验证 | ⚠️ 部分实现 | 建议完善 |

### 下一步行动

1. **修改后端接口，添加自动Parse功能**
2. **添加文件大小限制检查**（前端+后端）
3. **完善文件类型验证**（后端）
4. **测试上传+Parse流程**

---

## 🔗 相关文档

- API接口文档：`backend/API_DOCUMENTATION.md`
- 后端进度：`backend/BACKEND_PROGRESS.md`
- Phase 0任务：`PHASE0_PRIORITY_TASKS.md`

