ALTER TABLE xfollow.contracts
  ADD COLUMN IF NOT EXISTS xreview_procedure_id TEXT,
  ADD COLUMN IF NOT EXISTS xreview_lot_id TEXT,
  ADD COLUMN IF NOT EXISTS xreview_submission_id TEXT;

ALTER TABLE xfollow.contracts
  DROP CONSTRAINT IF EXISTS contracts_source_kind_check;

ALTER TABLE xfollow.contracts
  ADD CONSTRAINT contracts_source_kind_check
  CHECK (source_kind IN ('manual', 'xtender', 'pcsp', 'xreview'));

CREATE UNIQUE INDEX IF NOT EXISTS uq_xfollow_xreview_lot
  ON xfollow.contracts(tenant_id, xreview_procedure_id, xreview_lot_id)
  WHERE source_kind = 'xreview';

INSERT INTO xfollow.schema_migrations(version)
VALUES ('011_xreview_handoff')
ON CONFLICT (version) DO NOTHING;
