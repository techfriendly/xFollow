CREATE TABLE IF NOT EXISTS xfollow.ai_jobs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  contract_id TEXT NOT NULL REFERENCES xfollow.contracts(id) ON DELETE CASCADE,
  job_type TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'queued',
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  result JSONB NOT NULL DEFAULT '{}'::jsonb,
  attempts INTEGER NOT NULL DEFAULT 0,
  next_run_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  requested_by TEXT,
  claimed_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  last_error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (job_type IN ('obligations_extract', 'compliance_check', 'document_generate', 'change_report')),
  CHECK (status IN ('queued', 'running', 'retrying', 'completed', 'failed'))
);

CREATE INDEX IF NOT EXISTS idx_xfollow_ai_jobs_claim
ON xfollow.ai_jobs(status, next_run_at, created_at)
WHERE status IN ('queued', 'retrying');

CREATE INDEX IF NOT EXISTS idx_xfollow_ai_jobs_contract
ON xfollow.ai_jobs(tenant_id, contract_id, created_at DESC);

INSERT INTO xfollow.schema_migrations(version)
VALUES ('008_ai_jobs')
ON CONFLICT (version) DO NOTHING;
