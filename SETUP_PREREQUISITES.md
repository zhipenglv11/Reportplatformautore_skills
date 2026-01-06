# Phase 0 开发前置准备清单

> **开始开发之前，必须准备好以下服务和配置**

---

## 🔑 必须准备的项目

### 1. LLM API Key（必须）

**Phase 0 只需要 1-2 个 Provider：**

#### 1.1 OpenAI（推荐作为主选）

**需要注册：**
- ✅ 访问：https://platform.openai.com/
- ✅ 注册账号并登录
- ✅ 进入 API Keys 页面：https://platform.openai.com/api-keys
- ✅ 创建新的 API Key（Secret Key）
- ✅ **⚠️ 注意**：API Key 只显示一次，请立即保存！

**需要的Key：**
```
OPENAI_API_KEY=sk-...（你的API Key）
```

**模型选择（Phase 0）：**
- 文本LLM：`gpt-4o` 或 `gpt-3.5-turbo`（更便宜）
- 多模态LLM（Vision）：`gpt-4-vision-preview` 或 `gpt-4o`（如果支持vision）

**费用参考：**
- gpt-4o：约 $2.50 / 1M input tokens, $10 / 1M output tokens
- gpt-3.5-turbo：约 $0.50 / 1M input tokens, $1.50 / 1M output tokens
- gpt-4-vision-preview：约 $10 / 1M input tokens, $30 / 1M output tokens

**⚠️ 建议：**
- Phase 0 先充值少量金额测试（如 $5-10）
- 设置使用限制（Usage Limits）防止意外超支

---

#### 1.2 硅基流动（国产备选，可选）

**需要注册：**
- ✅ 访问：https://cloud.siliconflow.cn/
- ✅ 注册账号并登录
- ✅ 进入 API Keys 页面创建 Key
- ✅ 获取 API Key

**需要的Key：**
```
SILICONFLOW_API_KEY=sk-...（你的API Key）
```

**模型选择：**
- 文本LLM：根据平台提供的模型选择
- 多模态LLM：根据平台支持选择

**费用参考：**
- 通常比 OpenAI 便宜
- 具体价格查看平台文档

**⚠️ Phase 0建议：**
- 如果只选一个，先选 OpenAI（生态更成熟）
- 如果需要国产模型，再添加硅基流动

---

### 2. 对象存储（必须）

**Phase 0 推荐：MinIO（本地开发）或 AWS S3（生产环境）**

#### 2.1 MinIO（本地开发推荐，免费）

**本地安装（Docker方式，最简单）：**

```bash
# 使用Docker运行MinIO（推荐）
docker run -d \
  -p 9000:9000 \
  -p 9001:9001 \
  --name minio \
  -e "MINIO_ROOT_USER=minioadmin" \
  -e "MINIO_ROOT_PASSWORD=minioadmin" \
  -v minio-data:/data \
  minio/minio server /data --console-address ":9001"
```

**访问：**
- API端点：http://localhost:9000
- Web控制台：http://localhost:9001
- 默认用户名：`minioadmin`
- 默认密码：`minioadmin`

**配置信息：**
```env
OSS_ENDPOINT=localhost:9000
OSS_BUCKET=autore-files
OSS_ACCESS_KEY=minioadmin
OSS_SECRET_KEY=minioadmin
OSS_USE_SSL=false
```

**首次使用步骤：**
1. 访问 http://localhost:9001
2. 登录（minioadmin / minioadmin）
3. 创建 Bucket：`autore-files`
4. 设置 Bucket 为 Public（如果需要在浏览器直接访问文件）

---

#### 2.2 AWS S3（生产环境推荐）

**需要注册：**
- ✅ 访问：https://aws.amazon.com/
- ✅ 注册 AWS 账号（需要信用卡）
- ✅ 登录 AWS Console
- ✅ 进入 IAM 服务创建用户和访问密钥
- ✅ 进入 S3 服务创建 Bucket

**创建IAM用户：**
1. 登录 AWS Console
2. 进入 IAM 服务
3. 创建新用户（例如：`autore-backend`）
4. 授予权限：`AmazonS3FullAccess`（Phase 0简单起见，生产环境建议最小权限）
5. 创建访问密钥（Access Key ID 和 Secret Access Key）
6. **⚠️ 注意**：Secret Access Key 只显示一次，请立即保存！

**创建S3 Bucket：**
1. 进入 S3 服务
2. 创建 Bucket（例如：`autore-files`）
3. 选择区域（建议选择离你最近的区域）
4. 配置权限（Phase 0可以先设置简单权限）

**配置信息：**
```env
OSS_ENDPOINT=s3.amazonaws.com
OSS_BUCKET=autore-files
OSS_ACCESS_KEY=你的Access Key ID
OSS_SECRET_KEY=你的Secret Access Key
OSS_USE_SSL=true
OSS_REGION=us-east-1  # 你的Bucket所在区域
```

**⚠️ 建议：**
- Phase 0 本地开发用 MinIO（免费，简单）
- 生产环境再用 AWS S3

---

#### 2.3 阿里云OSS / 腾讯云COS（国产替代）

如果需要使用国产对象存储：

**阿里云OSS：**
- 访问：https://www.aliyun.com/product/oss
- 注册账号并开通OSS服务
- 创建 Bucket
- 获取 AccessKeyId 和 AccessKeySecret

**腾讯云COS：**
- 访问：https://cloud.tencent.com/product/cos
- 注册账号并开通COS服务
- 创建 Bucket
- 获取 SecretId 和 SecretKey

---

### 3. 数据库（必须）

**⚠️ Phase 0 强烈推荐：SQLite（最简单，无需Docker，无需安装）**

---

#### 3.1 SQLite（✅ Phase 0 首选，最简单）

**✅ 推荐理由（Phase 0）：**
- ✅ **无需安装任何服务** - SQLite是文件数据库，Python内置支持
- ✅ **无需Docker** - 直接使用，零配置
- ✅ **无需注册云端服务** - 完全本地运行
- ✅ **足够Phase 0使用** - 功能完整，性能足够

**使用步骤：**

1. **无需安装** - SQLite已包含在Python标准库中

2. **配置.env文件：**
```env
DB_URL=sqlite:///./phase0.db
```

3. **直接使用** - 代码会自动创建数据库文件

**⚠️ 注意：**
- SQLite 不适合生产环境（并发、性能限制）
- Phase 0验证成功后，Phase 1/2再切换到PostgreSQL
- **对于Phase 0，SQLite完全够用！**

---

#### 3.2 PostgreSQL（可选，Phase 0不是必须）

**什么时候需要PostgreSQL？**
- ❌ Phase 0：**不需要**，SQLite足够
- ✅ Phase 1+：如果系统稳定，可以考虑切换
- ✅ 生产环境：必须使用PostgreSQL或云数据库

**如果想用PostgreSQL（可选），有两种方式：**

##### 方式A：Docker本地运行（需要安装Docker）

**前提条件：**
- 需要安装Docker Desktop（Windows/Mac）或Docker Engine（Linux）
- Docker安装：https://www.docker.com/get-started

**运行命令：**
```bash
# 使用Docker运行PostgreSQL
docker run -d \
  --name postgres \
  -e POSTGRES_USER=autore \
  -e POSTGRES_PASSWORD=autore123 \
  -e POSTGRES_DB=autore \
  -p 5432:5432 \
  postgres:15
```

**配置：**
```env
DB_URL=postgresql+asyncpg://autore:autore123@localhost:5432/autore
```

##### 方式B：直接安装PostgreSQL（不推荐Phase 0）

- Windows: 下载安装包 https://www.postgresql.org/download/windows/
- Mac: `brew install postgresql@15`
- Linux: `sudo apt-get install postgresql-15`

---

#### 3.3 云数据库（生产环境，Phase 0不需要）

**什么时候需要？**
- ❌ Phase 0：**完全不需要**
- ✅ 生产环境部署时才需要

**可选方案：**
- **AWS RDS**：https://aws.amazon.com/rds/
- **阿里云RDS**：https://www.aliyun.com/product/rds
- **腾讯云CDB**：https://cloud.tencent.com/product/cdb

**配置：**
```env
DB_URL=postgresql+asyncpg://user:password@host:5432/database
```

---

## ✅ Phase 0 数据库选择建议

**强烈推荐：SQLite**

| 选项 | Phase 0推荐度 | 需要安装 | 需要Docker | 需要注册 | 说明 |
|------|-------------|---------|-----------|---------|------|
| **SQLite** | ⭐⭐⭐⭐⭐ 强烈推荐 | ❌ 不需要 | ❌ 不需要 | ❌ 不需要 | 最简单，零配置，直接使用 |
| PostgreSQL (Docker) | ⭐⭐⭐ 可选 | ✅ 需要Docker | ✅ 需要 | ❌ 不需要 | 如果想提前熟悉PostgreSQL |
| PostgreSQL (本地安装) | ⭐⭐ 不推荐 | ✅ 需要 | ❌ 不需要 | ❌ 不需要 | 安装麻烦，Phase 0不需要 |
| 云数据库 | ⭐ 不推荐 | ❌ 不需要 | ❌ 不需要 | ✅ 需要注册 | Phase 0完全不需要，生产环境才用 |

**总结：Phase 0直接用SQLite，最简单最快速！**

---

### 4. 前端配置（必须）

**前端需要配置的API端点：**

#### 4.1 API基础URL

**开发环境：**
```typescript
// src/lib/api.ts 或 src/config.ts
const API_BASE_URL = '/api'  // 使用Vite代理，无需完整URL
// 或
const API_BASE_URL = 'http://localhost:8000/api'  // 如果不用代理
```

**配置项：**
- 后端API地址：`http://localhost:8000`
- API路径前缀：`/api`
- Vite代理已配置（见 `vite.config.ts`）

**无需额外注册，只需确认：**
- ✅ Vite开发服务器端口：5173（默认）
- ✅ 后端API端口：8000（默认）
- ✅ CORS已配置（后端已设置允许localhost:5173）

---

## 📋 完整配置清单

### `.env` 文件配置（backend/.env）

创建 `backend/.env` 文件，填入以下配置：

```env
# =============================================================================
# 数据库配置
# =============================================================================
# ✅ Phase 0推荐：SQLite（最简单，无需安装，无需Docker）
DB_URL=sqlite:///./phase0.db

# （可选）PostgreSQL（Phase 0不需要，Phase 1+才考虑）
# DB_URL=postgresql+asyncpg://autore:autore123@localhost:5432/autore

# =============================================================================
# 对象存储配置
# =============================================================================
# MinIO（本地开发推荐）
OSS_ENDPOINT=localhost:9000
OSS_BUCKET=autore-files
OSS_ACCESS_KEY=minioadmin
OSS_SECRET_KEY=minioadmin
OSS_USE_SSL=false

# 或 AWS S3（生产环境）
# OSS_ENDPOINT=s3.amazonaws.com
# OSS_BUCKET=autore-files
# OSS_ACCESS_KEY=你的Access Key ID
# OSS_SECRET_KEY=你的Secret Access Key
# OSS_USE_SSL=true
# OSS_REGION=us-east-1

# =============================================================================
# LLM配置
# =============================================================================
# Phase 0只接1-2个Provider
LLM_PROVIDER=openai  # openai / siliconflow
LLM_MODEL=gpt-4o     # 文本模型
LLM_VISION_MODEL=gpt-4-vision-preview  # 多模态模型（Vision-first必需）

# OpenAI API Key（必须）
OPENAI_API_KEY=sk-...（填入你的API Key）

# 硅基流动API Key（可选）
# SILICONFLOW_API_KEY=sk-...（如果使用硅基流动）

# =============================================================================
# 环境配置
# =============================================================================
ENV=development
DEBUG=true
```

---

## ✅ 准备工作检查清单

### LLM API Key
- [ ] OpenAI账号已注册
- [ ] OpenAI API Key已创建并保存
- [ ] （可选）硅基流动账号已注册
- [ ] （可选）硅基流动API Key已创建并保存

### 对象存储
- [ ] MinIO已安装并运行（本地开发）
- [ ] MinIO控制台可以访问（http://localhost:9001）
- [ ] MinIO Bucket已创建（autore-files）
- [ ] （或）AWS S3账号已注册
- [ ] （或）AWS S3 Bucket已创建
- [ ] （或）AWS IAM用户和访问密钥已创建

### 数据库
- [ ] **✅ 选择SQLite（Phase 0推荐，无需安装）**
  - [ ] 确认.env中配置：`DB_URL=sqlite:///./phase0.db`
- [ ] （可选）如果想用PostgreSQL
  - [ ] Docker已安装（如果选择Docker方式）
  - [ ] PostgreSQL已运行（Docker或本地安装）
  - [ ] 连接信息已配置到.env

### 前端配置
- [ ] Vite配置已检查（vite.config.ts）
- [ ] API代理已配置（/api -> http://localhost:8000）
- [ ] 前端端口已确认（5173）
- [ ] 后端端口已确认（8000）

### 配置文件
- [ ] `backend/.env` 文件已创建
- [ ] 所有必要的配置项已填入
- [ ] `.env` 文件已添加到 `.gitignore`（不要提交到Git）
- [ ] `backend/.env.example` 已创建（作为模板，可以提交到Git）

---

## 🚀 快速开始步骤

### 1. 准备LLM API Key（5分钟）

```bash
# 1. 访问 OpenAI
https://platform.openai.com/api-keys

# 2. 创建API Key
# 3. 复制并保存到安全的地方
```

### 2. 安装MinIO（5分钟，Docker方式）

```bash
# 安装并运行MinIO
docker run -d \
  -p 9000:9000 \
  -p 9001:9001 \
  --name minio \
  -e "MINIO_ROOT_USER=minioadmin" \
  -e "MINIO_ROOT_PASSWORD=minioadmin" \
  -v minio-data:/data \
  minio/minio server /data --console-address ":9001"

# 访问控制台：http://localhost:9001
# 创建Bucket：autore-files
```

### 3. 配置数据库（1分钟）

**✅ Phase 0推荐：使用SQLite（无需安装，直接使用）**

在`.env`文件中配置：
```env
DB_URL=sqlite:///./phase0.db
```

**（可选）如果想用PostgreSQL：**

```bash
# 前提：需要先安装Docker
# 然后运行PostgreSQL
docker run -d \
  --name postgres \
  -e POSTGRES_USER=autore \
  -e POSTGRES_PASSWORD=autore123 \
  -e POSTGRES_DB=autore \
  -p 5432:5432 \
  postgres:15
```

**⚠️ 建议：Phase 0直接用SQLite，不需要PostgreSQL！**

### 4. 创建.env文件（2分钟）

```bash
cd backend
cp .env.example .env  # 如果.env.example存在
# 或手动创建.env文件，填入上面的配置模板
```

### 5. 验证配置（5分钟）

```bash
# 启动后端
cd backend
uvicorn main:app --reload --port 8000

# 访问健康检查
curl http://localhost:8000/health
# 应该返回：{"status":"ok"}

# 启动前端（另一个终端）
cd ..
npm run dev

# 访问前端
# http://localhost:5173
```

---

## 💰 费用估算（Phase 0测试）

### LLM API费用（粗略估算）

**假设Phase 0测试：**
- 上传10个PDF文件
- 每个PDF平均5页
- 每个PDF调用3次LLM（Parse + Entity Extraction + Mapping + Chapter Generation）

**费用估算：**
- GPT-4o（文本）：约 $0.10 - $0.50
- GPT-4 Vision（多模态）：约 $0.50 - $2.00
- **总计（Phase 0测试）**：约 $1 - $5

**⚠️ 建议：**
- 先充值 $5-10 测试
- 设置使用限制
- 监控使用量

### 对象存储费用

**MinIO（本地）：**
- ✅ 免费

**AWS S3：**
- 存储：$0.023 / GB / 月
- 请求：前1000次请求免费
- Phase 0测试：基本免费

### 数据库费用

**SQLite（Phase 0推荐）：**
- ✅ **完全免费**
- ✅ 无需安装，无需服务
- ✅ 本地文件存储

**PostgreSQL（本地Docker）：**
- ✅ 免费（本地运行）
- ⚠️ 需要Docker（但MinIO也需要，所以一起装）

**云数据库：**
- 根据提供商定价（Phase 0完全不需要）

---

## ⚠️ 重要提醒

1. **API Key安全**
   - ❌ 不要将API Key提交到Git
   - ✅ 使用 `.env` 文件存储
   - ✅ `.env` 文件添加到 `.gitignore`
   - ✅ 生产环境使用环境变量或密钥管理服务

2. **费用控制**
   - ✅ 设置API使用限制
   - ✅ 定期检查使用量
   - ✅ Phase 0测试阶段控制调用次数

3. **配置备份**
   - ✅ 将 `.env.example` 提交到Git（不含真实密钥）
   - ✅ 真实配置保存在 `.env`（不提交）
   - ✅ 记录配置说明文档

---

## 📝 下一步

准备好以上配置后，按照 `PHASE0_PRIORITY_TASKS.md` 开始实现！

