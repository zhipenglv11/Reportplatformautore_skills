"""
Schema for Delegate Info Check
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field, asdict


@dataclass
class MetaData:
    control_id: Optional[str] = None
    record_no: Optional[str] = None
    client_org: Optional[str] = None
    inspection_reason: Optional[str] = None
    inspection_basis: Optional[str] = None
    instrument_id: Optional[str] = None
    inspection_date: Optional[str] = None
    house_name: Optional[str] = None


@dataclass
class DelegateInfoSchema:
    meta: MetaData = field(default_factory=MetaData)
    house_details: Optional[str] = None
    source_file: Optional[str] = None
    status: str = "success"
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "meta": asdict(self.meta) if self.meta else {},
            "house_details": self.house_details,
            "source_file": self.source_file,
            "status": self.status,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DelegateInfoSchema':
        meta = MetaData(**data.get('meta', {})) if data.get('meta') else MetaData()
        return cls(
            meta=meta,
            house_details=data.get('house_details'),
            source_file=data.get('source_file'),
            status=data.get('status', 'success'),
            notes=data.get('notes'),
        )


def get_json_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "required": ["meta"],
        "properties": {
            "meta": {
                "type": "object",
                "properties": {
                    "control_id": {"type": ["string", "null"]},
                    "record_no": {"type": ["string", "null"]},
                    "client_org": {"type": ["string", "null"]},
                    "inspection_reason": {"type": ["string", "null"]},
                    "inspection_basis": {"type": ["string", "null"]},
                    "instrument_id": {"type": ["string", "null"]},
                    "inspection_date": {"type": ["string", "null"]},
                    "house_name": {"type": ["string", "null"]},
                },
            },
            "house_details": {"type": ["string", "null"]},
            "notes": {"type": ["string", "null"]},
        },
    }
