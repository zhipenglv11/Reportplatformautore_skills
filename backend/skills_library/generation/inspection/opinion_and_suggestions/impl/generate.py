"""
Generate chapter: 鉴定意见及处理建议（静态模板版）.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional


def generate_opinion_and_suggestions(
    project_id: str,
    node_id: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    _ = (project_id, node_id, context)

    sections: List[Dict[str, Any]] = [
        {
            "type": "text",
            "section_number": "",
            "section_title": "",
            "content": (
                "根据《危险房屋鉴定标准》（JGJ125-2016）进行综合评定，"
                "鉴定对象（建材新村5号楼）的危险性等级评定为B级，"
                "即个别结构构件评定为危险构件，但不影响主体结构安全，"
                "基本能满足安全使用要求。"
            ),
        },
        {
            "type": "text",
            "section_number": "",
            "section_title": "",
            "content": (
                "主要存在问题：\n"
                "1、一层24×D~F轴承重砖墙高厚比不满足要求；\n"
                "2、部分墙面存在渗水痕迹现象。"
            ),
        },
        {
            "type": "text",
            "section_number": "",
            "section_title": "",
            "content": "处理建议：对存在的问题采取相应措施进行处理。",
        },
    ]

    return {
        "dataset_key": "opinion_and_suggestions",
        "chapter_type": "opinion_and_suggestions",
        "sections": sections,
        "meta": {
            "title": "鉴定意见及处理建议",
            "has_data": True,
            "source": "static_template_v1",
            "generated_at": datetime.utcnow().isoformat(),
        },
    }


async def generate_opinion_and_suggestions_async(
    project_id: str,
    node_id: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return generate_opinion_and_suggestions(project_id, node_id, context)

