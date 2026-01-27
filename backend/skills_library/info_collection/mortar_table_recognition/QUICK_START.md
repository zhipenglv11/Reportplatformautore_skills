# 砂浆强度信息抽取 Skills - 快速配置指南

## ✅ 已完成的框架结构

恭喜!砂浆强度信息抽取的 Claude Code Skill 框架已经搭建完成。

### 📁 项目结构概览

```
mortar_table_recognition/
├── skills/              ✅ 核心技能模块(已创建)
│   ├── extractor.py    ✅ 数据抽取器
│   ├── schema.py       ⚠️  数据模式(需要更新字段)
│   ├── prompt.py       ✅ 提示词模板
│   └── utils.py        ✅ 工具函数
├── scripts/            ✅ 脚本工具(已创建)
│   ├── config.py       ✅ 配置管理
│   ├── qwen_client.py  ✅ 通义千问客户端
│   ├── pdf_processor.py ✅ PDF处理
│   ├── formatter.py    ✅ 数据格式化
│   ├── batch_process.py ✅ 批量处理
│   └── run.py          ✅ 主运行脚本
├── references/         ⚠️  参考文档(需要填充)
│   ├── fields.md       ⚠️  字段定义(待用户提供)
│   ├── table_schemas.md ⚠️ 表格模式(待用户提供)
│   └── table_types.md  ⚠️  表格类型(待用户提供)
├── examples/           ⚠️  示例(待用户提供后更新)
├── data/               ✅ 数据目录(已创建)
├── parse.py            ✅ 主入口文件
├── skill.json          ✅ Skill配置
├── fields.yaml         ⚠️  字段配置(待用户提供)
├── requirements.txt    ✅ 依赖包列表
├── .env.example        ✅ 环境变量示例
└── README.md           ✅ 项目说明
```

## 🎯 下一步:配置字段信息

### 步骤 1: 提供字段列表

请提供您需要从砂浆强度检测报告中抽取的字段。例如:

```yaml
# 示例字段列表(请根据实际需求提供)
fields:
  - name: report_number
    chinese_name: 报告编号
    type: string
    required: true
    description: 检测报告的唯一编号
    
  - name: test_date
    chinese_name: 检测日期
    type: date
    required: true
    description: 进行强度检测的日期
    
  - name: sample_id
    chinese_name: 样品编号
    type: string
    required: true
    description: 砂浆样品的编号
    
  - name: strength_value
    chinese_name: 强度值
    type: number
    required: true
    description: 测得的抗压强度值
    unit: MPa
    
  # ... 更多字段
```

### 步骤 2: 需要更新的文件

提供字段后,我将帮您更新以下文件:

1. **fields.yaml** - 字段配置文件
2. **skills/schema.py** - 数据模式定义
3. **references/fields.md** - 字段文档
4. **skills/prompt.py** - 提示词(根据字段生成)
5. **examples/** - 示例输出

## 📋 字段信息收集表

请提供以下信息:

### 基本字段信息

| 字段名 | 中文名 | 类型 | 必填 | 说明 | 示例值 |
|--------|--------|------|------|------|--------|
| ?      | ?      | ?    | ?    | ?    | ?      |

### 字段类型说明

- **string**: 文本字段
- **number**: 数值字段(整数或小数)
- **date**: 日期字段
- **boolean**: 是/否字段
- **array**: 列表字段(如多个测试值)

## 🔍 常见砂浆检测字段参考

以下是一些常见的砂浆强度检测字段供参考:

### 报告信息
- 报告编号
- 检测日期
- 报告日期
- 检测单位
- 委托单位
- 工程名称

### 样品信息
- 样品编号
- 样品名称
- 规格尺寸
- 强度等级
- 龄期

### 检测数据
- 抗压强度值
- 试件尺寸
- 破坏荷载
- 单个试块强度
- 平均强度
- 标准差

### 结论
- 检测结果
- 是否合格
- 备注说明

## 💡 使用建议

1. **优先抽取核心字段**: 先定义最重要的字段
2. **考虑数据一致性**: 确保字段定义清晰,避免歧义
3. **预留扩展空间**: 可以先定义主要字段,后续再补充
4. **提供示例**: 如果有样本图片或PDF,将极大帮助优化抽取效果

## 🚀 配置完成后

配置好字段后,您就可以:

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **配置API Key**
   ```bash
   cp env.example .env
   # 编辑 .env 文件,填入API Key
   ```

3. **运行测试**
   ```bash
   python parse.py your_test_file.pdf
   ```

## 📞 下一步行动

**请提供您需要抽取的字段列表**,包括:
- 字段名称(英文/中文)
- 字段类型
- 是否必填
- 字段说明
- 示例值

提供字段后,我将立即帮您完成配置!

---

**当前状态**: ✅ 框架已完成 | ⏳ 等待字段定义
