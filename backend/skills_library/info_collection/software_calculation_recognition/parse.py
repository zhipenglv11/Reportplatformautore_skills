#!/usr/bin/env python3
"""
Software calculation result extraction.
Extracts load/calculation parameters from uploaded documents.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULTS: Dict[str, Any] = {
    "mortar_strength_mpa": 1.1,
    "brick_strength_grade": "MU10.0",
    "live_loads": {
        "non_accessible_roof": 0.5,
        "living_room_bedroom_kitchen_wc": 2.0,
        "stair_and_balcony": 2.5,
    },
    "dead_loads": {
        "roof": 4.0,
        "floor_prefab": 3.0,
        "stair_room": 6.0,
    },
    "load_combination_type": "1.2D+1.4L",
}


def _to_float(v: Any) -> Optional[float]:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.strip()
        try:
            return float(s)
        except ValueError:
            return None
    return None


def _read_text_file(file_path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "gb18030", "gbk"):
        try:
            return file_path.read_text(encoding=enc, errors="ignore")
        except Exception:
            continue
    return file_path.read_text(encoding="latin-1", errors="ignore")


def _extract_pdf_text(file_path: Path) -> str:
    poppler_path = os.getenv("POPPLER_PATH", "").strip()
    candidates: List[str] = []
    if poppler_path:
        candidates.append(str(Path(poppler_path) / "pdftotext.exe"))
        candidates.append(str(Path(poppler_path) / "pdftotext"))
    candidates.append("pdftotext")

    for exe in candidates:
        try:
            cmd = [exe, "-layout", str(file_path), "-"]
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=60,
            )
            if proc.returncode == 0 and (proc.stdout or "").strip():
                return proc.stdout
        except Exception:
            continue

    # fallback: best-effort binary decode
    try:
        return file_path.read_bytes().decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _load_source_text(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return _extract_pdf_text(file_path)
    return _read_text_file(file_path)


def _find_first_float(text: str, patterns: List[str]) -> Optional[float]:
    for pattern in patterns:
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if not m:
            continue
        v = _to_float(m.group(1))
        if v is not None:
            return v
    return None


def _find_load_value(text: str, labels: List[str]) -> Optional[float]:
    for label in labels:
        pattern = rf"{label}\s*[:：]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:kN\s*/?\s*m(?:2|²)?)?"
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if m:
            v = _to_float(m.group(1))
            if v is not None:
                return v
    return None


def _find_load_value_in_prefixed_segment(text: str, labels: List[str], prefix: str) -> Optional[float]:
    # 优先在“活载：...”或“恒载（含自重）：...”段落内提取，减少同名标签串扰
    segment_match = re.search(
        rf"{re.escape(prefix)}[^\n:：]{{0,20}}[:：](.+?)(?:\n|$)",
        text,
        flags=re.IGNORECASE,
    )
    segment = segment_match.group(1) if segment_match else ""
    if segment:
        v = _find_load_value(segment, labels)
        if v is not None:
            return v
    return _find_load_value(text, labels)


def _normalize_brick_grade(raw: str) -> str:
    s = (raw or "").strip().upper().replace(" ", "")
    if s.startswith("MU"):
        num = s[2:]
        v = _to_float(num)
        if v is not None:
            return f"MU{v:.1f}"
        return s
    v = _to_float(s)
    if v is not None:
        return f"MU{v:.1f}"
    return "MU10.0"


def _extract_record(text: str, source_file: str) -> Dict[str, Any]:
    cleaned = (text or "").replace("\r\n", "\n")

    mortar = _find_first_float(
        cleaned,
        [
            r"砌筑砂浆(?:抗压)?强度(?:取值|等级)?\s*[:：]?\s*([0-9]+(?:\.[0-9]+)?)\s*MPA",
            r"砂浆强度(?:等级)?\s*M\s*[:：]?\s*([0-9]+(?:\.[0-9]+)?)",
            r"本层砂浆强度等级\s*M\s*[:：]?\s*([0-9]+(?:\.[0-9]+)?)",
        ],
    )

    brick_raw: Optional[str] = None
    for pattern in [
        r"砌墙砖(?:抗压)?强度等级\s*[:：]?\s*(MU\s*[0-9]+(?:\.[0-9]+)?)",
        r"块体强度等级\s*MU\s*[:：]?\s*([0-9]+(?:\.[0-9]+)?)",
        r"砖(?:墙)?强度(?:等级)?\s*MU\s*[:：]?\s*([0-9]+(?:\.[0-9]+)?)",
    ]:
        m = re.search(pattern, cleaned, flags=re.IGNORECASE)
        if m:
            brick_raw = m.group(1)
            break
    brick_grade = _normalize_brick_grade(brick_raw or "")

    live_loads = {
        "non_accessible_roof": _find_load_value_in_prefixed_segment(cleaned, ["不上人屋面"], "活载"),
        "living_room_bedroom_kitchen_wc": _find_load_value_in_prefixed_segment(
            cleaned,
            ["客厅、卧室、厨房、卫生间", "客厅卧室厨房卫生间"],
            "活载",
        ),
        "stair_and_balcony": _find_load_value_in_prefixed_segment(cleaned, ["楼梯、阳台", "楼梯阳台"], "活载"),
    }
    dead_loads = {
        "roof": _find_load_value_in_prefixed_segment(cleaned, ["屋面"], "恒载"),
        "floor_prefab": _find_load_value_in_prefixed_segment(
            cleaned,
            ["楼面（预制板）", "楼面(预制板)", "楼面预制板"],
            "恒载",
        ),
        "stair_room": _find_load_value_in_prefixed_segment(cleaned, ["楼梯间"], "恒载"),
    }

    combo_match = re.search(
        r"([0-9]+(?:\.[0-9]+)?\s*[dD]\s*\+\s*[0-9]+(?:\.[0-9]+)?\s*[lL])",
        cleaned,
    )
    load_combo = combo_match.group(1).upper().replace(" ", "") if combo_match else None

    wind = _find_load_value(cleaned, ["基本风压"])
    snow = _find_load_value(cleaned, ["基本雪压"])
    terrain_match = re.search(r"地面粗糙度(?:类别)?(?:为)?\s*([A-Da-d])\s*类", cleaned)
    terrain = f"{terrain_match.group(1).upper()}类" if terrain_match else None

    defaults_applied: List[str] = []

    if mortar is None:
        mortar = DEFAULTS["mortar_strength_mpa"]
        defaults_applied.append("mortar_strength_mpa")
    if not brick_raw:
        brick_grade = DEFAULTS["brick_strength_grade"]
        defaults_applied.append("brick_strength_grade")

    for k, v in list(live_loads.items()):
        if v is None:
            live_loads[k] = DEFAULTS["live_loads"][k]
            defaults_applied.append(f"live_loads.{k}")
    for k, v in list(dead_loads.items()):
        if v is None:
            dead_loads[k] = DEFAULTS["dead_loads"][k]
            defaults_applied.append(f"dead_loads.{k}")

    if not load_combo:
        load_combo = DEFAULTS["load_combination_type"]
        defaults_applied.append("load_combination_type")

    return {
        "meta": {
            "source_file": source_file,
            "parser": "software_calculation_recognition_v1",
        },
        "mortar_strength_mpa": round(float(mortar), 3),
        "brick_strength_grade": brick_grade,
        "live_loads": live_loads,
        "dead_loads": dead_loads,
        "load_combination_type": load_combo,
        "wind_snow_terrain": {
            "basic_wind_pressure": wind,
            "basic_snow_pressure": snow,
            "terrain_category": terrain,
        },
        "defaults_applied": sorted(set(defaults_applied)),
    }


def _make_report_entries(records: List[Dict[str, Any]], files: List[str]) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    for idx, file_path in enumerate(files):
        if idx < len(records):
            entries.append(
                {
                    "file": file_path,
                    "success": True,
                    "type": "software_calculation_results",
                    "data": records[idx],
                }
            )
        else:
            entries.append(
                {
                    "file": file_path,
                    "success": False,
                    "type": "software_calculation_results",
                    "error": "no_record_generated",
                }
            )
    return entries


def main() -> None:
    parser = argparse.ArgumentParser(description="Software calculation result extraction")
    parser.add_argument("files", nargs="+", help="Input files (PDF/TXT/MD)")
    parser.add_argument("--format", default="json", help="Output format (reserved)")
    parser.add_argument("--output-dir", "--output", "-o", default="data/output", dest="output_dir")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    records: List[Dict[str, Any]] = []
    input_files: List[str] = []
    for file_arg in args.files:
        path = Path(file_arg)
        input_files.append(str(path))
        if not path.exists():
            continue
        text = _load_source_text(path)
        record = _extract_record(text, path.name)
        records.append(record)

    report_entries = _make_report_entries(records, input_files)

    processing_report_path = out_dir / "processing_report.json"
    processing_report_path.write_text(
        json.dumps(report_entries, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    output_json_path = out_dir / "software_calculation_results.json"
    output_json_path.write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "success": True,
                "report": str(processing_report_path),
                "records": len(records),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
