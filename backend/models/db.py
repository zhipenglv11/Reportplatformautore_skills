# -*- coding: utf-8 -*-
"""Backward-compatible shim — real implementation lives in core.models.db."""
from core.models.db import (  # noqa: F401
    get_engine,
    insert_professional_data,
    insert_run_log,
    fetch_record_id_by_fingerprint,
    fetch_professional_data,
)
