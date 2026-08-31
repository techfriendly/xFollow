CREATE TABLE IF NOT EXISTS xfollow.contract_risks (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  contract_id TEXT NOT NULL REFERENCES xfollow.contracts(id) ON DELETE CASCADE,
  offer_evidence_id TEXT REFERENCES xfollow.contract_evidence(id) ON DELETE SET NULL,
  risk_type TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  comparison TEXT,
  severity TEXT NOT NULL DEFAULT 'media',
  citations JSONB NOT NULL DEFAULT '[]'::jsonb,
  validation_status TEXT NOT NULL DEFAULT 'draft',
  created_by TEXT,
  validated_by TEXT,
  validated_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (risk_type IN ('scope', 'schedule', 'resources', 'quality', 'economic', 'legal', 'other')),
  CHECK (severity IN ('baja', 'media', 'alta', 'critica')),
  CHECK (validation_status IN ('draft', 'validated', 'rejected'))
);

CREATE INDEX IF NOT EXISTS idx_xfollow_contract_risks_contract
ON xfollow.contract_risks(tenant_id, contract_id, validation_status, severity);

ALTER TABLE xfollow.ai_jobs DROP CONSTRAINT IF EXISTS ai_jobs_job_type_check;
ALTER TABLE xfollow.ai_jobs ADD CONSTRAINT ai_jobs_job_type_check
CHECK (job_type IN ('obligations_extract', 'compliance_check', 'document_generate', 'change_report', 'offer_risk_analysis'));

INSERT INTO xfollow.schema_migrations(version)
VALUES ('009_offer_risk_analysis')
ON CONFLICT (version) DO NOTHING;
