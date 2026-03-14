# Phase 0 优先任务清单（2天验证版）

> **目标**：2天内完成最小可卖Demo，能跑通"上传→专业库→生成1-2个关键章节→证据链→可下载"

---

## ⚠️ 开始之前：6个必要但容易遗漏的关键点

1. requirements.txt / pyproject.toml 先定下来

**⚠️ Parse 定位声明（非常重要，防止架构退化）：**

**Phase 0 文档解析采用 Vision-first 策略：**

- 页面图像是主输入，多模态 LLM 负责结构理解
- 支持文件类型：**PDF** 和 **图片**（JPG/PNG/BMP/TIFF/WebP等）
- OCR / PDF 文本解析仅作为辅助信号，不作为语义来源

**最小建议（Phase 0）：**

创建 `backend/requirements.txt`：

```txt
# Web框架
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6  # 文件上传必须

# 数据验证
pydantic==2.5.3
pydantic-settings==2.1.0  # 用于配置管理

# 数据库（Phase 0推荐SQLite，无需安装）
sqlalchemy==2.0.25

# 文件存储（Phase 0使用本地磁盘，无需对象存储服务）
# 注意：os, pathlib, shutil 都是Python标准库，无需安装

# =============================================================================
# Parse 定位声明（非常重要，防止架构退化）
# =============================================================================
# Phase 0 文档解析采用 Vision-first 策略：
# - 页面图像是主输入，多模态 LLM 负责结构理解
# - 支持文件类型：PDF、图片（JPG/PNG/BMP/TIFF等）
# - OCR / PDF 文本解析仅作为辅助信号，不作为语义来源
# =============================================================================

# PDF解析
pdfplumber==0.10.3  # 用于PDF基本信息提取（辅助）
pdf2image==1.16.3  # PDF转图片（Vision-first必需 - 主输入）

# 图片处理（Vision-first必需 - 支持PDF和图片文件）
Pillow==10.2.0     # 图片处理库（支持JPG/PNG/BMP/TIFF/WebP等格式）
                   # 用于：图片格式转换、尺寸调整、base64编码等

# OCR（Optional / Auxiliary - 可选，Phase 0作为辅助信号，不作为主输入）
# ⚠️ Vision-first：页面图像是主输入
# OCR 仅用于：
# - Top-K 关键页筛选
# - evidence_refs 的 snippet（可读性）
# - 检索索引（后续RAG）
# 选项1：PaddleOCR（如果要用OCR辅助）
# paddlepaddle==2.6.1
# paddleocr==2.7.3
# 选项2：Tesseract（如果要用OCR辅助）
# pytesseract==0.3.10
# 还需要安装系统依赖：apt-get install tesseract-ocr 或 brew install tesseract
# Phase 0可以先不装OCR，直接用多模态LLM（GPT-4V/Claude-3.5-Sonnet）

# HTTP客户端（调用LLM - OpenAI和硅基流动都支持OpenAI兼容API）
httpx==0.26.0  # 用于调用OpenAI和硅基流动API（两者都支持OpenAI兼容格式）

# 环境变量管理
python-dotenv==1.0.0

# 注意：uuid, hashlib, base64, json 都是Python标准库，无需安装
```

**安装：**

```bash
cd backend
pip install -r requirements.txt
```

---

### 2. CORS + 前端代理要一致

**⚠️ 前后端必须一致，否则请求会被CORS拦截！**

**Vite代理配置**（`vite.config.ts`，已更新）：

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      secure: false,
    },
  },
}
```

**后端CORS配置**（`backend/main.py`）：

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AutoRe API", version="0.1.0")

# CORS配置（必须与前端端口一致）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite默认端口
        "http://localhost:3000",  # 如果前端用其他端口
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 所有路由统一加 /api 前缀
from api import routes
app.include_router(routes.router, prefix="/api")
```

---

### 3. .env 必须有（不然后面到处改代码）

**创建 `backend/.env`：**

```env
# 数据库（Phase 0推荐SQLite，无需安装）
DB_URL=sqlite:///./phase0.db

# 文件存储（Phase 0使用本地磁盘，最简单）
STORAGE_BASE_PATH=/data/autore  # 本地存储根目录

# LLM配置
LLM_PROVIDER=openai  # openai 或 siliconflow
LLM_MODEL=gpt-4o
OPENAI_API_KEY=sk-...  # 填入你的API Key
SILICONFLOW_API_KEY=sk-...  # 硅基流动API Key（可选）

# 环境
ENV=development
DEBUG=true
```

**在代码中使用：**

```python
# backend/config.py
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class Settings(BaseSettings):
    db_url: str
    storage_base_path: str = "/data/autore"  # 本地存储根目录
    llm_provider: str = "openai"  # openai 或 siliconflow
    llm_model: str = "gpt-4o"
    openai_api_key: str
    siliconflow_api_key: str = ""  # 硅基流动API Key（可选）
    env: str = "development"
    debug: bool = True
  
    class Config:
        env_file = ".env"
  
    @property
    def uploads_path(self) -> Path:
        """上传文件存储路径"""
        return Path(self.storage_base_path) / "uploads"
  
    @property
    def parsed_path(self) -> Path:
        """解析结果存储路径"""
        return Path(self.storage_base_path) / "parsed"

settings = Settings()
```

---

### 4. run_log 和 professional_data 先建表（哪怕手动SQL）

**⚠️ 这一步要尽早做，否则后面"生成能跑但无法复现/反馈"会断。**

**创建 `backend/database/init.sql`：**

```sql
-- 专业数据库（先定死一个报告类型）
CREATE TABLE IF NOT EXISTS professional_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id VARCHAR NOT NULL,
    test_item VARCHAR NOT NULL,
    test_result DECIMAL(10, 2) NOT NULL,
    test_unit VARCHAR NOT NULL,
    component_type VARCHAR,
    location JSONB,
    evidence_refs JSONB NOT NULL,
    source_hash VARCHAR(64),
    confidence DECIMAL(3, 2),
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_project_id (project_id)
);

-- Run Log（第一等公民）
CREATE TABLE IF NOT EXISTS run_log (
    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    input_file_hashes JSONB,
    skill_steps JSONB,
    llm_usage JSONB,
    total_cost DECIMAL(10, 4) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    error_message TEXT,
    INDEX idx_project_id (project_id),
    INDEX idx_status (status)
);
```

**SQLite版本（Phase 0快速验证）：**

```sql
-- backend/database/init_sqlite.sql
CREATE TABLE IF NOT EXISTS professional_data (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    test_item TEXT NOT NULL,
    test_result REAL NOT NULL,
    test_unit TEXT NOT NULL,
    component_type TEXT,
    location TEXT,  -- JSON字符串
    evidence_refs TEXT NOT NULL,  -- JSON字符串
    source_hash TEXT,
    confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_project_id ON professional_data(project_id);

CREATE TABLE IF NOT EXISTS run_log (
    run_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    status TEXT NOT NULL,
    input_file_hashes TEXT,  -- JSON字符串
    skill_steps TEXT,  -- JSON字符串
    llm_usage TEXT,  -- JSON字符串
    total_cost REAL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_project_id_log ON run_log(project_id);
CREATE INDEX IF NOT EXISTS idx_status ON run_log(status);
```

**初始化脚本：**

```python
# backend/database/init_db.py
import sqlite3
from pathlib import Path

def init_db():
    db_path = Path("phase0.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
  
    # 读取SQL文件并执行
    sql_file = Path(__file__).parent / "init_sqlite.sql"
    with open(sql_file) as f:
        cursor.executescript(f.read())
  
    conn.commit()
    conn.close()
    print("数据库初始化完成！")

if __name__ == "__main__":
    init_db()
```

---

### 5. 目录结构里补 schemas/ + contracts/

**⚠️ 哪怕Phase 0只用2-3个JSON schema，也建议放好，后面抽Orchestrator/Registry不会返工。**

**更新目录结构：**

```
backend/
├── schemas/                  # ⚠️ 新增：JSON Schema定义
│   ├── __init__.py
│   ├── evidence_ref.json
│   └── professional_data.json
├── contracts/                # ⚠️ 新增：数据契约定义
│   ├── __init__.py
│   └── data_contract.py     # Phase 0简化版
├── services/
│   └── llm_gateway/         # ⚠️ 新增：LLM Gateway（支持OpenAI和硅基流动）
│       ├── __init__.py
│       └── gateway.py
├── storage/
├── models/
├── api/
├── database/
│   ├── __init__.py
│   ├── init_sqlite.sql
│   └── init_db.py
├── main.py
├── config.py                # ⚠️ 新增：配置管理
├── requirements.txt
└── .env
```

**示例schema文件：**

```json
// backend/schemas/evidence_ref.json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["object_key", "type", "page", "source_hash"],
  "properties": {
    "object_key": {
      "type": "string",
      "description": "对象存储key"
    },
    "type": {
      "type": "string",
      "enum": ["pdf", "image", "excel"],
      "description": "文件类型"
    },
    "page": {
      "type": "integer",
      "description": "页码（Phase 0只做page级）"
    },
    "snippet": {
      "type": "string",
      "description": "文本片段（可选）"
    },
    "source_hash": {
      "type": "string",
      "description": "源文件hash"
    }
  }
}
```

```json
// backend/schemas/professional_data.json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["test_item", "test_result", "test_unit", "evidence_refs"],
  "properties": {
    "test_item": {"type": "string"},
    "test_result": {"type": "number"},
    "test_unit": {"type": "string"},
    "component_type": {"type": "string"},
    "location": {"type": "object"},
    "evidence_refs": {
      "type": "array",
      "items": {"$ref": "evidence_ref.json"}
    },
    "source_hash": {"type": "string"},
    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
  }
}
```

---

### 6. 后端启动命令统一成一个入口

**确保项目结构：**

```
backend/
├── main.py              # ⚠️ FastAPI应用入口
├── api/
│   ├── __init__.py
│   └── routes.py        # ⚠️ 路由定义
└── ...
```

**`backend/main.py`：**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from api import routes

app = FastAPI(
    title="AutoRe API",
    version="0.1.0",
    description="Phase 0: 最小可卖Demo"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载路由（统一加/api前缀）
app.include_router(routes.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "AutoRe API", "version": "0.1.0"}

@app.get("/health")
async def health():
    return {"status": "ok"}
```

**`backend/api/routes.py`：**

```python
from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from typing import List

router = APIRouter()

class GenerateReportRequest(BaseModel):
    project_id: str
    chapter_config: dict
    project_context: dict

@router.post("/report/generate")
async def generate_report(request: GenerateReportRequest):
    """生成报告 - Phase 0版本（串行调用）"""
    # TODO: 实现串行调用skills
    return {
        "run_id": "xxx",
        "chapter_content": "...",
        "evidence_refs": []
    }

@router.get("/run/{run_id}")
async def get_run_status(run_id: str):
    """查询运行状态和日志"""
    # TODO: 从run_log表查询
    return {
        "run_id": run_id,
        "status": "RUNNING",
        "skill_steps": [],
        "llm_usage": []
    }
```

**启动命令：**

```bash
cd backend
uvicorn main:app --reload --port 8000
```

---

## 🎯 核心目标

**一个报告类型闭环**：选择你最常做、最有商业价值的报告类型（如"民标安全性"），先把它的专业库schema定死（10-30个关键字段），跑通完整流程。

---

## ✅ 前置条件检查清单

**开始实现之前，确保：**

- [ ] `requirements.txt` 已创建并安装依赖
- [ ] `.env` 文件已创建并配置
- [ ] CORS已配置（前后端端口一致）
- [ ] 数据库表已创建（run_log + professional_data）
- [ ] `schemas/` 和 `contracts/` 目录已创建
- [ ] `main.py` 和 `api/routes.py` 已创建基础结构
- [ ] 可以启动后端：`uvicorn main:app --reload --port 8000`
- [ ] 可以访问：http://localhost:8000/health
- [ ] 前端可以调用后端API（测试CORS）

---

## ⚠️ Phase 0 必须补的3个关键点

### 1. 最小Validation（⚠️ 必须做，否则Demo容易"胡写"）

**为什么必须做？**

工程报告一旦开始生成，就会遇到：

- 字段缺失（比如单位没抽到）
- 冲突（两份报告数值不一致）
- 低置信度（OCR错字）

**最小做法（Phase 0就够用）：**

**方案A：在mapping_skill后面做一个validate_min()函数**

```python
# services/skills/mapping_skill.py
def validate_min(professional_data: dict) -> dict:
    """最小验证：5-10条硬规则"""
    errors = []
    warnings = []
  
    # 1. 必填字段检查
    required_fields = ["test_item", "test_result", "test_unit", "component_type"]
    for field in required_fields:
        if not professional_data.get(field):
            errors.append(f"缺少必填字段: {field}")
  
    # 2. 单位合理性检查
    if professional_data.get("test_unit") not in ["MPa", "kPa", "Pa", "N/mm²"]:
        warnings.append(f"单位可能不正确: {professional_data.get('test_unit')}")
  
    # 3. 数值范围检查
    test_result = professional_data.get("test_result")
    if test_result and (test_result < 0 or test_result > 200):
        warnings.append(f"检测结果数值异常: {test_result}")
  
    # 4. 置信度检查
    if professional_data.get("confidence", 1.0) < 0.7:
        warnings.append(f"置信度过低: {professional_data.get('confidence')}")
  
    # 5. 证据链完整性检查
    if not professional_data.get("evidence_refs"):
        errors.append("缺少证据链")
  
    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }
```

**方案B：直接加validation_skill.py（推荐）**

```python
# services/skills/validation_skill.py
class ValidationSkill:
    """最小验证Skill - Phase 0版本"""
  
    def __init__(self):
        self.rules = self._load_min_rules()
  
    def _load_min_rules(self) -> list:
        """5-10条硬规则"""
        return [
            {"type": "required_fields", "fields": ["test_item", "test_result", "test_unit"]},
            {"type": "unit_check", "valid_units": ["MPa", "kPa", "Pa", "N/mm²"]},
            {"type": "value_range", "field": "test_result", "min": 0, "max": 200},
            {"type": "confidence_threshold", "min": 0.7},
            {"type": "evidence_required", "field": "evidence_refs"}
        ]
  
    async def execute(self, input_data: dict) -> dict:
        """执行最小验证"""
        professional_data = input_data.get("professional_data", {})
  
        errors = []
        warnings = []
  
        # 执行规则检查
        for rule in self.rules:
            result = self._check_rule(rule, professional_data)
            errors.extend(result.get("errors", []))
            warnings.extend(result.get("warnings", []))
  
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "professional_data": professional_data,
            "evidence_refs": professional_data.get("evidence_refs", [])
        }
```

**⚠️ 没有最小校验，Demo很容易"一生成就胡写"，客户看一次就不信了。**

---

### 2. Run Log数据库（⚠️ 第一等公民，必须做）

**为什么必须做？**

没有run_log，后面"复现、追责、成本统计、质量反馈闭环"全做不起来。

**Phase 0最小字段（必须包含）：**

```sql
-- Run Log（运行日志）- Phase 0最小集
CREATE TABLE run_log (
    run_id UUID PRIMARY KEY,
    project_id VARCHAR NOT NULL,
    status VARCHAR NOT NULL,  -- RUNNING/SUCCEEDED/FAILED
    input_file_hashes JSONB,  -- 输入文件hash列表（用于复现）
    skill_steps JSONB,        -- 技能名/版本/耗时/结果
    llm_usage JSONB,          -- tokens/cost/模型
    total_cost DECIMAL(10, 4) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    error_message TEXT,
    INDEX idx_project_id (project_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);
```

**skill_steps结构示例：**

```json
[
    {
        "skill_name": "ingest",
        "skill_version": "1.0",
        "start_time": "2024-12-30T10:00:00Z",
        "end_time": "2024-12-30T10:00:05Z",
        "execution_time_ms": 5000,
        "status": "SUCCEEDED",
        "result_id": "ingest-xxx"
    },
    {
        "skill_name": "parse",
        "skill_version": "1.0",
        "start_time": "2024-12-30T10:00:05Z",
        "end_time": "2024-12-30T10:00:15Z",
        "execution_time_ms": 10000,
        "status": "SUCCEEDED",
        "result_id": "parse-xxx"
    }
]
```

**llm_usage结构示例：**

```json
[
    {
        "skill_name": "entity_extraction",
        "provider": "openai",
        "model": "gpt-4o",
        "input_tokens": 1500,
        "output_tokens": 800,
        "cost": 0.003,
        "latency_ms": 1500
    }
]
```

**实现要点：**

```python
# 在API route中创建run_log
@app.post("/api/report/generate")
async def generate_report(request: GenerateReportRequest):
    run_id = generate_run_id()
  
    # 创建run_log
    run_log = {
        "run_id": run_id,
        "project_id": request.project_id,
        "status": "RUNNING",
        "input_file_hashes": [hash_file(f) for f in request.files],
        "skill_steps": [],
        "llm_usage": [],
        "total_cost": 0,
        "created_at": datetime.now()
    }
    await db.run_log.insert(run_log)
  
    try:
        # 执行流程，每步记录到run_log
        result = await execute_workflow(run_id, request)
  
        # 更新run_log
        await db.run_log.update(
            run_id,
            {
                "status": "SUCCEEDED",
                "completed_at": datetime.now(),
                "total_cost": calculate_total_cost(run_log["llm_usage"])
            }
        )
  
        return {"run_id": run_id, "result": result}
    except Exception as e:
        await db.run_log.update(
            run_id,
            {
                "status": "FAILED",
                "error_message": str(e),
                "completed_at": datetime.now()
            }
        )
        raise
```

---

### 3. 证据链字段规范化（⚠️ 避免evidence_refs变成大杂烩）

**为什么必须做？**

统一evidence_refs结构，UI才能很快做"点开证据链"。

**Phase 0最小结构（必须统一）：**

```python
# 统一的evidence_refs结构
evidence_ref = {
    "object_key": str,      # 对象存储key（必须）
    "type": str,            # pdf/image/excel（必须）
    "page": int,            # 页码（必须，Phase 0只做page级）
                           # PDF：实际页码（1, 2, 3...）
                           # 图片：统一用page=1（单张图片）
    "snippet": str,         # 文本片段（可选，但建议有）
    "source_hash": str      # 源文件hash（必须）
}
```

**示例：**

```json
{
    "evidence_refs": [
        {
            "object_key": "ingest/ingest-xxx/original.pdf",
            "type": "pdf",
            "page": 2,
            "snippet": "检测结果：混凝土强度为30.5MPa",
            "source_hash": "sha256:abc123..."
        },
        {
            "object_key": "ingest/ingest-xxx/original.jpg",
            "type": "image",
            "page": 1,
            "snippet": "检测现场照片",
            "source_hash": "sha256:def456..."
        },
        {
            "object_key": "parse/parse-xxx/images/page-3.png",
            "type": "image",
            "page": 1,
            "snippet": "从PDF第3页提取的图片",
            "source_hash": "sha256:ghi789..."
        }
    ]
}
```

**⚠️ 注意：**

- **PDF文件**：`page` 字段为实际页码（从1开始）
- **图片文件**：`page` 字段统一为 `1`（单张图片，无多页概念）
- **从PDF提取的页面图片**：`page` 字段为原PDF页码，`type` 为 `"image"`

**在professional_data中使用：**

```sql
-- 专业数据库（先定死一个报告类型）
CREATE TABLE professional_data (
    id UUID PRIMARY KEY,
    project_id VARCHAR,
    test_item VARCHAR,
    test_result DECIMAL(10, 2),
    test_unit VARCHAR,
    component_type VARCHAR,
    location JSONB,
    evidence_refs JSONB NOT NULL,  -- 必须包含，结构统一
    source_hash VARCHAR(64),       -- 源文件hash
    confidence DECIMAL(3, 2),
    created_at TIMESTAMP,
    INDEX idx_project_id (project_id),
    INDEX idx_source_hash (source_hash)
);
```

**⚠️ bbox可以Phase 1/2再做，Phase 0用page级就够。**

---

## 📋 Phase 0 完整任务清单

### 1. 数据库设计（第一天上午）

**SQLite表结构（见上方"4. run_log 和 professional_data 先建表"部分）**

---

### 2. Skills实现（第一天下午 + 第二天上午）

**必须实现的Skills（按顺序）：**

#### 2.1 Ingest Skill

```python
# services/skills/ingest_skill.py
from pathlib import Path
import hashlib
from config import settings

class IngestSkill:
    def __init__(self):
        self.base_path = settings.uploads_path
        self.base_path.mkdir(parents=True, exist_ok=True)
  
    async def execute(self, file: File, project_id: str) -> dict:
        # 1. 识别文件类型
        file_type = self._detect_file_type(file.name, file.type)
      
        # 2. 计算hash
        file_hash = self._calculate_hash(file)
      
        # 3. 保存到本地磁盘
        ingest_id = generate_id()
        file_ext = Path(file.name).suffix or (".pdf" if file_type == "pdf" else ".jpg")
        save_path = self.base_path / project_id / f"{ingest_id}_original{file_ext}"
        save_path.parent.mkdir(parents=True, exist_ok=True)
      
        # 写入文件
        with open(save_path, "wb") as f:
            content = await file.read()
            f.write(content)
      
        # object_key使用相对路径（便于后续迁移到OSS）
        object_key = f"/data/autore/uploads/{project_id}/{ingest_id}_original{file_ext}"
  
        # 4. 生成元数据
        metadata = {
            "source": "file-upload",
            "timestamp": datetime.now().isoformat(),
            "project_id": project_id,
            "file_info": {
                "name": file.name,
                "size": len(content),
                "type": file.type,
                "file_type": file_type
            }
        }
  
        # 5. 返回
        return {
            "ingest_id": ingest_id,
            "metadata": metadata,
            "object_key": object_key,  # 文件路径
            "file_hash": file_hash,
            "file_type": file_type,
            "evidence_refs": [{
                "object_key": object_key,
                "type": file_type,
                "page": None,
                "snippet": None,
                "source_hash": file_hash
            }]
        }
  
    def _detect_file_type(self, filename: str, mime_type: str) -> str:
        """检测文件类型：pdf 或 image"""
        filename_lower = filename.lower()
        if filename_lower.endswith('.pdf') or mime_type == 'application/pdf':
            return "pdf"
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp']
        image_mimes = ['image/jpeg', 'image/png', 'image/bmp', 'image/tiff', 'image/webp']
        if any(filename_lower.endswith(ext) for ext in image_extensions) or mime_type in image_mimes:
            return "image"
        raise ValueError(f"不支持的文件类型: {filename}")
  
    def _calculate_hash(self, file: File) -> str:
        """计算文件hash"""
        content = file.read()
        file.seek(0)  # 重置文件指针
        return f"sha256:{hashlib.sha256(content).hexdigest()}"
```

#### 2.2 Parse Skill（Vision-first：页面图像为主）

**⚠️ Parse 定位声明（非常重要，防止架构退化）：**

**Phase 0 文档解析采用 Vision-first 策略：**

- 页面图像是主输入，多模态 LLM 负责结构理解
- 支持文件类型：**PDF** 和 **图片**（JPG/PNG/BMP/TIFF/WebP等）
- OCR / PDF 文本解析仅作为辅助信号，不作为语义来源

**Vision-first方案（推荐）：**

```python
# services/skills/parse_skill.py
class ParseSkill:
    """Parse Skill - Vision-first方案（页面图像为主，OCR只做辅助）
  
    支持文件类型：
    - PDF：转成逐页图片后处理
    - 图片：直接使用多模态LLM处理（JPG/PNG/BMP/TIFF/WebP等）
    """
  
    def __init__(self, llm_gateway: LLMGateway):
        self.llm_gateway = llm_gateway  # 多模态LLM（GPT-4V/Claude-3.5-Sonnet）
  
    async def execute(self, ingest_result: dict) -> dict:
        """
        Vision-first流程（统一处理PDF和图片）：
        1. 判断文件类型（PDF或图片）
        2. PDF：转成逐页图片；图片：直接使用
        3. 多模态LLM直接读图，输出结构化字段
        4. OCR只用于辅助（可选）：快速筛关键页、给snippet、做索引
        """
        file_type = ingest_result.get("file_type", "").lower()
        object_key = ingest_result["object_key"]
      
        # 1. 根据文件类型准备图片
        if file_type == "pdf" or object_key.endswith(".pdf"):
            # PDF：转成逐页图片
            page_images = await self.pdf_to_images(object_key)
            file_category = "pdf"
        elif file_type in ["image", "jpg", "jpeg", "png", "bmp", "tiff", "webp"] or \
             any(object_key.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"]):
            # 图片：直接加载
            page_images = await self.load_image(object_key)
            file_category = "image"
        else:
            raise ValueError(f"不支持的文件类型: {file_type}")
    
        # 2. OCR（可选，用于辅助）
        ocr_results = await self.run_ocr_if_needed(page_images)  # Phase 0可以跳过
    
        # 3. 多模态LLM直接读图（主输入）
        # 明确告诉LLM：忽略OCR的行序，只以页面视觉结构为准
        llm_result = await self.llm_gateway.vision_completion(
            provider=settings.llm_provider,  # "openai" 或 "siliconflow"
            model="gpt-4-vision-preview" if settings.llm_provider == "openai" else "qwen-vl-plus",  # 根据provider选择模型
            images=page_images,
            prompt=self._build_vision_prompt(ocr_results, file_category),  # OCR作为提示，不是主输入
            response_format={"type": "json_object"},
            json_schema=self._get_parse_schema()
        )
    
        parsed_data = json.loads(llm_result['content'])
    
        # 4. 构建evidence_refs
        evidence_refs = []
      
        # PDF：每页都有page信息
        if file_category == "pdf":
            for page_num, page_data in enumerate(parsed_data.get("pages", []), 1):
                snippet = ocr_results.get(page_num, {}).get("text_snippet", "") if ocr_results else ""
                evidence_refs.append({
                    "object_key": object_key,
                    "type": "pdf",
                    "page": page_num,
                    "snippet": snippet,
                    "source_hash": ingest_result["file_hash"],
                    "image_key": f"/data/autore/parsed/{parse_id}/page-{page_num}.png"
                })
        # 图片：单张图片，page=1或None
        else:
            snippet = ocr_results.get(1, {}).get("text_snippet", "") if ocr_results else ""
            evidence_refs.append({
                "object_key": object_key,
                "type": "image",
                "page": 1,  # 图片统一用page=1，或None
                "snippet": snippet,
                "source_hash": ingest_result["file_hash"],
                "image_key": object_key  # 图片本身就是image_key
            })
    
        # 5. 返回（视觉结构为主）
        # ⚠️ 优先级：page_images > structured_data > ocr_text_optional
        return {
            "parse_id": generate_id(),
            "file_category": file_category,  # pdf 或 image
            # 第一等公民：page_images（image_key + page_num）
            "page_images": [
                {
                    "image_key": ref.get("image_key", object_key),
                    "page_num": ref.get("page", 1),
                    "object_key": ref["object_key"]
                }
                for ref in evidence_refs
            ],
            # 第二等公民：structured_data（LLM 输出）
            "structured_data": parsed_data,  # LLM直接输出的结构化数据
            # 第三等公民：ocr_text_optional（如果使用了OCR）
            "ocr_text_optional": ocr_results if ocr_results else None,  # OCR辅助文本（可选）
            "confidence_score": 0.95,  # Vision-first通常更准确
            "evidence_refs": evidence_refs
        }
  
    async def pdf_to_images(self, object_key: str) -> list:
        """PDF转成逐页图片，保存到本地并返回base64"""
        from pdf2image import convert_from_path
        from io import BytesIO
        import base64
        from pathlib import Path
        from config import settings
      
        # 从本地路径读取PDF（去掉/data/autore前缀，使用实际路径）
        pdf_path = Path(object_key.replace("/data/autore", str(settings.storage_base_path)))
      
        # 转换为图片
        images = convert_from_path(str(pdf_path))
      
        # 保存图片到本地并转换为base64
        parse_id = generate_id()
        parsed_dir = settings.parsed_path / parse_id
        parsed_dir.mkdir(parents=True, exist_ok=True)
      
        page_images = []
        for page_num, img in enumerate(images, 1):
            # 保存到本地
            page_path = parsed_dir / f"page-{page_num}.png"
            img.save(page_path, 'PNG')
          
            # 转换为base64（用于LLM API）
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            page_images.append(f"data:image/png;base64,{img_base64}")
      
        return page_images
  
    async def load_image(self, object_key: str) -> list:
        """加载图片文件，返回base64编码"""
        from PIL import Image
        from io import BytesIO
        import base64
        from pathlib import Path
        from config import settings
      
        # 从本地路径读取图片
        image_path = Path(object_key.replace("/data/autore", str(settings.storage_base_path)))
      
        # 使用Pillow打开图片
        img = Image.open(image_path)
      
        # 转换为base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
      
        return [f"data:image/png;base64,{img_base64}"]
  
    async def run_ocr_if_needed(self, page_images: list) -> dict:
        """
        OCR辅助（可选）
        - 快速筛"关键页"（Top-K）
        - 给evidence_refs做snippet（可读性）
        - 做检索索引（后续RAG）
        """
        # Phase 0可以先不实现，直接用多模态LLM
        return {}
```

**为什么Vision-first能解决复杂版式问题：**

- ✅ **版式结构乱 → OCR乱，但LLM仍然能看见**：表格线、标题层级、表头-表体关系、盖章、手写标注
- ✅ **图片和PDF统一处理**：都转换为图像后，用多模态LLM统一理解，无需区分文件格式
- ✅ **OCR不再决定语义结构**，最多只是"提示"
- ✅ **LLM输出时必须带page**（证据链页码，PDF有页码，图片统一用page=1）

**支持的文件类型：**

- **PDF**：使用 `pdf2image`转成逐页图片
- **图片**：使用 `Pillow`直接加载（支持JPG/PNG/BMP/TIFF/WebP等）
- **统一流程**：所有文件类型都转换为图像 → 多模态LLM处理 → 结构化输出

#### 2.3 Entity Extraction Skill

**⚠️ 注意：如果Parse Skill已经用Vision-first输出结构化数据，这一步可以简化或合并**

```python
# services/skills/entity_extraction_skill.py
class EntityExtractionSkill:
    """
    Entity Extraction Skill
    如果Parse已经用Vision-first输出结构化数据，这一步主要是：
    - 进一步结构化（提取具体实体）
    - 标准化实体格式
    - 合并多页数据
    """
  
    def __init__(self, llm_gateway: LLMGateway):
        self.llm_gateway = llm_gateway  # LLM Gateway（支持OpenAI和硅基流动）
  
    async def execute(self, parse_result: dict) -> dict:
        """
        如果Parse已经用Vision-first，这里主要是后处理
        如果需要进一步提取，可以：
        1. 用文本LLM进一步结构化（从Parse的结构化数据中提取实体）
        2. 或者直接使用Parse的输出（如果Parse已经足够结构化）
        """
        # 方案1：Parse已经足够结构化，直接使用
        if parse_result.get("structured_data", {}).get("entities"):
            entities = parse_result["structured_data"]["entities"]
        else:
            # 方案2：需要进一步提取实体（使用文本LLM）
            prompt = self._build_prompt_from_structured_data(parse_result["structured_data"])
        
            response = await self.llm_gateway.chat_completion(
                provider=settings.llm_provider,  # "openai" 或 "siliconflow"
                model=settings.llm_model,  # 根据配置选择模型
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                json_schema=self._get_extraction_schema()
            )
        
            entities = json.loads(response['content'])
  
        # 返回（继承evidence_refs，确保包含page信息）
        return {
            "extraction_id": generate_id(),
            "entities": entities,
            "evidence_refs": parse_result["evidence_refs"],  # 继承，已包含page信息
            "confidence": self._calculate_confidence(entities),
            "source_hash": parse_result.get("source_hash")
        }
```

**⚠️ Phase 0简化建议：**

如果Parse Skill已经用Vision-first输出结构化数据，Entity Extraction可以：

- **选项A**：直接使用Parse的输出（如果已经足够结构化）
- **选项B**：合并Parse和Entity Extraction（Parse直接输出entities）
- **选项C**：保留Entity Extraction，但主要是格式标准化和合并多页数据

#### 2.4 Mapping Skill（规则为主）

```python
# services/skills/mapping_skill.py
from config import settings

class MappingSkill:
    def __init__(self, llm_gateway: LLMGateway):
        self.llm_gateway = llm_gateway  # LLM Gateway（支持OpenAI和硅基流动）
        self.rule_engine = RuleEngine()  # 规则引擎（必须）
  
    async def execute(self, extraction_result: dict, project_context: dict) -> dict:
        # 1. 规则引擎映射（确定性字段）
        rule_mapped = self.rule_engine.map(
            extraction_result["entities"],
            project_context
        )
  
        # 2. LLM处理非标准表达（不确定性字段）
        llm_mapped = await self.llm_map_non_standard_fields(
            extraction_result["entities"],
            rule_mapped
        )
  
        # 3. 合并结果
        professional_data = self._merge_mappings(rule_mapped, llm_mapped)
  
        # 4. Schema校验（硬约束）
        validated = self.schema_validator.validate(professional_data)
  
        # 5. 添加evidence_refs（必须）
        professional_data["evidence_refs"] = extraction_result["evidence_refs"]
        professional_data["source_hash"] = extraction_result["source_hash"]
  
        return {
            "mapping_id": generate_id(),
            "professional_data": professional_data,
            "evidence_refs": professional_data["evidence_refs"]
        }
```

#### 2.5 Validation Skill（⚠️ 必须做，最小版本）

```python
# services/skills/validation_skill.py
class ValidationSkill:
    """最小验证Skill - Phase 0版本"""
  
    def __init__(self):
        self.rules = [
            {"type": "required_fields", "fields": ["test_item", "test_result", "test_unit"]},
            {"type": "unit_check", "valid_units": ["MPa", "kPa", "Pa", "N/mm²"]},
            {"type": "value_range", "field": "test_result", "min": 0, "max": 200},
            {"type": "confidence_threshold", "min": 0.7},
            {"type": "evidence_required", "field": "evidence_refs"}
        ]
  
    async def execute(self, mapping_result: dict) -> dict:
        professional_data = mapping_result["professional_data"]
  
        errors = []
        warnings = []
  
        # 执行规则检查
        for rule in self.rules:
            result = self._check_rule(rule, professional_data)
            errors.extend(result.get("errors", []))
            warnings.extend(result.get("warnings", []))
  
        # 如果有错误，拒绝继续
        if errors:
            raise ValidationError(f"验证失败: {errors}")
  
        return {
            "is_valid": True,
            "errors": errors,
            "warnings": warnings,
            "professional_data": professional_data,
            "evidence_refs": professional_data["evidence_refs"]
        }
```

#### 2.6 Chapter Generation Skill

```python
# services/skills/chapter_generation_skill.py
from config import settings

class ChapterGenerationSkill:
    def __init__(self, llm_gateway: LLMGateway, professional_db: ProfessionalDB):
        self.llm_gateway = llm_gateway  # LLM Gateway（支持OpenAI和硅基流动）
        self.professional_db = professional_db  # 只能读专业库
  
    async def execute(self, chapter_config: dict, project_id: str) -> dict:
        # 1. 从专业库读取数据（只能读专业库）
        professional_data = await self.professional_db.get_by_project(project_id)
  
        # 2. 构建prompt
        prompt = self._build_prompt(chapter_config, professional_data)
  
        # 3. 调用LLM生成章节
        response = await self.llm_gateway.chat_completion(
            provider=settings.llm_provider,  # "openai" 或 "siliconflow"
            model=settings.llm_model,  # 根据配置选择模型
            messages=[{"role": "user", "content": prompt}]
        )
  
        # 4. 返回（包含evidence_refs）
        return {
            "generation_id": generate_id(),
            "chapter_content": response['content'],
            "evidence_refs": self._collect_evidence_refs(professional_data)  # 从专业库收集
        }
```

---

### 3. API Routes（第二天下午）

**⚠️ Phase 0可以暂时不做Orchestrator，但要留接口**

**方案：先用API route串行调用skills跑通闭环**

```python
# api/routes.py
@app.post("/api/report/generate")
async def generate_report(request: GenerateReportRequest):
    """生成报告 - Phase 0版本（串行调用）"""
  
    # 1. 创建run_id和run_log
    run_id = generate_run_id()
    run_log = await create_run_log(run_id, request)
  
    try:
        # 2. Ingest
        ingest_result = await ingest_skill.execute(request.files[0], request.project_id)
        await record_skill_step(run_log, "ingest", ingest_result)
  
        # 3. Parse
        parse_result = await parse_skill.execute(ingest_result)
        await record_skill_step(run_log, "parse", parse_result)
  
        # 4. Entity Extraction
        extraction_result = await entity_extraction_skill.execute(parse_result)
        await record_llm_usage(run_log, "entity_extraction", extraction_result)
        await record_skill_step(run_log, "entity_extraction", extraction_result)
  
        # 5. Mapping
        mapping_result = await mapping_skill.execute(extraction_result, request.project_context)
        await record_llm_usage(run_log, "mapping", mapping_result)
        await record_skill_step(run_log, "mapping", mapping_result)
  
        # 6. Validation（⚠️ 必须做）
        validation_result = await validation_skill.execute(mapping_result)
        await record_skill_step(run_log, "validation", validation_result)
  
        # 7. 写入专业库
        professional_data_id = await professional_db.insert(validation_result["professional_data"])
  
        # 8. Chapter Generation
        chapter_result = await chapter_generation_skill.execute(
            request.chapter_config,
            request.project_id
        )
        await record_llm_usage(run_log, "chapter_generation", chapter_result)
        await record_skill_step(run_log, "chapter_generation", chapter_result)
  
        # 9. 更新run_log
        await update_run_log_success(run_log, chapter_result)
  
        return {
            "run_id": run_id,
            "chapter_content": chapter_result["chapter_content"],
            "evidence_refs": chapter_result["evidence_refs"]
        }
  
    except Exception as e:
        await update_run_log_failed(run_log, str(e))
        raise
```

**⚠️ 只要现在每个skill的输入输出都按schema走，后面抽orchestrator不痛。**

---

### 4. UI（第二天晚上）

**最小UI功能：**

1. **文件上传**
2. **结果展示**（章节内容 + 证据链）
3. **反馈入口**（某章不对、证据链不可信）

**证据链可视化（Phase 0最小版）：**

```typescript
// 点击证据链，显示来源
function EvidenceChainView({ evidenceRefs }) {
    return (
        <div>
            {evidenceRefs.map((ref, idx) => (
                <div key={idx} onClick={() => showSource(ref)}>
                    <span>来源: {ref.type}</span>
                    <span>页码: {ref.page}</span>
                    <span>片段: {ref.snippet}</span>
                </div>
            ))}
        </div>
    );
}
```

---

## ✅ Phase 0 检查清单

### 数据库

- [ ] professional_data表（schema定死一个报告类型）
- [ ] run_log表（第一等公民，包含所有必需字段）
- [ ] evidence_refs结构统一（object_key, type, page, snippet, source_hash）

### Skills

- [ ] Ingest Skill（文件上传 + hash + 对象存储，支持PDF和图片）
- [ ] Parse Skill（Vision-first：页面图像为主，OCR只做辅助，支持PDF和图片）
- [ ] Entity Extraction Skill（只接1-2个模型）
- [ ] Mapping Skill（规则为主、LLM为辅）
- [ ] **Validation Skill（⚠️ 必须做，最小版本）**
- [ ] Chapter Generation Skill（只读专业库）

### API

- [ ] 串行调用skills的API route
- [ ] run_log记录（每步都记录）
- [ ] 错误处理

### UI

- [ ] 文件上传
- [ ] 结果展示
- [ ] 证据链可视化（page级）
- [ ] 反馈入口

### 关键点

- [ ] **最小Validation已实现**（5-10条硬规则）
- [ ] **run_log是第一等公民**（包含skill_steps, llm_usage）
- [ ] **evidence_refs结构统一**（避免大杂烩）

---

## 🚫 Phase 0 先别做

- ❌ Orchestrator（Phase 1再做，但留接口）
- ❌ Job Queue（Phase 1再做）
- ❌ 多Provider（只接1-2个）
- ❌ bbox级证据链（只做page级）
- ❌ Skill Registry完整版（先写死调用）
- ❌ Validation完整版（先做最小版本）

---

## 📝 2天时间分配建议

**第一天：**

- 上午：数据库设计 + 创建表
- 下午：Ingest + Parse + Entity Extraction Skills
- 晚上：Mapping + Validation Skills

**第二天：**

- 上午：Chapter Generation Skill + API Routes
- 下午：UI基础功能
- 晚上：测试 + 调优

---

## 🎯 验证标准

**能跑通以下流程就算Phase 0完成：**

1. 上传一个PDF检测报告或图片文件
2. 系统解析并提取实体（Vision-first，支持PDF和图片）
3. 映射到专业库（带验证）
4. 生成1-2个关键章节
5. 显示证据链（可点击查看来源）
6. run_log完整记录所有步骤和成本

**如果以上都能跑通，Phase 0就成功了！**
