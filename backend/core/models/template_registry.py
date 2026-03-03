from __future__ import annotations

import json
from typing import Any, Dict, Optional

from sqlalchemy import text

from core.models.db import get_engine


def fetch_template_by_fingerprint(fingerprint: str) -> Optional[Dict[str, Any]]:
    query = text(
        """
        select
            template_id,
            dataset_key,
            fingerprint,
            schema_version,
            prompt_version,
            prompt,
            mapping_rules,
            validation_rules,
            status
        from template_registry
        where fingerprint = :fingerprint
          and status = 'active'
        """
    )
    with get_engine().begin() as conn:
        row = conn.execute(query, {"fingerprint": fingerprint}).mappings().first()
    return _deserialize_template(row)


def fetch_template_by_id(template_id: str) -> Optional[Dict[str, Any]]:
    query = text(
        """
        select
            template_id,
            dataset_key,
            fingerprint,
            schema_version,
            prompt_version,
            prompt,
            mapping_rules,
            validation_rules,
            status
        from template_registry
        where template_id = :template_id
          and status = 'active'
        """
    )
    with get_engine().begin() as conn:
        row = conn.execute(query, {"template_id": template_id}).mappings().first()
    return _deserialize_template(row)


def _deserialize_template(row: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not row:
        return None
    template = dict(row)
    template["mapping_rules"] = _load_json(template.get("mapping_rules")) or {}
    template["validation_rules"] = _load_json(template.get("validation_rules")) or {}
    return template


def _load_json(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value
