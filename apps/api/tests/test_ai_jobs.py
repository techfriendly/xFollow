from __future__ import annotations

import pytest

from xfollow_api import ai_jobs, llm, runtime
from xfollow_api.config import RuntimeConfig


def _job() -> dict:
    return {
        "id": "AIJ-test",
        "tenant_id": "tenant-a",
        "contract_id": "CTR-test",
        "job_type": "document_generate",
        "requested_by": "user-a",
        "attempts": 1,
        "payload": {"context": {"sources": [{"id": "EVD-1", "text": "documento privado"}]}, "options": {"document_type": "recepcion_acta"}},
    }


def test_public_job_hides_frozen_document_text() -> None:
    public = ai_jobs._public_job(_job())

    assert public is not None
    assert "payload" not in public
    assert public["source_count"] == 1


def test_worker_retries_transient_llm_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    marked: list[tuple[str, dict]] = []
    monkeypatch.setattr(ai_jobs, "claim_next", lambda: _job())
    monkeypatch.setattr(ai_jobs, "_execute", lambda _: (_ for _ in ()).throw(llm.LlmError("network", transient=True)))
    monkeypatch.setattr(ai_jobs, "_mark", lambda _job, status, **kwargs: marked.append((status, kwargs)))
    monkeypatch.setattr(ai_jobs.runtime, "_audit", lambda *_: None)
    monkeypatch.setattr(ai_jobs, "load_runtime_config", lambda: RuntimeConfig(ai_retry_max_seconds=60))

    assert ai_jobs.process_one() is True
    assert marked == [("retrying", {"error": "network", "delay_seconds": 3})]


def test_worker_marks_invalid_llm_output_as_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    marked: list[tuple[str, dict]] = []
    monkeypatch.setattr(ai_jobs, "claim_next", lambda: _job())
    monkeypatch.setattr(ai_jobs, "_execute", lambda _: (_ for _ in ()).throw(llm.LlmError("llm_invalid_json", transient=False)))
    monkeypatch.setattr(ai_jobs, "_mark", lambda _job, status, **kwargs: marked.append((status, kwargs)))
    monkeypatch.setattr(ai_jobs.runtime, "_audit", lambda *_: None)

    assert ai_jobs.process_one() is True
    assert marked == [("failed", {"error": "llm_invalid_json"})]


def test_manual_retry_rejects_jobs_that_are_not_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ai_jobs, "get", lambda *_: {"id": "AIJ-test", "status": "completed"})

    with pytest.raises(ValueError, match="ai_job_not_retryable"):
        ai_jobs.retry(runtime.UserContext(user_id="user-a", tenant_id="tenant-a", roles=["admin"]), "AIJ-test")
