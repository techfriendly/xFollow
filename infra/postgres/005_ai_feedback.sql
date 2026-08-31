CREATE TABLE IF NOT EXISTS xfollow.ai_feedback (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  contract_id TEXT REFERENCES xfollow.contracts(id) ON DELETE SET NULL,
  artifact_type TEXT NOT NULL,
  artifact_id TEXT,
  rating TEXT NOT NULL,
  comment TEXT,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_by TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (artifact_type IN ('obligation', 'check', 'document', 'penalty', 'invoice', 'change', 'proceeding', 'task', 'other')),
  CHECK (rating IN ('positive', 'negative', 'neutral'))
);

CREATE INDEX IF NOT EXISTS idx_xfollow_feedback_contract
ON xfollow.ai_feedback(tenant_id, contract_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_xfollow_feedback_artifact
ON xfollow.ai_feedback(tenant_id, artifact_type, artifact_id, created_at DESC);

INSERT INTO xfollow.schema_migrations(version)
VALUES ('005_ai_feedback')
ON CONFLICT (version) DO NOTHING;
