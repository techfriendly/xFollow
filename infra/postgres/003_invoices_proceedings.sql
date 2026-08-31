CREATE TABLE IF NOT EXISTS xfollow.contract_invoices (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  contract_id TEXT NOT NULL REFERENCES xfollow.contracts(id) ON DELETE CASCADE,
  obligation_id TEXT REFERENCES xfollow.contract_obligations(id) ON DELETE SET NULL,
  invoice_number TEXT NOT NULL,
  supplier TEXT,
  concept TEXT NOT NULL,
  invoice_date DATE,
  service_period_start DATE,
  service_period_end DATE,
  amount_without_tax NUMERIC NOT NULL DEFAULT 0,
  tax_amount NUMERIC NOT NULL DEFAULT 0,
  amount_with_tax NUMERIC NOT NULL DEFAULT 0,
  currency TEXT NOT NULL DEFAULT 'EUR',
  status TEXT NOT NULL DEFAULT 'registered',
  evidence_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
  compliance_check_id TEXT REFERENCES xfollow.compliance_checks(id) ON DELETE SET NULL,
  payment_due_date DATE,
  paid_at TIMESTAMPTZ,
  notes TEXT,
  registered_by TEXT,
  validated_by TEXT,
  validated_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (status IN ('draft', 'registered', 'conforming', 'rejected', 'payment_ordered', 'paid'))
);

CREATE TABLE IF NOT EXISTS xfollow.contract_proceedings (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  contract_id TEXT NOT NULL REFERENCES xfollow.contracts(id) ON DELETE CASCADE,
  penalty_case_id TEXT REFERENCES xfollow.penalty_cases(id) ON DELETE SET NULL,
  case_type TEXT NOT NULL,
  title TEXT NOT NULL,
  summary TEXT NOT NULL,
  legal_basis TEXT,
  proposed_action TEXT,
  status TEXT NOT NULL DEFAULT 'opened',
  due_date DATE,
  document_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
  timeline JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_by TEXT,
  updated_by TEXT,
  validated_by TEXT,
  validated_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (case_type IN ('penalty', 'resolution')),
  CHECK (status IN ('draft', 'opened', 'instruction', 'hearing', 'proposal', 'resolved', 'closed', 'rejected'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_xfollow_invoices_unique_number
ON xfollow.contract_invoices(tenant_id, contract_id, invoice_number);

CREATE INDEX IF NOT EXISTS idx_xfollow_invoices_contract_status
ON xfollow.contract_invoices(tenant_id, contract_id, status, payment_due_date);

CREATE INDEX IF NOT EXISTS idx_xfollow_proceedings_contract_status
ON xfollow.contract_proceedings(tenant_id, contract_id, status, due_date);

INSERT INTO xfollow.schema_migrations(version)
VALUES ('003_invoices_proceedings')
ON CONFLICT (version) DO NOTHING;
