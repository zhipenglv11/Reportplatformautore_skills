# Vertical Report Platform

垂直报告平台是一个用于生成专业工程报告的全栈应用，支持多种数据源和检测方法，特别是混凝土强度检测报告的自动化生成。

## 项目概述

该项目基于Figma设计稿（[链接](https://www.figma.com/design/YSOYSRXad6NB9R9aQd2oLn/Vertical-Report-Platform)）开发，提供了从数据采集到报告生成的完整解决方案。

### 核心功能

- 数据采集与管理
- 报告自动化生成
- 多种数据源支持
- 灵活的报告模板
- 基于规则的数据分析
- 证据管理与引用

## 技术栈

### 前端

- React 18+
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui组件库

### 后端

- Python 3.10+
- FastAPI
- SQLite（Phase 0）
- Pydantic
- SQLAlchemy
- LangChain（LLM集成）

## 快速开始

### 前置条件

- Node.js 16+
- Python 3.10+
- pip
- git

### 安装与运行

#### 1. 克隆仓库

```bash
git clone <repository-url>
cd Reportplatformautore
```

#### 2. 启动后端服务

```bash
# 进入后端目录
cd backend

# 创建并激活虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
# 或 source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 启动FastAPI服务器
uvicorn main:app --reload --port 8000
```

后端API将运行在 http://localhost:8000
API文档可访问：http://localhost:8000/docs

#### 3. 启动前端服务

```bash
# 返回项目根目录
cd ..

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端应用将运行在 http://localhost:5173

## 项目结构

```
Reportplatformautore/
├── backend/                    # 后端代码
│   ├── api/                    # API路由
│   │   ├── routes.py           # 主要路由
│   │   └── collection_routes.py # 数据采集路由
│   ├── contracts/              # 数据契约和规则
│   │   ├── mapping/            # 数据映射配置
│   │   └── rules/              # 验证规则
│   ├── database/               # 数据库初始化和配置
│   ├── models/                 # 数据模型
│   ├── services/               # 业务服务
│   │   ├── llm_gateway/        # LLM集成
│   │   ├── skills/             # 核心技能实现
│   │   │   ├── chapter_generation_skill.py  # 章节生成技能
│   │   │   ├── ingest_skill.py              # 文件上传技能
│   │   │   ├── mapping_skill.py             # 数据映射技能
│   │   │   ├── parse_skill.py               # 数据解析技能
│   │   │   ├── template_profile_skill.py    # 模板配置技能
│   │   │   └── validation_skill.py          # 数据验证技能
│   │   └── tools/              # 工具函数
│   ├── storage/                # 对象存储
│   ├── .env                    # 环境变量
│   ├── main.py                 # FastAPI入口
│   └── requirements.txt        # Python依赖
├── src/                       # 前端代码
│   ├── app/                    # 主应用
│   │   ├── components/         # 组件
│   │   │   ├── figma/          # Figma相关组件
│   │   │   ├── nodes/          # 节点组件
│   │   │   ├── ui/             # UI组件
│   │   │   ├── collection-detail-modal.tsx  # 采集详情模态框
│   │   │   ├── dashboard.tsx                # 仪表盘
│   │   │   ├── data-collection-editor.tsx   # 数据采集编辑器
│   │   │   ├── node-editor.tsx              # 节点编辑器
│   │   │   ├── project-overview.tsx         # 项目概览
│   │   │   ├── report-editor.tsx            # 报告编辑器
│   │   │   └── report-preview.tsx           # 报告预览
│   │   └── App.tsx             # 应用入口
│   ├── styles/                 # 样式文件
│   └── main.tsx                # 前端入口
├── package.json              # 前端依赖
├── vite.config.ts            # Vite配置
└── README.md                 # 项目说明文档
```

## 后端核心技能（Skills）

### 1. ChapterGenerationSkill

生成报告章节，支持多种数据源和报告模板。

**主要功能：**

- 从专业数据生成报告章节
- 支持混凝土回弹检测报告生成
- 支持多种报告模板样式
- 基于规则的结果评价
- 证据引用管理

**支持的数据集：**

- `concrete_rebound_tests`：混凝土回弹检测结果
- `concrete_rebound_record_sheet`：回弹检测原始记录
- `concrete_strength_description`：混凝土强度描述

### 2. IngestSkill

处理文件上传和存储，将上传的文件保存到本地存储。

**主要功能：**

- 接收文件上传
- 生成唯一文件标识
- 计算文件哈希值
- 保存文件到指定位置

### 3. MappingSkill

将原始数据映射到标准数据模型，支持自定义映射规则。

### 4. ParseSkill

解析上传的文件，提取结构化数据。

### 5. ValidationSkill

验证数据的完整性和准确性，基于预定义规则。

### 6. TemplateProfileSkill

管理报告模板配置，支持自定义模板样式。

## API端点

### 报告生成

```
POST /api/report/generate
```

生成报告章节，支持多种数据源和配置选项。

**请求体：**

```json
{
  "project_id": "string",
  "chapter_config": {
    "dataset_key": "concrete_rebound_tests",
    "template_style": "text_table_1",
    "use_llm": false
  },
  "project_context": {}
}
```

**响应：**

```json
{
  "report_id": "string",
  "chapters": [
    {
      "chapter_id": "string",
      "title": "string",
      "chapter_content": {
        "template_style": "string",
        "reference_spec_type": "string",
        "reference_spec": "string",
        "blocks": [],
        "summary": {}
      },
      "evidence_refs": []
    }
  ]
}
```

### 数据采集

```
POST /api/collection/upload
```

上传数据文件，支持多种格式。

### 运行状态查询

```
GET /api/run/{run_id}
```

查询报告生成的运行状态和日志。

## 前端功能

### 1. 项目管理

- 创建和管理项目
- 查看项目概览
- 项目上下文管理

### 2. 数据采集

- 上传检测数据
- 编辑和管理采集数据
- 数据验证和预览

### 3. 报告编辑

- 可视化报告编辑器
- 支持多种报告模板
- 章节管理和排序
- 实时预览功能

### 4. 节点管理

- 管理报告节点
- 配置节点属性
- 节点连接和依赖管理

### 5. 报告预览

- 实时预览报告内容
- 支持多种格式导出
- 证据引用查看

## 开发指南

### 环境变量配置

后端需要配置以下环境变量（.env文件）：

```
# 数据库配置
DATABASE_URL=sqlite:///./phase0.db

# LLM配置
LLM_PROVIDER=openai
LLM_MODEL=gpt-3.5-turbo
OPENAI_API_KEY=your-api-key

# 应用配置
APP_NAME=AutoRe API
APP_VERSION=0.1.0
```

### 代码规范

- 前端：使用ESLint和Prettier
- 后端：遵循PEP 8规范

### 测试

- 前端：使用Vitest和React Testing Library
- 后端：使用Pytest

## 部署

### 生产环境部署

#### 后端

```bash
# 安装依赖
pip install -r requirements.txt

# 启动生产服务器
uvicorn main:app --host 0.0.0.0 --port 8000
```

#### 前端

```bash
# 构建生产版本
npm run build

# 部署构建产物
# 可使用Nginx、Vercel、Netlify等
```

### 数据库迁移

Phase 0使用SQLite，无需额外迁移。后续可迁移到PostgreSQL或其他数据库。

## 版本历史

- v0.1.0：Phase 0版本，实现基本的报告生成功能

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 联系方式

/
