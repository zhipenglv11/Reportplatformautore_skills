from __future__ import annotations

import copy
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

from config import settings


FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures"
DEMO_CONFIG_PATH = FIXTURE_DIR / "demo_config.json"


def _coerce_bool(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return None


@lru_cache(maxsize=1)
def _load_demo_config() -> Dict[str, Any]:
    if not DEMO_CONFIG_PATH.exists():
        return {}

    payload = json.loads(DEMO_CONFIG_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("report_demo_config_invalid")
    return payload


def is_report_demo_enabled() -> bool:
    config_value = _coerce_bool(_load_demo_config().get("enabled"))
    if config_value is not None:
        return config_value
    return bool(getattr(settings, "report_demo_mode", False))


def get_report_demo_profile() -> str:
    config_profile = _load_demo_config().get("profile")
    if isinstance(config_profile, str) and config_profile.strip():
        return config_profile.strip()
    profile = getattr(settings, "report_demo_profile", "").strip()
    return profile or "weifang_v1"


@lru_cache(maxsize=8)
def _load_fixture_profile(profile: str) -> Dict[str, Any]:
    fixture_path = FIXTURE_DIR / f"{profile}.json"
    if not fixture_path.exists():
        raise ValueError(f"report_demo_profile_not_found:{profile}")

    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"report_demo_fixture_invalid:{profile}")
    if not isinstance(payload.get("datasets"), dict):
        raise ValueError(f"report_demo_fixture_missing_datasets:{profile}")
    return payload


def get_report_demo_result(dataset_key: str) -> Optional[Dict[str, Any]]:
    if not is_report_demo_enabled():
        return None

    profile_name = get_report_demo_profile()
    fixture_profile = _load_fixture_profile(profile_name)
    dataset_payload = fixture_profile["datasets"].get(dataset_key)
    if dataset_payload is None:
        raise ValueError(f"report_demo_dataset_not_found:{profile_name}:{dataset_key}")
    if not isinstance(dataset_payload, dict):
        raise ValueError(f"report_demo_dataset_invalid:{profile_name}:{dataset_key}")

    result = copy.deepcopy(dataset_payload)
    meta = result.setdefault("meta", {})
    if isinstance(meta, dict):
        meta.setdefault("demo_mode", True)
        meta.setdefault("demo_profile", fixture_profile.get("profile", profile_name))
        meta.setdefault("source", "report_demo_fixture")
        meta.setdefault("source_document", fixture_profile.get("source_document"))
    return result
