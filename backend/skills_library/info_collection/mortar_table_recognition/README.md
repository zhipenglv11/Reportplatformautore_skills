# Mortar Strength Recognition Skill

## 📋 项目简介

这是一个用于从砂浆强度检测报告中提取结构化数据的 Claude Code Skill。支持 PDF 和图片格式输入,能够自动识别和提取关键字段信息。

## 🎯 功能特点

- ✅ 支持 PDF 和图片格式
- ✅ 自动识别表格类型
- ✅ 结构化数据提取
- ✅ 多种输出格式(JSON/CSV/Excel)
- ✅ 批量处理支持
- ✅ 数据验证和质量检查

## 📁 项目结构

```
mortar_table_recognition/
├── skills/              # 核心技能模块
│   ├── extractor.py    # 数据抽取器
│   ├── schema.py       # 数据模式定义
│   ├── prompt.py       # 提示词模板
│   └── utils.py        # 工具函数
├── scripts/            # 脚本工具
│   ├── config.py       # 配置管理
│   ├── qwen_client.py  # 通义千问客户端
│   ├── pdf_processor.py # PDF处理
│   ├── formatter.py    # 数据格式化
│   ├── batch_process.py # 批量处理
│   └── run.py          # 主运行脚本
├── references/         # 参考文档
│   ├── fields.md       # 字段定义
│   ├── table_schemas.md # 表格模式
│   └── table_types.md  # 表格类型
├── examples/           # 示例输出
├── data/               # 数据目录
│   ├── input/         # 输入文件
│   ├── output/        # 输出结果
│   └── temp/          # 临时文件
├── parse.py            # 主入口文件
├── skill.json          # Skill配置
├── fields.yaml         # 字段配置
├── requirements.txt    # 依赖包
├── .env.example        # 环境变量示例
└── README.md           # 本文件
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境(推荐)
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填写 API Keys:

```bash
cp env.example .env
```

编辑 `.env` 文件:
```
DASHSCOPE_API_KEY=your_api_key_here
```

### 3. 配置字段

在 `fields.yaml` 中定义需要抽取的字段(待用户提供)。

### 4. 运行提取

```bash
# 单个文件
python parse.py your_file.pdf

# 多个文件
python parse.py file1.pdf file2.jpg file3.png

# 指定输出目录和格式
python parse.py input.pdf -o output/ -f json

# 生成多种格式
python parse.py input.pdf -f all
```

## 📝 字段配置

**重要**: 用户需要在以下文件中配置要抽取的字段:

1. `fields.yaml` - 字段定义配置
2. `references/fields.md` - 详细字段说明文档
3. `skills/schema.py` - 更新 MortarSchema 类

## 🔧 使用说明

### 命令行参数

```bash
python parse.py [files...] [options]

参数:
  files                 要处理的文件(PDF或图片)
  
选项:
  -o, --output DIR     输出目录 (默认: data/output)
  -f, --format FORMAT  输出格式: json|csv|excel|all (默认: json)
  -m, --model MODEL    使用的模型: claude|qwen (默认: 配置文件)
```

### Python API

```python
from scripts.config import Config
from scripts.batch_process import process_single_file

# 处理单个文件
config = Config()
result = process_single_file(
    file_path="test.pdf",
    model="qwen",
    config=config
)

print(result)
```

## 📊 输出格式

### JSON
```json
{
  "field_name": "field_value",
  "source_file": "example.pdf",
  "status": "success",
  "notes": "相关说明"
}
```

### CSV
逗号分隔的表格数据,适合Excel打开。

### Excel
标准的 .xlsx 格式,支持多工作表。

## ⚙️ 配置选项

### 环境变量 (.env)

```bash
# API配置
DASHSCOPE_API_KEY=your_key
ANTHROPIC_API_KEY=your_key

# 模型选择
DEFAULT_MODEL=qwen  # 或 claude
QWEN_MODEL=qwen-vl-max-latest
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# 处理配置
MAX_RETRIES=3
TIMEOUT=60
BATCH_SIZE=10

# Poppler路径(PDF转换)
POPPLER_PATH=./poppler-24.08.0/Library/bin
```

## 🔍 字段定义

### 表头字段 (meta)

| 字段名 | 中文名 | 类型 | 必填 | 说明 | 示例 |
|--------|--------|------|------|------|------|
| table_id | 控制编号 | string | 是 | 左上角表格ID | KJQR-056-206 |
| record_no | 原始记录编号 | string | 是 | 右上角 No: xxxxx | 2500108 |
| test_date | 检测日期 | date | 是 | YYYY-MM-DD格式 | 2023-02-26 |
| instrument_model | 仪器型号 | string | 否 | 检测仪器型号 | SJY-800B |

### 行字段 (rows)

每行包含以下字段:

| 字段名 | 中文名 | 类型 | 必填 | 说明 | 示例 |
|--------|--------|------|------|------|------|
| seq | 序号 | integer | 否 | 表格序号列 | 1 |
| test_location | 检测部位 | string | 是 | 第一列，检测位置描述 | 一层墙 19×D-F 轴 |
| converted_strength_mpa | 换算强度值 | number | 否 | 倒数第二列，单位MPa | 2.0 |
| estimated_strength_mpa | 推定强度值 | number | 否 | 倒数第一列，单位MPa | 1.8 |

### 数据格式规范

1. **日期格式**: 优先YYYY-MM-DD，无法规范化则保留原字符串，禁止推断补全
2. **数值格式**: 保留1位小数，空值或占位符(`—`, `//`)输出null
3. **序号**: 识别不到允许null，不自动补号
4. **文本**: 去首尾空格、压缩连续空格，不改写语义

## 📖 文档

- [字段定义](references/fields.md)
- [表格模式](references/table_schemas.md)
- [表格类型](references/table_types.md)
- [输出示例](examples/)

## 🛠️ 开发

### 添加新字段

1. 更新 `fields.yaml`
2. 修改 `skills/schema.py` 中的 `MortarSchema` 类
3. 更新 `references/fields.md` 文档
4. 测试提取和验证

### 添加新模板

1. 在 `references/table_schemas.md` 中记录新模板
2. 更新提示词模板
3. 添加示例

## 📦 依赖

主要依赖:
- python >= 3.8
- anthropic / dashscope (LLM客户端)
- pdf2image (PDF转换)
- pandas (数据处理)
- Pillow (图像处理)

完整依赖见 `requirements.txt`

## ⚠️ 注意事项

1. **API Key**: 确保正确配置 API Key
2. **Poppler**: Windows 用户需要 Poppler 进行 PDF 转换
3. **字段配置**: 使用前必须配置要抽取的字段
4. **图片质量**: 输入图片质量会影响识别准确率

## 📄 许可证

(待定)

## 👥 贡献

欢迎贡献代码和建议!

## 🙋 支持

如有问题,请提交 Issue 或联系开发者。

---

**待完成事项**:
- [ ] 用户提供字段列表
- [ ] 更新字段定义和模式
- [ ] 添加实际样本和示例
- [ ] 测试和优化提示词
- [ ] 补充Claude客户端支持
