"""
Generate chapter: 分析说明（静态模板版）.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional


def _table_8() -> Dict[str, Any]:
    columns = ["鉴定对象", "构件类型", "构件类别", "鉴定构件", "结论"]
    header_rows = [
        [
            {"label": "鉴定对象"},
            {"label": "鉴定构件", "colSpan": 3},
            {"label": "结论"},
        ]
    ]

    body_rows: List[List[Dict[str, Any]]] = [
        [
            {"text": "基础层"},
            {"text": "基础构件"},
            {"text": "//", "colSpan": 2},
            {"text": "无危险点"},
        ],
    ]

    floors = [
        "一层（含二层楼面结构）",
        "二层（含三层楼面结构）",
        "三层（含四层楼面结构）",
        "四层（含屋面结构）",
    ]

    for idx, floor in enumerate(floors):
        # 每层 4 行，楼层单元格纵向合并
        body_rows.append(
            [
                {"text": floor, "rowSpan": 4},
                {"text": "砌体结构构件", "rowSpan": 2},
                {"text": "主要构件"},
                {"text": "24×D~F 轴承重砖墙" if idx > 0 else "24×D~F 轴承重砖墙高厚比不满足"},
                {"text": "纳入危险构件统计" if idx > 0 else "危险点"},
            ]
        )
        body_rows.append(
            [
                {"text": "一般构件"},
                {"text": "其余承重砖墙"},
                {"text": "无危险点"},
            ]
        )
        body_rows.append(
            [
                {"text": "混凝土结构构件", "rowSpan": 2},
                {"text": "主要构件"},
                {"text": "全数"},
                {"text": "无危险点"},
            ]
        )
        body_rows.append(
            [
                {"text": "一般构件"},
                {"text": "全数"},
                {"text": "无危险点"},
            ]
        )

    return {
        "columns": columns,
        "header_rows": header_rows,
        "body_rows": body_rows,
    }


def _table_9() -> Dict[str, Any]:
    return {
        "columns": ["构件名称", "基础", "基础危险构件综合比例", "基础层危险性等级"],
        "rows": [
            ["构件数量", "105", "", ""],
            ["危险构件数量", "0", "Rf=0", "Au"],
        ],
    }


def _table_10() -> Dict[str, Any]:
    columns = [
        "楼层",
        "构件名称（加权系数）",
        "承重墙（2.7）",
        "中梁（1.9）",
        "边梁（1.4）",
        "次梁（1.0）",
        "自承重墙（1.0）",
        "楼板（1.0）",
        "楼层危险构件综合比例",
        "楼层危险性等级",
    ]
    body_rows: List[List[Dict[str, Any]]] = []
    for i in range(1, 5):
        body_rows.append(
            [
                {"text": f"{i}层", "rowSpan": 2},
                {"text": "构件数量"},
                {"text": "43"},
                {"text": "7"},
                {"text": "14" if i <= 2 else "10"},
                {"text": "5"},
                {"text": "51"},
                {"text": "39"},
                {"text": f"R{i}=1.1%", "rowSpan": 2},
                {"text": "Bu", "rowSpan": 2},
            ]
        )
        body_rows.append(
            [
                {"text": "危险构件数量"},
                {"text": "1"},
                {"text": "0"},
                {"text": "0"},
                {"text": "0"},
                {"text": "0"},
                {"text": "0"},
            ]
        )
    return {"columns": columns, "body_rows": body_rows}


def _table_11() -> Dict[str, Any]:
    return {
        "columns": [
            "构件名称（加权系数）",
            "基础（3.5）",
            "承重墙（2.7）",
            "边柱（2.7）",
            "中梁（1.9）",
            "边梁（1.4）",
            "次梁（1.0）",
            "挑梁（1.0）",
            "自承重墙（1.0）",
            "楼板（1.0）",
            "整体结构危险构件综合比例",
        ],
        "rows": [
            ["构件数量", "105", "172", "0", "26", "45", "20", "0", "204", "156", ""],
            ["危险构件数量", "0", "4", "0", "0", "0", "0", "0", "0", "0", "R=0.8%"],
        ],
    }


def generate_analysis_explanation(
    project_id: str,
    node_id: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    _ = (project_id, node_id, context)
    sections: List[Dict[str, Any]] = [
        {
            "type": "text",
            "section_number": "（一）",
            "section_title": "地基危险性评定",
            "content": (
                "依据《危险房屋鉴定标准》（JGJ125-2016）的第4.2.1条的规定，"
                "鉴定对象地面与主体结构之间没有出现明显的相对位移，鉴定对象上部结构未出现"
                "因倾斜和不均匀沉降产生的明显裂缝，鉴定对象整体倾斜率未超过2%，地基评定为非危险状态。"
            ),
        },
        {
            "type": "text",
            "section_number": "（二）",
            "section_title": "基础及上部结构危险性鉴定",
            "content": "1. 第一层次构件危险性鉴定。",
        },
        {
            "type": "table",
            "section_number": "表8·",
            "section_title": "构件危险性评定",
            "table": _table_8(),
        },
        {
            "type": "text",
            "section_number": "",
            "section_title": "",
            "content": "2. 第二层次楼层危险性鉴定\n（1）基础层危险性评级",
        },
        {
            "type": "table",
            "section_number": "表9·",
            "section_title": "基础危险构件综合比例统计表",
            "table": _table_9(),
        },
        {
            "type": "text",
            "section_number": "",
            "section_title": "",
            "content": "注：根据《危险房屋鉴定标准》（JGJ125-2016）第6.3.1、6.3.2条判定。\n（2）一层至六层危险性评级",
        },
        {
            "type": "table",
            "section_number": "表10·",
            "section_title": "上部结构各楼层危险构件综合比例统计表",
            "table": _table_10(),
        },
        {
            "type": "text",
            "section_number": "",
            "section_title": "",
            "content": "3. 第三层次房屋危险性鉴定",
        },
        {
            "type": "table",
            "section_number": "表11·",
            "section_title": "房屋危险构件综合比例统计表",
            "table": _table_11(),
        },
        {
            "type": "text",
            "section_number": "",
            "section_title": "",
            "content": (
                "鉴定对象整体结构危险构件数量为4，构件总数为728，根据《危险房屋鉴定标准》"
                "JGJ125-2016第6.3.5条公式计算得：整体结构危险构件综合比例为R=0.8%。\n"
                "根据《危险房屋鉴定标准》（JGJ125-2016）第6.3.6条，0%≤R<5%，且不含危险性等级为Du级的楼层，"
                "鉴定对象危险性等级评定为B级。"
            ),
        },
    ]

    return {
        "dataset_key": "analysis_explanation",
        "sections": sections,
        "meta": {
            "title": "分析说明",
            "has_data": True,
            "source": "static_template_v1",
            "generated_at": datetime.utcnow().isoformat(),
        },
    }


async def generate_analysis_explanation_async(
    project_id: str,
    node_id: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return generate_analysis_explanation(project_id, node_id, context)

