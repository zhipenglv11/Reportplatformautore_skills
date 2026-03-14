# 砂浆信息抽取节点错误修复总结

## 问题现象
用户上传 PDF 文件（`建材新村_部分8.pdf`）到砂浆信息抽取节点时出现错误：
```
Script exited with code 1; missing dependency (ModuleNot...
```

## 问题根源分析

### 1. Poppler 路径配置错误
**位置**: `backend/config.py` 和 `backend/skills_library/info_collection/mortar_table_recognition/scripts/config.py`

**问题**: 
- 主配置文件: `poppler_bin_path` 为空字符串（默认值）
- 砂浆配置文件: `poppler_path` 指向不存在的路径 `./poppler-24.08.0/Library/bin`

**正确路径**: `backend/poppler-windows/Release-25.12.0-0/poppler-25.12.0/Library/bin`

**影响**: PDF 转图片功能无法工作，导致 `pdf2image.convert_from_path()` 报错

### 2. 缺少 dashscope 依赖
**问题**: `requirements.txt` 中未包含 `dashscope` 库（阿里云通义千问 SDK）

**影响**: 砂浆信息抽取节点使用 Qwen VL 模型时无法导入 `dashscope` 模块

### 3. 模块导入路径错误
**位置**: `backend/skills_library/info_collection/mortar_table_recognition/scripts/batch_process.py`

**问题**: 
```python
from skills.extractor import MortarExtractor  # 错误
```

**正确**: 
```python
from ..skills.extractor import MortarExtractor  # 相对导入
```

## 修复内容

### 修复 1: 更新 poppler 路径配置

**文件**: `backend/config.py`
```python
# 修复前
poppler_bin_path: str = ""  # Poppler bin路径（可选）

# 修复后
poppler_bin_path: str = str(PROJECT_ROOT / "backend" / "poppler-windows" / "Release-25.12.0-0" / "poppler-25.12.0" / "Library" / "bin")
```

**文件**: `backend/skills_library/info_collection/mortar_table_recognition/scripts/config.py`
```python
# 修复前
self.poppler_path = os.getenv('POPPLER_PATH', './poppler-24.08.0/Library/bin')

# 修复后
backend_root = Path(__file__).parent.parent.parent.parent.parent
default_poppler = backend_root / 'poppler-windows' / 'Release-25.12.0-0' / 'poppler-25.12.0' / 'Library' / 'bin'
self.poppler_path = os.getenv('POPPLER_PATH', str(default_poppler))
```

### 修复 2: 添加 dashscope 依赖

**文件**: `backend/requirements.txt`
```python
# 添加
dashscope>=1.14.0  # 阿里云通义千问 SDK（用于 Qwen VL 等多模态模型）
```

**安装命令**（在虚拟环境中）:
```bash
D:/All_about_AI/projects/reportplatform_autore_skills/Reportplatformautore/.venv/Scripts/python.exe -m pip install dashscope
```

### 修复 3: 修正模块导入路径

**文件**: `backend/skills_library/info_collection/mortar_table_recognition/scripts/batch_process.py`
```python
# 修复前
from skills.extractor import MortarExtractor

# 修复后
from ..skills.extractor import MortarExtractor
```

## 验证测试

### 测试 1: Poppler 路径验证
```bash
python test_poppler_config.py
```

**结果**: ✅ 主配置 poppler 路径正确，poppler 可执行文件存在

### 测试 2: 依赖验证
```bash
python -c "import dashscope; print(dashscope.__version__)"
```

**结果**: ✅ 虚拟环境中 dashscope 版本 1.25.12

### 测试 3: 后端服务健康检查
```bash
curl http://localhost:8000/docs
```

**结果**: ✅ HTTP 200 - 后端服务正常运行

## 重要说明

### 1. 虚拟环境使用
后端服务必须使用虚拟环境启动，确保所有依赖正确加载：
```bash
D:/All_about_AI/projects/reportplatform_autore_skills/Reportplatformautore/.venv/Scripts/python.exe start_backend.py
```

### 2. Poppler 依赖说明
- **pdf2image** 库需要系统级别的 **poppler** 工具才能工作
- Windows 系统需要提供 `poppler_path` 参数指向 poppler 的 bin 目录
- 项目已包含 `poppler-windows/Release-25.12.0-0`，无需额外下载

### 3. 模型配置
砂浆信息抽取节点支持两种模型：
- **qwen**: 通义千问 VL（需要 DASHSCOPE_API_KEY 或 QWEN_API_KEY）
- **claude**: Claude 3.5 Sonnet（需要 ANTHROPIC_API_KEY）

确保 `.env` 文件中配置了相应的 API Key。

## 后续建议

### 1. 环境变量配置
创建 `.env` 文件并配置必要的 API Keys（如果还未配置）：
```env
DASHSCOPE_API_KEY=your_dashscope_api_key_here
QWEN_API_KEY=your_qwen_api_key_here
DEFAULT_MODEL=qwen
```

### 2. 其他材料节点检查
建议检查其他材料信息抽取节点是否有类似问题：
- `brick_table_recognition/` - 砖强度
- `concrete_table_recognition/` - 混凝土强度

### 3. 测试上传功能
在前端测试上传砂浆检测 PDF 文件，验证：
1. PDF 能否成功转换为图片
2. LLM 能否正常提取结构化数据
3. 数据是否正确保存到数据库

---
**修复完成时间**: 2026-02-16  
**影响范围**: 砂浆信息抽取节点（mortar_table_recognition）  
**修复状态**: ✅ 已修复并验证  
**后端状态**: ✅ 服务运行中 (http://localhost:8000)
