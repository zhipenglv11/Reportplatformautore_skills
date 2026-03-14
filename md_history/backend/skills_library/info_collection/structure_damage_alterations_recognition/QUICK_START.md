# 快速开始指南

本文档提供快速上手指南。

## 安装

### 1. 克隆或下载项目

```bash
cd structure_damage_alterations_recognition
```

### 2. 创建虚拟环境

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
# 复制示例配置
cp env.example .env

# 编辑.env文件,填入你的API Key
# Windows: notepad .env
# Linux/Mac: nano .env
```

`.env` 文件内容:
```
DASHSCOPE_API_KEY=your_dashscope_api_key_here
DEFAULT_MODEL=qwen
```

## 使用

### 基础用法

```bash
# 处理单个PDF文件
python parse.py document.pdf

# 处理图片文件
python parse.py image.jpg

# 处理多个文件
python parse.py file1.pdf file2.jpg file3.png
```

### 指定输出

```bash
# 指定输出目录
python parse.py input.pdf -o my_output/

# 指定输出格式
python parse.py input.pdf -f csv
python parse.py input.pdf -f excel
python parse.py input.pdf -f all

# 组合使用
python parse.py input.pdf -o results/ -f all
```

### 指定模型

```bash
# 使用Qwen模型
python parse.py input.pdf -m qwen

# 使用Claude模型(需配置ANTHROPIC_API_KEY)
python parse.py input.pdf -m claude
```

## 输出文件

默认输出在 `data/output/` 目录:

- **JSON格式**: `filename_1.json`, `filename_2.json`, ...
- **CSV格式**: `filename.csv`
- **Excel格式**: `filename.xlsx`
- **Markdown格式**: `filename_1.md`, `filename_2.md`, ...

## 示例

### 示例1: 基础提取

```bash
python parse.py examples/sample.pdf
```

输出文件: `data/output/sample_1.json`

### 示例2: 批量处理

```bash
python parse.py data/input/*.pdf -o data/output/ -f all
```

### 示例3: 使用Python API

```python
from scripts.config import Config
from scripts.batch_process import process_single_file

# 初始化配置
config = Config()

# 处理文件
results = process_single_file(
    file_path="test.pdf",
    model="qwen",
    config=config
)

# 查看结果
for result in results:
    print(f"控制编号: {result.meta.control_no}")
    print(f"记录编号: {result.meta.record_no}")
    print(f"数据行数: {len(result.rows)}")
```

## 验证安装

运行以下命令验证安装:

```python
python -c "from scripts.config import Config; c = Config(); print(c.validate())"
```

如果返回 `(True, [])` 表示配置正确。

## 常见问题

### 1. PDF转换失败

**问题**: `PDFPageCountError` 或类似错误

**解决**: Windows用户需要安装Poppler
- 下载: https://github.com/oschwartz10612/poppler-windows/releases
- 解压到项目目录
- 在.env中配置: `POPPLER_PATH=./poppler-24.08.0/Library/bin`

### 2. API调用失败

**问题**: `API Key错误` 或 `认证失败`

**解决**: 
- 检查.env文件中的API Key是否正确
- 确保API Key有足够的额度
- 检查网络连接

### 3. 识别不准确

**问题**: 提取的数据不完整或错误

**解决**:
- 确保输入图片清晰度足够(建议200dpi以上)
- 检查表格格式是否标准
- 可能需要调整提示词(skills/prompt.py)

## 下一步

- 查看 [README.md](README.md) 了解完整功能
- 查看 [references/fields.md](references/fields.md) 了解字段定义
- 查看 [examples/](examples/) 了解输出格式

## 获取帮助

```bash
# 查看帮助信息
python parse.py --help

# 查看版本
python parse.py --version
```
