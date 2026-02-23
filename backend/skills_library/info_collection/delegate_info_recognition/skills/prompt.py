"""
Prompt templates for Delegate Info Recognition
"""


def get_system_prompt() -> str:
    return """你是一个专业的建筑检测文档信息提取助手。你的任务是从委托单、检测记录或鉴定报告PDF/图片中精确提取关键信息，并输出为结构化JSON格式。请严格按照字段要求提取信息。"""


def get_extraction_prompt() -> str:
    return """请从文档中提取以下信息并输出为 JSON格式：

meta（元数据）:
- control_id: 控制编号（如 KJQR-056-2047）
- record_no: 原始记录编号（格式为No:xxxxx，保留完整格式）
- client_org: 委托单位/委托方
- inspection_reason: 检测原因/委托鉴定事项
- inspection_basis: 检测依据/依据标准
- instrument_id: 仪器编号/设备编号
- inspection_date: 检测日期（规范化为YYYY-MM-DD格式）
- house_name: 房屋名称/建筑名称

house_details（房屋详情）:
- 提取"房屋概况"部分的完整内容，包括但不限于：
  * 房屋位置/地址
  * 建成年份/使用现状
  * 建筑面积
  * 结构类型（如：砌体结构、框架结构等）
  * 楼层数
  * 主要构件材料（如：混凝土楼板、砖墙、砂浆等）
  * 其他重要的房屋信息
- 请将这些信息整合为一段连贯的文字描述

注意事项：
1. 严格按照JSON格式输出，不要添加额外的解释
2. 如果某个字段没有找到对应信息，设置为 null
3. 日期格式统一为 YYYY-MM-DD
4. house_details 应该是完整的段落描述，不是简单的列表

输出示例：
{
  "meta": {
    "control_id": "KJQR-056-2047",
    "record_no": "No:2500063",
    "client_org": "昆山高新技术产业开发区青阳城市管理办事处",
    "inspection_reason": "危险性鉴定",
    "inspection_basis": "JGJ125-2016",
    "instrument_id": "MLG01-01",
    "inspection_date": "2025-02-11",
    "house_name": "建材新村5号楼"
  },
  "house_details": "鉴定对象位于昆山市开发区朝阳路以南、昆塔路以东建材新村小区内，建成后作为住宅楼使用至今。据委托方提供资料，鉴定对象约建于1987年，建筑面积1672㎡，为四层砌体结构，楼、屋面均采用预应力混凝土空心板，现浇混凝土楼梯，竖向承重构件为烧结粘土砖实墙，混合砂浆砌筑。",
  "notes": null
}
"""
