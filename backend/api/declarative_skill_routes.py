# -*- coding: utf-8 -*-
"""Backward-compatible shim — real implementation lives in collection.api.declarative_skill_routes."""
from collection.api.declarative_skill_routes import (  # noqa: F401
    router,
    skill_registry,
    initialize_declarative_skills,
    _normalize_record,
    _build_payload,
    _pick_output_arg,
    _resolve_report_path,
    _extract_report_entries,
    _extract_entry_data,
)
