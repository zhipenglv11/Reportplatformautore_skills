"""
Prompt Templates for Mortar Strength Extraction
砂浆强度检测数据抽取提示词模板
"""

from typing import Dict, List


def get_system_prompt() -> str:
    """
    Get the system prompt for mortar strength extraction.
    
    Returns:
        System prompt string
    """
    return """你是一个专业的砂浆强度检测报告数据抽取助手。你的任务是从提供的图片或文档中准确提取砂浆强度检测相关的结构化数据。

请遵循以下原则:
1. 准确识别表格中的所有字段
2. 保持数据的原始格式和精度
3. 对于缺失的字段,使用 null 值
4. 如遇到模糊或不确定的信息,在notes字段中说明
5. 确保数值类型的正确性(整数、浮点数、日期等)
6. 严格按照指定的JSON schema格式输出

你的输出必须是有效的JSON格式,不要包含任何额外的解释文字。"""


def get_extraction_prompt(field_descriptions: Dict[str, str]) -> str:
    """
    Get the extraction prompt with field descriptions.
    
    Args:
        field_descriptions: Dictionary of field names to descriptions
        
    Returns:
        Extraction prompt string
    """
    return """请从图片中提取砂浆强度检测表格的结构化数据。

## 一、表头字段（meta）

1. **table_id** (控制编号/表格ID) - 位于左上角
   - 示例: KJQR-056-206
   - 类型: string

2. **record_no** (原始记录编号) - 位于右上角 "No: xxxxx"
   - 示例: 2500108
   - 类型: string

3. **test_date** (检测日期)
   - 示例: 2023-02-26
   - 格式: YYYY-MM-DD（无法规范化则保留原字符串）
   - 禁止推断补全
   - 类型: string

4. **instrument_model** (仪器型号)
   - 示例: SJY-800B
   - 类型: string | null

## 二、表格数据行（rows）

每一行数据包含以下字段:

1. **seq** (序号)
   - 表格序号列
   - 类型: integer | null
   - 识别不到允许 null，不自动补号/重排

2. **test_location** (检测部位) - **第一列**
   - 示例: 一层墙 19×D-F 轴
   - 清洗规则: 去首尾空格、压缩连续空格为1个
   - 不改写语义，不拆分楼层/轴线字段
   - 类型: string

3. **converted_strength_mpa** (砂浆抗压强度换算值) - **倒数第二列**
   - 示例: 2.0
   - 单位: MPa
   - **按原记录数值保留位数，不改变精度**
   - 若为空、为"—"或"//"等占位符，输出 null
   - 类型: number | null

4. **estimated_strength_mpa** (单个构件强度推定值) - **倒数第一列**
   - 示例: 1.8
   - 单位: MPa
   - **按原记录数值保留位数，不改变精度**
   - 若为空、为"—"或"//"等占位符，输出 null
   - 类型: number | null

## 三、输出格式

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
    }
  ],
  "notes": "任何不确定或需要说明的情况"
}
```

## 四、重要提醒

1. **列位置识别**: 检测部位=第一列、换算值=倒数第二列、推定值=倒数第一列（以列语义为准，不是固定列序号）
2. **数值格式**: 保留1位小数，空值/占位符输出 null
3. **日期格式**: 优先YYYY-MM-DD，无法规范化保留原样
4. **文本清洗**: 轻量清洗，不改变原意
5. **序号处理**: 识别不到允许 null，禁止自动补全

现在请开始提取数据。"""


def get_validation_prompt(extracted_data: Dict) -> str:
    """
    Get prompt for validating extracted data.
    
    Args:
        extracted_data: The extracted data to validate
        
    Returns:
        Validation prompt string
    """
    return f"""请验证以下提取的砂浆强度检测数据是否准确和完整:

{extracted_data}

检查要点:
1. 所有必填字段是否已提取
2. 数值是否在合理范围内
3. 日期格式是否正确
4. 是否有明显的识别错误
5. 单位是否正确

如果发现问题,请指出具体错误并提供修正建议。
如果数据正确,回复"验证通过"。"""


def get_few_shot_examples() -> List[Dict[str, str]]:
    """
    Get few-shot examples for better extraction.
    TODO: 用户提供实际样本后添加示例
    
    Returns:
        List of example input-output pairs
    """
    return [
        {
            "description": "示例1: 待添加实际样本",
            "input": "图片描述...",
            "output": "{...}"
        }
    ]
