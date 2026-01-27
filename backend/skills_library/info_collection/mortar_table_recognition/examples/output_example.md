# Mortar Strength Extraction - Output Examples
# 砂浆强度检测数据抽取 - 输出示例

## 单个文件提取示例

### JSON 格式

```json
{
  "meta": {
    "table_id": "KJQR-056-206",
    "record_no": "2500108",
    "test_date": "2023-02-26",
    "instrument_model": "SJY-800B"
  },
  "rows": [
    {
      "seq": 1,
      "test_location": "一层墙 19×D-F 轴",
      "converted_strength_mpa": 2.0,
      "estimated_strength_mpa": 1.8
    },
    {
      "seq": 2,
      "test_location": "二层墙 20×D-F 轴",
      "converted_strength_mpa": 2.2,
      "estimated_strength_mpa": 2.0
    },
    {
      "seq": 3,
      "test_location": "三层墙 21×D-F 轴",
      "converted_strength_mpa": null,
      "estimated_strength_mpa": null
    }
  ],
  "notes": "第3行数据因破损无法读取强度值",
  "source_file": "example.pdf",
  "status": "success"
}
```

### CSV 格式

```csv
table_id,record_no,test_date,instrument_model,seq,test_location,converted_strength_mpa,estimated_strength_mpa,notes
KJQR-056-206,2500108,2023-02-26,SJY-800B,1,一层墙 19×D-F 轴,2.0,1.8,
KJQR-056-206,2500108,2023-02-26,SJY-800B,2,二层墙 20×D-F 轴,2.2,2.0,
KJQR-056-206,2500108,2023-02-26,SJY-800B,3,三层墙 21×D-F 轴,,,第3行数据因破损无法读取强度值
```

### Excel 格式示例

| table_id | record_no | test_date | instrument_model | seq | test_location | converted_strength_mpa | estimated_strength_mpa | notes |
|----------|-----------|-----------|------------------|-----|---------------|------------------------|------------------------|-------|
| KJQR-056-206 | 2500108 | 2023-02-26 | SJY-800B | 1 | 一层墙 19×D-F 轴 | 2.0 | 1.8 | |
| KJQR-056-206 | 2500108 | 2023-02-26 | SJY-800B | 2 | 二层墙 20×D-F 轴 | 2.2 | 2.0 | |
| KJQR-056-206 | 2500108 | 2023-02-26 | SJY-800B | 3 | 三层墙 21×D-F 轴 | | | 第3行数据因破损无法读取强度值 |

---

## 批量处理输出示例

```json
{
  "results": [
    {
      "meta": {
        "table_id": "KJQR-056-206",
        "record_no": "2500108",
        "test_date": "2023-02-26",
        "instrument_model": "SJY-800B"
      },
      "rows": [
        {
          "seq": 1,
          "test_location": "一层墙 19×D-F 轴",
          "converted_strength_mpa": 2.0,
          "estimated_strength_mpa": 1.8
        }
      ],
      "source_file": "file1.pdf",
      "status": "success"
    },
    {
      "meta": {
        "table_id": "KJQR-057-207",
        "record_no": "2500109",
        "test_date": "2023-02-27",
        "instrument_model": "SJY-800B"
      },
      "rows": [
        {
          "seq": 1,
          "test_location": "地下室墙 1×A-C 轴",
          "converted_strength_mpa": 3.5,
          "estimated_strength_mpa": 3.2
        }
      ],
      "source_file": "file2.pdf",
      "status": "success"
    }
  ],
  "total": 2
}
```

---

## 错误处理示例

```json
{
  "meta": null,
  "rows": [],
  "source_file": "problematic_file.pdf",
  "status": "error",
  "error": "无法识别表格结构",
  "notes": "图片质量过低，建议重新扫描"
}
```

---

## 特殊情况示例

### 1. 日期无法规范化

```json
{
  "meta": {
    "table_id": "KJQR-056-206",
    "record_no": "2500108",
    "test_date": "2023年2月",
    "instrument_model": null
  },
  "notes": "检测日期缺少具体日期，保留原格式"
}
```

### 2. 序号缺失

```json
{
  "rows": [
    {
      "seq": null,
      "test_location": "一层墙 19×D-F 轴",
      "converted_strength_mpa": 2.0,
      "estimated_strength_mpa": 1.8
    }
  ],
  "notes": "表格无序号列"
}
```

### 3. 空值占位符

```json
{
  "rows": [
    {
      "seq": 1,
      "test_location": "一层墙 19×D-F 轴",
      "converted_strength_mpa": null,
      "estimated_strength_mpa": null
    }
  ],
  "notes": "强度值为占位符'—'，输出为null"
}
```
