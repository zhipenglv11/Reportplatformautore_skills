# Material Strength Skills - 后续工作

**当前状态**：父子架构已创建，concrete_strength 完整实现  
**最后更新**：2026-01-28  
**Git分支**：feature/generation-skills

---

## ✅ 已完成

- [x] 创建父子skill架构
- [x] 实现父skill编排逻辑（assemble.py）
- [x] 完整实现concrete_strength子skill
  - [x] SKILL.md, fields.yaml, render.md, impl/parse.py
- [x] 创建brick_strength和mortar_strength框架
- [x] Git提交（commit 6088cae, c1708bb）

---

## 🔴 高优先级（本周必做）

### 1. 推送到远程仓库
```bash
git push origin feature/generation-skills
```

### 2. 更新父skill配置文件
- [ ] 更新 `fields.yaml` → 父skill版本（控制参数、子skills注册）
- [ ] 更新 `render.md` → 段落组装规则
- [ ] 更新 `impl/__init__.py` → 导出 assemble_material_strength

### 3. 系统集成检查
- [ ] 检查 `services/declarative_skills/loader.py` 是否支持父子结构
- [ ] 检查 `services/declarative_skills/executor.py` 的调用方式
- [ ] 确认如何调用父skill的 assemble 函数

### 4. 完善brick_strength子skill
```bash
# 复制concrete_strength作为模板
cd subskills/brick_strength/
# 创建：fields.yaml, render.md, impl/parse.py
```
**关键修改点**：
- Query: `test_item LIKE '%砌体砖%'`
- 强度等级: `MU\d+`（而非 C\d+）
- 移除碳化深度字段
- 规范: GB/T 50315-2011

### 5. 完善mortar_strength子skill
```bash
cd subskills/mortar_strength/
# 创建：fields.yaml, render.md, impl/parse.py
```
**关键修改点**：
- Query: `test_item LIKE '%砂浆%'`
- 强度等级: `M\d+\.\d+`（如M5.0）
- 规范: JGJ/T 70-2009

---

## 🟡 中优先级（下周）

### 6. 编写测试
```
tests/skills/generation/material_strength/
├── test_assemble.py           # 父skill编排逻辑
├── test_concrete_strength.py  # concrete子skill
├── test_brick_strength.py
└── test_mortar_strength.py
```

### 7. 更新README文档
- [ ] 更新架构说明（父子结构图）
- [ ] 添加使用示例
- [ ] 添加"如何添加新材料"指南

---

## 🟢 低优先级（后续）

### 8. 集成测试
- [ ] 端到端测试：info_collection → generation
- [ ] 与API路由集成测试

### 9. 性能优化
- [ ] 子skill并行调用（如果可能）
- [ ] 数据库查询优化

### 10. 文档完善
- [ ] API文档
- [ ] 架构图（Mermaid）

---

## 📁 关键文件位置

```
material_strength/
├── SKILL.md                    ✅ v2.0 已更新
├── fields.yaml                 ❌ 待更新
├── render.md                   ❌ 待更新  
├── README.md                   ⚠️  待更新
├── impl/
│   ├── assemble.py            ✅ 已实现
│   └── __init__.py            ❌ 待更新
└── subskills/
    ├── concrete_strength/     ✅ 完整实现
    ├── brick_strength/        ❌ 仅框架
    └── mortar_strength/       ❌ 仅框架
```

---

## 🔍 系统集成点

**需要检查的文件**：
- `backend/services/declarative_skills/loader.py` - skill加载器
- `backend/services/declarative_skills/executor.py` - skill执行器
- `backend/api/skill_orchestrator_routes.py` - API路由

**关键问题**：
1. loader是否支持扫描 subskills/ 子目录？
2. executor是否支持 async 函数调用？
3. 如何传递 project_id 和 node_id？

---

## 💡 快速测试代码

```python
# test_material_strength_demo.py
import asyncio
from backend.skills_library.generation.inspection.material_strength.impl.assemble import (
    assemble_material_strength
)

async def test():
    result = await assemble_material_strength(
        project_id="test-001",
        node_id="node-001"
    )
    print("✅ Success:", result.get("has_data"))
    return result

asyncio.run(test())
```

---

## 📞 遇到问题时

- **父子skill集成** → 查看 services/declarative_skills/
- **复制子skill** → 使用 concrete_strength 作为模板
- **数据库查询** → 参考 models/db.py
- **测试编写** → 参考现有 tests/ 目录结构

---

**下一步建议**：先推送到远程，再逐步完成高优先级任务。
