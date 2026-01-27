from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class BrickStrengthRow(BaseModel):
    seq: Optional[int] = Field(
        default=None, description="Row sequence number as shown in the table."
    )
    test_location: Optional[str] = Field(
        default=None, description="Test location (raw text)."
    )
    estimated_strength_mpa: Optional[float] = Field(
        default=None, description="Estimated strength value in MPa (1 decimal)."
    )


class BrickStrengthRecord(BaseModel):
    table_id: Optional[str] = Field(default=None, description="Table control code.")
    test_date: Optional[str] = Field(
        default=None, description="Test date (preferred YYYY-MM-DD)."
    )
    instrument_id: Optional[str] = Field(default=None, description="Instrument ID.")
    brick_type: Optional[str] = Field(default=None, description="Brick type.")
    strength_grade: Optional[str] = Field(default=None, description="Strength grade.")
    rows: List[BrickStrengthRow] = Field(default_factory=list)
