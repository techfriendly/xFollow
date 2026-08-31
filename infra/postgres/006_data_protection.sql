CREATE TABLE IF NOT EXISTS xfollow.data_protection_assessments (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  contract_id TEXT NOT NULL REFERENCES xfollow.contracts(id) ON DELETE CASCADE,
  evidence_id TEXT REFERENCES xfollow.contract_evidence(id) ON DELETE SET NULL,
  scope TEXT NOT NULL,
  source_title TEXT NOT NULL,
  result TEXT NOT NULL,
  severity TEXT NOT NULL DEFAULT 'baja',
  findings JSONB NOT NULL DEFAULT '[]'::jsonb,
  redacted_preview TEXT,
  recommendation TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'draft',
  created_by TEXT,
  resolved_by TEXT,
  resolved_at TIMESTAMPTZ,
  resolution_comment TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (scope IN ('contract', 'evidence')),
  CHECK (result IN ('clear', 'personal_data', 'confidential', 'mixed', 'needs_review')),
  CHECK (severity IN ('baja', 'media', 'alta', 'critica')),
  CHECK (status IN ('draft', 'resolved', 'accepted_risk', 'false_positive'))
);

CREATE INDEX IF NOT EXISTS idx_xfollow_data_protection_contract
ON xfollow.data_protection_assessments(tenant_id, contract_id, status, severity, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_xfollow_data_protection_evidence
ON xfollow.data_protection_assessments(tenant_id, evidence_id, created_at DESC);

INSERT INTO xfollow.schema_migrations(version)
VALUES ('006_data_protection')
ON CONFLICT (version) DO NOTHING;
