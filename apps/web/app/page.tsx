"use client";

import clsx from "clsx";
import {
  Archive,
  Bell,
  Bot,
  ClipboardCheck,
  FileCheck2,
  FileText,
  FolderKanban,
  Gavel,
  History,
  Landmark,
  ListChecks,
  Loader2,
  MessageSquare,
  PackagePlus,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  Upload,
  WandSparkles,
  X,
  type LucideIcon
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  api,
  isApiError,
  type AiJob,
  type Alert,
  type AuditEvent,
  type ComplianceCheck,
  type Contract,
  type ContractChange,
  type ContractComment,
  type ContractGovernance,
  type ContractInvoice,
  type ContractProceeding,
  type ContractRisk,
  type ContractTask,
  type DataProtectionAssessment,
  type Evidence,
  type GeneratedDocument,
  type LiquidationSummary,
  type Obligation,
  type PenaltyCase,
  type XtenderWorkspace,
  type XreviewAward
} from "@/lib/api";
import { formatEuro, severityClass, shortDate, statusLabel } from "@/lib/data";

type ModuleId = "contratos" | "obligaciones" | "alertas" | "tareas" | "cumplimiento" | "datos" | "facturas" | "cambios" | "documentos" | "penalidades" | "expedientes" | "gobierno";

type ModuleCopy = {
  label: string;
  title: string;
  subtitle: string;
};

type NewContractStep = "select" | "offer";

const navItems: Array<{ id: ModuleId; icon: LucideIcon }> = [
  { id: "contratos", icon: FolderKanban },
  { id: "obligaciones", icon: ListChecks },
  { id: "alertas", icon: Bell },
  { id: "tareas", icon: ClipboardCheck },
  { id: "cumplimiento", icon: ClipboardCheck },
  { id: "datos", icon: ShieldCheck },
  { id: "facturas", icon: FileCheck2 },
  { id: "cambios", icon: RefreshCw },
  { id: "documentos", icon: FileText },
  { id: "penalidades", icon: Gavel },
  { id: "expedientes", icon: Landmark },
  { id: "gobierno", icon: ShieldCheck }
];

const copy: Record<ModuleId, ModuleCopy> = {
  contratos: {
    label: "Contratos",
    title: "Contratos en ejecucion",
    subtitle: "Inventario operativo conectado a xTender, PCSP y altas manuales."
  },
  obligaciones: {
    label: "Obligaciones",
    title: "Obligaciones y condiciones",
    subtitle: "Hitos, SLA, garantias, prorrogas y condiciones especiales pendientes de validacion."
  },
  alertas: {
    label: "Alertas",
    title: "Vencimientos y preavisos",
    subtitle: "Control de plazos parciales, duracion, prorroga, garantia y evidencias pendientes."
  },
  tareas: {
    label: "Tareas",
    title: "Trabajo interno",
    subtitle: "Acciones asignables derivadas de alertas, obligaciones y revisiones pendientes."
  },
  cumplimiento: {
    label: "Cumplimiento",
    title: "Verificacion con evidencias",
    subtitle: "Contraste trazable entre obligaciones validadas y documentacion aportada."
  },
  datos: {
    label: "Datos",
    title: "Proteccion de datos",
    subtitle: "Escaneo de datos personales, IBAN, telefonos y senales de confidencialidad antes de reutilizar evidencias."
  },
  facturas: {
    label: "Facturas",
    title: "Facturacion y liquidacion",
    subtitle: "Registro, conformidad, pago y resumen economico para cierre del contrato."
  },
  cambios: {
    label: "Cambios",
    title: "Modificaciones y prorrogas",
    subtitle: "Propuestas, informe juridico, validacion y aplicacion controlada al contrato."
  },
  documentos: {
    label: "Documentos",
    title: "Borradores revisables",
    subtitle: "Actas, liquidacion, modificacion, prorroga, penalidad y resolucion."
  },
  penalidades: {
    label: "Penalidades",
    title: "Calculo y expediente",
    subtitle: "Importes, topes, motivacion y tramitacion con validacion humana."
  },
  expedientes: {
    label: "Expedientes",
    title: "Tramitacion guiada",
    subtitle: "Apertura, audiencia, propuesta y resolucion con timeline y documentos asociados."
  },
  gobierno: {
    label: "Gobierno",
    title: "Trazabilidad y control IA",
    subtitle: "Manifiesto operativo, auditoria, permisos, devolucion y feedback del contrato."
  }
};

const fallbackContracts: Contract[] = [
  {
    id: "CTR-DEMO",
    source_kind: "xtender",
    source_id: "EXP-DEMO-XTENDER",
    file_number: "2026/SERV/310",
    title: "Servicio de mantenimiento integral de edificios",
    contracting_body: "Ayuntamiento demo",
    contractor: "Servicios Urbanos Demo SL",
    responsible_unit: "Servicios Generales",
    contract_manager: "Responsable del contrato",
    contract_type: "Servicios",
    procedure: "Abierto",
    cpv_codes: ["50700000-2"],
    status: "active",
    start_date: "2026-08-01",
    end_date: "2027-07-31",
    warranty_end_date: "2027-10-31",
    extension_deadline: "2027-05-31",
    awarded_amount: 186000,
    counts: { obligations: 4, open_alerts: 3, evidence: 1, checks: 1, penalties: 1, invoices: 1, pending_invoices: 1, open_proceedings: 1, open_changes: 1, open_tasks: 1, data_protection_open: 1 }
  }
];

const fallbackObligations: Obligation[] = [
  { id: "OBL-1", contract_id: "CTR-DEMO", category: "deadline", title: "Fin de ejecucion contractual", description: "Preparar recepcion y continuidad del servicio.", due_date: "2027-07-31", severity: "alta", status: "pending", validation_status: "validated" },
  { id: "OBL-2", contract_id: "CTR-DEMO", category: "extension", title: "Preaviso y decision de prorroga", description: "Revisar la prorroga antes del vencimiento.", due_date: "2027-05-31", severity: "media", status: "pending", validation_status: "draft" },
  { id: "OBL-3", contract_id: "CTR-DEMO", category: "special_condition", title: "Plan preventivo mensual", description: "Entrega mensual de partes e indicadores.", severity: "alta", status: "pending", validation_status: "draft" }
];

const fallbackAlerts: Alert[] = [
  { id: "ALT-1", contract_id: "CTR-DEMO", obligation_id: "OBL-2", alert_type: "extension", title: "Preaviso y decision de prorroga", due_date: "2027-05-31", lead_days: 30, severity: "media", status: "open" },
  { id: "ALT-2", contract_id: "CTR-DEMO", obligation_id: "OBL-1", alert_type: "deadline", title: "Fin de ejecucion contractual", due_date: "2027-07-31", lead_days: 30, severity: "alta", status: "open" }
];

const fallbackTasks: ContractTask[] = [
  { id: "TSK-1", contract_id: "CTR-DEMO", source_type: "alert", source_id: "ALT-1", title: "Preparar decision de prorroga", description: "Revisar continuidad, informe y preaviso.", due_date: "2027-05-31", severity: "media", status: "todo" }
];

const fallbackEvidence: Evidence[] = [
  { id: "EVD-1", contract_id: "CTR-DEMO", obligation_id: "OBL-1", title: "Parte mensual recibido", evidence_type: "document", extracted_text: "La prestacion cumple lo requerido.", created_at: "2026-07-13T10:00:00Z" }
];

const fallbackChecks: ComplianceCheck[] = [
  { id: "CHK-1", contract_id: "CTR-DEMO", obligation_id: "OBL-1", result: "compliant", reasoning: "La evidencia aportada parece respaldar el cumplimiento, pendiente de validacion humana.", status: "draft" }
];

const fallbackDataProtection: DataProtectionAssessment[] = [
  {
    id: "DPT-1",
    contract_id: "CTR-DEMO",
    evidence_id: "EVD-1",
    scope: "evidence",
    source_title: "Informe mensual con anexos",
    result: "mixed",
    severity: "critica",
    findings: [
      { kind: "personal_data", label: "email", severity: "media", match_hash: "demo-email", snippet: "Contacto [EMAIL] para incidencias." },
      { kind: "confidential", label: "secreto_tecnico", severity: "critica", match_hash: "demo-secret", snippet: "Retirar [SECRETO_TECNICO] antes de compartir." }
    ],
    redacted_preview: "Informe mensual con anexos. Contacto [EMAIL]. Retirar [SECRETO_TECNICO] antes de compartir.",
    recommendation: "Revisar datos personales y confidencialidad conjuntamente; limitar acceso y documentar decision de tratamiento.",
    status: "draft",
    created_at: "2026-07-13T10:00:00Z"
  }
];

const fallbackDocuments: GeneratedDocument[] = [
  { id: "DOC-1", contract_id: "CTR-DEMO", document_type: "recepcion_acta", title: "Acta de recepcion", content_text: "Borrador generado por xFollow. Requiere revision humana.", status: "draft" }
];

const fallbackPenalties: PenaltyCase[] = [
  { id: "PEN-1", contract_id: "CTR-DEMO", calculated_amount: 3000, basis_text: "Penalidad diaria por retraso.", calculation: { method: "daily_amount_x_days_late", raw_amount: 3600, cap_amount: 3000, requires_human_validation: true }, status: "draft" }
];

const fallbackInvoices: ContractInvoice[] = [
  { id: "INV-1", contract_id: "CTR-DEMO", obligation_id: "OBL-1", invoice_number: "F-2026-0001", supplier: "Servicios Urbanos Demo SL", concept: "Servicio mensual conformable", invoice_date: "2026-09-01", amount_without_tax: 1000, tax_amount: 210, amount_with_tax: 1210, currency: "EUR", status: "conforming", payment_due_date: "2026-10-01" }
];

const fallbackLiquidation: LiquidationSummary = {
  awarded_amount: 186000,
  invoiced_amount: 1210,
  conforming_amount: 1210,
  paid_amount: 0,
  pending_payment_amount: 1210,
  validated_penalties_amount: 3000,
  settlement_balance: -1790,
  remaining_authorized_budget: 184790,
  draft_obligations: 2,
  risky_checks: 0,
  open_proceedings: 1,
  warnings: ["Hay facturas conformadas pendientes de pago", "Hay expedientes abiertos antes del cierre"],
  requires_human_validation: true
};

const fallbackProceedings: ContractProceeding[] = [
  { id: "PRC-1", contract_id: "CTR-DEMO", penalty_case_id: "PEN-1", case_type: "penalty", title: "Expediente de imposicion de penalidad", summary: "Retraso acreditado pendiente de audiencia.", legal_basis: "Clausula de penalidades.", proposed_action: "Conceder audiencia y formular propuesta.", status: "opened", due_date: "2026-10-15", timeline: [{ at: "2026-07-13T10:00:00Z", status: "opened", user_id: "demo-user", comment: "Apertura propuesta." }] }
];

const fallbackChanges: ContractChange[] = [
  { id: "CHG-1", contract_id: "CTR-DEMO", change_type: "extension", title: "Propuesta de prorroga", reason: "Continuidad del servicio.", legal_basis: "Prorroga prevista en contrato.", impact_summary: "Amplia seis meses el contrato.", amount_delta: 93000, proposed_end_date: "2028-01-31", extension_months: 6, document_id: "DOC-1", ai_draft: true, status: "under_review" }
];

const fallbackAudit: AuditEvent[] = [
  { id: "AUD-1", contract_id: "CTR-DEMO", user_id: "demo-user", action: "document.generated", trace_id: "AUD-1", payload: { document_type: "recepcion_acta" }, created_at: "2026-07-13T10:00:00Z" }
];

const fallbackGovernance: ContractGovernance = {
  manifest: {
    generated_at: "2026-07-13T10:00:00Z",
    runtime: { auth_mode: "development_headers" },
    ai: {
      model: "ver_modelo_real_en_destino",
      user_disclosure: "La interfaz informa de que la persona usuaria interactua con asistencia de IA.",
      generated_content_label: "Los documentos y verificaciones se marcan como borradores revisables.",
      limitations: ["No produce actos administrativos por si misma."]
    },
    human_oversight: { default_state: "draft", validation_required_for: ["documentos", "verificaciones"], feedback_enabled: true },
    security: { auth_mode: "development_headers", permissions: { consulta: ["read"] }, export_requires_permission: "export", sensitive_actions_require_permission: "validate", tenant_isolation: "tenant_id obligatorio" },
    data_governance: { postgres_schema: "xfollow" },
    service_return: { formats: ["json", "zip", "docx", "markdown"], included: ["contrato", "auditoria"] }
  },
  audit_summary: { events: 1, actions: { "document.generated": 1 }, last_event_at: "2026-07-13T10:00:00Z" },
  feedback_summary: { items: 0, ratings: {} }
};

export default function Home() {
  const [activeModule, setActiveModule] = useState<ModuleId>("contratos");
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [selectedId, setSelectedId] = useState<string>("");
  const [contractQuery, setContractQuery] = useState("");
  const [contractStatus, setContractStatus] = useState("");
  const [renewalStatus, setRenewalStatus] = useState("");
  const [obligations, setObligations] = useState<Obligation[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [tasks, setTasks] = useState<ContractTask[]>([]);
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [risks, setRisks] = useState<ContractRisk[]>([]);
  const [checks, setChecks] = useState<ComplianceCheck[]>([]);
  const [dataProtection, setDataProtection] = useState<DataProtectionAssessment[]>([]);
  const [invoices, setInvoices] = useState<ContractInvoice[]>([]);
  const [liquidation, setLiquidation] = useState<LiquidationSummary | null>(null);
  const [changes, setChanges] = useState<ContractChange[]>([]);
  const [documents, setDocuments] = useState<GeneratedDocument[]>([]);
  const [penalties, setPenalties] = useState<PenaltyCase[]>([]);
  const [proceedings, setProceedings] = useState<ContractProceeding[]>([]);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [governance, setGovernance] = useState<ContractGovernance | null>(null);
  const [comments, setComments] = useState<ContractComment[]>([]);
  const [summary, setSummary] = useState<Record<string, number>>({});
  const [backend, setBackend] = useState("offline");
  const [llmStatus, setLlmStatus] = useState<{ configured: boolean; available: boolean; model?: string | null; error?: string | null; context_window?: number | null } | null>(null);
  const [aiJobs, setAiJobs] = useState<AiJob[]>([]);
  const [apiError, setApiError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("Listo");
  const [newContractOpen, setNewContractOpen] = useState(false);
  const [newContractStep, setNewContractStep] = useState<NewContractStep>("select");
  const [xtenderQuery, setXtenderQuery] = useState("");
  const [xtenderCandidates, setXtenderCandidates] = useState<XtenderWorkspace[]>([]);
  const [selectedXtenderId, setSelectedXtenderId] = useState("");
  const [xtenderLoading, setXtenderLoading] = useState(false);
  const [newContractBusy, setNewContractBusy] = useState(false);
  const [newContractError, setNewContractError] = useState<string | null>(null);
  const [importedContract, setImportedContract] = useState<Contract | null>(null);
  const [winningOfferFile, setWinningOfferFile] = useState<File | null>(null);
  const [xreviewOpen, setXreviewOpen] = useState(false);
  const [xreviewCandidates, setXreviewCandidates] = useState<XreviewAward[]>([]);
  const [selectedXreviewId, setSelectedXreviewId] = useState("");
  const [xreviewBusy, setXreviewBusy] = useState(false);
  const [xreviewError, setXreviewError] = useState<string | null>(null);

  const selected = useMemo(() => contracts.find((item) => item.id === selectedId) || contracts[0], [contracts, selectedId]);
  const selectedObligation = obligations[0];
  const importedXtenderContracts = useMemo(
    () => new Map(contracts.filter((item) => item.source_kind === "xtender" && item.source_id).map((item) => [item.source_id as string, item])),
    [contracts]
  );

  const selectContract = useCallback((contractId: string) => {
    setSelectedId(contractId);
    if (typeof window !== "undefined") window.localStorage.setItem("xfollow.active_contract_id", contractId);
  }, []);

  const clearDetails = useCallback(() => {
    setObligations([]);
    setAlerts([]);
    setTasks([]);
    setEvidence([]);
    setRisks([]);
    setChecks([]);
    setDataProtection([]);
    setInvoices([]);
    setLiquidation(null);
    setChanges([]);
    setDocuments([]);
    setPenalties([]);
    setProceedings([]);
    setAuditEvents([]);
    setGovernance(null);
    setComments([]);
    setAiJobs([]);
  }, []);

  const loadDetails = useCallback(async (contractId: string) => {
    const [nextObligations, nextAlerts, nextTasks, nextEvidence, nextRisks, nextChecks, nextDataProtection, nextInvoices, nextLiquidation, nextChanges, nextDocuments, nextPenalties, nextProceedings, nextAudit, nextGovernance, nextComments, nextAiJobs] = await Promise.all([
      api.obligations(contractId),
      api.alerts(contractId),
      api.tasks(contractId),
      api.evidence(contractId),
      api.risks(contractId),
      api.checks(contractId),
      api.dataProtection(contractId),
      api.invoices(contractId),
      api.liquidation(contractId),
      api.changes(contractId),
      api.documents(contractId),
      api.penalties(contractId),
      api.proceedings(contractId),
      api.audit(contractId),
      api.governance(contractId),
      api.comments(contractId),
      api.aiJobs(contractId)
    ]);
    setObligations(nextObligations.items);
    setAlerts(nextAlerts.items);
    setTasks(nextTasks.items);
    setEvidence(nextEvidence.items);
    setRisks(nextRisks.items);
    setChecks(nextChecks.items);
    setDataProtection(nextDataProtection.items);
    setInvoices(nextInvoices.items);
    setLiquidation(nextLiquidation.summary);
    setChanges(nextChanges.items);
    setDocuments(nextDocuments.items);
    setPenalties(nextPenalties.items);
    setProceedings(nextProceedings.items);
    setAuditEvents(nextAudit.items);
    setGovernance(nextGovernance);
    setComments(nextComments.items);
    setAiJobs(nextAiJobs.items);
  }, []);

  const loadXtenderCandidates = useCallback(async (query: string) => {
    setXtenderLoading(true);
    setNewContractError(null);
    try {
      const response = await api.xtenderCandidates(query.trim());
      setXtenderCandidates(response.items);
    } catch (error) {
      setXtenderCandidates([]);
      setNewContractError(isApiError(error) ? error.message : "No se pudieron consultar los contratos de xTender");
    } finally {
      setXtenderLoading(false);
    }
  }, []);

  const refresh = useCallback(async () => {
    setBusy(true);
    try {
      const [health, list] = await Promise.all([api.health(), api.contracts({ query: contractQuery, status: contractStatus, renewal_status: renewalStatus })]);
      const items = list.items;
      setBackend(health.db_backend);
      setLlmStatus(health.llm || null);
      setApiError(null);
      setContracts(items);
      setSummary(list.summary || {});
      const storedId = typeof window !== "undefined" ? window.localStorage.getItem("xfollow.active_contract_id") || "" : "";
      const nextSelected = selectedId && items.some((item) => item.id === selectedId) ? selectedId : storedId && items.some((item) => item.id === storedId) ? storedId : items[0]?.id || "";
      selectContract(nextSelected);
      if (nextSelected) {
        await loadDetails(nextSelected);
      } else {
        clearDetails();
      }
      setMessage(items.length ? "Datos sincronizados" : "Sin contratos todavia");
    } catch (error) {
      setBackend("offline");
      setLlmStatus(null);
      setContracts([]);
      setSummary({});
      setSelectedId("");
      clearDetails();
      const detail = isApiError(error) ? error.message : "No se pudo contactar con la API";
      setApiError(detail);
      setMessage(`API no disponible: ${detail}`);
    } finally {
      setBusy(false);
    }
  }, [clearDetails, contractQuery, contractStatus, loadDetails, renewalStatus, selectedId, selectContract]);

  useEffect(() => {
    void refresh();
  }, [contractQuery, contractStatus, renewalStatus]);

  useEffect(() => {
    if (!selected?.id || backend === "offline") return;
    void loadDetails(selected.id).catch((error) => setApiError(isApiError(error) ? error.message : "No se pudieron cargar los datos del contrato"));
  }, [backend, loadDetails, selected?.id]);

  useEffect(() => {
    if (!selected?.id || !aiJobs.some((job) => ["queued", "running", "retrying"].includes(job.status))) return;
    const timer = window.setInterval(() => {
      void loadDetails(selected.id).catch((error) => setApiError(isApiError(error) ? error.message : "No se pudo actualizar el trabajo de IA"));
    }, 3000);
    return () => window.clearInterval(timer);
  }, [aiJobs, loadDetails, selected?.id]);

  useEffect(() => {
    if (!newContractOpen || newContractStep !== "select") return;
    const timer = window.setTimeout(() => void loadXtenderCandidates(xtenderQuery), 200);
    return () => window.clearTimeout(timer);
  }, [loadXtenderCandidates, newContractOpen, newContractStep, xtenderQuery]);

  async function runAction(label: string, action: () => Promise<void>) {
    setBusy(true);
    try {
      await action();
      setMessage(label);
    } catch (error) {
      setMessage(isApiError(error) ? error.message : "No se pudo completar la accion");
    } finally {
      setBusy(false);
    }
  }

  function openNewContract() {
    setNewContractOpen(true);
    setNewContractStep("select");
    setXtenderQuery("");
    setXtenderCandidates([]);
    setSelectedXtenderId("");
    setNewContractError(null);
    setImportedContract(null);
    setWinningOfferFile(null);
  }

  function closeNewContract() {
    if (newContractBusy) return;
    setNewContractOpen(false);
    setNewContractError(null);
    setWinningOfferFile(null);
  }

  function openExistingContract(contractId: string) {
    setNewContractOpen(false);
    setActiveModule("contratos");
    selectContract(contractId);
    setMessage("El contrato ya estaba incorporado; se ha abierto su ficha.");
  }

  async function importSelectedXtender() {
    if (!selectedXtenderId) {
      setNewContractError("Selecciona un contrato de xTender.");
      return;
    }
    setNewContractBusy(true);
    setNewContractError(null);
    try {
      const imported = await api.importXtender(selectedXtenderId);
      await refresh();
      selectContract(imported.contract.id);
      setActiveModule("contratos");
      if (!imported.created) {
        setNewContractOpen(false);
        setMessage("El contrato ya estaba incorporado; se ha abierto su ficha.");
        return;
      }
      setImportedContract(imported.contract);
      setNewContractStep("offer");
      setMessage("Contrato incorporado. Añade la oferta adjudicataria para iniciar el contraste.");
    } catch (error) {
      setNewContractError(isApiError(error) ? error.message : "No se pudo incorporar el contrato de xTender");
    } finally {
      setNewContractBusy(false);
    }
  }

  async function uploadWinningOfferFromIntake() {
    if (!importedContract) return;
    if (!winningOfferFile) {
      setNewContractError("Selecciona la oferta adjudicataria.");
      return;
    }
    setNewContractBusy(true);
    setNewContractError(null);
    try {
      const uploaded = await api.uploadEvidence(importedContract.id, winningOfferFile, undefined, "winning_offer");
      await api.analyzeWinningOffer(importedContract.id, uploaded.evidence.id);
      await refresh();
      selectContract(importedContract.id);
      setActiveModule("documentos");
      setNewContractOpen(false);
      setWinningOfferFile(null);
      setMessage("Oferta adjudicataria incorporada y análisis con IA en cola.");
    } catch (error) {
      setNewContractError(isApiError(error) ? error.message : "No se pudo guardar y analizar la oferta adjudicataria");
    } finally {
      setNewContractBusy(false);
    }
  }

  function skipWinningOfferFromIntake() {
    setNewContractOpen(false);
    setWinningOfferFile(null);
    if (importedContract) selectContract(importedContract.id);
    setMessage("Contrato incorporado. La oferta adjudicataria se puede cargar desde Documentos.");
  }

  async function importPcsp() {
    await runAction("Contrato PCSP importado", async () => {
      const candidates = await api.pcspCandidates();
      const tenderId = candidates.items[0]?.id || "PCSP-DEMO-ADJ";
      const imported = await api.importPcsp(tenderId);
      selectContract(imported.contract.id);
      await refresh();
    });
  }

  async function openXreviewImport() {
    setXreviewOpen(true);
    setXreviewBusy(true);
    setXreviewError(null);
    setSelectedXreviewId("");
    try {
      const response = await api.xreviewCandidates();
      setXreviewCandidates(response.items);
    } catch (error) {
      setXreviewCandidates([]);
      setXreviewError(isApiError(error) ? error.message : "No se pudieron consultar las adjudicaciones de xreview");
    } finally {
      setXreviewBusy(false);
    }
  }

  async function importSelectedXreview() {
    if (!selectedXreviewId) return;
    const candidate = xreviewCandidates.find((item) => item.id === selectedXreviewId);
    if (candidate?.imported_contract_id) {
      setXreviewOpen(false);
      openExistingContract(candidate.imported_contract_id);
      return;
    }
    setXreviewBusy(true);
    setXreviewError(null);
    try {
      const imported = await api.importXreview(selectedXreviewId);
      setXreviewOpen(false);
      await refresh();
      selectContract(imported.contract.id);
      setActiveModule("obligaciones");
      setMessage(imported.created ? "Adjudicación de xreview incorporada con oferta y compromisos." : "La adjudicación ya estaba incorporada.");
    } catch (error) {
      setXreviewError(isApiError(error) ? error.message : "No se pudo importar la adjudicación de xreview");
    } finally {
      setXreviewBusy(false);
    }
  }

  async function extractObligations() {
    if (!selected) return;
    await runAction("Extracción con IA en cola", async () => {
      await api.extractObligations(selected.id);
      await loadDetails(selected.id);
    });
  }

  async function validateFirstObligation() {
    if (!selectedObligation || !selected) return;
    await runAction("Obligacion validada", async () => {
      await api.validateObligation(selectedObligation.id);
      await loadDetails(selected.id);
      await refresh();
    });
  }

  async function addEvidence() {
    if (!selected) return;
    await runAction("Evidencia registrada", async () => {
      await api.addEvidence(selected.id, selectedObligation?.id);
      await loadDetails(selected.id);
      await refresh();
    });
  }

  async function uploadEvidence(file?: File, obligationId?: string, evidenceType = "document") {
    if (!selected || !file) return;
    await runAction("Documento cargado y texto extraído", async () => {
      await api.uploadEvidence(selected.id, file, obligationId, evidenceType);
      await loadDetails(selected.id);
      await refresh();
    });
  }

  async function linkEvidence(evidenceId: string, obligationId?: string | null) {
    if (!selected) return;
    await runAction(obligationId ? "Documento vinculado a la obligación" : "Documento desvinculado", async () => {
      await api.updateEvidence(evidenceId, obligationId);
      await loadDetails(selected.id);
    });
  }

  async function runCheck() {
    if (!selected) return;
    await runAction("Verificación con IA en cola", async () => {
      await api.runChecks(selected.id, selectedObligation?.id);
      await loadDetails(selected.id);
    });
  }

  async function validateFirstCheck() {
    if (!selected || !checks[0]) return;
    await runAction("Verificacion validada", async () => {
      await api.resolveCheck(checks[0].id);
      await loadDetails(selected.id);
      await refresh();
    });
  }

  async function scanDataProtection() {
    if (!selected) return;
    await runAction("Revision de datos generada", async () => {
      await api.scanDataProtection(selected.id);
      await loadDetails(selected.id);
      await refresh();
    });
  }

  async function resolveFirstDataProtection() {
    if (!selected) return;
    const pending = dataProtection.find((item) => item.status === "draft" && item.result !== "clear");
    if (!pending) return;
    await runAction("Revision de datos resuelta", async () => {
      await api.resolveDataProtection(pending.id);
      await loadDetails(selected.id);
      await refresh();
    });
  }

  async function sendCheckFeedback() {
    if (!selected || !checks[0]) return;
    await runAction("Feedback registrado", async () => {
      await api.sendFeedback(selected.id, "check", checks[0].id, "positive");
    });
  }

  async function createInvoice() {
    if (!selected) return;
    await runAction("Factura registrada", async () => {
      await api.createInvoice(selected.id, selectedObligation?.id, evidence[0]?.id);
      await loadDetails(selected.id);
      await refresh();
    });
  }

  async function conformFirstInvoice() {
    if (!selected || !invoices[0]) return;
    await runAction("Factura conformada", async () => {
      await api.conformInvoice(invoices[0].id);
      await loadDetails(selected.id);
      await refresh();
    });
  }

  async function payFirstInvoice() {
    if (!selected || !invoices[0]) return;
    await runAction("Factura pagada", async () => {
      await api.payInvoice(invoices[0].id);
      await loadDetails(selected.id);
      await refresh();
    });
  }

  async function proposeExtension() {
    if (!selected) return;
    await runAction("Prorroga propuesta", async () => {
      await api.proposeExtension(selected.id);
      await loadDetails(selected.id);
      await refresh();
    });
  }

  async function proposeModification() {
    if (!selected) return;
    await runAction("Modificacion propuesta", async () => {
      await api.proposeModification(selected.id);
      await loadDetails(selected.id);
      await refresh();
    });
  }

  async function generateFirstChangeReport() {
    if (!selected || !changes[0]) return;
    await runAction("Informe con IA en cola", async () => {
      await api.generateChangeReport(changes[0].id);
      await loadDetails(selected.id);
    });
  }

  async function validateFirstChange() {
    if (!selected || !changes[0]) return;
    await runAction("Cambio validado", async () => {
      await api.validateChange(changes[0].id);
      await loadDetails(selected.id);
      await refresh();
    });
  }

  async function applyFirstChange() {
    if (!selected || !changes[0]) return;
    await runAction("Cambio aplicado", async () => {
      await api.applyChange(changes[0].id);
      await loadDetails(selected.id);
      await refresh();
    });
  }

  async function generateTasks() {
    if (!selected) return;
    await runAction("Tareas generadas", async () => {
      await api.generateTasks(selected.id);
      await loadDetails(selected.id);
      await refresh();
    });
  }

  async function completeFirstTask() {
    if (!selected || !tasks[0]) return;
    await runAction("Tarea cerrada", async () => {
      await api.completeTask(tasks[0].id);
      await loadDetails(selected.id);
      await refresh();
    });
  }

  async function generateDocument(documentType = "recepcion_acta") {
    if (!selected) return;
    await runAction("Generación con IA en cola", async () => {
      await api.generateDocument(selected.id, documentType);
      await loadDetails(selected.id);
    });
  }

  async function retryAiJob(jobId: string) {
    if (!selected) return;
    await runAction("Trabajo de IA reintentado", async () => {
      await api.retryAiJob(jobId);
      await loadDetails(selected.id);
    });
  }

  async function analyzeWinningOffer(evidenceId: string) {
    if (!selected) return;
    await runAction("Análisis de oferta con IA en cola", async () => {
      await api.analyzeWinningOffer(selected.id, evidenceId);
      await loadDetails(selected.id);
    });
  }

  async function validateFirstRisk() {
    const risk = risks.find((item) => item.validation_status === "draft");
    if (!selected || !risk) return;
    await runAction("Riesgo validado", async () => {
      await api.validateRisk(risk.id);
      await loadDetails(selected.id);
    });
  }

  async function validateFirstDocument() {
    if (!selected || !documents[0]) return;
    await runAction("Documento validado", async () => {
      await api.resolveDocument(documents[0].id);
      await loadDetails(selected.id);
    });
  }

  async function sendDocumentFeedback() {
    if (!selected || !documents[0]) return;
    await runAction("Feedback registrado", async () => {
      await api.sendFeedback(selected.id, "document", documents[0].id, "positive");
    });
  }

  function downloadFirstDocument() {
    if (documents[0]) window.open(api.documentDocxUrl(documents[0].id), "_blank", "noopener,noreferrer");
  }

  async function calculatePenalty() {
    if (!selected) return;
    await runAction("Penalidad calculada", async () => {
      await api.calculatePenalty(selected.id, selectedObligation?.id);
      await loadDetails(selected.id);
      await refresh();
    });
  }

  async function validateFirstPenalty() {
    if (!selected || !penalties[0]) return;
    await runAction("Penalidad validada", async () => {
      await api.resolvePenalty(penalties[0].id);
      await loadDetails(selected.id);
      await refresh();
    });
  }

  async function openProceeding() {
    if (!selected) return;
    await runAction("Expediente abierto", async () => {
      await api.openProceeding(selected.id, penalties[0]?.id);
      await loadDetails(selected.id);
      await refresh();
    });
  }

  async function advanceFirstProceeding() {
    if (!selected || !proceedings[0]) return;
    await runAction("Expediente avanzado", async () => {
      await api.advanceProceeding(proceedings[0].id);
      await loadDetails(selected.id);
      await refresh();
    });
  }

  function exportSelectedZip() {
    if (selected) window.open(api.exportZipUrl(selected.id), "_blank", "noopener,noreferrer");
  }

  function exportServiceReturnZip() {
    window.open(api.serviceReturnZipUrl(), "_blank", "noopener,noreferrer");
  }

  async function addComment(body: string) {
    if (!selected || !body.trim()) return;
    await runAction("Comentario registrado", async () => {
      await api.addComment(selected.id, body.trim());
      const nextComments = await api.comments(selected.id);
      setComments(nextComments.items);
    });
  }

  const module = copy[activeModule];
  const openAlerts = alerts.filter((item) => item.status === "open").length;
  const openTasks = tasks.filter((item) => item.status === "todo" || item.status === "doing").length;
  const draftObligations = obligations.filter((item) => item.validation_status === "draft").length;
  const riskyChecks = checks.filter((item) => item.result !== "compliant").length;
  const openDataProtection = dataProtection.filter((item) => item.status === "draft" && item.result !== "clear").length;
  const pendingInvoices = invoices.filter((item) => item.status === "registered" || item.status === "conforming" || item.status === "payment_ordered").length;
  const openProceedings = proceedings.filter((item) => item.status !== "resolved" && item.status !== "closed" && item.status !== "rejected").length;
  const openChanges = changes.filter((item) => item.status !== "applied" && item.status !== "rejected").length;
  const llmAvailable = Boolean(llmStatus?.available);
  const llmLabel = llmStatus?.model || "llm2";
  const llmCapacity = llmStatus?.context_window ? `${Math.round(llmStatus.context_window / 1000)}K` : apiError ? "offline" : "";

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <img src="/brand/xfollow-wordmark.svg" alt="xFollow" className="brand-logo" />
        </div>
        <button className="primary-contract-action" onClick={openNewContract}>
          <PackagePlus size={18} />
          Nuevo contrato
        </button>
        <nav className="nav-list" aria-label="Principal">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button key={item.id} className={clsx("nav-item", activeModule === item.id && "active")} onClick={() => setActiveModule(item.id)}>
                <Icon size={18} />
                <span>{copy[item.id].label}</span>
              </button>
            );
          })}
        </nav>
        <div className={clsx("model-chip", llmAvailable ? "online" : "offline")} title={llmStatus?.error || undefined}>
          <span className="model-status-dot" />
          <Bot size={16} />
          <span>{llmLabel}</span>
          <strong>{llmCapacity}</strong>
        </div>
        <a className="powered-by" href="https://www.techfriendly.es" target="_blank" rel="noreferrer">powered by <strong>TECH friendly</strong></a>
      </aside>

      <section className="workspace-shell">
        <header className="topbar">
          <label className="active-project-select">
            <span>Proyecto activo</span>
            <select value={selected?.id ?? ""} onChange={(event) => selectContract(event.target.value)} aria-label="Proyecto activo">
              {!contracts.length && <option value="">Sin proyectos</option>}
              {contracts.map((contract) => (
                <option key={contract.id} value={contract.id}>{contract.file_number || contract.id} · {contract.title}</option>
              ))}
            </select>
          </label>
          <div className="topbar-actions">
            <button className="icon-button" onClick={() => void refresh()} title="Actualizar">
              <RefreshCw size={18} />
            </button>
            <button className="icon-button" onClick={openNewContract} title="Nuevo contrato">
              <PackagePlus size={18} />
            </button>
            <button className="icon-button" onClick={openNewContract} title="Buscar en xTender">
              <WandSparkles size={18} />
            </button>
            <button className="icon-button" onClick={() => void importPcsp()} title="Importar PCSP">
              <Search size={18} />
            </button>
            <button className="icon-button" onClick={() => void openXreviewImport()} title="Importar adjudicación de xreview">
              <Gavel size={18} />
            </button>
          </div>
        </header>

        <div className="content">
          <section className="filter-bar" aria-label="Filtros de contratos">
            <div className="search-field">
              <Search size={17} />
              <input value={contractQuery} onChange={(event) => setContractQuery(event.target.value)} placeholder="Buscar proyecto, expediente o contratista" />
            </div>
            <select value={contractStatus} onChange={(event) => setContractStatus(event.target.value)} aria-label="Estado del contrato">
              <option value="">Todos los estados</option>
              <option value="active">En ejecucion</option>
              <option value="completed">Completados</option>
              <option value="liquidated">Liquidados</option>
              <option value="archived">Archivados</option>
            </select>
            <select value={renewalStatus} onChange={(event) => setRenewalStatus(event.target.value)} aria-label="Decision de continuidad">
              <option value="">Toda continuidad</option>
              <option value="undefined">Decision pendiente</option>
              <option value="will_extend">Se prorrogara</option>
              <option value="retender">Se licitara de nuevo</option>
              <option value="no_renewal">No se renueva</option>
              <option value="extended">Prorrogado</option>
            </select>
          </section>
          <section className="screen-heading">
            <div>
              <p className="eyebrow">{module.label}</p>
              <h1>{module.title}</h1>
              <p>{module.subtitle}</p>
            </div>
            <span className="ai-disclosure">
              <Sparkles size={16} />
              IA con validacion humana
            </span>
          </section>

          <section className="metric-grid">
            <Metric icon={FolderKanban} label="Contratos" value={summary.total ?? contracts.length} />
            <Metric icon={Bell} label="Alertas abiertas" value={summary.open_alerts ?? openAlerts} tone={openAlerts ? "warning" : "info"} />
            <Metric icon={ListChecks} label="Obligaciones" value={obligations.length} />
            <Metric icon={ClipboardCheck} label="Tareas" value={summary.open_tasks ?? openTasks} tone={openTasks ? "warning" : "success"} />
            <Metric icon={ShieldCheck} label="Datos" value={summary.data_protection_open ?? openDataProtection} tone={openDataProtection ? "danger" : "success"} />
            <Metric icon={FileCheck2} label="Facturas" value={summary.pending_invoices ?? pendingInvoices} tone={pendingInvoices ? "warning" : "success"} />
            <Metric icon={RefreshCw} label="Cambios" value={summary.open_changes ?? openChanges} tone={openChanges ? "warning" : "success"} />
            <Metric icon={FileText} label="Documentos" value={documents.length} />
            <Metric icon={Gavel} label="Penalidades" value={penalties.length} tone={penalties.length ? "danger" : "info"} />
            <Metric icon={Landmark} label="Expedientes" value={summary.open_proceedings ?? openProceedings} tone={openProceedings ? "danger" : "success"} />
            <Metric icon={History} label="Auditoria" value={governance?.audit_summary.events ?? auditEvents.length} />
          </section>

          <section className="status-strip">
            <History size={16} />
            <span>{message}</span>
            {apiError && <button className="inline-action" onClick={() => void refresh()}><RefreshCw size={15} />Reintentar</button>}
          </section>

          {!!aiJobs.length && <AiJobsStatus jobs={aiJobs} onRetry={(jobId) => void retryAiJob(jobId)} />}

          <div className="work-grid">
            <ContractList contracts={contracts} selectedId={selected?.id} onSelect={selectContract} />
            <section className="main-panel">
              {activeModule === "contratos" && <ContractDetail contract={selected} comments={comments} onComment={(body) => void addComment(body)} onCreate={openNewContract} onImportPcsp={() => void importPcsp()} onExport={exportSelectedZip} />}
              {activeModule === "obligaciones" && <Obligations obligations={obligations} onExtract={() => void extractObligations()} onValidate={() => void validateFirstObligation()} draftCount={draftObligations} />}
              {activeModule === "alertas" && <Alerts alerts={alerts} />}
              {activeModule === "tareas" && <Tasks tasks={tasks} onGenerate={() => void generateTasks()} onComplete={() => void completeFirstTask()} />}
              {activeModule === "cumplimiento" && (
                <Compliance
                  evidence={evidence}
                  checks={checks}
                  onEvidence={() => void addEvidence()}
                  onUpload={(file) => void uploadEvidence(file, selectedObligation?.id)}
                  onCheck={() => void runCheck()}
                  onValidate={() => void validateFirstCheck()}
                  onFeedback={() => void sendCheckFeedback()}
                  onOpenDocuments={() => setActiveModule("documentos")}
                />
              )}
              {activeModule === "datos" && <DataProtection assessments={dataProtection} onScan={() => void scanDataProtection()} onResolve={() => void resolveFirstDataProtection()} />}
              {activeModule === "facturas" && <Invoices invoices={invoices} liquidation={liquidation} onCreate={() => void createInvoice()} onConform={() => void conformFirstInvoice()} onPay={() => void payFirstInvoice()} />}
              {activeModule === "cambios" && <Changes changes={changes} onExtension={() => void proposeExtension()} onModification={() => void proposeModification()} onReport={() => void generateFirstChangeReport()} onValidate={() => void validateFirstChange()} onApply={() => void applyFirstChange()} />}
              {activeModule === "documentos" && (
                <Documents
                  documents={documents}
                  evidence={evidence}
                  obligations={obligations}
                  risks={risks}
                  onGenerate={(documentType) => void generateDocument(documentType)}
                  onUpload={(file, obligationId, evidenceType) => void uploadEvidence(file, obligationId, evidenceType)}
                  onLink={(evidenceId, obligationId) => void linkEvidence(evidenceId, obligationId)}
                  onAnalyzeOffer={(evidenceId) => void analyzeWinningOffer(evidenceId)}
                  onValidateRisk={() => void validateFirstRisk()}
                  onValidate={() => void validateFirstDocument()}
                  onDownload={downloadFirstDocument}
                  onFeedback={() => void sendDocumentFeedback()}
                />
              )}
              {activeModule === "penalidades" && <Penalties penalties={penalties} onCalculate={() => void calculatePenalty()} onValidate={() => void validateFirstPenalty()} />}
              {activeModule === "expedientes" && <Proceedings proceedings={proceedings} onOpen={() => void openProceeding()} onAdvance={() => void advanceFirstProceeding()} />}
              {activeModule === "gobierno" && <Governance governance={governance} auditEvents={auditEvents} onServiceReturn={exportServiceReturnZip} />}
            </section>
          </div>
        </div>
      </section>
      <NewContractDialog
        open={newContractOpen}
        step={newContractStep}
        query={xtenderQuery}
        candidates={xtenderCandidates}
        selectedWorkspaceId={selectedXtenderId}
        importedContracts={importedXtenderContracts}
        loading={xtenderLoading}
        busy={newContractBusy}
        error={newContractError}
        winningOfferFile={winningOfferFile}
        importedContract={importedContract}
        onClose={closeNewContract}
        onQueryChange={setXtenderQuery}
        onSelect={setSelectedXtenderId}
        onOpenExisting={openExistingContract}
        onImport={() => void importSelectedXtender()}
        onWinningOfferChange={setWinningOfferFile}
        onUploadOffer={() => void uploadWinningOfferFromIntake()}
        onSkipOffer={skipWinningOfferFromIntake}
      />
      <XreviewImportDialog
        open={xreviewOpen}
        candidates={xreviewCandidates}
        selectedId={selectedXreviewId}
        busy={xreviewBusy}
        error={xreviewError}
        onClose={() => !xreviewBusy && setXreviewOpen(false)}
        onSelect={setSelectedXreviewId}
        onOpenExisting={openExistingContract}
        onImport={() => void importSelectedXreview()}
      />
    </main>
  );
}

function XreviewImportDialog({ open, candidates, selectedId, busy, error, onClose, onSelect, onOpenExisting, onImport }: {
  open: boolean;
  candidates: XreviewAward[];
  selectedId: string;
  busy: boolean;
  error: string | null;
  onClose: () => void;
  onSelect: (id: string) => void;
  onOpenExisting: (contractId: string) => void;
  onImport: () => void;
}) {
  if (!open) return null;
  const selected = candidates.find((item) => item.id === selectedId);
  return (
    <div className="modal-backdrop" role="presentation">
      <section className="contract-intake-dialog" role="dialog" aria-modal="true" aria-labelledby="xreview-import-title">
        <header className="dialog-header">
          <div><p className="eyebrow">xreview</p><h2 id="xreview-import-title">Incorporar adjudicación</h2></div>
          <button className="icon-button" type="button" onClick={onClose} disabled={busy} title="Cerrar" aria-label="Cerrar"><X size={18} /></button>
        </header>
        <p className="dialog-hint">Paquetes inmutables publicados al finalizar cada lote. La oferta y sus compromisos se enlazan sin volver a subir documentos.</p>
        <div className="intake-candidate-list" aria-live="polite">
          {candidates.map((candidate) => {
            const imported = candidate.imported_contract_id;
            const title = [candidate.procedure?.title, candidate.lot?.code, candidate.lot?.title].filter(Boolean).join(" · ");
            return (
              <button key={candidate.id} type="button" className={clsx("intake-candidate", selectedId === candidate.id && "selected", imported && "imported")} onClick={() => imported ? onOpenExisting(imported) : onSelect(candidate.id)}>
                <span><strong>{title || candidate.id}</strong><small>{candidate.procedure?.file_number || candidate.procedure_id} · {candidate.bidder?.name || "Adjudicatario"}</small></span>
                <b>{imported ? "Ya incorporado" : selectedId === candidate.id ? "Seleccionado" : candidate.awarded_amount != null ? formatEuro(candidate.awarded_amount) : "Disponible"}</b>
              </button>
            );
          })}
          {busy && !candidates.length && <p className="empty">Consultando adjudicaciones de xreview...</p>}
          {!busy && !candidates.length && !error && <p className="empty">No hay lotes finalizados pendientes de incorporar.</p>}
        </div>
        {error && <p className="dialog-error">{error}</p>}
        <footer className="dialog-actions">
          <button className="dialog-secondary" type="button" onClick={onClose} disabled={busy}>Cancelar</button>
          <button className="dialog-primary" type="button" onClick={onImport} disabled={!selected || Boolean(selected.imported_contract_id) || busy}><PackagePlus size={16} />{busy ? "Incorporando..." : "Incorporar contrato"}</button>
        </footer>
      </section>
    </div>
  );
}

function NewContractDialog({ open, step, query, candidates, selectedWorkspaceId, importedContracts, loading, busy, error, winningOfferFile, importedContract, onClose, onQueryChange, onSelect, onOpenExisting, onImport, onWinningOfferChange, onUploadOffer, onSkipOffer }: {
  open: boolean;
  step: NewContractStep;
  query: string;
  candidates: XtenderWorkspace[];
  selectedWorkspaceId: string;
  importedContracts: Map<string, Contract>;
  loading: boolean;
  busy: boolean;
  error: string | null;
  winningOfferFile: File | null;
  importedContract: Contract | null;
  onClose: () => void;
  onQueryChange: (query: string) => void;
  onSelect: (workspaceId: string) => void;
  onOpenExisting: (contractId: string) => void;
  onImport: () => void;
  onWinningOfferChange: (file: File | null) => void;
  onUploadOffer: () => void;
  onSkipOffer: () => void;
}) {
  if (!open) return null;
  return (
    <div className="modal-backdrop" role="presentation">
      <section className="contract-intake-dialog" role="dialog" aria-modal="true" aria-labelledby="new-contract-title">
        <header className="dialog-header">
          <div>
            <p className="eyebrow">{step === "select" ? "xTender" : "Documentación inicial"}</p>
            <h2 id="new-contract-title">{step === "select" ? "Incorporar contrato" : "Oferta adjudicataria"}</h2>
          </div>
          <button className="icon-button" type="button" onClick={onClose} disabled={busy} title="Cerrar" aria-label="Cerrar">
            <X size={18} />
          </button>
        </header>

        {step === "select" ? (
          <>
            <label className="dialog-search">
              <Search size={18} />
              <input autoFocus value={query} onChange={(event) => onQueryChange(event.target.value)} placeholder="Buscar por expediente o título" />
            </label>
            <div className="intake-candidate-list" aria-live="polite">
              {candidates.map((candidate) => {
                const imported = importedContracts.get(candidate.id);
                const fileNumber = typeof candidate.data?.file_number === "string" ? candidate.data.file_number : candidate.id;
                return (
                  <button
                    key={candidate.id}
                    type="button"
                    className={clsx("intake-candidate", selectedWorkspaceId === candidate.id && "selected", imported && "imported")}
                    onClick={() => imported ? onOpenExisting(imported.id) : onSelect(candidate.id)}
                  >
                    <span>
                      <strong>{candidate.title}</strong>
                      <small>{fileNumber}{candidate.unit ? ` · ${candidate.unit}` : ""}</small>
                    </span>
                    <b>{imported ? "Ya incorporado" : selectedWorkspaceId === candidate.id ? "Seleccionado" : candidate.status || "Disponible"}</b>
                  </button>
                );
              })}
              {loading && <p className="empty">Buscando contratos de xTender...</p>}
              {!loading && !candidates.length && !error && <p className="empty">No hay contratos de xTender que coincidan con la búsqueda.</p>}
            </div>
            {error && <p className="dialog-error">{error}</p>}
            <footer className="dialog-actions">
              <button className="dialog-secondary" type="button" onClick={onClose} disabled={busy}>Cancelar</button>
              <button className="dialog-primary" type="button" onClick={onImport} disabled={!selectedWorkspaceId || busy}>
                <PackagePlus size={16} />{busy ? "Incorporando..." : "Incorporar contrato"}
              </button>
            </footer>
          </>
        ) : (
          <>
            <div className="intake-contract-summary">
              <strong>{importedContract?.title}</strong>
              <span>{importedContract?.file_number || importedContract?.id}</span>
            </div>
            <label className="offer-file-input">
              <Upload size={20} />
              <span>{winningOfferFile?.name || "Seleccionar oferta adjudicataria"}</span>
              <input type="file" accept=".pdf,.docx,.txt,.md,.markdown" onChange={(event) => onWinningOfferChange(event.target.files?.[0] || null)} />
            </label>
            <p className="dialog-hint">PDF, DOCX, TXT o Markdown · máximo 25 MB</p>
            {error && <p className="dialog-error">{error}</p>}
            <footer className="dialog-actions">
              <button className="dialog-secondary" type="button" onClick={onSkipOffer} disabled={busy}>Omitir por ahora</button>
              <button className="dialog-primary" type="button" onClick={onUploadOffer} disabled={!winningOfferFile || busy}>
                <Sparkles size={16} />{busy ? "Guardando..." : "Guardar y analizar con IA"}
              </button>
            </footer>
          </>
        )}
      </section>
    </div>
  );
}

function Metric({ icon: Icon, label, value, tone = "info" }: { icon: LucideIcon; label: string; value: number; tone?: "info" | "success" | "warning" | "danger" }) {
  return (
    <article className="metric-card">
      <span className={clsx("metric-icon", tone)}>
        <Icon size={18} />
      </span>
      <strong>{value}</strong>
      <span>{label}</span>
    </article>
  );
}

function AiJobsStatus({ jobs, onRetry }: { jobs: AiJob[]; onRetry: (jobId: string) => void }) {
  const labels: Record<AiJob["job_type"], string> = {
    obligations_extract: "Extracción de obligaciones",
    compliance_check: "Verificación de cumplimiento",
    document_generate: "Generación de documento",
    change_report: "Informe de cambio",
    offer_risk_analysis: "Análisis de oferta adjudicataria"
  };
  return (
    <section className="ai-jobs" aria-label="Trabajos de IA">
      <div className="panel-title"><span>Trabajos de IA</span><strong>{jobs.length}</strong></div>
      <div className="job-list">
        {jobs.slice(0, 5).map((job) => (
          <article key={job.id} className={clsx("job-row", `job-${job.status}`)}>
            {job.status === "running" || job.status === "queued" || job.status === "retrying" ? <Loader2 size={16} className="spin" /> : job.status === "completed" ? <ShieldCheck size={16} /> : <Bell size={16} />}
            <span>{labels[job.job_type]}</span>
            <small>{statusLabel(job.status)}{job.attempts ? ` · intento ${job.attempts}` : ""}{job.last_error ? ` · ${job.last_error}` : ""}</small>
            {job.status === "failed" && <button className="inline-action" onClick={() => onRetry(job.id)}><RefreshCw size={15} />Reintentar</button>}
          </article>
        ))}
      </div>
    </section>
  );
}

function ContractList({ contracts, selectedId, onSelect }: { contracts: Contract[]; selectedId?: string; onSelect: (id: string) => void }) {
  return (
    <section className="side-panel">
      <div className="panel-title">
        <span>Contratos</span>
        <strong>{contracts.length}</strong>
      </div>
      <div className="contract-list">
        {contracts.map((contract) => (
          <button key={contract.id} className={clsx("contract-row", selectedId === contract.id && "selected")} onClick={() => onSelect(contract.id)}>
            <strong>{contract.title}</strong>
            <span>{contract.file_number || contract.id}</span>
            <small>{statusLabel(contract.status)} · {contract.counts?.open_alerts ?? 0} alertas</small>
          </button>
        ))}
        {!contracts.length && <p className="empty">No hay contratos cargados.</p>}
      </div>
    </section>
  );
}

function ContractDetail({ contract, comments, onComment, onCreate, onImportPcsp, onExport }: { contract?: Contract; comments: ContractComment[]; onComment: (body: string) => void; onCreate: () => void; onImportPcsp: () => void; onExport: () => void }) {
  if (!contract) {
    return (
      <div className="empty-state">
        <FolderKanban size={28} />
        <strong>Sin contrato activo</strong>
        <div className="action-row">
          <button onClick={onCreate}><PackagePlus size={16} />Nuevo contrato</button>
          <button onClick={onImportPcsp}><Search size={16} />PCSP</button>
        </div>
      </div>
    );
  }
  return (
    <>
      <div className="panel-title">
        <span>Ficha</span>
        <strong>{contract.file_number || contract.id}</strong>
      </div>
      <Toolbar>
        <button onClick={onExport}><Archive size={16} />Export ZIP</button>
      </Toolbar>
      <div className="detail-grid">
        <Detail label="Objeto" value={contract.title} wide />
        <Detail label="Organo" value={contract.contracting_body} />
        <Detail label="Contratista" value={contract.contractor} />
        <Detail label="Responsable" value={contract.contract_manager} />
        <Detail label="Tipo" value={contract.contract_type} />
        <Detail label="CPV" value={contract.cpv_codes.join(", ")} />
        <Detail label="Adjudicacion" value={formatEuro(contract.awarded_amount)} />
        <Detail label="Inicio" value={shortDate(contract.start_date)} />
        <Detail label="Fin" value={shortDate(contract.end_date)} />
        <Detail label="Preaviso prorroga" value={shortDate(contract.extension_deadline)} />
        <Detail label="Garantia" value={shortDate(contract.warranty_end_date)} />
        <Detail label="Continuidad" value={statusLabel(contract.renewal_status || "undefined")} />
        <Detail label="Decision antes de" value={shortDate(contract.decision_due_date)} />
      </div>
      <CommentBox comments={comments} onSubmit={onComment} />
    </>
  );
}

function CommentBox({ comments, onSubmit }: { comments: ContractComment[]; onSubmit: (body: string) => void }) {
  const [body, setBody] = useState("");
  return (
    <section className="comment-box">
      <div className="panel-title"><span><MessageSquare size={15} /> Comentarios</span><strong>{comments.length}</strong></div>
      <form className="comment-form" onSubmit={(event) => { event.preventDefault(); if (body.trim()) { onSubmit(body); setBody(""); } }}>
        <textarea value={body} onChange={(event) => setBody(event.target.value)} placeholder="Añadir una nota de seguimiento" rows={3} />
        <button type="submit" disabled={!body.trim()}><MessageSquare size={15} />Guardar comentario</button>
      </form>
      <div className="comment-list">
        {comments.map((comment) => <article key={comment.id}><p>{comment.body}</p><small>{comment.created_by || "usuario"} · {shortDate(comment.created_at)}</small></article>)}
        {!comments.length && <p className="empty">Aún no hay comentarios.</p>}
      </div>
    </section>
  );
}

function Obligations({ obligations, onExtract, onValidate, draftCount }: { obligations: Obligation[]; onExtract: () => void; onValidate: () => void; draftCount: number }) {
  return (
    <>
      <Toolbar>
        <button onClick={onExtract}><WandSparkles size={16} />Extraer con IA</button>
        <button onClick={onValidate} disabled={!draftCount}><ShieldCheck size={16} />Validar primera</button>
      </Toolbar>
      <div className="item-list">
        {obligations.map((item) => (
          <article key={item.id} className="item-card">
            <div>
              <strong>{item.title}</strong>
              <p>{item.description}</p>
            </div>
            <div className="item-meta">
              <span className={clsx("severity", severityClass(item.severity))}>{item.severity}</span>
              <span className="status-pill">{statusLabel(item.validation_status)}</span>
              <span>{shortDate(item.due_date)}</span>
            </div>
          </article>
        ))}
        {!obligations.length && <p className="empty">No hay obligaciones registradas.</p>}
      </div>
    </>
  );
}

function Alerts({ alerts }: { alerts: Alert[] }) {
  return (
    <div className="item-list">
      {alerts.map((item) => (
        <article key={item.id} className="item-card">
          <div>
            <strong>{item.title}</strong>
            <p>{item.alert_type} · preaviso {item.lead_days} dias</p>
          </div>
          <div className="item-meta">
            <span className={clsx("severity", severityClass(item.severity))}>{item.severity}</span>
            <span className="status-pill">{statusLabel(item.status)}</span>
            <span>{shortDate(item.due_date)}</span>
          </div>
        </article>
      ))}
      {!alerts.length && <p className="empty">No hay alertas abiertas.</p>}
    </div>
  );
}

function Tasks({ tasks, onGenerate, onComplete }: { tasks: ContractTask[]; onGenerate: () => void; onComplete: () => void }) {
  return (
    <>
      <Toolbar>
        <button onClick={onGenerate}><WandSparkles size={16} />Generar</button>
        <button onClick={onComplete} disabled={!tasks.length}><ShieldCheck size={16} />Cerrar primera</button>
      </Toolbar>
      <div className="item-list">
        {tasks.map((item) => (
          <article key={item.id} className="item-card">
            <div>
              <strong>{item.title}</strong>
              <p>{item.description || "Tarea de seguimiento contractual."}</p>
            </div>
            <div className="item-meta">
              <span className={clsx("severity", severityClass(item.severity))}>{item.severity}</span>
              <span className="status-pill">{statusLabel(item.status)}</span>
              <span>{shortDate(item.due_date)}</span>
            </div>
          </article>
        ))}
        {!tasks.length && <p className="empty">No hay tareas abiertas.</p>}
      </div>
    </>
  );
}

function Compliance({ evidence, checks, onEvidence, onUpload, onCheck, onValidate, onFeedback, onOpenDocuments }: { evidence: Evidence[]; checks: ComplianceCheck[]; onEvidence: () => void; onUpload: (file?: File) => void; onCheck: () => void; onValidate: () => void; onFeedback: () => void; onOpenDocuments: () => void }) {
  return (
    <>
      <Toolbar>
        <button onClick={onEvidence}><Upload size={16} />Evidencia</button>
        <label className="toolbar-upload"><Upload size={16} />Subir documento<input type="file" accept=".pdf,.docx,.txt,.md,.markdown" onChange={(event) => { const file = event.target.files?.[0]; event.currentTarget.value = ""; onUpload(file); }} /></label>
        <button onClick={onCheck}><ClipboardCheck size={16} />Verificar con IA</button>
        <button onClick={onOpenDocuments}><FileText size={16} />Biblioteca</button>
        <button onClick={onValidate} disabled={!checks.length}><ShieldCheck size={16} />Validar check</button>
        <button onClick={onFeedback} disabled={!checks.length}><Sparkles size={16} />Feedback</button>
      </Toolbar>
      <div className="split-panels">
        <div>
          <div className="panel-title"><span>Evidencias</span><strong>{evidence.length}</strong></div>
          {evidence.map((item) => (
            <article key={item.id} className="compact-card">
              <strong>{item.title}</strong>
              <span>{item.evidence_type} {item.obligation_id ? "· vinculada" : "· sin vincular"}</span>
            </article>
          ))}
        </div>
        <div>
          <div className="panel-title"><span>Checks</span><strong>{checks.length}</strong></div>
          {checks.map((item) => (
            <article key={item.id} className="compact-card">
              <strong>{statusLabel(item.result)}</strong>
              <span>{item.reasoning}</span>
            </article>
          ))}
        </div>
      </div>
    </>
  );
}

function DataProtection({ assessments, onScan, onResolve }: { assessments: DataProtectionAssessment[]; onScan: () => void; onResolve: () => void }) {
  const open = assessments.filter((item) => item.status === "draft" && item.result !== "clear");
  const resolved = assessments.filter((item) => item.status !== "draft" || item.result === "clear");
  const findingLabels = Array.from(new Set(assessments.flatMap((item) => item.findings.map((finding) => finding.label)))).slice(0, 8);

  return (
    <>
      <Toolbar>
        <button onClick={onScan}><ShieldCheck size={16} />Escanear</button>
        <button onClick={onResolve} disabled={!open.length}><ShieldCheck size={16} />Resolver primero</button>
      </Toolbar>
      <div className="split-panels">
        <div>
          <div className="panel-title"><span>Control</span><strong>{open.length} abiertas</strong></div>
          <div className="compact-stack">
            <MiniStat label="Evaluaciones" value={String(assessments.length)} />
            <MiniStat label="Resueltas" value={String(resolved.length)} />
            <MiniStat label="Hallazgos" value={String(assessments.reduce((total, item) => total + item.findings.length, 0))} />
            <MiniStat label="Maximo riesgo" value={open[0]?.severity || assessments[0]?.severity || "baja"} />
          </div>
        </div>
        <div>
          <div className="panel-title"><span>Senales</span><strong>{findingLabels.length}</strong></div>
          <div className="tag-grid">
            {findingLabels.map((label) => <span key={label}>{label}</span>)}
            {!findingLabels.length && <span>sin hallazgos</span>}
          </div>
          <div className="warning-list">
            {open.slice(0, 2).map((item) => <span key={item.id}>{item.recommendation}</span>)}
          </div>
        </div>
      </div>
      <div className="item-list">
        {assessments.map((item) => (
          <article key={item.id} className="item-card">
            <div>
              <strong>{item.source_title}</strong>
              <p>{item.recommendation}</p>
              {!!item.redacted_preview && <p className="redacted-preview">{item.redacted_preview}</p>}
              {!!item.findings.length && (
                <div className="tag-grid">
                  {item.findings.slice(0, 6).map((finding) => (
                    <span key={`${item.id}-${finding.match_hash}-${finding.label}`}>{finding.label}: {finding.snippet}</span>
                  ))}
                </div>
              )}
            </div>
            <div className="item-meta">
              <span className={clsx("severity", severityClass(item.severity))}>{item.severity}</span>
              <span className="status-pill">{statusLabel(item.result)}</span>
              <span className="status-pill">{statusLabel(item.status)}</span>
              <span>{item.scope}</span>
              <span>{shortDate(item.resolved_at || item.created_at)}</span>
            </div>
          </article>
        ))}
        {!assessments.length && <p className="empty">No hay revisiones de datos todavia.</p>}
      </div>
    </>
  );
}

function Invoices({ invoices, liquidation, onCreate, onConform, onPay }: { invoices: ContractInvoice[]; liquidation: LiquidationSummary | null; onCreate: () => void; onConform: () => void; onPay: () => void }) {
  return (
    <>
      <Toolbar>
        <button onClick={onCreate}><FileCheck2 size={16} />Registrar</button>
        <button onClick={onConform} disabled={!invoices.length}><ShieldCheck size={16} />Conformar</button>
        <button onClick={onPay} disabled={!invoices.length}><Archive size={16} />Marcar pago</button>
      </Toolbar>
      <div className="split-panels">
        <div>
          <div className="panel-title"><span>Liquidacion</span><strong>{formatEuro(liquidation?.settlement_balance)}</strong></div>
          <div className="compact-stack">
            <MiniStat label="Adjudicado" value={formatEuro(liquidation?.awarded_amount)} />
            <MiniStat label="Facturado" value={formatEuro(liquidation?.invoiced_amount)} />
            <MiniStat label="Conformado" value={formatEuro(liquidation?.conforming_amount)} />
            <MiniStat label="Pagado" value={formatEuro(liquidation?.paid_amount)} />
            <MiniStat label="Pendiente" value={formatEuro(liquidation?.pending_payment_amount)} />
          </div>
          {!!liquidation?.warnings.length && (
            <div className="warning-list">
              {liquidation.warnings.map((warning) => <span key={warning}>{warning}</span>)}
            </div>
          )}
        </div>
        <div>
          <div className="panel-title"><span>Facturas</span><strong>{invoices.length}</strong></div>
          {invoices.map((item) => (
            <article key={item.id} className="compact-card">
              <strong>{item.invoice_number} · {formatEuro(item.amount_with_tax)}</strong>
              <span>{item.concept}</span>
              <small>{statusLabel(item.status)} · vence {shortDate(item.payment_due_date)}</small>
            </article>
          ))}
          {!invoices.length && <p className="empty">No hay facturas registradas.</p>}
        </div>
      </div>
    </>
  );
}

function Changes({ changes, onExtension, onModification, onReport, onValidate, onApply }: { changes: ContractChange[]; onExtension: () => void; onModification: () => void; onReport: () => void; onValidate: () => void; onApply: () => void }) {
  return (
    <>
      <Toolbar>
        <button onClick={onExtension}><RefreshCw size={16} />Prorroga</button>
        <button onClick={onModification}><WandSparkles size={16} />Modificar</button>
        <button onClick={onReport} disabled={!changes.length}><Sparkles size={16} />Generar informe con IA</button>
        <button onClick={onValidate} disabled={!changes.length}><ShieldCheck size={16} />Validar</button>
        <button onClick={onApply} disabled={!changes.length}><Archive size={16} />Aplicar</button>
      </Toolbar>
      <div className="item-list">
        {changes.map((item) => (
          <article key={item.id} className="item-card">
            <div>
              <strong>{item.title}</strong>
              <p>{item.reason}</p>
            </div>
            <div className="item-meta">
              <span>{item.change_type === "extension" ? "prorroga" : "modificacion"}</span>
              <span className="status-pill">{statusLabel(item.status)}</span>
              <span>{formatEuro(item.amount_delta)}</span>
              <span>{shortDate(item.proposed_end_date)}</span>
            </div>
          </article>
        ))}
        {!changes.length && <p className="empty">No hay propuestas de modificacion o prorroga.</p>}
      </div>
    </>
  );
}

function Documents({ documents, evidence, obligations, risks, onGenerate, onUpload, onLink, onAnalyzeOffer, onValidateRisk, onValidate, onDownload, onFeedback }: { documents: GeneratedDocument[]; evidence: Evidence[]; obligations: Obligation[]; risks: ContractRisk[]; onGenerate: (documentType: string) => void; onUpload: (file?: File, obligationId?: string, evidenceType?: string) => void; onLink: (evidenceId: string, obligationId?: string | null) => void; onAnalyzeOffer: (evidenceId: string) => void; onValidateRisk: () => void; onValidate: () => void; onDownload: () => void; onFeedback: () => void }) {
  const [documentType, setDocumentType] = useState("recepcion_acta");
  const [uploadObligationId, setUploadObligationId] = useState("");
  const [uploadEvidenceType, setUploadEvidenceType] = useState("document");
  const winningOffers = evidence.filter((item) => item.evidence_type === "winning_offer");
  const draftRisks = risks.filter((item) => item.validation_status === "draft");
  return (
    <>
      <Toolbar>
        <select value={documentType} onChange={(event) => setDocumentType(event.target.value)} aria-label="Tipo de acta o informe">
          <option value="recepcion_acta">Acta de recepción</option>
          <option value="liquidacion_informe">Informe de liquidación</option>
          <option value="modificacion_informe_juridico">Informe de modificación</option>
          <option value="prorroga_informe_juridico">Informe de prórroga</option>
          <option value="penalidad_expediente">Expediente de penalidad</option>
          <option value="resolucion_expediente">Expediente de resolución</option>
        </select>
        <button onClick={() => onGenerate(documentType)}><Sparkles size={16} />Generar con IA</button>
        <button onClick={onDownload} disabled={!documents.length}><Archive size={16} />DOCX</button>
        <button onClick={onValidate} disabled={!documents.length}><ShieldCheck size={16} />Validar</button>
        <button onClick={onFeedback} disabled={!documents.length}><Sparkles size={16} />Feedback</button>
      </Toolbar>
      <section className="document-library" aria-label="Biblioteca documental">
        <div className="panel-title"><span>Biblioteca documental</span><strong>{evidence.length} archivos</strong></div>
        <div className="library-upload">
          <select value={uploadEvidenceType} onChange={(event) => setUploadEvidenceType(event.target.value)} aria-label="Tipo de documento">
            <option value="document">Documento de ejecución</option>
            <option value="winning_offer">Oferta adjudicataria</option>
            <option value="contract">Contrato formalizado</option>
            <option value="specification">Pliego o condición contractual</option>
            <option value="award">Resolución de adjudicación</option>
          </select>
          <select value={uploadObligationId} onChange={(event) => setUploadObligationId(event.target.value)} aria-label="Vincular el documento a una obligación">
            <option value="">Sin vincular a una obligación</option>
            {obligations.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}
          </select>
          <label className="toolbar-upload"><Upload size={16} />Subir documento<input type="file" accept=".pdf,.docx,.txt,.md,.markdown" onChange={(event) => { const file = event.target.files?.[0]; event.currentTarget.value = ""; onUpload(file, uploadObligationId || undefined, uploadEvidenceType); }} /></label>
        </div>
        <div className="item-list">
          {evidence.map((item) => (
            <article key={item.id} className="item-card">
              <div>
                <strong>{item.title}</strong>
                <p>{item.original_filename || item.evidence_type} · {item.evidence_type === "winning_offer" ? "Oferta adjudicataria" : item.evidence_type} · {item.content_hash ? `hash ${item.content_hash.slice(0, 12)}` : "sin archivo original"}</p>
              </div>
              <div className="item-meta">
                <select value={item.obligation_id || ""} onChange={(event) => onLink(item.id, event.target.value || null)} aria-label={`Vincular ${item.title}`}>
                  <option value="">Sin vincular</option>
                  {obligations.map((obligation) => <option key={obligation.id} value={obligation.id}>{obligation.title}</option>)}
                </select>
                {item.evidence_type === "winning_offer" && <button className="inline-action" onClick={() => onAnalyzeOffer(item.id)}><Sparkles size={15} />Analizar oferta con IA</button>}
                {item.object_key && <a className="inline-action" href={api.evidenceDownloadUrl(item.id)}>Descargar</a>}
              </div>
            </article>
          ))}
          {!evidence.length && <p className="empty">Sube el primer documento para crear la biblioteca del contrato.</p>}
        </div>
      </section>
      <section className="offer-risks" aria-label="Riesgos de la oferta adjudicataria">
        <div className="panel-title"><span>Oferta adjudicataria y riesgos</span><strong>{risks.length} riesgos</strong></div>
        {!winningOffers.length && <p className="empty">Carga la oferta adjudicataria para contrastarla con el contrato y las demás fuentes.</p>}
        {!!winningOffers.length && <p className="offer-hint">El análisis compara los compromisos de la oferta con el contrato, obligaciones y documentos disponibles. Sus conclusiones requieren validación humana.</p>}
        <div className="item-list">
          {risks.map((item) => (
            <article key={item.id} className="item-card">
              <div>
                <strong>{item.title}</strong>
                <p>{item.description}</p>
                <p className="comparison">Comparación: {item.comparison || "Pendiente"}</p>
              </div>
              <div className="item-meta">
                <span className={clsx("severity", severityClass(item.severity))}>{item.severity}</span>
                <span className="status-pill">{item.risk_type}</span>
                <span className="status-pill">{statusLabel(item.validation_status)}</span>
                <span>{item.citations.length} fuentes</span>
              </div>
            </article>
          ))}
        </div>
        {!!draftRisks.length && <button className="validate-risk" onClick={onValidateRisk}><ShieldCheck size={16} />Validar primer riesgo</button>}
      </section>
      <div className="item-list">
        {documents.map((item) => (
          <article key={item.id} className="item-card">
            <div>
              <strong>{item.title}</strong>
              <p>{item.content_text.slice(0, 220)}</p>
            </div>
            <span className="status-pill">{statusLabel(item.status)}</span>
          </article>
        ))}
        {!documents.length && <p className="empty">No hay borradores generados todavía.</p>}
      </div>
    </>
  );
}

function Penalties({ penalties, onCalculate, onValidate }: { penalties: PenaltyCase[]; onCalculate: () => void; onValidate: () => void }) {
  return (
    <>
      <Toolbar>
        <button onClick={onCalculate}><Gavel size={16} />Calcular</button>
        <button onClick={onValidate} disabled={!penalties.length}><ShieldCheck size={16} />Validar</button>
      </Toolbar>
      <div className="item-list">
        {penalties.map((item) => (
          <article key={item.id} className="item-card">
            <div>
              <strong>{formatEuro(item.calculated_amount)}</strong>
              <p>{item.basis_text}</p>
            </div>
            <div className="item-meta">
              <span>{item.calculation.method}</span>
              <span className="status-pill">{statusLabel(item.status)}</span>
            </div>
          </article>
        ))}
        {!penalties.length && <p className="empty">No hay penalidades calculadas.</p>}
      </div>
    </>
  );
}

function Proceedings({ proceedings, onOpen, onAdvance }: { proceedings: ContractProceeding[]; onOpen: () => void; onAdvance: () => void }) {
  return (
    <>
      <Toolbar>
        <button onClick={onOpen}><Gavel size={16} />Abrir</button>
        <button onClick={onAdvance} disabled={!proceedings.length}><ShieldCheck size={16} />Avanzar</button>
      </Toolbar>
      <div className="item-list">
        {proceedings.map((item) => (
          <article key={item.id} className="item-card">
            <div>
              <strong>{item.title}</strong>
              <p>{item.summary}</p>
            </div>
            <div className="item-meta">
              <span>{item.case_type}</span>
              <span className="status-pill">{statusLabel(item.status)}</span>
              <span>{shortDate(item.due_date)}</span>
            </div>
          </article>
        ))}
        {!proceedings.length && <p className="empty">No hay expedientes abiertos.</p>}
      </div>
    </>
  );
}

function Governance({ governance, auditEvents, onServiceReturn }: { governance: ContractGovernance | null; auditEvents: AuditEvent[]; onServiceReturn: () => void }) {
  const manifest = governance?.manifest;
  const actions = governance?.audit_summary.actions || {};
  const topActions = Object.entries(actions).sort((a, b) => b[1] - a[1]).slice(0, 6);
  return (
    <>
      <Toolbar>
        <button onClick={onServiceReturn}><Archive size={16} />Devolucion completa</button>
      </Toolbar>
      <div className="split-panels">
        <div>
          <div className="panel-title"><span>Manifiesto</span><strong>{manifest?.runtime.auth_mode ? String(manifest.runtime.auth_mode) : "runtime"}</strong></div>
          <div className="compact-stack">
            <MiniStat label="Modelo" value={manifest?.ai.model || "Pendiente"} />
            <MiniStat label="Validacion" value={manifest?.human_oversight.default_state || "draft"} />
            <MiniStat label="Export" value={manifest?.security.export_requires_permission || "export"} />
            <MiniStat label="Feedback" value={manifest?.human_oversight.feedback_enabled ? "activo" : "pendiente"} />
          </div>
          <div className="warning-list">
            {(manifest?.ai.limitations || []).slice(0, 3).map((item) => <span key={item}>{item}</span>)}
          </div>
        </div>
        <div>
          <div className="panel-title"><span>Devolucion</span><strong>{manifest?.service_return.formats.join(", ") || "json"}</strong></div>
          <div className="tag-grid">
            {(manifest?.service_return.included || []).map((item) => <span key={item}>{item}</span>)}
          </div>
        </div>
      </div>
      <div className="split-panels">
        <div>
          <div className="panel-title"><span>Acciones</span><strong>{governance?.audit_summary.events ?? auditEvents.length}</strong></div>
          {topActions.map(([action, count]) => (
            <article key={action} className="compact-card">
              <strong>{action}</strong>
              <span>{count} eventos</span>
            </article>
          ))}
          {!topActions.length && <p className="empty">No hay acciones auditadas.</p>}
        </div>
        <div>
          <div className="panel-title"><span>Eventos recientes</span><strong>{auditEvents.length}</strong></div>
          {auditEvents.slice(0, 8).map((item) => (
            <article key={item.id} className="compact-card">
              <strong>{item.action}</strong>
              <span>{item.user_id || "sistema"} · {shortDate(item.created_at)}</span>
            </article>
          ))}
          {!auditEvents.length && <p className="empty">No hay eventos auditados.</p>}
        </div>
      </div>
    </>
  );
}

function Detail({ label, value, wide = false }: { label: string; value?: string | null; wide?: boolean }) {
  return (
    <div className={clsx("detail", wide && "wide")}>
      <span>{label}</span>
      <strong>{value || "Pendiente"}</strong>
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="mini-stat">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function Toolbar({ children }: { children: React.ReactNode }) {
  return <div className="action-row">{children}</div>;
}
