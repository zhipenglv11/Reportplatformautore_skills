from typing import Dict, Any, List, Optional
import re
from datetime import datetime

class AuditTools:
    """
    原始记录与报告审核的公共工具函数库。
    供 RawRecordAuditSkill, ReportAuditSkill, CrossCheckSkill 共同调用。
    """

    @staticmethod
    def extract_dates(text: str) -> List[str]:
        """从文本中提取所有日期字符串 (YYYY-MM-DD 或 YYYY.MM.DD)"""
        # 简单示例正则
        patterns = [
            r'\d{4}-\d{2}-\d{2}',
            r'\d{4}\.\d{2}\.\d{2}',
            r'\d{4}年\d{2}月\d{2}日'
        ]
        dates = []
        for p in patterns:
            matches = re.findall(p, text)
            dates.extend(matches)
        return dates

    @staticmethod
    def validate_date_format(date_str: str) -> bool:
        """验证日期格式是否合法"""
        # TODO: 实现更复杂的日期校验
        return True

    @staticmethod
    def check_value_consistency(val1: Any, val2: Any, tolerance: float = 0.0) -> bool:
        """
        检查两个数值是否一致（支持误差范围）
        """
        try:
            v1 = float(str(val1).strip())
            v2 = float(str(val2).strip())
            return abs(v1 - v2) <= tolerance
        except ValueError:
            # 如果不是数字，进行字符串比较
            return str(val1).strip() == str(val2).strip()

    @staticmethod
    def normalize_text(text: str) -> str:
        """标准化文本（去除空白、统一标点等）"""
        if not text:
            return ""
        return text.strip().replace(" ", "").replace("：", ":")
