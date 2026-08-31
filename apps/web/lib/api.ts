export type Contract = {
  id: string;
  tenant_id?: string;
  source_kind: "manual" | "xtender" | "pcsp" | "xreview";
  source_id?: string | null;
  xreview_procedure_id?: string | null;
  xreview_lot_id?: string | null;
  xreview_submission_id?: string | null;
  file_number?: string | null;
  title: string;
  contracting_body?: string | null;
  contractor?: string | null;
  responsible_unit?: string | null;
  contract_manager?: string | null;
  contract_type?: string | null;
  procedure?: string | null;
  cpv_codes: string[];
  status: "draft" | "active" | "completed" | "liquidated" | "resolved" | "archived";
  renewal_status?: "undefined" | "will_extend" | "extended" | "retender" | "no_renewal" | "finished" | "cancelled";
  budget_without_tax?: number | null;
  budget_with_tax?: number | null;
  awarded_amount?: number | null;
  currency?: string;
  start_date?: string | null;
  end_date?: string | null;
  warranty_end_date?: string | null;
  extension_deadline?: string | null;
  guarantee_amount?: number | null;
  decision_due_date?: string | null;
  tags?: string[];
  archived_at?: string | null;
  counts?: {
    obligations: number;
    open_alerts: number;
    evidence: number;
    checks: number;
    penalties: number;
    invoices?: number;
    pending_invoices?: number;
    open_proceedings?: number;
    open_changes?: number;
    open_tasks?: number;
    data_protection_open?: number;
  };
};

export type Obligation = {
  id: string;
  contract_id: string;
  category: string;
  title: string;
  description: string;
  due_date?: string | null;
  severity: "baja" | "media" | "alta" | "critica";
  status: string;
  validation_status: "draft" | "validated" | "rejected";
};

export type Alert = {
  id: string;
  contract_id: string;
  obligation_id?: string | null;
  alert_type: string;
  title: string;
  due_date: string;
  lead_days: number;
  severity: "baja" | "media" | "alta" | "critica";
  status: string;
};

export type Evidence = {
  id: string;
  contract_id: string;
  obligation_id?: string | null;
  title: string;
  evidence_type: string;
  original_filename?: string | null;
  object_key?: string | null;
  content_hash?: string | null;
  extracted_text?: string | null;
  source_url?: string | null;
  status?: "available" | "excluded" | "error";
  uploaded_by?: string | null;
  created_at?: string;
};

export type AiJob = {
  id: string;
  contract_id: string;
  job_type: "obligations_extract" | "compliance_check" | "document_generate" | "change_report" | "offer_risk_analysis";
  status: "queued" | "running" | "retrying" | "completed" | "failed";
  attempts: number;
  next_run_at?: string;
  last_error?: string | null;
  result?: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
};

export type ComplianceCheck = {
  id: string;
  contract_id: string;
  obligation_id?: string | null;
  result: "compliant" | "at_risk" | "breach" | "needs_review";
  reasoning: string;
  status: string;
  created_at?: string;
};

export type ContractRisk = {
  id: string;
  contract_id: string;
  offer_evidence_id?: string | null;
  risk_type: "scope" | "schedule" | "resources" | "quality" | "economic" | "legal" | "other";
  title: string;
  description: string;
  comparison?: string | null;
  severity: "baja" | "media" | "alta" | "critica";
  citations: Array<{ evidence_id: string; title?: string | null }>;
  validation_status: "draft" | "validated" | "rejected";
  created_at?: string;
};

export type DataProtectionAssessment = {
  id: string;
  contract_id: string;
  evidence_id?: string | null;
  scope: "contract" | "evidence";
  source_title: string;
  result: "clear" | "personal_data" | "confidential" | "mixed" | "needs_review";
  severity: "baja" | "media" | "alta" | "critica";
  findings: Array<{
    kind: "personal_data" | "confidential";
    label: string;
    severity: "baja" | "media" | "alta" | "critica";
    match_hash: string;
    snippet: string;
  }>;
  redacted_preview: string;
  recommendation: string;
  status: "draft" | "resolved" | "accepted_risk" | "false_positive";
  resolved_by?: string | null;
  resolved_at?: string | null;
  resolution_comment?: string | null;
  created_at?: string;
};

export type GeneratedDocument = {
  id: string;
  contract_id: string;
  document_type: string;
  title: string;
  content_text: string;
  status: string;
  created_at?: string;
};

export type PenaltyCase = {
  id: string;
  contract_id: string;
  calculated_amount: number;
  basis_text: string;
  calculation: { method: string; raw_amount: number; cap_amount?: number | null; requires_human_validation: boolean };
  status: string;
  created_at?: string;
};

export type ContractInvoice = {
  id: string;
  contract_id: string;
  obligation_id?: string | null;
  invoice_number: string;
  supplier?: string | null;
  concept: string;
  invoice_date?: string | null;
  service_period_start?: string | null;
  service_period_end?: string | null;
  amount_without_tax: number;
  tax_amount: number;
  amount_with_tax: number;
  currency: string;
  status: "draft" | "registered" | "conforming" | "rejected" | "payment_ordered" | "paid";
  evidence_ids?: string[];
  payment_due_date?: string | null;
  paid_at?: string | null;
  notes?: string | null;
};

export type LiquidationSummary = {
  awarded_amount: number;
  invoiced_amount: number;
  conforming_amount: number;
  paid_amount: number;
  pending_payment_amount: number;
  validated_penalties_amount: number;
  settlement_balance: number;
  remaining_authorized_budget?: number | null;
  draft_obligations: number;
  risky_checks: number;
  open_proceedings: number;
  open_changes?: number;
  warnings: string[];
  requires_human_validation: boolean;
};

export type ContractProceeding = {
  id: string;
  contract_id: string;
  penalty_case_id?: string | null;
  case_type: "penalty" | "resolution";
  title: string;
  summary: string;
  legal_basis?: string | null;
  proposed_action?: string | null;
  status: "draft" | "opened" | "instruction" | "hearing" | "proposal" | "resolved" | "closed" | "rejected";
  due_date?: string | null;
  document_ids?: string[];
  timeline?: Array<{ at: string; status: string; user_id: string; comment?: string | null }>;
  created_at?: string;
};

export type ContractChange = {
  id: string;
  contract_id: string;
  change_type: "modification" | "extension";
  title: string;
  reason: string;
  legal_basis?: string | null;
  impact_summary?: string | null;
  amount_delta?: number | null;
  proposed_start_date?: string | null;
  proposed_end_date?: string | null;
  extension_months?: number | null;
  document_id?: string | null;
  ai_draft: boolean;
  status: "draft" | "under_review" | "validated" | "applied" | "rejected";
  notes?: string | null;
  created_at?: string;
};

export type AiFeedback = {
  id: string;
  contract_id?: string | null;
  artifact_type: string;
  artifact_id?: string | null;
  rating: "positive" | "negative" | "neutral";
  comment?: string | null;
  created_at?: string;
};

export type AuditEvent = {
  id: string;
  contract_id?: string | null;
  user_id?: string | null;
  action: string;
  trace_id: string;
  payload: Record<string, unknown>;
  created_at?: string;
};

export type GovernanceManifest = {
  generated_at: string;
  runtime: Record<string, unknown>;
  ai: {
    model: string;
    user_disclosure: string;
    generated_content_label: string;
    limitations: string[];
  };
  human_oversight: {
    default_state: string;
    validation_required_for: string[];
    feedback_enabled: boolean;
  };
  security: {
    auth_mode: string;
    permissions: Record<string, string[]>;
    export_requires_permission: string;
    sensitive_actions_require_permission: string;
    tenant_isolation: string;
  };
  data_governance: Record<string, unknown>;
  service_return: {
    formats: string[];
    included: string[];
  };
};

export type ContractGovernance = {
  manifest: GovernanceManifest;
  audit_summary: {
    events: number;
    actions: Record<string, number>;
    last_event_at?: string | null;
  };
  feedback_summary: {
    items: number;
    ratings: Record<string, number>;
  };
};

export type ContractTask = {
  id: string;
  contract_id: string;
  source_type?: string | null;
  source_id?: string | null;
  title: string;
  description?: string | null;
  due_date?: string | null;
  owner_user_id?: string | null;
  severity: "baja" | "media" | "alta" | "critica";
  status: "todo" | "doing" | "done" | "dismissed";
  completed_by?: string | null;
};

export type ContractComment = {
  id: string;
  contract_id: string;
  body: string;
  created_by?: string | null;
  created_at?: string;
};

export type AlertRule = {
  id: string;
  name: string;
  filters: Record<string, unknown>;
  lead_days: number;
  enabled: boolean;
  shared: boolean;
};

export type XtenderWorkspace = {
  id: string;
  title: string;
  unit?: string | null;
  status?: string | null;
  data?: Record<string, unknown>;
};

export type PcspTender = {
  id: string;
  expediente?: string | null;
  title: string;
};

export type XreviewAward = {
  id: string;
  procedure_id: string;
  lot_id: string;
  status: "published";
  immutable: true;
  imported_contract_id?: string | null;
  procedure?: { title?: string; file_number?: string; contracting_body?: string };
  lot?: { code?: string; title?: string; budget_without_tax?: number };
  bidder?: { name?: string; tax_id?: string };
  awarded_amount?: number | null;
  result?: { total_score?: string; eligible?: boolean };
};

const API_BASE = process.env.NEXT_PUBLIC_XFOLLOW_API_BASE_URL || "http://localhost:8101";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {})
    },
    cache: "no-store"
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: string } | null;
    const detail = body?.detail ? `: ${body.detail}` : "";
    throw new Error(`${response.status} ${response.statusText}${detail}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string; db_backend: string; db?: Record<string, unknown>; llm?: { configured: boolean; available: boolean; model?: string | null; error?: string | null; context_window?: number | null }; integrations?: Record<string, unknown> }>("/health"),
  contracts: (filters: { query?: string; status?: string; renewal_status?: string; responsible_unit?: string; contractor?: string } = {}) => {
    const params = new URLSearchParams({ include_archived: "true" });
    Object.entries(filters).forEach(([key, value]) => value && params.set(key, value));
    return request<{ items: Contract[]; summary: Record<string, number> }>(`/contracts?${params.toString()}`);
  },
  comments: (contractId: string) => request<{ items: ContractComment[] }>(`/contracts/${contractId}/comments`),
  addComment: (contractId: string, body: string) => request<{ comment: ContractComment }>(`/contracts/${contractId}/comments`, { method: "POST", body: JSON.stringify({ body }) }),
  alertRules: () => request<{ items: AlertRule[] }>("/alert-rules"),
  createAlertRule: (name: string, filters: Record<string, unknown>, leadDays = 30, shared = true) => request<{ alert_rule: AlertRule }>("/alert-rules", {
    method: "POST",
    body: JSON.stringify({ name, filters, lead_days: leadDays, shared })
  }),
  xtenderCandidates: (query = "") => request<{ items: XtenderWorkspace[] }>(`/integrations/xtender/workspaces${query ? `?${new URLSearchParams({ query }).toString()}` : ""}`),
  pcspCandidates: () => request<{ items: PcspTender[] }>("/integrations/pcsp/tenders"),
  xreviewCandidates: (query = "") => request<{ items: XreviewAward[] }>(`/integrations/xreview/awards${query ? `?${new URLSearchParams({ query }).toString()}` : ""}`),
  importXtender: (workspaceId: string) => request<{ contract: Contract; draft_obligations?: Obligation[]; created: boolean }>("/contracts/import/xtender", { method: "POST", body: JSON.stringify({ workspace_id: workspaceId }) }),
  importPcsp: (tenderId: string) => request<{ contract: Contract; draft_obligations?: Obligation[]; created: boolean }>("/contracts/import/pcsp", { method: "POST", body: JSON.stringify({ tender_id: tenderId }) }),
  importXreview: (handoffId: string) => request<{ contract: Contract; accepted_obligations: Obligation[]; winning_offer_evidence: Evidence[]; basis_evidence: Evidence[]; created: boolean }>("/contracts/import/xreview", { method: "POST", body: JSON.stringify({ handoff_id: handoffId }) }),
  obligations: (contractId: string) => request<{ items: Obligation[] }>(`/contracts/${contractId}/obligations`),
  extractObligations: (contractId: string) => request<{ job: AiJob }>(`/contracts/${contractId}/obligations/extract`, { method: "POST" }),
  validateObligation: (id: string) => request<{ obligation: Obligation }>(`/obligations/${id}`, { method: "PATCH", body: JSON.stringify({ validation_status: "validated" }) }),
  alerts: (contractId: string) => request<{ items: Alert[] }>(`/contracts/${contractId}/alerts`),
  tasks: (contractId: string) => request<{ items: ContractTask[] }>(`/contracts/${contractId}/tasks`),
  generateTasks: (contractId: string) => request<{ items: ContractTask[] }>(`/contracts/${contractId}/tasks/generate`, { method: "POST" }),
  completeTask: (taskId: string) => request<{ task: ContractTask }>(`/tasks/${taskId}`, { method: "PATCH", body: JSON.stringify({ status: "done" }) }),
  evidence: (contractId: string) => request<{ items: Evidence[] }>(`/contracts/${contractId}/evidence`),
  addEvidence: (contractId: string, obligationId?: string) =>
    request<{ evidence: Evidence }>(`/contracts/${contractId}/evidence`, {
      method: "POST",
      body: JSON.stringify({
        obligation_id: obligationId,
        title: "Parte de servicio validado",
        extracted_text: "La prestacion se ha entregado y cumple lo requerido, pendiente de conformidad final."
      })
    }),
  uploadEvidence: async (contractId: string, file: File, obligationId?: string, evidenceType = "document") => {
    const form = new FormData();
    form.append("file", file);
    form.append("title", file.name);
    form.append("evidence_type", evidenceType);
    if (obligationId) form.append("obligation_id", obligationId);
    const response = await fetch(`${API_BASE}/contracts/${contractId}/evidence/upload`, {
      method: "POST",
      body: form
    });
    if (!response.ok) {
      throw new Error(`${response.status} ${response.statusText}`);
    }
    return response.json() as Promise<{ evidence: Evidence }>;
  },
  updateEvidence: (evidenceId: string, obligationId?: string | null) => request<{ evidence: Evidence }>(`/evidence/${evidenceId}`, {
    method: "PATCH",
    body: JSON.stringify({ obligation_id: obligationId ?? null })
  }),
  risks: (contractId: string) => request<{ items: ContractRisk[] }>(`/contracts/${contractId}/risks`),
  analyzeWinningOffer: (contractId: string, evidenceId: string) => request<{ job: AiJob }>(`/contracts/${contractId}/offer-analysis`, { method: "POST", body: JSON.stringify({ evidence_id: evidenceId }) }),
  validateRisk: (riskId: string) => request<{ risk: ContractRisk }>(`/risks/${riskId}`, { method: "PATCH", body: JSON.stringify({ validation_status: "validated" }) }),
  aiJobs: (contractId: string) => request<{ items: AiJob[] }>(`/contracts/${contractId}/ai-jobs`),
  retryAiJob: (jobId: string) => request<{ job: AiJob }>(`/ai-jobs/${jobId}/retry`, { method: "POST" }),
  dataProtection: (contractId: string) => request<{ items: DataProtectionAssessment[] }>(`/contracts/${contractId}/data-protection`),
  scanDataProtection: (contractId: string) => request<{ items: DataProtectionAssessment[] }>(`/contracts/${contractId}/data-protection/scan`, { method: "POST" }),
  resolveDataProtection: (assessmentId: string) =>
    request<{ assessment: DataProtectionAssessment }>(`/data-protection/${assessmentId}`, {
      method: "PATCH",
      body: JSON.stringify({ status: "resolved", resolution_comment: "Revisado desde xFollow" })
    }),
  checks: (contractId: string) => request<{ items: ComplianceCheck[] }>(`/contracts/${contractId}/checks`),
  runChecks: (contractId: string, obligationId?: string) => request<{ job: AiJob }>(`/contracts/${contractId}/checks/run`, { method: "POST", body: JSON.stringify({ obligation_id: obligationId }) }),
  resolveCheck: (checkId: string) => request<{ check: ComplianceCheck }>(`/checks/${checkId}/resolve`, { method: "PATCH", body: JSON.stringify({ status: "validated" }) }),
  feedback: (contractId: string) => request<{ items: AiFeedback[] }>(`/contracts/${contractId}/feedback`),
  sendFeedback: (contractId: string, artifactType: string, artifactId?: string, rating: "positive" | "negative" | "neutral" = "positive") =>
    request<{ feedback: AiFeedback }>("/feedback", {
      method: "POST",
      body: JSON.stringify({
        contract_id: contractId,
        artifact_type: artifactType,
        artifact_id: artifactId,
        rating,
        comment: rating === "positive" ? "Resultado util tras revision." : "Resultado a mejorar."
      })
    }),
  governanceManifest: () => request<GovernanceManifest>("/governance/manifest"),
  audit: (contractId: string) => request<{ items: AuditEvent[] }>(`/contracts/${contractId}/audit`),
  governance: (contractId: string) => request<ContractGovernance>(`/contracts/${contractId}/governance`),
  invoices: (contractId: string) => request<{ items: ContractInvoice[] }>(`/contracts/${contractId}/invoices`),
  createInvoice: (contractId: string, obligationId?: string, evidenceId?: string) =>
    request<{ invoice: ContractInvoice }>(`/contracts/${contractId}/invoices`, {
      method: "POST",
      body: JSON.stringify({
        obligation_id: obligationId,
        invoice_number: `F-${new Date().toISOString().slice(0, 10).replace(/-/g, "")}`,
        concept: "Servicio conformable de ejecucion contractual",
        invoice_date: new Date().toISOString().slice(0, 10),
        service_period_start: "2026-08-01",
        service_period_end: "2026-08-31",
        amount_without_tax: 1000,
        tax_amount: 210,
        evidence_ids: evidenceId ? [evidenceId] : []
      })
    }),
  conformInvoice: (invoiceId: string) => request<{ invoice: ContractInvoice }>(`/invoices/${invoiceId}`, { method: "PATCH", body: JSON.stringify({ status: "conforming" }) }),
  payInvoice: (invoiceId: string) => request<{ invoice: ContractInvoice }>(`/invoices/${invoiceId}`, { method: "PATCH", body: JSON.stringify({ status: "paid" }) }),
  liquidation: (contractId: string) => request<{ summary: LiquidationSummary }>(`/contracts/${contractId}/liquidation`),
  changes: (contractId: string) => request<{ items: ContractChange[] }>(`/contracts/${contractId}/changes`),
  proposeExtension: (contractId: string) =>
    request<{ change: ContractChange }>(`/contracts/${contractId}/changes`, {
      method: "POST",
      body: JSON.stringify({
        change_type: "extension",
        reason: "Continuidad del servicio mientras se prepara la siguiente licitacion.",
        legal_basis: "Prorroga prevista en el contrato y sujeta a validacion del organo competente.",
        impact_summary: "Amplia el plazo seis meses, manteniendo condiciones de ejecucion y control.",
        amount_delta: 93000,
        extension_months: 6
      })
    }),
  proposeModification: (contractId: string) =>
    request<{ change: ContractChange }>(`/contracts/${contractId}/changes`, {
      method: "POST",
      body: JSON.stringify({
        change_type: "modification",
        reason: "Necesidad sobrevenida detectada durante el seguimiento de la ejecucion.",
        legal_basis: "Modificacion contractual sujeta a informe juridico y validacion.",
        impact_summary: "Ajuste de alcance e importe pendiente de completar por la unidad responsable.",
        amount_delta: 5000
      })
    }),
  generateChangeReport: (changeId: string) => request<{ job: AiJob }>(`/changes/${changeId}/report`, { method: "POST" }),
  validateChange: (changeId: string) => request<{ change: ContractChange }>(`/changes/${changeId}`, { method: "PATCH", body: JSON.stringify({ status: "validated" }) }),
  applyChange: (changeId: string) => request<{ change: ContractChange; contract: Contract }>(`/changes/${changeId}/apply`, { method: "POST" }),
  documents: (contractId: string) => request<{ items: GeneratedDocument[] }>(`/contracts/${contractId}/generated-documents`),
  generateDocument: (contractId: string, documentType = "recepcion_acta") => request<{ job: AiJob }>(`/contracts/${contractId}/generated-documents`, { method: "POST", body: JSON.stringify({ document_type: documentType, language: "es" }) }),
  resolveDocument: (documentId: string) => request<{ document: GeneratedDocument }>(`/generated-documents/${documentId}/resolve`, { method: "PATCH", body: JSON.stringify({ status: "validated" }) }),
  penalties: (contractId: string) => request<{ items: PenaltyCase[] }>(`/contracts/${contractId}/penalty-cases`),
  calculatePenalty: (contractId: string, obligationId?: string) =>
    request<{ penalty_case: PenaltyCase }>(`/contracts/${contractId}/penalty-cases/calculate`, {
      method: "POST",
      body: JSON.stringify({
        obligation_id: obligationId,
        basis_text: "Penalidad diaria por retraso segun clausula de ejecucion.",
        daily_amount: 300,
        days_late: 12,
        cap_amount: 3000
      })
    }),
  resolvePenalty: (penaltyId: string) => request<{ penalty_case: PenaltyCase }>(`/penalty-cases/${penaltyId}/resolve`, { method: "PATCH", body: JSON.stringify({ status: "validated" }) }),
  proceedings: (contractId: string) => request<{ items: ContractProceeding[] }>(`/contracts/${contractId}/proceedings`),
  openProceeding: (contractId: string, penaltyId?: string) =>
    request<{ proceeding: ContractProceeding }>(`/contracts/${contractId}/proceedings`, {
      method: "POST",
      body: JSON.stringify({
        case_type: penaltyId ? "penalty" : "resolution",
        penalty_case_id: penaltyId,
        trigger_text: penaltyId ? "Incumplimiento con penalidad calculada pendiente de tramitacion." : "Riesgo de resolucion contractual detectado durante el seguimiento.",
        legal_basis: "Clausulas de ejecucion y regimen de penalidades/resolucion del contrato.",
        proposed_action: "Abrir expediente, recabar informe de la unidad responsable y conceder audiencia.",
        due_date: "2026-10-15"
      })
    }),
  advanceProceeding: (proceedingId: string) => request<{ proceeding: ContractProceeding }>(`/proceedings/${proceedingId}`, { method: "PATCH", body: JSON.stringify({ status: "hearing", comment: "Audiencia iniciada desde xFollow" }) }),
  documentDocxUrl: (documentId: string) => `${API_BASE}/generated-documents/${documentId}/docx`,
  evidenceDownloadUrl: (evidenceId: string) => `${API_BASE}/evidence/${evidenceId}/download`,
  exportZipUrl: (contractId: string) => `${API_BASE}/contracts/${contractId}/export.zip`,
  serviceReturnZipUrl: () => `${API_BASE}/service-return/export.zip`
};

export function isApiError(error: unknown): error is Error {
  return error instanceof Error;
}
