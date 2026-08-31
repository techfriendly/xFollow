ALTER TABLE xfollow.contracts ADD COLUMN IF NOT EXISTS renewal_status TEXT NOT NULL DEFAULT 'undefined';
ALTER TABLE xfollow.contracts ADD COLUMN IF NOT EXISTS decision_due_date DATE;
ALTER TABLE xfollow.contracts ADD COLUMN IF NOT EXISTS tags JSONB NOT NULL DEFAULT '[]'::jsonb;

CREATE TABLE IF NOT EXISTS xfollow.contract_comments (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  contract_id TEXT NOT NULL REFERENCES xfollow.contracts(id) ON DELETE CASCADE,
  body TEXT NOT NULL,
  created_by TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS xfollow.contract_alert_rules (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  name TEXT NOT NULL,
  filters JSONB NOT NULL DEFAULT '{}'::jsonb,
  lead_days INTEGER NOT NULL DEFAULT 30,
  enabled BOOLEAN NOT NULL DEFAULT TRUE,
  shared BOOLEAN NOT NULL DEFAULT FALSE,
  created_by TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_xfollow_contracts_control
ON xfollow.contracts(tenant_id, renewal_status, decision_due_date, end_date);

CREATE INDEX IF NOT EXISTS idx_xfollow_comments_contract
ON xfollow.contract_comments(tenant_id, contract_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_xfollow_alert_rules_tenant
ON xfollow.contract_alert_rules(tenant_id, enabled, updated_at DESC);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'contracts_renewal_status_check'
  ) THEN
    ALTER TABLE xfollow.contracts ADD CONSTRAINT contracts_renewal_status_check
      CHECK (renewal_status IN ('undefined', 'will_extend', 'extended', 'retender', 'no_renewal', 'finished', 'cancelled'));
  END IF;
END $$;

INSERT INTO xfollow.schema_migrations(version)
VALUES ('007_contract_control')
ON CONFLICT (version) DO NOTHING;
