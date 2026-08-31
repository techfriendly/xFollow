from __future__ import annotations

import io
from typing import Any

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from . import ai_jobs, db, llm, runtime
from .config import load_runtime_config, sanitized_config
from .models import (
    AlertUpdate,
    AlertRuleCreate,
    ComplianceCheckRequest,
    ContractCommentCreate,
    ContractCreate,
    ContractChangeCreate,
    ContractChangeUpdate,
    ContractRiskUpdate,
    ContractUpdate,
    DataProtectionAssessmentUpdate,
    EvidenceCreate,
    EvidenceUpdate,
    FeedbackCreate,
    GeneratedDocumentRequest,
    ImportPcspRequest,
    ImportXreviewRequest,
    ImportXtenderRequest,
    InvoiceCreate,
    InvoiceUpdate,
    ObligationCreate,
    ObligationUpdate,
    OfferRiskAnalysisRequest,
    PenaltyCalculationRequest,
    ProceedingCreate,
    ProceedingUpdate,
    ResolutionRequest,
    TaskCreate,
    TaskUpdate,
    UserContext,
)
from .security import current_user, ensure_permission

app = FastAPI(
    title="xFollow Execution API",
    version="0.1.0",
    description="Seguimiento y control de ejecucion contractual con IA supervisada.",
)

_config = load_runtime_config()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _not_found(exc: KeyError) -> HTTPException:
    return HTTPException(status_code=404, detail=str(exc).strip("'") or "not_found")


@app.get("/health")
def health() -> dict[str, Any]:
    config = load_runtime_config()
    db_status = db.status()
    if config.db_required and not db_status["connected"]:
        raise HTTPException(status_code=503, detail={"reason": "database_unavailable", "db": db_status})
    return {
        "status": "ok" if db_status["connected"] else "degraded",
        "service": "xfollow-api",
        "db_backend": db_status["backend"],
        "db": db_status,
        "llm": llm.status(config),
        "integrations": runtime.integrations.status(),
        "schema": "xfollow",
        "llm_model": config.llm_model,
    }


@app.get("/config/runtime")
def runtime_config(_: UserContext = Depends(current_user)) -> dict[str, Any]:
    return {"trace_id": runtime.trace_id("cfg"), "config": sanitized_config(load_runtime_config())}


@app.get("/governance/manifest")
def governance_manifest(user: UserContext = Depends(current_user)) -> dict[str, Any]:
    return runtime.governance_manifest(user)


@app.get("/contracts")
def list_contracts(
    include_archived: bool = False,
    query: str | None = Query(default=None),
    status: str | None = Query(default=None),
    renewal_status: str | None = Query(default=None),
    responsible_unit: str | None = Query(default=None),
    contractor: str | None = Query(default=None),
    user: UserContext = Depends(current_user),
) -> dict[str, Any]:
    return runtime.list_contracts(
        user,
        include_archived=include_archived,
        query=query,
        status=status,
        renewal_status=renewal_status,
        responsible_unit=responsible_unit,
        contractor=contractor,
    )


@app.get("/integrations/status")
def integrations_status(user: UserContext = Depends(current_user)) -> dict[str, Any]:
    return {"trace_id": runtime.trace_id("int"), "integrations": runtime.integrations.status()}


@app.get("/alert-rules")
def list_alert_rules(user: UserContext = Depends(current_user)) -> dict[str, Any]:
    return runtime.list_alert_rules(user)


@app.post("/alert-rules")
def create_alert_rule(payload: AlertRuleCreate, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    return {"trace_id": runtime.trace_id("alr"), "alert_rule": runtime.create_alert_rule(user, payload)}


@app.post("/contracts")
def create_contract(payload: ContractCreate, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    contract = runtime.create_contract(user, payload)
    return {"trace_id": runtime.trace_id("ctr"), "contract": contract}


@app.get("/contracts/{contract_id}")
def get_contract(contract_id: str, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    contract = runtime.get_contract(user, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="contract_not_found")
    return {"trace_id": runtime.trace_id("ctr"), "contract": contract}


@app.get("/contracts/{contract_id}/comments")
def list_contract_comments(contract_id: str, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return runtime.list_contract_comments(user, contract_id)
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.post("/contracts/{contract_id}/comments")
def create_contract_comment(contract_id: str, payload: ContractCommentCreate, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return {"trace_id": runtime.trace_id("cmt"), "comment": runtime.create_contract_comment(user, contract_id, payload)}
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.patch("/contracts/{contract_id}")
def update_contract(contract_id: str, payload: ContractUpdate, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return {"trace_id": runtime.trace_id("ctr"), "contract": runtime.update_contract(user, contract_id, payload)}
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.post("/contracts/{contract_id}/archive")
def archive_contract(contract_id: str, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return {"trace_id": runtime.trace_id("ctr"), "contract": runtime.archive_contract(user, contract_id, True)}
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.post("/contracts/{contract_id}/restore")
def restore_contract(contract_id: str, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return {"trace_id": runtime.trace_id("ctr"), "contract": runtime.archive_contract(user, contract_id, False)}
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.get("/integrations/xtender/workspaces")
def xtender_workspaces(query: str | None = None, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    return runtime.xtender_candidates(user, query)


@app.post("/contracts/import/xtender")
def import_xtender(payload: ImportXtenderRequest, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return runtime.import_xtender(user, payload)
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.get("/integrations/pcsp/tenders")
def pcsp_tenders(query: str | None = None, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    return runtime.pcsp_candidates(user, query)


@app.post("/contracts/import/pcsp")
def import_pcsp(payload: ImportPcspRequest, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return runtime.import_pcsp(user, payload)
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.get("/integrations/xreview/awards")
def xreview_awards(query: str | None = None, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    return runtime.xreview_candidates(user, query)


@app.post("/contracts/import/xreview")
def import_xreview(payload: ImportXreviewRequest, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        result = runtime.import_xreview(user, payload)
        evidence = result.get("winning_offer_evidence") or []
        if result.get("created") and evidence and not load_runtime_config().force_memory:
            result["risk_analysis_job"] = ai_jobs.enqueue(
                user,
                result["contract"]["id"],
                "offer_risk_analysis",
                {"offer_evidence_id": evidence[0]["id"]},
            )
        return result
    except KeyError as exc:
        raise _not_found(exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/contracts/{contract_id}/obligations")
def list_obligations(contract_id: str, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return runtime.list_obligations(user, contract_id)
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.post("/contracts/{contract_id}/obligations")
def create_obligation(contract_id: str, payload: ObligationCreate, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return {"trace_id": runtime.trace_id("obl"), "obligation": runtime.create_obligation(user, contract_id, payload)}
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.post("/contracts/{contract_id}/obligations/extract")
def extract_obligations(contract_id: str, user: UserContext = Depends(current_user)) -> Any:
    try:
        if load_runtime_config().force_memory:
            return runtime.extract_obligations(user, contract_id)
        job = ai_jobs.enqueue(user, contract_id, "obligations_extract")
        return JSONResponse(status_code=202, content={"trace_id": runtime.trace_id("aij"), "job": job})
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.patch("/obligations/{obligation_id}")
def update_obligation(obligation_id: str, payload: ObligationUpdate, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        if payload.validation_status in {"validated", "rejected"}:
            ensure_permission(user, "validate")
        return {"trace_id": runtime.trace_id("obl"), "obligation": runtime.update_obligation(user, obligation_id, payload)}
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.get("/contracts/{contract_id}/alerts")
def list_alerts(contract_id: str, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return runtime.list_alerts(user, contract_id)
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.patch("/alerts/{alert_id}")
def update_alert(alert_id: str, payload: AlertUpdate, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return {"trace_id": runtime.trace_id("alt"), "alert": runtime.update_alert(user, alert_id, payload)}
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.get("/contracts/{contract_id}/tasks")
def list_tasks(contract_id: str, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return runtime.list_tasks(user, contract_id)
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.post("/contracts/{contract_id}/tasks")
def create_task(contract_id: str, payload: TaskCreate, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return {"trace_id": runtime.trace_id("tsk"), "task": runtime.create_task(user, contract_id, payload)}
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.post("/contracts/{contract_id}/tasks/generate")
def generate_tasks(contract_id: str, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return runtime.generate_tasks(user, contract_id)
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.patch("/tasks/{task_id}")
def update_task(task_id: str, payload: TaskUpdate, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return {"trace_id": runtime.trace_id("tsk"), "task": runtime.update_task(user, task_id, payload)}
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.get("/contracts/{contract_id}/evidence")
def list_evidence(contract_id: str, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return runtime.list_evidence(user, contract_id)
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.post("/contracts/{contract_id}/evidence")
def create_evidence(contract_id: str, payload: EvidenceCreate, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return {"trace_id": runtime.trace_id("evd"), "evidence": runtime.create_evidence(user, contract_id, payload)}
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.post("/contracts/{contract_id}/evidence/upload")
async def upload_evidence(
    contract_id: str,
    file: UploadFile = File(...),
    obligation_id: str | None = Form(default=None),
    title: str | None = Form(default=None),
    evidence_type: str | None = Form(default=None),
    user: UserContext = Depends(current_user),
) -> dict[str, Any]:
    try:
        evidence = runtime.create_evidence_from_upload(
            user,
            contract_id,
            filename=file.filename or "evidencia.bin",
            content_type=file.content_type,
            content=await file.read(),
            title=title,
            obligation_id=obligation_id,
            evidence_type=evidence_type,
        )
        return {"trace_id": runtime.trace_id("evd"), "evidence": evidence}
    except KeyError as exc:
        raise _not_found(exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.patch("/evidence/{evidence_id}")
def update_evidence(evidence_id: str, payload: EvidenceUpdate, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return {"trace_id": runtime.trace_id("evd"), "evidence": runtime.update_evidence(user, evidence_id, payload.obligation_id)}
    except KeyError as exc:
        raise _not_found(exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/evidence/{evidence_id}/download")
def download_evidence(evidence_id: str, user: UserContext = Depends(current_user)) -> StreamingResponse:
    try:
        filename, content = runtime.evidence_download_bytes(user, evidence_id)
    except KeyError as exc:
        raise _not_found(exc) from exc
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/contracts/{contract_id}/risks")
def list_contract_risks(contract_id: str, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return runtime.list_contract_risks(user, contract_id)
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.post("/contracts/{contract_id}/offer-analysis")
def analyze_winning_offer(contract_id: str, payload: OfferRiskAnalysisRequest, user: UserContext = Depends(current_user)) -> Any:
    try:
        if load_runtime_config().force_memory:
            raise RuntimeError("offer_analysis_requires_postgres")
        evidence = runtime._get_evidence(user, payload.evidence_id)
        if not evidence or evidence["contract_id"] != contract_id or evidence.get("evidence_type") != "winning_offer":
            raise ValueError("winning_offer_not_found")
        job = ai_jobs.enqueue(user, contract_id, "offer_risk_analysis", {"offer_evidence_id": payload.evidence_id})
        return JSONResponse(status_code=202, content={"trace_id": runtime.trace_id("aij"), "job": job})
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except KeyError as exc:
        raise _not_found(exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.patch("/risks/{risk_id}")
def update_contract_risk(risk_id: str, payload: ContractRiskUpdate, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        if payload.validation_status in {"validated", "rejected"}:
            ensure_permission(user, "validate")
        return {"trace_id": runtime.trace_id("rsk"), "risk": runtime.update_contract_risk(user, risk_id, payload)}
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.get("/contracts/{contract_id}/data-protection")
def list_data_protection(contract_id: str, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return runtime.list_data_protection_assessments(user, contract_id)
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.post("/contracts/{contract_id}/data-protection/scan")
def scan_data_protection(contract_id: str, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return runtime.scan_data_protection(user, contract_id)
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.patch("/data-protection/{assessment_id}")
def resolve_data_protection(assessment_id: str, payload: DataProtectionAssessmentUpdate, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        ensure_permission(user, "validate")
        return {"trace_id": runtime.trace_id("dpt"), "assessment": runtime.resolve_data_protection_assessment(user, assessment_id, payload)}
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.get("/contracts/{contract_id}/checks")
def list_checks(contract_id: str, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return runtime.list_checks(user, contract_id)
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.post("/contracts/{contract_id}/checks/run")
def run_checks(contract_id: str, payload: ComplianceCheckRequest, user: UserContext = Depends(current_user)) -> Any:
    try:
        if load_runtime_config().force_memory:
            return runtime.run_compliance_checks(user, contract_id, payload)
        job = ai_jobs.enqueue(
            user,
            contract_id,
            "compliance_check",
            {"obligation_id": payload.obligation_id, "evidence_ids": payload.evidence_ids},
        )
        return JSONResponse(status_code=202, content={"trace_id": runtime.trace_id("aij"), "job": job})
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.patch("/checks/{check_id}/resolve")
def resolve_check(check_id: str, payload: ResolutionRequest, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return {"trace_id": runtime.trace_id("chk"), "check": runtime.resolve_check(user, check_id, payload)}
    except KeyError as exc:
        raise _not_found(exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/contracts/{contract_id}/invoices")
def list_invoices(contract_id: str, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return runtime.list_invoices(user, contract_id)
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.post("/contracts/{contract_id}/invoices")
def create_invoice(contract_id: str, payload: InvoiceCreate, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return {"trace_id": runtime.trace_id("inv"), "invoice": runtime.create_invoice(user, contract_id, payload)}
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.patch("/invoices/{invoice_id}")
def update_invoice(invoice_id: str, payload: InvoiceUpdate, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        if payload.status in {"conforming", "rejected", "payment_ordered", "paid"}:
            ensure_permission(user, "validate")
        return {"trace_id": runtime.trace_id("inv"), "invoice": runtime.update_invoice(user, invoice_id, payload)}
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.get("/contracts/{contract_id}/changes")
def list_contract_changes(contract_id: str, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return runtime.list_contract_changes(user, contract_id)
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.post("/contracts/{contract_id}/changes")
def create_contract_change(contract_id: str, payload: ContractChangeCreate, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return {"trace_id": runtime.trace_id("chg"), "change": runtime.create_contract_change(user, contract_id, payload)}
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.patch("/changes/{change_id}")
def update_contract_change(change_id: str, payload: ContractChangeUpdate, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        if payload.status in {"validated", "applied", "rejected"}:
            ensure_permission(user, "validate")
        return {"trace_id": runtime.trace_id("chg"), "change": runtime.update_contract_change(user, change_id, payload)}
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.post("/changes/{change_id}/report")
def generate_contract_change_report(change_id: str, user: UserContext = Depends(current_user)) -> Any:
    try:
        if load_runtime_config().force_memory:
            return runtime.generate_contract_change_report(user, change_id)
        change = runtime.get_contract_change(user, change_id)
        if not change:
            raise KeyError(change_id)
        document_type = "prorroga_informe_juridico" if change["change_type"] == "extension" else "modificacion_informe_juridico"
        notes = "\n".join(
            [
                f"Propuesta: {change.get('title')}",
                f"Motivo: {change.get('reason')}",
                f"Base juridica: {change.get('legal_basis') or 'pendiente de completar'}",
                f"Impacto: {change.get('impact_summary') or 'pendiente de completar'}",
                f"Variacion economica: {change.get('amount_delta') if change.get('amount_delta') is not None else 'sin variacion indicada'}",
                f"Nueva fecha propuesta: {change.get('proposed_end_date') or 'sin cambio de fecha indicado'}",
            ]
        )
        job = ai_jobs.enqueue(
            user,
            change["contract_id"],
            "change_report",
            {"change_id": change_id, "document_type": document_type, "language": "es", "notes": notes},
        )
        return JSONResponse(status_code=202, content={"trace_id": runtime.trace_id("aij"), "job": job})
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.post("/changes/{change_id}/apply")
def apply_contract_change(change_id: str, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return runtime.apply_contract_change(user, change_id)
    except KeyError as exc:
        raise _not_found(exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/contracts/{contract_id}/liquidation")
def liquidation_preview(contract_id: str, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return runtime.liquidation_preview(user, contract_id)
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.get("/contracts/{contract_id}/generated-documents")
def list_documents(contract_id: str, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return runtime.list_documents(user, contract_id)
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.post("/contracts/{contract_id}/generated-documents")
def generate_document(contract_id: str, payload: GeneratedDocumentRequest, user: UserContext = Depends(current_user)) -> Any:
    try:
        if load_runtime_config().force_memory:
            return runtime.generate_document(user, contract_id, payload)
        job = ai_jobs.enqueue(
            user,
            contract_id,
            "document_generate",
            {"document_type": payload.document_type, "language": payload.language, "notes": payload.notes},
        )
        return JSONResponse(status_code=202, content={"trace_id": runtime.trace_id("aij"), "job": job})
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.get("/contracts/{contract_id}/ai-jobs")
def list_ai_jobs(contract_id: str, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return ai_jobs.list_for_contract(user, contract_id)
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.post("/ai-jobs/{job_id}/retry")
def retry_ai_job(job_id: str, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return {"trace_id": runtime.trace_id("aij"), "job": ai_jobs.retry(user, job_id)}
    except KeyError as exc:
        raise _not_found(exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.patch("/generated-documents/{document_id}/resolve")
def resolve_document(document_id: str, payload: ResolutionRequest, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return {"trace_id": runtime.trace_id("doc"), "document": runtime.resolve_document(user, document_id, payload)}
    except KeyError as exc:
        raise _not_found(exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/generated-documents/{document_id}/docx")
def download_document_docx(document_id: str, user: UserContext = Depends(current_user)) -> StreamingResponse:
    try:
        filename, content = runtime.document_docx_bytes(user, document_id)
    except KeyError as exc:
        raise _not_found(exc) from exc
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/contracts/{contract_id}/penalty-cases")
def list_penalties(contract_id: str, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return runtime.list_penalties(user, contract_id)
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.post("/contracts/{contract_id}/penalty-cases/calculate")
def calculate_penalty(contract_id: str, payload: PenaltyCalculationRequest, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return runtime.calculate_penalty(user, contract_id, payload)
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.patch("/penalty-cases/{penalty_id}/resolve")
def resolve_penalty(penalty_id: str, payload: ResolutionRequest, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return {"trace_id": runtime.trace_id("pen"), "penalty_case": runtime.resolve_penalty(user, penalty_id, payload)}
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.get("/contracts/{contract_id}/proceedings")
def list_proceedings(contract_id: str, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return runtime.list_proceedings(user, contract_id)
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.post("/contracts/{contract_id}/proceedings")
def open_proceeding(contract_id: str, payload: ProceedingCreate, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return {"trace_id": runtime.trace_id("prc"), "proceeding": runtime.open_proceeding(user, contract_id, payload)}
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.patch("/proceedings/{proceeding_id}")
def update_proceeding(proceeding_id: str, payload: ProceedingUpdate, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return {"trace_id": runtime.trace_id("prc"), "proceeding": runtime.update_proceeding(user, proceeding_id, payload)}
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.post("/feedback")
def create_feedback(payload: FeedbackCreate, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return {"trace_id": runtime.trace_id("fbk"), "feedback": runtime.create_feedback(user, payload)}
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.get("/contracts/{contract_id}/feedback")
def list_feedback(contract_id: str, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return runtime.list_feedback(user, contract_id)
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.get("/contracts/{contract_id}/audit")
def list_audit_events(contract_id: str, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return runtime.list_audit_events(user, contract_id)
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.get("/contracts/{contract_id}/governance")
def contract_governance(contract_id: str, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return runtime.contract_governance(user, contract_id)
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.get("/service-return/export")
def export_service_return(user: UserContext = Depends(current_user)) -> dict[str, Any]:
    return runtime.service_return_export(user)


@app.get("/service-return/export.zip")
def export_service_return_zip(user: UserContext = Depends(current_user)) -> StreamingResponse:
    filename, content = runtime.service_return_zip_bytes(user)
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/contracts/{contract_id}/export")
def export_contract(contract_id: str, user: UserContext = Depends(current_user)) -> dict[str, Any]:
    try:
        return runtime.export_contract(user, contract_id)
    except KeyError as exc:
        raise _not_found(exc) from exc


@app.get("/contracts/{contract_id}/export.zip")
def export_contract_zip(contract_id: str, user: UserContext = Depends(current_user)) -> StreamingResponse:
    try:
        filename, content = runtime.export_contract_zip_bytes(user, contract_id)
    except KeyError as exc:
        raise _not_found(exc) from exc
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
