from __future__ import annotations

from typing import Any, Dict

from .schema import BrickStrengthRecord
from .prompt import SYSTEM_PROMPT


def extract_brick_strength(payload: Dict[str, Any]) -> BrickStrengthRecord:
    """
    Extract brick strength fields from OCR/table payload.

    This is a stub entry point. Integrate with your LLM/OCR pipeline:
    1) Prepare OCR text / table cells as `payload`
    2) Call Claude with SYSTEM_PROMPT
    3) Parse and validate against BrickStrengthRecord
    """
    # Placeholder: raise until wired to real pipeline.
    raise NotImplementedError("Wire this to the Claude extraction pipeline.")
