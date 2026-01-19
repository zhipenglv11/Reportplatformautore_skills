# 文件上传测试指南

## 📋 快速开始

### 方式1：使用 PowerShell 脚本（推荐，Windows）

```powershell
# 基本用法
.\test_file_upload.ps1 -FilePath "C:\path\to\your\table.pdf"

# 指定输出格式
.\test_file_upload.ps1 -FilePath "C:\path\to\your\table.pdf" -Format "json"

# 指定输出目录
.\test_file_upload.ps1 -FilePath "C:\path\to\your\table.pdf" -Format "json" -OutputDir "./output"
```

### 方式2：使用 Python 脚本

```bash
# 基本用法
python test_file_upload.py "C:\path\to\your\table.pdf"

# 指定输出格式
python test_file_upload.py "C:\path\to\your\table.pdf" --format json

# 指定输出目录
python test_file_upload.py "C:\path\to\your\table.pdf" --format json --output-dir ./output
```

### 方式3：使用 PowerShell 直接调用 API

```powershell
# 准备文件路径
$filePath = "C:\path\to\your\table.pdf"

# 构建表单
$form = @{
    file = Get-Item $filePath
    format = "json"
}

# 发送请求
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/skill/concrete-table-recognition" `
    -Method Post `
    -Form $form

# 查看结果
$response | ConvertTo-Json -Depth 10
```

### 方式4：使用 curl（如果已安装）

```bash
curl -X POST http://localhost:8000/api/skill/concrete-table-recognition \
  -F "file=@C:\path\to\your\table.pdf" \
  -F "format=json"
```

---

## 📝 详细说明

### API 端点

**URL**: `POST http://localhost:8000/api/skill/concrete-table-recognition`

**Content-Type**: `multipart/form-data`

### 参数

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `file` | File | ✅ | 要处理的文件（PDF 或图片） |
| `format` | String | ❌ | 输出格式：`json`（默认）、`csv`、`excel` |
| `output_dir` | String | ❌ | 输出目录路径（可选） |

### 响应格式

```json
{
  "success": true,
  "data": {
    "文件": "table.pdf",
    "检测日期": "2024-10-10",
    "检测部位": "2#楼柱梁板楼面",
    "强度等级": "C30",
    ...
  },
  "metadata": {
    "name": "concrete-table-recognition",
    "description": "...",
    "version": "1.0.0"
  },
  "script_result": {
    "success": true,
    "returncode": 0,
    "output": {...},
    "stdout": "...",
    "stderr": ""
  }
}
```

---

## 🔍 测试步骤

### 1. 确认服务运行

```powershell
# 检查服务是否运行
Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
```

应该返回：
```json
{
  "status": "ok"
}
```

### 2. 检查技能是否可用

```powershell
$skills = Invoke-RestMethod -Uri "http://localhost:8000/api/skills/list" -Method Get
$skills.declarative
```

应该包含 `"concrete-table-recognition"`

### 3. 上传文件测试

使用上面任一方式上传文件。

---

## 🐛 常见问题

### Q1: 文件上传失败

**错误**: `400 Bad Request` 或 `文件格式不支持`

**解决方案**:
- 确认文件是 PDF 或图片格式
- 检查文件路径是否正确
- 确认文件没有被其他程序占用

### Q2: 技能未找到

**错误**: `404 Skill not found: concrete-table-recognition`

**解决方案**:
1. 检查声明式 Skills 目录配置
2. 确认技能目录存在且包含 `SKILL.md`
3. 重启后端服务

### Q3: 脚本执行失败

**错误**: `500 Execution failed` 或 `script_result.success = false`

**解决方案**:
1. 查看 `script_result.stderr` 获取详细错误
2. 检查技能脚本的依赖是否已安装
3. 确认技能目录下的虚拟环境已配置

### Q4: 超时错误

**错误**: `Timeout` 或请求长时间无响应

**解决方案**:
1. 检查文件大小，大文件可能需要更长时间
2. 查看后端日志确认脚本是否正在执行
3. 增加超时时间（在脚本中修改）

---

## 📚 更多信息

- 查看 [HOW_TO_USE_DECLARATIVE_SKILLS.md](./HOW_TO_USE_DECLARATIVE_SKILLS.md) 了解完整使用指南
- 查看 [DECLARATIVE_SKILLS_USAGE.md](./DECLARATIVE_SKILLS_USAGE.md) 了解更多高级用法
