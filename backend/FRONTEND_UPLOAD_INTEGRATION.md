# 前端文件上传功能位置和对接说明

> 创建时间：2024-12-30

---

## 📍 前端文件上传代码位置

### 1. 上传按钮位置

**文件：** `src/app/components/collection-detail-modal.tsx`

**位置：** 第332-338行

```tsx
<button
  onClick={handleUploadClick}
  className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-xs font-medium inline-flex items-center gap-2"
>
  <Upload className="w-3.5 h-3.5" />
  选择文件
</button>
```

**触发函数：** `handleUploadClick()` (第86-88行)
```tsx
const handleUploadClick = () => {
  onUpload(node.id, node.data.label);
};
```

### 2. 文件选择和处理逻辑

**文件：** `src/app/components/data-collection-editor.tsx`

**位置：** 第118-143行

```tsx
// 处理文件上传
const handleFileUpload = useCallback((nodeId: string, nodeLabel: string) => {
  const input = document.createElement('input');
  input.type = 'file';
  input.multiple = true;  // 支持多文件
  input.accept = 'image/*,.pdf,.doc,.docx,.xls,.xlsx';  // 文件类型限制
  
  input.onchange = (e: any) => {
    const files = Array.from(e.target.files || []) as File[];
    const newFiles = files.map((file: File) => ({
      id: `${nodeId}-file-${Date.now()}-${Math.random()}`,
      name: file.name,
      type: file.type,
      size: file.size,
      url: URL.createObjectURL(file),  // ⚠️ 目前只是前端本地URL
      uploadDate: new Date().toLocaleString('zh-CN'),
    }));
    
    setUploadedFiles(prev => ({
      ...prev,
      [nodeId]: [...(prev[nodeId] || []), ...newFiles]
    }));
  };
  
  input.click();
}, []);
```

---

## ⚠️ 当前实现状态

### 当前行为
- ✅ 前端可以选择文件（多文件支持）
- ✅ 文件信息存储在前端状态中
- ✅ 使用 `URL.createObjectURL(file)` 创建本地URL（仅用于前端预览）
- ❌ **未真正上传到后端服务器**

### 问题
当前实现只是在前端本地存储文件对象，并没有调用后端API进行实际上传。

---

## 🔌 需要对接的后端API

### API接口设计（建议）

#### 1. 文件上传接口

**端点：** `POST /api/upload`

**请求格式：**
```typescript
// FormData格式
const formData = new FormData();
formData.append('file', file);  // File对象
formData.append('project_id', projectId);  // 项目ID
formData.append('node_id', nodeId);  // 节点ID（可选）
```

**响应格式：**
```json
{
  "project_id": "project-123",
  "object_key": "/data/autore/uploads/project-123/xxx.pdf",
  "source_hash": "sha256:abc123...",
  "filename": "original.pdf",
  "file_type": "pdf",
  "file_size": 1024000,
  "upload_date": "2024-12-30T10:00:00Z"
}
```

#### 2. 批量上传接口（可选）

**端点：** `POST /api/upload/batch`

**请求格式：**
```typescript
const formData = new FormData();
files.forEach((file, index) => {
  formData.append(`files`, file);
});
formData.append('project_id', projectId);
```

**响应格式：**
```json
{
  "uploads": [
    {
      "object_key": "/data/autore/uploads/project-123/file1.pdf",
      "source_hash": "sha256:...",
      "filename": "file1.pdf",
      "file_type": "pdf"
    },
    {
      "object_key": "/data/autore/uploads/project-123/file2.jpg",
      "source_hash": "sha256:...",
      "filename": "file2.jpg",
      "file_type": "image"
    }
  ],
  "total": 2,
  "success_count": 2
}
```

---

## 💡 前端集成建议

### 方案1：修改现有的 `handleFileUpload` 函数

**文件：** `src/app/components/data-collection-editor.tsx`

**修改建议：**

```tsx
// 处理文件上传
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
      formData.append('project_id', nodeId);  // 使用nodeId作为project_id（或需要获取真实的project_id）
      
      try {
        const response = await fetch('/api/upload', {
          method: 'POST',
          body: formData,
        });
        
        if (!response.ok) {
          throw new Error(`上传失败: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        return {
          id: `${nodeId}-file-${Date.now()}-${Math.random()}`,
          name: result.filename,
          type: file.type,
          size: file.size,
          url: result.object_key,  // 后端返回的文件路径
          uploadDate: new Date().toLocaleString('zh-CN'),
          object_key: result.object_key,
          source_hash: result.source_hash,
        };
      } catch (error) {
        console.error('文件上传失败:', error);
        alert(`文件 ${file.name} 上传失败: ${error.message}`);
        return null;
      }
    });
    
    const uploadResults = await Promise.all(uploadPromises);
    const successfulUploads = uploadResults.filter(result => result !== null);
    
    setUploadedFiles(prev => ({
      ...prev,
      [nodeId]: [...(prev[nodeId] || []), ...successfulUploads]
    }));
  };
  
  input.click();
}, []);
```

### 方案2：创建独立的API工具函数（推荐）

**新建文件：** `src/lib/api/upload.ts`

```typescript
// src/lib/api/upload.ts
export interface UploadResponse {
  project_id: string;
  object_key: string;
  source_hash: string;
  filename: string;
  file_type: string;
  file_size: number;
  upload_date: string;
}

export async function uploadFile(
  file: File,
  projectId: string,
  nodeId?: string
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('project_id', projectId);
  if (nodeId) {
    formData.append('node_id', nodeId);
  }
  
  const response = await fetch('/api/upload', {
    method: 'POST',
    body: formData,
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: response.statusText }));
    throw new Error(error.message || `上传失败: ${response.statusText}`);
  }
  
  return response.json();
}

export async function uploadFiles(
  files: File[],
  projectId: string,
  nodeId?: string
): Promise<UploadResponse[]> {
  const uploadPromises = files.map(file => uploadFile(file, projectId, nodeId));
  return Promise.all(uploadPromises);
}
```

**然后在 `data-collection-editor.tsx` 中使用：**

```tsx
import { uploadFiles } from '@/lib/api/upload';

const handleFileUpload = useCallback(async (nodeId: string, nodeLabel: string) => {
  const input = document.createElement('input');
  input.type = 'file';
  input.multiple = true;
  input.accept = 'image/*,.pdf,.doc,.docx,.xls,.xlsx';
  
  input.onchange = async (e: any) => {
    const files = Array.from(e.target.files || []) as File[];
    
    try {
      // 获取真实的project_id（需要从props或context获取）
      const projectId = getCurrentProjectId(); // 需要实现这个函数
      
      // 上传文件
      const uploadResults = await uploadFiles(files, projectId, nodeId);
      
      // 转换格式
      const newFiles = uploadResults.map((result, index) => ({
        id: `${nodeId}-file-${Date.now()}-${index}`,
        name: result.filename,
        type: files[index].type,
        size: result.file_size,
        url: result.object_key,  // 后端返回的文件路径
        uploadDate: new Date().toLocaleString('zh-CN'),
        object_key: result.object_key,
        source_hash: result.source_hash,
      }));
      
      setUploadedFiles(prev => ({
        ...prev,
        [nodeId]: [...(prev[nodeId] || []), ...newFiles]
      }));
    } catch (error) {
      console.error('文件上传失败:', error);
      alert(`上传失败: ${error.message}`);
    }
  };
  
  input.click();
}, []);
```

---

## 📋 后端需要实现的接口

### 1. 文件上传接口

**路由：** `POST /api/upload`

**实现位置：** `backend/api/routes.py`

**实现示例：**

```python
from fastapi import APIRouter, UploadFile, File, Form
from services.skills.ingest_skill import IngestSkill

router = APIRouter()

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    project_id: str = Form(...),
    node_id: str = Form(None)
):
    """文件上传接口"""
    ingest_skill = IngestSkill()
    
    try:
        result = await ingest_skill.execute(file, project_id)
        return {
            "project_id": project_id,
            "object_key": result["object_key"],
            "source_hash": result["file_hash"],
            "filename": file.filename,
            "file_type": result.get("file_type", "unknown"),
            "file_size": file.size if hasattr(file, 'size') else 0,
            "upload_date": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 2. 支持的文件类型

根据前端代码，需要支持：
- 图片：`image/*` (JPG, PNG, BMP, TIFF, WebP等)
- PDF：`.pdf`
- Word：`.doc`, `.docx`
- Excel：`.xls`, `.xlsx`

**注意：** Phase 0目前主要支持PDF和图片，Word和Excel可以后续支持。

---

## 🔄 数据流向

### 当前流程（前端本地）
```
用户选择文件
  ↓
前端File对象
  ↓
URL.createObjectURL() (前端本地URL)
  ↓
存储在前端state中
```

### 目标流程（对接后端）
```
用户选择文件
  ↓
前端File对象
  ↓
FormData + fetch('/api/upload')
  ↓
后端Ingest Skill
  ↓
本地存储 + 计算hash
  ↓
返回object_key和source_hash
  ↓
更新前端state（使用后端返回的信息）
```

---

## 📝 注意事项

1. **项目ID获取**
   - 前端需要能够获取当前的`project_id`
   - 可能需要从props、context或路由参数中获取

2. **错误处理**
   - 需要处理上传失败的情况
   - 显示错误提示给用户
   - 支持重试机制

3. **上传进度（可选）**
   - 可以添加上传进度条
   - 使用`XMLHttpRequest`或`fetch`的进度事件

4. **文件大小限制**
   - 后端需要设置文件大小限制
   - 前端可以预先检查文件大小

5. **文件类型验证**
   - 后端需要验证文件类型
   - 确保只接受允许的文件格式

---

## 🎯 下一步行动

1. **后端：** 实现 `POST /api/upload` 接口
2. **前端：** 修改 `handleFileUpload` 函数，调用后端API
3. **测试：** 验证文件上传功能
4. **优化：** 添加错误处理、进度显示等

---

## 📚 相关文件

- 前端上传按钮：`src/app/components/collection-detail-modal.tsx` (第332-338行)
- 前端上传逻辑：`src/app/components/data-collection-editor.tsx` (第118-143行)
- 后端Ingest Skill：`backend/services/skills/ingest_skill.py`
- 后端API路由：`backend/api/routes.py` (待实现)

