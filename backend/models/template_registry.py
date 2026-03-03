# -*- coding: utf-8 -*-
"""Backward-compatible shim — real implementation lives in core.models.template_registry."""
from core.models.template_registry import (  # noqa: F401
    fetch_template_by_fingerprint,
    fetch_template_by_id,
)
