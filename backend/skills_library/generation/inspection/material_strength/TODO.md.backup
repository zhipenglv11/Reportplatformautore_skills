# Material Strength Skills - 后续工作清单

生成时间：2026-01-28
当前状态：父子架构已创建，concrete_strength已完整实现

---

## 🎯 工作清单（按优先级）

### ✅ 已完成

- [x] 创建父子skill架构
- [x] 实现父skill编排逻辑（assemble.py）
- [x] 完整实现concrete_strength子skill
  - [x] SKILL.md
  - [x] fields.yaml
  - [x] render.md
  - [x] impl/parse.py
- [x] 创建brick_strength和mortar_strength框架
- [x] Git提交（commit 6088cae）

---

### 🔴 高优先级（核心功能）

#### 1. **更新父skill配置文件**
**当前问题**：fields.yaml和render.md还是v1.0单体架构的配置

**需要做的：**
- [ ] 重写 `fields.yaml` 为父skill版本
  - 只定义控制参数（project_id, node_id, material_order等）
  - 定义子skills注册信息
  - 定义编排策略
- [ ] 重写 `render.md` 为父skill版本
  - 定义段落组装规则
  - 定义总述生成规范（如果需要）
  - 定义过渡句规则

**文件路径：**
- `backend/skills_library/generation/inspection/material_strength/fields.yaml`
- `backend/skills_library/generation/inspection/material_strength/render.md`

---

#### 2. **与declarative_skills系统集成**
**当前问题**：assemble.py是独立的，还没有与现有的SkillLoader和Executor集成

**需要做的：**
- [ ] 检查 `services/declarative_skills/loader.py` 是否支持父子skill
- [ ] 检查 `services/declarative_skills/executor.py` 的调用方式
- [ ] 可能需要在executor中添加对父skill的识别和调用逻辑
- [ ] 更新 `impl/__init__.py` 导出assemble函数

**文件路径：**
- `backend/services/declarative_skills/loader.py`
- `backend/services/declarative_skills/executor.py`
- `backend/skills_library/generation/inspection/material_strength/impl/__init__.py`

---

#### 3. **完善brick_strength子skill**
**当前状态**：只有SKILL.md框架

**需要做的：**
```bash
# 复制concrete_strength作为模板
cd backend/skills_library/generation/inspection/material_strength/subskills/brick_strength

# 创建文件：
- [ ] fields.yaml   # 基于concrete修改，移除carbonation_depth
- [ ] render.md     # 修改描述模板
- [ ] impl/parse.py # 修改查询条件和字段提取逻辑
- [ ] impl/__init__.py
```

**主要修改点：**
- Query条件：`test_item LIKE '%砌体砖%' OR LIKE '%砖强度%'`
- 强度等级格式：`MU\d+` 而不是 `C\d+`
- 移除碳化深度字段
- 规范依据：GB/T 50315-2011、GB 50003-2011

---

#### 4. **完善mortar_strength子skill**
**当前状态**：只有SKILL.md框架

**需要做的：**
```bash
cd backend/skills_library/generation/inspection/material_strength/subskills/mortar_strength

# 创建文件：
- [ ] fields.yaml   # 基于concrete修改
- [ ] render.md     # 修改描述模板  
- [ ] impl/parse.py # 修改查询条件
- [ ] impl/__init__.py
```

**主要修改点：**
- Query条件：`test_item LIKE '%砂浆%'`
- 强度等级格式：`M\d+\.\d+` (如M5.0)
- 移除碳化深度字段
- 规范依据：JGJ/T 70-2009
- 检测单位：测点 而不是 构件

---

### 🟡 中优先级（完善功能）

#### 5. **更新README文档**
**当前问题**：README.md还是v1.0的说明

**需要做的：**
- [ ] 更新架构说明（父子结构图）
- [ ] 更新使用示例（如何调用父skill）
- [ ] 添加子skills说明
- [ ] 添加"如何添加新材料类型"的指南

**文件路径：**
- `backend/skills_library/generation/inspection/material_strength/README.md`

---

#### 6. **编写单元测试**
**需要做的：**
```bash
tests/skills/generation/inspection/material_strength/
├── test_assemble.py           # 测试父skill编排逻辑
├── test_concrete_strength.py  # 测试concrete子skill
├── test_brick_strength.py     # 测试brick子skill
└── test_mortar_strength.py    # 测试mortar子skill
```

**测试场景：**
- [ ] 父skill：有数据时正确调用子skills
- [ ] 父skill：无数据时返回正确的空消息
- [ ] 父skill：部分子skill失败时继续执行
- [ ] 子skill：正确解析数据
- [ ] 子skill：数据验证规则
- [ ] 子skill：生成内容格式正确

---

#### 7. **集成测试**
**需要做的：**
- [ ] 准备测试数据（mock professional_data）
- [ ] 测试端到端流程：info_collection → professional_data → generation
- [ ] 测试与现有API路由的集成
- [ ] 测试证据链追溯

**文件路径：**
- `tests/integration/test_material_strength_flow.py`

---

### 🟢 低优先级（优化增强）

#### 8. **性能优化**
- [ ] assemble.py中的子skill调用改为并行（如果可能）
- [ ] 数据库查询优化（添加索引）
- [ ] 缓存机制（避免重复查询）

#### 9. **错误处理增强**
- [ ] 添加更详细的日志
- [ ] 添加Sentry等错误追踪
- [ ] 友好的错误提示信息

#### 10. **文档完善**
- [ ] 添加API文档（OpenAPI/Swagger）
- [ ] 添加架构图（使用Mermaid或PlantUML）
- [ ] 添加开发者指南

---

## 🚀 推荐的执行顺序

### **第一阶段：让系统能运行起来**（1-2天）
1. 更新父skill的fields.yaml和render.md
2. 与declarative_skills系统集成
3. 更新README文档
4. 推送到远程仓库

### **第二阶段：完善子skills**（2-3天）
5. 完善brick_strength子skill
6. 完善mortar_strength子skill
7. 编写单元测试

### **第三阶段：测试和优化**（1-2天）
8. 集成测试
9. 性能优化
10. 文档完善

---

## 💡 关键注意事项

### **集成时可能遇到的问题：**

1. **SkillLoader识别问题**
   - 现有loader可能不支持父子结构
   - 需要检查如何加载subskills目录

2. **异步调用问题**
   - assemble.py使用了async/await
   - 确保executor也支持异步

3. **数据库连接问题**
   - parse.py直接使用get_engine()
   - 可能需要依赖注入或配置管理

4. **Import路径问题**
   - 子skills的相对导入路径
   - 确保Python路径配置正确

---

## 📝 快速检查清单

在开始下一步之前，确认：

- [ ] 当前分支：feature/generation-skills
- [ ] 最新提交：6088cae
- [ ] 文件结构完整：父skill + 1个完整子skill + 2个框架
- [ ] 备份文件已创建：SKILL.md.v1.backup, parse.py.backup, fields.yaml.v1.backup
- [ ] Git状态干净（或已commit）

---

## 🎯 下一步建议

**如果您想快速验证架构可行性：**
→ 先做第一阶段的工作（系统集成）

**如果您想完整实现所有材料类型：**
→ 先完成brick_strength和mortar_strength

**如果您想让同事review架构：**
→ 先推送到远程，写一份架构说明文档

---

## 📞 需要帮助时

- 父子skill集成问题 → 查看 `services/declarative_skills/`
- 子skill复制问题 → 使用concrete_strength作为模板
- 测试编写问题 → 参考现有的test文件结构
- 数据库查询问题 → 查看 `models/db.py`

---

**文档版本**：v1.0
**创建者**：GitHub Copilot
**更新时间**：2026-01-28
