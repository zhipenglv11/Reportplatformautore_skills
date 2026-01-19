# 声明式 Skills 快速开始

## ✅ 已完成的工作

1. ✅ **核心组件实现**
   - `SkillLoader`: 解析 SKILL.md 和 fields.yaml
   - `ScriptRunner`: 执行脚本（parse.py 等）
   - `DeclarativeSkillExecutor`: 执行声明式 Skills
   - `SkillRegistry`: 统一技能注册表

2. ✅ **API 路由**
   - `/api/skills/list` - 列出所有技能
   - `/api/skill/{skill_name}/info` - 获取技能信息
   - `/api/skill/execute` - 执行声明式 Skill（通用接口）
   - `/api/skill/concrete-table-recognition` - 混凝土表格识别（专用接口）

3. ✅ **配置更新**
   - 在 `config.py` 中添加了声明式 Skills 配置
   - 支持通过环境变量配置路径

## 🚀 快速测试

### 1. 启动服务

```bash
cd backend
python main.py
```

### 2. 测试列出技能

```bash
curl http://localhost:8000/api/skills/list
```

应该看到：
```json
{
  "imperative": ["ingest", "parse", "mapping", ...],
  "declarative": ["concrete-table-recognition", "notebooklm"]
}
```

### 3. 测试混凝土表格识别

```bash
curl -X POST http://localhost:8000/api/skill/concrete-table-recognition \
  -F "file=@path/to/your/table.pdf" \
  -F "format=json"
```

## 📝 注意事项

### 1. 路径配置

确保 `backend/config.py` 中的 `declarative_skills_path` 指向正确的目录：

```python
declarative_skills_path: str = "D:/All_about_AI/projects/5_skills_create"
```

或者通过环境变量设置：
```env
DECLARATIVE_SKILLS_PATH=D:/All_about_AI/projects/5_skills_create
```

### 2. 脚本依赖

`concrete-table-recognition` 技能需要：
- Python 虚拟环境（`.venv`）
- 已安装的依赖（`requirements.txt`）
- 环境变量（如 `QWEN_API_KEY`）

如果脚本执行失败，检查：
- 技能目录下是否有 `.venv` 目录
- 是否已安装所有依赖
- 环境变量是否正确设置

### 3. 脚本执行方式

当前实现直接使用系统 Python 执行脚本。如果技能需要虚拟环境，可以：

**选项 A**：修改 `ScriptRunner` 使用虚拟环境的 Python
**选项 B**：在脚本内部处理虚拟环境（如 `concrete-table-recognition` 的 `run.py`）

## 🔧 下一步优化建议

1. **虚拟环境支持**：在 `ScriptRunner` 中自动检测和使用技能的虚拟环境
2. **环境变量传递**：自动从配置中读取并传递给脚本
3. **结果缓存**：对相同输入的结果进行缓存
4. **异步执行**：支持长时间运行的脚本异步执行
5. **进度跟踪**：支持脚本执行进度报告

## 📚 更多信息

- [使用指南](./DECLARATIVE_SKILLS_USAGE.md)
- [集成方案](./DECLARATIVE_SKILLS_INTEGRATION_PLAN.md)
- [架构对比](./SKILL_ARCHITECTURE_COMPARISON.md)
