"""
Qwen (OpenAI-compatible) client for brick table extraction.
"""

import base64
import json
import sys
import io
from pathlib import Path
from typing import Dict, Any

try:
    from openai import OpenAI
except ImportError:
    print("Missing openai package. Install with: pip install openai")
    sys.exit(1)

from scripts.config import QWEN_API_KEY, QWEN_MODEL


def get_client() -> OpenAI:
    return OpenAI(
        api_key=QWEN_API_KEY,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )


def _image_to_base64(image_path: Path) -> str:
    with open(image_path, "rb") as f:
        image_data = f.read()
    return base64.b64encode(image_data).decode("utf-8")


def classify_table_type(image_path: Path) -> Dict[str, Any]:
    if not QWEN_API_KEY:
        raise ValueError("Missing QWEN_API_KEY in .env")

    image_base64 = _image_to_base64(image_path)

    prompt = (
        "请查看图片并判断表格类型。\n"
        "优先检查左上角表格控制编号：若为 KJQR-056-223，则表格类型为“砖强度（回弹法）原始记录表”。\n"
        "若无法确认，返回“未知”。\n"
        "只返回表格类型名称，不要解释。"
    )

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
            max_tokens=50,
        )

        content = response.choices[0].message.content
        if isinstance(content, str):
            result_text = content
        elif isinstance(content, list) and len(content) > 0:
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
    if not QWEN_API_KEY:
        raise ValueError("Missing QWEN_API_KEY in .env")

    prompt = (
        "请从图像中提取砖强度（回弹法）原始记录表字段，并输出为标准 JSON。\n"
        "字段要求：\n"
        "- table_id：表格控制编号（左上角），不能识别则为 null\n"
        "- commission_id：委托单编号（右上角），通常格式为 No:xxxx，提取内容（包含No:前缀或者仅编号均可），识别不到为 null\n"
        "- test_date：检测日期，完整清晰时规范为 YYYY-MM-DD，否则保持原样字符串，不补全\n"
        "- instrument_id：仪器编号，识别不到为 null\n"
        "- brick_type：砖的种类，识别不到为 null\n"
        "- strength_grade：强度等级，识别不到为 null\n"
        "- rows：行数组，每行仅包含2个字段：\n"
        "  - test_location：检测部位，保留原意，仅做首尾空格与连续空格压缩\n"
        "  - estimated_strength_mpa：该检测部位对应的强度推定值（MPa），位于该行最后一列，空白或占位符为 null，数值严格保留 1 位小数（例如 15.0），不计算\n"
        "注意：每个检测部位只有一个强度推定值，不要提取序号。\n"
        "规则：能识别则输出，无法确认则输出 null，不推断不计算。\n"
        "输出必须是有效 JSON，不要附加解释。"
    )

    try:
        image_base64 = _image_to_base64(image_path)
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

        content = response.choices[0].message.content
        if isinstance(content, str):
            result_text = content
        elif isinstance(content, list) and len(content) > 0:
            first_item = content[0]
            if isinstance(first_item, dict):
                result_text = first_item.get("text", str(first_item))
            else:
                result_text = str(first_item)
        elif isinstance(content, dict):
            result_text = content.get("text", str(content))
        else:
            result_text = str(content)

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
                "error": "提取结果不是有效的 JSON",
                "raw_response": result_text,
            }

    except Exception as e:
        return {"success": False, "error": f"提取失败: {str(e)}"}


def test_api_connection() -> bool:
    if not QWEN_API_KEY:
        print("Missing QWEN_API_KEY")
        return False

    try:
        client = get_client()
        client.chat.completions.create(
            model=QWEN_MODEL,
            messages=[{"role": "user", "content": "测试"}],
            max_tokens=10,
        )
        print("API 连接成功")
        return True
    except Exception as e:
        print(f"API 连接失败: {str(e)}")
        return False


if __name__ == "__main__":
    test_api_connection()
