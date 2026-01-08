# Report Platform Autore

Report Platform Autore 是一个智能化的自动化报告生成平台，旨在通过 AI 技术简化专业报告的编写流程。该平台能够自动提取文档信息（如 PDF 原始记录），进行数据映射与验证，并最终生成符合标准的专业报告。

## ✨ 核心功能

*   **智能文档解析**: 集成 PDF 解析工具（Poppler），支持从原始记录文件中自动提取关键数据。
*   **自动化流程 (Pipeline)**:
    *   **Ingest Skill**: 数据摄入与预处理。
    *   **Parse Skill**: 结构化数据解析。
    *   **Mapping Skill**: 数据映射到标准模板。
    *   **Validation Skill**: 数据完整性与规则校验。
    *   **Generation Skill**: 自动生成最终报告章节。
*   **LLM 集成**: 内置 LLM Gateway，支持接入大语言模型以增强文本生成和语义理解能力。
*   **可视化管理**: 提供直观的前端界面，支持项目管理、数据采集编辑、报告预览与审核。
*   **模板系统**: 灵活的模板注册与管理机制，适应不同类型的报告需求。

## 🛠 技术栈

### 前端 (Frontend)
*   **框架**: [React](https://react.dev/) + [TypeScript](https://www.typescriptlang.org/)
*   **构建工具**: [Vite](https://vitejs.dev/)
*   **样式**: [Tailwind CSS](https://tailwindcss.com/)
*   **UI 组件库**: [Radix UI](https://www.radix-ui.com/), [Lucide React](https://lucide.dev/) (图标)
*   **状态管理与工具**: `react-hook-form` (表单), `framer-motion` (动画), `recharts` (图表)

### 后端 (Backend)
*   **框架**: [FastAPI](https://fastapi.tiangolo.com/) (Python)
*   **数据库**: SQLite (Phase 0 阶段), 支持扩展 PostgreSQL
*   **PDF 处理**: Poppler
*   **AI/LLM**: 自定义 LLM Gateway 架构

## 📂 项目结构

```
Reportplatformautore/
├── backend/                # 后端核心代码
│   ├── api/                # API 路由定义
│   ├── contracts/          # 数据契约与验证规则
│   ├── database/           # 数据库初始化与 SQL 脚本
│   ├── models/             # 数据模型定义
│   ├── schemas/            # Pydantic 数据验证模式
│   ├── services/           # 核心业务逻辑 (Skills, LLM Gateway)
│   ├── storage/            # 文件存储服务
│   ├── tests/              # 后端测试用例
│   ├── main.py             # FastAPI 应用入口
│   └── requirements.txt    # Python 依赖列表
├── src/                    # 前端源代码
│   ├── app/                # 应用程序主逻辑
│   │   ├── components/     # UI 组件
│   │   ├── nodes/          # 流程节点组件
│   │   └── ui/             # 基础 UI 库
│   ├── styles/             # 全局样式文件
│   └── main.tsx            # 前端入口文件
├── data/                   # 本地数据存储 (上传文件等)
├── guidelines/             # 项目开发指南
└── README_Gemini.md        # 本文档
```

## 🚀 快速开始

### 环境要求
*   Node.js (推荐 v18+)
*   Python 3.10+
*   Poppler (用于 PDF 处理，Windows 下已内置于 `backend/poppler-windows`)

### 1. 后端设置

1.  进入后端目录：
    ```bash
    cd backend
    ```

2.  创建并激活虚拟环境：
    ```bash
    # Windows
    python -m venv venv
    venv\Scripts\activate

    # Linux/macOS
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  安装依赖：
    ```bash
    pip install -r requirements.txt
    ```

4.  初始化数据库（首次运行）：
    ```bash
    # 确保在 backend 目录下
    python -m database.init_db
    ```

5.  启动后端服务：
    ```bash
    uvicorn main:app --reload --port 8000
    ```
    后端 API 文档地址：http://localhost:8000/docs

### 2. 前端设置

1.  打开新的终端窗口，进入项目根目录：
    ```bash
    # 如果还在 backend 目录，请先返回上级
    cd ..
    ```

2.  安装依赖：
    ```bash
    npm install
    # 或者
    yarn install
    # 或者
    pnpm install
    ```

3.  启动开发服务器：
    ```bash
    npm run dev
    ```
    前端访问地址：http://localhost:5173

## 📖 开发指南

*   **API 交互**: 前端通过 Vite 代理 (`vite.config.ts`) 将 `/api` 请求转发至后端 `localhost:8000`。
*   **数据库**: 当前使用 SQLite (`phase0.db`)，通过 `backend/database/` 下的脚本进行管理。
*   **添加新功能**:
    1.  在 `backend/schemas` 定义数据结构。
    2.  在 `backend/services/skills` 实现业务逻辑。
    3.  在 `backend/api` 注册路由。
    4.  在前端 `src/app` 创建对应组件并调用 API。

## 📝 许可证

[MIT License](LICENSE) (如有需要请替换为具体 License)

