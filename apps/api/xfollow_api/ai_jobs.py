from __future__ import annotations

import json
from typing import Any

from psycopg2.extras import Json

from . import db, llm, runtime
from .config import load_runtime_config
from .models import ContractChangeUpdate, GeneratedDocumentRequest, UserContext


def _id() -> str:
    return runtime._id("AIJ")


def _json_safe(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str, ensure_ascii=False))


def _sources(user: UserContext, contract_id: str) -> list[dict[str, Any]]:
    config = load_runtime_config()
    remaining = config.ai_source_total_chars
    sources: list[dict[str, Any]] = []
    for evidence in runtime.list_evidence(user, contract_id)["items"]:
        if evidence.get("status") != "available" or remaining <= 0:
            continue
        text = str(evidence.get("extracted_text") or "").strip()
        if not text:
            continue
        excerpt = text[: min(config.ai_source_max_chars, remaining)]
        remaining -= len(excerpt)
        sources.append(
            {
                "id": evidence["id"],
                "title": evidence.get("title") or evidence.get("original_filename") or evidence["id"],
                "obligation_id": evidence.get("obligation_id"),
                "evidence_type": evidence.get("evidence_type") or "document",
                "text": excerpt,
            }
        )
    return sources


def _context(user: UserContext, contract_id: str) -> dict[str, Any]:
    contract = runtime.get_contract(user, contract_id)
    if not contract:
        raise KeyError(contract_id)
    return _json_safe(
        {
            "contract": contract,
            "obligations": runtime.list_obligations(user, contract_id)["items"],
            "checks": runtime.list_checks(user, contract_id)["items"],
            "invoices": runtime.list_invoices(user, contract_id)["items"],
            "penalties": runtime.list_penalties(user, contract_id)["items"],
            "proceedings": runtime.list_proceedings(user, contract_id)["items"],
            "changes": runtime.list_contract_changes(user, contract_id)["items"],
            "sources": _sources(user, contract_id),
        }
    )


def _apply_options_to_context(context: dict[str, Any], job_type: str, options: dict[str, Any]) -> dict[str, Any]:
    """Freeze an explicit target while keeping the contract library available to the model."""
    if job_type != "compliance_check":
        return context
    obligation_id = str(options.get("obligation_id") or "")
    evidence_ids = {str(item) for item in options.get("evidence_ids") or []}
    scoped = dict(context)
    if obligation_id:
        scoped["obligations"] = [item for item in context["obligations"] if item.get("id") == obligation_id]
    if evidence_ids:
        scoped["sources"] = [item for item in context["sources"] if item.get("id") in evidence_ids]
    return scoped


def _public_job(row: dict[str, Any] | None) -> dict[str, Any] | None:
    item = runtime._row(row)
    if not item:
        return None
    payload = item.pop("payload", {})
    context = payload.get("context", {}) if isinstance(payload, dict) else {}
    sources = context.get("sources", []) if isinstance(context, dict) else []
    item["source_count"] = len(sources) if isinstance(sources, list) else 0
    return item


def enqueue(user: UserContext, contract_id: str, job_type: str, options: dict[str, Any] | None = None) -> dict[str, Any]:
    if not db.db_available():
        raise RuntimeError("ai_jobs_require_postgres")
    job_options = options or {}
    payload = {
        "context": _apply_options_to_context(_context(user, contract_id), job_type, job_options),
        "options": job_options,
    }
    job_id = _id()
    with db.connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO xfollow.ai_jobs(id, tenant_id, contract_id, job_type, payload, requested_by)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (job_id, user.tenant_id, contract_id, job_type, Json(payload), user.user_id),
        )
        conn.commit()
    job = get(user, job_id)
    runtime._audit(user, "ai_job.queued", contract_id, {"job_id": job_id, "job_type": job_type})
    return job or {"id": job_id, "status": "queued", "job_type": job_type}


def list_for_contract(user: UserContext, contract_id: str) -> dict[str, Any]:
    if not runtime.get_contract(user, contract_id):
        raise KeyError(contract_id)
    if not db.db_available():
        return {"trace_id": runtime.trace_id("aij"), "items": []}
    rows = db.fetch_all(
        "SELECT * FROM xfollow.ai_jobs WHERE tenant_id = %s AND contract_id = %s ORDER BY created_at DESC LIMIT 30",
        (user.tenant_id, contract_id),
    )
    return {"trace_id": runtime.trace_id("aij"), "items": [_public_job(row) for row in rows]}


def get(user: UserContext, job_id: str) -> dict[str, Any] | None:
    if not db.db_available():
        return None
    return _public_job(db.fetch_one("SELECT * FROM xfollow.ai_jobs WHERE tenant_id = %s AND id = %s", (user.tenant_id, job_id)))


def retry(user: UserContext, job_id: str) -> dict[str, Any]:
    job = get(user, job_id)
    if not job:
        raise KeyError(job_id)
    if job["status"] not in {"failed", "retrying"}:
        raise ValueError("ai_job_not_retryable")
    with db.connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            "UPDATE xfollow.ai_jobs SET status = 'queued', next_run_at = now(), last_error = NULL, updated_at = now() WHERE tenant_id = %s AND id = %s",
            (user.tenant_id, job_id),
        )
        conn.commit()
    runtime._audit(user, "ai_job.requeued", job["contract_id"], {"job_id": job_id})
    return get(user, job_id) or job


def claim_next() -> dict[str, Any] | None:
    if not db.db_available():
        return None
    with db.connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            """
            WITH candidate AS (
              SELECT id FROM xfollow.ai_jobs
              WHERE status IN ('queued', 'retrying') AND next_run_at <= now()
              ORDER BY next_run_at, created_at
              FOR UPDATE SKIP LOCKED
              LIMIT 1
            )
            UPDATE xfollow.ai_jobs job
            SET status = 'running', attempts = attempts + 1, claimed_at = now(), updated_at = now()
            FROM candidate
            WHERE job.id = candidate.id
            RETURNING job.*
            """
        )
        row = cursor.fetchone()
        conn.commit()
    return runtime._row(row) if row else None


def _messages(job: dict[str, Any]) -> list[dict[str, str]]:
    payload = job["payload"]
    context = payload["context"]
    sources = context.get("sources") or []
    source_text = "\n\n".join(
        f"[Fuente {source['id']}: {source['title']}; tipo: {source.get('evidence_type')}; obligación vinculada: {source.get('obligation_id') or 'ninguna'}]\n{source['text']}"
        for source in sources
    )
    base = (
        "Eres un asistente de seguimiento de ejecucion contractual publica. "
        "No inventes hechos, fechas ni decisiones. Si las fuentes no bastan, indicalo expresamente. "
        "Todo resultado es un borrador para validacion humana.\n\n"
        f"Contexto estructurado:\n{json.dumps({key: value for key, value in context.items() if key != 'sources'}, ensure_ascii=False)}\n\n"
        f"Documentos disponibles:\n{source_text or '(No hay documentos con texto extraido.)'}"
    )
    job_type = job["job_type"]
    if job_type == "obligations_extract":
        instruction = (
            "Devuelve exclusivamente JSON con una clave 'items'. Cada item debe incluir category, title, description, due_date "
            "(ISO o null), severity y source_ids. category solo puede ser deadline, delivery, sla, special_condition, warranty, "
            "payment, documentation, extension u other. severity solo baja, media, alta o critica. source_ids debe referirse solo "
            "a identificadores de fuente proporcionados."
        )
    elif job_type == "compliance_check":
        instruction = (
            "Devuelve exclusivamente JSON con una clave 'items'. Cada item debe incluir obligation_id, result, reasoning y evidence_ids. "
            "result solo puede ser compliant, at_risk, breach o needs_review. evidence_ids debe usar solo fuentes proporcionadas."
        )
    elif job_type == "offer_risk_analysis":
        options = payload.get("options") or {}
        instruction = (
            "Analiza la oferta adjudicataria indicada y compárala con los datos del contrato y las demás fuentes disponibles. "
            "Devuelve exclusivamente JSON con una clave 'items'. Cada item debe incluir title, description, comparison, risk_type, "
            "severity y source_ids. risk_type solo puede ser scope, schedule, resources, quality, economic, legal u other. "
            "severity solo puede ser baja, media, alta o critica. Identifica únicamente riesgos o lagunas de ejecución verificables; "
            "si no hay evidencia suficiente, indícalo en comparison y no inventes compromisos. source_ids debe incluir la oferta "
            f"adjudicataria {options.get('offer_evidence_id')} y solo referencias de fuente proporcionadas."
        )
    else:
        options = payload.get("options") or {}
        instruction = (
            "Redacta exclusivamente un borrador Markdown profesional del documento solicitado. Usa solo los datos aportados, menciona "
            "las lagunas de informacion y termina con una seccion de validacion humana. Tipo de documento: "
            f"{options.get('document_type')}. Observaciones: {options.get('notes') or 'ninguna'}."
        )
    return [
        {"role": "system", "content": "Responde en espanol y sigue estrictamente el formato solicitado."},
        {"role": "user", "content": f"{base}\n\n{instruction}"},
    ]


def _execute(job: dict[str, Any]) -> dict[str, Any]:
    payload = job["payload"]
    context = payload["context"]
    user = UserContext(user_id=job.get("requested_by") or "xfollow-worker", tenant_id=job["tenant_id"], roles=["admin"])
    if job["job_type"] == "obligations_extract":
        result = llm.chat_json(_messages(job), max_tokens=4096)
        return runtime.create_ai_obligations(user, job["contract_id"], result, context.get("sources") or [])
    if job["job_type"] == "compliance_check":
        result = llm.chat_json(_messages(job), max_tokens=4096)
        return runtime.create_ai_checks(user, job["contract_id"], result, context.get("sources") or [])
    if job["job_type"] == "offer_risk_analysis":
        result = llm.chat_json(_messages(job), max_tokens=4096)
        return runtime.create_ai_offer_risks(
            user,
            job["contract_id"],
            str(payload.get("options", {}).get("offer_evidence_id") or ""),
            result,
            context.get("sources") or [],
        )
    content = llm.chat_text(_messages(job), max_tokens=load_runtime_config().llm_max_output_tokens)
    options = payload.get("options") or {}
    document = runtime.create_ai_document(
        user,
        job["contract_id"],
        GeneratedDocumentRequest(document_type=options["document_type"], language=options.get("language") or "es", notes=options.get("notes")),
        content,
        context.get("sources") or [],
    )
    if job["job_type"] == "change_report":
        change_id = options["change_id"]
        runtime.update_contract_change(user, change_id, ContractChangeUpdate(document_id=document["id"], status="under_review"))
    return {"document_id": document["id"]}


def _mark(job: dict[str, Any], status: str, *, result: dict[str, Any] | None = None, error: str | None = None, delay_seconds: int = 0) -> None:
    with db.connection() as conn, conn.cursor() as cursor:
        if status == "retrying":
            cursor.execute(
                """
                UPDATE xfollow.ai_jobs
                SET status = %s, last_error = %s, next_run_at = now() + (%s * interval '1 second'), updated_at = now()
                WHERE id = %s
                """,
                (status, error, delay_seconds, job["id"]),
            )
        else:
            cursor.execute(
                """
                UPDATE xfollow.ai_jobs
                SET status = %s, result = %s, last_error = %s, finished_at = now(), updated_at = now()
                WHERE id = %s
                """,
                (status, Json(result or {}), error, job["id"]),
            )
        conn.commit()


def process_one() -> bool:
    job = claim_next()
    if not job:
        return False
    user = UserContext(user_id=job.get("requested_by") or "xfollow-worker", tenant_id=job["tenant_id"], roles=["admin"])
    try:
        result = _execute(job)
    except llm.LlmError as exc:
        if exc.transient:
            config = load_runtime_config()
            delay = min(config.ai_retry_max_seconds, max(3, 2 ** min(int(job["attempts"]), 10)))
            _mark(job, "retrying", error=str(exc)[:1000], delay_seconds=delay)
            runtime._audit(user, "ai_job.retrying", job["contract_id"], {"job_id": job["id"], "delay_seconds": delay})
        else:
            _mark(job, "failed", error=str(exc)[:1000])
            runtime._audit(user, "ai_job.failed", job["contract_id"], {"job_id": job["id"], "error": str(exc)[:160]})
    except Exception as exc:
        _mark(job, "failed", error=f"worker_error:{exc.__class__.__name__}")
        runtime._audit(user, "ai_job.failed", job["contract_id"], {"job_id": job["id"], "error": exc.__class__.__name__})
    else:
        _mark(job, "completed", result=result)
        runtime._audit(user, "ai_job.completed", job["contract_id"], {"job_id": job["id"], "job_type": job["job_type"]})
    return True
