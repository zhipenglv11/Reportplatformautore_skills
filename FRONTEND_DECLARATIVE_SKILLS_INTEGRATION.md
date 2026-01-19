# 前端声明式 Skills 集成文档

## ✅ 已完成的工作

### 1. 创建技能选择器组件 (`skill-selector.tsx`)

**功能**：
- 自动加载可用的声明式技能列表
- 显示技能详细信息（描述、版本等）
- 支持技能选择回调
- 显示加载状态和错误处理

**位置**：`src/app/components/skill-selector.tsx`

**使用方式**：
```tsx
<SkillSelector
  selectedSkill={selectedSkill}
  onSkillSelect={(skillName, skillType) => setSelectedSkill(skillName)}
  showOnlyDeclarative={true}
/>
```

### 2. 在文件详情模态框中集成声明式技能

**功能**：
- 在中间面板添加"声明式技能"区域
- 集成技能选择器
- 添加技能执行按钮
- 显示技能执行结果

**位置**：`src/app/components/collection-detail-modal.tsx`

**新增功能**：
- `handleExecuteSkill()` - 执行声明式技能的函数
- 支持混凝土表格识别专用接口 (`/api/skill/concrete-table-recognition`)
- 支持通用执行接口 (`/api/skill/execute`)
- 技能执行结果展示

### 3. API 集成

**已集成的 API 端点**：

1. **列出技能**：`GET /api/skills/list`
   - 获取所有可用的命令式和声明式技能

2. **获取技能信息**：`GET /api/skill/{skill_name}/info`
   - 获取技能的详细信息

3. **执行技能（专用接口）**：`POST /api/skill/concrete-table-recognition`
   - 混凝土表格识别专用接口
   - 支持文件上传（multipart/form-data）

4. **执行技能（通用接口）**：`POST /api/skill/execute`
   - 通用技能执行接口
   - 支持 JSON 格式请求

---

## 📋 使用流程

### 用户操作流程

1. **上传文件**
   - 在数据采集编辑器中双击节点
   - 在文件详情模态框中点击"选择文件"
   - 选择要处理的文件（PDF 或图片）

2. **选择技能**
   - 在"声明式技能"区域
   - 从下拉菜单中选择要使用的技能
   - 查看技能描述和版本信息

3. **执行技能**
   - 点击"执行技能"按钮
   - 等待技能执行完成
   - 查看执行结果

4. **查看结果**
   - 技能执行成功后，结果会显示在技能选择器下方
   - 结果以 JSON 格式展示
   - 可以复制或进一步处理结果

---

## 🎨 UI 界面

### 声明式技能区域

位置：文件详情模态框 → 中间面板 → "声明式技能"区域

**界面元素**：
- 标题：带图标和颜色标识
- 技能选择器：下拉菜单，显示可用技能
- 执行按钮：带加载状态
- 结果展示：成功/失败状态 + JSON 数据

**样式特点**：
- 使用紫色/靛蓝色主题区分于其他功能
- 渐变背景 (`from-indigo-50 to-purple-50`)
- 响应式设计，适配不同屏幕尺寸

---

## 🔧 技术实现

### 状态管理

```typescript
const [selectedSkill, setSelectedSkill] = useState<string>('');
const [isExecutingSkill, setIsExecutingSkill] = useState(false);
const [skillResults, setSkillResults] = useState<Record<string, any>>({});
```

### 技能执行逻辑

1. **混凝土表格识别**（专用接口）
   ```typescript
   const formData = new FormData();
   formData.append('file', selectedFile.file);
   formData.append('format', 'json');
   
   const response = await fetch('/api/skill/concrete-table-recognition', {
     method: 'POST',
     body: formData,
   });
   ```

2. **其他技能**（通用接口）
   ```typescript
   const response = await fetch('/api/skill/execute', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({
       skill_name: selectedSkill,
       user_input: `处理文件: ${selectedFile.name}`,
       use_llm: false,
       use_script: true,
     }),
   });
   ```

### 错误处理

- 网络错误捕获
- API 错误信息提取
- 用户友好的错误提示
- 控制台日志记录

---

## 📝 文件修改清单

### 新增文件

1. `src/app/components/skill-selector.tsx`
   - 技能选择器组件

### 修改文件

1. `src/app/components/collection-detail-modal.tsx`
   - 添加声明式技能相关状态
   - 添加技能执行函数
   - 添加技能选择器 UI
   - 添加结果展示区域
   - 更新 FileItem 接口（添加 `skill_result` 字段）

---

## 🚀 下一步优化建议

### 1. 结果集成到现有流程

当前技能执行结果独立显示，可以考虑：
- 将结果转换为 `preview_chunks` 格式
- 与现有的数据分析流程集成
- 支持结果确认和提交

### 2. 批量处理支持

- 支持选择多个文件批量执行技能
- 显示批量处理进度
- 汇总批量处理结果

### 3. 技能参数配置

- 为不同技能添加参数配置界面
- 支持自定义输出格式（JSON/CSV/Excel）
- 支持自定义输出目录

### 4. 历史记录

- 保存技能执行历史
- 支持查看历史结果
- 支持重新执行历史任务

### 5. 技能结果可视化

- 表格数据可视化展示
- 图表展示（如果适用）
- 导出功能增强

---

## 🐛 已知问题

1. **结果未自动集成到现有流程**
   - 当前技能执行结果独立显示
   - 需要手动处理才能与现有数据分析流程集成

2. **文件状态更新**
   - 技能执行成功后，文件状态更新逻辑需要完善
   - 需要与父组件通信更新文件列表

---

## 📚 相关文档

- [声明式 Skills 使用指南](./HOW_TO_USE_DECLARATIVE_SKILLS.md)
- [后端 API 文档](./backend/API_DOCUMENTATION.md)
- [文件上传测试指南](./TEST_FILE_UPLOAD.md)

---

## ✅ 测试检查清单

- [x] 技能选择器组件创建
- [x] 技能列表加载
- [x] 技能信息显示
- [x] 技能执行功能
- [x] 结果展示
- [x] 错误处理
- [x] 加载状态显示
- [ ] 结果集成到现有流程（待优化）
- [ ] 批量处理（待实现）
- [ ] 参数配置（待实现）

---

**集成完成时间**：2025-01-XX
**版本**：v1.0.0
