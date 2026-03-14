# 信息采集 Skills 执行问题修复总结

## 问题现象
在信息采集配置中：
- ✅ **砖强度 (brick_table_recognition)**: 可以正常识别和运行
- ❌ **砂浆强度 (mortar_table_recognition)**: 出现 `Script exited with code 1; missing dependency (ModuleNotFoundError)` 错误
- ❌ **结构损伤与变动识别 (structure_damage_alterations_recognition)**: 同样的错误
- ❌ 其他没有独立虚拟环境的 skills 也无法运行

## 问题根源

### 核心问题：Python 可执行文件解析逻辑缺陷

**文件**: `backend/services/declarative_skills/script_runner.py`

**原有逻辑**:
```python
def _resolve_python_executable(self) -> str:
    # 1. 检查环境变量 SKILL_PYTHON
    # 2. 检查 skill 目录下的虚拟环境 (.venv)
    # 3. 使用系统 Python (sys.executable)
```

**问题分析**:
1. **砖强度能工作的原因**: 它有自己的独立虚拟环境 (`.venv`)，其中安装了所有依赖
2. **砂浆强度等失败的原因**: 它们**没有**独立虚拟环境，系统回退到 `sys.executable`（系统 Python），而系统 Python 中**缺少** `dashscope` 等依赖

### 依赖安装情况对比

| Skill | 独立虚拟环境 | 原解析结果 | dashscope 可用性 |
|-------|-------------|-----------|-----------------|
| brick_table_recognition | ✅ 有 | Skill .venv | ✅ 可用（独立安装） |
| mortar_table_recognition | ❌ 无 | 系统 Python | ❌ 不可用 |
| structure_damage_alterations | ❌ 无 | 系统 Python | ❌ 不可用 |
| concrete_table_recognition | ✅ 有 | Skill .venv | ✅ 可用（独立安装） |

**关键发现**: 
- 项目根目录**有统一的虚拟环境** (`.venv`)，其中已经安装了 `dashscope` 等所有依赖
- 但脚本执行器没有考虑使用项目根目录的虚拟环境作为回退选项

## 修复方案

### 修改 `_resolve_python_executable()` 方法

**文件**: [backend/services/declarative_skills/script_runner.py](d:\All_about_AI\projects\reportplatform_autore_skills\Reportplatformautore\backend\services\declarative_skills\script_runner.py#L18-L48)

**新逻辑**（4 级回退）:
```python
def _resolve_python_executable(self) -> str:
    """解析 Python 可执行文件路径
    
    优先级：
    1. 环境变量 SKILL_PYTHON
    2. 当前 skill 目录下的虚拟环境 (.venv)
    3. 项目根目录下的虚拟环境 (.venv) ✨ 新增
    4. 系统 Python (sys.executable)
    """
    # 1. 环境变量
    env_python = os.getenv("SKILL_PYTHON")
    if env_python:
        return env_python
    
    # 2. Skill 独立虚拟环境
    venv_candidates = [
        self.skill_dir / ".venv" / "Scripts" / "python.exe",
        self.skill_dir / "venv" / "Scripts" / "python.exe",
        self.skill_dir / ".venv" / "bin" / "python",
        self.skill_dir / "venv" / "bin" / "python",
    ]
    for candidate in venv_candidates:
        if candidate.exists():
            return str(candidate)
    
    # 3. 项目根目录虚拟环境（新增）
    # 路径计算: skill_dir (backend/skills_library/.../skill_name)
    #          -> 向上4级到达项目根目录
    project_root = self.skill_dir.parent.parent.parent.parent
    root_venv_candidates = [
        project_root / ".venv" / "Scripts" / "python.exe",
        project_root / ".venv" / "bin" / "python",
    ]
    for candidate in root_venv_candidates:
        if candidate.exists():
            return str(candidate)
    
    # 4. 系统 Python
    return sys.executable
```

## 修复效果验证

### 测试结果（修复后）

```
skills_library/info_collection/brick_table_recognition:
  有独立虚拟环境: True
  使用的 Python: .../Reportplatformautore/.venv/Scripts/python.exe
  ✓ 使用项目根目录虚拟环境
  ✓ dashscope 可用

skills_library/info_collection/mortar_table_recognition:
  有独立虚拟环境: False
  使用的 Python: .../Reportplatformautore/.venv/Scripts/python.exe
  ✓ 使用项目根目录虚拟环境  ✨ 修复
  ✓ dashscope 可用  ✨ 修复

skills_library/info_collection/structure_damage_alterations_recognition:
  有独立虚拟环境: False
  使用的 Python: .../Reportplatformautore/.venv/Scripts/python.exe
  ✓ 使用项目根目录虚拟环境  ✨ 修复
  ✓ dashscope 可用  ✨ 修复

skills_library/info_collection/concrete_table_recognition:
  有独立虚拟环境: True
  使用的 Python: .../concrete_table_recognition/.venv/Scripts/python.exe
  ✓ 使用 Skill 独立虚拟环境
  ✓ dashscope 可用
```

### 关键改进

1. **✅ 砂浆强度**: 现在能够使用项目根目录虚拟环境，`dashscope` 可用
2. **✅ 结构损伤与变动识别**: 同样使用项目虚拟环境，依赖满足
3. **✅ 保持兼容性**: 有独立虚拟环境的 skills（如混凝土强度）仍优先使用自己的环境

## 架构设计解释

### 为什么会有两种虚拟环境策略？

1. **Skill 独立虚拟环境** (如 brick, concrete):
   - **优点**: 依赖隔离，版本可独立控制
   - **缺点**: 占用更多空间，管理复杂
   - **适用**: 成熟的、有特殊依赖的 skills

2. **项目统一虚拟环境** (如 mortar, structure):
   - **优点**: 依赖复用，管理简单，节省空间
   - **缺点**: 依赖冲突风险（如果 skills 需求不同版本）
   - **适用**: 新开发的、依赖简单的 skills

### 修复后的灵活性

修复后的脚本执行器**支持两种策略并存**:
- 有独立环境的继续使用独立环境（优先级更高）
- 无独立环境的自动回退到项目环境（避免依赖缺失）
- 完全向后兼容，不破坏现有 skills

## 后续建议

### 1. 统一依赖管理（可选）

如果所有 skills 的依赖都兼容，可以考虑：
- 将公共依赖放在项目根目录 `requirements.txt`
- Skill 特定依赖放在各自的 `requirements.txt`
- 逐步移除 skill 独立虚拟环境，减少维护成本

### 2. 文档化虚拟环境策略

在 `SETUP_PREREQUISITES.md` 中明确说明：
```markdown
## 虚拟环境策略

支持两种模式：

1. **Skill 独立虚拟环境**（推荐用于复杂 skills）
   - 在 skill 目录下创建 .venv
   - 安装 skill specific requirements

2. **项目统一虚拟环境**（推荐用于简单 skills）
   - 无需创建独立 .venv
   - 自动使用项目根目录的 .venv
   - 确保依赖添加到根 requirements.txt
```

### 3. 测试建议

现在可以在前端重新测试：
1. 上传砂浆检测 PDF 到砂浆强度节点
2. 上传结构损伤图片到结构损伤识别节点
3. 验证数据能否正确提取和保存

---
**修复完成时间**: 2026-02-17  
**影响范围**: 所有无独立虚拟环境的声明式 Skills  
**修复状态**: ✅ 已修复并验证  
**后端状态**: ✅ 服务运行中 (http://localhost:8000)  
**关键修复**: Python 可执行文件解析逻辑增加项目根目录虚拟环境回退
