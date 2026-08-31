CREATE SCHEMA IF NOT EXISTS xfollow;

CREATE TABLE IF NOT EXISTS xfollow.schema_migrations (
  version TEXT PRIMARY KEY,
  applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS xfollow.contracts (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  source_kind TEXT NOT NULL DEFAULT 'manual',
  source_id TEXT,
  xtender_workspace_id TEXT,
  pcsp_tender_id TEXT,
  xreview_procedure_id TEXT,
  xreview_lot_id TEXT,
  xreview_submission_id TEXT,
  file_number TEXT,
  title TEXT NOT NULL,
  contracting_body TEXT,
  contractor TEXT,
  responsible_unit TEXT,
  contract_manager TEXT,
  contract_type TEXT,
  procedure TEXT,
  cpv_codes JSONB NOT NULL DEFAULT '[]'::jsonb,
  status TEXT NOT NULL DEFAULT 'draft',
  budget_without_tax NUMERIC,
  budget_with_tax NUMERIC,
  awarded_amount NUMERIC,
  currency TEXT NOT NULL DEFAULT 'EUR',
  start_date DATE,
  end_date DATE,
  warranty_end_date DATE,
  extension_deadline DATE,
  guarantee_amount NUMERIC,
  data JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_by TEXT,
  updated_by TEXT,
  archived_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (source_kind IN ('manual', 'xtender', 'pcsp', 'xreview')),
  CHECK (status IN ('draft', 'active', 'completed', 'liquidated', 'resolved', 'archived'))
);

CREATE TABLE IF NOT EXISTS xfollow.contract_obligations (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  contract_id TEXT NOT NULL REFERENCES xfollow.contracts(id) ON DELETE CASCADE,
  category TEXT NOT NULL DEFAULT 'other',
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  source_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
  due_date DATE,
  recurrence TEXT,
  severity TEXT NOT NULL DEFAULT 'media',
  status TEXT NOT NULL DEFAULT 'pending',
  validation_status TEXT NOT NULL DEFAULT 'draft',
  created_by TEXT,
  validated_by TEXT,
  validated_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (category IN ('deadline', 'delivery', 'sla', 'special_condition', 'warranty', 'payment', 'documentation', 'extension', 'other')),
  CHECK (severity IN ('baja', 'media', 'alta', 'critica')),
  CHECK (status IN ('draft', 'pending', 'met', 'breached', 'waived')),
  CHECK (validation_status IN ('draft', 'validated', 'rejected'))
);

CREATE TABLE IF NOT EXISTS xfollow.contract_alerts (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  contract_id TEXT NOT NULL REFERENCES xfollow.contracts(id) ON DELETE CASCADE,
  obligation_id TEXT REFERENCES xfollow.contract_obligations(id) ON DELETE CASCADE,
  alert_type TEXT NOT NULL,
  title TEXT NOT NULL,
  due_date DATE NOT NULL,
  lead_days INTEGER NOT NULL DEFAULT 30,
  severity TEXT NOT NULL DEFAULT 'media',
  status TEXT NOT NULL DEFAULT 'open',
  generated_by TEXT NOT NULL DEFAULT 'system',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (severity IN ('baja', 'media', 'alta', 'critica')),
  CHECK (status IN ('open', 'snoozed', 'done', 'dismissed'))
);

CREATE TABLE IF NOT EXISTS xfollow.contract_evidence (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  contract_id TEXT NOT NULL REFERENCES xfollow.contracts(id) ON DELETE CASCADE,
  obligation_id TEXT REFERENCES xfollow.contract_obligations(id) ON DELETE SET NULL,
  title TEXT NOT NULL,
  evidence_type TEXT NOT NULL DEFAULT 'document',
  original_filename TEXT,
  object_key TEXT,
  content_hash TEXT,
  extracted_text TEXT,
  source_url TEXT,
  status TEXT NOT NULL DEFAULT 'available',
  uploaded_by TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (status IN ('available', 'excluded', 'error'))
);

CREATE TABLE IF NOT EXISTS xfollow.compliance_checks (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  contract_id TEXT NOT NULL REFERENCES xfollow.contracts(id) ON DELETE CASCADE,
  obligation_id TEXT REFERENCES xfollow.contract_obligations(id) ON DELETE SET NULL,
  evidence_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
  result TEXT NOT NULL,
  reasoning TEXT NOT NULL,
  citations JSONB NOT NULL DEFAULT '[]'::jsonb,
  ai_draft BOOLEAN NOT NULL DEFAULT TRUE,
  status TEXT NOT NULL DEFAULT 'draft',
  created_by TEXT,
  validated_by TEXT,
  validated_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (result IN ('compliant', 'at_risk', 'breach', 'needs_review')),
  CHECK (status IN ('draft', 'validated', 'rejected'))
);

CREATE TABLE IF NOT EXISTS xfollow.generated_documents (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  contract_id TEXT NOT NULL REFERENCES xfollow.contracts(id) ON DELETE CASCADE,
  document_type TEXT NOT NULL,
  title TEXT NOT NULL,
  content_text TEXT NOT NULL,
  citations JSONB NOT NULL DEFAULT '[]'::jsonb,
  prompt_trace JSONB NOT NULL DEFAULT '{}'::jsonb,
  status TEXT NOT NULL DEFAULT 'draft',
  generated_by TEXT,
  validated_by TEXT,
  validated_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (document_type IN ('recepcion_acta', 'liquidacion_informe', 'modificacion_informe_juridico', 'prorroga_informe_juridico', 'penalidad_expediente', 'resolucion_expediente')),
  CHECK (status IN ('draft', 'validated', 'rejected'))
);

CREATE TABLE IF NOT EXISTS xfollow.penalty_cases (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  contract_id TEXT NOT NULL REFERENCES xfollow.contracts(id) ON DELETE CASCADE,
  obligation_id TEXT REFERENCES xfollow.contract_obligations(id) ON DELETE SET NULL,
  case_type TEXT NOT NULL DEFAULT 'penalty',
  basis_text TEXT NOT NULL,
  daily_amount NUMERIC,
  days_late INTEGER,
  base_amount NUMERIC,
  percentage NUMERIC,
  cap_amount NUMERIC,
  calculated_amount NUMERIC NOT NULL,
  calculation JSONB NOT NULL DEFAULT '{}'::jsonb,
  content_text TEXT,
  citations JSONB NOT NULL DEFAULT '[]'::jsonb,
  status TEXT NOT NULL DEFAULT 'draft',
  created_by TEXT,
  validated_by TEXT,
  validated_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (case_type IN ('penalty', 'resolution')),
  CHECK (status IN ('draft', 'validated', 'opened', 'resolved', 'rejected'))
);

CREATE TABLE IF NOT EXISTS xfollow.contract_members (
  contract_id TEXT NOT NULL REFERENCES xfollow.contracts(id) ON DELETE CASCADE,
  user_id TEXT NOT NULL,
  access_level TEXT NOT NULL DEFAULT 'edit',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (contract_id, user_id),
  CHECK (access_level IN ('read', 'edit', 'validate', 'manage'))
);

CREATE TABLE IF NOT EXISTS xfollow.audit_events (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  contract_id TEXT REFERENCES xfollow.contracts(id) ON DELETE SET NULL,
  user_id TEXT,
  action TEXT NOT NULL,
  trace_id TEXT NOT NULL,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_xfollow_contracts_tenant_status ON xfollow.contracts(tenant_id, status, archived_at);
CREATE INDEX IF NOT EXISTS idx_xfollow_contracts_xtender ON xfollow.contracts(tenant_id, xtender_workspace_id);
CREATE INDEX IF NOT EXISTS idx_xfollow_contracts_pcsp ON xfollow.contracts(tenant_id, pcsp_tender_id);
CREATE INDEX IF NOT EXISTS idx_xfollow_obligations_contract ON xfollow.contract_obligations(tenant_id, contract_id, validation_status, status);
CREATE INDEX IF NOT EXISTS idx_xfollow_alerts_contract_status ON xfollow.contract_alerts(tenant_id, contract_id, status, due_date);
CREATE INDEX IF NOT EXISTS idx_xfollow_evidence_contract ON xfollow.contract_evidence(tenant_id, contract_id, obligation_id);
CREATE INDEX IF NOT EXISTS idx_xfollow_checks_contract ON xfollow.compliance_checks(tenant_id, contract_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_xfollow_documents_contract ON xfollow.generated_documents(tenant_id, contract_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_xfollow_penalties_contract ON xfollow.penalty_cases(tenant_id, contract_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_xfollow_audit_contract ON xfollow.audit_events(tenant_id, contract_id, created_at DESC);

INSERT INTO xfollow.schema_migrations(version)
VALUES ('001_xfollow_schema')
ON CONFLICT (version) DO NOTHING;
