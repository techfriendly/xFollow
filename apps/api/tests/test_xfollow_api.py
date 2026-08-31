from __future__ import annotations

import io
import zipfile

from fastapi.testclient import TestClient

from xfollow_api import runtime
from xfollow_api.main import app
from xfollow_api.models import UserContext

client = TestClient(app, backend_options={"use_uvloop": True})


def setup_function() -> None:
    runtime.reset_memory()


def test_contract_lifecycle_extracts_alerts_and_exports() -> None:
    created = client.post(
        "/contracts",
        json={
            "title": "Servicio de limpieza de edificios",
            "file_number": "2026/SERV/010",
            "contracting_body": "Ayuntamiento demo",
            "contractor": "Limpiezas Demo SL",
            "contract_type": "Servicios",
            "cpv_codes": ["90911200-8"],
            "status": "active",
            "awarded_amount": 186000,
            "start_date": "2026-08-01",
            "end_date": "2027-07-31",
            "warranty_end_date": "2027-10-31",
            "extension_deadline": "2027-05-31",
            "data": {
                "special_execution_conditions": [
                    {"title": "Clausula social", "description": "Acreditar mensualmente el cumplimiento laboral."}
                ]
            },
        },
    )
    assert created.status_code == 200
    contract_id = created.json()["contract"]["id"]

    extracted = client.post(f"/contracts/{contract_id}/obligations/extract")
    obligations = extracted.json()["items"]
    assert extracted.status_code == 200
    assert len(obligations) >= 4

    validated = client.patch(f"/obligations/{obligations[0]['id']}", json={"validation_status": "validated"})
    assert validated.status_code == 200
    assert validated.json()["obligation"]["validation_status"] == "validated"

    alerts = client.get(f"/contracts/{contract_id}/alerts")
    assert alerts.status_code == 200
    assert alerts.json()["items"]

    evidence = client.post(
        f"/contracts/{contract_id}/evidence",
        json={
            "obligation_id": obligations[0]["id"],
            "title": "Acta de entrega mensual",
            "extracted_text": "La prestacion se ha entregado y cumple lo requerido.",
        },
    )
    assert evidence.status_code == 200
    sensitive_evidence = client.post(
        f"/contracts/{contract_id}/evidence",
        json={
            "title": "Informe con datos a revisar",
            "extracted_text": "Contacto ana@example.org con DNI 12345678Z. Documento confidencial con API key pendiente de retirar.",
        },
    )
    assert sensitive_evidence.status_code == 200

    uploaded = client.post(
        f"/contracts/{contract_id}/evidence/upload",
        data={"obligation_id": obligations[0]["id"], "title": "Informe de servicio"},
        files={"file": ("informe.txt", b"La prestacion cumple y fue recibida sin incidencias.", "text/plain")},
    )
    assert uploaded.status_code == 200
    assert uploaded.json()["evidence"]["content_hash"]
    assert "cumple" in uploaded.json()["evidence"]["extracted_text"]
    uploaded_evidence_id = uploaded.json()["evidence"]["id"]
    downloaded = client.get(f"/evidence/{uploaded_evidence_id}/download")
    assert downloaded.status_code == 200
    assert downloaded.content.startswith(b"La prestacion cumple")
    detached = client.patch(f"/evidence/{uploaded_evidence_id}", json={"obligation_id": None})
    assert detached.status_code == 200
    assert detached.json()["evidence"]["obligation_id"] is None
    relinked = client.patch(f"/evidence/{uploaded_evidence_id}", json={"obligation_id": obligations[0]["id"]})
    assert relinked.status_code == 200
    assert relinked.json()["evidence"]["obligation_id"] == obligations[0]["id"]

    winning_offer = client.post(
        f"/contracts/{contract_id}/evidence/upload",
        data={"title": "Oferta adjudicataria", "evidence_type": "winning_offer"},
        files={"file": ("oferta.txt", b"La empresa se compromete a presentar un plan de mantenimiento mensual con equipo dedicado.", "text/plain")},
    )
    assert winning_offer.status_code == 200
    offer_evidence = winning_offer.json()["evidence"]
    assert offer_evidence["evidence_type"] == "winning_offer"
    risks = runtime.create_ai_offer_risks(
        UserContext(user_id="demo-user", tenant_id="tenant-demo", roles=["admin"]),
        contract_id,
        offer_evidence["id"],
        {
            "items": [
                {
                    "title": "Plan mensual sin evidencia de entrega",
                    "description": "La oferta compromete un plan mensual y no hay evidencia de su presentación.",
                    "comparison": "El contrato requiere seguimiento documental, pero no fija la frecuencia del plan en las fuentes disponibles.",
                    "risk_type": "schedule",
                    "severity": "media",
                    "source_ids": [offer_evidence["id"]],
                }
            ]
        },
        [{"id": offer_evidence["id"], "title": offer_evidence["title"]}],
    )
    assert risks["items"][0]["validation_status"] == "draft"
    listed_risks = client.get(f"/contracts/{contract_id}/risks")
    assert listed_risks.status_code == 200
    assert listed_risks.json()["items"][0]["offer_evidence_id"] == offer_evidence["id"]
    validated_risk = client.patch(f"/risks/{risks['items'][0]['id']}", json={"validation_status": "validated"})
    assert validated_risk.status_code == 200
    assert validated_risk.json()["risk"]["validation_status"] == "validated"

    data_scan = client.post(f"/contracts/{contract_id}/data-protection/scan")
    assert data_scan.status_code == 200
    flagged = [item for item in data_scan.json()["items"] if item["result"] != "clear"]
    assert flagged
    assert any(finding["label"] == "email" for item in flagged for finding in item["findings"])
    assert "[EMAIL]" in flagged[0]["redacted_preview"] or "[DNI_NIE]" in flagged[0]["redacted_preview"]
    resolved_data = client.patch(f"/data-protection/{flagged[0]['id']}", json={"status": "resolved", "resolution_comment": "Anonimizado en origen"})
    assert resolved_data.status_code == 200
    assert resolved_data.json()["assessment"]["resolved_by"] == "demo-user"

    checks = client.post(
        f"/contracts/{contract_id}/checks/run",
        json={
            "obligation_id": obligations[0]["id"],
            "evidence_ids": [evidence.json()["evidence"]["id"], uploaded.json()["evidence"]["id"]],
        },
    )
    assert checks.status_code == 200
    assert checks.json()["items"][0]["result"] == "compliant"
    assert checks.json()["items"][0]["status"] == "draft"
    resolved_check = client.patch(f"/checks/{checks.json()['items'][0]['id']}/resolve", json={"status": "validated"})
    assert resolved_check.status_code == 200
    assert resolved_check.json()["check"]["validated_by"] == "demo-user"

    invoice = client.post(
        f"/contracts/{contract_id}/invoices",
        json={
            "obligation_id": obligations[0]["id"],
            "invoice_number": "F-2026-0001",
            "concept": "Servicio mensual de limpieza",
            "invoice_date": "2026-09-01",
            "service_period_start": "2026-08-01",
            "service_period_end": "2026-08-31",
            "amount_without_tax": 1000,
            "tax_amount": 210,
            "evidence_ids": [evidence.json()["evidence"]["id"]],
        },
    )
    assert invoice.status_code == 200
    invoice_payload = invoice.json()["invoice"]
    assert invoice_payload["amount_with_tax"] == 1210
    assert invoice_payload["payment_due_date"] == "2026-10-01"

    conformed_invoice = client.patch(f"/invoices/{invoice_payload['id']}", json={"status": "conforming"})
    assert conformed_invoice.status_code == 200
    assert conformed_invoice.json()["invoice"]["validated_by"] == "demo-user"

    paid_invoice = client.patch(f"/invoices/{invoice_payload['id']}", json={"status": "paid"})
    assert paid_invoice.status_code == 200
    assert paid_invoice.json()["invoice"]["paid_at"]

    tasks = client.post(f"/contracts/{contract_id}/tasks/generate")
    assert tasks.status_code == 200
    assert tasks.json()["items"]
    task_id = tasks.json()["items"][0]["id"]
    closed_task = client.patch(f"/tasks/{task_id}", json={"status": "done"})
    assert closed_task.status_code == 200
    assert closed_task.json()["task"]["completed_by"] == "demo-user"

    document = client.post(
        f"/contracts/{contract_id}/generated-documents",
        json={"document_type": "recepcion_acta", "language": "es"},
    )
    assert document.status_code == 200
    assert "requiere revision" in document.json()["document"]["content_text"].lower()
    document_id = document.json()["document"]["id"]
    docx = client.get(f"/generated-documents/{document_id}/docx")
    assert docx.status_code == 200
    assert docx.content.startswith(b"PK")
    resolved_document = client.patch(f"/generated-documents/{document_id}/resolve", json={"status": "validated"})
    assert resolved_document.status_code == 200
    assert resolved_document.json()["document"]["status"] == "validated"

    feedback = client.post(
        "/feedback",
        json={
            "contract_id": contract_id,
            "artifact_type": "document",
            "artifact_id": document_id,
            "rating": "positive",
            "comment": "Borrador util tras revision.",
        },
    )
    assert feedback.status_code == 200
    assert feedback.json()["feedback"]["rating"] == "positive"
    feedback_list = client.get(f"/contracts/{contract_id}/feedback")
    assert feedback_list.status_code == 200
    assert feedback_list.json()["items"][0]["artifact_id"] == document_id
    audit = client.get(f"/contracts/{contract_id}/audit")
    assert audit.status_code == 200
    assert any(item["action"] == "feedback.created" for item in audit.json()["items"])
    governance = client.get(f"/contracts/{contract_id}/governance")
    assert governance.status_code == 200
    assert governance.json()["manifest"]["human_oversight"]["feedback_enabled"] is True
    assert governance.json()["audit_summary"]["events"] >= 1
    manifest = client.get("/governance/manifest")
    assert manifest.status_code == 200
    assert manifest.json()["service_return"]["formats"]

    change = client.post(
        f"/contracts/{contract_id}/changes",
        json={
            "change_type": "extension",
            "reason": "Continuidad del servicio mientras se tramita nueva licitacion.",
            "legal_basis": "Prorroga prevista en el expediente.",
            "impact_summary": "Amplia el plazo seis meses sin alterar condiciones esenciales.",
            "amount_delta": 93000,
            "extension_months": 6,
        },
    )
    assert change.status_code == 200
    change_payload = change.json()["change"]
    assert change_payload["status"] == "draft"
    assert change_payload["proposed_end_date"] == "2028-01-31"

    report = client.post(f"/changes/{change_payload['id']}/report")
    assert report.status_code == 200
    assert report.json()["document"]["document_type"] == "prorroga_informe_juridico"
    assert report.json()["change"]["status"] == "under_review"

    blocked_apply = client.post(f"/changes/{change_payload['id']}/apply")
    assert blocked_apply.status_code == 400

    validated_change = client.patch(f"/changes/{change_payload['id']}", json={"status": "validated"})
    assert validated_change.status_code == 200
    assert validated_change.json()["change"]["validated_by"] == "demo-user"

    applied = client.post(f"/changes/{change_payload['id']}/apply")
    assert applied.status_code == 200
    assert applied.json()["change"]["status"] == "applied"
    assert applied.json()["contract"]["end_date"] == "2028-01-31"
    assert applied.json()["contract"]["awarded_amount"] == 279000

    exported = client.get(f"/contracts/{contract_id}/export")
    assert exported.status_code == 200
    assert exported.json()["manifest"]["service"] == "xFollow"
    assert exported.json()["contract"]["id"] == contract_id
    assert exported.json()["invoices"][0]["invoice_number"] == "F-2026-0001"
    assert exported.json()["data_protection"]
    assert exported.json()["liquidation"]["paid_amount"] == 1210
    assert exported.json()["changes"][0]["status"] == "applied"
    assert exported.json()["feedback"][0]["rating"] == "positive"
    assert exported.json()["governance"]["manifest"]["security"]["export_requires_permission"] == "export"
    exported_zip = client.get(f"/contracts/{contract_id}/export.zip")
    assert exported_zip.status_code == 200
    assert exported_zip.content.startswith(b"PK")

    service_return = client.get("/service-return/export")
    assert service_return.status_code == 200
    assert service_return.json()["manifest"]["format"] == "service_return_json"
    assert any(item["id"] == contract_id for item in service_return.json()["contracts"])
    assert "USER_GUIDE.md" in service_return.json()["transition_documents"]
    assert "COMPLIANCE_MATRIX.md" in service_return.json()["transition_documents"]
    service_return_zip = client.get("/service-return/export.zip")
    assert service_return_zip.status_code == 200
    assert service_return_zip.content.startswith(b"PK")
    with zipfile.ZipFile(io.BytesIO(service_return_zip.content)) as archive:
        names = set(archive.namelist())
    assert "transition/USER_GUIDE.md" in names
    assert "transition/COMPLIANCE_MATRIX.md" in names
    assert any(name.endswith("/data_protection.json") for name in names)


def test_import_xtender_and_pcsp_are_idempotent() -> None:
    first = client.post("/contracts/import/xtender", json={"workspace_id": "EXP-DEMO-XTENDER"})
    second = client.post("/contracts/import/xtender", json={"workspace_id": "EXP-DEMO-XTENDER"})

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["contract"]["id"] == second.json()["contract"]["id"]
    assert second.json()["created"] is False
    assert first.json()["draft_obligations"]

    pcsp_first = client.post("/contracts/import/pcsp", json={"tender_id": "PCSP-DEMO-ADJ"})
    pcsp_second = client.post("/contracts/import/pcsp", json={"tender_id": "PCSP-DEMO-ADJ"})

    assert pcsp_first.status_code == 200
    assert pcsp_second.json()["created"] is False
    assert pcsp_first.json()["contract"]["source_kind"] == "pcsp"


def test_import_xreview_reuses_award_package_idempotently() -> None:
    candidates = client.get("/integrations/xreview/awards")
    assert candidates.status_code == 200
    assert candidates.json()["items"][0]["id"] == "HOF-DEMO-XREVIEW"

    first = client.post("/contracts/import/xreview", json={"handoff_id": "HOF-DEMO-XREVIEW"})
    second = client.post("/contracts/import/xreview", json={"handoff_id": "HOF-DEMO-XREVIEW"})

    assert first.status_code == 200
    assert second.status_code == 200
    payload = first.json()
    assert payload["contract"]["source_kind"] == "xreview"
    assert payload["contract"]["xreview_lot_id"] == "LOT-DEMO-XREVIEW"
    assert payload["winning_offer_evidence"][0]["object_key"] == "s3://xreview/xreview/demo/oferta-adjudicataria.pdf"
    assert payload["basis_evidence"][0]["object_key"] == "s3://xreview/xreview/demo/pcap.pdf"
    assert payload["basis_evidence"][0]["evidence_type"] == "tender_basis"
    assert payload["accepted_obligations"][0]["validation_status"] == "validated"
    assert second.json()["created"] is False
    assert second.json()["contract"]["id"] == payload["contract"]["id"]
    assert len(second.json()["winning_offer_evidence"]) == 1
    assert len(second.json()["basis_evidence"]) == 1
    assert len(second.json()["accepted_obligations"]) == 1


def test_penalty_calculation_is_capped_and_requires_validation() -> None:
    contract = client.post("/contracts", json={"title": "Contrato con retraso", "status": "active"}).json()["contract"]
    penalty = client.post(
        f"/contracts/{contract['id']}/penalty-cases/calculate",
        json={
            "basis_text": "Clausula 32: penalidad diaria por retraso.",
            "daily_amount": 300,
            "days_late": 20,
            "cap_amount": 5000,
        },
    )

    assert penalty.status_code == 200
    payload = penalty.json()["penalty_case"]
    assert payload["calculated_amount"] == 5000
    assert payload["calculation"]["raw_amount"] == 6000
    assert payload["status"] == "draft"

    resolved = client.patch(f"/penalty-cases/{payload['id']}/resolve", json={"status": "validated", "comment": "Revisado"})
    assert resolved.status_code == 200
    assert resolved.json()["penalty_case"]["validated_by"] == "demo-user"

    proceeding = client.post(
        f"/contracts/{contract['id']}/proceedings",
        json={
            "case_type": "penalty",
            "penalty_case_id": payload["id"],
            "trigger_text": "Retraso acreditado por la unidad responsable.",
            "legal_basis": "Clausula 32 del PCAP.",
            "proposed_action": "Conceder audiencia y formular propuesta.",
            "due_date": "2026-10-15",
        },
    )
    assert proceeding.status_code == 200
    proceeding_payload = proceeding.json()["proceeding"]
    assert proceeding_payload["status"] == "opened"
    assert proceeding_payload["timeline"]

    advanced = client.patch(f"/proceedings/{proceeding_payload['id']}", json={"status": "hearing", "comment": "Audiencia iniciada"})
    assert advanced.status_code == 200
    assert advanced.json()["proceeding"]["status"] == "hearing"

    liquidation = client.get(f"/contracts/{contract['id']}/liquidation")
    assert liquidation.status_code == 200
    assert liquidation.json()["summary"]["validated_penalties_amount"] == 5000


def test_tenant_isolation_and_read_only_permissions() -> None:
    created = client.post(
        "/contracts",
        headers={"X-User-Id": "owner", "X-Tenant-Id": "tenant-a", "X-Roles": "responsable_contrato"},
        json={"title": "Contrato tenant A"},
    )
    contract_id = created.json()["contract"]["id"]

    hidden = client.get(
        f"/contracts/{contract_id}",
        headers={"X-User-Id": "reader", "X-Tenant-Id": "tenant-b", "X-Roles": "responsable_contrato"},
    )
    assert hidden.status_code == 404

    forbidden = client.post(
        "/contracts",
        headers={"X-User-Id": "reader", "X-Tenant-Id": "tenant-a", "X-Roles": "consulta"},
        json={"title": "No permitido"},
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["detail"] == "permission_required:edit"

    obligation = client.post(
        f"/contracts/{contract_id}/obligations",
        headers={"X-User-Id": "editor", "X-Tenant-Id": "tenant-a", "X-Roles": "editor"},
        json={"title": "Obligacion editable", "description": "Preparada por perfil editor."},
    )
    assert obligation.status_code == 200
    forbidden_validation = client.patch(
        f"/obligations/{obligation.json()['obligation']['id']}",
        headers={"X-User-Id": "editor", "X-Tenant-Id": "tenant-a", "X-Roles": "editor"},
        json={"validation_status": "validated"},
    )
    assert forbidden_validation.status_code == 403
    assert forbidden_validation.json()["detail"] == "permission_required:validate"

    forbidden_export = client.get(
        f"/contracts/{contract_id}/export.zip",
        headers={"X-User-Id": "reader", "X-Tenant-Id": "tenant-a", "X-Roles": "consulta"},
    )
    assert forbidden_export.status_code == 403
    assert forbidden_export.json()["detail"] == "permission_required:export"

    forbidden_service_return = client.get(
        "/service-return/export.zip",
        headers={"X-User-Id": "reader", "X-Tenant-Id": "tenant-a", "X-Roles": "consulta"},
    )
    assert forbidden_service_return.status_code == 403
    assert forbidden_service_return.json()["detail"] == "permission_required:export"

    allowed_export = client.get(
        f"/contracts/{contract_id}/export",
        headers={"X-User-Id": "auditor", "X-Tenant-Id": "tenant-a", "X-Roles": "intervencion"},
    )
    assert allowed_export.status_code == 200
    allowed_service_return = client.get(
        "/service-return/export",
        headers={"X-User-Id": "auditor", "X-Tenant-Id": "tenant-a", "X-Roles": "intervencion"},
    )
    assert allowed_service_return.status_code == 200
    assert all(item["tenant_id"] == "tenant-a" for item in allowed_service_return.json()["contracts"])

    forbidden_data_resolution = client.patch(
        "/data-protection/not-found",
        headers={"X-User-Id": "editor", "X-Tenant-Id": "tenant-a", "X-Roles": "editor"},
        json={"status": "resolved"},
    )
    assert forbidden_data_resolution.status_code == 403
    assert forbidden_data_resolution.json()["detail"] == "permission_required:validate"


def test_contract_control_filters_comments_alert_rules_and_export() -> None:
    headers = {"X-User-Id": "control-user", "X-Tenant-Id": "control-tenant", "X-Roles": "responsable_contrato"}
    first = client.post(
        "/contracts",
        headers=headers,
        json={
            "title": "Servicio con decision pendiente",
            "status": "active",
            "renewal_status": "will_extend",
            "decision_due_date": "2027-05-31",
            "tags": ["prioritario"],
        },
    )
    second = client.post(
        "/contracts",
        headers=headers,
        json={"title": "Servicio finalizado", "status": "completed", "renewal_status": "finished"},
    )
    assert first.status_code == 200
    assert second.status_code == 200
    contract_id = first.json()["contract"]["id"]

    filtered = client.get(
        "/contracts",
        headers=headers,
        params={"status": "active", "renewal_status": "will_extend", "query": "decision pendiente"},
    )
    assert filtered.status_code == 200
    assert [item["id"] for item in filtered.json()["items"]] == [contract_id]

    comment = client.post(
        f"/contracts/{contract_id}/comments",
        headers=headers,
        json={"body": "Revisar la continuidad con la unidad responsable."},
    )
    assert comment.status_code == 200
    assert client.get(f"/contracts/{contract_id}/comments", headers=headers).json()["items"]

    rule = client.post(
        "/alert-rules",
        headers=headers,
        json={"name": "Decision de continuidad", "filters": {"renewal_status": "will_extend"}, "lead_days": 45, "shared": True},
    )
    assert rule.status_code == 200
    assert rule.json()["alert_rule"]["filters"]["renewal_status"] == "will_extend"

    exported = client.get(f"/contracts/{contract_id}/export", headers=headers)
    assert exported.status_code == 200
    assert exported.json()["comments"][0]["body"].startswith("Revisar")

    exported_zip = client.get(f"/contracts/{contract_id}/export.zip", headers=headers)
    assert exported_zip.status_code == 200
    with zipfile.ZipFile(io.BytesIO(exported_zip.content)) as archive:
        assert "comments.json" in archive.namelist()
