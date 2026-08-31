CREATE TABLE IF NOT EXISTS xfollow.contract_tasks (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  contract_id TEXT NOT NULL REFERENCES xfollow.contracts(id) ON DELETE CASCADE,
  source_type TEXT,
  source_id TEXT,
  title TEXT NOT NULL,
  description TEXT,
  due_date DATE,
  owner_user_id TEXT,
  severity TEXT NOT NULL DEFAULT 'media',
  status TEXT NOT NULL DEFAULT 'todo',
  created_by TEXT,
  completed_by TEXT,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (severity IN ('baja', 'media', 'alta', 'critica')),
  CHECK (status IN ('todo', 'doing', 'done', 'dismissed'))
);

CREATE INDEX IF NOT EXISTS idx_xfollow_tasks_contract_status ON xfollow.contract_tasks(tenant_id, contract_id, status, due_date);
CREATE INDEX IF NOT EXISTS idx_xfollow_tasks_owner ON xfollow.contract_tasks(tenant_id, owner_user_id, status, due_date);

INSERT INTO xfollow.schema_migrations(version)
VALUES ('002_contract_tasks')
ON CONFLICT (version) DO NOTHING;
