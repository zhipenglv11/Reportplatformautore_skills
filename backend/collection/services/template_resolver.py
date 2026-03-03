from __future__ import annotations

from typing import Any, Dict, Optional

from core.models.template_registry import fetch_template_by_fingerprint, fetch_template_by_id


class TemplateResolver:
    """Resolve template registry entry by fingerprint or template_id."""

    def resolve(
        self,
        fingerprint: Optional[str],
        template_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        if template_id:
            return fetch_template_by_id(template_id)
        if fingerprint:
            return fetch_template_by_fingerprint(fingerprint)
        return None
