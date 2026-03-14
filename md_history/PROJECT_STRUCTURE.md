# 项目结构建议

## 📁 推荐的项目结构

```
Reportplatformautore/
├── backend/                    # ⚠️ 新建：后端代码
│   ├── services/
│   │   ├── skills/            # Skills实现
│   │   ├── llm_gateway/       # LLM Gateway
│   │   └── tools/            # 工具函数
│   ├── storage/               # 对象存储
│   ├── models/                # 数据模型
│   ├── api/                   # API路由
│   ├── requirements.txt       # Python依赖
│   ├── main.py               # FastAPI入口
│   └── .env                   # 环境变量
├── src/                       # 前端代码（现有）
│   ├── app/
│   └── ...
├── package.json              # 前端依赖（现有）
├── vite.config.ts            # Vite配置（需要更新代理）
└── ...
```

---

## 🔧 配置步骤

### 1. 创建backend文件夹结构

```bash
# 在项目根目录下
mkdir backend
cd backend

# 创建基础结构
mkdir -p services/skills
mkdir -p services/llm_gateway
mkdir -p services/tools
mkdir -p storage
mkdir -p models
mkdir -p api
```

### 2. 初始化Python后端

```bash
cd backend

# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 创建requirements.txt
```

### 3. 配置Vite代理（前端调用后端）

更新 `vite.config.ts`：

```typescript
import { defineConfig } from 'vite'
import path from 'path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',  // 后端FastAPI默认端口
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
```

### 4. 前端API调用示例

```typescript
// src/lib/api.ts
const API_BASE_URL = '/api'  // 使用代理，不需要完整URL

export async function generateReport(data: GenerateReportRequest) {
  const response = await fetch(`${API_BASE_URL}/report/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
  return response.json()
}
```

---

## 🚀 开发流程

### 启动后端（Terminal 1）

```bash
cd backend
source venv/bin/activate  # 或 venv\Scripts\activate (Windows)
uvicorn main:app --reload --port 8000
```

### 启动前端（Terminal 2）

```bash
# 在项目根目录
npm run dev
```

### 访问

- 前端：http://localhost:5173（Vite默认端口）
- 后端API：http://localhost:8000
- API文档：http://localhost:8000/docs（FastAPI自动生成）

---

## 📝 Phase 0 后端最小结构

```
backend/
├── services/
│   ├── skills/
│   │   ├── __init__.py
│   │   ├── ingest_skill.py
│   │   ├── parse_skill.py
│   │   ├── entity_extraction_skill.py
│   │   ├── mapping_skill.py
│   │   ├── validation_skill.py          # ⚠️ 必须做
│   │   └── chapter_generation_skill.py
│   ├── llm_gateway/
│   │   ├── __init__.py
│   │   └── gateway.py                   # 简化版，只接1-2个Provider
│   └── tools/
│       ├── __init__.py
│       ├── pdf_parser.py
│       └── ocr_tool.py
├── storage/
│   ├── __init__.py
│   └── object_storage.py
├── models/
│   ├── __init__.py
│   └── professional_db.py
├── api/
│   ├── __init__.py
│   └── routes.py                         # Phase 0串行调用
├── main.py                               # FastAPI入口
├── requirements.txt
└── .env                                  # 环境变量（API keys等）
```

---

## ⚠️ 注意事项

1. **CORS配置**：FastAPI需要允许前端跨域
   ```python
   from fastapi.middleware.cors import CORSMiddleware
   
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:5173"],  # Vite默认端口
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. **环境变量**：`.env`文件不要提交到Git
   ```
   .env
   .env.local
   ```

3. **数据库**：Phase 0可以用SQLite，方便快速验证
   ```python
   # 使用SQLite（Phase 0）
   DATABASE_URL = "sqlite:///./phase0.db"
   ```

4. **文件上传**：FastAPI处理文件上传
   ```python
   from fastapi import UploadFile, File
   
   @app.post("/api/upload")
   async def upload_file(file: UploadFile = File(...)):
       # 处理文件上传
       pass
   ```

---

## ✅ 检查清单

- [ ] 创建backend文件夹
- [ ] 初始化Python虚拟环境
- [ ] 创建基础文件夹结构
- [ ] 配置Vite代理
- [ ] 创建FastAPI入口文件
- [ ] 配置CORS
- [ ] 测试前后端连接

---

## 🎯 下一步

按照 `PHASE0_PRIORITY_TASKS.md` 中的任务清单，开始实现后端Skills。

