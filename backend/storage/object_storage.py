# -*- coding: utf-8 -*-
"""Backward-compatible shim — real implementation lives in core.storage.object_storage."""
from core.storage.object_storage import (  # noqa: F401
    LocalObjectStorage,
    get_object_storage,
)
