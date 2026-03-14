# Report Platform Autore

Report Platform Autore 是一个智能化的自动化报告生成平台，旨在通过 AI 技术简化专业报告的编写流程。该平台能够自动提取文档信息（如 PDF 原始记录），进行数据映射与验证，并最终生成符合标准的专业报告。

## ✨ 核心功能

* **智能文档解析**: 集成 PDF 解析工具（Poppler），支持从原始记录文件中自动提取关键数据。
* **自动化流程 (Pipeline)**:
  * **Ingest Skill**: 数据摄入与预处理。
  * **Parse Skill**: 结构化数据解析。
  * **Mapping Skill**: 数据映射到标准模板。
  * **Validation Skill**: 数据完整性与规则校验。
  * **Generation Skill**: 自动生成最终报告章节。
* **LLM 集成**: 内置 LLM Gateway，支持接入大语言模型以增强文本生成和语义理解能力。
* **可视化管理**: 提供直观的前端界面，支持项目管理、数据采集编辑、报告预览与审核。
* **模板系统**: 灵活的模板注册与管理机制，适应不同类型的报告需求。

## 🛠 技术栈

### 前端 (Frontend)

* **框架**: [React](https://react.dev/) + [TypeScript](https://www.typescriptlang.org/)
* **构建工具**: [Vite](https://vitejs.dev/)
* **样式**: [Tailwind CSS](https://tailwindcss.com/)
* **UI 组件库**: [Radix UI](https://www.radix-ui.com/), [Lucide React](https://lucide.dev/) (图标)
* **状态管理与工具**: `react-hook-form` (表单), `framer-motion` (动画), `recharts` (图表)

### 后端 (Backend)

* **框架**: [FastAPI](https://fastapi.tiangolo.com/) (Python)
* **数据库**: SQLite (Phase 0 阶段), 支持扩展 PostgreSQL
* **PDF 处理**: Poppler
* **AI/LLM**: 自定义 LLM Gateway 架构

## 📂 项目结构

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

## 🚀 快速开始

### 环境要求

* Node.js (推荐 v18+)
* Python 3.10+
* Poppler (用于 PDF 处理，Windows 下已内置于 `backend/poppler-windows`)

### 1. 后端设置

1. 进入后端目录：

   ```bash
   cd backend
   ```
2. 创建并激活虚拟环境：

   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux/macOS
   python3 -m venv venv
   source venv/bin/activate
   ```
3. 安装依赖：

   ```bash
   pip install -r requirements.txt
   ```
4. 初始化数据库（首次运行）：

   ```bash
   # 确保在 backend 目录下
   python -m database.init_db
   ```
5. 启动后端服务：

   ```bash
   uvicorn main:app --reload --port 8000
   ```

   后端 API 文档地址：http://localhost:8000/docs

### 2. 前端设置

1. 打开新的终端窗口，进入项目根目录：

   ```bash
   # 如果还在 backend 目录，请先返回上级
   cd ..
   ```
2. 安装依赖：

   ```bash
   npm install
   # 或者
   yarn install
   # 或者
   pnpm install
   ```
3. 启动开发服务器：

   ```bash
   npm run dev
   ```

   前端访问地址：http://localhost:5173

## 📖 开发指南

* **API 交互**: 前端通过 Vite 代理 (`vite.config.ts`) 将 `/api` 请求转发至后端 `localhost:8000`。
* **数据库**: 当前使用 SQLite (`phase0.db`)，通过 `backend/database/` 下的脚本进行管理。
* **添加新功能**:
  1. 在 `backend/schemas` 定义数据结构。
  2. 在 `backend/services/skills` 实现业务逻辑。
  3. 在 `backend/api` 注册路由。
  4. 在前端 `src/app` 创建对应组件并调用 API。

## 📝 许可证

[MIT License](LICENSE) (如有需要请替换为具体 License)
