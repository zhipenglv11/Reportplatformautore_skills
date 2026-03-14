# 数据提取逻辑说明

## 📋 概述

本文档详细说明如何从数据库的 `test_value_json` 和 `raw_result` 字段中提取第三章所需的两个表格数据。

## 🗄️ 数据源

### 数据库表：`professional_data`

相关字段：
- `test_item`: 测试项目名称（如"砖强度"、"砂浆强度"）
- `raw_result`: TEXT，存储 JSON 格式的原始结果
- `confirmed_result`: TEXT，存储 JSON 格式的确认结果（优先使用）
- `record_code`: 记录编号
- `test_value_json`: TEXT，存储 JSON 格式的测试值

## 📊 表格1：主要检测仪器设备

### 需要提取的字段

| 目标字段 | 数据来源路径 | 说明 |
|---------|------------|------|
| 仪器名称 | 推断：根据 `test_item` | 见仪器类型映射表 |
| 规格型号 | `raw_result.meta.instrument_model` 或 `raw_result.instrument_model` | 如 "SJY-800B" |
| 编号 | `raw_result.meta.instrument_id` 或 `raw_result.instrument_id` | 如 "MLG01-01" |
| 有效截止日期 | 暂无（需要单独的仪器配置表） | 如 "2026-1-12" |

### 仪器类型映射表

```python
INSTRUMENT_TYPE_MAPPING = {
    "砖强度": {
        "name": "测砖回弹仪",
        "default_model": "ZC4"
    },
    "砂浆强度": {
        "name": "贯入式砂浆强度检测仪",
        "default_model": "SJY-800B"
    },
    "混凝土": {
        "name": "回弹仪",
        "default_model": "HT-225"
    },
    "钢筋": {
        "name": "钢筋扫描仪",
        "default_model": "PROFOMETER-6"
    },
    "倾斜": {
        "name": "手持式激光测距仪",
        "default_model": "GLM40"
    }
}
```

### 提取逻辑

1. **查询数据库**
   ```sql
   SELECT test_item, raw_result, confirmed_result
   FROM professional_data
   WHERE project_id = ? AND node_id = ?
   ```

2. **解析 JSON 字段**
   ```python
   data = confirmed_result or raw_result
   meta = data.get('meta', {})
   ```

3. **推断仪器类型**
   - 根据 `test_item` 中的关键词匹配（如"砖强度"→"测砖回弹仪"）

4. **提取具体信息**
   ```python
   model = meta.get('instrument_model') or data.get('instrument_model')
   serial_number = meta.get('instrument_id') or data.get('instrument_id')
   ```

5. **去重**
   - 使用 `(仪器名称, 规格型号, 编号)` 作为唯一键
   - 保留最早出现的记录

### 示例数据结构

#### raw_result 示例（砂浆强度）
```json
{
  "meta": {
    "table_id": "KJQR-056-206",
    "record_no": "2500108",
    "test_date": "2023-02-26",
    "instrument_model": "SJY-800B"
  },
  "rows": [...]
}
```

#### 提取结果
```python
{
  "instrument_name": "贯入式砂浆强度检测仪",
  "model": "SJY-800B",
  "serial_number": "",  # 该记录未提供
  "valid_until": None
}
```

## 📋 表格2：原始记录一览表

### 需要提取的字段

| 目标字段 | 数据来源路径 | 说明 |
|---------|------------|------|
| 原始记录名称 | 推断：根据 `control_id` 或 `test_item` | 见记录名称映射表 |
| 内部编号 | `raw_result.meta.record_no` 或 `record_code` | 格式：NO:2500063 |

### 记录名称映射表

```python
RECORD_NAME_MAPPING = {
    # 通过控制编号匹配
    "KJQR-056-2047": "结构布置检查原始记录",
    "KJQR-056-2048": "结构构件拆改检查原始记录",
    "KJQR-056-206": "贯入法检测砂浆强度原始记录",
    "KJQR-056-223": "砖回弹原始记录",
    "KJQR-056-215": "混凝土回弹检测原始记录",
    
    # 通过关键词匹配
    "砂浆": "贯入法检测砂浆强度原始记录",
    "砖": "砖回弹原始记录",
    "混凝土": "混凝土回弹检测原始记录",
    "倾斜": "倾斜测量检测原始记录",
    "PKPM": "PKPM计算原始记录",
    "拆改": "结构构件拆改检查原始记录",
    "布置": "结构布置检查原始记录"
}
```

### 提取逻辑

1. **查询数据库**
   ```sql
   SELECT test_item, raw_result, confirmed_result, record_code
   FROM professional_data
   WHERE project_id = ? AND node_id = ?
   ```

2. **提取记录编号**
   ```python
   data = confirmed_result or raw_result
   meta = data.get('meta', {})
   
   record_no = (
       meta.get('record_no') or
       data.get('record_no') or
       record_code
   )
   
   # 格式化：NO:2500063
   if not record_no.startswith('NO:'):
       record_no = f"NO:{record_no}"
   ```

3. **推断记录名称**
   - 优先通过 `control_id` 匹配
   - 其次通过 `test_item` 关键词匹配

4. **合并连续编号**
   - NO:2500108 + NO:2500109 → NO:2500108~2500109
   - 按记录名称分组
   - 查找连续的数字区间

### 示例数据结构

#### raw_result 示例
```json
{
  "meta": {
    "control_id": "KJQR-056-206",
    "record_no": "2500108",
    "test_date": "2023-02-26"
  },
  "rows": [...]
}
```

#### 提取结果（合并前）
```python
[
  {"record_name": "贯入法检测砂浆强度原始记录", "internal_number": "NO:2500108"},
  {"record_name": "贯入法检测砂浆强度原始记录", "internal_number": "NO:2500109"}
]
```

#### 提取结果（合并后）
```python
[
  {"record_name": "贯入法检测砂浆强度原始记录", "internal_number": "NO:2500108~2500109"}
]
```

## 🔄 使用方式

### Python API

```python
from impl.extract_utils import extract_instruments_from_db, extract_records_from_db

# 提取仪器设备
instruments = extract_instruments_from_db(project_id="proj-xxx", node_id="node-xxx")

# 提取原始记录
records = extract_records_from_db(project_id="proj-xxx", node_id="node-xxx")
```

### 生成章节时使用

```python
from impl import generate_inspection_content_and_methods

result = generate_inspection_content_and_methods(
    project_id="proj-xxx",
    node_id="node-xxx",
    context={
        "use_dynamic_data": True  # 启用动态数据提取
    }
)
```

## 🎯 数据质量保证

### 1. 优先级策略
- `confirmed_result` > `raw_result`
- `meta.*` > 顶层字段

### 2. 容错处理
- 如果动态提取失败，回退到默认静态数据
- JSON 解析错误时返回空字典
- 缺失字段时使用默认值或空字符串

### 3. 去重策略
- 仪器设备：按 `(名称, 型号, 编号)` 去重
- 原始记录：按 `internal_number` 去重后合并

### 4. 日志记录
```python
logger.info(f"成功从项目 {project_id} 提取到 {len(instruments)} 个仪器设备")
logger.warning(f"项目 {project_id} 未提取到数据，使用默认数据")
logger.error(f"动态提取失败: {e}，使用默认数据")
```

## 📝 扩展建议

### 1. 添加仪器配置表
创建独立的 `instruments` 表存储：
- 仪器名称、型号、编号
- 有效期、校准信息
- 使用历史记录

### 2. 智能推断增强
- 根据检测方法推断仪器（如"回弹法"→"回弹仪"）
- 从 PDF 文件名或上传记录中提取信息

### 3. 记录关联
- 建立 `professional_data` 与实际文件的关联
- 自动生成记录清单的完整性检查

## 🐛 故障排查

### 问题：提取不到仪器信息
**检查项**：
1. `test_item` 是否包含关键词？
2. `raw_result.meta.instrument_model` 是否存在？
3. JSON 格式是否正确？

### 问题：记录编号格式错误
**检查项**：
1. `record_no` 字段是否存在？
2. 编号格式是否为 "No:xxx" 或纯数字？
3. 是否需要添加格式化规则？

### 问题：连续编号合并不正确
**检查项**：
1. 编号是否为连续数字？
2. 记录名称是否完全一致？
3. 是否包含非数字编号？
