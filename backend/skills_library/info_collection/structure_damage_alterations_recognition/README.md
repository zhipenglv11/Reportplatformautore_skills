# Structure Damage and Alterations Recognition Skill

## 📋 项目简介

这是一个用于从结构损伤及拆改检查原始记录中提取结构化数据的 Claude/Qwen Skill。支持 PDF 和图片格式输入,能够自动识别和提取关键字段信息。

## 🎯 功能特点

- ✅ 支持 PDF 和图片格式
- ✅ 自动识别表格结构
- ✅ 提取拆改部位和内容描述
- ✅ 识别控制编号和原始记录编号
- ✅ 提取仪器编号等元数据
- ✅ 结构化数据输出
- ✅ 多种输出格式(JSON/CSV/Excel/Markdown)
- ✅ 批量处理支持
- ✅ 数据验证和质量检查

## 📦 项目结构

```
structure_damage_alterations_recognition/
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
│   └── fields.md       # 字段定义
├── examples/           # 示例输出
│   ├── output_example.json
│   └── output_example.md
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

复制 `env.example` 为 `.env` 并填入 API Keys:

```bash
cp env.example .env
```

编辑 `.env` 文件:
```
DASHSCOPE_API_KEY=your_api_key_here
```

### 3. 运行提取

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

## 📝 字段说明

### 表头字段 (meta)

| 字段名 | 中文名 | 类型 | 必填 | 说明 |
|--------|--------|------|------|------|
| control_no | 控制编号 | string | 是 | 表格控制编号/ID |
| record_no | 原始记录编号 | string | 是 | 格式如No: xxxxx |
| instrument_no | 仪器编号 | string | 否 | 检测仪器编号 |
| inspection_date | 检测日期 | string | 否 | YYYY-MM-DD格式 |
| project_name | 工程名称 | string | 否 | 项目名称 |
| inspector | 检查人 | string | 否 | 检查人员 |
| reviewer | 审核人 | string | 否 | 审核人员 |

### 表格行字段 (rows)

| 字段名 | 中文名 | 类型 | 必填 | 说明 |
|--------|--------|------|------|------|
| seq | 序号 | integer | 否 | 表格序号 |
| alteration_location | 拆改部位 | string | 是 | 拆改的具体部位 |
| alteration_description | 拆改内容描述 | string | 是 | **最重要**,正文核心内容 |
| alteration_type | 拆改类型 | string | 否 | 拆除/新增/改造/加固/其他 |
| damage_description | 损伤描述 | string | 否 | 损伤详细描述 |
| damage_type | 损伤类型 | string | 否 | 裂缝/剥落/锈蚀/变形/渗漏 |
| damage_level | 损伤程度 | string | 否 | 轻微/中等/严重 |
| dimension_length | 长度尺寸 | string | 否 | 长度,带单位 |
| dimension_width | 宽度尺寸 | string | 否 | 宽度,带单位 |
| dimension_height | 高度尺寸 | string | 否 | 高度,带单位 |
| remarks | 备注 | string | 否 | 其他说明 |

详细字段说明请查看 [references/fields.md](references/fields.md)

## 💻 使用说明

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
results = process_single_file(
    file_path="test.pdf",
    model="qwen",
    config=config
)

# 结果是列表,每个元素是一个StructureAlterationSchema对象
for result in results:
    print(result.to_dict())
```

## 📤 输出格式

### JSON格式
```json
{
  "meta": {
    "control_no": "KJQR-056-206",
    "record_no": "No: 2500108",
    ...
  },
  "rows": [
    {
      "seq": 1,
      "alteration_location": "一层A轴-B轴间墙体",
      "alteration_description": "拆除原有砖墙...",
      ...
    }
  ],
  "source_file": "example.pdf",
  "status": "success"
}
```

### CSV格式
逗号分隔的表格数据,适合Excel打开。

### Excel格式
标准的.xlsx格式,支持多工作表。

### Markdown格式
可读性好的文本格式,适合文档查看。

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

# Poppler路径(PDF转换,Windows需要)
POPPLER_PATH=./poppler-24.08.0/Library/bin

# 输出配置
DEFAULT_OUTPUT_DIR=data/output
DEFAULT_OUTPUT_FORMAT=json
```

## 📋 字段配置

字段定义在以下文件中:

1. **fields.yaml** - 字段定义配置文件
2. **references/fields.md** - 详细字段说明文档
3. **skills/schema.py** - Python数据模式类

如需修改字段,请同时更新以上三个文件以保持一致。

## 📚 文档

- [字段定义](references/fields.md) - 详细的字段说明和规范
- [输出示例](examples/) - JSON和Markdown格式的输出示例

## 🔧 开发

### 添加新字段

1. 更新 `fields.yaml`
2. 修改 `skills/schema.py` 中的数据类
3. 更新 `skills/prompt.py` 中的提示词
4. 更新 `references/fields.md` 文档
5. 测试提取和验证

### 调试提示词

提示词模板在 `skills/prompt.py` 中,可以根据实际情况调整:
- `get_system_prompt()` - 系统提示词
- `get_extraction_prompt()` - 提取提示词

## 📦 依赖

主要依赖:
- python >= 3.8
- dashscope (通义千问)
- anthropic (Claude,可选)
- pdf2image (PDF转换)
- pandas (数据处理)
- Pillow (图像处理)
- openpyxl (Excel导出)

完整依赖见 `requirements.txt`

## ⚠️ 注意事项

1. **API Key**: 确保正确配置 API Key
2. **Poppler**: Windows 用户需要 Poppler 进行 PDF 转换
   - 下载地址: https://github.com/oschwartz10612/poppler-windows/releases
3. **字段配置**: 使用前请检查字段配置是否符合实际需求
4. **图片质量**: 输入图片质量会影响识别准确率,建议使用高清图片
5. **拆改内容描述**: 这是最重要的字段,会尽可能完整提取

## 🎯 待完善事项

以下是当前需要注意和后续可能需要调整的内容:

### 字段配置
- [x] 基础字段已配置
- [ ] 根据实际样本调整字段定义
- [ ] 补充更多字段(根据用户需求)

### 功能增强
- [ ] 添加 Claude 客户端支持
- [ ] 增加数据验证规则
- [ ] 优化提示词准确率
- [ ] 添加更多输出格式

### 文档完善
- [ ] 添加更多实际样本示例
- [ ] 补充常见问题FAQ
- [ ] 添加性能优化建议

## 📄 许可证

(待定)

## 🤝 贡献

欢迎贡献代码和建议!

## 📞 支持

如有问题,请提交 Issue。

---

**Created with ❤️ for construction inspection automation**
