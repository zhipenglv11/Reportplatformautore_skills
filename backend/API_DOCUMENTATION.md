# API接口文档

> 创建时间：2024-12-30  
> Phase 0 - 数据采集接口

---

## 📋 目录结构

本接口文档按照前端操作逻辑组织，与前端功能模块一一对应。

```
API接口文档
├── 数据采集模块 (Collection)
│   ├── 文件上传接口
│   ├── 数据分析接口（待实现）
│   └── 数据保存接口（待实现）
├── 报告生成模块 (Report)
│   ├── 报告生成接口（待实现）
│   └── 运行状态查询接口（待实现）
└── 其他模块（待实现）
```

---

## 🔵 数据采集模块 (Collection)

### 1. 文件上传接口

**接口路径：** `POST /api/collection/upload`

**功能说明：**  
用于数据采集节点（如混凝土强度节点）上传文件到后端服务器。支持PDF和图片文件。

**使用场景：**  
- 用户在"混凝土强度"节点点击"选择文件"按钮
- 选择PDF或图片文件后，前端调用此接口上传文件
- 后端保存文件并返回文件路径和hash等信息

---

#### 请求信息

**请求方法：** `POST`

**Content-Type：** `multipart/form-data`

**请求参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| file | File | 是 | 上传的文件对象（支持PDF、图片） |
| project_id | string | 是 | 项目ID（如："1"） |
| node_id | string | 是 | 节点ID（如："concrete-strength"） |

**支持的文件类型：**
- PDF文件：`.pdf`
- 图片文件：`image/*` (JPG, PNG, BMP, TIFF, WebP等)

**文件大小限制：**  
建议限制为 50MB（后端可根据需要调整）

---

#### 请求示例

**前端代码（TypeScript/React）：**

```typescript
const formData = new FormData();
formData.append('file', file);  // File对象
formData.append('project_id', '1');  // 项目ID
formData.append('node_id', 'concrete-strength');  // 节点ID

const response = await fetch('/api/collection/upload', {
  method: 'POST',
  body: formData,
});

const result = await response.json();
```

**cURL示例：**

```bash
curl -X POST "http://localhost:8000/api/collection/upload" \
  -F "file=@test.pdf" \
  -F "project_id=1" \
  -F "node_id=concrete-strength"
```

---

#### 响应信息

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

**响应字段说明：**

| 字段名 | 类型 | 说明 |
|--------|------|------|
| project_id | string | 项目ID |
| node_id | string | 节点ID |
| object_key | string | 文件存储路径（本地文件系统路径） |
| source_hash | string | 文件SHA256哈希值（用于文件完整性校验） |
| filename | string | 原始文件名 |
| file_type | string | 文件类型（"pdf" 或 "image"） |
| file_size | number | 文件大小（字节） |
| upload_date | string | 上传时间（ISO 8601格式） |

**错误响应（HTTP 400/500）：**

```json
{
  "detail": "文件上传失败: 错误信息"
}
```

**常见错误：**
- `400 Bad Request`: 请求参数缺失或格式错误
- `413 Payload Too Large`: 文件大小超出限制
- `415 Unsupported Media Type`: 不支持的文件类型
- `500 Internal Server Error`: 服务器内部错误（如存储失败）

---

#### 实现细节

**后端实现位置：**
- 路由定义：`backend/api/collection_routes.py`
- 业务逻辑：`backend/services/skills/ingest_skill.py`
- 存储层：`backend/storage/object_storage.py`

**处理流程：**
1. 接收FormData请求
2. 验证文件类型和大小
3. 调用IngestSkill处理文件
4. 保存文件到本地存储（`/data/autore/uploads/{project_id}/`）
5. 计算文件SHA256哈希值
6. 返回文件元数据

**文件存储位置：**
- 本地路径：`/data/autore/uploads/{project_id}/{filename}`
- Phase 0使用本地文件系统存储
- 后续可迁移到对象存储（S3/OSS/MinIO）

---

#### 前端集成

**代码位置：**  
`src/app/components/data-collection-editor.tsx` 第118-190行

**关键代码：**

```typescript
const handleFileUpload = useCallback(async (nodeId: string, nodeLabel: string) => {
  // ... 文件选择逻辑 ...
  
  input.onchange = async (e: any) => {
    const files = Array.from(e.target.files || []) as File[];
    
    const uploadPromises = files.map(async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('project_id', projectId);
      formData.append('node_id', nodeId);
      
      const response = await fetch('/api/collection/upload', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error(`上传失败: ${response.statusText}`);
      }
      
      return await response.json();
    });
    
    // ... 处理上传结果 ...
  };
}, [projectId]);
```

---

#### 注意事项

1. **CORS配置**  
   后端已配置CORS，允许前端域名（localhost:5173, localhost:3000）跨域请求

2. **文件路径格式**  
   `object_key` 使用本地文件系统路径格式，后续迁移到对象存储时格式会变化，但前端无需修改（后端统一处理）

3. **文件哈希**  
   `source_hash` 是文件的SHA256哈希值，用于：
   - 文件完整性校验
   - 去重（相同hash的文件可以复用）
   - 证据链追溯

4. **错误处理**  
   前端应该捕获上传错误并显示用户友好的错误提示

5. **上传进度（可选）**  
   当前实现未包含上传进度，如需进度显示，可以使用XMLHttpRequest或fetch的上传进度事件

---

## 📝 接口开发计划

### Phase 0（当前阶段）

- [x] **文件上传接口** (`POST /api/collection/upload`) ✅ 已完成

### 后续接口（待实现）

- [ ] 数据分析接口（调用Parse Skill）
- [ ] 数据保存接口（保存到专业库）
- [ ] 报告生成接口
- [ ] 运行状态查询接口

---

## 🔗 相关文档

- 后端进度：`backend/BACKEND_PROGRESS.md`
- 前端集成说明：`backend/FRONTEND_UPLOAD_INTEGRATION.md`
- Phase 0任务清单：`PHASE0_PRIORITY_TASKS.md`

---

## 📞 接口测试

### 使用FastAPI自动文档

启动后端后，访问：  
http://localhost:8000/docs

在Swagger UI中可以：
1. 查看接口文档
2. 在线测试接口
3. 查看请求/响应示例

### 使用Postman/cURL

参考上方"请求示例"部分的cURL命令进行测试。

