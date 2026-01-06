from __future__ import annotations

from typing import Any, Dict, List


def _fake_parse_result(page_count: int) -> Dict[str, Any]:
    page_images = [f"data:image/png;base64,page-{idx}" for idx in range(1, page_count + 1)]
    evidence_refs = [
        {
            "object_key": "dummy.pdf",
            "type": "pdf",
            "page": idx,
            "snippet": "",
            "source_hash": "hash-123",
        }
        for idx in range(1, page_count + 1)
    ]
    return {
        "page_images": page_images,
        "evidence_refs": evidence_refs,
        "file_type": "pdf",
    }


def test_preview_chunk_merging(client, monkeypatch):
    from api import collection_routes

    async def fake_ingest(self, upload, project_id):
        return {
            "project_id": project_id,
            "object_key": "dummy.pdf",
            "source_hash": "hash-123",
            "filename": upload.filename,
        }

    async def fake_parse(self, ingest_result, use_llm=False, prompt=None):
        return _fake_parse_result(4)

    profiles = [
        {"record_code": "KSQR-4.13-XC-10", "fingerprint": "fp-a"},
        {"record_code": "KSQR-4.13-XC-10", "fingerprint": "fp-a"},
        {"record_code": None, "fingerprint": "fp-missing"},
        {"record_code": "KJQR-056-215", "fingerprint": "fp-b"},
    ]
    call_state = {"index": 0}

    async def fake_profile(self, images: List[str]):
        idx = call_state["index"]
        call_state["index"] += 1
        return profiles[idx]

    def fake_resolve(self, fingerprint, template_id=None):
        if fingerprint == "fp-a":
            return {"template_id": "template_a", "dataset_key": "ds_a"}
        if fingerprint == "fp-b":
            return {"template_id": "template_b", "dataset_key": "ds_b"}
        return None

    monkeypatch.setattr(collection_routes.IngestSkill, "execute", fake_ingest)
    monkeypatch.setattr(collection_routes.ParseSkill, "execute", fake_parse)
    monkeypatch.setattr(collection_routes.TemplateProfileSkill, "execute", fake_profile)
    monkeypatch.setattr(collection_routes.TemplateResolver, "resolve", fake_resolve)
    monkeypatch.setattr(collection_routes, "insert_run_log", lambda *_args, **_kwargs: None)

    response = client.post(
        "/api/ingest/preview",
        data={"project_id": "proj-1", "node_id": "node-1"},
        files={"file": ("demo.pdf", b"%PDF-1.4", "application/pdf")},
    )
    assert response.status_code == 200
    data = response.json()
    chunks = data.get("chunks") or []

    assert [chunk["chunk_id"] for chunk in chunks] == ["chunk-1-2", "chunk-3", "chunk-4"]
    assert chunks[0]["template_code"] == "KSQR-4.13-XC-10"
    assert chunks[0]["suggested_template_id"] == "template_a"
    assert chunks[1]["template_code"] is None
    assert chunks[1]["suggested_template_id"] is None
    assert chunks[2]["template_code"] == "KJQR-056-215"
    assert chunks[2]["suggested_template_id"] == "template_b"


def test_commit_multi_page_and_dedup(client, monkeypatch):
    from api import collection_routes
    from services.skills.validation_skill import ValidationResult

    async def fake_parse(self, ingest_result, use_llm=False, prompt=None):
        return _fake_parse_result(2)

    def fake_template_lookup(template_id):
        return {
            "template_id": template_id,
            "dataset_key": "ds_a",
            "prompt": "extract",
            "prompt_version": "v1",
            "schema_version": "v1",
            "mapping_rules": {},
            "validation_rules": None,
        }

    async def fake_vision_completion(self, **kwargs):
        images = kwargs.get("images") or []
        fake_vision_completion.images = images
        return {
            "content": {
                "test_item": "concrete_compressive_strength",
                "test_result": 12.5,
                "test_unit": "MPa",
            },
            "usage": {"tokens": 1},
        }

    def fake_mapping_execute(
        self,
        project_id,
        node_id,
        source_hash,
        structured_data,
        evidence_refs=None,
        run_id=None,
        test_item_override=None,
        mapping_override=None,
    ):
        payload = {
            "project_id": project_id,
            "node_id": node_id,
            "run_id": run_id,
            "test_item": "concrete_compressive_strength",
            "test_result": 12.5,
            "test_unit": "MPa",
            "test_value_json": {},
            "component_type": None,
            "location": None,
            "evidence_refs": evidence_refs or [],
            "raw_result": structured_data or {},
            "confirmed_result": None,
            "result_version": 1,
            "source_prompt_version": "v1",
            "schema_version": "v1",
            "raw_hash": "hash",
            "input_fingerprint": f"{source_hash}:{node_id}",
            "confirmed_by": None,
            "confirmed_at": None,
            "source_hash": source_hash,
            "confidence": None,
        }
        return {"mapped": payload, "meta": {"test_item_from_fallback": False}}

    def fake_validation_execute(self, payload, meta=None):
        return ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            normalized=payload,
            policy={},
        )

    monkeypatch.setattr(collection_routes.ParseSkill, "execute", fake_parse)
    monkeypatch.setattr(collection_routes, "fetch_template_by_id", fake_template_lookup)
    monkeypatch.setattr(collection_routes.LLMGateway, "vision_completion", fake_vision_completion)
    monkeypatch.setattr(collection_routes.MappingSkill, "execute", fake_mapping_execute)
    monkeypatch.setattr(collection_routes.ValidationSkill, "execute", fake_validation_execute)
    monkeypatch.setattr(collection_routes, "insert_run_log", lambda *_args, **_kwargs: None)

    request_body = {
        "project_id": "proj-1",
        "node_id": "node-1",
        "object_key": "dummy.pdf",
        "source_hash": "hash-123",
        "filename": "demo.pdf",
        "selections": [{"chunk_id": "chunk-1-2", "template_id": "template_a"}],
        "persist_result": True,
        "use_llm": True,
    }

    response = client.post("/api/ingest/commit", json=request_body)
    assert response.status_code == 200
    result = response.json()
    assert fake_vision_completion.images and len(fake_vision_completion.images) == 2
    assert result["results"][0]["deduped"] is False

    response = client.post("/api/ingest/commit", json=request_body)
    assert response.status_code == 200
    result = response.json()
    assert result["results"][0]["deduped"] is True
