from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from config import settings


def get_engine() -> Engine:
    db_url = settings.db_url
    # Ensure client_encoding is UTF8, which is critical for handling Chinese characters correctly
    # especially when the client OS environment (e.g. Windows) defaults to other encodings (e.g. GBK).
    if "postgresql" in db_url and "client_encoding" not in db_url:
        separator = "&" if "?" in db_url else "?"
        db_url += f"{separator}client_encoding=utf8"
    
    return create_engine(db_url, pool_pre_ping=True)


def insert_professional_data(payload: Dict[str, Any]) -> Optional[str]:
    for key in (
        "record_code",
        "test_location_text",
        "design_strength_grade",
        "strength_estimated_mpa",
        "carbonation_depth_avg_mm",
        "test_date",
        "casting_date",
    ):
        payload.setdefault(key, None)
    base_query = """
        insert into professional_data (
            project_id,
            node_id,
            run_id,
            test_item,
            test_result,
            test_unit,
            record_code,
            test_location_text,
            design_strength_grade,
            strength_estimated_mpa,
            carbonation_depth_avg_mm,
            test_date,
            casting_date,
            test_value_json,
            component_type,
            location,
            evidence_refs,
            raw_result,
            confirmed_result,
            result_version,
            source_prompt_version,
            schema_version,
            raw_hash,
            input_fingerprint,
            confirmed_by,
            confirmed_at,
            source_hash,
            confidence
        )
        values (
            :project_id,
            :node_id,
            :run_id,
            :test_item,
            :test_result,
            :test_unit,
            :record_code,
            :test_location_text,
            :design_strength_grade,
            :strength_estimated_mpa,
            :carbonation_depth_avg_mm,
            :test_date,
            :casting_date,
            :test_value_json,
            :component_type,
            :location,
            :evidence_refs,
            :raw_result,
            :confirmed_result,
            :result_version,
            :source_prompt_version,
            :schema_version,
            :raw_hash,
            :input_fingerprint,
            :confirmed_by,
            :confirmed_at,
            :source_hash,
            :confidence
        )
    """
    params = {
        **payload,
        "location": json.dumps(payload.get("location"), ensure_ascii=False) if payload.get("location") is not None else None,
        "evidence_refs": json.dumps(payload.get("evidence_refs") or []),
        "raw_result": json.dumps(payload.get("raw_result") or {}, ensure_ascii=False),
        "confirmed_result": json.dumps(payload.get("confirmed_result"), ensure_ascii=False) if payload.get("confirmed_result") else None,
        "test_value_json": json.dumps(payload.get("test_value_json"), ensure_ascii=False) if payload.get("test_value_json") else None,
    }
    engine = get_engine()
    has_fingerprint = bool(payload.get("input_fingerprint"))

    if has_fingerprint:
        if engine.dialect.name == "postgresql":
            query = text(
                base_query
                + """
                on conflict (input_fingerprint) where input_fingerprint is not null do nothing
                returning id
                """
            )
            with engine.begin() as conn:
                row = conn.execute(query, params).fetchone()
                if row:
                    return str(row[0])
                row = conn.execute(
                    text(
                        """
                        select id
                        from professional_data
                        where input_fingerprint = :input_fingerprint
                        order by created_at desc
                        limit 1
                        """
                    ),
                    params,
                ).fetchone()
                return str(row[0]) if row else None
        if engine.dialect.name == "sqlite":
            query = text(
                base_query
                + """
                on conflict(input_fingerprint) do nothing
                """
            )
            with engine.begin() as conn:
                conn.execute(query, params)
                row = conn.execute(
                    text(
                        """
                        select id
                        from professional_data
                        where input_fingerprint = :input_fingerprint
                        order by created_at desc
                        limit 1
                        """
                    ),
                    params,
                ).fetchone()
                return str(row[0]) if row else None

    query = text(base_query + " returning id")
    with engine.begin() as conn:
        row = conn.execute(query, params).fetchone()
        return str(row[0]) if row else None


def insert_run_log(payload: Dict[str, Any]) -> Optional[str]:
    query = text(
        """
        insert into run_log (
            run_id,
            project_id,
            node_id,
            record_id,
            status,
            stage,
            prompt_version,
            schema_version,
            input_file_hashes,
            skill_steps,
            llm_usage,
            total_cost,
            error_message
        )
        values (
            :run_id,
            :project_id,
            :node_id,
            :record_id,
            :status,
            :stage,
            :prompt_version,
            :schema_version,
            :input_file_hashes,
            :skill_steps,
            :llm_usage,
            :total_cost,
            :error_message
        )
        returning id
        """
    )

    with get_engine().begin() as conn:
        result = conn.execute(
            query,
            {
                **payload,
                "input_file_hashes": json.dumps(payload.get("input_file_hashes") or {}),
                "skill_steps": json.dumps(payload.get("skill_steps") or {}),
                "llm_usage": json.dumps(payload.get("llm_usage") or {}),
            },
        )
        row = result.fetchone()
        return str(row[0]) if row else None


def fetch_record_id_by_fingerprint(
    input_fingerprint: str,
) -> Optional[str]:
    query = text(
        """
        select id
        from professional_data
        where input_fingerprint = :input_fingerprint
        order by created_at desc
        limit 1
        """
    )

    with get_engine().begin() as conn:
        row = conn.execute(
            query,
            {
                "input_fingerprint": input_fingerprint,
            },
        ).fetchone()
    return str(row[0]) if row else None


def fetch_professional_data(
    project_id: str,
    node_id: Optional[str] = None,
    test_item: Optional[str] = None,
) -> List[Dict[str, Any]]:
    query = """
        select
            id,
            project_id,
            node_id,
            run_id,
            test_item,
            test_result,
            test_unit,
            record_code,
            test_location_text,
            design_strength_grade,
            strength_estimated_mpa,
            carbonation_depth_avg_mm,
            test_date,
            casting_date,
            test_value_json,
            component_type,
            location,
            evidence_refs,
            raw_result,
            confirmed_result,
            result_version,
            source_prompt_version,
            schema_version,
            raw_hash,
            input_fingerprint,
            confirmed_by,
            confirmed_at,
            source_hash,
            confidence,
            created_at
        from professional_data
        where project_id = :project_id
    """
    params: Dict[str, Any] = {"project_id": project_id}
    if node_id:
        query += " and node_id = :node_id"
        params["node_id"] = node_id
    if test_item:
        query += " and test_item = :test_item"
        params["test_item"] = test_item
    query += " order by created_at desc"

    with get_engine().begin() as conn:
        rows = conn.execute(text(query), params).mappings().all()

    def load_json(value: Any) -> Any:
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

    results: List[Dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["location"] = load_json(item.get("location")) or {}
        item["evidence_refs"] = load_json(item.get("evidence_refs")) or []
        item["raw_result"] = load_json(item.get("raw_result")) or {}
        item["confirmed_result"] = load_json(item.get("confirmed_result"))
        item["test_value_json"] = load_json(item.get("test_value_json")) or {}
        results.append(item)
    return results
