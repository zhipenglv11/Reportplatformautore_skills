"""
千问API客户端
使用OpenAI兼容接口调用千问视觉模型
"""

import base64
import json
import sys
import io
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from openai import OpenAI
except ImportError:
    print("需要安装 openai 库: pip install openai")
    sys.exit(1)

from scripts.config import QWEN_API_KEY, QWEN_MODEL

# Windows控制台编码修复
if sys.platform == "win32" and hasattr(sys.stdout, "buffer"):
    try:
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace"
        )
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer, encoding="utf-8", errors="replace"
        )
    except (ValueError, AttributeError):
        pass


def get_client() -> OpenAI:
    """获取OpenAI客户端（百炼兼容模式）"""
    return OpenAI(
        api_key=QWEN_API_KEY,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )


def classify_table_type(image_path: Path) -> Dict[str, Any]:
    """
    使用千问API快速分类表格类型

    Args:
        image_path: 图片文件路径

    Returns:
        包含表格类型信息的字典
    """
    if not QWEN_API_KEY:
        raise ValueError("未配置QWEN_API_KEY，请在.env文件中设置")

    # 读取图片并编码为base64
    with open(image_path, "rb") as f:
        image_data = f.read()
        image_base64 = base64.b64encode(image_data).decode("utf-8")

    # 构建分类prompt
    prompt = """请查看这张图片，判断这是哪种混凝土表格类型。

判断标准（按优先级）：
1. 优先检查左上角"控制标号"字段：
   - 如果控制标号为 "KJQR-056-215"，则判断为「混凝土回弹检测记录表」
   - 如果控制标号为 "KSQR-4.13-XC-10"，则判断为「混凝土强度检测表格」

2. 如果无控制标号或控制标号不是上述值，则检查其他特征：
   - 如果表格中包含「构件检测」「现场结构检测」「回弹法」「构件检测原始记录」「结构检测」等关键词
   - 并且出现字段「检测部位」「混凝土品种」「检测方法」「强度等级」「施工日期」
   - 则判断为「混凝土回弹检测记录表」
   - 如果出现网格结构的回弹值矩阵和「推定值 MPa」「平均值 MPa」「标准差」等统计项
   - 则判断为「混凝土强度检测表格」

只需返回表格类型名称（「混凝土回弹检测记录表」或「混凝土强度检测表格」），不需要解析表格内容。"""

    try:
        client = get_client()
        response = client.chat.completions.create(
            model=QWEN_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}"
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
            max_tokens=100,
        )

        # 处理不同的响应格式
        content = response.choices[0].message.content
        if isinstance(content, str):
            result_text = content
        elif isinstance(content, list) and len(content) > 0:
            # 如果content是列表，取第一个元素的text字段
            first_item = content[0]
            if isinstance(first_item, dict):
                result_text = first_item.get("text", str(first_item))
            else:
                result_text = str(first_item)
        elif isinstance(content, dict):
            result_text = content.get("text", str(content))
        else:
            result_text = str(content)
        
        return {
            "success": True,
            "type": result_text.strip(),
            "raw_response": result_text,
        }

    except Exception as e:
        return {"success": False, "error": f"分类失败: {str(e)}"}


def extract_table_data(
    image_path: Path, table_type: str, schema: Dict[str, Any]
) -> Dict[str, Any]:
    """
    使用千问API提取表格数据

    Args:
        image_path: 图片文件路径
        table_type: 表格类型
        schema: 表格数据结构的JSON Schema

    Returns:
        包含提取数据的字典
    """
    if not QWEN_API_KEY:
        raise ValueError("未配置QWEN_API_KEY，请在.env文件中设置")

    # 根据表格类型构建不同的提取prompt
    if "混凝土回弹检测记录表" in table_type or "concrete_strength_sheet" in table_type:
        prompt = """请从以下图像中提取以下字段信息，并输出为标准 JSON 格式：

- 检测日期：表格右上角「检测日期」字段
- 检测原因：表格中部靠右的「检测原因」字段
- 检测方法：表格中部靠右的「检测方法」字段（如：回弹法）
- 检测部位：从「工程名称」或「检测部位」字段提取
- 混凝土品种：表格右上方的「混凝土品种」字段（如：泵送混凝土）
- 强度等级：表格右下区域每行「强度等级」字段，统一提取为主等级（如 C30）
- 施工日期列表：提取所有明细行中的「施工日期」，去重后输出为字符串数组（如：["2021"]）

说明：
- 若字段缺失或无法读取，请设置为 null
- 输出内容应尽量保持与表格原始内容一致
- 输出必须是有效的 JSON 格式，不要添加任何额外的解释文字

输出格式示例：
{
  "检测日期": "2024-10-10",
  "检测原因": "委托检测",
  "检测方法": "回弹法",
  "检测部位": "2#楼柱梁板楼面",
  "混凝土品种": "泵送混凝土",
  "强度等级": "C30",
  "施工日期列表": ["2021"]
}"""
    elif "混凝土强度检测表格" in table_type or "concrete_strength_grid" in table_type:
        prompt = """请从以下混凝土强度检测表格中提取以下字段，并以标准 JSON 格式返回：

- 控制标号：表格左上角控制编号（如：KSQR-4.13-XC-10）
- 设计强度等级：混凝土设计强度等级（如：C30）
- 检测部位：混凝土构件位置描述（如：一层柱3/1/B）
- 混凝土品种：混凝土类型（如：泵送混凝土）
- 检测日期：表格右上区域（如：2024-10-14）
- 施工日期：表格右上区域（如：2021-01-01）
- 碳化深度（mm）：表格中「碳化深度」列的「计算」值，数值类型（如：6.00）
- 测区强度最小值（MPa）：表格底部字段，数值类型（如：33.7）
- 测区强度平均值（MPa）：表格底部字段，数值类型（如：35.7）
- 测区强度标准差（MPa）：表格底部字段，数值类型（如：1.19）
- 混凝土强度推定值（MPa）：最终计算结果，数值类型（如：33.7）

说明：
- 控制标号位于表格左上角
- 碳化深度：提取表格中「碳化深度(mm)」列的「计算」值（不是测值）
- 输出字段顺序固定，如未提取到设为 null
- 数值字段（MPa、mm）应为数字类型，不要带单位
- 输出必须是有效的 JSON 格式，不要添加任何额外的解释文字

输出格式示例：
{
  "控制标号": "KSQR-4.13-XC-10",
  "设计强度等级": "C30",
  "检测部位": "一层柱3/1/B",
  "混凝土品种": "泵送混凝土",
  "检测日期": "2024-10-14",
  "施工日期": "2021-01-01",
  "碳化深度（mm）": 6.00,
  "测区强度最小值（MPa）": 33.7,
  "测区强度平均值（MPa）": 35.7,
  "测区强度标准差（MPa）": 1.19,
  "混凝土强度推定值（MPa）": 33.7
}"""
    else:
        # 其他表格类型使用通用prompt
        schema_str = json.dumps(schema, ensure_ascii=False, indent=2)
        prompt = f"""请仔细分析这张{table_type}图片，提取所有表格数据。

要求：
1. 识别表格的行列结构
2. 提取所有字段值
3. 按照以下JSON Schema格式输出：
{schema_str}

注意：
- 保持数值精度
- 保留单位信息
- 空单元格标记为null
- 输出必须是有效的JSON格式
- 不要添加任何额外的解释文字"""

    try:
        # 读取图片并编码为base64
        with open(image_path, "rb") as f:
            image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode("utf-8")

        client = get_client()
        response = client.chat.completions.create(
            model=QWEN_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}"
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
            max_tokens=4000,
        )

        # 处理不同的响应格式
        content = response.choices[0].message.content
        if isinstance(content, str):
            result_text = content
        elif isinstance(content, list) and len(content) > 0:
            # 如果content是列表，取第一个元素的text字段
            first_item = content[0]
            if isinstance(first_item, dict):
                result_text = first_item.get("text", str(first_item))
            else:
                result_text = str(first_item)
        elif isinstance(content, dict):
            result_text = content.get("text", str(content))
        else:
            result_text = str(content)

        # 尝试解析JSON（可能包含markdown代码块）
        json_text = result_text.strip()
        if "```json" in json_text:
            json_text = json_text.split("```json")[1].split("```")[0].strip()
        elif "```" in json_text:
            json_text = json_text.split("```")[1].split("```")[0].strip()

        try:
            extracted_data = json.loads(json_text)
            return {
                "success": True,
                "data": extracted_data,
                "raw_response": result_text,
            }
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": "提取的数据不是有效的JSON格式",
                "raw_response": result_text,
            }

    except Exception as e:
        return {"success": False, "error": f"提取失败: {str(e)}"}


def test_api_connection() -> bool:
    """测试API连接"""
    if not QWEN_API_KEY:
        print("未配置QWEN_API_KEY")
        return False

    try:
        client = get_client()
        response = client.chat.completions.create(
            model=QWEN_MODEL,
            messages=[{"role": "user", "content": "测试"}],
            max_tokens=10,
        )
        print("API连接成功")
        return True
    except Exception as e:
        print(f"API连接失败: {str(e)}")
        return False


if __name__ == "__main__":
    test_api_connection()
