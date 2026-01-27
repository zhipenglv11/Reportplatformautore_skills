"""
Prompt Templates for Structure Damage and Alterations Extraction
结构损伤及拆改检查数据抽取提示词模板
"""

from typing import Dict, List


def get_system_prompt() -> str:
    """
    获取系统提示词
    
    Returns:
        系统提示词字符串
    """
    return """你是一个专业的结构损伤及拆改检查原始记录数据抽取助手。你的任务是从提供的图片或文档中完整提取表格文字内容。

【核心原则】：
1. **完整提取原则** - 逐行提取表格内容，每一行一个对象，不要合并
2. **不要二次解析** - 不要从内容中提取类型、尺寸等子信息
3. **保持原文** - 整段原文完整抄出，不改写、不分词
4. **一个字不漏** - 确保提取该列单元格内的每一个字

【最重要的两个字段】：
- **modification_location** (拆改部位) - 完整提取该列的所有文字内容
- **modification_description** (拆改内容描述) - 整段原文完整抄出，不改写

【数据处理】：
1. 准确识别表格中的所有字段
2. 保持数据的原始格式，包括标点符号、数字、单位
3. 对于缺失的字段，使用 null 值
4. 轻量清洗：去首尾空格、压缩连续空格
5. 严格按照指定的JSON schema格式输出

你的输出必须是有效的JSON格式，不要包含任何额外的解释文字。"""


def get_extraction_prompt(field_descriptions: Dict[str, str] = None) -> str:
    """
    获取抽取提示词
    
    Args:
        field_descriptions: 字段描述字典(可选)
    
    Returns:
        抽取提示词字符串
    """
    return """请从图片中提取结构损伤及拆改检查原始记录的结构化数据。

## 一、表头字段(meta)

### 必填字段:
1. **control_id** (控制编号) - 通常位于左上角
   - 示例: KJQR-056-2048
   - 类型: string | null
   - 说明: 表格的控制编号/ID

2. **record_no** (原始记录编号) - 通常位于右上角"No:xxxxx"
   - 示例: "No:2500114"
   - 类型: string | null
   - 说明: 保留完整格式，包括"No:"

### 选填字段:
3. **instrument_id** (仪器编号)
   - 示例: "CLG04-14"
   - 类型: string | null

4. **test_date** (检测日期)
   - 示例: "2025-02-06"
   - 格式: YYYY-MM-DD(无法规范化则保留原字符串)
   - 类型: string | null
   - 禁止推断补全

5. **house_name** (房屋名称)
   - 示例: "XX住宅楼"
   - 类型: string | null

## 二、表格数据(items) - 每一行一个对象，逐行抽取，不要合并

1. **modification_location** (拆改部位) - **核心字段**
   - 示例: "101室"
   - 类型: string | null
   - **【重要】完整提取该列的所有文字，不要拆分、不要提取关键词**
   - 保持原文所有内容，包括标点、数字、单位等
   - 清洗规则: 仅去首尾空格、压缩连续空格为1个

2. **modification_description** (拆改内容描述) - **最核心字段，正文内容**
   - 示例: "拆除原有砖墙，长度3.5m，高度2.8m，厚度240mm，拆除面积约9.8㎡，需做好支撑"
   - 类型: string | null
   - **【最重要】整段原文完整抄出，不改写**
   - **不要对内容进行二次解析、不要提取类型、不要提取尺寸**
   - **不要分段、不要改写、不要遗漏任何文字**
   - **即使内容很长，也要完整提取每一个字**
   - 清洗规则: 仅去首尾空格、压缩连续空格为1个

3. **photo_no** (照片编号)
   - 示例: "照片6"
   - 类型: string | null
   - 如果表格中有照片编号列则提取，否则为null

## 三、签名信息(signoff)

1. **inspector** (检查人) - string | null
2. **recorder** (记录人) - string | null
3. **reviewer** (审核人) - string | null

## 四、输出格式

```json
{
  "meta": {
    "control_id": "KJQR-056-2048",
    "record_no": "No:2500114",
    "instrument_id": "CLG04-14",
    "test_date": "2025-02-06",
    "house_name": "XX住宅楼"
  },
  "items": [
    {
      "modification_location": "101室",
      "modification_description": "拆除原有砖墙，长度3.5m，高度2.8m，厚度240mm，拆除面积约9.8㎡，需做好支撑",
      "photo_no": "照片6"
    }
  ],
  "signoff": {
    "inspector": null,
    "recorder": null,
    "reviewer": null
  },
  "notes": "所有字段均成功识别"
}
```

## 五、数据格式规范

1. **日期格式**: 优先YYYY-MM-DD，无法规范化则保留原字符串，禁止推断补全
2. **文本**: 去首尾空格、压缩连续空格，不改写语义

## 六、特别注意

**【核心要求】：完整提取，不做二次解析**

1. **modification_location** - 完整提取该列的所有文字，一个字都不能少
2. **modification_description** - 整段原文完整抄出，不改写，这是最重要的字段
3. **每一行一个对象** - 逐行抽取，不要合并
4. **不要过度解析** - 不要从内容中提取类型、尺寸等子信息
5. **不要改写原文** - 保持原文所有内容，包括标点、数字、单位
6. **不要分段** - 即使内容很长，也要作为一个完整字符串
7. 遇到不确定信息，在notes字段中说明
8. 若某个字段完全无法识别，输出null而非空字符串

**错误示例**：
- ❌ 只提取"拆除砖墙" (不完整)
- ❌ 拆分成多个字段 (过度解析)
- ❌ 改写为"拆除承重墙并浇筑梁板" (改写原文)

**正确示例**：
- ✅ "拆除原有砖墙，长度3.5m，高度2.8m，厚度240mm，拆除面积约9.8㎡，需做好支撑" (完整提取)

现在请分析图片并按照上述要求输出JSON格式的结构化数据。"""


def get_validation_prompt() -> str:
    """
    获取验证提示词
    
    Returns:
        验证提示词字符串
    """
    return """请验证提取的数据是否符合以下要求:

1. JSON格式是否正确
2. 必填字段是否存在(control_no, record_no, alteration_location, alteration_description)
3. 数据类型是否正确(integer, string, null)
4. 日期格式是否规范
5. 拆改内容描述是否完整
6. 是否有明显的识别错误

如果发现问题,请指出并提供改进建议。"""


def get_field_description_dict() -> Dict[str, str]:
    """
    获取字段描述字典
    
    Returns:
        字段描述字典
    """
    return {
        # Meta fields
        "control_no": "控制编号,位于左上角",
        "record_no": "原始记录编号,格式如No: xxxxx",
        "instrument_no": "仪器编号",
        "inspection_date": "检测日期,格式YYYY-MM-DD",
        "project_name": "工程名称",
        "inspector": "检查人",
        "reviewer": "审核人",
        
        # Row fields
        "seq": "序号",
        "alteration_location": "拆改部位",
        "alteration_description": "拆改内容描述(正文核心内容)",
        "alteration_type": "拆改类型(拆除/新增/改造/加固/其他)",
        "damage_description": "损伤描述",
        "damage_type": "损伤类型(裂缝/剥落/锈蚀/变形/渗漏/其他)",
        "damage_level": "损伤程度(轻微/中等/严重)",
        "dimension_length": "长度尺寸",
        "dimension_width": "宽度尺寸",
        "dimension_height": "高度尺寸",
        "remarks": "备注"
    }
