from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Locale = Literal["es", "ca", "va", "gl", "eu"]
ContractStatus = Literal["draft", "active", "completed", "liquidated", "resolved", "archived"]
RenewalStatus = Literal["undefined", "will_extend", "extended", "retender", "no_renewal", "finished", "cancelled"]
ObligationCategory = Literal["deadline", "delivery", "sla", "special_condition", "warranty", "payment", "documentation", "extension", "other"]
Severity = Literal["baja", "media", "alta", "critica"]
ObligationStatus = Literal["draft", "pending", "met", "breached", "waived"]
ValidationStatus = Literal["draft", "validated", "rejected"]
AlertStatus = Literal["open", "snoozed", "done", "dismissed"]
ComplianceResult = Literal["compliant", "at_risk", "breach", "needs_review"]
InvoiceStatus = Literal["draft", "registered", "conforming", "rejected", "payment_ordered", "paid"]
ProceedingType = Literal["penalty", "resolution"]
ProceedingStatus = Literal["draft", "opened", "instruction", "hearing", "proposal", "resolved", "closed", "rejected"]
ChangeType = Literal["modification", "extension"]
ChangeStatus = Literal["draft", "under_review", "validated", "applied", "rejected"]
FeedbackRating = Literal["positive", "negative", "neutral"]
FeedbackArtifactType = Literal["obligation", "check", "document", "penalty", "invoice", "change", "proceeding", "task", "other"]
DataProtectionStatus = Literal["draft", "resolved", "accepted_risk", "false_positive"]
GeneratedDocumentType = Literal[
    "recepcion_acta",
    "liquidacion_informe",
    "modificacion_informe_juridico",
    "prorroga_informe_juridico",
    "penalidad_expediente",
    "resolucion_expediente",
]


class UserContext(BaseModel):
    user_id: str
    tenant_id: str
    roles: list[str]


class ContractCreate(BaseModel):
    title: str
    file_number: str | None = None
    contracting_body: str | None = None
    contractor: str | None = None
    responsible_unit: str | None = None
    contract_manager: str | None = None
    contract_type: str | None = None
    procedure: str | None = None
    cpv_codes: list[str] = Field(default_factory=list)
    status: ContractStatus = "draft"
    renewal_status: RenewalStatus = "undefined"
    budget_without_tax: float | None = None
    budget_with_tax: float | None = None
    awarded_amount: float | None = None
    currency: str = "EUR"
    start_date: str | None = None
    end_date: str | None = None
    warranty_end_date: str | None = None
    extension_deadline: str | None = None
    guarantee_amount: float | None = None
    decision_due_date: str | None = None
    tags: list[str] = Field(default_factory=list)
    data: dict[str, Any] = Field(default_factory=dict)


class ContractUpdate(BaseModel):
    title: str | None = None
    file_number: str | None = None
    contracting_body: str | None = None
    contractor: str | None = None
    responsible_unit: str | None = None
    contract_manager: str | None = None
    contract_type: str | None = None
    procedure: str | None = None
    cpv_codes: list[str] | None = None
    status: ContractStatus | None = None
    renewal_status: RenewalStatus | None = None
    budget_without_tax: float | None = None
    budget_with_tax: float | None = None
    awarded_amount: float | None = None
    currency: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    warranty_end_date: str | None = None
    extension_deadline: str | None = None
    guarantee_amount: float | None = None
    decision_due_date: str | None = None
    tags: list[str] | None = None
    data: dict[str, Any] | None = None


class ImportXtenderRequest(BaseModel):
    workspace_id: str


class ImportPcspRequest(BaseModel):
    tender_id: str


class ImportXreviewRequest(BaseModel):
    handoff_id: str


class ObligationCreate(BaseModel):
    category: ObligationCategory = "other"
    title: str
    description: str
    source_refs: list[dict[str, Any]] = Field(default_factory=list)
    due_date: str | None = None
    recurrence: str | None = None
    severity: Severity = "media"
    status: ObligationStatus = "pending"
    validation_status: ValidationStatus = "draft"


class ObligationUpdate(BaseModel):
    category: ObligationCategory | None = None
    title: str | None = None
    description: str | None = None
    source_refs: list[dict[str, Any]] | None = None
    due_date: str | None = None
    recurrence: str | None = None
    severity: Severity | None = None
    status: ObligationStatus | None = None
    validation_status: ValidationStatus | None = None


class AlertUpdate(BaseModel):
    status: AlertStatus | None = None
    due_date: str | None = None
    lead_days: int | None = Field(default=None, ge=0, le=365)


class ContractCommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=10000)


class AlertRuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    filters: dict[str, Any] = Field(default_factory=dict)
    lead_days: int = Field(default=30, ge=0, le=365)
    shared: bool = False


class EvidenceCreate(BaseModel):
    obligation_id: str | None = None
    title: str
    evidence_type: str = "document"
    original_filename: str | None = None
    object_key: str | None = None
    content_hash: str | None = None
    extracted_text: str | None = None
    source_url: str | None = None


class EvidenceUpdate(BaseModel):
    obligation_id: str | None = None


class OfferRiskAnalysisRequest(BaseModel):
    evidence_id: str


class ContractRiskUpdate(BaseModel):
    validation_status: ValidationStatus | None = None


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    due_date: str | None = None
    owner_user_id: str | None = None
    severity: Severity = "media"
    status: Literal["todo", "doing", "done", "dismissed"] = "todo"
    source_type: str | None = None
    source_id: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    due_date: str | None = None
    owner_user_id: str | None = None
    severity: Severity | None = None
    status: Literal["todo", "doing", "done", "dismissed"] | None = None


class InvoiceCreate(BaseModel):
    obligation_id: str | None = None
    invoice_number: str
    supplier: str | None = None
    concept: str
    invoice_date: str | None = None
    service_period_start: str | None = None
    service_period_end: str | None = None
    amount_without_tax: float = Field(ge=0)
    tax_amount: float = Field(default=0, ge=0)
    amount_with_tax: float | None = Field(default=None, ge=0)
    currency: str = "EUR"
    evidence_ids: list[str] = Field(default_factory=list)
    payment_due_date: str | None = None
    notes: str | None = None


class InvoiceUpdate(BaseModel):
    obligation_id: str | None = None
    invoice_number: str | None = None
    supplier: str | None = None
    concept: str | None = None
    invoice_date: str | None = None
    service_period_start: str | None = None
    service_period_end: str | None = None
    amount_without_tax: float | None = Field(default=None, ge=0)
    tax_amount: float | None = Field(default=None, ge=0)
    amount_with_tax: float | None = Field(default=None, ge=0)
    currency: str | None = None
    evidence_ids: list[str] | None = None
    payment_due_date: str | None = None
    paid_at: str | None = None
    notes: str | None = None
    status: InvoiceStatus | None = None


class ContractChangeCreate(BaseModel):
    change_type: ChangeType = "extension"
    title: str | None = None
    reason: str
    legal_basis: str | None = None
    impact_summary: str | None = None
    amount_delta: float | None = None
    proposed_start_date: str | None = None
    proposed_end_date: str | None = None
    extension_months: int | None = Field(default=None, ge=0, le=120)
    source_refs: list[dict[str, Any]] = Field(default_factory=list)
    notes: str | None = None


class ContractChangeUpdate(BaseModel):
    title: str | None = None
    reason: str | None = None
    legal_basis: str | None = None
    impact_summary: str | None = None
    amount_delta: float | None = None
    proposed_start_date: str | None = None
    proposed_end_date: str | None = None
    extension_months: int | None = Field(default=None, ge=0, le=120)
    source_refs: list[dict[str, Any]] | None = None
    document_id: str | None = None
    status: ChangeStatus | None = None
    notes: str | None = None


class ComplianceCheckRequest(BaseModel):
    obligation_id: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)


class GeneratedDocumentRequest(BaseModel):
    document_type: GeneratedDocumentType
    language: Locale = "es"
    notes: str | None = None


class PenaltyCalculationRequest(BaseModel):
    obligation_id: str | None = None
    case_type: Literal["penalty", "resolution"] = "penalty"
    basis_text: str
    daily_amount: float | None = Field(default=None, ge=0)
    days_late: int | None = Field(default=None, ge=0)
    base_amount: float | None = Field(default=None, ge=0)
    percentage: float | None = Field(default=None, ge=0)
    cap_amount: float | None = Field(default=None, ge=0)


class ProceedingCreate(BaseModel):
    case_type: ProceedingType = "penalty"
    penalty_case_id: str | None = None
    title: str | None = None
    trigger_text: str
    legal_basis: str | None = None
    proposed_action: str | None = None
    due_date: str | None = None
    document_ids: list[str] = Field(default_factory=list)


class ProceedingUpdate(BaseModel):
    status: ProceedingStatus | None = None
    title: str | None = None
    summary: str | None = None
    legal_basis: str | None = None
    proposed_action: str | None = None
    due_date: str | None = None
    document_ids: list[str] | None = None
    comment: str | None = None


class FeedbackCreate(BaseModel):
    contract_id: str | None = None
    artifact_type: FeedbackArtifactType = "other"
    artifact_id: str | None = None
    rating: FeedbackRating = "neutral"
    comment: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DataProtectionAssessmentUpdate(BaseModel):
    status: DataProtectionStatus = "resolved"
    resolution_comment: str | None = None


class ResolutionRequest(BaseModel):
    status: ValidationStatus | Literal["opened", "resolved"] = "validated"
    comment: str | None = None
