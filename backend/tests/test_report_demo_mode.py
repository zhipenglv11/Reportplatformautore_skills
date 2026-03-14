from __future__ import annotations

import asyncio
import json


def test_dispatch_skill_uses_demo_fixture(monkeypatch, tmp_path):
    from report.services import report_demo, report_generator

    async def should_not_run(*_args, **_kwargs):
        raise AssertionError("real generation should not run in demo mode")

    demo_config_path = tmp_path / "demo_config.json"
    demo_config_path.write_text(
        json.dumps({"enabled": True, "profile": "weifang_v1"}, ensure_ascii=False),
        encoding="utf-8",
    )
    monkeypatch.setattr(report_demo, "DEMO_CONFIG_PATH", demo_config_path)
    report_demo._load_demo_config.cache_clear()
    report_demo._load_fixture_profile.cache_clear()
    monkeypatch.setattr(report_generator, "generate_basic_situation_async", should_not_run)

    try:
        result = asyncio.run(
            report_generator.dispatch_skill("basic_situation", "demo-project", "chapter-1", {})
        )
    finally:
        report_demo._load_demo_config.cache_clear()
        report_demo._load_fixture_profile.cache_clear()

    assert result["dataset_key"] == "basic_situation"
    assert result["meta"]["demo_mode"] is True
    assert any(item["label"] == "鉴定对象" for item in result["items"])


def test_report_generate_returns_demo_blocks(client, monkeypatch, tmp_path):
    from report.api import routes as report_routes
    from report.services import report_demo

    demo_config_path = tmp_path / "demo_config.json"
    demo_config_path.write_text(
        json.dumps({"enabled": True, "profile": "weifang_v1"}, ensure_ascii=False),
        encoding="utf-8",
    )
    monkeypatch.setattr(report_demo, "DEMO_CONFIG_PATH", demo_config_path)
    report_demo._load_demo_config.cache_clear()
    report_demo._load_fixture_profile.cache_clear()
    monkeypatch.setattr(report_routes, "insert_run_log", lambda *_args, **_kwargs: None)

    try:
        response = client.post(
            "/api/report/generate",
            json={
                "project_id": "demo-project",
                "chapter_config": {
                    "node_id": "chapter-3",
                    "chapter_id": "chapter-3",
                    "title": "鉴定内容和方法及原始记录一览表",
                    "dataset_key": "inspection_content_and_methods",
                    "sourceNodeId": "scope_inspection_content_and_methods",
                    "context": {
                        "source_node_id": "scope_inspection_content_and_methods",
                        "sourceNodeId": "scope_inspection_content_and_methods",
                    },
                },
                "project_context": {},
            },
        )
    finally:
        report_demo._load_demo_config.cache_clear()
        report_demo._load_fixture_profile.cache_clear()

    assert response.status_code == 200
    payload = response.json()
    blocks = payload["chapters"][0]["chapter_content"]["blocks"]
    assert len(blocks) >= 3
    assert any(block["type"] == "text" for block in blocks)
    assert any(block["type"] == "table" for block in blocks)
    assert payload["chapters"][0]["summary"]["demo_mode"] is True
