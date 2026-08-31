CREATE TABLE IF NOT EXISTS xfollow.contract_changes (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  contract_id TEXT NOT NULL REFERENCES xfollow.contracts(id) ON DELETE CASCADE,
  change_type TEXT NOT NULL,
  title TEXT NOT NULL,
  reason TEXT NOT NULL,
  legal_basis TEXT,
  impact_summary TEXT,
  amount_delta NUMERIC,
  proposed_start_date DATE,
  proposed_end_date DATE,
  extension_months INTEGER,
  source_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
  document_id TEXT REFERENCES xfollow.generated_documents(id) ON DELETE SET NULL,
  ai_draft BOOLEAN NOT NULL DEFAULT TRUE,
  status TEXT NOT NULL DEFAULT 'draft',
  notes TEXT,
  created_by TEXT,
  validated_by TEXT,
  validated_at TIMESTAMPTZ,
  applied_by TEXT,
  applied_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (change_type IN ('modification', 'extension')),
  CHECK (status IN ('draft', 'under_review', 'validated', 'applied', 'rejected'))
);

CREATE INDEX IF NOT EXISTS idx_xfollow_changes_contract_status
ON xfollow.contract_changes(tenant_id, contract_id, status, change_type);

INSERT INTO xfollow.schema_migrations(version)
VALUES ('004_contract_changes')
ON CONFLICT (version) DO NOTHING;
